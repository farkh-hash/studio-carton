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


CREATE_PIPELINE_TABLE = """
CREATE TABLE IF NOT EXISTS pipeline_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL,
    style TEXT DEFAULT 'viral',
    duration INTEGER DEFAULT 60,
    status TEXT DEFAULT 'pending',
    script TEXT,
    video_url TEXT,
    error_msg TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    credits INTEGER DEFAULT 3,
    is_pro INTEGER DEFAULT 0,
    stripe_customer_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_VIDEOS_TABLE)
        await db.execute(CREATE_PIPELINE_TABLE)
        await db.execute(CREATE_USERS_TABLE)
        await db.commit()


async def get_db():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db
