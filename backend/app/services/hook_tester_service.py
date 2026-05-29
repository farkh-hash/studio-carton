from groq import Groq
from app.core.config import settings
import json


def generate_and_score_hooks(topic: str, analysis_context: str = "") -> list[dict]:
    """
    Génère 5 hooks différents pour le sujet et les évalue.
    Retourne la liste triée par score décroissant.
    """
    client = Groq(api_key=settings.GROQ_API_KEY)

    context_section = f"\nCONTEXTE des scripts viraux analysés :\n{analysis_context}" if analysis_context else ""

    prompt = f"""Tu es expert en hooks viraux pour TikTok, YouTube Shorts et Instagram Reels.
{context_section}

SUJET : "{topic}"

Génère 5 hooks DIFFÉRENTS pour ce sujet, chacun utilisant une technique différente.
Pour chaque hook, évalue son potentiel viral.

Retourne un JSON avec une liste de 5 objets :
[
  {{
    "hook": "texte exact du hook (max 12 mots, percutant, en français naturel)",
    "type": "type de hook (transformation/choc/curiosité/nombre/urgence/contre-intuitif/identification)",
    "trigger": "émotion psychologique déclenchée (curiosité/peur/espoir/surprise/colère)",
    "score": 8,
    "why": "pourquoi ce hook accroche en 1 phrase"
  }}
]

RÈGLES pour les hooks :
- Maximum 12 mots
- Jamais de formule générique comme "Découvrez comment..."
- Utilise des chiffres précis quand possible
- Crée une boucle ouverte — le spectateur DOIT regarder la suite
- Pas de fausses promesses, mais des promesses fortes

Score : 1-10 basé sur le potentiel de rétention estimé.
JSON uniquement, sans texte autour."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
        temperature=0.9,
    )

    raw = response.choices[0].message.content.strip()
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        hooks = json.loads(raw.strip())
        return sorted(hooks, key=lambda h: h.get("score", 0), reverse=True)
    except Exception:
        return []


def select_best_hook(hooks: list[dict]) -> str:
    """Retourne le meilleur hook (score le plus élevé)."""
    if not hooks:
        return ""
    return hooks[0].get("hook", "")
