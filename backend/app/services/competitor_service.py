import httpx
import asyncio
import json
from app.core.config import settings

YOUTUBE_API = "https://www.googleapis.com/youtube/v3"


async def _get_top_channels(topic: str) -> list[dict]:
    """Cherche les chaînes qui cartonnent sur ce sujet via YouTube API."""
    params = {
        "part": "snippet",
        "q": topic,
        "type": "channel",
        "order": "relevance",
        "maxResults": 8,
        "relevanceLanguage": "fr",
        "key": settings.YOUTUBE_API_KEY,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{YOUTUBE_API}/search", params=params)
        resp.raise_for_status()
        data = resp.json()

    channels = []
    for item in data.get("items", []):
        snippet = item.get("snippet", {})
        channel_id = item.get("id", {}).get("channelId", "")
        channels.append({
            "id": channel_id,
            "name": snippet.get("channelTitle", ""),
            "description": snippet.get("description", "")[:200],
        })
    return channels


async def _get_channel_top_videos(channel_id: str, max_results: int = 5) -> list[dict]:
    """Récupère les vidéos les plus vues d'une chaîne."""
    params = {
        "part": "snippet,statistics",
        "channelId": channel_id,
        "order": "viewCount",
        "maxResults": max_results,
        "type": "video",
        "key": settings.YOUTUBE_API_KEY,
    }
    async with httpx.AsyncClient(timeout=12) as client:
        resp = await client.get(f"{YOUTUBE_API}/search", params=params)
        resp.raise_for_status()
        data = resp.json()

    videos = []
    for item in data.get("items", []):
        snippet = item.get("snippet", {})
        videos.append({
            "title": snippet.get("title", ""),
            "description": snippet.get("description", "")[:150],
        })
    return videos


async def analyze_competitors(topic: str) -> dict:
    """
    Analyse les concurrents qui cartonnent sur le sujet.
    Extrait leurs patterns de succès.
    """
    print(f"[COMPETITORS] Analyse concurrents pour: {topic}")

    try:
        channels = await _get_top_channels(topic)
        print(f"[COMPETITORS] {len(channels)} chaînes trouvées")
    except Exception as e:
        print(f"[COMPETITORS] Erreur: {e}")
        return {}

    # Récupérer les vidéos des 3 premières chaînes en parallèle
    tasks = [_get_channel_top_videos(ch["id"], 3) for ch in channels[:3]]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    competitor_data = []
    for i, (channel, videos) in enumerate(zip(channels[:3], results)):
        if not isinstance(videos, Exception) and videos:
            competitor_data.append({
                "channel": channel["name"],
                "description": channel["description"],
                "top_videos": videos,
            })

    if not competitor_data:
        return {}

    # Analyse Groq des patterns des concurrents
    from app.services.groq_client import chat as groq_chat
    context = json.dumps(competitor_data, ensure_ascii=False, indent=2)

    prompt = f"""Analyse ces chaînes concurrentes qui cartonnent sur le sujet "{topic}".

{context[:2500]}

Identifie leurs patterns de succès communs et retourne un JSON :
{{
  "successful_title_patterns": [
    "Pattern de titre 1 qui revient",
    "Pattern 2",
    "Pattern 3"
  ],
  "content_angle": "L'angle éditorial dominant qui différencie ces chaînes",
  "hook_patterns": [
    "Pattern de hook identifié dans leurs titres 1",
    "Pattern 2"
  ],
  "gap_opportunity": "Ce que PERSONNE ne fait encore sur ce sujet (opportunité à saisir)",
  "differentiation": "Comment se différencier de ces concurrents pour se démarquer"
}}

JSON uniquement."""

    raw = groq_chat(messages=[{"role": "user", "content": prompt}], max_tokens=700, temperature=0.5)
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        analysis = json.loads(raw.strip())
    except Exception:
        analysis = {}

    analysis["channels_analyzed"] = len(competitor_data)
    return analysis
