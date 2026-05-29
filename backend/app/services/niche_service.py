from groq import Groq
from app.core.config import settings
import json
from datetime import date

NICHES = [
    "motivation et développement personnel",
    "finances personnelles et investissement",
    "santé et bien-être",
    "productivité et organisation",
    "entrepreneuriat et business",
    "relations et psychologie",
    "alimentation et régime",
    "technologie et IA",
    "voyage et lifestyle",
    "éducation et apprentissage",
]


def analyze_niches() -> list[dict]:
    client = Groq(api_key=settings.GROQ_API_KEY)
    today = date.today().strftime("%d/%m/%Y")

    prompt = f"""Tu es un expert en contenu viral pour TikTok, YouTube Shorts et Instagram Reels.
Date du jour : {today}

Analyse ces 10 niches et pour chacune génère 3 sujets de vidéos ultra-viraux en français.

Niches : {json.dumps(NICHES, ensure_ascii=False)}

Pour chaque niche, retourne un objet JSON avec :
- "niche" : nom de la niche
- "emoji" : 1 emoji représentatif
- "score" : score viral de 1 à 10 (basé sur les tendances actuelles)
- "why" : une phrase expliquant pourquoi cette niche performe maintenant
- "topics" : liste de 3 sujets de vidéos (strings), chaque sujet doit être accrocheur et spécifique

Retourne UNIQUEMENT un tableau JSON valide, sans texte avant ou après."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=3000,
        temperature=0.8,
    )

    raw = response.choices[0].message.content.strip()
    # Extraire le JSON si entouré de markdown
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    data = json.loads(raw.strip())
    # Trier par score décroissant
    return sorted(data, key=lambda x: x.get("score", 0), reverse=True)
