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

SYSTEM_PROMPT = """Tu es le ghostwriter des créateurs TikTok francophones qui font des millions de vues.
Tes scripts arrêtent le scroll en moins de deux secondes. Chaque mot est calculé.

FORMAT OBLIGATOIRE :
- Phrases de 4 à 7 mots. Un point après chaque phrase.
- Pas de virgule. Jamais. Que des points.
- Jamais de tirets, listes, guillemets, parenthèses, astérisques.
- Jamais de "Voici", "Découvrez", "Dans cette vidéo", "Aujourd'hui".
- Chiffres TOUJOURS en lettres : "soixante-treize pourcent" pas "73%", "cinq cents euros" pas "500€".

TECHNIQUE NARRATIVE :
- Phrase 1 (hook) : fait choc ou question impossible à ignorer.
- Phrases 2-4 : creuser le problème. Rendre la douleur réelle.
- Milieu : révélation progressive. Chaque phrase ouvre une question.
- Fin : CTA naturel. Une question à laquelle tout le monde veut répondre.

SCRIPT PARFAIT exemple (finance, 60s) :
Tu perds de l'argent sans le savoir. Chaque mois. Automatiquement. Quatre-vingt-trois pourcent des Français ont ce problème. Et personne ne leur dit. Quand tu laisses ton argent sur un compte courant. Il perd de la valeur. Deux virgule cinq pourcent par an. C'est l'inflation. En dix ans. Tu as perdu vingt pourcent. Sans rien faire. Les gens qui s'enrichissent font l'inverse. Ils placent. Même cinquante euros par mois. Ça change tout. En vingt ans c'est cent vingt mille euros. Pas de chance. Juste une habitude. Est-ce que tu places déjà tes économies.

Génère UNIQUEMENT le texte à lire. Rien d'autre."""


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
            asyncio.get_running_loop().run_in_executor(None, build_persona, topic, "tiktok"),
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
            analysis = await asyncio.get_running_loop().run_in_executor(
                None, analyze_script_deeply, t.get("text", ""), t.get("title", "")
            )
            if analysis:
                deep_analyses.append(analysis)
        except Exception:
            pass

    synthesis = {}
    if deep_analyses:
        try:
            synthesis = await asyncio.get_running_loop().run_in_executor(
                None, synthesize_analyses, deep_analyses
            )
        except Exception:
            pass

    # Générer et scorer 5 hooks (Agent 2)
    analysis_context = synthesis.get("key_insight", "") if synthesis else ""
    hooks = []
    try:
        hooks = await asyncio.get_running_loop().run_in_executor(
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
    """Un seul appel Groq avec prompt béton — rapide, économe, qualité maximale."""
    from app.services.groq_client import chat as groq_chat

    target_words = WORD_COUNTS.get(duration, 140)
    style_note = STYLE_INSTRUCTIONS.get(style, STYLE_INSTRUCTIONS["viral"])

    prompt = f"""SUJET : {topic}
STYLE : {style_note}
DURÉE : {duration} secondes — EXACTEMENT {target_words} mots

STRUCTURE :
1. HOOK (5 mots max) : fait choc ou question impossible à ignorer. Commence directement.
2. DÉVELOPPEMENT : révélations enchaînées, chaque phrase force à écouter la suivante.
3. CTA final : question courte et engageante.

RÈGLES ABSOLUES — NE PAS DÉVIER :
- Phrases de 4 à 7 mots. Point après chaque phrase. JAMAIS de virgule.
- Chiffres en toutes lettres : "soixante-treize pourcent" pas "73%"
- JAMAIS : "Voici", "Découvrez", "Dans cette vidéo", "Aujourd'hui je vais"
- JAMAIS : listes, tirets, numéros, guillemets, parenthèses
- Langage oral, naturel, direct. Comme si tu parlais à un ami.
- LONGUEUR STRICTE : {target_words} mots (±5 mots maximum)

Écris le script maintenant, directement, sans titre ni commentaire :"""

    def _call():
        return groq_chat(
            messages=[{"role": "user", "content": prompt}],
            system=SYSTEM_PROMPT,
            max_tokens=2000,
            temperature=0.75,
        )

    loop = asyncio.get_running_loop()
    return await asyncio.wait_for(loop.run_in_executor(None, _call), timeout=45)
