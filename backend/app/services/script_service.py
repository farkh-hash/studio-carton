from groq import Groq
from app.core.config import settings

# Formules de hooks validées par les données 2025-2026
# Source : études rétention TikTok, 80% du succès = 3 premières secondes
HOOK_FORMULAS = {
    "curiosite": [
        "Ce que personne ne te dit sur {topic}...",
        "La vérité cachée sur {topic} que tu dois savoir.",
        "Tu ne sais pas encore ça sur {topic} et c'est dommage.",
        "Voici pourquoi tu te trompes complètement sur {topic}.",
        "Ce que les experts de {topic} font en secret.",
    ],
    "choc": [
        "Arrête tout. Ce que tu crois sur {topic} est faux.",
        "{topic} : le mensonge qu'on te cache depuis des années.",
        "J'ai testé {topic} pendant 30 jours. Le résultat m'a choqué.",
        "Ils ne veulent pas que tu saches ça sur {topic}.",
        "Le truc sur {topic} que tu ne verras jamais en école.",
    ],
    "identification": [
        "Si tu rates encore {topic}, lis ça maintenant.",
        "Tu fais cette erreur avec {topic} sans le savoir.",
        "Pourquoi tu échoues avec {topic} (et comment arrêter).",
        "Toi aussi tu galères avec {topic} ? Regarde ça.",
        "Si tu veux vraiment maîtriser {topic}, écoute bien.",
    ],
    "resultat": [
        "La méthode exacte pour {topic} en moins de 7 jours.",
        "Comment j'ai transformé {topic} en résultats concrets.",
        "Le secret des gens qui réussissent avec {topic}.",
        "3 étapes pour maîtriser {topic} une fois pour toutes.",
        "Ce que font différemment les 1% qui réussissent en {topic}.",
    ],
    "contre_intuitif": [
        "Arrête de faire ça si tu veux vraiment {topic}.",
        "Moins tu travailles {topic}, plus tu réussis. Voilà pourquoi.",
        "L'erreur numéro 1 que tout le monde fait avec {topic}.",
        "Tout ce qu'on t'a dit sur {topic} est faux.",
        "La chose que tout le monde fait avec {topic} est une erreur.",
    ],
    "nombre": [
        "3 choses sur {topic} que tu dois savoir MAINTENANT.",
        "5 erreurs qui ruinent tes chances avec {topic}.",
        "En 60 secondes tu vas tout comprendre sur {topic}.",
        "7 faits sur {topic} qui vont changer ta vision.",
        "Les 3 secrets de {topic} que personne ne partage.",
    ],
    "urgence": [
        "Stop ! Regarde ça avant de te lancer dans {topic}.",
        "Avant qu'il soit trop tard pour {topic}, lis ça.",
        "Si tu ne changes pas ça sur {topic} maintenant, tu vas regretter.",
        "C'est maintenant ou jamais pour {topic}.",
        "Tu as 3 minutes pour tout savoir sur {topic}.",
    ],
}

# Structure par durée — basée sur les benchmarks de rétention 2025
# Objectif : 70% à 3s, 60% à 15s, 50% à 30s
STRUCTURES = {
    30:  {"hook_sec": 3,  "points": 1, "content_sec": 20, "cta_sec": 7},
    60:  {"hook_sec": 4,  "points": 3, "content_sec": 44, "cta_sec": 12},
    90:  {"hook_sec": 5,  "points": 4, "content_sec": 68, "cta_sec": 17},
    120: {"hook_sec": 5,  "points": 5, "content_sec": 95, "cta_sec": 20},
    180: {"hook_sec": 5,  "points": 7, "content_sec": 150, "cta_sec": 25},
}

STYLE_INSTRUCTIONS = {
    "viral": "Rythme ultra rapide. Max 8 mots par phrase. Chaque phrase crée tension ou curiosité. Boucles ouvertes. Zéro fioritures.",
    "educatif": "Clair et pédagogique. Faits précis avec chiffres et exemples. Structure logique progressive.",
    "storytelling": "Histoire personnelle ou scénario réel. Émotion d'abord. Début → tension → résolution → leçon.",
    "humour": "Ton décalé et fun. Situation absurde, autodérision, jeux de mots. Informer en faisant sourire.",
}

# Techniques de rétention validées (données 2025)
RETENTION_TECHNIQUES = """
Techniques de rétention à appliquer :
- BOUCLE OUVERTE : pose une question ou une promesse dès le hook, réponds-y à la fin
- MICRO-CLIFFHANGERS : chaque phrase donne envie d'entendre la suivante
- PATTERN INTERRUPT : change de rythme ou d'angle pour garder l'attention
- CHIFFRES PRÉCIS : "83% des gens" au lieu de "la plupart des gens"
- MOTS INTERDITS : jamais "donc", "alors", "en conclusion" — ils signalent la fin"""

SYSTEM_PROMPT = f"""Tu es un expert des contenus viraux TikTok, YouTube Shorts et Instagram Reels.
Tu crées des scripts optimisés pour un taux de rétention de 70%+ à 3 secondes.

Tes règles absolues :
- Hook = accroche dans les 2 PREMIÈRES secondes, sinon le spectateur part
- Chaque phrase justifie la suivante (technique boucle ouverte)
- Maximum 10 mots par phrase
- Zéro mot inutile, zéro remplissage
- CTA naturel, pas forcé
- Français parlé, naturel, pas académique

{RETENTION_TECHNIQUES}"""


def _get_structure(duration: int) -> dict:
    durations = sorted(STRUCTURES.keys())
    return STRUCTURES[min(durations, key=lambda d: abs(d - duration))]


async def generate_script(topic: str, duration: int = 60, style: str = "viral") -> str:
    client = Groq(api_key=settings.GROQ_API_KEY)
    struct = _get_structure(duration)
    style_note = STYLE_INSTRUCTIONS.get(style, STYLE_INSTRUCTIONS["viral"])

    prompt = f"""Crée un script viral de {duration} secondes.

SUJET : {topic}
STYLE : {style_note}

STRUCTURE IMPOSÉE :
- HOOK ({struct['hook_sec']}s) : Phrase d'accroche directe, choc ou curiosité. PAS de "Bonjour", PAS d'introduction. Directement dans le vif. Le spectateur DOIT rester.
- CONTENU ({struct['content_sec']}s) : {struct['points']} points. Chaque point = 1-2 phrases max. Chiffres précis. Rythme soutenu. Boucles ouvertes entre les points.
- CTA ({struct['cta_sec']}s) : Appel à l'action ancré dans le contenu. Fort et naturel.

RÈGLES STRICTES :
- Uniquement le texte à dire à voix haute
- Phrases courtes (max 10 mots)
- Pas de tirets, numéros, crochets, annotations
- Langage parlé, familier mais professionnel
- Chiffres précis plutôt que vagues ("73%" pas "la plupart")

Commence directement par le hook, sans préambule."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        max_tokens=2048,
        temperature=0.85,
    )
    return response.choices[0].message.content.strip()


async def generate_script_with_hook(topic: str, duration: int, style: str, hook_type: str = "curiosite") -> str:
    import random
    hooks = HOOK_FORMULAS.get(hook_type, HOOK_FORMULAS["curiosite"])
    forced_hook = random.choice(hooks).format(topic=topic)

    client = Groq(api_key=settings.GROQ_API_KEY)
    struct = _get_structure(duration)
    style_note = STYLE_INSTRUCTIONS.get(style, STYLE_INSTRUCTIONS["viral"])

    prompt = f"""Crée un script de {duration} secondes.

SUJET : {topic}
STYLE : {style_note}

HOOK IMPOSÉ — commence EXACTEMENT par :
"{forced_hook}"

STRUCTURE après le hook :
- CONTENU ({struct['content_sec']}s) : {struct['points']} points clés, phrases courtes, rythme rapide, chiffres précis.
- CTA ({struct['cta_sec']}s) : appel à l'action fort et naturel.

RÈGLES : uniquement le texte à lire, pas d'annotations, phrases max 10 mots, langage parlé.

Continue directement après le hook imposé."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        max_tokens=2048,
        temperature=0.85,
    )
    return response.choices[0].message.content.strip()
