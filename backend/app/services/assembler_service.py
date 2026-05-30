import os
import subprocess
import unicodedata
from app.services.subtitle_service import SubtitleChunk
from typing import List

WIDTH, HEIGHT = 1080, 1920
FPS = 30

FONT_PATHS = [
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/liberation/LiberationSans-Bold.ttf",
]


def _get_font() -> str:
    for p in FONT_PATHS:
        if os.path.exists(p):
            return p
    return ""


def _escape_ffmpeg(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = text.replace("'", " ").replace("’", " ").replace("‘", " ")
    text = text.replace('"', " ").replace(":", " ").replace("%", "pct")
    text = text.replace("[", "").replace("]", "").replace("\\", "").replace("/", " ")
    return text.strip()


def _wrap_text(text: str, max_chars: int = 20) -> list[str]:
    words = text.split()
    lines, line = [], []
    for word in words:
        if sum(len(w) for w in line) + len(line) + len(word) > max_chars:
            if line:
                lines.append(" ".join(line))
            line = [word]
        else:
            line.append(word)
    if line:
        lines.append(" ".join(line))
    return lines[:3]


def _get_audio_duration(audio_path: str) -> float:
    r = subprocess.run([
        "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", audio_path
    ], capture_output=True, text=True, timeout=10)
    try:
        return float(r.stdout.strip())
    except Exception:
        return 60.0


def _build_subtitle_filters(chunks: List[SubtitleChunk], font: str) -> str:
    if not font or not chunks:
        return ""

    filters = []
    FONT_SIZE = 90
    LINE_H = 108

    for chunk in chunks:
        t_start = chunk.start
        t_end = chunk.end
        enable = f"'gte(t\\,{t_start:.3f})*lte(t\\,{t_end:.3f})'"

        lines = _wrap_text(chunk.text, max_chars=24)
        base_y = HEIGHT - 480

        for i, line_text in enumerate(lines):
            escaped = _escape_ffmpeg(line_text)
            if not escaped:
                continue
            y = base_y + i * LINE_H

            # Fond semi-transparent derrière le texte pour lisibilité maximale
            filters.append(
                f"drawtext=fontfile='{font}':text='{escaped}':fontsize={FONT_SIZE}:"
                f"fontcolor=white@0.0:x=(w-tw)/2:y={y}:"
                f"box=1:boxcolor=black@0.55:boxborderw=18:enable={enable}"
            )
            # Contour sombre (4 passes)
            for dx, dy in [(-3, -3), (-3, 3), (3, -3), (3, 3)]:
                filters.append(
                    f"drawtext=fontfile='{font}':text='{escaped}':fontsize={FONT_SIZE}:"
                    f"fontcolor=black@0.9:x=(w-tw)/2+{dx}:y={y+dy}:enable={enable}"
                )
            # Texte jaune vif — couleur signature TikTok
            filters.append(
                f"drawtext=fontfile='{font}':text='{escaped}':fontsize={FONT_SIZE}:"
                f"fontcolor=0xFFE600:x=(w-tw)/2:y={y}:enable={enable}"
            )

    return ",".join(filters)


def assemble_video(
    audio_path: str,
    chunks: List[SubtitleChunk],
    output_path: str,
    bg_video_path: str = None,
) -> str:
    font = _get_font()
    duration = _get_audio_duration(audio_path)

    # 1. Normaliser l'audio — loudnorm -14 LUFS (standard TikTok/YouTube), 192kbps AAC
    audio_norm = output_path.replace(".mp4", "_norm.aac")
    subprocess.run([
        "ffmpeg", "-y", "-i", audio_path,
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
        "-c:a", "aac", "-b:a", "192k",
        "-loglevel", "quiet", audio_norm
    ], capture_output=True, timeout=60)
    audio_to_use = audio_norm if os.path.exists(audio_norm) else audio_path

    # 2. Préparer le fond vidéo — CRF 20, luminosité 80% (lisible sans être sombre)
    bg_tmp = output_path.replace(".mp4", "_bg.mp4")
    if bg_video_path and os.path.exists(bg_video_path):
        subprocess.run([
            "ffmpeg", "-y", "-stream_loop", "-1", "-i", bg_video_path,
            "-t", str(duration + 0.5),
            "-vf", (
                f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
                f"crop={WIDTH}:{HEIGHT},"
                "colorlevels=rimin=0:rimax=0.80:gimin=0:gimax=0.80:bimin=0:bimax=0.80"
            ),
            "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-an",
            "-loglevel", "quiet", bg_tmp
        ], capture_output=True, timeout=120)
    else:
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"color=c=0x080814:size={WIDTH}x{HEIGHT}:rate={FPS}",
            "-t", str(duration + 0.5),
            "-c:v", "libx264", "-preset", "fast", "-loglevel", "quiet", bg_tmp
        ], capture_output=True, timeout=30)

    # 3. Filtres sous-titres drawtext
    vf = _build_subtitle_filters(chunks, font)
    vf = vf if vf else "null"

    # 4. Assemblage final — CRF 18 = haute qualité, +faststart pour streaming web
    cmd = [
        "ffmpeg", "-y",
        "-i", bg_tmp,
        "-i", audio_to_use,
        "-vf", vf,
        "-map", "0:v",
        "-map", "1:a",
        "-t", str(duration),
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        "-loglevel", "warning",
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=300)

    for f in [bg_tmp, audio_norm]:
        try:
            if os.path.exists(f):
                os.remove(f)
        except Exception:
            pass
    if bg_video_path and os.path.exists(bg_video_path):
        try:
            os.remove(bg_video_path)
        except Exception:
            pass

    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg error: {result.stderr.decode()[-300:]}")

    return output_path
