from fastapi import APIRouter, Query
from app.services import monetisation_service

router = APIRouter(prefix="/monetisation", tags=["monetisation"])


@router.get("/analyze")
async def analyze(target_subscribers: int = Query(default=50000, ge=1000, le=10000000)):
    return await monetisation_service.analyze_monetisation(target_subscribers)
