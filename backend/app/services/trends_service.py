import httpx
import asyncio
import json
import re
from datetime import date
from groq import Groq
from app.core.config import settings


async def _youtube_trending_fr(max_results: int = 20) -> list[dict]:
    """Récupère les vraies vidéos trending sur YouTube France via l'API officielle."""
    params = {
        "part": "snippet,statistics",
        "chart": "mostPopular",
        "regionCode": "FR",
        "maxResults": max_results,
        "key": settings.YOUTUBE_API_KEY,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get("https://www.googleapis.com/youtube/v3/videos", params=params)
        resp.raise_for_status()
        data = resp.json()

    videos = []
    for item in data.get("items", []):
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})
        videos.append({
            "title": snippet.get("title", ""),
            "channel": snippet.get("channelTitle", ""),
            "category": snippet.get("categoryId", ""),
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "tags": snippet.get("tags", [])[:5],
        })
    return videos


async def _youtube_trending_shorts_fr() -> list[dict]:
    """Cherche les YouTube Shorts trending en France."""
    params = {
        "part": "snippet,statistics",
        "q": "#shorts viral france",
        "type": "video",
        "order": "viewCount",
        "maxResults": 15,
        "regionCode": "FR",
        "relevanceLanguage": "fr",
        "videoDuration": "short",
        "key": settings.YOUTUBE_API_KEY,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get("https://www.googleapis.com/youtube/v3/search", params=params)
        resp.raise_for_status()
        data = resp.json()

    videos = []
    for item in data.get("items", []):
        snippet = item.get("snippet", {})
        videos.append({
            "title": snippet.get("title", ""),
            "channel": snippet.get("channelTitle", ""),
            "description": snippet.get("description", "")[:200],
        })
    return videos


async def _google_trends_fr() -> list[str]:
    """Récupère les tendances Google en France via l'API publique."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "fr-FR,fr;q=0.9",
        }
        # Google Trends RSS feed France - pas besoin de pytrends
        url = "https://trends.google.fr/trending/rss?geo=FR"
        async with httpx.AsyncClient(timeout=10, headers=headers) as client:
            resp = await client.get(url)
            text = resp.text

        # Extraire les titres du RSS
        titles = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', text)
        if not titles:
            titles = re.findall(r'<title>(.*?)</title>', text)
        # Exclure le premier titre (nom du feed)
        return [t for t in titles[1:21] if t and len(t) > 2]
    except Exception as e:
        print(f"[TRENDS] Google Trends erreur: {e}")
        return []


async def _reddit_trending_fr() -> list[dict]:
    """Récupère les posts viraux via les flux RSS publics francophones."""
    sources = [
        ("https://www.reddit.com/r/france/hot.json?limit=5&raw_json=1", "france"),
        ("https://news.ycombinator.com/rss", "hackernews"),
    ]
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; StudioCarton/1.0)",
        "Accept": "application/json, text/xml, */*",
    }
    posts = []

    async with httpx.AsyncClient(timeout=10, headers=headers, follow_redirects=True) as client:
        for url, source in sources:
            try:
                resp = await client.get(url)
                if "json" in url and resp.status_code == 200:
                    data = resp.json()
                    for post in data.get("data", {}).get("children", [])[:5]:
                        p = post.get("data", {})
                        title = p.get("title", "")
                        if title:
                            posts.append({"title": title, "upvotes": p.get("score", 0), "subreddit": source})
                elif resp.status_code == 200:
                    # Parse RSS
                    import re
                    titles = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', resp.text)
                    if not titles:
                        titles = re.findall(r'<title>(.*?)</title>', resp.text)[1:6]
                    for t in titles[:5]:
                        posts.append({"title": t, "upvotes": 100, "subreddit": source})
            except Exception:
                continue

    return posts[:10]


async def _tiktok_trends_google() -> list[str]:
    """Cherche les tendances virales France via DuckDuckGo (moins restrictif que Google)."""
    queries = [
        f"tendances virales france {date.today().strftime('%B %Y')} tiktok reels",
        "video virale france finance investissement 2025",
    ]
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0",
        "Accept-Language": "fr-FR,fr;q=0.9",
        "Accept": "text/html,application/xhtml+xml",
    }
    titles = []
    async with httpx.AsyncClient(timeout=12, headers=headers, follow_redirects=True) as client:
        for q in queries[:2]:
            try:
                resp = await client.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": q, "kl": "fr-fr"},
                )
                found = re.findall(r'class="result__a"[^>]*>(.*?)</a>', resp.text, re.DOTALL)
                for t in found[:5]:
                    clean = re.sub(r'<[^>]+>', '', t).strip()
                    if clean and len(clean) > 10:
                        titles.append(clean)
            except Exception:
                continue
    return titles[:10]


async def analyze_trends() -> dict:
    """
    Analyse complète des tendances du moment en France.
    Sources : YouTube Trending FR, YouTube Shorts, Google Trends, Reddit FR, TikTok Google.
    """
    today = date.today().strftime("%d/%m/%Y")
    print(f"[TRENDS] Analyse tendances France — {today}")

    # Tout en parallèle
    results = await asyncio.gather(
        _youtube_trending_fr(20),
        _youtube_trending_shorts_fr(),
        _google_trends_fr(),
        _reddit_trending_fr(),
        _tiktok_trends_google(),
        return_exceptions=True
    )

    yt_trending = results[0] if not isinstance(results[0], Exception) else []
    yt_shorts = results[1] if not isinstance(results[1], Exception) else []
    google_trends = results[2] if not isinstance(results[2], Exception) else []
    reddit_posts = results[3] if not isinstance(results[3], Exception) else []
    tiktok_trends = results[4] if not isinstance(results[4], Exception) else []

    print(f"[TRENDS] YT: {len(yt_trending)} | Shorts: {len(yt_shorts)} | Google: {len(google_trends)} | Reddit: {len(reddit_posts)} | TikTok: {len(tiktok_trends)}")

    # Construire le contexte pour Groq
    context = f"DATE: {today}\n"

    if yt_trending:
        context += "\n=== YOUTUBE TRENDING FRANCE (vidéos les plus vues en ce moment) ===\n"
        for v in yt_trending[:10]:
            context += f"- {v['title']} ({v['views']:,} vues) | Chaîne: {v['channel']}\n"

    if yt_shorts:
        context += "\n=== YOUTUBE SHORTS VIRAUX FRANCE ===\n"
        for v in yt_shorts[:8]:
            context += f"- {v['title']} | {v['channel']}\n"

    if google_trends:
        context += "\n=== GOOGLE TRENDS FRANCE (recherches du moment) ===\n"
        for t in google_trends[:15]:
            context += f"- {t}\n"

    if reddit_posts:
        context += "\n=== REDDIT FRANCOPHONE (posts viraux) ===\n"
        for p in reddit_posts[:8]:
            context += f"- [{p['subreddit']}] {p['title']} ({p['upvotes']} upvotes)\n"

    if tiktok_trends:
        context += "\n=== TENDANCES TIKTOK FRANCE ===\n"
        for t in tiktok_trends[:5]:
            context += f"- {t}\n"

    # Analyse Groq
    client = Groq(api_key=settings.GROQ_API_KEY)

    prompt = f"""Analyse ces données réelles de tendances en France du {today} et identifie les meilleures opportunités de contenu viral.

{context}

Génère une analyse stratégique et retourne un JSON :
{{
  "top_niches": [
    {{
      "niche": "Nom de la niche trending",
      "score": 9,
      "proof": "Preuve chiffrée tirée des vraies données (ex: X millions de vues sur YT, tendance Google #1)",
      "why_now": "Pourquoi cette niche explose MAINTENANT (événement, saison, tendance)",
      "best_platform": "TikTok/YouTube/Instagram",
      "content_ideas": [
        "Idée de vidéo virale 1 basée sur les tendances réelles",
        "Idée 2",
        "Idée 3"
      ],
      "hook_inspiration": "Hook inspiré des vrais contenus trending trouvés",
      "monetisation": "Comment monétiser cette niche"
    }}
  ],
  "trending_keywords": ["mot-clé 1", "mot-clé 2", "mot-clé 3", "mot-clé 4", "mot-clé 5"],
  "hot_formats": ["Format de contenu qui cartonne 1", "Format 2"],
  "avoid_now": ["Sujet saturé/mort en ce moment 1", "Sujet 2"]
}}

Retourne exactement 5 niches. Base-toi UNIQUEMENT sur les données réelles fournies.
JSON uniquement, sans texte autour."""

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
        "youtube_trending": len(yt_trending),
        "youtube_shorts": len(yt_shorts),
        "google_trends": len(google_trends),
        "reddit": len(reddit_posts),
        "tiktok": len(tiktok_trends),
    }
    return data
