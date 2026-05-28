import asyncio
import os
import aiofiles
import aiosqlite

from app.services import runway_client
from app.services.prompt_service import build_animatediff_prompt, build_negative_prompt
from app.schemas.video import VideoGenerateRequest

_DB_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "../../data/studio_carton.db")
)
_OUTPUTS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "../../../outputs/videos")
)


async def create_video(req: VideoGenerateRequest, db: aiosqlite.Connection) -> dict:
    final_prompt = build_animatediff_prompt(req.prompt, mood="fun", style_variant="classic")
    negative = req.negative_prompt or build_negative_prompt()

    cursor = await db.execute(
        """INSERT INTO videos
           (task_id, prompt, negative_prompt, style, duration, aspect_ratio, model, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, 'processing')""",
        (
            f"runway_{os.urandom(6).hex()}",
            final_prompt,
            negative,
            req.style,
            req.duration,
            req.aspect_ratio,
            "runway-gen4-turbo",
        ),
    )
    await db.commit()
    video_id = cursor.lastrowid

    asyncio.create_task(_run_generation(video_id, final_prompt, negative, req.duration))

    return await _fetch_video(video_id, db)


async def _run_generation(video_id: int, prompt: str, negative: str, duration: int):
    try:
        video_url_remote = await runway_client.generate_video(prompt, negative, duration)
        video_bytes = await runway_client.download_video(video_url_remote)

        os.makedirs(_OUTPUTS_DIR, exist_ok=True)
        local_file = f"video_{video_id}.mp4"
        filepath = os.path.join(_OUTPUTS_DIR, local_file)
        async with aiofiles.open(filepath, "wb") as f:
            await f.write(video_bytes)

        video_url = f"/videos/{local_file}"
        async with aiosqlite.connect(_DB_PATH) as db:
            await db.execute(
                "UPDATE videos SET status='completed', video_url=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (video_url, video_id),
            )
            await db.commit()

    except Exception as e:
        async with aiosqlite.connect(_DB_PATH) as db:
            await db.execute(
                "UPDATE videos SET status='failed', error_msg=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (str(e)[:500], video_id),
            )
            await db.commit()


async def list_videos(db: aiosqlite.Connection, limit: int = 50) -> list:
    rows = await (
        await db.execute("SELECT * FROM videos ORDER BY created_at DESC LIMIT ?", (limit,))
    ).fetchall()
    return [dict(r) for r in rows]


async def get_video(video_id: int, db: aiosqlite.Connection) -> dict | None:
    row = await (await db.execute("SELECT * FROM videos WHERE id=?", (video_id,))).fetchone()
    return dict(row) if row else None


async def delete_video(video_id: int, db: aiosqlite.Connection) -> bool:
    row = await (await db.execute("SELECT video_url FROM videos WHERE id=?", (video_id,))).fetchone()
    if row and row["video_url"]:
        filepath = os.path.join(_OUTPUTS_DIR, os.path.basename(row["video_url"]))
        if os.path.exists(filepath):
            os.remove(filepath)
    await db.execute("DELETE FROM videos WHERE id=?", (video_id,))
    await db.commit()
    return True


async def _fetch_video(video_id: int, db: aiosqlite.Connection) -> dict:
    row = await (await db.execute("SELECT * FROM videos WHERE id=?", (video_id,))).fetchone()
    return dict(row) if row else {}
