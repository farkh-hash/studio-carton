import os
import tempfile
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    AudioFileClip, ImageClip, VideoFileClip,
    CompositeVideoClip, ColorClip, concatenate_videoclips,
    concatenate_audioclips
)

WIDTH, HEIGHT = 1080, 1920
FPS = 30
BG_COLOR = (15, 15, 25)

CHARACTER_COLORS = {
    "ALEX": (96, 165, 250),
    "SARAH": (244, 114, 182),
}


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    paths = [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def _make_fallback_bg(duration: float) -> ImageClip:
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(BG_COLOR[0] + (40 - BG_COLOR[0]) * ratio)
        g = int(BG_COLOR[1] + (15 - BG_COLOR[1]) * ratio)
        b = int(BG_COLOR[2] + (50 - BG_COLOR[2]) * ratio)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))
    return ImageClip(np.array(img), duration=duration)


def _make_dialogue_frame(character: str, line: str, emotion: str) -> np.ndarray:
    """Frame simple avec nom du personnage + réplique."""
    img = Image.new("RGBA", (WIDTH, 380), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    color = CHARACTER_COLORS.get(character, (255, 255, 255))
    font_name = _load_font(40)
    font_line = _load_font(64)

    # Fond
    draw.rounded_rectangle([20, 5, WIDTH - 20, 375], radius=20, fill=(0, 0, 0, 210))
    # Accent couleur
    draw.rounded_rectangle([20, 5, 34, 375], radius=10, fill=(*color, 255))

    # Nom
    name_text = f"  {character}" + (f"  •  {emotion}" if emotion else "")
    draw.text((48, 16), name_text, font=font_name, fill=(*color, 255))

    # Texte avec wrap
    words = line.split()
    lines_out, buf = [], []
    for word in words:
        test = " ".join(buf + [word])
        bbox = draw.textbbox((0, 0), test, font=font_line)
        if bbox[2] > WIDTH - 80:
            lines_out.append(" ".join(buf))
            buf = [word]
        else:
            buf.append(word)
    if buf:
        lines_out.append(" ".join(buf))

    total_h = len(lines_out) * (64 + 8)
    y = 65 + max(0, (285 - total_h) // 2)

    for lt in lines_out:
        bbox = draw.textbbox((0, 0), lt, font=font_line)
        x = (WIDTH - (bbox[2] - bbox[0])) // 2
        for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
            draw.text((x + dx, y + dy), lt, font=font_line, fill=(0, 0, 0, 255))
        draw.text((x, y), lt, font=font_line, fill=(255, 255, 255, 255))
        y += 64 + 8

    return np.array(img)


def assemble_scenario(
    segments: list[dict],
    output_path: str,
    bg_video_path: str = None,
    music_path: str = None,
    character_clips: dict = None,
) -> str:
    """
    Assemblage simple et rapide :
    - 1 audio combiné via ffmpeg concat
    - 1 fond global
    - Overlay texte par réplique (timing basé sur durée audio réelle)
    """
    if not segments:
        raise ValueError("Aucun segment audio")

    # Sauvegarder les audios et mesurer les durées
    segment_files = []
    durations = []
    PAUSE = 0.25  # secondes entre répliques

    for i, seg in enumerate(segments):
        tmp = tempfile.NamedTemporaryFile(suffix=f"_seg{i}.mp3", delete=False)
        tmp.write(seg["audio_bytes"])
        tmp.close()
        segment_files.append(tmp.name)

        try:
            r = subprocess.run([
                "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", tmp.name
            ], capture_output=True, text=True, timeout=10)
            dur = float(r.stdout.strip() or "3.0")
        except Exception:
            dur = max(1.5, len(seg.get("line", "").split()) / 2.5)
        durations.append(dur)

    # Concatener les audios avec ffmpeg (rapide et fiable)
    concat_file = tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w")
    silence_files = []
    for f in segment_files:
        concat_file.write(f"file '{f}'\n")
        # Silence de 0.25s
        sil = f.replace(".mp3", "_sil.mp3")
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i",
            "anullsrc=r=44100:cl=stereo",
            "-t", str(PAUSE), "-acodec", "libmp3lame",
            "-loglevel", "quiet", sil
        ], capture_output=True, timeout=15)
        concat_file.write(f"file '{sil}'\n")
        silence_files.append(sil)
    concat_file.close()

    combined_audio = output_path.replace(".mp4", "_combined.mp3")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_file.name, "-acodec", "libmp3lame",
        "-loglevel", "quiet", combined_audio
    ], capture_output=True, timeout=60)
    os.remove(concat_file.name)

    # Charger l'audio final et obtenir la durée réelle
    audio_clip = AudioFileClip(combined_audio)
    total_duration = audio_clip.duration

    # Fond global
    if bg_video_path and os.path.exists(bg_video_path):
        try:
            c = VideoFileClip(bg_video_path, audio=False)
            if c.duration < total_duration:
                loops = int(total_duration / c.duration) + 1
                bg = concatenate_videoclips([c] * loops).subclip(0, total_duration)
            else:
                bg = c.subclip(0, total_duration)
        except Exception:
            bg = _make_fallback_bg(total_duration)
    else:
        bg = _make_fallback_bg(total_duration)

    # Overlay sombre
    overlay = ColorClip(size=(WIDTH, HEIGHT), color=(0, 0, 0), duration=total_duration).set_opacity(0.30)

    # Clips dialogue avec timing calculé
    dialogue_clips = []
    t = 0.0
    for seg, dur in zip(segments, durations):
        line = seg.get("line", "").strip()
        if not line:
            t += dur + PAUSE
            continue

        frame = _make_dialogue_frame(
            seg.get("character", "ALEX"),
            line,
            seg.get("emotion", "")
        )
        d_clip = (
            ImageClip(frame, ismask=False)
            .set_start(t)
            .set_duration(dur)
            .set_position(("center", HEIGHT - 410))
            .fadein(0.1)
            .fadeout(0.1)
        )
        dialogue_clips.append(d_clip)
        t += dur + PAUSE

    # Composition finale légère
    video = CompositeVideoClip(
        [bg, overlay] + dialogue_clips,
        size=(WIDTH, HEIGHT)
    ).set_audio(audio_clip)

    video.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile=output_path + ".tmp.m4a",
        remove_temp=True,
        logger=None,
        threads=2,
    )

    audio_clip.close()
    video.close()

    # Nettoyage
    for f in segment_files + silence_files + [combined_audio]:
        try:
            os.remove(f)
        except Exception:
            pass

    return output_path
