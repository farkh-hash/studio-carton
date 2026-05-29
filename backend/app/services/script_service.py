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
- HOOK ({struct['hook_sec']}s) : Phrase d'accroche directe, choc ou curiosité. PAS de "Bonjour", PAS d'introduction. Le spectateur DOIT rester. Max 10 mots. N'utilise PAS le titre du sujet mot pour mot — reformule en concept court et percutant.
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


def _extract_concept(topic: str, client) -> str:
    """Extrait un concept court (2-4 mots) du sujet pour construire le hook."""
    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": f"Résume ce sujet en 2-4 mots maximum (concept clé uniquement, pas de phrase) : '{topic}'. Réponds UNIQUEMENT avec les mots, rien d'autre."}],
        max_tokens=15,
        temperature=0.3,
    )
    return r.choices[0].message.content.strip().strip('"').strip("'")


def _generate_hook(topic: str, hook_type: str, client) -> str:
    """Génère un hook percutant adapté au sujet — pas de template littéral."""
    concept = _extract_concept(topic, client)
    hook_descriptions = {
        "curiosite": "Formule curiosité : révèle quelque chose que personne ne sait. Ex: 'Ce que personne ne te dit sur [concept court]...' ou 'La vérité cachée sur [concept] va tout changer.'",
        "choc": "Formule choc/surprise : déclaration audacieuse qui contredit une croyance. Ex: 'Tout ce qu'on t'a dit sur [concept] est faux.' ou 'J'ai testé X pendant 30 jours. Le résultat m'a choqué.'",
        "identification": "Formule identification : parle directement à quelqu'un qui galère. Ex: 'Tu fais encore cette erreur avec [concept] ?' ou 'Si tu rates [concept], lis ça maintenant.'",
        "resultat": "Formule résultat promis : promet un résultat concret avec chiffre précis. Ex: 'La méthode exacte pour [résultat chiffré] en [durée].' ou 'Comment passer de 0 à X en Y jours.'",
        "contre_intuitif": "Formule contre-intuitif : contredit l'intuition. Ex: 'Arrête de faire ça si tu veux [résultat].' ou 'Moins tu travailles sur [concept], plus tu réussis.'",
        "nombre": "Formule nombre : utilise un chiffre précis dès le début. Ex: '3 choses sur [concept] que 97% des gens ignorent.' ou 'En 60 secondes tu vas tout comprendre sur [concept].'",
        "urgence": "Formule urgence : crée un sentiment d'urgence ou de FOMO. Ex: 'Stop ! Regarde ça avant de te lancer dans [concept].' ou 'Si tu ne changes pas ça maintenant, tu vas regretter.'",
    }

    desc = hook_descriptions.get(hook_type, hook_descriptions["curiosite"])

    prompt = f"""Génère UN SEUL hook d'accroche pour une vidéo TikTok.

SUJET : "{topic}"
CONCEPT CLÉ (utilise ce mot/groupe court dans le hook) : "{concept}"
Type de hook : {desc}

RÈGLES STRICTES :
- Maximum 12 mots
- Commence directement par l'accroche, aucune introduction
- Utilise des mots courts et percutants
- Chiffre précis si possible (ex: "83%", "30 jours", "3 erreurs")
- Crée une boucle ouverte : le spectateur DOIT regarder la suite pour comprendre
- Utilise le CONCEPT CLÉ (2-4 mots), PAS le titre complet du sujet
- NE RÉPÈTE JAMAIS le titre complet verbatim
- Langue : français naturel parlé

Retourne UNIQUEMENT la phrase d'accroche, rien d'autre."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=60,
        temperature=0.9,
    )
    return response.choices[0].message.content.strip().strip('"').strip("'")


async def generate_script_with_hook(topic: str, duration: int, style: str, hook_type: str = "curiosite") -> str:
    client = Groq(api_key=settings.GROQ_API_KEY)
    struct = _get_structure(duration)
    style_note = STYLE_INSTRUCTIONS.get(style, STYLE_INSTRUCTIONS["viral"])

    # Générer un hook propre et adapté au sujet
    hook = _generate_hook(topic, hook_type, client)

    prompt = f"""Crée un script de {duration} secondes.

SUJET : {topic}
STYLE : {style_note}

HOOK IMPOSÉ — commence EXACTEMENT par :
"{hook}"

STRUCTURE après le hook :
- CONTENU ({struct['content_sec']}s) : {struct['points']} points clés, phrases courtes (max 8 mots), rythme rapide, chiffres précis.
- CTA ({struct['cta_sec']}s) : question engageante + appel à l'action naturel.

RÈGLES : uniquement le texte à lire, pas d'annotations, langage parlé naturel.

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
