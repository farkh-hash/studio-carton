import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.db.database import init_db
from app.api.routes import health, videos, prompts

OUTPUTS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "../../outputs/videos")
)
STATIC_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "../../static")
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    await init_db()
    yield


app = FastAPI(title="Studio Carton API", version="1.0.0", lifespan=lifespan)

cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(videos.router, prefix="/api")
app.include_router(prompts.router, prefix="/api")

# Sert les vidéos générées
if os.path.isdir(OUTPUTS_DIR):
    app.mount("/videos", StaticFiles(directory=OUTPUTS_DIR), name="videos")

# Sert le frontend React en production
if os.path.isdir(STATIC_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
