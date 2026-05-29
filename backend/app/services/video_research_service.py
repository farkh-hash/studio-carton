import httpx
import json
import re
import asyncio
from groq import Groq
from app.core.config import settings


async def _search_youtube_videos(query: str, max_results: int = 5) -> list[dict]:
    """Cherche des vidéos YouTube virales sans API key."""
    search_url = "https://www.youtube.com/results"
    params = {"search_query": query + " shorts viral", "sp": "EgQQARgC"}  # filtre Shorts

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "fr-FR,fr;q=0.9",
    }

    async with httpx.AsyncClient(timeout=15, headers=headers) as client:
        resp = await client.get(search_url, params=params)
        html = resp.text

    # Extraire les données JSON de YouTube
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
        for item in contents[:max_results * 3]:
            video = item.get("videoRenderer")
            if not video:
                continue
            video_id = video.get("videoId", "")
            title = "".join(r.get("text", "") for r in video.get("title", {}).get("runs", []))
            views_text = video.get("viewCountText", {}).get("simpleText", "")
            videos.append({"id": video_id, "title": title, "views": views_text})
            if len(videos) >= max_results:
                break

        return videos
    except Exception:
        return []


async def _get_transcript(video_id: str) -> str:
    """Récupère le transcript d'une vidéo YouTube."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        loop = asyncio.get_event_loop()
        transcript_list = await loop.run_in_executor(
            None,
            lambda: YouTubeTranscriptApi.get_transcript(video_id, languages=["fr", "fr-FR", "en"])
        )
        text = " ".join(t["text"] for t in transcript_list)
        return text[:3000]  # Limiter à 3000 chars
    except Exception:
        return ""


async def research_viral_scripts(topic: str) -> dict:
    """
    Cherche les vraies vidéos virales sur le sujet,
    extrait leurs scripts et analyse les patterns.
    """
    print(f"[RESEARCH] Recherche YouTube pour: {topic}")

    # Chercher des vidéos en français et en anglais
    queries = [
        topic,
        topic + " comment faire",
        topic.replace("l'", "").replace("le ", "").replace("la ", ""),
    ]

    all_videos = []
    for query in queries[:2]:
        videos = await _search_youtube_videos(query, max_results=3)
        all_videos.extend(videos)

    print(f"[RESEARCH] {len(all_videos)} vidéos trouvées")

    # Extraire les transcripts
    transcripts = []
    for video in all_videos[:4]:
        if video["id"]:
            transcript = await _get_transcript(video["id"])
            if len(transcript) > 100:
                transcripts.append({
                    "title": video["title"],
                    "transcript": transcript[:1500],
                })
            if len(transcripts) >= 3:
                break

    print(f"[RESEARCH] {len(transcripts)} transcripts extraits")

    # Si pas de transcripts, utiliser juste les titres
    if not transcripts and all_videos:
        titles = [v["title"] for v in all_videos[:5] if v["title"]]
        transcripts_context = "Titres des vidéos virales trouvées:\n" + "\n".join(f"- {t}" for t in titles)
    elif transcripts:
        transcripts_context = "\n\n".join(
            f"VIDÉO: {t['title']}\nSCRIPT:\n{t['transcript']}"
            for t in transcripts
        )
    else:
        transcripts_context = "Aucune vidéo trouvée."

    # Analyser avec Groq
    client = Groq(api_key=settings.GROQ_API_KEY)

    analysis_prompt = f"""Analyse ces vraies vidéos virales YouTube sur le sujet "{topic}" et extrais les patterns qui font qu'elles fonctionnent.

{transcripts_context}

Retourne un JSON avec :
{{
  "best_hooks": ["hook 1 extrait ou inspiré des vrais scripts", "hook 2", "hook 3"],
  "viral_patterns": ["Pattern 1 qui revient", "Pattern 2", "Pattern 3"],
  "key_facts": ["Fait 1 concret avec chiffre", "Fait 2", "Fait 3"],
  "tone": "description du ton qui marche (ex: urgent, informatif, choc, storytelling)",
  "structure": "structure narrative qui marche sur ce sujet",
  "avoided": ["Ce qui ne marche pas 1", "Ce qui ne marche pas 2"]
}}

Sois précis et basé sur les vrais scripts analysés.
JSON uniquement, sans texte autour."""

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
        analysis = {"best_hooks": [], "viral_patterns": [], "key_facts": [], "tone": "viral", "structure": "hook + contenu + CTA"}

    analysis["videos_found"] = len(all_videos)
    analysis["transcripts_extracted"] = len(transcripts)
    return analysis
