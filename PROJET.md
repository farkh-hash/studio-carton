# Sunny Surprise — Studio Carton

## Liens
- **Railway** : https://sunny-surprise-production-fec2.up.railway.app
- **GitHub** : https://github.com/farkh-hash/studio-carton
- **Railway Dashboard** : https://railway.com/project/95000de6-f31c-4134-a555-e984b9bf412c

---

## Stack technique
- **Backend** : FastAPI (Python 3.11) + aiosqlite
- **Frontend** : React 19 + Vite
- **Déploiement** : Railway (Dockerfile multi-stage)
- **DB** : SQLite (locale dans `backend/data/`)

---

## Pipelines

### Pipeline A — Kling AI (existant)
Prompt texte → Kling AI → vidéo IA générée (5-10s)
- Route : `POST /api/videos/generate`
- Modèle : `kling-v1-6`

### Pipeline B — Assemblage Viral (à construire)
Sujet → Claude script → ElevenLabs voix → Whisper sous-titres → MoviePy assemble → export TikTok
- Route : `POST /api/pipeline/generate`
- Format : 9:16 vertical, 60s max
- Plateformes cibles : TikTok, Reels, Shorts

---

## Variables d'environnement

### Configurées (Railway + .env local)
| Variable | Statut | Usage |
|---|---|---|
| `RUNWAY_API_KEY` | ✅ Configurée | Runway ML vidéo |
| `DEBUG` | ✅ `false` | Mode debug |
| `CORS_ORIGINS` | ✅ Configurée | Domaine Railway + localhost |

### À configurer (Pipeline B)
| Variable | Statut | Où obtenir |
|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ Configurée | console.anthropic.com → API Keys |
| `ELEVENLABS_API_KEY` | ✅ Configurée | elevenlabs.io → Settings → API Keys |

### Clés Kling AI
| Variable | Statut |
|---|---|
| `KLING_ACCESS_KEY` | ❌ À remplir |
| `KLING_SECRET_KEY` | ❌ À remplir |

---

## Structure du projet
```
studio-carton/
├── backend/
│   ├── app/
│   │   ├── api/routes/        # health, videos, prompts (+ pipeline à venir)
│   │   ├── core/config.py     # Variables d'environnement
│   │   ├── db/database.py     # Schema SQLite
│   │   ├── schemas/           # Modèles Pydantic
│   │   ├── services/          # kling, runway, prompt, video (+ script, tts, subtitle, assembler à venir)
│   │   └── main.py            # Point d'entrée FastAPI
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/        # GeneratorForm, VideoGallery, VideoCard, PromptBuilder
│       ├── api/client.js
│       └── App.jsx
├── Dockerfile                 # Multi-stage : build React → FastAPI
├── railway.toml
└── PROJET.md                  # Ce fichier
```

---

## Historique des décisions
- **2026-05-28** : Suppression de `book-to-youtube-studio` et `scriptstorm-agent`
- **2026-05-28** : Déploiement de `studio-carton` sur Railway (sunny-surprise)
- **2026-05-28** : Pipeline B (ElevenLabs + Whisper + MoviePy) prévu — en attente des clés API

---

## Prochaines étapes
- [ ] Obtenir `ANTHROPIC_API_KEY` → console.anthropic.com
- [ ] Obtenir `ELEVENLABS_API_KEY` → elevenlabs.io
- [ ] Ajouter les clés sur Railway (`railway variable set ...`)
- [ ] Coder Pipeline B (script + TTS + subtitles + assemblage)
- [ ] Mettre à jour le frontend avec onglet "Pipeline Viral"
- [ ] Tester end-to-end et redéployer
