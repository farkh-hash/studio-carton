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


def _get_niche_color(topic: str) -> tuple[str, str]:
    """Retourne (couleur_base, couleur_vive) selon la niche."""
    t = topic.lower()
    if any(w in t for w in ["finance", "argent", "invest", "bourse", "riche", "patrimoine", "crypto", "trading"]):
        return "0x0A1628", "0x1E5FA0"   # Bleu foncé / bleu vif
    if any(w in t for w in ["santé", "sante", "sport", "fitness", "maigrir", "nutrition", "regime"]):
        return "0x081A0A", "0x1A7A30"   # Vert foncé / vert vif
    if any(w in t for w in ["ia", "tech", "intelligence", "robot", "ai", "digital", "code", "app"]):
        return "0x10082A", "0x6020C0"   # Violet foncé / violet vif
    if any(w in t for w in ["amour", "relation", "psycho", "mental", "confiance"]):
        return "0x1A040C", "0xA0184A"   # Rouge foncé / rouge vif
    if any(w in t for w in ["business", "entrepreneur", "startup", "vente", "marketing"]):
        return "0x160E02", "0xC07010"   # Ambre foncé / or vif
    return "0x0C0820", "0x5020A0"       # Violet foncé / violet vif — défaut


def _create_animated_bg(output_path: str, duration: float, topic: str = "") -> None:
    """Fond animé avec rotation de teinte — donne de la vie sans être lent."""
    base, vivid = _get_niche_color(topic)
    h3 = HEIGHT // 3

    result = subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c={base}:size={WIDTH}x{HEIGHT}:rate={FPS}",
        "-t", str(duration + 1),
        "-vf", (
            # Gradient : couleur vive en haut, transition vers le bas
            f"drawbox=x=0:y=0:w={WIDTH}:h={h3}:color={vivid}@0.85:t=fill,"
            f"drawbox=x=0:y={h3}:w={WIDTH}:h={h3}:color={vivid}@0.35:t=fill,"
            # Rotation de teinte lente — crée du mouvement sans slowdown
            "hue=H='0.4*t':s=1.5"
        ),
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "24", "-an",
        "-loglevel", "error", output_path
    ], capture_output=True, timeout=60)
    if result.returncode != 0:
        print(f"[BG] error: {result.stderr.decode()[-200:]}")


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


def _generate_ass_subtitles(chunks: List[SubtitleChunk]) -> str:
    """Génère un fichier ASS avec les sous-titres stylés (jaune, gras, contour noir)."""
    # Style viral : jaune #FFE600, gros, contour noir épais
    # Couleurs ASS format &HAABBGGRR (alpha, blue, green, red)
    yellow = "&H0000E6FF"   # #FFE600 en ABGR
    black  = "&H00000000"
    shadow = "&H80000000"   # noir semi-transparent

    ass = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {WIDTH}
PlayResY: {HEIGHT}
WrapStyle: 1

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,88,{yellow},{yellow},{black},{shadow},-1,0,0,0,100,100,0,0,1,5,1,2,60,60,200,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    for chunk in chunks:
        start = _sec_to_ass(chunk.start)
        end = _sec_to_ass(chunk.end)
        # Texte clean (uppercase, sans caractères spéciaux ASS)
        text = chunk.text.upper()
        text = text.replace("{", "").replace("}", "").replace("\\", "")
        text = text.replace("'", " ").replace('"', " ")
        if text.strip():
            ass += f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n"

    return ass


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

    # 2. Fond animé professionnel — niche-aware, zéro stock footage générique
    bg_tmp = output_path.replace(".mp4", "_bg.mp4")
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
