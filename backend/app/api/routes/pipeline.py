import asyncio
import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from app.db.database import get_db
from app.schemas.pipeline import PipelineRequest
from app.services import pipeline_service
from app.services import background_service

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.post("/generate")
async def generate(req: PipelineRequest, db: aiosqlite.Connection = Depends(get_db)):
    cursor = await db.execute(
        "INSERT INTO pipeline_jobs (topic, style, duration, status) VALUES (?, ?, ?, 'pending')",
        (req.topic, req.style, req.duration),
    )
    await db.commit()
    job_id = cursor.lastrowid

    asyncio.create_task(pipeline_service.run_pipeline(job_id, req.topic, req.style, req.duration))

    row = await (await db.execute("SELECT * FROM pipeline_jobs WHERE id=?", (job_id,))).fetchone()
    return dict(row)


@router.get("/")
async def list_jobs(limit: int = 50, db: aiosqlite.Connection = Depends(get_db)):
    rows = await (
        await db.execute("SELECT * FROM pipeline_jobs ORDER BY created_at DESC LIMIT ?", (limit,))
    ).fetchall()
    return [dict(r) for r in rows]


@router.get("/{job_id}")
async def get_job(job_id: int, db: aiosqlite.Connection = Depends(get_db)):
    row = await (await db.execute("SELECT * FROM pipeline_jobs WHERE id=?", (job_id,))).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    return dict(row)


@router.get("/{job_id}/status")
async def get_status(job_id: int, db: aiosqlite.Connection = Depends(get_db)):
    row = await (await db.execute("SELECT id, status, video_url, error_msg FROM pipeline_jobs WHERE id=?", (job_id,))).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    return dict(row)


@router.delete("/{job_id}")
async def delete_job(job_id: int, db: aiosqlite.Connection = Depends(get_db)):
    await db.execute("DELETE FROM pipeline_jobs WHERE id=?", (job_id,))
    await db.commit()
    return {"deleted": True}


@router.get("/debug/pexels")
async def debug_pexels():
    try:
        clips = await background_service.fetch_background_clips("morning routine wake up", 30)
        return {"success": True, "clips_downloaded": len(clips), "paths": clips}
    except Exception as e:
        return {"success": False, "error": str(e)}
