from groq import Groq
from app.core.config import settings
import json
from datetime import date

NICHES = [
    "motivation et développement personnel",
    "finances personnelles et investissement",
    "santé, bien-être et fitness",
    "productivité et organisation",
    "entrepreneuriat et business en ligne",
    "psychologie et relations humaines",
    "alimentation, régime et nutrition",
    "technologie, IA et outils digitaux",
    "éducation rapide et apprentissage",
    "lifestyle, minimalisme et habitudes",
]

SYSTEM_PROMPT = """Tu es un expert en stratégie de contenu viral pour TikTok, YouTube Shorts et Instagram Reels.
Tu analyses les tendances actuelles et crées des stratégies de contenu basées sur ce qui performe réellement.
Tu réponds toujours en JSON valide uniquement."""


def analyze_niches() -> list[dict]:
    client = Groq(api_key=settings.GROQ_API_KEY)
    today = date.today().strftime("%d/%m/%Y")

    prompt = f"""Date : {today}

Analyse ces 10 niches pour créer du contenu viral en français sur TikTok/YouTube Shorts/Reels.

Niches : {json.dumps(NICHES, ensure_ascii=False)}

Pour chaque niche retourne un objet JSON avec exactement ces champs :
- "niche" : nom de la niche
- "emoji" : 1 emoji
- "score" : note de 1 à 10 (potentiel viral actuel)
- "why" : 1 phrase — pourquoi cette niche performe en ce moment
- "best_platform" : "TikTok" ou "YouTube" ou "Instagram" (où ça performe le mieux)
- "posting_frequency" : "1x/jour" ou "3x/semaine" etc.
- "topics" : liste de 3 objets avec :
  - "title" : le sujet de la vidéo (accrocheur, spécifique)
  - "hook" : la première phrase d'accroche (max 12 mots, choc immédiat)
  - "format" : "60s" ou "90s" ou "30s" (format recommandé)
  - "hashtags" : liste de 5 hashtags pertinents (sans #)
- "content_angle" : l'angle éditorial unique de cette niche (ex: "révèle les secrets", "contredit les idées reçues")

Retourne UNIQUEMENT un tableau JSON valide, sans texte avant ou après, sans markdown."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        max_tokens=4000,
        temperature=0.8,
    )

    raw = response.choices[0].message.content.strip()
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    data = json.loads(raw.strip())
    return sorted(data, key=lambda x: x.get("score", 0), reverse=True)


def generate_script_from_topic(topic: str, hook: str, niche: str, format_duration: str, style: str = "viral") -> str:
    """Génère un script complet à partir d'un sujet + hook pré-défini de l'agent niches."""
    client = Groq(api_key=settings.GROQ_API_KEY)

    duration_map = {"30s": 30, "60s": 60, "90s": 90, "2min": 120, "3min": 180}
    duration = duration_map.get(format_duration, 60)

    content_seconds = duration - 10

    prompt = f"""Crée un script viral de {duration} secondes.

SUJET : {topic}
NICHE : {niche}
HOOK IMPOSÉ (commence EXACTEMENT par ces mots) : "{hook}"

STRUCTURE :
1. HOOK ({min(5, duration//10)}s) : commence par le hook imposé mot pour mot
2. CONTENU ({content_seconds}s) : développe avec des faits précis, chiffres, exemples. Phrases de max 8 mots. Rythme rapide.
3. CTA (5-7s) : abonne-toi, commente ou partage. Rattaché au contenu.

RÈGLES STRICTES :
- Commence directement par le hook, aucune introduction
- Phrases courtes (max 8-10 mots)
- Uniquement le texte à lire à voix haute
- Pas d'annotations, pas de tirets, pas de numéros
- Chaque phrase crée l'envie d'entendre la suivante
- Français parlé naturel

Commence maintenant :{hook}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,
        temperature=0.85,
    )
    return response.choices[0].message.content.strip()
