import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    AudioFileClip,
    ImageClip,
    VideoFileClip,
    CompositeVideoClip,
    ColorClip,
)
from app.services.subtitle_service import SubtitleChunk
from typing import List

WIDTH, HEIGHT = 1080, 1920
FPS = 30
FONT_SIZE = 88
FONT_COLOR = (255, 230, 0)
OUTLINE_COLOR = (0, 0, 0)
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


def _make_subtitle_frame(text: str) -> np.ndarray:
    img = Image.new("RGBA", (WIDTH, 320), (0, 0, 0, 0))
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

    total_h = len(lines) * (FONT_SIZE + 14)
    y = (320 - total_h) // 2

    for line_text in lines:
        bbox = draw.textbbox((0, 0), line_text, font=font)
        x = (WIDTH - (bbox[2] - bbox[0])) // 2
        for dx in [-3, -2, 0, 2, 3]:
            for dy in [-3, -2, 0, 2, 3]:
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), line_text, font=font, fill=(*OUTLINE_COLOR, 255))
        draw.text((x, y), line_text, font=font, fill=(*FONT_COLOR, 255))
        y += FONT_SIZE + 14

    return np.array(img)


def assemble_video(
    audio_path: str,
    chunks: List[SubtitleChunk],
    output_path: str,
    bg_video_path: str = None,
) -> str:
    audio = AudioFileClip(audio_path)
    duration = audio.duration

    if bg_video_path and os.path.exists(bg_video_path):
        try:
            bg = VideoFileClip(bg_video_path, audio=False).subclip(0, duration)
        except Exception:
            bg = _make_fallback_bg(duration)
    else:
        bg = _make_fallback_bg(duration)

    overlay = ColorClip(size=(WIDTH, HEIGHT), color=(0, 0, 0), duration=duration).set_opacity(0.30)

    subtitle_clips = []
    for chunk in chunks:
        frame = _make_subtitle_frame(chunk.text)
        clip = (
            ImageClip(frame, ismask=False)
            .set_start(chunk.start)
            .set_duration(chunk.end - chunk.start)
            .set_position(("center", HEIGHT - 420))
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

    if bg_video_path and os.path.exists(bg_video_path):
        try:
            os.remove(bg_video_path)
        except Exception:
            pass

    return output_path
