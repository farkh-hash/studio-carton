import asyncio
import os
import aiosqlite
import aiofiles
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from app.db.database import get_db
from app.core.config import settings

router = APIRouter(prefix="/scenario", tags=["scenario"])

_DATA_DIR = "/data" if os.path.exists("/data") else os.path.normpath(
    os.path.join(os.path.dirname(__file__), "../../../data_local")
)
_OUTPUTS_DIR = os.path.join(_DATA_DIR, "outputs/pipeline")


class ScenarioRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=300)
    duration: int = Field(default=60, ge=15, le=180)
    scenario_type: str = Field(default="revelation")


@router.post("/generate")
async def generate_scenario(req: ScenarioRequest, db: aiosqlite.Connection = Depends(get_db)):
    cursor = await db.execute(
        "INSERT INTO pipeline_jobs (topic, style, duration, status) VALUES (?, ?, ?, 'pending')",
        (req.topic, "scenario", req.duration),
    )
    await db.commit()
    job_id = cursor.lastrowid

    asyncio.create_task(_run_scenario_pipeline(job_id, req.topic, req.duration, req.scenario_type))

    row = await (await db.execute("SELECT * FROM pipeline_jobs WHERE id=?", (job_id,))).fetchone()
    return dict(row)


@router.post("/preview")
async def preview_scenario(req: ScenarioRequest):
    from app.services import scenario_script_service
    loop = asyncio.get_event_loop()
    scenario = await loop.run_in_executor(
        None, scenario_script_service.generate_scenario,
        req.topic, req.duration, req.scenario_type
    )
    plain = scenario_script_service.scenario_to_plain_script(scenario)
    return {"scenario": scenario, "script_preview": plain}


async def _run_scenario_pipeline(job_id: int, topic: str, duration: int, scenario_type: str):
    from app.services import scenario_script_service, scenario_tts_service, scenario_assembler_service, background_service
    from app.db.database import DB_PATH

    async def _update(job_id, **kwargs):
        async with aiosqlite.connect(DB_PATH) as db:
            fields = ", ".join(f"{k}=?" for k in kwargs)
            values = list(kwargs.values()) + [job_id]
            await db.execute(f"UPDATE pipeline_jobs SET {fields}, updated_at=CURRENT_TIMESTAMP WHERE id=?", values)
            await db.commit()

    os.makedirs(_OUTPUTS_DIR, exist_ok=True)

    try:
        # Étape 1 — Génération du scénario
        await _update(job_id, status="generating_script")
        loop = asyncio.get_event_loop()
        scenario = await loop.run_in_executor(
            None, scenario_script_service.generate_scenario,
            topic, duration, scenario_type
        )
        plain_script = scenario_script_service.scenario_to_plain_script(scenario)
        await _update(job_id, status="generating_audio", script=plain_script)

        # Étape 2 — Audio multi-voix + Background en parallèle
        async def get_bg():
            if not settings.PEXELS_API_KEY:
                return None
            try:
                clips = await background_service.fetch_background_clips(topic, duration)
                if not clips:
                    return None
                bg_path = os.path.join(_OUTPUTS_DIR, f"bg_{job_id}.mp4")
                ok = background_service.build_background_video(clips, duration + 5, bg_path)
                for p in clips:
                    try:
                        os.remove(p)
                    except Exception:
                        pass
                return bg_path if ok else None
            except Exception as e:
                print(f"[SCENARIO] Background error: {e}")
                return None

        audio_segments, bg_video_path = await asyncio.gather(
            scenario_tts_service.generate_scenario_audio(scenario),
            get_bg(),
        )

        await _update(job_id, status="assembling_video")

        # Étape 3 — Assemblage
        video_filename = f"video_{job_id}.mp4"
        video_path = os.path.join(_OUTPUTS_DIR, video_filename)

        await loop.run_in_executor(
            None,
            scenario_assembler_service.assemble_scenario,
            audio_segments,
            video_path,
            bg_video_path,
            None,
        )

        await _update(job_id, status="completed", video_url=f"/pipeline/{video_filename}")

    except Exception as e:
        await _update(job_id, status="failed", error_msg=str(e)[:500])
