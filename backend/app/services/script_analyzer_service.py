from app.core.config import settings
import json


def analyze_script_deeply(transcript: str, title: str = "") -> dict:
    """
    Analyse profonde d'un vrai script viral.
    Extrait les techniques exactes qui font que ce contenu performe.
    """
    from app.services.groq_client import chat_fast as groq_chat

    prompt = f"""Tu es un expert en psychologie du contenu viral. Analyse ce script réel d'une vidéo qui cartonne.

TITRE : {title}
SCRIPT :
{transcript[:2000]}

Analyse EXACTEMENT et PRÉCISÉMENT chaque élément. Retourne un JSON :
{{
  "hook_type": "classification exacte (ex: transformation personnelle, révélation choc, question rhétorique, statistique surprenante, contradiction, urgence)",
  "hook_formula": "la formule exacte du hook (ex: 'J'étais X, maintenant je suis Y en Z jours')",
  "hook_words": ["mot fort 1", "mot fort 2", "mot fort 3"],
  "emotional_arc": {{
    "opening_emotion": "émotion déclenchée au début (curiosité/peur/espoir/frustration/surprise)",
    "tension_point": "où et comment la tension monte dans le script",
    "resolution": "comment la tension se résout",
    "closing_emotion": "émotion finale laissée au spectateur"
  }},
  "retention_techniques": [
    "Technique 1 utilisée pour garder l'attention (ex: boucle ouverte à 10s)",
    "Technique 2",
    "Technique 3"
  ],
  "power_words": ["mot puissant 1", "mot puissant 2", "mot puissant 3", "mot puissant 4"],
  "sentence_rhythm": "analyse du rythme (ex: 3-4 mots par phrase, accélération en milieu de vidéo)",
  "social_proof": "comment la preuve sociale est utilisée (chiffres, témoignages, autorité)",
  "cta_formula": "formule exacte du call-to-action et pourquoi il fonctionne",
  "why_viral": "en 1 phrase : la raison principale pour laquelle ce script accroche"
}}

Sois extrêmement précis et basé uniquement sur ce qui est présent dans le script.
JSON uniquement, sans texte autour."""

    raw = groq_chat(messages=[{"role": "user", "content": prompt}], max_tokens=1200, temperature=0.3)
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        return json.loads(raw.strip())
    except Exception:
        return {}


def synthesize_analyses(analyses: list[dict]) -> dict:
    """
    Synthétise plusieurs analyses pour extraire les patterns communs.
    Ce sont les patterns qui apparaissent dans plusieurs vidéos virales = patterns prouvés.
    """
    if not analyses:
        return {}

    from app.services.groq_client import chat_fast as groq_chat

    analyses_text = json.dumps(analyses, ensure_ascii=False, indent=2)

    prompt = f"""Tu as analysé {len(analyses)} scripts viraux réels. Voici les analyses individuelles :

{analyses_text[:3000]}

Synthétise les PATTERNS COMMUNS qui apparaissent dans PLUSIEURS de ces scripts.
Ce qui revient = ce qui marche vraiment.

Retourne un JSON :
{{
  "dominant_hook_type": "le type de hook qui revient le plus souvent",
  "proven_hook_formula": "la formule de hook la plus utilisée et efficace",
  "recurring_power_words": ["mot 1", "mot 2", "mot 3", "mot 4", "mot 5"],
  "common_retention_technique": "la technique de rétention la plus utilisée",
  "optimal_rhythm": "le rythme de phrases qui revient (longueur, rythme)",
  "emotional_pattern": "l'arc émotionnel dominant (quelle émotion → quelle émotion)",
  "proven_cta": "le type de CTA qui revient le plus souvent",
  "key_insight": "l'insight principal : pourquoi ces scripts captivent (en 1-2 phrases précises)"
}}

JSON uniquement."""

    raw = groq_chat(messages=[{"role": "user", "content": prompt}], max_tokens=800, temperature=0.3)
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        return json.loads(raw.strip())
    except Exception:
        return {}
