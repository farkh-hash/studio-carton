import os
import subprocess
import unicodedata
from app.services.subtitle_service import SubtitleChunk
from typing import List

WIDTH, HEIGHT = 1080, 1920
FPS = 30

FONT_PATHS = [
    # Linux / Railway (Docker)
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/liberation/LiberationSans-Bold.ttf",
    # Windows (sans caracteres speciaux dans le nom)
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/arial.ttf",
]


def _get_font() -> str:
    for p in FONT_PATHS:
        if os.path.exists(p):
            return p
    return ""


def _escape_ffmpeg(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = text.replace("'", " ").replace("’", " ").replace("‘", " ")
    text = text.replace('"', " ").replace(":", " ").replace("%", " pourcent")
    text = text.replace("[", "").replace("]", "").replace("\\", "").replace("/", " ")
    text = text.replace("€", " euros").replace("$", " dollars")
    # ALL CAPS — style viral TikTok
    return text.upper().strip()


def _wrap_text(text: str, max_chars: int = 16) -> list[str]:
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
    return lines[:2]


def _create_animated_bg(output_path: str, duration: float, topic: str = "") -> None:
    """Fond noir pur — fallback si Pexels indisponible."""
    result = subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c=0x0A0A0A:size={WIDTH}x{HEIGHT}:rate={FPS}",
        "-t", str(duration + 1),
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28", "-an",
        "-loglevel", "error", output_path
    ], capture_output=True, timeout=30)
    if result.returncode != 0:
        print(f"[BG] error: {result.stderr.decode()[-200:]}")


def _prepare_pexels_bg(input_path: str, output_path: str, duration: float) -> bool:
    """Adapte le fond Pexels : scale/crop 9:16, légèrement assombri pour lisibilité."""
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-vf", (
            f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={WIDTH}:{HEIGHT},"
            "eq=brightness=-0.15:saturation=1.1"
        ),
        "-t", str(duration + 1),
        "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-an",
        "-loglevel", "error", output_path
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=60)
    if result.returncode != 0:
        print(f"[BG] Pexels prepare error: {result.stderr.decode()[-200:]}")
    return result.returncode == 0


def _get_audio_duration(audio_path: str) -> float:
    r = subprocess.run([
        "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", audio_path
    ], capture_output=True, text=True, timeout=10)
    try:
        return float(r.stdout.strip())
    except Exception:
        return 60.0


def _sec_to_ass(t: float) -> str:
    """Convertit un temps en secondes vers le format ASS H:MM:SS.cc"""
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    cs = int((t - int(t)) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _generate_ass_subtitles(chunks: List[SubtitleChunk], animated: bool = False) -> str:
    """Génère un fichier ASS. animated=True : effet pop-in mot par mot (fad + scale)."""
    white  = "&H00FFFFFF"
    black  = "&H00000000"
    shadow = "&HAA000000"

    ass = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {WIDTH}
PlayResY: {HEIGHT}
WrapStyle: 1

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,102,{white},{white},{black},{shadow},-1,0,0,0,100,100,2,0,1,8,3,5,80,80,80,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    for chunk in chunks:
        start = _sec_to_ass(chunk.start)
        end = _sec_to_ass(chunk.end)
        text = chunk.text.upper()
        text = text.replace("{", "").replace("}", "").replace("\\", "")
        text = text.replace("'", " ").replace('"', " ")
        if not text.strip():
            continue
        # Effet pop-in: fade rapide + léger scale up à l'apparition
        prefix = r"{\fad(60,20)\t(0,80,\fscx108\fscy108)\t(80,160,\fscx100\fscy100)}" if animated else ""
        ass += f"Dialogue: 0,{start},{end},Default,,0,0,0,,{prefix}{text}\n"

    return ass


def _process_clip_for_scene(input_path: str, output_path: str, duration: float) -> bool:
    """Prépare un clip Pexels pour une scène : scale 9:16, assombri, trimé."""
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-vf", (
            f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={WIDTH}:{HEIGHT},"
            "eq=brightness=-0.1:saturation=1.1"
        ),
        "-t", str(duration),
        "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-an",
        "-loglevel", "error", output_path
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=60)
    return result.returncode == 0


def _create_scene_bg(output_path: str, duration: float) -> None:
    """Fond noir pour une scène (fallback si clip Pexels indisponible)."""
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c=0x0A0A0A:size={WIDTH}x{HEIGHT}:rate={FPS}",
        "-t", str(duration),
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28", "-an",
        "-loglevel", "error", output_path
    ], capture_output=True, timeout=30)


def assemble_storyboard_video(
    scenes: list,
    clip_paths: list,
    audio_path: str,
    subtitle_chunks: List[SubtitleChunk],
    output_path: str,
) -> str:
    """Assemble scène par scène avec clips Pexels spécifiques + sous-titres animés."""
    import tempfile as _tempfile

    font = _get_font()

    # 1. Normaliser l'audio
    audio_norm = output_path.replace(".mp4", "_norm.aac")
    subprocess.run([
        "ffmpeg", "-y", "-i", audio_path,
        "-af", "aresample=44100,loudnorm=I=-14:TP=-1.5:LRA=11",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        "-loglevel", "quiet", audio_norm
    ], capture_output=True, timeout=60)
    audio_to_use = audio_norm if os.path.exists(audio_norm) else audio_path
    total_duration = _get_audio_duration(audio_to_use)

    # 2. Durées proportionnelles au temps audio réel
    declared_total = sum(float(s.get("duration", 2)) for s in scenes) or total_duration
    scale = total_duration / declared_total

    scene_clips = []
    for i, scene in enumerate(scenes):
        scene_dur = round(float(scene.get("duration", 2)) * scale, 3)
        scene_path = output_path.replace(".mp4", f"_s{i}.mp4")
        clip = clip_paths[i] if i < len(clip_paths) else None

        if clip and os.path.exists(clip):
            ok = _process_clip_for_scene(clip, scene_path, scene_dur)
            if not ok:
                _create_scene_bg(scene_path, scene_dur)
        else:
            _create_scene_bg(scene_path, scene_dur)

        if os.path.exists(scene_path):
            scene_clips.append(scene_path)

    if not scene_clips:
        raise RuntimeError("Aucune scène vidéo générée")

    # 3. Concaténer toutes les scènes
    bg_tmp = output_path.replace(".mp4", "_bg.mp4")
    concat_txt = _tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w")
    for p in scene_clips:
        concat_txt.write(f"file '{p.replace(chr(92), '/')}'\n")
    concat_txt.close()

    r = subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", concat_txt.name,
        "-t", str(total_duration),
        "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-an",
        "-loglevel", "error", bg_tmp
    ], capture_output=True, timeout=180)

    try:
        os.remove(concat_txt.name)
    except Exception:
        pass

    if r.returncode != 0:
        raise RuntimeError(f"Scene concat error: {r.stderr.decode()[-200:]}")

    # 4. Sous-titres ASS animés (pop-in mot par mot)
    vf = "null"
    filter_file = None
    if subtitle_chunks and font:
        ass_content = _generate_ass_subtitles(subtitle_chunks, animated=True)
        filter_file = output_path.replace(".mp4", "_subs.ass")
        with open(filter_file, "w", encoding="utf-8") as f:
            f.write(ass_content)
        ass_path = filter_file.replace("\\", "/")
        vf = f"ass='{ass_path}'"

    # 5. Assemblage final vidéo + audio + sous-titres
    cmd = [
        "ffmpeg", "-y",
        "-i", bg_tmp,
        "-i", audio_to_use,
        "-vf", vf,
        "-map", "0:v", "-map", "1:a",
        "-t", str(total_duration),
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        "-loglevel", "warning",
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=300)

    for f in scene_clips + [bg_tmp, audio_norm, filter_file]:
        try:
            if f and os.path.exists(str(f)):
                os.remove(f)
        except Exception:
            pass
    for clip in clip_paths:
        try:
            if clip and os.path.exists(clip):
                os.remove(clip)
        except Exception:
            pass

    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg final error: {result.stderr.decode()[-300:]}")

    return output_path


def _build_subtitle_filters(chunks: List[SubtitleChunk], font: str) -> str:
    """Retourne le filtre ffmpeg pour les sous-titres (vide = pas de sous-titres)."""
    return ""  # Géré séparément via ASS


def assemble_video(
    audio_path: str,
    chunks: List[SubtitleChunk],
    output_path: str,
    bg_video_path: str = None,
    topic: str = "",
) -> str:
    font = _get_font()
    duration = _get_audio_duration(audio_path)

    # 1. Normaliser l'audio — loudnorm -14 LUFS standard TikTok/YouTube, 192kbps
    audio_norm = output_path.replace(".mp4", "_norm.aac")
    subprocess.run([
        "ffmpeg", "-y", "-i", audio_path,
        "-af", "aresample=44100,loudnorm=I=-14:TP=-1.5:LRA=11",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        "-loglevel", "quiet", audio_norm
    ], capture_output=True, timeout=60)
    audio_to_use = audio_norm if os.path.exists(audio_norm) else audio_path

    # 2. Fond vidéo — Pexels si disponible, sinon fond noir animé
    bg_tmp = output_path.replace(".mp4", "_bg.mp4")
    if bg_video_path and os.path.exists(bg_video_path):
        ok = _prepare_pexels_bg(bg_video_path, bg_tmp, duration)
        if not ok:
            _create_animated_bg(bg_tmp, duration, topic=topic)
    else:
        _create_animated_bg(bg_tmp, duration, topic=topic)

    # 3. Générer le fichier de sous-titres ASS
    # Important: utiliser un chemin SANS deux-points pour le filtre ffmpeg
    filter_file = None
    vf = "null"
    if chunks and font:
        ass_content = _generate_ass_subtitles(chunks)
        # Placer le fichier ASS au même endroit que la vidéo (chemin sans C:)
        filter_file = output_path.replace(".mp4", "_subs.ass")
        with open(filter_file, "w", encoding="utf-8") as f:
            f.write(ass_content)
        # Chemin pour ffmpeg : forward slashes, pas de drive letter Windows
        ass_path = filter_file.replace("\\", "/")
        # Sur Windows, /data/... → ffmpeg le résout correctement
        vf = f"ass='{ass_path}'"

    # 4. Assemblage final — CRF 18 haute qualité, faststart pour web
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

    for f in [bg_tmp, audio_norm, filter_file]:
        try:
            if f and os.path.exists(str(f)):
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
