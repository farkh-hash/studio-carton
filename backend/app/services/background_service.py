import os
import httpx
import tempfile
import subprocess
from groq import Groq
from app.core.config import settings

PEXELS_VIDEO_API = "https://api.pexels.com/videos/search"


def _get_english_keywords(topic: str) -> str:
    try:
        client = Groq(api_key=settings.GROQ_API_KEY)
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": f"Extract 3 simple English keywords for a Pexels video search about: '{topic}'. Return ONLY the keywords separated by spaces, nothing else."}],
            max_tokens=20,
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return "lifestyle motivation success"


def _process_clip_ffmpeg(input_path: str, output_path: str, width: int = 1080, height: int = 1920) -> bool:
    """Utilise ffmpeg pour crop + resize un clip en 9:16."""
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-vf", f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "28",
        "-an", output_path
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=60)
    return result.returncode == 0


def build_background_video(clip_paths: list[str], duration: float, output_path: str) -> bool:
    """Assemble les clips en une seule vidéo de fond 9:16 avec ffmpeg."""
    if not clip_paths:
        return False

    processed = []
    for i, path in enumerate(clip_paths):
        out = path.replace(".mp4", "_proc.mp4")
        if _process_clip_ffmpeg(path, out):
            processed.append(out)

    if not processed:
        return False

    # Créer un fichier concat
    concat_file = tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w")
    # Répéter les clips pour couvrir la durée
    total = 0
    lines = []
    while total < duration:
        for p in processed:
            lines.append(f"file '{p}'\n")
            # durée approximative par clip
            total += 10
            if total >= duration:
                break
    concat_file.write("".join(lines))
    concat_file.close()

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", concat_file.name,
        "-t", str(duration),
        "-c:v", "libx264", "-preset", "fast", "-crf", "26",
        "-vf", f"scale=1080:1920,fade=t=in:st=0:d=0.8,fade=t=out:st={max(0, duration-1.2)}:d=0.8",
        "-an", output_path
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=120)

    # Nettoyage
    try:
        os.remove(concat_file.name)
        for p in processed:
            os.remove(p)
    except Exception:
        pass

    return result.returncode == 0


async def fetch_background_clips(topic: str, duration: int) -> list[str]:
    keywords = _get_english_keywords(topic)
    headers = {"Authorization": settings.PEXELS_API_KEY}
    params = {"query": keywords, "per_page": 8, "size": "small"}

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(PEXELS_VIDEO_API, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()

    videos = data.get("videos", [])
    if not videos:
        return []

    clips_needed = max(2, duration // 10)
    selected = (videos * 5)[:clips_needed]

    paths = []
    async with httpx.AsyncClient(timeout=90, follow_redirects=True) as client:
        for i, video in enumerate(selected):
            files = video.get("video_files", [])
            sd_files = [f for f in files if f.get("width", 9999) <= 1280]
            if not sd_files:
                sd_files = files
            if not sd_files:
                continue
            chosen = min(sd_files, key=lambda f: f.get("width", 9999))
            url = chosen.get("link", "")
            if not url:
                continue
            try:
                tmp = tempfile.NamedTemporaryFile(suffix=f"_bg_{i}.mp4", delete=False)
                tmp.close()
                r = await client.get(url)
                r.raise_for_status()
                with open(tmp.name, "wb") as f:
                    f.write(r.content)
                paths.append(tmp.name)
            except Exception:
                continue

    return paths
