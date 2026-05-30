from app.core.config import settings
import json


def build_persona(topic: str, platform: str = "tiktok") -> dict:
    """
    Construit le profil exact du spectateur cible pour ce sujet.
    Plus le profil est précis, plus le script sera ciblé et impactant.
    """
    from app.services.groq_client import chat_fast as groq_chat

    prompt = f"""Tu es expert en psychologie des audiences sociales (TikTok, YouTube, Instagram).

SUJET DE LA VIDÉO : "{topic}"
PLATEFORME : {platform}

Définis le profil exact du spectateur qui va regarder cette vidéo jusqu'au bout.

Retourne un JSON :
{{
  "age_range": "tranche d'âge principale (ex: 22-35 ans)",
  "profile": "description du profil en 1 phrase (ex: 'entrepreneur débutant qui cherche à quitter son CDI')",
  "main_pain": "sa douleur principale liée au sujet (ce qui le frustre/bloque)",
  "main_desire": "son désir profond lié au sujet (ce qu'il veut vraiment)",
  "fear": "sa peur principale (ce qu'il craint de faire ou rater)",
  "language": "le vocabulaire exact qu'il utilise pour parler de ce sujet",
  "objections": ["Objection 1 qu'il a en regardant", "Objection 2"],
  "trigger_emotion": "l'émotion qui le fait cliquer et regarder (peur/espoir/curiosité/colère/honte)",
  "scroll_stopper": "ce qui l'arrête dans son scroll pour ce sujet précis",
  "hook_address": "comment l'adresser directement dans le hook (ex: 'Tu galères encore avec...')"
}}

Sois très précis et réaliste. Pas de généralités.
JSON uniquement."""

    raw = groq_chat(messages=[{"role": "user", "content": prompt}], max_tokens=800, temperature=0.6)
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        return json.loads(raw.strip())
    except Exception:
        return {}
