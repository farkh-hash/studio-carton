import os
import tempfile
import subprocess
import re

WIDTH, HEIGHT = 1080, 1920
FPS = 30

CHARACTER_COLORS_HEX = {
    "ALEX": "6ea5fa",
    "SARAH": "f472b6",
}

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


def _escape_text(text: str) -> str:
    """Simplifie le texte pour ffmpeg drawtext — supprime les caractères problématiques."""
    import unicodedata
    # Normaliser les accents
    text = unicodedata.normalize("NFC", text)
    # Remplacer apostrophes typographiques
    text = text.replace("’", " ").replace("‘", " ").replace("'", " ")
    text = text.replace('"', ' ').replace(':', ' ').replace('%', ' ')
    text = text.replace('[', '').replace(']', '').replace('\\', '')
    return text.strip()


def _wrap_text(text: str, max_chars: int = 28) -> list[str]:
    """Découpe le texte en lignes pour le rendu."""
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
    return lines[:3]  # max 3 lignes


def _concat_audios(segment_files: list[str], durations: list[float]) -> tuple[str, float]:
    """Concatene les audios avec silences entre les répliques."""
    PAUSE = 0.3
    concat_list = tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w")
    silence_files = []

    for f in segment_files:
        concat_list.write(f"file '{f}'\n")
        sil = f.replace(".mp3", "_sil.mp3")
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
            "-t", str(PAUSE), "-acodec", "libmp3lame", "-loglevel", "quiet", sil
        ], capture_output=True, timeout=10)
        concat_list.write(f"file '{sil}'\n")
        silence_files.append(sil)

    concat_list.close()
    out = tempfile.NamedTemporaryFile(suffix="_combined.mp3", delete=False)
    out.close()

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list.name, "-acodec", "libmp3lame",
        "-loglevel", "quiet", out.name
    ], capture_output=True, timeout=60)

    os.remove(concat_list.name)
    for f in silence_files:
        try:
            os.remove(f)
        except Exception:
            pass

    # Mesurer durée totale
    r = subprocess.run([
        "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", out.name
    ], capture_output=True, text=True, timeout=10)
    total = float(r.stdout.strip() or sum(durations) + len(durations) * 0.3)

    return out.name, total


def _build_drawtext_filters(segments: list[dict], durations: list[float]) -> str:
    """Construit le filtre drawtext pour tous les dialogues."""
    font = _get_font()
    PAUSE = 0.3
    filters = []
    t = 0.0

    for seg, dur in zip(segments, durations):
        char = seg.get("character", "ALEX")
        line = seg.get("line", "").strip()
        emotion = seg.get("emotion", "")
        color = CHARACTER_COLORS_HEX.get(char, "ffffff")
        t_end = t + dur

        if not line:
            t += dur + PAUSE
            continue

        # Utiliser gte*lte au lieu de between() pour eviter les virgules
        enable = f"'gte(t\\,{t:.3f})*lte(t\\,{t_end:.3f})'"

        # Badge nom du personnage
        name_text = _escape_text(f"{char}" + (f"  |  {emotion}" if emotion else ""))
        badge_y = HEIGHT - 440
        filters.append(
            f"drawtext=fontfile='{font}':text='{name_text}':fontsize=38:"
            f"fontcolor={color}:x=60:y={badge_y}:"
            f"box=1:boxcolor=black@0.8:boxborderw=12:"
            f"enable={enable}"
        )

        # Lignes de dialogue
        lines = _wrap_text(line, max_chars=25)
        line_y = HEIGHT - 390
        for i, ln in enumerate(lines):
            escaped = _escape_text(ln)
            y = line_y + i * 76
            # Contour
            for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
                filters.append(
                    f"drawtext=fontfile='{font}':text='{escaped}':fontsize=68:"
                    f"fontcolor=black:x=(w-tw)/2+{dx}:y={y+dy}:"
                    f"enable={enable}"
                )
            # Texte blanc
            filters.append(
                f"drawtext=fontfile='{font}':text='{escaped}':fontsize=68:"
                f"fontcolor=white:x=(w-tw)/2:y={y}:"
                f"enable={enable}"
            )

        t += dur + PAUSE

    return ",".join(filters)


def assemble_scenario(
    segments: list[dict],
    output_path: str,
    bg_video_path: str = None,
    music_path: str = None,
    character_clips: dict = None,
) -> str:
    """
    100% ffmpeg — rapide, fiable, pas de MoviePy.
    """
    if not segments:
        raise ValueError("Aucun segment audio")

    # 1. Mesurer durées audio
    segment_files = []
    durations = []
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

    # 2. Concatener les audios
    combined_audio, total_duration = _concat_audios(segment_files, durations)

    # 3. Créer le fond vidéo
    bg_tmp = output_path.replace(".mp4", "_bg.mp4")
    if bg_video_path and os.path.exists(bg_video_path):
        subprocess.run([
            "ffmpeg", "-y", "-stream_loop", "-1", "-i", bg_video_path,
            "-t", str(total_duration + 0.5),
            "-vf", f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,crop={WIDTH}:{HEIGHT},"
                   "colorlevels=rimin=0:rimax=0.65:gimin=0:gimax=0.65:bimin=0:bimax=0.65",
            "-c:v", "libx264", "-preset", "fast", "-crf", "28", "-an",
            "-loglevel", "quiet", bg_tmp
        ], capture_output=True, timeout=120)
    else:
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"color=c=0x0f0f19:size={WIDTH}x{HEIGHT}:rate={FPS}",
            "-t", str(total_duration + 0.5),
            "-c:v", "libx264", "-preset", "fast",
            "-loglevel", "quiet", bg_tmp
        ], capture_output=True, timeout=30)

    # 4. Construire les filtres drawtext
    vf = _build_drawtext_filters(segments, durations)
    if not vf:
        vf = "null"

    # 5. Assembler le tout
    cmd = [
        "ffmpeg", "-y",
        "-i", bg_tmp,
        "-i", combined_audio,
        "-vf", vf,
        "-map", "0:v",
        "-map", "1:a",
        "-t", str(total_duration),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-loglevel", "warning",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, timeout=180)

    # Nettoyage
    for f in segment_files + [combined_audio, bg_tmp]:
        try:
            os.remove(f)
        except Exception:
            pass

    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg error: {result.stderr.decode()[-300:]}")

    return output_path
