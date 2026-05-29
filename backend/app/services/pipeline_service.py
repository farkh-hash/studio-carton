import asyncio
import os
import re
import unicodedata
import aiosqlite
import aiofiles

from app.services import script_service, tts_service, subtitle_service, assembler_service, background_service
from app.core.config import settings

_DATA_DIR = "/data" if os.path.exists("/data") else os.path.normpath(
    os.path.join(os.path.dirname(__file__), "../../data_local")
)
_DB_PATH = os.path.join(_DATA_DIR, "studio_carton.db")
_OUTPUTS_DIR = os.environ.get("PIPELINE_DIR") or os.path.join(_DATA_DIR, "outputs/pipeline")


def _clean_script(script: str) -> str:
    """Nettoie le script : encodage + mise en forme."""
    script = unicodedata.normalize("NFC", script)
    # Fix artefacts encodage courants
    replacements = [
        ("â¬", "euros"), ("â€™", "'"), ("â€œ", '"'), ("â€", '"'),
        ("Ã©", "é"), ("Ã ", "à"), ("Ã¨", "è"), ("Ã§", "ç"),
        ("Ã¢", "â"), ("Ãª", "ê"), ("Ã®", "î"), ("Ã´", "ô"),
        ("Ã»", "û"), ("Ã¹", "ù"), ("Ã«", "ë"), ("Ã¯", "ï"),
    ]
    for bad, good in replacements:
        script = script.replace(bad, good)
    # Nettoyer lignes et espaces
    script = re.sub(r'\n{3,}', '\n\n', script)
    script = re.sub(r'[ \t]+', ' ', script)
    script = '\n'.join(line.strip() for line in script.split('\n') if line.strip())
    return script


async def _update_job(job_id: int, **kwargs):
    async with aiosqlite.connect(_DB_PATH) as db:
        fields = ", ".join(f"{k}=?" for k in kwargs)
        values = list(kwargs.values()) + [job_id]
        await db.execute(
            f"UPDATE pipeline_jobs SET {fields}, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            values,
        )
        await db.commit()


async def _build_background(job_id: int, topic: str, duration: int) -> str | None:
    if not settings.PEXELS_API_KEY:
        return None
    try:
        clip_paths = await background_service.fetch_background_clips(topic, duration)
        if not clip_paths:
            return None
        bg_path = os.path.join(_OUTPUTS_DIR, f"bg_{job_id}.mp4")
        ok = background_service.build_background_video(clip_paths, duration + 5, bg_path)
        for p in clip_paths:
            try:
                os.remove(p)
            except Exception:
                pass
        return bg_path if ok else None
    except Exception as e:
        print(f"[PIPELINE] Background error: {e}")
        return None


async def run_pipeline(job_id: int, topic: str, style: str, duration: int, script_override: str = None, hook_type: str = "auto"):
    os.makedirs(_OUTPUTS_DIR, exist_ok=True)

    try:
        await _update_job(job_id, status="generating_script")

        if script_override:
            script = _clean_script(script_override)
        else:
            script = await script_service.generate_script(topic, duration, style, hook_type)
            script = _clean_script(script)

            # Validation longueur — au moins 1 mot par seconde
            word_count = len(script.split())
            min_words = max(60, duration)
            if word_count < min_words:
                print(f"[PIPELINE] Script trop court ({word_count} mots < {min_words}), regeneration...")
                script = await script_service.generate_script(topic, duration, style, hook_type)
                script = _clean_script(script)

        print(f"[PIPELINE] Script final: {len(script.split())} mots")
        await _update_job(job_id, status="generating_audio", script=script)

        # Audio TTS + Background en parallèle
        (audio_bytes, word_boundaries), bg_video_path = await asyncio.gather(
            tts_service.generate_audio(script),
            _build_background(job_id, topic, duration),
        )

        audio_path = os.path.join(_OUTPUTS_DIR, f"audio_{job_id}.mp3")
        async with aiofiles.open(audio_path, "wb") as f:
            await f.write(audio_bytes)

        await _update_job(job_id, status="assembling_video")

        # Sous-titres synchronisés si timestamps disponibles
        if word_boundaries:
            chunks = subtitle_service.build_subtitles_from_words(word_boundaries, words_per_chunk=3)
            print(f"[PIPELINE] Sous-titres sync: {len(chunks)} chunks")
        else:
            from moviepy.editor import AudioFileClip
            audio_clip = AudioFileClip(audio_path)
            audio_duration = audio_clip.duration
            audio_clip.close()
            chunks = subtitle_service.build_subtitles(script, audio_duration)
            print(f"[PIPELINE] Sous-titres fallback: {len(chunks)} chunks")

        video_filename = f"video_{job_id}.mp4"
        video_path = os.path.join(_OUTPUTS_DIR, video_filename)

        await asyncio.get_event_loop().run_in_executor(
            None,
            assembler_service.assemble_video,
            audio_path,
            chunks,
            video_path,
            bg_video_path,
        )

        video_url = f"/pipeline/{video_filename}"
        await _update_job(job_id, status="completed", video_url=video_url)

    except Exception as e:
        await _update_job(job_id, status="failed", error_msg=str(e)[:500])
