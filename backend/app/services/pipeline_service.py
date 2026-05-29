import asyncio
import os
import aiosqlite
import aiofiles

from app.services import script_service, tts_service, subtitle_service, assembler_service, background_service
from app.core.config import settings

# Utilise les chemins définis par main.py via env, sinon fallback
_DATA_DIR = "/data" if os.path.exists("/data") else os.path.normpath(
    os.path.join(os.path.dirname(__file__), "../../data_local")
)
_DB_PATH = os.path.join(_DATA_DIR, "studio_carton.db")
_OUTPUTS_DIR = os.environ.get("PIPELINE_DIR") or os.path.join(_DATA_DIR, "outputs/pipeline")


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
            script = script_override
        else:
            script = await script_service.generate_script(topic, duration, style, hook_type)

        # Nettoyage encodage — supprime les artefacts UTF-8 mal décodés
        import unicodedata
        script = unicodedata.normalize("NFC", script)
        # Remplace les caractères spéciaux problématiques pour TTS
        script = script.replace("", "€").replace("â¬", "€")
        script = script.replace("Ã©", "é").replace("Ã ", "à").replace("Ã¨", "è")
        script = script.replace("Ã§", "ç").replace("Ã¢", "â").replace("Ãª", "ê")
        script = script.replace("Ã®", "î").replace("Ã´", "ô").replace("Ã»", "û")
        script = script.replace("Ã¹", "ù").replace("Ã«", "ë").replace("Ã¯", "ï")
        # Supprimer les espaces multiples et lignes vides
        import re
        script = re.sub(r'\n\s*\n', '\n', script)
        script = re.sub(r'[ \t]+', ' ', script)
        script = '\n'.join(line.strip() for line in script.split('\n') if line.strip())

        await _update_job(job_id, status="generating_audio", script=script)

        (audio_bytes, word_boundaries), bg_video_path = await asyncio.gather(
            tts_service.generate_audio(script),
            _build_background(job_id, topic, duration),
        )

        audio_path = os.path.join(_OUTPUTS_DIR, f"audio_{job_id}.mp3")
        async with aiofiles.open(audio_path, "wb") as f:
            await f.write(audio_bytes)

        await _update_job(job_id, status="assembling_video")

        # Sous-titres synchronisés si timestamps disponibles (edge-tts), sinon fallback
        if word_boundaries:
            chunks = subtitle_service.build_subtitles_from_words(word_boundaries, words_per_chunk=3)
            print(f"[PIPELINE] Sous-titres synchronisés: {len(chunks)} chunks depuis {len(word_boundaries)} mots")
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
