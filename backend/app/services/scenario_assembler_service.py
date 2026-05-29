import os
import tempfile
import subprocess
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


def _process_character_clip(input_path: str, output_path: str, duration: float) -> bool:
    """Crop et resize un clip en portrait 9:16 avec ffmpeg."""
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-t", str(duration + 0.5),
        "-vf", f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,crop={WIDTH}:{HEIGHT}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "28",
        "-an", output_path
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=60)
    return result.returncode == 0 and os.path.exists(output_path)


def _make_fallback_bg(duration: float) -> ImageClip:
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    for y in range(HEIGHT):
        r = int(BG_COLOR[0] + (40 - BG_COLOR[0]) * y / HEIGHT)
        g = int(BG_COLOR[1] + (15 - BG_COLOR[1]) * y / HEIGHT)
        b = int(BG_COLOR[2] + (50 - BG_COLOR[2]) * y / HEIGHT)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))
    return ImageClip(np.array(img), duration=duration)


def _make_character_bg(clip_path: str, duration: float) -> VideoFileClip | None:
    """Charge et boucle un clip de personnage."""
    try:
        tmp_proc = clip_path.replace(".mp4", "_proc.mp4")
        if _process_character_clip(clip_path, tmp_proc, duration):
            c = VideoFileClip(tmp_proc, audio=False)
            # Boucler si nécessaire
            if c.duration < duration:
                loops = int(duration / c.duration) + 1
                clips = [c] * loops
                c = concatenate_videoclips(clips).subclip(0, duration)
            else:
                c = c.subclip(0, duration)
            return c
    except Exception as e:
        print(f"[SCENARIO] Clip erreur: {e}")
    return None


def _make_name_badge(character: str) -> np.ndarray:
    """Crée un badge avec le nom du personnage."""
    img = Image.new("RGBA", (WIDTH, 120), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = _load_font(52)
    color = CHARACTER_COLORS.get(character, (255, 255, 255))

    # Fond du badge
    draw.rounded_rectangle([40, 10, 500, 105], radius=20, fill=(0, 0, 0, 200))

    # Point coloré + nom
    draw.ellipse([60, 40, 95, 75], fill=(*color, 255))
    draw.text((110, 35), character, font=font, fill=(255, 255, 255, 255))

    return np.array(img)


def _make_dialogue_overlay(character: str, line: str) -> np.ndarray:
    """Crée le texte de la réplique en bas de l'écran."""
    img = Image.new("RGBA", (WIDTH, 350), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font_line = _load_font(64)
    color = CHARACTER_COLORS.get(character, (255, 255, 255))

    # Fond semi-transparent
    draw.rounded_rectangle([20, 10, WIDTH - 20, 340], radius=20, fill=(0, 0, 0, 210))

    # Ligne colorée du personnage
    draw.rectangle([20, 10, 8, 340], fill=(*color, 255))

    # Texte avec word wrap
    words = line.split()
    lines_out, line_buf = [], []
    for word in words:
        test = " ".join(line_buf + [word])
        bbox = draw.textbbox((0, 0), test, font=font_line)
        if bbox[2] > WIDTH - 80:
            lines_out.append(" ".join(line_buf))
            line_buf = [word]
        else:
            line_buf.append(word)
    if line_buf:
        lines_out.append(" ".join(line_buf))

    total_h = len(lines_out) * (64 + 8)
    y = (330 - total_h) // 2 + 10

    for lt in lines_out:
        bbox = draw.textbbox((0, 0), lt, font=font_line)
        x = (WIDTH - (bbox[2] - bbox[0])) // 2
        for dx in [-2, 0, 2]:
            for dy in [-2, 0, 2]:
                if dx != 0 or dy != 0:
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
    Assemble le scénario :
    - Chaque personnage a son propre clip vidéo qui s'affiche quand il parle
    - Le dialogue apparaît en bas de l'écran
    - Le badge du personnage apparaît en haut
    """
    if not segments:
        raise ValueError("Aucun segment audio")

    # Sauvegarder les segments audio
    segment_files = []
    for i, seg in enumerate(segments):
        tmp = tempfile.NamedTemporaryFile(suffix=f"_seg_{i}.mp3", delete=False)
        tmp.write(seg["audio_bytes"])
        tmp.close()
        segment_files.append(tmp.name)

    # Charger les clips audio et mesurer les durées réelles
    audio_clips = []
    durations = []
    for f in segment_files:
        try:
            ac = AudioFileClip(f)
            audio_clips.append(ac)
            durations.append(ac.duration + 0.3)  # pause entre répliques
        except Exception:
            durations.append(seg.get("duration_estimate", 3.0))
            audio_clips.append(None)

    total_duration = sum(durations)

    # Préparer les clips de personnages (si disponibles)
    char_clips_processed = {}
    if character_clips:
        for char, clip_path in character_clips.items():
            if clip_path and os.path.exists(clip_path):
                processed_path = clip_path.replace(".mp4", f"_{char}_proc.mp4")
                if _process_character_clip(clip_path, processed_path, total_duration):
                    char_clips_processed[char] = processed_path

    # Construire la timeline segment par segment
    video_clips_sequence = []
    dialogue_clips = []
    badge_clips = []

    t = 0.0
    for i, (seg, dur) in enumerate(zip(segments, durations)):
        character = seg.get("character", "ALEX")

        # Background pour ce segment : clip du personnage ou fallback
        if character in char_clips_processed:
            try:
                char_clip_path = char_clips_processed[character]
                c = VideoFileClip(char_clip_path, audio=False)
                if c.duration < dur:
                    loops = int(dur / c.duration) + 1
                    c = concatenate_videoclips([c] * loops).subclip(0, dur)
                else:
                    c = c.subclip(0, dur)
                bg_seg = c.set_start(t)
            except Exception:
                bg_seg = _make_fallback_bg(dur).set_start(t)
        elif bg_video_path and os.path.exists(bg_video_path):
            try:
                c = VideoFileClip(bg_video_path, audio=False)
                offset = (t % c.duration)
                if offset + dur > c.duration:
                    bg_seg = c.subclip(0, dur).set_start(t)
                else:
                    bg_seg = c.subclip(offset, offset + dur).set_start(t)
            except Exception:
                bg_seg = _make_fallback_bg(dur).set_start(t)
        else:
            bg_seg = _make_fallback_bg(dur).set_start(t)

        video_clips_sequence.append(bg_seg)

        # Overlay texte du dialogue
        dialogue_frame = _make_dialogue_overlay(character, seg.get("line", ""))
        dialogue_clip = (
            ImageClip(dialogue_frame, ismask=False)
            .set_start(t)
            .set_duration(dur - 0.1)
            .set_position(("center", HEIGHT - 360))
            .fadein(0.1)
            .fadeout(0.1)
        )
        dialogue_clips.append(dialogue_clip)

        # Badge nom du personnage
        badge_frame = _make_name_badge(character)
        badge_clip = (
            ImageClip(badge_frame, ismask=False)
            .set_start(t)
            .set_duration(dur - 0.1)
            .set_position((0, 60))
            .fadein(0.1)
            .fadeout(0.1)
        )
        badge_clips.append(badge_clip)

        t += dur

    # Overlay sombre léger
    overlay = ColorClip(size=(WIDTH, HEIGHT), color=(0, 0, 0), duration=total_duration).set_opacity(0.25)

    # Composer la vidéo finale
    all_clips = video_clips_sequence + [overlay] + badge_clips + dialogue_clips
    video = CompositeVideoClip(all_clips, size=(WIDTH, HEIGHT))

    # Audio : enchaînement des répliques
    audio_parts = []
    t = 0.0
    for ac, dur in zip(audio_clips, durations):
        if ac:
            audio_parts.append(ac.set_start(t))
        t += dur

    if audio_parts:
        from moviepy.editor import CompositeAudioClip as CAC
        final_audio = CAC(audio_parts)

        # Musique de fond optionnelle
        if music_path and os.path.exists(music_path):
            try:
                music = audio_loop(AudioFileClip(music_path).volumex(0.08), duration=total_duration)
                final_audio = CAC([final_audio, music])
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

    # Supprimer les clips traités
    for p in char_clips_processed.values():
        try:
            os.remove(p)
        except Exception:
            pass

    return output_path
