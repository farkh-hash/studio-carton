from groq import Groq
from app.core.config import settings

HOOK_TYPES = {
    "auto": "Choisis le meilleur type de hook pour ce sujet.",
    "curiosite": "Hook CURIOSITÉ : révèle quelque chose que personne ne sait. Court, mystérieux, crée un vide informationnel.",
    "choc": "Hook CHOC : déclaration audacieuse qui contredit une croyance commune. Surprenant et contre-intuitif.",
    "identification": "Hook IDENTIFICATION : parle directement à quelqu'un qui vit ce problème. Crée une reconnaissance immédiate.",
    "resultat": "Hook RÉSULTAT : promet un bénéfice concret avec un chiffre précis. Ex: 'X€ en Y jours', 'X% de [résultat]'.",
    "contre_intuitif": "Hook CONTRE-INTUITIF : contredit l'intuition commune. Ce que tout le monde fait est une erreur.",
    "nombre": "Hook NOMBRE : utilise un chiffre précis dès le début. '3 choses que 97% ignorent', '73% des gens font cette erreur'.",
    "urgence": "Hook URGENCE : crée un sentiment d'urgence ou de FOMO. 'Stop !', 'Avant qu'il soit trop tard', 'Si tu ne changes pas ça...'.",
}

# Nombre de mots cibles par durée (français parlé = ~130-140 mots/min)
WORD_COUNTS = {
    30: 65,
    60: 130,
    90: 195,
    120: 260,
    180: 390,
}

STYLE_INSTRUCTIONS = {
    "viral": "Rythme ultra rapide. Max 8 mots par phrase. Chaque phrase crée tension ou curiosité. Boucles ouvertes.",
    "educatif": "Clair et pédagogique. Faits précis avec chiffres. Structure logique progressive.",
    "storytelling": "Histoire personnelle ou scénario réel. Émotion d'abord. Début → tension → résolution → leçon.",
    "humour": "Ton décalé et fun. Situation absurde, autodérision. Informer en faisant sourire.",
}

SYSTEM_PROMPT = """Tu es un expert des contenus viraux TikTok, YouTube Shorts et Instagram Reels.
Tu crées des scripts COMPLETS optimisés pour 70%+ de rétention.

Règles absolues :
- Hook = les 2 PREMIÈRES secondes décident si le spectateur reste ou part
- Max 8-10 mots par phrase — jamais plus
- Chaque phrase crée l'envie d'entendre la suivante (boucle ouverte)
- Chiffres précis : "73%" pas "la plupart", "30 jours" pas "quelques semaines"
- Zéro mot inutile, zéro remplissage
- Français parlé naturel, pas académique
- Le script DOIT avoir le nombre de mots demandé pour remplir la durée"""


async def generate_script(topic: str, duration: int = 60, style: str = "viral", hook_type: str = "auto") -> str:
    from app.services.viral_research_service import research_viral_patterns
    client = Groq(api_key=settings.GROQ_API_KEY)

    target_words = WORD_COUNTS.get(duration, 130)
    style_note = STYLE_INSTRUCTIONS.get(style, STYLE_INSTRUCTIONS["viral"])
    hook_instruction = HOOK_TYPES.get(hook_type, HOOK_TYPES["auto"])

    hook_sec = min(5, duration // 10)
    cta_sec = min(10, duration // 8)
    content_sec = duration - hook_sec - cta_sec

    # Étape 1 : Recherche de vrais scripts viraux YouTube sur ce sujet
    research_context = ""
    try:
        from app.services.video_research_service import research_viral_scripts
        research = await research_viral_scripts(topic)
        print(f"[SCRIPT] Research: {research.get('videos_found', 0)} vidéos, {research.get('transcripts_extracted', 0)} transcripts")

        if research.get("best_hooks") or research.get("viral_patterns"):
            research_context = f"""
ANALYSE DE VRAIS SCRIPTS VIRAUX SUR CE SUJET (inspiré de YouTube) :
- Hooks qui cartonnent vraiment : {' | '.join(research.get('best_hooks', [])[:3])}
- Patterns viraux récurrents : {' | '.join(research.get('viral_patterns', [])[:3])}
- Faits concrets à intégrer : {' | '.join(research.get('key_facts', [])[:3])}
- Ton qui marche : {research.get('tone', 'viral et direct')}
- Structure narrative gagnante : {research.get('structure', 'hook fort + contenu dense + CTA')}
- À éviter absolument : {' | '.join(research.get('avoided', []))}

IMPORTANT : inspire-toi FORTEMENT de ces patterns réels pour créer quelque chose de similaire mais unique.
"""
    except Exception as e:
        print(f"[SCRIPT] Recherche vidéos échouée: {e}")

    prompt = f"""Crée un script VIRAL de {duration} secondes (~{target_words} mots).

SUJET : {topic}
STYLE : {style_note}
{research_context}

HOOK ({hook_sec}s) :
{hook_instruction}
- Maximum 10 mots
- PAS de "Bonjour", PAS d'introduction — directement dans le vif
- Utilise les patterns viraux analysés ci-dessus
- Déclenche immédiatement l'émotion cible
- N'utilise PAS le titre du sujet mot pour mot

CONTENU ({content_sec}s) :
- Intègre les faits clés et angles viraux de la recherche
- Parle directement à la douleur de l'audience
- Faits précis avec chiffres (73%, 30 jours, 500€)
- Phrases courtes max 8 mots
- Boucles ouvertes entre chaque point — maintiens la tension

CTA ({cta_sec}s) :
- Utilise le CTA viral identifié
- Question qui provoque des commentaires
- Naturel, pas forcé

RÈGLES ABSOLUES :
- UNIQUEMENT le texte à dire à voix haute — comme si tu parlais à un ami
- PHRASES COMPLÈTES avec sujet + verbe + complément — jamais de fragments
- INTERDIT : listes, tirets, numéros, bullet points, annotations
- INTERDIT : phrases de moins de 5 mots sauf le hook
- Environ {target_words} mots — le script DOIT être long enough pour {duration} secondes
- Langage parlé naturel français — conversationnel, pas des titres
- Commence directement par le hook, sans préambule
- EXEMPLE de bon rythme : "Tu ne sais pas encore que 73% des gens qui essaient l'IA perdent du temps à cause d'une seule erreur. Et cette erreur, tout le monde la fait."
- Écris le SCRIPT COMPLET du début à la fin"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        max_tokens=2500,
        temperature=0.85,
    )
    return response.choices[0].message.content.strip()
