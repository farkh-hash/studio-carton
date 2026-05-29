from groq import Groq
from app.core.config import settings
import json
import re

# Voix disponibles par personnage
CHARACTERS = {
    "ALEX": {"voice": "fr-FR-HenriNeural", "gender": "homme", "style": "confiant et direct"},
    "SARAH": {"voice": "fr-FR-DeniseNeural", "gender": "femme", "style": "curieuse et réactive"},
    "MARC": {"voice": "fr-FR-HenriNeural", "gender": "homme", "style": "sceptique puis convaincu"},
    "LEA": {"voice": "fr-FR-EloiseNeural", "gender": "femme", "style": "experte et assertive"},
}

WORD_COUNTS = {30: 60, 60: 120, 90: 180, 120: 240, 180: 360}

SCENARIO_TYPES = {
    "revelation": "Un personnage révèle un secret/info à l'autre. Tension + surprise.",
    "transformation": "Avant/après. Un personnage a changé de vie, l'autre découvre comment.",
    "debat": "Deux personnes ont des points de vue opposés. L'un finit par convaincre l'autre.",
    "mentor": "Un expert enseigne quelque chose à un débutant de manière surprenante.",
    "drama": "Situation tendue qui révèle une vérité inattendue sur le sujet.",
}


def generate_scenario(topic: str, duration: int = 60, scenario_type: str = "revelation") -> dict:
    """
    Génère un script de scénario avec plusieurs personnages.
    Retourne un dict avec les répliques par personnage + scènes.
    """
    client = Groq(api_key=settings.GROQ_API_KEY)
    target_words = WORD_COUNTS.get(duration, 120)
    scenario_desc = SCENARIO_TYPES.get(scenario_type, SCENARIO_TYPES["revelation"])

    prompt = f"""Tu es scénariste expert en contenu viral TikTok/Reels.

SUJET : "{topic}"
DURÉE : {duration} secondes (~{target_words} mots de dialogue total)
TYPE DE SCÉNARIO : {scenario_desc}

Crée un script de scénario viral avec 2 personnages (ALEX et SARAH).
Le scénario doit être accrocheur, naturel, et donner envie de s'abonner pour voir la suite.

RÈGLES DU SCÉNARIO :
- La 1ère réplique = hook ultra-fort qui accroche en 2 secondes
- Chaque réplique = max 15 mots (dialogue naturel parlé)
- Tension dramatique qui monte progressivement
- Fin sur un cliffhanger ou révélation qui donne envie d'en voir plus
- Les personnages doivent sembler RÉELS, pas des robots

FORMAT DE RÉPONSE — retourne un JSON :
{{
  "title": "Titre accrocheur de la vidéo",
  "hook_line": "La première phrase qui accroche (max 10 mots)",
  "scenes": [
    {{
      "scene_id": 1,
      "setting": "description courte du lieu/contexte (ex: bureau, café, rue)",
      "dialogues": [
        {{
          "character": "ALEX",
          "line": "réplique de max 15 mots",
          "emotion": "émotion du personnage (confiant/surpris/excité/sérieux)"
        }},
        {{
          "character": "SARAH",
          "line": "réplique de max 15 mots",
          "emotion": "curiosité/choc/intérêt/sceptique"
        }}
      ]
    }}
  ],
  "cta": "Call-to-action final (max 10 mots, donne envie de s'abonner ou commenter)"
}}

Le scénario doit avoir 2-3 scènes et ~{target_words} mots de dialogue total.
JSON uniquement, sans texte autour."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,
        temperature=0.88,
    )

    raw = response.choices[0].message.content.strip()
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    scenario = json.loads(raw.strip())
    scenario["topic"] = topic
    scenario["duration"] = duration
    scenario["type"] = scenario_type

    # Ajouter les infos de voix pour chaque personnage
    for scene in scenario.get("scenes", []):
        for dialogue in scene.get("dialogues", []):
            char = dialogue["character"]
            if char in CHARACTERS:
                dialogue["voice"] = CHARACTERS[char]["voice"]
            else:
                dialogue["voice"] = "fr-FR-DeniseNeural"

    return scenario


def scenario_to_plain_script(scenario: dict) -> str:
    """Convertit le scénario en script texte simple pour affichage."""
    lines = []
    for scene in scenario.get("scenes", []):
        setting = scene.get("setting", "")
        if setting:
            lines.append(f"[{setting.upper()}]")
        for d in scene.get("dialogues", []):
            char = d.get("character", "")
            line = d.get("line", "")
            emotion = d.get("emotion", "")
            lines.append(f"{char} ({emotion}) : {line}")
    if scenario.get("cta"):
        lines.append(f"\n[CTA] {scenario['cta']}")
    return "\n".join(lines)
