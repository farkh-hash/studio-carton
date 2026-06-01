import os
import asyncio
import httpx
import tempfile
import subprocess
from app.core.config import settings

PEXELS_VIDEO_API = "https://api.pexels.com/videos/search"


def _get_english_keywords(topic: str) -> str:
    try:
        from app.services.groq_client import chat as groq_chat
        return groq_chat(
            messages=[{"role": "user", "content": f"Extract 3 simple English keywords for a Pexels video search about: '{topic}'. Return ONLY the keywords separated by spaces, nothing else."}],
            max_tokens=20,
            temperature=0.3,
        )
    except Exception:
        return "lifestyle motivation success"


def _process_clip_ffmpeg(input_path: str, output_path: str, width: int = 1080, height: int = 1920) -> bool:
    """Utilise ffmpeg pour crop + resize un clip en 9:16."""
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-vf", f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
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
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-vf", f"scale=1080:1920,fade=t=in:st=0:d=0.5,fade=t=out:st={max(0, duration-0.8)}:d=0.5",
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


async def fetch_character_clips(character: str, topic_keywords: str) -> str | None:
    """Télécharge un clip d'un personnage qui parle pour le scénario."""
    if not settings.PEXELS_API_KEY:
        return None

    # Chercher des clips de personnes qui parlent selon le personnage
    gender_query = "man talking camera" if character == "ALEX" else "woman talking camera"
    queries = [
        f"{gender_query} {topic_keywords}",
        gender_query,
        "person talking camera",
    ]

    headers = {"Authorization": settings.PEXELS_API_KEY}

    async with httpx.AsyncClient(timeout=20) as client:
        for query in queries:
            try:
                params = {"query": query, "per_page": 5, "size": "small", "orientation": "portrait"}
                resp = await client.get(PEXELS_VIDEO_API, headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()
                videos = data.get("videos", [])
                if not videos:
                    continue

                # Prendre la première vidéo disponible
                video = videos[0]
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

                async with httpx.AsyncClient(timeout=60, follow_redirects=True) as dl:
                    r = await dl.get(url)
                    r.raise_for_status()
                    import tempfile
                    tmp = tempfile.NamedTemporaryFile(suffix=f"_{character}.mp4", delete=False)
                    tmp.write(r.content)
                    tmp.close()
                    return tmp.name
            except Exception:
                continue
    return None


async def fetch_clips_for_scenes(scenes: list) -> list:
    """Fetche un clip Pexels par scène. Retourne une liste (None si échec)."""
    from app.core.config import settings
    if not settings.PEXELS_API_KEY:
        return [None] * len(scenes)

    headers = {"Authorization": settings.PEXELS_API_KEY}

    async def _fetch_one(scene: dict, idx: int):
        query = scene.get("pexels_query", "lifestyle motivation success")
        params = {"query": query, "per_page": 3, "size": "small", "orientation": "portrait"}
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(PEXELS_VIDEO_API, headers=headers, params=params)
                resp.raise_for_status()
                videos = resp.json().get("videos", [])
                if not videos:
                    return None
                files = videos[0].get("video_files", [])
                sd = [f for f in files if f.get("width", 9999) <= 1280] or files
                if not sd:
                    return None
                url = min(sd, key=lambda f: f.get("width", 9999)).get("link", "")
                if not url:
                    return None
                async with httpx.AsyncClient(timeout=30, follow_redirects=True) as dl:
                    r = await dl.get(url)
                    r.raise_for_status()
                    tmp = tempfile.NamedTemporaryFile(suffix=f"_scene{idx}.mp4", delete=False)
                    tmp.write(r.content)
                    tmp.close()
                    return tmp.name
        except Exception as e:
            print(f"[BG] Scène {idx} clip failed: {e}")
            return None

    return list(await asyncio.gather(*[_fetch_one(s, i) for i, s in enumerate(scenes)]))


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
