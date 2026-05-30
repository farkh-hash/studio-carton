"""
Client LLM unifie avec cascade automatique :
1. Ollama local (GPU) si OLLAMA_URL est configure
2. Groq llama-3.3-70b (gratuit, haute qualite)
3. Groq llama-3.1-8b  (500k tokens/jour, fallback)
4. Groq gemma2-9b     (backup final)
"""
from app.core.config import settings
from groq import Groq

GROQ_FALLBACK_MODELS = [
    settings.GROQ_MODEL_PRIMARY,   # llama-3.3-70b-versatile
    settings.GROQ_MODEL_FALLBACK,  # llama-3.1-8b-instant
    "gemma2-9b-it",
]


def _call_ollama(messages: list, max_tokens: int, temperature: float) -> str:
    """Appel vers Ollama local (GPU)."""
    import httpx
    import json as _json
    payload = {
        "model": settings.OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature, "num_predict": max_tokens},
    }
    resp = httpx.post(
        f"{settings.OLLAMA_URL.rstrip('/')}/api/chat",
        json=payload,
        timeout=300,
    )
    resp.raise_for_status()
    data = _json.loads(resp.content.decode("utf-8"))
    return data["message"]["content"].strip()


def chat(messages: list, max_tokens: int = 2000, temperature: float = 0.8, system: str = None) -> str:
    """Appel LLM : Ollama GPU -> Groq 70B -> Groq 8B -> Gemma2"""
    if system:
        messages = [{"role": "system", "content": system}] + messages

    # 1. Ollama local en priorite (GPU, illimite)
    if settings.OLLAMA_URL:
        try:
            result = _call_ollama(messages, max_tokens, temperature)
            print(f"[LLM] Ollama ({settings.OLLAMA_MODEL}) OK")
            return result
        except Exception as e:
            print(f"[LLM] Ollama indisponible ({type(e).__name__}) -> fallback Groq")

    # 2. Groq avec cascade de modeles
    client = Groq(api_key=settings.GROQ_API_KEY)
    for model in GROQ_FALLBACK_MODELS:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            if model != settings.GROQ_MODEL_PRIMARY:
                print(f"[LLM] Groq fallback: {model}")
            return response.choices[0].message.content.strip()
        except Exception as e:
            err = str(e)
            if "rate_limit" in err or "429" in err or "rate limit" in err.lower():
                print(f"[LLM] Rate limit {model} -> suivant...")
                continue
            raise

    raise RuntimeError("Tous les LLM sont indisponibles. Reessaie dans 30 minutes.")
