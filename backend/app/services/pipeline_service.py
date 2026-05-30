import asyncio
import os
import re
import unicodedata


def _clean_script(script: str) -> str:
    script = unicodedata.normalize("NFC", script)
    replacements = [
        ("â¬", "euros"), ("â€™", "'"), ("â€œ", '"'), ("â€", '"'),
        ("Ã©", "é"), ("Ã ", "à"), ("Ã¨", "è"), ("Ã§", "ç"),
        ("Ã¢", "â"), ("Ãª", "ê"), ("Ã®", "î"), ("Ã´", "ô"),
        ("Ã»", "û"), ("Ã¹", "ù"),
    ]
    for bad, good in replacements:
        script = script.replace(bad, good)
    script = re.sub(r'\n{3,}', '\n\n', script)
    script = re.sub(r'[ \t]+', ' ', script)
    script = '\n'.join(line.strip() for line in script.split('\n') if line.strip())
    return script


def _get_paths():
    data_dir = "/data" if os.path.exists("/data") else os.path.normpath(
        os.path.join(os.path.dirname(__file__), "../../data_local")
    )
    return (
        os.path.join(data_dir, "studio_carton.db"),
        os.environ.get("PIPELINE_DIR") or os.path.join(data_dir, "outputs/pipeline"),
    )


async def _update_job(job_id: int, **kwargs):
    import aiosqlite
    db_path, _ = _get_paths()
    async with aiosqlite.connect(db_path) as db:
        fields = ", ".join(f"{k}=?" for k in kwargs)
        values = list(kwargs.values()) + [job_id]
        await db.execute(
            f"UPDATE pipeline_jobs SET {fields}, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            values,
        )
        await db.commit()


async def _build_background(job_id: int, topic: str, duration: int) -> str | None:
    from app.services.background_service import fetch_background_clips, build_background_video
    from app.core.config import settings
    _, outputs_dir = _get_paths()

    if not settings.PEXELS_API_KEY:
        return None
    try:
        clip_paths = await fetch_background_clips(topic, duration)
        if not clip_paths:
            return None
        bg_path = os.path.join(outputs_dir, f"bg_{job_id}.mp4")
        ok = build_background_video(clip_paths, duration + 5, bg_path)
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
    import aiosqlite
    import aiofiles
    from app.services import script_service, tts_service, subtitle_service, assembler_service

    _, outputs_dir = _get_paths()
    os.makedirs(outputs_dir, exist_ok=True)

    try:
        await _update_job(job_id, status="generating_script")

        if script_override:
            script = _clean_script(script_override)
        else:
            script = await script_service.generate_script(topic, duration, style, hook_type)
            script = _clean_script(script)

            word_count = len(script.split())
            min_words = max(80, int(duration * 1.8))
            if word_count < min_words:
                print(f"[PIPELINE] Script trop court ({word_count} mots < {min_words}), regeneration...")
                script = await script_service.generate_script(topic, duration, style, hook_type)
                script = _clean_script(script)

        # Agent 4 — Validation
        if not script_override:
            try:
                from app.services.script_validator_service import validate_script
                loop = asyncio.get_event_loop()
                validation = await loop.run_in_executor(None, validate_script, script, topic, duration)
                score = validation.get("scores", {}).get("overall", 5)
                print(f"[PIPELINE] Validation: {score}/10 | {len(script.split())} mots")
                if validation.get("regenerate") or score < 6:
                    print(f"[PIPELINE] Score insuffisant, régénération...")
                    script = await script_service.generate_script(topic, duration, style, hook_type)
                    script = _clean_script(script)
            except Exception as e:
                print(f"[PIPELINE] Validation error: {e}")

        print(f"[PIPELINE] Script final: {len(script.split())} mots")
        await _update_job(job_id, status="generating_audio", script=script)

        (audio_bytes, word_boundaries), bg_video_path = await asyncio.gather(
            tts_service.generate_audio(script),
            _build_background(job_id, topic, duration),
        )

        audio_path = os.path.join(outputs_dir, f"audio_{job_id}.mp3")
        async with aiofiles.open(audio_path, "wb") as f:
            await f.write(audio_bytes)

        await _update_job(job_id, status="assembling_video")

        if word_boundaries:
            chunks = subtitle_service.build_subtitles_from_words(word_boundaries, words_per_chunk=3)
        else:
            audio_duration = assembler_service._get_audio_duration(audio_path)
            chunks = subtitle_service.build_subtitles(script, audio_duration)

        video_filename = f"video_{job_id}.mp4"
        video_path = os.path.join(outputs_dir, video_filename)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            assembler_service.assemble_video,
            audio_path,
            chunks,
            video_path,
            bg_video_path,
        )

        await _update_job(job_id, status="completed", video_url=f"/pipeline/{video_filename}")

    except Exception as e:
        await _update_job(job_id, status="failed", error_msg=str(e)[:500])
