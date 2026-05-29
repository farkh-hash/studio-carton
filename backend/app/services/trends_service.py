import httpx
import asyncio
import json
import re
from datetime import date
from groq import Groq
from app.core.config import settings

YOUTUBE_API = "https://www.googleapis.com/youtube/v3"

# Pays francophones pour élargir l'analyse
FRANCOPHONE_REGIONS = ["FR", "BE", "CA", "CH", "MA", "SN"]


async def _youtube_trending(region: str = "FR", max_results: int = 10) -> list[dict]:
    """YouTube trending pour une région."""
    if not settings.YOUTUBE_API_KEY:
        return []
    params = {
        "part": "snippet,statistics",
        "chart": "mostPopular",
        "regionCode": region,
        "maxResults": max_results,
        "key": settings.YOUTUBE_API_KEY,
    }
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            resp = await client.get(f"{YOUTUBE_API}/videos", params=params)
            resp.raise_for_status()
            data = resp.json()
        return [
            {
                "title": item["snippet"]["title"],
                "channel": item["snippet"]["channelTitle"],
                "views": int(item["statistics"].get("viewCount", 0)),
                "region": region,
            }
            for item in data.get("items", [])
        ]
    except Exception as e:
        print(f"[TRENDS] YouTube {region}: {e}")
        return []


async def _youtube_search_viral(query: str, max_results: int = 8) -> list[dict]:
    """Cherche les vidéos virales sur un sujet via YouTube."""
    if not settings.YOUTUBE_API_KEY:
        return []
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "order": "viewCount",
        "maxResults": max_results,
        "relevanceLanguage": "fr",
        "key": settings.YOUTUBE_API_KEY,
    }
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            resp = await client.get(f"{YOUTUBE_API}/search", params=params)
            resp.raise_for_status()
            data = resp.json()
        return [
            {"title": item["snippet"]["title"], "channel": item["snippet"]["channelTitle"]}
            for item in data.get("items", [])
        ]
    except Exception as e:
        print(f"[TRENDS] YouTube search: {e}")
        return []


async def _google_trends_multi() -> list[str]:
    """Google Trends RSS pour plusieurs pays francophones."""
    regions = {
        "FR": "https://trends.google.fr/trending/rss?geo=FR",
        "CA": "https://trends.google.ca/trending/rss?geo=CA",
        "BE": "https://trends.google.be/trending/rss?geo=BE",
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "fr-FR,fr;q=0.9",
    }
    all_trends = []
    async with httpx.AsyncClient(timeout=10, headers=headers) as client:
        for country, url in regions.items():
            try:
                resp = await client.get(url)
                titles = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', resp.text)
                if not titles:
                    titles = re.findall(r'<title>(.*?)</title>', resp.text)[1:]
                all_trends.extend([f"[{country}] {t}" for t in titles[:7]])
            except Exception:
                continue
    return all_trends[:20]


async def _tiktok_trends() -> list[str]:
    """Tendances TikTok via DuckDuckGo (multi-plateforme)."""
    queries = [
        "tiktok viral france 2025 finance argent",
        "trending tiktok francophone IA technologie",
        "reels instagram viral france investissement",
        "youtube shorts viral français 2025",
    ]
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0",
        "Accept-Language": "fr-FR,fr;q=0.9",
    }
    results = []
    async with httpx.AsyncClient(timeout=12, headers=headers, follow_redirects=True) as client:
        for q in queries[:3]:
            try:
                resp = await client.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": q, "kl": "fr-fr"},
                )
                found = re.findall(r'class="result__a"[^>]*>(.*?)</a>', resp.text, re.DOTALL)
                for t in found[:4]:
                    clean = re.sub(r'<[^>]+>', '', t).strip()
                    if clean and len(clean) > 10:
                        results.append(clean)
            except Exception:
                continue
    return results[:12]


async def _social_trending_scrape() -> list[str]:
    """Scrape les tendances multi-réseaux via sources publiques."""
    sources = [
        # Hacker News (tech trends)
        "https://news.ycombinator.com/rss",
        # Reddit France
        "https://www.reddit.com/r/france/hot.json?limit=5&raw_json=1",
        # Reddit francophone finance
        "https://www.reddit.com/r/financepersonnelle/hot.json?limit=5&raw_json=1",
    ]
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; StudioCarton/1.0)",
        "Accept": "application/json, text/xml, */*",
    }
    titles = []
    async with httpx.AsyncClient(timeout=10, headers=headers, follow_redirects=True) as client:
        for url in sources:
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    continue
                if "json" in url:
                    data = resp.json()
                    for post in data.get("data", {}).get("children", [])[:4]:
                        t = post.get("data", {}).get("title", "")
                        if t:
                            titles.append(t)
                else:
                    found = re.findall(r'<title>(.*?)</title>', resp.text)[1:6]
                    titles.extend(found)
            except Exception:
                continue
    return titles[:15]


async def analyze_trends() -> dict:
    """
    Analyse complète multi-plateformes et multi-pays francophones.
    Sources : YouTube (FR/BE/CA/CH) + Google Trends multi-pays + TikTok + Instagram + Reddit
    """
    today = date.today().strftime("%d/%m/%Y")
    print(f"[TRENDS] Analyse multi-plateformes — {today}")

    # Lancer toutes les sources en parallèle
    tasks = [
        # YouTube trending sur plusieurs régions
        _youtube_trending("FR", 10),
        _youtube_trending("BE", 5),
        _youtube_trending("CA", 5),
        # YouTube search pour niches rentables en français
        _youtube_search_viral("finance argent viral français", 6),
        _youtube_search_viral("IA intelligence artificielle viral", 6),
        # Google Trends multi-pays
        _google_trends_multi(),
        # TikTok + Instagram via DuckDuckGo
        _tiktok_trends(),
        # Reddit + Hacker News
        _social_trending_scrape(),
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    yt_fr = results[0] if not isinstance(results[0], Exception) else []
    yt_be = results[1] if not isinstance(results[1], Exception) else []
    yt_ca = results[2] if not isinstance(results[2], Exception) else []
    yt_finance = results[3] if not isinstance(results[3], Exception) else []
    yt_ia = results[4] if not isinstance(results[4], Exception) else []
    google_trends = results[5] if not isinstance(results[5], Exception) else []
    tiktok_ig = results[6] if not isinstance(results[6], Exception) else []
    social = results[7] if not isinstance(results[7], Exception) else []

    all_yt = yt_fr + yt_be + yt_ca

    print(f"[TRENDS] YT FR:{len(yt_fr)} BE:{len(yt_be)} CA:{len(yt_ca)} | Finance:{len(yt_finance)} IA:{len(yt_ia)} | Google:{len(google_trends)} | TikTok/IG:{len(tiktok_ig)} | Social:{len(social)}")

    # Construire le contexte pour Groq
    context = f"DATE: {today}\n"
    context += f"ANALYSE MULTI-PLATEFORMES (YouTube France/Belgique/Canada + Google Trends + TikTok + Instagram + Reddit)\n\n"

    if all_yt:
        context += "=== YOUTUBE TRENDING (France, Belgique, Canada) ===\n"
        for v in sorted(all_yt, key=lambda x: x.get("views", 0), reverse=True)[:12]:
            context += f"- [{v['region']}] {v['title']} — {v.get('views', 0):,} vues\n"

    if yt_finance:
        context += "\n=== YOUTUBE FINANCE/ARGENT VIRAL (francophone) ===\n"
        for v in yt_finance[:6]:
            context += f"- {v['title']}\n"

    if yt_ia:
        context += "\n=== YOUTUBE IA/TECH VIRAL (francophone) ===\n"
        for v in yt_ia[:6]:
            context += f"- {v['title']}\n"

    if google_trends:
        context += "\n=== GOOGLE TRENDS (France, Canada, Belgique) ===\n"
        for t in google_trends[:15]:
            context += f"- {t}\n"

    if tiktok_ig:
        context += "\n=== TIKTOK & INSTAGRAM TENDANCES ===\n"
        for t in tiktok_ig[:8]:
            context += f"- {t}\n"

    if social:
        context += "\n=== REDDIT & RÉSEAUX SOCIAUX ===\n"
        for t in social[:8]:
            context += f"- {t}\n"

    # Analyse Groq
    client = Groq(api_key=settings.GROQ_API_KEY)

    prompt = f"""Analyse ces données réelles de tendances virales du {today} sur TOUS les réseaux sociaux francophones (YouTube, TikTok, Instagram, Reddit).

{context}

Identifie les meilleures opportunités de contenu viral monétisable en français.

Retourne ce JSON :
{{
  "top_niches": [
    {{
      "niche": "Nom de la niche",
      "score": 9,
      "proof": "Preuve chiffrée tirée des données réelles ci-dessus (titre vidéo + vues ou tendance)",
      "why_now": "Pourquoi cette niche explose sur TOUS les réseaux maintenant",
      "best_platform": "TikTok ou YouTube ou Instagram",
      "content_ideas": [
        "Idée vidéo virale 1 basée sur les vraies tendances",
        "Idée 2",
        "Idée 3"
      ],
      "hook_inspiration": "Hook inspiré des vrais titres viraux trouvés",
      "monetisation": "Comment monétiser (RPM, affiliation, brand deals)"
    }}
  ],
  "trending_keywords": ["mot-clé 1", "mot-clé 2", "mot-clé 3", "mot-clé 4", "mot-clé 5"],
  "hot_formats": ["Format qui cartonne 1 sur tous les réseaux", "Format 2"],
  "avoid_now": ["Sujet saturé/mort 1", "Sujet 2"]
}}

5 niches maximum. Base-toi UNIQUEMENT sur les données ci-dessus.
JSON uniquement."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=3000,
        temperature=0.6,
    )

    raw = response.choices[0].message.content.strip()
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        data = json.loads(raw.strip())
    except Exception:
        data = {"top_niches": [], "trending_keywords": [], "hot_formats": [], "avoid_now": []}

    data["date"] = today
    data["sources"] = {
        "youtube_fr": len(yt_fr),
        "youtube_be_ca": len(yt_be) + len(yt_ca),
        "youtube_niche_search": len(yt_finance) + len(yt_ia),
        "google_trends": len(google_trends),
        "tiktok_instagram": len(tiktok_ig),
        "social_reddit": len(social),
    }
    return data
