import os
import httpx
import asyncio
import tempfile
from app.core.config import settings

PEXELS_API = "https://api.pexels.com/videos/search"


async def fetch_background_clips(topic: str, duration: int) -> list[str]:
    """Télécharge des clips vidéo Pexels liés au sujet. Retourne les chemins des fichiers."""
    headers = {"Authorization": settings.PEXELS_API_KEY}
    params = {"query": topic, "per_page": 5, "orientation": "portrait", "size": "medium"}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(PEXELS_API, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()

    videos = data.get("videos", [])
    if not videos:
        return []

    clips_needed = max(1, duration // 10)
    selected = (videos * 10)[:clips_needed]

    paths = []
    async with httpx.AsyncClient(timeout=60) as client:
        for i, video in enumerate(selected):
            # Prendre le fichier HD portrait (le plus proche de 1080p)
            files = sorted(
                [f for f in video["video_files"] if f.get("width") and f["width"] <= 1080],
                key=lambda f: f.get("width", 0),
                reverse=True,
            )
            if not files:
                files = video["video_files"][:1]
            if not files:
                continue

            url = files[0]["link"]
            tmp = tempfile.NamedTemporaryFile(suffix=f"_bg_{i}.mp4", delete=False)
            tmp.close()

            r = await client.get(url, follow_redirects=True)
            with open(tmp.name, "wb") as f:
                f.write(r.content)
            paths.append(tmp.name)

    return paths
