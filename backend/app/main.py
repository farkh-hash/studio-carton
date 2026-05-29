import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.db.database import init_db
from app.api.routes import health, videos, prompts, pipeline, niches, users, trends

# /data est le volume Railway persistant — fallback local pour le dev
DATA_DIR = "/data" if os.path.exists("/data") else os.path.normpath(os.path.join(os.path.dirname(__file__), "../../data_local"))

OUTPUTS_DIR = os.path.join(DATA_DIR, "outputs/videos")
PIPELINE_DIR = os.path.join(DATA_DIR, "outputs/pipeline")
STATIC_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "../static"))

os.makedirs(OUTPUTS_DIR, exist_ok=True)
os.makedirs(PIPELINE_DIR, exist_ok=True)

# Exporter les chemins pour les autres modules
os.environ["DATA_DIR"] = DATA_DIR
os.environ["PIPELINE_DIR"] = PIPELINE_DIR
os.environ["OUTPUTS_DIR"] = OUTPUTS_DIR


@asynccontextmanager
async def lifespan(app: FastAPI):
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
app.include_router(pipeline.router, prefix="/api")
app.include_router(niches.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(trends.router, prefix="/api")
# scenario et monetisation routes ajoutées après stabilisation


app.mount("/videos", StaticFiles(directory=OUTPUTS_DIR), name="videos")
app.mount("/pipeline", StaticFiles(directory=PIPELINE_DIR), name="pipeline")

if os.path.isdir(STATIC_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
