import os
import tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    AudioFileClip, ImageClip, VideoFileClip,
    CompositeVideoClip, ColorClip, concatenate_videoclips,
    CompositeAudioClip
)
from moviepy.audio.fx.all import audio_loop

WIDTH, HEIGHT = 1080, 1920
FPS = 30
BG_COLOR = (15, 15, 25)

CHARACTER_COLORS = {
    "ALEX": (96, 165, 250),    # bleu
    "SARAH": (244, 114, 182),  # rose
}

CHARACTER_POSITIONS = {
    "ALEX": "left",
    "SARAH": "right",
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
    """Crée une frame avec le personnage identifié et sa réplique."""
    img = Image.new("RGBA", (WIDTH, 420), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    color = CHARACTER_COLORS.get(character, (255, 255, 255))
    font_name = _load_font(44)
    font_line = _load_font(70)

    # Fond du bloc dialogue
    draw.rounded_rectangle([30, 10, WIDTH - 30, 410], radius=24, fill=(0, 0, 0, 210))

    # Barre colorée latérale
    draw.rounded_rectangle([30, 10, 44, 410], radius=12, fill=(*color, 255))

    # Nom du personnage
    name_text = f"  {character}  •  {emotion}" if emotion else f"  {character}"
    draw.text((60, 22), name_text, font=font_name, fill=(*color, 255))

    # Réplique avec word wrap
    words = line.split()
    lines_out, line_buf = [], []
    for word in words:
        test = " ".join(line_buf + [word])
        bbox = draw.textbbox((0, 0), test, font=font_line)
        if bbox[2] > WIDTH - 100:
            lines_out.append(" ".join(line_buf))
            line_buf = [word]
        else:
            line_buf.append(word)
    if line_buf:
        lines_out.append(" ".join(line_buf))

    total_h = len(lines_out) * (70 + 8)
    y = 75 + max(0, (310 - total_h) // 2)

    for lt in lines_out:
        bbox = draw.textbbox((0, 0), lt, font=font_line)
        x = (WIDTH - (bbox[2] - bbox[0])) // 2
        # Contour
        for dx in [-2, 0, 2]:
            for dy in [-2, 0, 2]:
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), lt, font=font_line, fill=(0, 0, 0, 255))
        draw.text((x, y), lt, font=font_line, fill=(255, 255, 255, 255))
        y += 70 + 8

    return np.array(img)


def assemble_scenario(
    segments: list[dict],
    output_path: str,
    bg_video_path: str = None,
    music_path: str = None,
    character_clips: dict = None,
) -> str:
    """
    Assemble le scénario de façon simple et fiable :
    - Un fond global (Pexels ou dégradé)
    - Overlay dialogue par réplique avec nom du personnage et couleur
    - Audio séquentiel de chaque réplique
    """
    if not segments:
        raise ValueError("Aucun segment audio")

    # Sauvegarder les segments audio et mesurer les durées
    segment_files = []
    for i, seg in enumerate(segments):
        tmp = tempfile.NamedTemporaryFile(suffix=f"_seg_{i}.mp3", delete=False)
        tmp.write(seg["audio_bytes"])
        tmp.close()
        segment_files.append(tmp.name)

    audio_clips = []
    durations = []
    for f in segment_files:
        try:
            ac = AudioFileClip(f)
            audio_clips.append(ac)
            durations.append(ac.duration + 0.25)
        except Exception as e:
            print(f"[SCENARIO] Audio error: {e}")
            durations.append(3.0)
            audio_clips.append(None)

    total_duration = sum(durations)

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
    overlay = ColorClip(size=(WIDTH, HEIGHT), color=(0, 0, 0), duration=total_duration).set_opacity(0.35)

    # Clips de dialogue (simple, un par réplique)
    dialogue_clips = []
    t = 0.0
    for seg, dur in zip(segments, durations):
        character = seg.get("character", "ALEX")
        line = seg.get("line", "")
        emotion = seg.get("emotion", "")

        if not line:
            t += dur
            continue

        frame = _make_dialogue_frame(character, line, emotion)
        clip = (
            ImageClip(frame, ismask=False)
            .set_start(t)
            .set_duration(max(0.1, dur - 0.1))
            .set_position(("center", HEIGHT - 440))
            .fadein(0.1)
            .fadeout(0.1)
        )
        dialogue_clips.append(clip)
        t += dur

    # Composition finale
    video = CompositeVideoClip(
        [bg, overlay] + dialogue_clips,
        size=(WIDTH, HEIGHT),
    )

    # Audio séquentiel
    audio_parts = []
    t = 0.0
    for ac, dur in zip(audio_clips, durations):
        if ac is not None:
            audio_parts.append(ac.set_start(t))
        t += dur

    if audio_parts:
        final_audio = CompositeAudioClip(audio_parts)

        if music_path and os.path.exists(music_path):
            try:
                music = audio_loop(
                    AudioFileClip(music_path).volumex(0.08),
                    duration=total_duration
                )
                final_audio = CompositeAudioClip([final_audio, music])
            except Exception:
                pass

        video = video.set_audio(final_audio)

    video.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile=output_path + ".tmp.m4a",
        remove_temp=True,
        logger=None,
    )

    # Nettoyage
    for f in segment_files:
        try:
            os.remove(f)
        except Exception:
            pass
    for ac in audio_clips:
        if ac:
            try:
                ac.close()
            except Exception:
                pass
    video.close()

    return output_path
