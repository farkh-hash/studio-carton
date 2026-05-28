"""
Client Runway ML Gen-4 Turbo — génération vidéo virale haute qualité.
Endpoint text-to-video asynchrone avec polling.
"""
import asyncio
import httpx

from app.core.config import settings

_BASE = "https://api.runwayml.com/v1"
_HEADERS = {
    "Authorization": f"Bearer {settings.RUNWAY_API_KEY}",
    "X-Runway-Version": "2024-11-06",
    "Content-Type": "application/json",
}


async def generate_video(prompt: str, negative_prompt: str = "", duration: int = 5) -> str:
    """
    Soumet une génération text-to-video et retourne l'URL de la vidéo finale.
    duration : 5 ou 10 secondes (valeurs supportées par Runway).
    """
    dur = 10 if duration >= 8 else 5

    payload = {
        "model": "gen4_turbo",
        "promptText": prompt,
        "ratio": "768:1280",   # 9:16 portrait TikTok/Reels
        "duration": dur,
    }
    if negative_prompt:
        payload["negativePromptText"] = negative_prompt

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(f"{_BASE}/text_to_video", json=payload, headers=_HEADERS)
        resp.raise_for_status()
        task_id = resp.json()["id"]

    return await _wait_for_video(task_id)


async def _wait_for_video(task_id: str, timeout: int = 300) -> str:
    """Attend la fin de la tâche et retourne l'URL de téléchargement."""
    async with httpx.AsyncClient(timeout=15) as client:
        for _ in range(timeout // 5):
            await asyncio.sleep(5)
            resp = await client.get(f"{_BASE}/tasks/{task_id}", headers=_HEADERS)
            resp.raise_for_status()
            data = resp.json()
            status = data.get("status")

            if status == "SUCCEEDED":
                outputs = data.get("output", [])
                if outputs:
                    return outputs[0]
                raise RuntimeError("Runway a terminé sans fichier de sortie")

            if status == "FAILED":
                raise RuntimeError(f"Runway génération échouée : {data.get('failure', 'raison inconnue')}")

    raise RuntimeError(f"Timeout — tâche Runway {task_id} pas terminée en {timeout}s")


async def download_video(url: str) -> bytes:
    """Télécharge la vidéo depuis l'URL Runway."""
    async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content
