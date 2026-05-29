from fastapi import APIRouter
from app.services import niche_service
import asyncio

router = APIRouter(prefix="/niches", tags=["niches"])


@router.get("/analyze")
async def analyze():
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, niche_service.analyze_niches)
    return data
