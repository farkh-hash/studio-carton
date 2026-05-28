import anthropic
from app.core.config import settings

SYSTEM_PROMPT = """Tu es un expert en création de contenu viral pour TikTok, Reels et Shorts.
Tu génères des scripts courts, percutants et optimisés pour la rétention.
Règles absolues :
- Hook ultra fort dans les 3 premières secondes
- Phrases courtes, rythme rapide
- Pas de remplissage, chaque mot compte
- CTA clair à la fin
- Langue : français naturel et dynamique"""


async def generate_script(topic: str, duration: int = 60, style: str = "viral") -> str:
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    prompt = f"""Génère un script pour une vidéo de {duration} secondes sur : "{topic}"
Style : {style}

Format de réponse — uniquement le texte à lire à voix haute, découpé en 3 parties séparées par des sauts de ligne :

[HOOK - 3 secondes]
Une phrase choc qui accroche immédiatement.

[CONTENU - {duration - 10} secondes]
Développement rapide avec des informations concrètes et surprenantes.

[CTA - 5 secondes]
Appel à l'action direct (abonner, commenter, partager).

Retourne UNIQUEMENT le texte à lire, sans crochets ni annotations."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()
