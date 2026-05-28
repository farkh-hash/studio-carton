# Studio Carton

Génération de vidéos virales carton 3D pour TikTok/Reels via Kling AI.

## Architecture

- **Backend**: FastAPI + aiosqlite — `http://localhost:8000`
- **Frontend**: React (Vite) — `http://localhost:5173`
- **API vidéo**: Kling AI (`https://api.klingai.com`)

```
studio-carton/
  backend/
    app/
      core/config.py          # Settings (KLING_ACCESS_KEY, KLING_SECRET_KEY)
      db/database.py          # SQLite schema + get_db()
      api/routes/
        health.py             # GET /api/health
        videos.py             # CRUD vidéos + génération
        prompts.py            # Build/enhance prompts
      services/
        kling_client.py       # Appels API Kling AI (JWT auth)
        prompt_service.py     # Prompt builder carton 3D
        video_service.py      # Orchestration génération
    .env                      # Clés API (ne pas committer)
  frontend/
    src/
      api/client.js           # Axios calls vers le backend
      components/
        GeneratorForm.jsx     # Formulaire de génération
        PromptBuilder.jsx     # Builder prompt carton 3D
        VideoCard.jsx         # Card avec statut + actions
        VideoGallery.jsx      # Grille de vidéos
      App.jsx                 # App principale
```

## Démarrage

**Terminal 1 — Backend:**
```powershell
cd C:\Users\moadf\studio-carton\backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

**Terminal 2 — Frontend:**
```powershell
cd C:\Users\moadf\studio-carton\frontend
npm run dev
```

Swagger: `http://localhost:8000/docs`
App: `http://localhost:5173`

## Config Kling AI (`backend/.env`)

```
KLING_ACCESS_KEY=ta_cle_ici
KLING_SECRET_KEY=ton_secret_ici
```

Obtenir les clés : https://klingai.com → API Platform

## Flux de génération

1. User soumet un prompt via le formulaire
2. `POST /api/videos/generate` → backend enrichit le prompt (style carton 3D) + appelle Kling API
3. Kling retourne un `task_id`, vidéo en statut `submitted`
4. User clique "Rafraîchir" → `POST /api/videos/{id}/refresh` → polling Kling pour le statut
5. Quand `completed`, le lien vidéo est disponible pour téléchargement

## Statuts vidéo

`pending → submitted → processing → completed / failed`

## Modèles Kling disponibles

- `kling-v1` — standard
- `kling-v1-6` — recommandé (meilleur rapport qualité/vitesse)
- `kling-v2-master` — le plus récent, haute qualité
