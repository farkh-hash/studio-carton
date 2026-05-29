import os
import httpx
import tempfile
from groq import Groq
from app.core.config import settings

PEXELS_VIDEO_API = "https://api.pexels.com/videos/search"


def _get_english_keywords(topic: str) -> str:
    """Utilise Groq pour extraire 3 mots-clés anglais depuis le sujet."""
    try:
        client = Groq(api_key=settings.GROQ_API_KEY)
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{
                "role": "user",
                "content": f"Extract 3 simple English keywords for a Pexels video search about: '{topic}'. Return ONLY the keywords separated by spaces, nothing else. Example: 'morning routine sunrise'"
            }],
            max_tokens=20,
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return "lifestyle motivation success"


async def fetch_background_clips(topic: str, duration: int) -> list[str]:
    """Télécharge des clips vidéo Pexels liés au sujet. Retourne les chemins des fichiers."""
    keywords = _get_english_keywords(topic)

    headers = {"Authorization": settings.PEXELS_API_KEY}
    params = {"query": keywords, "per_page": 8, "size": "small"}

    print(f"[PEXELS] Searching: '{keywords}' | key={settings.PEXELS_API_KEY[:8]}...")
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(PEXELS_VIDEO_API, headers=headers, params=params)
        print(f"[PEXELS] API status: {resp.status_code}")
        resp.raise_for_status()
        data = resp.json()

    videos = data.get("videos", [])
    print(f"[PEXELS] Videos found: {len(videos)}")
    if not videos:
        return []

    clips_needed = max(1, duration // 10)
    selected = (videos * 10)[:clips_needed]

    paths = []
    async with httpx.AsyncClient(timeout=90, follow_redirects=True) as client:
        for i, video in enumerate(selected):
            # Prendre le fichier SD (plus léger, plus rapide à télécharger)
            files = video.get("video_files", [])
            sd_files = [f for f in files if f.get("quality") in ("sd", "hd") and f.get("width", 9999) <= 1280]
            if not sd_files:
                sd_files = files
            if not sd_files:
                continue

            # Prendre le plus petit fichier disponible
            chosen = min(sd_files, key=lambda f: f.get("width", 9999))
            url = chosen.get("link", "")
            if not url:
                continue

            try:
                tmp = tempfile.NamedTemporaryFile(suffix=f"_bg_{i}.mp4", delete=False)
                tmp.close()
                print(f"[PEXELS] Downloading clip {i}: {url[:60]}...")
                r = await client.get(url)
                r.raise_for_status()
                with open(tmp.name, "wb") as f:
                    f.write(r.content)
                print(f"[PEXELS] Clip {i} downloaded: {len(r.content)} bytes")
                paths.append(tmp.name)
            except Exception as e:
                print(f"[PEXELS] Clip {i} download failed: {e}")
                continue

    return paths
