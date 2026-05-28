from fastapi import APIRouter, Depends, HTTPException
import aiosqlite

from app.db.database import get_db
from app.schemas.video import VideoGenerateRequest
from app.services import video_service

router = APIRouter(prefix="/videos", tags=["videos"])


@router.post("/generate")
async def generate_video(req: VideoGenerateRequest, db: aiosqlite.Connection = Depends(get_db)):
    try:
        result = await video_service.create_video(req, db)
        return result
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/")
async def list_videos(limit: int = 50, db: aiosqlite.Connection = Depends(get_db)):
    return await video_service.list_videos(db, limit)


@router.get("/{video_id}")
async def get_video(video_id: int, db: aiosqlite.Connection = Depends(get_db)):
    video = await video_service.get_video(video_id, db)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


@router.get("/{video_id}/status")
async def get_status(video_id: int, db: aiosqlite.Connection = Depends(get_db)):
    video = await video_service.get_video(video_id, db)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return {"id": video_id, "status": video["status"], "video_url": video.get("video_url"), "error_msg": video.get("error_msg")}


@router.delete("/{video_id}")
async def delete_video(video_id: int, db: aiosqlite.Connection = Depends(get_db)):
    await video_service.delete_video(video_id, db)
    return {"deleted": True}
