from fastapi import APIRouter
import os

router = APIRouter()


@router.get("/health")
async def health():
    data_dir = "/data" if os.path.exists("/data") else "local"
    return {
        "status": "ok",
        "service": "studio-carton",
        "storage": data_dir,
    }


@router.get("/health/tts")
async def test_tts():
    from app.services.tts_service import generate_audio
    try:
        audio = await generate_audio("Bonjour, ceci est un test de voix pour Studio Carton.")
        return {"status": "ok", "bytes": len(audio), "message": "Voix générée avec succès"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
