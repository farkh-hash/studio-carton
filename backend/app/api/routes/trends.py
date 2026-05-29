from fastapi import APIRouter
from app.services import trends_service

router = APIRouter(prefix="/trends", tags=["trends"])


@router.get("/analyze")
async def analyze():
    return await trends_service.analyze_trends()
