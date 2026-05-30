import httpx
import json
import re
import asyncio
from groq import Groq
from app.core.config import settings

YOUTUBE_API = "https://www.googleapis.com/youtube/v3"


async def _youtube_search(query: str, max_results: int = 10) -> list[dict]:
    """Cherche les vidéos les plus vues sur YouTube via l'API officielle."""
    if not settings.YOUTUBE_API_KEY:
        print("[RESEARCH] Pas de YOUTUBE_API_KEY configurée")
        return []

    # Simplifier la query pour de meilleurs résultats
    simplified = query[:80] if len(query) > 80 else query
    params = {
        "part": "snippet",
        "q": simplified,
        "type": "video",
        "order": "viewCount",
        "maxResults": max_results,
        "relevanceLanguage": "fr",
        "key": settings.YOUTUBE_API_KEY,
    }
    print(f"[RESEARCH] YouTube API search: '{simplified}'")
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{YOUTUBE_API}/search", params=params)
        resp.raise_for_status()
        data = resp.json()

    videos = []
    for item in data.get("items", []):
        vid_id = item.get("id", {}).get("videoId", "")
        title = item.get("snippet", {}).get("title", "")
        description = item.get("snippet", {}).get("description", "")
        if vid_id and title:
            videos.append({"id": vid_id, "title": title, "description": description[:300]})
    return videos


async def _get_youtube_transcript(video_id: str) -> str:
    """Récupère le vrai transcript d'une vidéo YouTube."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        loop = asyncio.get_running_loop()
        transcript_list = await loop.run_in_executor(
            None,
            lambda: YouTubeTranscriptApi.get_transcript(video_id, languages=["fr", "fr-FR", "en"])
        )
        return " ".join(t["text"] for t in transcript_list)[:2500]
    except Exception as e:
        print(f"[RESEARCH] Transcript {video_id} impossible: {e}")
        return ""


async def _google_search_platform(platform: str, query: str) -> list[str]:
    """Cherche du contenu viral sur TikTok/Instagram via Google."""
    site_query = {
        "tiktok": f'site:tiktok.com {query}',
        "instagram": f'site:instagram.com reels {query}',
        "reddit": f'site:reddit.com {query} viral',
    }
    q = site_query.get(platform, f'{query} viral {platform}')

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "fr-FR,fr;q=0.9",
    }
    async with httpx.AsyncClient(timeout=10, headers=headers) as client:
        resp = await client.get("https://www.google.com/search", params={"q": q, "num": 8, "hl": "fr"})
        html = resp.text

    titles = re.findall(r'<h3[^>]*>(.*?)</h3>', html, re.DOTALL)
    results = []
    for t in titles[:8]:
        clean = re.sub(r'<[^>]+>', '', t).strip()
        if clean and len(clean) > 10:
            results.append(clean)
    return results


async def research_viral_scripts(topic: str) -> dict:
    """
    Recherche multi-plateforme réelle :
    - YouTube API officielle (vidéos + transcripts réels)
    - TikTok via Google Search
    - Instagram via Google Search
    - Reddit via Google Search
    """
    print(f"[RESEARCH] Démarrage recherche multi-plateforme: {topic}")

    # Lancer tout en parallèle
    tasks = [
        _youtube_search(topic + " comment faire gagner argent", max_results=8),
        _youtube_search(topic + " viral shorts", max_results=5),
        _google_search_platform("tiktok", topic),
        _google_search_platform("instagram", topic),
        _google_search_platform("reddit", topic),
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)
    yt_main = results[0] if not isinstance(results[0], Exception) else []
    yt_shorts = results[1] if not isinstance(results[1], Exception) else []
    tiktok_titles = results[2] if not isinstance(results[2], Exception) else []
    instagram_titles = results[3] if not isinstance(results[3], Exception) else []
    reddit_titles = results[4] if not isinstance(results[4], Exception) else []

    all_yt = (yt_main + yt_shorts)[:8]
    print(f"[RESEARCH] YouTube: {len(all_yt)} vidéos | TikTok: {len(tiktok_titles)} | Instagram: {len(instagram_titles)} | Reddit: {len(reddit_titles)}")

    # Extraire les transcripts YouTube réels (top 4 vidéos)
    transcripts = []
    for video in all_yt[:4]:
        transcript = await _get_youtube_transcript(video["id"])
        if len(transcript) > 200:
            transcripts.append({
                "title": video["title"],
                "transcript": transcript[:1500],
            })
            print(f"[RESEARCH] Transcript OK: {video['title'][:50]}")
        if len(transcripts) >= 3:
            break

    # Construire le contexte complet
    context_parts = []

    if transcripts:
        context_parts.append("=== VRAIS SCRIPTS YOUTUBE (transcripts réels) ===")
        for t in transcripts:
            context_parts.append(f"\nVidéo virale: {t['title']}\nScript réel:\n{t['transcript']}")

    if all_yt:
        context_parts.append("\n=== TITRES YOUTUBE LES PLUS VUS ===")
        for v in all_yt[:6]:
            context_parts.append(f"- {v['title']}")
            if v['description']:
                context_parts.append(f"  Description: {v['description']}")

    if tiktok_titles:
        context_parts.append("\n=== CONTENUS VIRAUX TIKTOK ===")
        context_parts.extend([f"- {t}" for t in tiktok_titles[:5]])

    if instagram_titles:
        context_parts.append("\n=== CONTENUS VIRAUX INSTAGRAM REELS ===")
        context_parts.extend([f"- {t}" for t in instagram_titles[:5]])

    if reddit_titles:
        context_parts.append("\n=== DISCUSSIONS VIRALES REDDIT ===")
        context_parts.extend([f"- {t}" for t in reddit_titles[:4]])

    full_context = "\n".join(context_parts) if context_parts else "Aucune donnée disponible."

    # Analyse Groq basée sur les vrais scripts
    client = Groq(api_key=settings.GROQ_API_KEY)

    analysis_prompt = f"""Analyse ces VRAIS scripts et contenus viraux sur "{topic}" trouvés sur YouTube, TikTok, Instagram et Reddit.

{full_context}

Extrais exactement ce qui fait qu'ils cartonnent. Retourne un JSON :
{{
  "best_hooks": [
    "Hook 1 directement inspiré des vrais scripts (avec chiffres réels si présents)",
    "Hook 2",
    "Hook 3"
  ],
  "viral_patterns": [
    "Pattern narratif 1 qui revient dans plusieurs scripts",
    "Pattern 2",
    "Pattern 3"
  ],
  "key_facts": [
    "Fait concret 1 avec chiffre tiré des vrais scripts",
    "Fait 2",
    "Fait 3"
  ],
  "tone": "Ton exact utilisé dans les scripts viraux (ex: urgent et personnel, révélation choc, storytelling financier)",
  "structure": "Structure narrative exacte qui revient",
  "avoided": [
    "Ce qui ne marche pas sur ce sujet",
    "Erreur 2"
  ]
}}

IMPORTANT : base-toi UNIQUEMENT sur les vrais scripts et titres analysés, pas sur tes connaissances générales.
JSON uniquement, sans texte autour."""

    def _call_groq_analysis():
        return client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": analysis_prompt}],
            max_tokens=1200,
            temperature=0.4,
        )

    loop = asyncio.get_running_loop()
    response = await loop.run_in_executor(None, _call_groq_analysis)

    raw = response.choices[0].message.content.strip()
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        analysis = json.loads(raw.strip())
    except Exception:
        analysis = {
            "best_hooks": [],
            "viral_patterns": [],
            "key_facts": [],
            "tone": "direct et percutant",
            "structure": "hook choc + faits précis + CTA fort"
        }

    analysis["videos_found"] = len(all_yt)
    analysis["transcripts_extracted"] = len(transcripts)
    analysis["platforms_searched"] = ["YouTube", "TikTok", "Instagram", "Reddit"]
    return analysis
