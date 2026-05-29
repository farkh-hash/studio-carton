from fastapi import APIRouter
from pydantic import BaseModel
from app.services import niche_service
import asyncio

router = APIRouter(prefix="/niches", tags=["niches"])


class ScriptFromTopicRequest(BaseModel):
    topic: str
    hook: str
    niche: str
    format: str = "60s"
    style: str = "viral"


@router.get("/analyze")
async def analyze():
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, niche_service.analyze_niches)
    return data


@router.post("/script")
async def generate_script(req: ScriptFromTopicRequest):
    loop = asyncio.get_event_loop()
    script = await loop.run_in_executor(
        None,
        niche_service.generate_script_from_topic,
        req.topic, req.hook, req.niche, req.format, req.style
    )
    return {
        "script": script,
        "topic": req.topic,
        "hook": req.hook,
        "niche": req.niche,
        "format": req.format,
    }
