import asyncio
from groq import Groq
from app.core.config import settings

WORD_COUNTS = {30: 70, 60: 140, 90: 210, 120: 280, 180: 420}

STYLE_INSTRUCTIONS = {
    "viral": "Rythme ultra rapide. Max 8 mots par phrase. Chaque phrase crée tension ou curiosité. Boucles ouvertes.",
    "educatif": "Clair et pédagogique. Faits précis avec chiffres. Structure logique progressive.",
    "storytelling": "Histoire personnelle ou scénario réel. Émotion d'abord. Début → tension → résolution → leçon.",
    "humour": "Ton décalé et fun. Situation absurde, autodérision. Informer en faisant sourire.",
}

SYSTEM_PROMPT = """Tu es un expert des contenus viraux TikTok, YouTube Shorts et Instagram Reels.
Tu crées des scripts COMPLETS, FLUIDES et PERCUTANTS — jamais des bullet points, toujours de la vraie parole naturelle.

Règles absolues :
- PHRASES COMPLÈTES avec sujet + verbe + complément — jamais de fragments
- Max 8-10 mots par phrase sauf le hook
- Chaque phrase justifie la suivante (boucle ouverte)
- Chiffres précis : "73%" pas "la plupart"
- Zéro fausse promesse — fort mais honnête
- Français parlé naturel, conversationnel"""


async def _run_all_research(topic: str, style: str) -> dict:
    """
    Lance tous les agents de recherche en parallèle.
    Agent 1: Analyse profonde des vrais scripts
    Agent 2: 5 hooks testés et scorés
    Agent 3: Persona/audience cible
    Agent 5: Analyse concurrents
    """
    from app.services.video_research_service import research_viral_scripts
    from app.services.script_analyzer_service import analyze_script_deeply, synthesize_analyses
    from app.services.hook_tester_service import generate_and_score_hooks
    from app.services.persona_service import build_persona
    from app.services.competitor_service import analyze_competitors

    print(f"[SCRIPT] Lancement recherche multi-agents pour: {topic}")

    # Lancer recherche vidéos + persona + concurrents en parallèle avec timeout
    async def safe_research():
        return await asyncio.wait_for(research_viral_scripts(topic), timeout=25)

    async def safe_persona():
        return await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(None, build_persona, topic, "tiktok"),
            timeout=15
        )

    async def safe_competitors():
        return await asyncio.wait_for(analyze_competitors(topic), timeout=20)

    research, persona, competitors = await asyncio.gather(
        safe_research(), safe_persona(), safe_competitors(),
        return_exceptions=True
    )

    if isinstance(research, Exception):
        research = {}
        print(f"[SCRIPT] Research failed: {research}")
    if isinstance(persona, Exception):
        persona = {}
    if isinstance(competitors, Exception):
        competitors = {}

    # Analyser en profondeur les transcripts obtenus (Agent 1)
    deep_analyses = []
    transcripts = research.get("transcripts", []) if isinstance(research, dict) else []
    for t in transcripts[:3]:
        try:
            analysis = await asyncio.get_event_loop().run_in_executor(
                None, analyze_script_deeply, t.get("text", ""), t.get("title", "")
            )
            if analysis:
                deep_analyses.append(analysis)
        except Exception:
            pass

    synthesis = {}
    if deep_analyses:
        try:
            synthesis = await asyncio.get_event_loop().run_in_executor(
                None, synthesize_analyses, deep_analyses
            )
        except Exception:
            pass

    # Générer et scorer 5 hooks (Agent 2)
    analysis_context = synthesis.get("key_insight", "") if synthesis else ""
    hooks = []
    try:
        hooks = await asyncio.get_event_loop().run_in_executor(
            None, generate_and_score_hooks, topic, analysis_context
        )
    except Exception:
        pass

    print(f"[SCRIPT] Research: {research.get('videos_found', 0) if isinstance(research, dict) else 0} vidéos | Deep analyses: {len(deep_analyses)} | Hooks: {len(hooks)} | Persona: {'OK' if persona else 'KO'} | Competitors: {'OK' if competitors else 'KO'}")

    return {
        "research": research if isinstance(research, dict) else {},
        "synthesis": synthesis,
        "hooks": hooks,
        "persona": persona if isinstance(persona, dict) else {},
        "competitors": competitors if isinstance(competitors, dict) else {},
    }


def _build_mega_context(data: dict, topic: str) -> str:
    """Construit le contexte complet pour la génération du script."""
    parts = []

    # Agent 1 — Patterns prouvés
    synthesis = data.get("synthesis", {})
    if synthesis:
        parts.append("=== PATTERNS PROUVÉS DES VRAIS SCRIPTS VIRAUX ===")
        if synthesis.get("dominant_hook_type"):
            parts.append(f"Type de hook dominant : {synthesis['dominant_hook_type']}")
        if synthesis.get("proven_hook_formula"):
            parts.append(f"Formule de hook prouvée : {synthesis['proven_hook_formula']}")
        if synthesis.get("recurring_power_words"):
            parts.append(f"Mots puissants récurrents : {', '.join(synthesis['recurring_power_words'])}")
        if synthesis.get("emotional_pattern"):
            parts.append(f"Arc émotionnel dominant : {synthesis['emotional_pattern']}")
        if synthesis.get("common_retention_technique"):
            parts.append(f"Technique rétention prouvée : {synthesis['common_retention_technique']}")
        if synthesis.get("optimal_rhythm"):
            parts.append(f"Rythme optimal : {synthesis['optimal_rhythm']}")
        if synthesis.get("proven_cta"):
            parts.append(f"CTA prouvé : {synthesis['proven_cta']}")
        if synthesis.get("key_insight"):
            parts.append(f"Insight clé : {synthesis['key_insight']}")

    # Agent 2 — Meilleur hook
    hooks = data.get("hooks", [])
    if hooks:
        best_hook = hooks[0]
        parts.append(f"\n=== MEILLEUR HOOK TESTÉ ET SCORÉ (score: {best_hook.get('score', '?')}/10) ===")
        parts.append(f"Hook : \"{best_hook.get('hook', '')}\"")
        parts.append(f"Type : {best_hook.get('type', '')} | Trigger : {best_hook.get('trigger', '')}")
        parts.append(f"Pourquoi il accroche : {best_hook.get('why', '')}")
        if len(hooks) > 1:
            parts.append(f"Hook alternatif : \"{hooks[1].get('hook', '')}\" (score: {hooks[1].get('score', '?')}/10)")

    # Agent 3 — Persona
    persona = data.get("persona", {})
    if persona:
        parts.append(f"\n=== PROFIL DU SPECTATEUR CIBLE ===")
        if persona.get("profile"):
            parts.append(f"Profil : {persona['profile']}")
        if persona.get("main_pain"):
            parts.append(f"Douleur principale : {persona['main_pain']}")
        if persona.get("main_desire"):
            parts.append(f"Désir profond : {persona['main_desire']}")
        if persona.get("trigger_emotion"):
            parts.append(f"Émotion déclencheuse : {persona['trigger_emotion']}")
        if persona.get("scroll_stopper"):
            parts.append(f"Ce qui l'arrête : {persona['scroll_stopper']}")
        if persona.get("language"):
            parts.append(f"Son vocabulaire : {persona['language']}")

    # Agent 5 — Concurrents
    competitors = data.get("competitors", {})
    if competitors:
        parts.append(f"\n=== ANALYSE CONCURRENTS ===")
        if competitors.get("gap_opportunity"):
            parts.append(f"Opportunité non exploitée : {competitors['gap_opportunity']}")
        if competitors.get("differentiation"):
            parts.append(f"Comment se différencier : {competitors['differentiation']}")
        if competitors.get("successful_title_patterns"):
            parts.append(f"Patterns titres qui marchent : {' | '.join(competitors['successful_title_patterns'][:2])}")

    # Recherche brute
    research = data.get("research", {})
    if research.get("best_hooks"):
        parts.append(f"\n=== HOOKS VIRAUX DES VRAIES VIDÉOS ===")
        for h in research["best_hooks"][:3]:
            parts.append(f"- {h}")
    if research.get("key_facts"):
        parts.append(f"\n=== FAITS RÉELS À INTÉGRER ===")
        for f in research["key_facts"][:3]:
            parts.append(f"- {f}")

    return "\n".join(parts)


async def generate_script(topic: str, duration: int = 60, style: str = "viral", hook_type: str = "auto") -> str:
    """
    Génère un script viral en utilisant les 5 agents :
    1. Analyse profonde des vrais scripts
    2. Multi-hook testé et scoré
    3. Persona/audience ciblée
    4. (Validateur intégré dans pipeline_service)
    5. Analyse concurrents
    """
    target_words = WORD_COUNTS.get(duration, 140)
    style_note = STYLE_INSTRUCTIONS.get(style, STYLE_INSTRUCTIONS["viral"])

    hook_sec = min(5, duration // 10)
    cta_sec = min(10, duration // 8)
    content_sec = duration - hook_sec - cta_sec

    # Lancer tous les agents en parallèle
    try:
        data = await _run_all_research(topic, style)
        mega_context = _build_mega_context(data, topic)
    except Exception as e:
        print(f"[SCRIPT] Erreur agents: {e}")
        mega_context = ""
        data = {}

    # Utiliser le meilleur hook généré par l'Agent 2
    best_hook = ""
    if data.get("hooks"):
        best_hook = data["hooks"][0].get("hook", "")

    client = Groq(api_key=settings.GROQ_API_KEY)

    prompt = f"""Crée un script viral COMPLET et FLUIDE de {duration} secondes (~{target_words} mots).

SUJET : {topic}
STYLE : {style_note}

{mega_context}

STRUCTURE :
- HOOK ({hook_sec}s) : {"Utilise ce hook prouvé : \"" + best_hook + "\"" if best_hook else "Utilise les patterns prouvés ci-dessus pour créer un hook ultra-fort"}
- CONTENU ({content_sec}s) : développe en utilisant les faits réels, la douleur du persona, les techniques de rétention prouvées
- CTA ({cta_sec}s) : utilise le CTA prouvé, question engageante

RÈGLES ABSOLUES :
- PHRASES COMPLÈTES — jamais de fragments ou bullet points
- Max 8-10 mots par phrase
- {target_words} mots minimum — script COMPLET du début à la fin
- Langage parlé naturel, conversationnel
- Zéro fausse promesse
- Commence directement par le hook, aucun préambule
- EXEMPLE de bon rythme : "73% des gens qui essaient ça font une erreur fatale. Et personne ne leur dit laquelle. Jusqu'à aujourd'hui."

Écris le script complet maintenant :"""

    def _call_groq():
        return client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=3000,
            temperature=0.82,
        )

    loop = asyncio.get_event_loop()
    response = await asyncio.wait_for(
        loop.run_in_executor(None, _call_groq),
        timeout=45
    )
    return response.choices[0].message.content.strip()
