import aiosqlite
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "../../data/studio_carton.db")
DB_PATH = os.path.normpath(DB_PATH)

CREATE_VIDEOS_TABLE = """
CREATE TABLE IF NOT EXISTS videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT UNIQUE NOT NULL,
    prompt TEXT NOT NULL,
    negative_prompt TEXT DEFAULT '',
    style TEXT DEFAULT 'cardboard_3d',
    duration INTEGER DEFAULT 5,
    aspect_ratio TEXT DEFAULT '9:16',
    model TEXT DEFAULT 'kling-v1-6',
    status TEXT DEFAULT 'pending',
    video_url TEXT,
    cover_url TEXT,
    error_msg TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_VIDEOS_TABLE)
        await db.commit()


async def get_db():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db
