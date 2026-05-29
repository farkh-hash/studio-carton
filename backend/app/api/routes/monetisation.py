from fastapi import APIRouter, Query

router = APIRouter(prefix="/monetisation", tags=["monetisation"])


@router.get("/analyze")
async def analyze(target_subscribers: int = Query(default=50000, ge=1000, le=10000000)):
    from app.services.monetisation_service import analyze_monetisation
    return await analyze_monetisation(target_subscribers)
