import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    AudioFileClip,
    ImageClip,
    VideoFileClip,
    CompositeVideoClip,
    CompositeAudioClip,
    ColorClip,
)
from moviepy.audio.fx.all import audio_loop
from app.services.subtitle_service import SubtitleChunk
from typing import List

WIDTH, HEIGHT = 1080, 1920
FPS = 30
FONT_SIZE = 88
FONT_COLOR = (255, 230, 0)
OUTLINE_COLOR = (0, 0, 0)
BG_COLOR = (10, 10, 20)
INTRO_DURATION = 2.5


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


def _make_intro_frame(topic: str) -> np.ndarray:
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Fond semi-transparent centré
    box_top = HEIGHT // 2 - 200
    box_bot = HEIGHT // 2 + 200
    draw.rounded_rectangle([60, box_top, WIDTH - 60, box_bot], radius=40, fill=(0, 0, 0, 210))

    font = _load_font(64)
    words = topic.split()
    lines, line = [], []
    for word in words:
        test = " ".join(line + [word])
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] > WIDTH - 160:
            lines.append(" ".join(line))
            line = [word]
        else:
            line.append(word)
    if line:
        lines.append(" ".join(line))

    total_h = len(lines) * (64 + 12)
    y = HEIGHT // 2 - total_h // 2

    for line_text in lines:
        bbox = draw.textbbox((0, 0), line_text, font=font)
        x = (WIDTH - (bbox[2] - bbox[0])) // 2
        for dx in [-3, 0, 3]:
            for dy in [-3, 0, 3]:
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), line_text, font=font, fill=(0, 0, 0, 255))
        draw.text((x, y), line_text, font=font, fill=(255, 255, 255, 255))
        y += 64 + 12

    return np.array(img)


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
    music_path: str = None,
    topic: str = "",
) -> str:
    audio = AudioFileClip(audio_path)
    duration = audio.duration

    # Fond vidéo ou fallback dégradé
    if bg_video_path and os.path.exists(bg_video_path):
        try:
            bg = VideoFileClip(bg_video_path, audio=False).subclip(0, duration)
        except Exception:
            bg = _make_fallback_bg(duration)
    else:
        bg = _make_fallback_bg(duration)

    # Overlay sombre léger
    overlay = ColorClip(size=(WIDTH, HEIGHT), color=(0, 0, 0), duration=duration).set_opacity(0.30)

    # Intro animée (titre du sujet)
    intro_clips = []
    if topic:
        try:
            intro_frame = _make_intro_frame(topic)
            intro_clip = (
                ImageClip(intro_frame, ismask=False)
                .set_start(0)
                .set_duration(INTRO_DURATION)
                .set_position("center")
                .crossfadeout(0.6)
            )
            intro_clips = [intro_clip]
        except Exception:
            pass

    # Sous-titres avec animation zoom
    subtitle_clips = []
    for chunk in chunks:
        frame = _make_subtitle_frame(chunk.text)
        try:
            clip = (
                ImageClip(frame, ismask=False)
                .set_start(chunk.start)
                .set_duration(chunk.end - chunk.start)
                .set_position(("center", HEIGHT - 420))
                .resize(lambda t: min(1.0, 0.85 + 0.15 * (t / 0.12)) if t < 0.12 else 1.0)
            )
        except Exception:
            clip = (
                ImageClip(frame, ismask=False)
                .set_start(chunk.start)
                .set_duration(chunk.end - chunk.start)
                .set_position(("center", HEIGHT - 420))
            )
        subtitle_clips.append(clip)

    video = CompositeVideoClip(
        [bg, overlay] + intro_clips + subtitle_clips,
        size=(WIDTH, HEIGHT),
    )

    # Audio : voix + musique de fond
    if music_path and os.path.exists(music_path):
        try:
            music = audio_loop(
                AudioFileClip(music_path).volumex(0.12),
                duration=duration,
            )
            final_audio = CompositeAudioClip([audio, music])
            video = video.set_audio(final_audio)
        except Exception:
            video = video.set_audio(audio)
    else:
        video = video.set_audio(audio)

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

    for path in [bg_video_path, music_path]:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass

    return output_path
