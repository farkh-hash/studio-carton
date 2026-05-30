from app.core.config import settings
import json


async def research_viral_patterns(topic: str, platform: str = "tiktok") -> dict:
    """
    Analyse les patterns viraux pour ce sujet sur les réseaux sociaux.
    Retourne les insights pour créer un script optimisé.
    """
        research_prompt = f"""Tu es un analyste expert en contenu viral avec accès aux données de performance TikTok, YouTube Shorts et Instagram Reels.

SUJET À ANALYSER : "{topic}"
PLATEFORME CIBLE : {platform}

Analyse les meilleures vidéos virales sur ce sujet et fournis une analyse stratégique détaillée.

Réponds en JSON avec exactement cette structure :
{{
  "top_hooks": [
    "Hook exemple 1 qui a des millions de vues",
    "Hook exemple 2 ultra performant",
    "Hook exemple 3 viral"
  ],
  "viral_angles": [
    "Angle 1 : ce qui choque/surprend sur ce sujet",
    "Angle 2 : ce que personne ne dit",
    "Angle 3 : la transformation/résultat promis"
  ],
  "key_facts": [
    "Fait surprenant 1 avec chiffre précis",
    "Fait surprenant 2 contre-intuitif",
    "Fait surprenant 3 actionnable"
  ],
  "target_pain": "La douleur/frustration principale de l'audience sur ce sujet",
  "best_format": "Structure narrative qui performe (ex: liste, storytelling, révélation, tutoriel)",
  "forbidden_mistakes": [
    "Erreur 1 à éviter dans ce type de contenu",
    "Erreur 2 qui tue la rétention"
  ],
  "viral_cta": "Le CTA qui génère le plus de commentaires/partages sur ce sujet",
  "emotion_target": "L'émotion principale à déclencher (curiosité/peur/espoir/colère/surprise)"
}}

Base-toi sur ce qui FONCTIONNE VRAIMENT sur {platform} pour ce sujet en 2025.
Sois précis, concret, avec des chiffres réels quand possible.
Retourne UNIQUEMENT le JSON, sans texte autour."""

    raw_content = groq_chat(messages=[{"role": "user", "content": research_prompt}], max_tokens=1500, temperature=0.7)

    raw = raw_resp
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    return json.loads(raw.strip())
