from groq import Groq
from app.core.config import settings

# Ordre de fallback : 70B (meilleure qualité) → 8B (500k tokens/jour) → gemma2 (backup)
FALLBACK_MODELS = [
    settings.GROQ_MODEL_PRIMARY,   # llama-3.3-70b-versatile
    settings.GROQ_MODEL_FALLBACK,  # llama-3.1-8b-instant
    "gemma2-9b-it",                # backup gratuit avec quotas élevés
]


def chat(messages: list, max_tokens: int = 2000, temperature: float = 0.8, system: str = None) -> str:
    """Appel Groq avec fallback automatique si rate limit."""
    client = Groq(api_key=settings.GROQ_API_KEY)

    if system:
        messages = [{"role": "system", "content": system}] + messages

    for model in FALLBACK_MODELS:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            if model != settings.GROQ_MODEL_PRIMARY:
                print(f"[GROQ] Utilisation modèle fallback : {model}")
            return response.choices[0].message.content.strip()
        except Exception as e:
            err = str(e)
            if "rate_limit" in err or "429" in err or "rate limit" in err.lower():
                print(f"[GROQ] Rate limit {model} → fallback suivant...")
                continue
            raise

    raise RuntimeError("Quota Groq épuisé sur tous les modèles. Réessaie dans 30 minutes.")
