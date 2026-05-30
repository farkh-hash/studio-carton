import json


def generate_captions(topic: str, script: str, niche: str = "") -> dict:
    """Génère les captions/titres/hashtags optimisés pour chaque plateforme."""
    from app.services.groq_client import chat as groq_chat

    prompt = f"""Tu es expert en stratégie de publication sur les réseaux sociaux.

SUJET : {topic}
NICHE : {niche or "contenu viral"}
DÉBUT DU SCRIPT : {script[:300]}...

Génère les éléments de publication optimisés pour chaque plateforme.

Retourne UNIQUEMENT ce JSON valide :
{{
  "tiktok": {{
    "caption": "Caption TikTok (max 150 caractères, accrocheur, inclut 1-2 hashtags dans le texte)",
    "hashtags": ["hashtag1", "hashtag2", "hashtag3", "hashtag4", "hashtag5"],
    "best_time": "Meilleur moment pour poster (ex: 18h-21h en semaine)"
  }},
  "youtube": {{
    "title": "Titre YouTube Shorts (max 60 caractères, SEO optimisé, curiosité)",
    "description": "Description YouTube (2-3 phrases, mots-clés naturels, CTA abonnement)",
    "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"],
    "best_time": "Meilleur moment pour poster"
  }},
  "instagram": {{
    "caption": "Caption Instagram (accrocheur, 3-4 lignes, émoji, CTA en fin)",
    "hashtags": ["hashtag1", "hashtag2", "hashtag3", "hashtag4", "hashtag5", "hashtag6", "hashtag7"],
    "best_time": "Meilleur moment pour poster"
  }}
}}

Règles :
- Hashtags sans #, en minuscules, pertinents et mixés (niche + tendance + large)
- Textes en français naturel
- Optimisé pour l'algorithme de chaque plateforme
- CTA naturel (pas forcé)"""

    raw = groq_chat(messages=[{"role": "user", "content": prompt}], max_tokens=1500, temperature=0.7)
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    return json.loads(raw.strip())
