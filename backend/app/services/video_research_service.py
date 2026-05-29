import httpx
import json
import re
import asyncio
from groq import Groq
from app.core.config import settings


async def _google_search(query: str) -> list[dict]:
    """Cherche sur Google et retourne les résultats (titres + snippets)."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0",
        "Accept-Language": "fr-FR,fr;q=0.9",
    }
    url = "https://www.google.com/search"
    params = {"q": query, "num": 8, "hl": "fr"}

    async with httpx.AsyncClient(timeout=12, headers=headers, follow_redirects=True) as client:
        resp = await client.get(url, params=params)
        html = resp.text

    results = []
    # Extraire les titres et snippets
    titles = re.findall(r'<h3[^>]*>(.*?)</h3>', html, re.DOTALL)
    snippets = re.findall(r'<div[^>]*data-sncf[^>]*>(.*?)</div>', html, re.DOTALL)

    for i, title in enumerate(titles[:8]):
        clean_title = re.sub(r'<[^>]+>', '', title).strip()
        if clean_title and len(clean_title) > 10:
            results.append({"title": clean_title, "snippet": ""})

    return results


async def _search_platform(platform: str, query: str) -> list[str]:
    """Cherche du contenu viral sur une plateforme spécifique via Google."""
    platform_queries = {
        "tiktok": f'site:tiktok.com "{query}" OR ({query} viral tiktok)',
        "instagram": f'site:instagram.com "{query}" OR ({query} reels viral)',
        "youtube": f'site:youtube.com shorts "{query}" viral',
        "google": f'{query} viral script contenu 2025',
    }

    q = platform_queries.get(platform, f'{query} viral {platform}')
    results = await _google_search(q)
    return [r["title"] for r in results if r["title"]]


async def _get_youtube_transcript(video_id: str) -> str:
    """Récupère le transcript d'une vidéo YouTube."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        loop = asyncio.get_event_loop()
        transcript_list = await loop.run_in_executor(
            None,
            lambda: YouTubeTranscriptApi.get_transcript(video_id, languages=["fr", "fr-FR", "en"])
        )
        return " ".join(t["text"] for t in transcript_list)[:2000]
    except Exception:
        return ""


async def _get_youtube_videos(query: str, max_results: int = 4) -> list[dict]:
    """Cherche des vidéos YouTube virales."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    url = "https://www.youtube.com/results"
    params = {"search_query": query + " viral", "sp": "EgQQARgC"}

    async with httpx.AsyncClient(timeout=12, headers=headers) as client:
        resp = await client.get(url, params=params)
        html = resp.text

    match = re.search(r'var ytInitialData = ({.*?});</script>', html, re.DOTALL)
    if not match:
        return []

    try:
        data = json.loads(match.group(1))
        contents = (
            data.get("contents", {})
            .get("twoColumnSearchResultsRenderer", {})
            .get("primaryContents", {})
            .get("sectionListRenderer", {})
            .get("contents", [{}])[0]
            .get("itemSectionRenderer", {})
            .get("contents", [])
        )
        videos = []
        for item in contents:
            v = item.get("videoRenderer")
            if not v:
                continue
            vid_id = v.get("videoId", "")
            title = "".join(r.get("text", "") for r in v.get("title", {}).get("runs", []))
            if vid_id and title:
                videos.append({"id": vid_id, "title": title})
            if len(videos) >= max_results:
                break
        return videos
    except Exception:
        return []


async def research_viral_scripts(topic: str) -> dict:
    """
    Recherche multi-plateforme : YouTube (transcripts), TikTok, Instagram, Google.
    Analyse les patterns viraux réels et retourne les insights.
    """
    print(f"[RESEARCH] Recherche multi-plateforme pour: {topic}")

    # Lancer toutes les recherches en parallèle
    yt_videos_task = _get_youtube_videos(topic, max_results=4)
    tiktok_task = _search_platform("tiktok", topic)
    instagram_task = _search_platform("instagram", topic)
    google_task = _search_platform("google", topic)

    yt_videos, tiktok_titles, instagram_titles, google_titles = await asyncio.gather(
        yt_videos_task, tiktok_task, instagram_task, google_task,
        return_exceptions=True
    )

    if isinstance(yt_videos, Exception):
        yt_videos = []
    if isinstance(tiktok_titles, Exception):
        tiktok_titles = []
    if isinstance(instagram_titles, Exception):
        instagram_titles = []
    if isinstance(google_titles, Exception):
        google_titles = []

    print(f"[RESEARCH] YouTube: {len(yt_videos)} vidéos | TikTok: {len(tiktok_titles)} | Instagram: {len(instagram_titles)} | Google: {len(google_titles)}")

    # Extraire transcripts YouTube
    transcripts = []
    for video in yt_videos[:3]:
        if video.get("id"):
            transcript = await _get_youtube_transcript(video["id"])
            if len(transcript) > 100:
                transcripts.append({"title": video["title"], "text": transcript[:1200]})

    # Construire le contexte pour l'analyse
    context_parts = []

    if transcripts:
        context_parts.append("=== SCRIPTS RÉELS YOUTUBE ===")
        for t in transcripts:
            context_parts.append(f"Vidéo: {t['title']}\n{t['text']}")

    if yt_videos:
        context_parts.append("\n=== TITRES VIDÉOS YOUTUBE VIRALES ===")
        context_parts.extend([f"- {v['title']}" for v in yt_videos])

    if tiktok_titles:
        context_parts.append("\n=== CONTENUS TIKTOK VIRAUX ===")
        context_parts.extend([f"- {t}" for t in tiktok_titles[:5]])

    if instagram_titles:
        context_parts.append("\n=== CONTENUS INSTAGRAM REELS ===")
        context_parts.extend([f"- {t}" for t in instagram_titles[:5]])

    if google_titles:
        context_parts.append("\n=== CONTENUS VIRAUX GÉNÉRAUX ===")
        context_parts.extend([f"- {t}" for t in google_titles[:5]])

    full_context = "\n".join(context_parts) if context_parts else "Aucune donnée trouvée."

    # Analyser avec Groq
    client = Groq(api_key=settings.GROQ_API_KEY)

    analysis_prompt = f"""Analyse ces données de contenus viraux réels sur "{topic}" trouvées sur YouTube, TikTok, Instagram et Google.

{full_context}

Extrais les patterns qui font qu'ils cartonnent et retourne un JSON :
{{
  "best_hooks": ["Hook 1 inspiré des vrais contenus viraux", "Hook 2", "Hook 3"],
  "viral_patterns": ["Pattern 1 qui revient sur toutes les plateformes", "Pattern 2", "Pattern 3"],
  "key_facts": ["Fait 1 concret avec chiffre réel", "Fait 2", "Fait 3"],
  "tone": "ton exact qui marche (ex: direct et choquant, storytelling personnel, éducatif rapide)",
  "structure": "structure narrative exacte qui performe",
  "avoided": ["Erreur 1 à éviter absolument", "Erreur 2"]
}}

Base-toi UNIQUEMENT sur les vrais contenus analysés. JSON uniquement."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": analysis_prompt}],
        max_tokens=1000,
        temperature=0.5,
    )

    raw = response.choices[0].message.content.strip()
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        analysis = json.loads(raw.strip())
    except Exception:
        analysis = {"best_hooks": [], "viral_patterns": [], "key_facts": [], "tone": "direct et percutant", "structure": "hook choc + contenu dense + CTA"}

    analysis["videos_found"] = len(yt_videos) + len(tiktok_titles) + len(instagram_titles)
    analysis["transcripts_extracted"] = len(transcripts)
    return analysis
