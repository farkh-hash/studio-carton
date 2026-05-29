import asyncio
import os
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from app.db.database import get_db
import aiosqlite

router = APIRouter(prefix="/scenario", tags=["scenario"])


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
    from app.services.scenario_script_service import generate_scenario as gen, scenario_to_plain_script
    loop = asyncio.get_event_loop()
    scenario = await loop.run_in_executor(None, gen, req.topic, req.duration, req.scenario_type)
    return {"scenario": scenario, "script_preview": scenario_to_plain_script(scenario)}


async def _run_scenario_pipeline(job_id: int, topic: str, duration: int, scenario_type: str):
    from app.services.scenario_script_service import generate_scenario as gen, scenario_to_plain_script
    from app.services.scenario_tts_service import generate_scenario_audio
    from app.services.scenario_assembler_service import assemble_scenario
    from app.services.background_service import fetch_background_clips, build_background_video
    from app.core.config import settings
    from app.db.database import DB_PATH

    data_dir = "/data" if os.path.exists("/data") else os.path.normpath(
        os.path.join(os.path.dirname(__file__), "../../../../data_local")
    )
    outputs_dir = os.path.join(data_dir, "outputs/pipeline")
    os.makedirs(outputs_dir, exist_ok=True)

    async def _update(**kwargs):
        async with aiosqlite.connect(DB_PATH) as db:
            fields = ", ".join(f"{k}=?" for k in kwargs)
            values = list(kwargs.values()) + [job_id]
            await db.execute(f"UPDATE pipeline_jobs SET {fields}, updated_at=CURRENT_TIMESTAMP WHERE id=?", values)
            await db.commit()

    try:
        await _update(status="generating_script")
        loop = asyncio.get_event_loop()
        scenario = await loop.run_in_executor(None, gen, topic, duration, scenario_type)
        plain_script = scenario_to_plain_script(scenario)
        await _update(status="generating_audio", script=plain_script)

        async def get_character_clips():
            """Télécharge des clips pour chaque personnage."""
            if not settings.PEXELS_API_KEY:
                return {}
            from app.services.background_service import fetch_character_clips as fetch_char
            from app.services.scenario_script_service import CHARACTERS
            clips = {}
            # Extraire des mots-clés du topic pour contextualiser les clips
            topic_kw = topic.split()[:3]
            topic_str = " ".join(topic_kw)
            for char in CHARACTERS:
                try:
                    clip_path = await asyncio.wait_for(
                        fetch_char(char, topic_str),
                        timeout=30
                    )
                    if clip_path:
                        clips[char] = clip_path
                        print(f"[SCENARIO] Clip {char}: OK")
                except Exception as e:
                    print(f"[SCENARIO] Clip {char} error: {e}")
            return clips

        audio_segments, character_clips = await asyncio.gather(
            generate_scenario_audio(scenario),
            get_character_clips(),
        )
        bg_video_path = None

        await _update(status="assembling_video")
        video_filename = f"video_{job_id}.mp4"
        video_path = os.path.join(outputs_dir, video_filename)

        await loop.run_in_executor(None, assemble_scenario, audio_segments, video_path, bg_video_path, None, character_clips)
        await _update(status="completed", video_url=f"/pipeline/{video_filename}")

    except Exception as e:
        await _update(status="failed", error_msg=str(e)[:500])
