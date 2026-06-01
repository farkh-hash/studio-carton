import asyncio
import json
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


async def run_pipeline(
    job_id: int,
    topic: str,
    style: str,
    duration: int,
    script_override: str = None,
    hook_type: str = "auto",
    visual_style: str = "cinematic",
):
    import aiosqlite
    import aiofiles
    from app.services import tts_service, subtitle_service, assembler_service

    _, outputs_dir = _get_paths()
    os.makedirs(outputs_dir, exist_ok=True)

    try:
        await _update_job(job_id, status="generating_script")

        storyboard = None

        if script_override:
            # Mode manuel : script fourni, pas de storyboard
            script = _clean_script(script_override)
        else:
            # Mode automatique : storyboard complet
            from app.services import storyboard_service
            storyboard = await storyboard_service.generate_storyboard(topic, duration, style, visual_style)
            script = _clean_script(storyboard["narration"])
            storyboard_json = json.dumps(storyboard, ensure_ascii=False)
            print(f"[PIPELINE] Storyboard: {len(storyboard['scenes'])} scènes, score {storyboard.get('scores', {}).get('total', 0)}/50")
            await _update_job(job_id, status="generating_audio", script=script, storyboard=storyboard_json)

        if storyboard is None:
            await _update_job(job_id, status="generating_audio", script=script)

        # Audio + clips scènes en parallèle
        audio_task = asyncio.create_task(tts_service.generate_audio(script))

        if storyboard:
            from app.services.background_service import fetch_clips_for_scenes
            from app.core.config import settings
            if settings.PEXELS_API_KEY:
                clips_task = asyncio.create_task(fetch_clips_for_scenes(storyboard["scenes"]))
                (audio_bytes, word_boundaries), clip_paths = await asyncio.gather(audio_task, clips_task)
            else:
                audio_bytes, word_boundaries = await audio_task
                clip_paths = [None] * len(storyboard["scenes"])
        else:
            bg_task = asyncio.create_task(_build_background(job_id, topic, duration))
            (audio_bytes, word_boundaries), bg_video_path = await asyncio.gather(audio_task, bg_task)
            clip_paths = None

        audio_path = os.path.join(outputs_dir, f"audio_{job_id}.mp3")
        async with aiofiles.open(audio_path, "wb") as f:
            await f.write(audio_bytes)

        await _update_job(job_id, status="assembling_video")

        # Sous-titres mot par mot (1 mot = 1 chunk — style viral TikTok)
        if word_boundaries:
            chunks = subtitle_service.build_subtitles_from_words(word_boundaries, words_per_chunk=1)
        else:
            audio_duration = assembler_service._get_audio_duration(audio_path)
            chunks = subtitle_service.build_subtitles(script, audio_duration, words_per_chunk=1)

        video_filename = f"video_{job_id}.mp4"
        video_path = os.path.join(outputs_dir, video_filename)
        loop = asyncio.get_running_loop()

        if storyboard and clip_paths is not None:
            await loop.run_in_executor(
                None,
                lambda: assembler_service.assemble_storyboard_video(
                    storyboard["scenes"], clip_paths, audio_path, chunks, video_path
                ),
            )
        else:
            await loop.run_in_executor(
                None,
                lambda: assembler_service.assemble_video(
                    audio_path, chunks, video_path, bg_video_path if clip_paths is None else None, topic
                ),
            )

        await _update_job(job_id, status="completed", video_url=f"/pipeline/{video_filename}")

    except Exception as e:
        await _update_job(job_id, status="failed", error_msg=str(e)[:500])
