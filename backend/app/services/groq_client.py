from groq import Groq
from app.core.config import settings


def chat(messages: list, max_tokens: int = 2000, temperature: float = 0.8, system: str = None) -> str:
    """
    Appel Groq avec fallback automatique sur le modèle léger si rate limit.
    """
    client = Groq(api_key=settings.GROQ_API_KEY)

    if system:
        messages = [{"role": "system", "content": system}] + messages

    for model in [settings.GROQ_MODEL_PRIMARY, settings.GROQ_MODEL_FALLBACK]:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            err = str(e)
            if "rate_limit" in err or "429" in err:
                print(f"[GROQ] Rate limit sur {model}, fallback...")
                continue
            raise

    raise RuntimeError("Tous les modèles Groq sont en rate limit. Réessaie dans quelques minutes.")
