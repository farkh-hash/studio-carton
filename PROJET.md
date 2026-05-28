# Sunny Surprise — Studio Carton

## Liens
- **Site** : https://sunny-surprise-production-fec2.up.railway.app
- **GitHub** : https://github.com/farkh-hash/studio-carton
- **Railway Dashboard** : https://railway.com/project/95000de6-f31c-4134-a555-e984b9bf412c

---

## Stack technique
- **Backend** : FastAPI (Python 3.11) + aiosqlite
- **Frontend** : React 19 + Vite
- **Déploiement** : Railway (Dockerfile multi-stage)
- **DB** : SQLite (locale dans `backend/data/`)
- **IA** : Claude API (scripts) + ElevenLabs (TTS) + MoviePy (assemblage)

---

## Pipelines

### Pipeline A — Kling AI
Prompt texte → Kling AI → vidéo IA générée (5-10s)
- Route : `POST /api/videos/generate`
- Onglet : "Kling AI" dans le frontend

### Pipeline B — Assemblage Viral ✅ CODÉ
Sujet → Claude script → ElevenLabs voix → sous-titres → MoviePy 9:16 → MP4
- Route : `POST /api/pipeline/generate`
- Onglet : "Pipeline Viral" dans le frontend (onglet par défaut)
- Format : 1080x1920 (9:16), 30fps, fond sombre + sous-titres blancs
- Durées : 30s / 60s / 90s
- Styles : viral / éducatif / storytelling / humour

---

## Variables d'environnement

| Variable | Statut | Usage |
|---|---|---|
| `RUNWAY_API_KEY` | ✅ | Runway ML |
| `ANTHROPIC_API_KEY` | ✅ | Claude API (scripts) |
| `ELEVENLABS_API_KEY` | ✅ | Synthèse vocale |
| `CORS_ORIGINS` | ✅ | Domaine Railway + localhost |
| `DEBUG` | ✅ `false` | Mode debug |
| `KLING_ACCESS_KEY` | ❌ À remplir | Kling AI |
| `KLING_SECRET_KEY` | ❌ À remplir | Kling AI |

---

## Structure du projet
```
studio-carton/
├── backend/
│   ├── app/
│   │   ├── api/routes/
│   │   │   ├── health.py
│   │   │   ├── videos.py          # Pipeline A (Kling)
│   │   │   ├── prompts.py
│   │   │   └── pipeline.py        # Pipeline B (Viral)
│   │   ├── core/config.py
│   │   ├── db/database.py         # Tables: videos + pipeline_jobs
│   │   ├── schemas/
│   │   │   ├── video.py
│   │   │   └── pipeline.py
│   │   ├── services/
│   │   │   ├── script_service.py  # Claude → script
│   │   │   ├── tts_service.py     # ElevenLabs → audio
│   │   │   ├── subtitle_service.py# timing sous-titres
│   │   │   ├── assembler_service.py# MoviePy → vidéo 9:16
│   │   │   └── pipeline_service.py# orchestrateur async
│   │   └── main.py
│   └── requirements.txt
├── frontend/src/
│   ├── components/
│   │   ├── PipelineForm.jsx       # Formulaire Pipeline B
│   │   ├── PipelineGallery.jsx    # Galerie + polling statut
│   │   ├── GeneratorForm.jsx      # Formulaire Kling
│   │   └── VideoGallery.jsx
│   ├── api/client.js
│   └── App.jsx                    # 2 onglets : Pipeline Viral + Kling AI
├── Dockerfile                     # multi-stage + ffmpeg + fonts
├── railway.toml
└── PROJET.md
```

---

## Historique des sessions

### Session 1 — 2026-05-28
- Suppression de `book-to-youtube-studio` et `scriptstorm-agent`
- Nettoyage de `studio-carton` (.venv, node_modules, outputs, pycache)
- Initialisation git + push GitHub
- Déploiement Railway (projet : sunny-surprise)
- Obtention clés API : Anthropic + ElevenLabs
- Codage complet du Pipeline B (4 services + route + frontend)
- Fix chemins fichiers dans le container Railway (`../../` → `../`)
- Dernier déploiement : build en cours (fix chemins)

---

## Prochaines étapes

### Immédiat
- [ ] Vérifier que le site fonctionne après le dernier build
- [ ] Tester Pipeline B end-to-end (générer une vraie vidéo)

### Court terme
- [ ] Améliorer le visuel des vidéos (backgrounds, animations)
- [ ] Choisir une voix française dans ElevenLabs (remplacer Rachel)
- [ ] Améliorer les sous-titres (taille, position, couleur)

### Moyen terme
- [ ] Upload automatique YouTube Shorts
- [ ] Upload automatique TikTok
- [ ] Génération en batch (CSV d'idées → 10-20 vidéos)

### Long terme
- [ ] Nom de domaine personnalisé
- [ ] Clés Kling AI pour activer Pipeline A
