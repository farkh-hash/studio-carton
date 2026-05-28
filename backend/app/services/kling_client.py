import time
import httpx
from jose import jwt

from app.core.config import settings


def _make_jwt_token() -> str:
    now = int(time.time())
    payload = {
        "iss": settings.KLING_ACCESS_KEY,
        "exp": now + 1800,
        "nbf": now - 5,
    }
    return jwt.encode(payload, settings.KLING_SECRET_KEY, algorithm="HS256")


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {_make_jwt_token()}",
        "Content-Type": "application/json",
    }


async def create_text2video(
    prompt: str,
    negative_prompt: str = "",
    model: str = "kling-v1-6",
    duration: int = 5,
    aspect_ratio: str = "9:16",
    cfg_scale: float = 0.5,
) -> dict:
    payload = {
        "model_name": model,
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "cfg_scale": cfg_scale,
        "mode": "std",
        "duration": str(duration),
        "aspect_ratio": aspect_ratio,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{settings.KLING_API_BASE}/v1/videos/text2video",
            json=payload,
            headers=_headers(),
        )
        resp.raise_for_status()
        return resp.json()


async def get_task_status(task_id: str) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{settings.KLING_API_BASE}/v1/videos/text2video/{task_id}",
            headers=_headers(),
        )
        resp.raise_for_status()
        return resp.json()
