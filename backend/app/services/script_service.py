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
    client = Groq(api_key=settings.GROQ_API_KEY)

    target_words = WORD_COUNTS.get(duration, 130)
    style_note = STYLE_INSTRUCTIONS.get(style, STYLE_INSTRUCTIONS["viral"])
    hook_instruction = HOOK_TYPES.get(hook_type, HOOK_TYPES["auto"])

    # Structure proportionnelle à la durée
    hook_sec = min(5, duration // 10)
    cta_sec = min(10, duration // 8)
    content_sec = duration - hook_sec - cta_sec

    prompt = f"""Crée un script complet de {duration} secondes (~{target_words} mots).

SUJET : {topic}
STYLE : {style_note}

HOOK ({hook_sec}s) :
{hook_instruction}
- Maximum 10 mots
- PAS de "Bonjour", PAS d'introduction, directement dans le vif
- Le spectateur DOIT rester pour la suite
- N'utilise PAS le titre du sujet mot pour mot — reformule en concept court et percutant

CONTENU ({content_sec}s) :
- Développe avec des faits précis, chiffres concrets, exemples réels
- Phrases courtes (max 8 mots)
- Boucles ouvertes entre chaque point
- Rythme soutenu, pas de ralentissement

CTA ({cta_sec}s) :
- Question engageante liée au contenu
- Appel à l'action naturel (abonne, commente, partage)
- Pas forcé, intégré naturellement

RÈGLES CRITIQUES :
- Écris UNIQUEMENT le texte à dire à voix haute
- Pas d'annotations [HOOK], [CTA], pas de tirets, pas de numéros
- Langage parlé naturel
- Le script doit faire environ {target_words} mots — pas moins !
- Commence directement par le hook"""

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
