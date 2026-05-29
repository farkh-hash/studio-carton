from groq import Groq
from app.core.config import settings
import json
import re

CHARACTERS = {
    "ALEX": {"voice": "fr-FR-HenriNeural", "gender": "homme"},
    "SARAH": {"voice": "fr-FR-DeniseNeural", "gender": "femme"},
}

# Nombre de mots cible par personnage (dialogue total)
WORD_COUNTS = {30: 60, 60: 130, 90: 195, 120: 260, 180: 390}

SCENARIO_TYPES = {
    "revelation": "Révélation progressive. ALEX cache quelque chose. SARAH pose des questions. Tension qui monte. Révélation finale choc. Fin ouverte — on veut savoir la suite.",
    "transformation": "ALEX a complètement changé sa vie. SARAH découvre comment. Dialogue avant/après avec des chiffres réels. Fin inspirante avec CTA.",
    "debat": "SARAH et ALEX ont des opinions opposées. Arguments des deux côtés. SARAH finit par convaincre ALEX avec des faits concrets. Fin surprenante.",
    "mentor": "SARAH est l'experte. ALEX est le débutant sceptique. SARAH lui révèle un secret simple mais puissant. ALEX est choqué. Fin avec CTA.",
    "drama": "Situation de crise. ALEX panique. SARAH a la solution. Rebondissement inattendu. Résolution choc. Fin cliffhanger.",
}


def generate_scenario(topic: str, duration: int = 60, scenario_type: str = "revelation") -> dict:
    """
    Génère un script de scénario complet avec plusieurs personnages.
    RÈGLE ABSOLUE : le dialogue doit faire au minimum {target_words} mots.
    """
    client = Groq(api_key=settings.GROQ_API_KEY)
    target_words = WORD_COUNTS.get(duration, 130)
    scenario_desc = SCENARIO_TYPES.get(scenario_type, SCENARIO_TYPES["revelation"])

    prompt = f"""Tu es scénariste expert en contenu viral TikTok.

SUJET : "{topic}"
DURÉE : {duration} secondes
TYPE : {scenario_desc}

RÈGLES ABSOLUES :
1. Le dialogue total doit faire EXACTEMENT {target_words} mots minimum
2. ALEX et SARAH ont chacun AU MOINS 5 répliques
3. Chaque réplique = 8 à 15 mots (ni trop court, ni trop long)
4. La première réplique d'ALEX = HOOK ultra-fort (curiosité ou choc)
5. Le dialogue doit développer VRAIMENT le sujet avec des détails concrets
6. La dernière réplique = cliffhanger ou révélation qui force à s'abonner

STRUCTURE OBLIGATOIRE :
- Scène 1 : Hook + introduction du problème/mystère (3-4 répliques)
- Scène 2 : Développement avec des faits concrets, chiffres, tension (4-5 répliques)
- Scène 3 : Révélation + CTA (2-3 répliques)

EXEMPLE de bonne réplique : "J'ai généré 3000 euros ce mois-ci sans quitter mon canapé."
EXEMPLE de mauvaise réplique : "Wow." ou "Vraiment ?" (trop court, pas de valeur)

Retourne UNIQUEMENT ce JSON :
{{
  "title": "Titre accrocheur",
  "scenes": [
    {{
      "scene_id": 1,
      "setting": "lieu court (ex: bureau, café, rue)",
      "dialogues": [
        {{
          "character": "ALEX",
          "line": "réplique de 8 à 15 mots avec impact",
          "emotion": "confiant"
        }},
        {{
          "character": "SARAH",
          "line": "réplique de 8 à 15 mots avec curiosité ou scepticisme",
          "emotion": "curieuse"
        }}
      ]
    }}
  ],
  "cta": "phrase finale 10-15 mots qui donne envie de s abonner"
}}

IMPORTANT : Le dialogue TOTAL doit faire au moins {target_words} mots. Compte tes mots !
JSON uniquement, sans texte autour."""

    from app.services.groq_client import chat
    raw = chat([{"role": "user", "content": prompt}], max_tokens=3000, temperature=0.88)
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    scenario = json.loads(raw.strip())

    # Vérifier et compléter si trop court
    total_words = sum(
        len(d.get("line", "").split())
        for scene in scenario.get("scenes", [])
        for d in scene.get("dialogues", [])
    )

    # Si trop court, régénérer avec instruction plus forte
    if total_words < target_words * 0.7:
        print(f"[SCENARIO] Script trop court ({total_words} mots < {target_words}), régénération forcée...")
        return generate_scenario(topic, duration, scenario_type)

    # Ajouter les voix
    for scene in scenario.get("scenes", []):
        for d in scene.get("dialogues", []):
            char = d.get("character", "ALEX")
            d["voice"] = CHARACTERS.get(char, CHARACTERS["ALEX"])["voice"]

    scenario["topic"] = topic
    scenario["duration"] = duration
    scenario["type"] = scenario_type
    print(f"[SCENARIO] Script généré: {total_words} mots, {sum(len(s.get('dialogues',[])) for s in scenario.get('scenes',[]))} répliques")
    return scenario


def scenario_to_plain_script(scenario: dict) -> str:
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
