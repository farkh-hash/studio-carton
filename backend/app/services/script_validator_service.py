from app.core.config import settings
import json
import re


def validate_script(script: str, topic: str, duration: int) -> dict:
    """
    Valide un script sur plusieurs critères.
    Retourne un score global et des recommandations.
    """
    from app.services.groq_client import chat as groq_chat

    word_count = len(script.split())
    target_words = int(duration * 2.2)  # ~2.2 mots/seconde en français naturel
    sentence_count = len([s for s in re.split(r'[.!?]', script) if s.strip()])
    avg_words_per_sentence = word_count / max(sentence_count, 1)

    prompt = f"""Tu es un expert en contenu viral qui valide la qualité des scripts.

SUJET : "{topic}"
DURÉE CIBLE : {duration} secondes
SCRIPT :
{script}

MÉTRIQUES CALCULÉES :
- Nombre de mots : {word_count} (cible : {target_words})
- Nombre de phrases : {sentence_count}
- Moyenne mots/phrase : {avg_words_per_sentence:.1f} (idéal : 6-9)

Évalue ce script sur ces critères et retourne un JSON :
{{
  "scores": {{
    "hook_strength": 7,
    "clarity": 8,
    "rhythm": 6,
    "authenticity": 7,
    "cta_effectiveness": 5,
    "overall": 7
  }},
  "issues": [
    "Problème 1 identifié dans le script",
    "Problème 2"
  ],
  "false_claims": ["Fausse promesse ou affirmation mensongère détectée"],
  "improvements": [
    "Amélioration 1 concrète à apporter",
    "Amélioration 2"
  ],
  "regenerate": false,
  "regenerate_reason": "raison si regenerate=true"
}}

CRITÈRES D'ÉVALUATION :
- hook_strength (1-10) : le hook accroche-t-il vraiment en 2 secondes ?
- clarity (1-10) : le message est-il clair et compréhensible ?
- rhythm (1-10) : le rythme est-il adapté à la vidéo courte ? (phrases courtes = bon)
- authenticity (1-10) : sonne-t-il naturel et authentique ?
- cta_effectiveness (1-10) : le CTA donne-t-il envie d'agir ?
- overall (1-10) : note globale

Si overall < 6 OU false_claims non vide → met regenerate: true

JSON uniquement."""

    raw = groq_chat(messages=[{"role": "user", "content": prompt}], max_tokens=800, temperature=0.3)
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        result = json.loads(raw.strip())
    except Exception:
        result = {"scores": {"overall": 5}, "issues": [], "false_claims": [], "improvements": [], "regenerate": False}

    result["word_count"] = word_count
    result["target_words"] = target_words
    result["avg_words_per_sentence"] = round(avg_words_per_sentence, 1)
    return result
