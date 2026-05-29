from groq import Groq
from app.core.config import settings

# Formules de hooks viraux prouvées
HOOK_FORMULAS = {
    "curiosite": [
        "La plupart des gens ignorent que {topic}...",
        "Personne ne te dit la vérité sur {topic}.",
        "Ce que j'ai découvert sur {topic} va te choquer.",
        "Tu ne sais pas encore ça sur {topic}.",
    ],
    "choc": [
        "J'ai testé {topic} pendant 30 jours. Le résultat m'a surpris.",
        "Arrête tout. Ce que tu crois sur {topic} est faux.",
        "{topic} : le mensonge qu'on te cache depuis des années.",
        "Ils ne veulent pas que tu saches ça sur {topic}.",
    ],
    "identification": [
        "Si tu rates encore {topic}, lis ça maintenant.",
        "Tu fais cette erreur avec {topic} sans le savoir.",
        "Pourquoi tu échoues avec {topic} (et comment arrêter).",
        "Toi aussi tu galères avec {topic} ? Regarde ça.",
    ],
    "resultat": [
        "La méthode exacte pour réussir {topic} en moins de 7 jours.",
        "Comment j'ai transformé {topic} en résultats concrets.",
        "Le secret des gens qui réussissent avec {topic}.",
        "3 étapes pour maîtriser {topic} une fois pour toutes.",
    ],
    "contre_intuitif": [
        "Arrête de faire ça si tu veux vraiment {topic}.",
        "La chose que tout le monde fait avec {topic} est une erreur.",
        "Moins tu travailles {topic}, plus tu réussis. Voilà pourquoi.",
        "L'erreur numéro 1 que tout le monde fait avec {topic}.",
    ],
}

# Structure par durée
STRUCTURES = {
    30:  {"hook": 3,  "points": 1, "content": 20, "cta": 7},
    60:  {"hook": 4,  "points": 3, "content": 44, "cta": 12},
    90:  {"hook": 5,  "points": 4, "content": 68, "cta": 17},
    120: {"hook": 5,  "points": 5, "content": 95, "cta": 20},
    180: {"hook": 5,  "points": 7, "content": 150, "cta": 25},
}

# Consignes par style
STYLE_INSTRUCTIONS = {
    "viral": "Rythme ultra rapide. Phrases de max 8 mots. Chaque phrase crée une tension ou une curiosité. Pas de fioritures.",
    "educatif": "Ton clair et pédagogique. Donne des faits précis, des chiffres, des exemples concrets. Structure logique.",
    "storytelling": "Raconte une histoire personnelle ou un scénario réel. Créer de l'émotion. Début → tension → résolution.",
    "humour": "Ton décalé et fun. Jeux de mots, situation absurde, autodérision. Faire sourire tout en informant.",
}

SYSTEM_PROMPT = """Tu es un expert des contenus viraux TikTok, YouTube Shorts et Instagram Reels.
Tu crées des scripts optimisés pour la rétention maximale et le passage à l'action.

Tes règles absolues :
- Le hook doit accrocher dans les 2 PREMIÈRES secondes ou le spectateur part
- Chaque phrase justifie la suivante (technique de la boucle ouverte)
- Phrases courtes : maximum 10 mots par phrase
- Zéro mot inutile, zéro remplissage
- Le CTA doit être naturel, pas forcé
- Langue : français parlé, naturel, dynamique — pas académique"""


def _get_structure_prompt(duration: int) -> dict:
    durations = sorted(STRUCTURES.keys())
    closest = min(durations, key=lambda d: abs(d - duration))
    return STRUCTURES[closest]


async def generate_script(topic: str, duration: int = 60, style: str = "viral") -> str:
    client = Groq(api_key=settings.GROQ_API_KEY)
    struct = _get_structure_prompt(duration)
    style_note = STYLE_INSTRUCTIONS.get(style, STYLE_INSTRUCTIONS["viral"])

    prompt = f"""Crée un script pour une vidéo courte de {duration} secondes.

SUJET : {topic}
STYLE : {style_note}

STRUCTURE OBLIGATOIRE :
- HOOK ({struct['hook']} secondes) : Une phrase d'accroche qui crée un choc, de la curiosité ou de l'identification. Le spectateur DOIT rester. Pas de "Bonjour", pas d'introduction. Directement dans le vif.
- CONTENU ({struct['content']} secondes) : {struct['points']} points clés maximum. Chaque point = 1-2 phrases max. Rythme soutenu. Informations utiles, surprenantes ou émotionnelles.
- CTA ({struct['cta']} secondes) : Appel à l'action naturel et fort (abonne-toi, commente, partage, like). Rattache-le au contenu.

RÈGLES :
- Écris UNIQUEMENT le texte à lire à voix haute
- Phrases courtes (max 10 mots)
- Pas de tirets, pas de numéros, pas de symboles
- Pas d'annotations comme [HOOK] ou [CTA]
- Langage parlé, familier mais professionnel
- Crée des boucles ouvertes (commence quelque chose, finit-le plus tard)

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
    """Génère un script en forçant un type de hook spécifique."""
    import random
    hooks = HOOK_FORMULAS.get(hook_type, HOOK_FORMULAS["curiosite"])
    forced_hook = random.choice(hooks).format(topic=topic)

    client = Groq(api_key=settings.GROQ_API_KEY)
    struct = _get_structure_prompt(duration)
    style_note = STYLE_INSTRUCTIONS.get(style, STYLE_INSTRUCTIONS["viral"])

    prompt = f"""Crée un script pour une vidéo de {duration} secondes.

SUJET : {topic}
STYLE : {style_note}

HOOK IMPOSÉ (tu dois commencer EXACTEMENT par cette phrase) :
"{forced_hook}"

STRUCTURE après le hook :
- CONTENU ({struct['content']} secondes) : {struct['points']} points clés, phrases courtes, rythme rapide.
- CTA ({struct['cta']} secondes) : appel à l'action fort et naturel.

RÈGLES :
- Commence par le hook imposé mot pour mot
- Uniquement le texte à lire, pas d'annotations
- Phrases courtes (max 10 mots)
- Langage parlé et naturel

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
