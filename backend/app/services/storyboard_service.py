"""Génère des storyboards viraux scène par scène avec prompts IA et scoring /50."""
import json
import re
import asyncio

VISUAL_STYLES = {
    "cinematic": "cinématique réaliste, caméra professionnelle, lumière dramatique, couleurs riches",
    "cartoon": "dessin animé 2D coloré, traits stylisés, couleurs vives, humour visuel",
    "anime": "style anime japonais, dynamique, expressions dramatiques, effets visuels intenses",
    "pixar": "animation 3D Pixar, personnages expressifs, monde coloré et détaillé, qualité cinéma",
    "disney": "animation Disney classique, couleurs vibrantes, personnages charismatiques, magie",
    "scifi": "science-fiction futuriste, effets néon, hologrammes, cyberpunk, technologie avancée",
    "documentary": "documentaire réaliste, plans authentiques, style reportage journalistique",
    "humour": "comédie visuelle, expressions exagérées, timing comique, absurde et décalé",
    "motivation": "inspirant, lumière épique, montées dramatiques, grandeur et puissance",
    "business": "professionnel, clean, bureau moderne, lifestyle entrepreneurial et premium",
}

SYSTEM_PROMPT = """Tu es un réalisateur, monteur et expert en viralité TikTok, Reels et YouTube Shorts.
Tu produis des storyboards qui maximisent rétention, watch time, replays, commentaires et partages.

RÈGLES ABSOLUES:
- Hook dans les 3 premières secondes: choc / curiosité / contradiction / émotion / question
- Changement toutes les 1-2 secondes: nouveau plan, nouvelle info, nouvelle émotion
- Caméra TOUJOURS en mouvement: zoom_in, zoom_out, pan_left, pan_right, tilt_up, tilt_down, dolly_in
- Structure: HOOK → PROBLÈME → ESCALADE → TWIST → PAYOFF
- Fin: surprise/question/débat/retournement pour provoquer les commentaires
- Score total DOIT être >= 45/50

Réponds UNIQUEMENT avec du JSON valide, zéro texte autour, zéro balise markdown."""


def _extract_json(text: str) -> dict:
    """Parse JSON robuste — gère les modèles qui ajoutent du texte autour."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Chercher le premier bloc {...}
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    # Nettoyer les balises markdown
    clean = re.sub(r'```(?:json)?\s*', '', text).rstrip('`').strip()
    return json.loads(clean)


async def generate_storyboard(topic: str, duration: int, style: str, visual_style: str = "cinematic") -> dict:
    """
    Génère un storyboard complet:
    - narration voix-off pour TTS
    - scènes avec phase/émotion/caméra/pexels_query/video_prompt
    - scores Hook/Émotion/Rétention/Visuel/Partageabilité (/50)
    Auto-réécrit si score < 45.
    """
    from app.services.groq_client import chat

    visual_desc = VISUAL_STYLES.get(visual_style, VISUAL_STYLES["cinematic"])
    n_scenes = max(5, min(duration // 2, 20))

    user_prompt = f"""Sujet: "{topic}"
Style narratif: {style}
Style visuel: {visual_style} — {visual_desc}
Durée totale: {duration} secondes
Nombre de scènes cible: ~{n_scenes} (chaque scène = 1 à 4 secondes)

Structure virale obligatoire:
- 0-3s: HOOK (stoppe le scroll — choc, curiosité, contradiction, question)
- 3-8s: PROBLÈME (creuse la douleur ou la curiosité)
- 8-12s: ESCALADE (tension montante)
- 12-16s: TWIST (retournement inattendu)
- 16+s: PAYOFF (résolution + fin provocatrice pour commentaires)

Génère ce JSON exact (la somme des durées des scènes doit être égale à {duration}):
{{
  "style": "{visual_style}",
  "dominant_emotion": "émotion principale de la vidéo",
  "narration": "texte narration voix-off complet en français — oral, phrases courtes 4-7 mots, pas de listes ni tirets ni markdown, fluide à l'oral",
  "scenes": [
    {{
      "scene": 1,
      "duration": 3,
      "phase": "HOOK",
      "emotion": "surprise",
      "camera": "zoom_in",
      "action": "description précise de l'action visible à l'écran",
      "pexels_query": "3 english keywords for Pexels video search",
      "video_prompt": "Optimized English prompt for Kling/Veo/Sora: [{visual_style} visual style], [subject/character with detail], [setting/environment], [lighting description], [camera: slow zoom in], [emotion: shocked/surprised], [4K ultra-detailed, cinematic, vertical 9:16 format]"
    }}
  ],
  "scores": {{
    "hook": 9,
    "emotion": 8,
    "retention": 9,
    "visual": 8,
    "shareability": 9,
    "total": 43
  }}
}}"""

    loop = asyncio.get_running_loop()

    for attempt in range(3):
        try:
            resp = await loop.run_in_executor(
                None,
                lambda: chat(
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    max_tokens=3000,
                    temperature=0.85 if attempt == 0 else 0.7,
                )
            )

            data = _extract_json(resp)

            if not data.get("scenes") or not data.get("narration"):
                print(f"[STORYBOARD] Tentative {attempt + 1}: structure JSON invalide")
                continue

            score = data.get("scores", {}).get("total", 0)
            if score < 45 and attempt < 2:
                print(f"[STORYBOARD] Score {score}/50 insuffisant, réécriture automatique...")
                continue

            n = len(data["scenes"])
            print(f"[STORYBOARD] OK — {n} scènes, score {score}/50, style {visual_style}")
            return data

        except Exception as e:
            print(f"[STORYBOARD] Tentative {attempt + 1} échouée: {e}")

    raise RuntimeError("Storyboard generation failed after 3 attempts")
