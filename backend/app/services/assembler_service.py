import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    AudioFileClip,
    ImageClip,
    VideoFileClip,
    CompositeVideoClip,
    concatenate_videoclips,
    ColorClip,
)
from app.services.subtitle_service import SubtitleChunk
from typing import List

WIDTH, HEIGHT = 1080, 1920
FPS = 30
FONT_SIZE = 72
FONT_COLOR = (255, 255, 255)
SHADOW_COLOR = (0, 0, 0)
BG_COLOR = (10, 10, 20)


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    font_paths = [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/liberation/LiberationSans-Bold.ttf",
    ]
    for path in font_paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _make_fallback_bg(duration: float) -> ImageClip:
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(BG_COLOR[0] + (30 - BG_COLOR[0]) * ratio)
        g = int(BG_COLOR[1] + (10 - BG_COLOR[1]) * ratio)
        b = int(BG_COLOR[2] + (40 - BG_COLOR[2]) * ratio)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))
    return ImageClip(np.array(img), duration=duration)


def _build_video_bg(clip_paths: List[str], duration: float):
    """Assemble les clips vidéo en fond 9:16 pour couvrir toute la durée."""
    clips = []
    for path in clip_paths:
        try:
            print(f"[ASSEMBLER] Loading clip: {path}")
            c = VideoFileClip(path, audio=False)
            print(f"[ASSEMBLER] Clip size: {c.size}, duration: {c.duration:.1f}s")
            # Crop centre pour obtenir 9:16
            orig_w, orig_h = c.size
            target_ratio = WIDTH / HEIGHT
            clip_ratio = orig_w / orig_h
            if clip_ratio > target_ratio:
                new_w = int(orig_h * target_ratio)
                x1 = (orig_w - new_w) // 2
                c = c.crop(x1=x1, x2=x1 + new_w)
            else:
                new_h = int(orig_w / target_ratio)
                y1 = (orig_h - new_h) // 2
                c = c.crop(y1=y1, y2=y1 + new_h)
            c = c.resize((WIDTH, HEIGHT))
            print(f"[ASSEMBLER] Clip processed OK -> {c.size}")
            clips.append(c)
        except Exception as e:
            print(f"[ASSEMBLER] Clip error: {e}")
            continue

    print(f"[ASSEMBLER] {len(clips)} clips loaded")
    if not clips:
        return None

    # Boucler les clips jusqu'à couvrir la durée
    total = sum(c.duration for c in clips)
    while total < duration:
        clips += clips
        total = sum(c.duration for c in clips)

    bg = concatenate_videoclips(clips).subclip(0, duration)
    return bg


def _make_subtitle_frame(text: str) -> np.ndarray:
    img = Image.new("RGBA", (WIDTH, 300), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = _load_font(FONT_SIZE)

    words = text.split()
    lines, line = [], []
    for word in words:
        test = " ".join(line + [word])
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] > WIDTH - 80:
            lines.append(" ".join(line))
            line = [word]
        else:
            line.append(word)
    if line:
        lines.append(" ".join(line))

    total_h = len(lines) * (FONT_SIZE + 10)
    y = (300 - total_h) // 2

    for line_text in lines:
        bbox = draw.textbbox((0, 0), line_text, font=font)
        x = (WIDTH - (bbox[2] - bbox[0])) // 2
        draw.text((x + 3, y + 3), line_text, font=font, fill=(*SHADOW_COLOR, 200))
        draw.text((x, y), line_text, font=font, fill=(*FONT_COLOR, 255))
        y += FONT_SIZE + 10

    return np.array(img)


def assemble_video(
    audio_path: str,
    chunks: List[SubtitleChunk],
    output_path: str,
    clip_paths: List[str] = None,
) -> str:
    audio = AudioFileClip(audio_path)
    duration = audio.duration

    # Fond vidéo ou fallback dégradé
    bg = None
    if clip_paths:
        bg = _build_video_bg(clip_paths, duration)

    if bg is None:
        bg = _make_fallback_bg(duration)

    # Overlay sombre semi-transparent pour lisibilité des sous-titres
    overlay = ColorClip(size=(WIDTH, HEIGHT), color=(0, 0, 0), duration=duration).set_opacity(0.45)

    # Sous-titres
    subtitle_clips = []
    for chunk in chunks:
        frame = _make_subtitle_frame(chunk.text)
        clip = (
            ImageClip(frame, ismask=False)
            .set_start(chunk.start)
            .set_duration(chunk.end - chunk.start)
            .set_position(("center", HEIGHT - 400))
        )
        subtitle_clips.append(clip)

    video = CompositeVideoClip(
        [bg, overlay] + subtitle_clips,
        size=(WIDTH, HEIGHT),
    ).set_audio(audio)

    video.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile=output_path + ".tmp.m4a",
        remove_temp=True,
        logger=None,
    )
    audio.close()
    video.close()

    # Nettoyage clips temp
    if clip_paths:
        for p in clip_paths:
            try:
                os.remove(p)
            except Exception:
                pass

    return output_path
