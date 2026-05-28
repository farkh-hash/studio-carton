import asyncio
import os
import aiosqlite
import aiofiles

from app.services import script_service, tts_service, subtitle_service, assembler_service

_DB_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "../../data/studio_carton.db")
)
_OUTPUTS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "../../outputs/pipeline")
)


async def _update_job(job_id: int, **kwargs):
    async with aiosqlite.connect(_DB_PATH) as db:
        fields = ", ".join(f"{k}=?" for k in kwargs)
        values = list(kwargs.values()) + [job_id]
        await db.execute(
            f"UPDATE pipeline_jobs SET {fields}, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            values,
        )
        await db.commit()


async def run_pipeline(job_id: int, topic: str, style: str, duration: int):
    os.makedirs(_OUTPUTS_DIR, exist_ok=True)

    try:
        # Étape 1 — Script
        await _update_job(job_id, status="generating_script")
        script = await script_service.generate_script(topic, duration, style)
        await _update_job(job_id, status="generating_audio", script=script)

        # Étape 2 — Audio TTS
        audio_bytes = await tts_service.generate_audio(script)
        audio_path = os.path.join(_OUTPUTS_DIR, f"audio_{job_id}.mp3")
        async with aiofiles.open(audio_path, "wb") as f:
            await f.write(audio_bytes)
        await _update_job(job_id, status="assembling_video")

        # Étape 3 — Sous-titres
        from moviepy.editor import AudioFileClip
        audio_clip = AudioFileClip(audio_path)
        audio_duration = audio_clip.duration
        audio_clip.close()

        chunks = subtitle_service.build_subtitles(script, audio_duration)

        # Étape 4 — Assemblage vidéo
        video_filename = f"video_{job_id}.mp4"
        video_path = os.path.join(_OUTPUTS_DIR, video_filename)

        await asyncio.get_event_loop().run_in_executor(
            None,
            assembler_service.assemble_video,
            audio_path,
            chunks,
            video_path,
        )

        video_url = f"/pipeline/{video_filename}"
        await _update_job(job_id, status="completed", video_url=video_url)

    except Exception as e:
        await _update_job(job_id, status="failed", error_msg=str(e)[:500])
