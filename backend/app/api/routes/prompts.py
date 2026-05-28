from fastapi import APIRouter
from app.schemas.video import PromptEnhanceRequest
from app.services.prompt_service import build_viral_prompt, build_negative_prompt, MOOD_MODIFIERS, STYLE_VARIANTS

router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.post("/enhance")
async def enhance_prompt(req: PromptEnhanceRequest):
    prompt = build_viral_prompt(req.topic, req.mood, req.style_variant)
    negative = build_negative_prompt()
    return {"prompt": prompt, "negative_prompt": negative}


@router.get("/options")
async def get_options():
    return {
        "moods": list(MOOD_MODIFIERS.keys()),
        "style_variants": list(STYLE_VARIANTS.keys()),
        "models": ["kling-v1", "kling-v1-6", "kling-v2-master"],
        "durations": [5, 10],
        "aspect_ratios": ["9:16", "16:9", "1:1"],
    }
