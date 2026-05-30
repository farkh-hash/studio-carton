import asyncio
import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from app.db.database import get_db
from app.schemas.pipeline import PipelineRequest
from app.services import pipeline_service
from app.services import background_service
from typing import Optional
from pydantic import BaseModel

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


class ScriptPreviewRequest(BaseModel):
    topic: str
    duration: int = 60
    style: str = "viral"
    hook_type: str = "auto"


@router.post("/preview-script")
async def preview_script(req: ScriptPreviewRequest):
    from app.services import script_service
    try:
        script = await script_service.generate_script(req.topic, req.duration, req.style, req.hook_type)
        return {"script": script, "topic": req.topic, "duration": req.duration, "style": req.style}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate")
async def generate(req: PipelineRequest, email: Optional[str] = None, db: aiosqlite.Connection = Depends(get_db)):
    # Vérification des crédits si email fourni
    if email:
        user = await (await db.execute("SELECT * FROM users WHERE email=?", (email.lower(),))).fetchone()
        if user:
            user = dict(user)
            if not user["is_pro"] and user["credits"] <= 0:
                raise HTTPException(status_code=402, detail="Plus de crédits. Passez Pro pour continuer.")
            if not user["is_pro"]:
                await db.execute("UPDATE users SET credits=credits-1 WHERE email=?", (email.lower(),))
                await db.commit()

    cursor = await db.execute(
        "INSERT INTO pipeline_jobs (topic, style, duration, status) VALUES (?, ?, ?, 'pending')",
        (req.topic, req.style, req.duration),
    )
    await db.commit()
    job_id = cursor.lastrowid

    asyncio.create_task(pipeline_service.run_pipeline(job_id, req.topic, req.style, req.duration, req.script_override, req.hook_type))

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


@router.get("/{job_id}/captions")
async def get_captions(job_id: int, db: aiosqlite.Connection = Depends(get_db)):
    row = await (await db.execute("SELECT topic, script FROM pipeline_jobs WHERE id=?", (job_id,))).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    from app.services import caption_service
    import asyncio
    loop = asyncio.get_running_loop()
    captions = await loop.run_in_executor(
        None, caption_service.generate_captions, row["topic"], row["script"] or "", ""
    )
    return captions


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
