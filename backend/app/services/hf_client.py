"""
Hugging Face Inference API — génération vidéo gratuite.
Utilise router.huggingface.co (nouvelle URL, résout les problèmes DNS).

Modèles supportés (gratuits) :
  - damo-vilab/text-to-video-ms-1.7b  (rapide, 256x256)
  - cerspense/zeroscope_v2_576w        (meilleure qualité, 576x320)
"""
import asyncio
import httpx

from app.core.config import settings

_TIMEOUT = 300
# Nouvelle URL qui contourne les problèmes DNS
_ROUTER_BASE = "https://router.huggingface.co/hf-inference/models"


async def generate_video(prompt: str) -> bytes:
    url = f"{_ROUTER_BASE}/{settings.HF_MODEL}"
    headers = {"Authorization": f"Bearer {settings.HF_API_TOKEN}"}
    payload = {"inputs": prompt, "options": {"wait_for_model": True}}

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        for attempt in range(3):
            resp = await client.post(url, json=payload, headers=headers)

            # Modèle en cours de chargement → attendre et réessayer
            if resp.status_code == 503:
                try:
                    wait = resp.json().get("estimated_time", 20)
                except Exception:
                    wait = 20
                await asyncio.sleep(min(wait, 30))
                continue

            resp.raise_for_status()

            content_type = resp.headers.get("content-type", "")
            if "video" in content_type or len(resp.content) > 1000:
                return resp.content

            raise ValueError(f"Réponse inattendue ({resp.status_code}): {resp.text[:300]}")

    raise RuntimeError("Le modèle n'a pas répondu après 3 tentatives")
