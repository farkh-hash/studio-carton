"""
Client LLM avec deux modes :
- chat()       : Ollama GPU (script) -> Groq fallback
- chat_fast()  : Groq uniquement (agents tendances/niches/monetisation)
"""
from app.core.config import settings
from groq import Groq

GROQ_FALLBACK_MODELS = [
    settings.GROQ_MODEL_PRIMARY,   # llama-3.3-70b-versatile
    settings.GROQ_MODEL_FALLBACK,  # llama-3.1-8b-instant
    "gemma2-9b-it",
]


def _call_ollama(messages: list, max_tokens: int, temperature: float) -> str:
    """Appel vers Ollama local (GPU) - pour la generation de scripts."""
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


def _call_groq(messages: list, max_tokens: int, temperature: float) -> str:
    """Appel Groq avec cascade de modeles."""
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
    raise RuntimeError("Tous les modeles Groq sont en rate limit.")


def chat(messages: list, max_tokens: int = 2000, temperature: float = 0.8, system: str = None) -> str:
    """
    Pour la generation de SCRIPTS : Ollama GPU d'abord, Groq en fallback.
    Ollama = meilleure qualite, pas de rate limit.
    """
    if system:
        messages = [{"role": "system", "content": system}] + messages

    if settings.OLLAMA_URL:
        try:
            result = _call_ollama(messages, max_tokens, temperature)
            print(f"[LLM] Ollama OK ({settings.OLLAMA_MODEL})")
            return result
        except Exception as e:
            print(f"[LLM] Ollama ({type(e).__name__}) -> Groq fallback")

    return _call_groq(messages, max_tokens, temperature)


def chat_fast(messages: list, max_tokens: int = 2000, temperature: float = 0.8, system: str = None) -> str:
    """
    Pour les AGENTS (tendances, niches, monetisation) : Groq uniquement.
    Rapide, pas de timeout Ollama sur les grands prompts.
    """
    if system:
        messages = [{"role": "system", "content": system}] + messages
    return _call_groq(messages, max_tokens, temperature)
