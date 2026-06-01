# ── Stage 1 : build React ──────────────────────────────────────────────────────
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/ ./
RUN npm ci && npm run build

# ── Stage 2 : FastAPI + fichiers statiques ────────────────────────────────────
FROM python:3.11-slim
WORKDIR /app

# ffmpeg + polices pour MoviePy et PIL
RUN apt-get update && apt-get install -y \
    ffmpeg \
    fonts-liberation \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./

# Copie le build React dans /app/static
COPY --from=frontend-builder /app/frontend/dist ./static

EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
