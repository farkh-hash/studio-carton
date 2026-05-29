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
    "ALEX": (96, 165, 250),    # bleu
    "SARAH": (244, 114, 182),  # rose
    "MARC": (74, 222, 128),    # vert
    "LEA": (251, 191, 36),     # jaune
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


def _make_dialogue_frame(character: str, line: str, emotion: str) -> np.ndarray:
    """Crée une frame avec le nom du personnage + sa réplique en bas d'écran."""
    img = Image.new("RGBA", (WIDTH, 420), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    char_color = CHARACTER_COLORS.get(character, (255, 255, 255))
    font_name = _load_font(42)
    font_line = _load_font(68)

    # Fond semi-transparent pour la réplique
    draw.rounded_rectangle([30, 10, WIDTH - 30, 410], radius=24, fill=(0, 0, 0, 200))

    # Nom du personnage + émotion
    char_text = f"{character}  •  {emotion}" if emotion else character
    draw.text((60, 24), char_text, font=font_name, fill=(*char_color, 255))

    # Réplique avec word wrap
    words = line.split()
    lines_out, line_buf = [], []
    for word in words:
        test = " ".join(line_buf + [word])
        bbox = draw.textbbox((0, 0), test, font=font_line)
        if bbox[2] > WIDTH - 120:
            lines_out.append(" ".join(line_buf))
            line_buf = [word]
        else:
            line_buf.append(word)
    if line_buf:
        lines_out.append(" ".join(line_buf))

    total_h = len(lines_out) * (68 + 8)
    y = 80 + max(0, (280 - total_h) // 2)

    for lt in lines_out:
        bbox = draw.textbbox((0, 0), lt, font=font_line)
        x = (WIDTH - (bbox[2] - bbox[0])) // 2
        # Contour noir
        for dx in [-3, 0, 3]:
            for dy in [-3, 0, 3]:
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), lt, font=font_line, fill=(0, 0, 0, 255))
        draw.text((x, y), lt, font=font_line, fill=(255, 255, 255, 255))
        y += 68 + 8

    return np.array(img)


def _make_fallback_bg(duration: float) -> ImageClip:
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    for y in range(HEIGHT):
        r = int(BG_COLOR[0] + (40 - BG_COLOR[0]) * y / HEIGHT)
        g = int(BG_COLOR[1] + (15 - BG_COLOR[1]) * y / HEIGHT)
        b = int(BG_COLOR[2] + (50 - BG_COLOR[2]) * y / HEIGHT)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))
    return ImageClip(np.array(img), duration=duration)


def assemble_scenario(
    segments: list[dict],
    output_path: str,
    bg_video_path: str = None,
    music_path: str = None,
) -> str:
    """
    Assemble le scénario complet :
    - Séquence les répliques avec l'audio de chaque personnage
    - Affiche le nom + réplique de chaque personnage
    - Background vidéo Pexels ou dégradé
    """
    if not segments:
        raise ValueError("Aucun segment audio")

    # Sauvegarder chaque segment audio
    segment_files = []
    for i, seg in enumerate(segments):
        tmp = tempfile.NamedTemporaryFile(suffix=f"_seg_{i}.mp3", delete=False)
        tmp.write(seg["audio_bytes"])
        tmp.close()
        segment_files.append(tmp.name)

    # Charger les clips audio et calculer les durées réelles
    audio_clips = []
    durations = []
    for f in segment_files:
        try:
            ac = AudioFileClip(f)
            audio_clips.append(ac)
            durations.append(ac.duration)
        except Exception:
            durations.append(seg.get("duration_estimate", 2.0))
            audio_clips.append(None)

    total_duration = sum(durations)

    # Background global
    if bg_video_path and os.path.exists(bg_video_path):
        try:
            bg = VideoFileClip(bg_video_path, audio=False).subclip(0, total_duration)
        except Exception:
            bg = _make_fallback_bg(total_duration)
    else:
        bg = _make_fallback_bg(total_duration)

    overlay = ColorClip(size=(WIDTH, HEIGHT), color=(0, 0, 0), duration=total_duration).set_opacity(0.35)

    # Construire les clips de dialogue
    dialogue_clips = []
    t = 0.0
    for i, (seg, dur) in enumerate(zip(segments, durations)):
        frame = _make_dialogue_frame(
            seg.get("character", ""),
            seg.get("line", ""),
            seg.get("emotion", ""),
        )
        clip = (
            ImageClip(frame, ismask=False)
            .set_start(t)
            .set_duration(dur)
            .set_position(("center", HEIGHT - 440))
            .fadein(0.15)
            .fadeout(0.1)
        )
        dialogue_clips.append(clip)
        t += dur

    # Concaténer l'audio
    audio_parts = []
    t = 0.0
    for ac, dur in zip(audio_clips, durations):
        if ac:
            audio_parts.append(ac.set_start(t))
        t += dur

    from moviepy.editor import CompositeAudioClip as CAC
    if audio_parts:
        final_audio = CAC(audio_parts)
    else:
        raise ValueError("Aucun audio disponible")

    # Ajouter musique de fond
    if music_path and os.path.exists(music_path):
        try:
            music = audio_loop(
                AudioFileClip(music_path).volumex(0.10),
                duration=total_duration
            )
            final_audio = CAC([final_audio, music])
        except Exception:
            pass

    video = CompositeVideoClip(
        [bg, overlay] + dialogue_clips,
        size=(WIDTH, HEIGHT),
    ).set_audio(final_audio)

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
