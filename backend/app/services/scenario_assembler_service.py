import os
import tempfile
import subprocess
import aiofiles
from PIL import Image, ImageDraw, ImageFont
import numpy as np

WIDTH, HEIGHT = 1080, 1920
FPS = 30
BG_COLOR = "0f0f19"

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


def _make_combined_audio(segment_files: list[str], durations: list[float], output_path: str) -> bool:
    """Concatene tous les audios en un seul fichier avec des silences entre."""
    concat_list = tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w")
    for i, (f, dur) in enumerate(zip(segment_files, durations)):
        concat_list.write(f"file '{f}'\n")
        # Ajouter 0.25s de silence entre les répliques
        silence_path = f.replace(".mp3", "_silence.mp3")
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
            "-t", "0.25", "-acodec", "libmp3lame", silence_path
        ], capture_output=True)
        concat_list.write(f"file '{silence_path}'\n")
    concat_list.close()

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", concat_list.name,
        "-acodec", "libmp3lame", "-q:a", "2",
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=60)
    try:
        os.remove(concat_list.name)
    except Exception:
        pass
    return result.returncode == 0


def _make_subtitle_image(character: str, line: str, emotion: str) -> str:
    """Crée une image PNG pour les sous-titres d'un personnage."""
    img = Image.new("RGBA", (WIDTH, 380), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    color = CHARACTER_COLORS.get(character, (255, 255, 255))
    font_name = _load_font(42)
    font_line = _load_font(66)

    # Fond
    draw.rounded_rectangle([20, 5, WIDTH - 20, 375], radius=20, fill=(0, 0, 0, 210))
    draw.rounded_rectangle([20, 5, 34, 375], radius=10, fill=(*color, 255))

    # Nom
    name_text = f"  {character}"
    if emotion:
        name_text += f"  •  {emotion}"
    draw.text((50, 18), name_text, font=font_name, fill=(*color, 255))

    # Ligne avec wrap
    words = line.split()
    lines_out, buf = [], []
    for word in words:
        test = " ".join(buf + [word])
        bbox = draw.textbbox((0, 0), test, font=font_line)
        if bbox[2] > WIDTH - 80:
            lines_out.append(" ".join(buf))
            buf = [word]
        else:
            buf.append(word)
    if buf:
        lines_out.append(" ".join(buf))

    total_h = len(lines_out) * (66 + 8)
    y = 68 + max(0, (280 - total_h) // 2)
    for lt in lines_out:
        bbox = draw.textbbox((0, 0), lt, font=font_line)
        x = (WIDTH - (bbox[2] - bbox[0])) // 2
        for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
            draw.text((x + dx, y + dy), lt, font=font_line, fill=(0, 0, 0, 255))
        draw.text((x, y), lt, font=font_line, fill=(255, 255, 255, 255))
        y += 66 + 8

    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp.close()
    img.save(tmp.name)
    return tmp.name


def assemble_scenario(
    segments: list[dict],
    output_path: str,
    bg_video_path: str = None,
    music_path: str = None,
    character_clips: dict = None,
) -> str:
    """
    Assemble le scénario via ffmpeg pur — rapide et fiable.
    Pas de MoviePy pour éviter les timeouts.
    """
    if not segments:
        raise ValueError("Aucun segment audio")

    # 1. Sauvegarder les audios
    segment_files = []
    durations = []
    for i, seg in enumerate(segments):
        tmp = tempfile.NamedTemporaryFile(suffix=f"_seg{i}.mp3", delete=False)
        tmp.write(seg["audio_bytes"])
        tmp.close()
        segment_files.append(tmp.name)

        # Mesurer la durée avec ffprobe
        try:
            r = subprocess.run([
                "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", tmp.name
            ], capture_output=True, text=True, timeout=10)
            dur = float(r.stdout.strip() or "3.0")
        except Exception:
            dur = len(seg.get("line", "").split()) / 2.5
        durations.append(dur)

    total_duration = sum(durations) + len(durations) * 0.25

    # 2. Concatener tous les audios
    combined_audio = output_path.replace(".mp4", "_audio.mp3")
    if not _make_combined_audio(segment_files, durations, combined_audio):
        raise RuntimeError("Erreur concatenation audio")

    # 3. Créer le fond
    if bg_video_path and os.path.exists(bg_video_path):
        # Boucler le fond pour couvrir la durée
        bg_final = output_path.replace(".mp4", "_bg.mp4")
        subprocess.run([
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", bg_video_path,
            "-t", str(total_duration + 1),
            "-vf", f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,crop={WIDTH}:{HEIGHT},colorlevels=rimin=0:rimax=0.7:gimin=0:gimax=0.7:bimin=0:bimax=0.7",
            "-c:v", "libx264", "-preset", "fast", "-crf", "28", "-an",
            bg_final
        ], capture_output=True, timeout=120)
    else:
        bg_final = output_path.replace(".mp4", "_bg.mp4")
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color=c=#{BG_COLOR}:size={WIDTH}x{HEIGHT}:rate={FPS}",
            "-t", str(total_duration + 1),
            "-c:v", "libx264", "-preset", "fast",
            bg_final
        ], capture_output=True, timeout=30)

    # 4. Construire les filtres de sous-titres avec ffmpeg drawtext
    # Créer des images PNG pour chaque réplique et les superposer
    subtitle_images = []
    t = 0.0
    overlay_filters = []
    inputs = ["-i", bg_final, "-i", combined_audio]

    for i, (seg, dur) in enumerate(zip(segments, durations)):
        img_path = _make_subtitle_image(
            seg.get("character", "ALEX"),
            seg.get("line", ""),
            seg.get("emotion", "")
        )
        subtitle_images.append(img_path)
        inputs.extend(["-i", img_path])
        t_end = t + dur
        overlay_filters.append((i + 2, t, t_end))
        t += dur + 0.25

    # Construire le filter_complex
    filter_parts = ["[0:v]colorlevels=rimin=0:rimax=1[bg]"]
    prev = "bg"
    for idx, (inp_idx, t_start, t_end) in enumerate(overlay_filters):
        out_label = f"v{idx}"
        y_pos = HEIGHT - 400
        filter_parts.append(
            f"[{prev}][{inp_idx}:v]overlay=x=(W-w)/2:y={y_pos}:enable='between(t,{t_start:.3f},{t_end:.3f})'[{out_label}]"
        )
        prev = out_label

    filter_complex = ";".join(filter_parts)

    # 5. Assembler avec ffmpeg
    cmd = (
        ["ffmpeg", "-y"]
        + inputs
        + [
            "-filter_complex", filter_complex,
            "-map", f"[{prev}]",
            "-map", "1:a",
            "-t", str(total_duration),
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            output_path
        ]
    )

    result = subprocess.run(cmd, capture_output=True, timeout=300)

    # Nettoyage
    for f in segment_files + subtitle_images:
        try:
            os.remove(f)
        except Exception:
            pass
    for f in [combined_audio, bg_final]:
        try:
            os.remove(f)
        except Exception:
            pass
    # Silences
    for f in segment_files:
        silence = f.replace(".mp3", "_silence.mp3")
        try:
            os.remove(silence)
        except Exception:
            pass

    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg error: {result.stderr.decode()[-500:]}")

    return output_path
