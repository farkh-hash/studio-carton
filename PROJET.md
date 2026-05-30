# Sunny Surprise — Studio Carton

## Liens
- **Site** : https://sunny-surprise-production-fec2.up.railway.app
- **GitHub** : https://github.com/farkh-hash/studio-carton
- **Railway Dashboard** : https://railway.com/project/95000de6-f31c-4134-a555-e984b9bf412c

---

## Objectif du projet
Créer des chaînes TikTok/YouTube/Instagram automatisées avec du contenu viral en français.
Générer des vidéos de qualité à grande échelle pour construire une audience et monétiser.
**Pas un SaaS** — usage personnel pour construire sa propre audience.

---

## Stack technique
- **Backend** : FastAPI (Python 3.11) + aiosqlite
- **Frontend** : React 19 + Vite
- **Déploiement** : Railway (Dockerfile multi-stage)
- **DB** : SQLite sur Volume Railway persistant `/data`
- **IA Script** : Groq (Llama 3.3 70B + fallback Llama 3.1 8B)
- **TTS** : edge-tts (Microsoft Denise Neural FR) + fallback gTTS
- **Vidéo fond** : Pexels API (clips HD)
- **Assemblage** : ffmpeg (100% natif, pas de MoviePy pour le scénario)

---

## Variables d'environnement Railway

| Variable | Statut | Usage |
|---|---|---|
| `GROQ_API_KEY` | ✅ | Scripts IA (llama-3.3-70b + fallback llama-3.1-8b) |
| `PEXELS_API_KEY` | ✅ | Fond vidéo HD |
| `YOUTUBE_API_KEY` | ✅ | YouTube Trending FR/BE/CA + recherche virale |
| `ANTHROPIC_API_KEY` | ❌ (inutilisé) | Remplacé par Groq |
| `ELEVENLABS_API_KEY` | ❌ (inutilisé) | Remplacé par edge-tts |
| `STRIPE_SECRET_KEY` | ⚠️ Non configuré | Pour monétisation future |

---

## Fonctionnalités implémentées

### Agents IA
| Agent | Route | Statut |
|---|---|---|
| 💰 Agent Monétisation | `/api/monetisation/analyze` | ✅ Opérationnel |
| 📡 Agent Tendances | `/api/trends/analyze` | ✅ Multi-plateformes |
| 🤖 Agent Niches | `/api/niches/analyze` | ✅ Opérationnel |
| 🔍 Recherche virale | Intégré dans script_service | ✅ YouTube API |

### Pipeline Vidéo
| Feature | Statut |
|---|---|
| ✍️ Génération script (hooks viraux + recherche) | ✅ |
| 🎙️ TTS edge-tts (Microsoft Denise Neural FR) | ✅ |
| 🎬 Fond vidéo Pexels HD (ffmpeg) | ✅ |
| 📝 Sous-titres synchronisés (edge-tts WordBoundary) | ✅ |
| 📋 Captions prêt-à-poster (TikTok/YouTube/Instagram) | ✅ |
| ⏱️ Durées 30s → 3min | ✅ |
| 🔄 Fallback Groq automatique (rate limit) | ✅ |

### Pipeline Scénario (NOUVEAU)
| Feature | Statut |
|---|---|
| 🎭 Dialogue ALEX (homme) + SARAH (femme) | ✅ |
| 🎤 2 voix distinctes (Henri + Denise Neural) | ✅ |
| 🏷️ Badge personnage (ALEX bleu, SARAH rose) | ✅ |
| 📺 Fond Pexels + sous-titres ffmpeg drawtext | ✅ |
| ⚡ Assemblage 100% ffmpeg (~2 min pour 60s) | ✅ |
| 🎬 5 types : révélation, transformation, débat, mentor, drama | ✅ |

### Infrastructure
| Feature | Statut |
|---|---|
| 🗄️ Volume Railway /data (DB + vidéos persistants) | ✅ |
| 👤 Auth email + crédits utilisateurs | ✅ |
| 🚀 Imports lazy (résolution crash démarrage) | ✅ |

---

## Données de recherche virales intégrées

### Règles d'or
- **80% du succès = les 3 premières secondes** (hook)
- **Objectif rétention** : 70%+ à 3s, 60% à 15s, 50% à 30s
- **Durée optimale** : 60s standard, >60s pour TikTok Creator Rewards
- **Fréquence** : 3-5x/semaine TikTok, 1-3x/semaine YouTube Shorts

### Niches les plus rentables (Agent Monétisation)
| Rang | Niche | Revenu estimé à 50K abonnés |
|---|---|---|
| 🥇 | Immobilier/Investissement | 6 500 - 14 400€/mois |
| 🥈 | IA & Outils Digitaux | 4 400 - 10 000€/mois |
| 🥉 | Finance Personnelle | 3 500 - 8 200€/mois |

### Agent Tendances — Sources actives
- YouTube Trending : France + Belgique + Canada (API officielle)
- Google Trends : France + Canada + Belgique (RSS)
- TikTok : via DuckDuckGo
- Reddit : flux publics (r/france, r/financepersonnelle)

---

## Structure du projet
```
studio-carton/
├── backend/
│   ├── app/
│   │   ├── api/routes/
│   │   │   ├── health.py
│   │   │   ├── videos.py
│   │   │   ├── pipeline.py       # génération + preview-script + captions
│   │   │   ├── niches.py         # agent niches + génération script
│   │   │   ├── scenario.py       # pipeline scénario multi-voix
│   │   │   ├── trends.py         # agent tendances multi-plateformes
│   │   │   ├── monetisation.py   # agent monétisation + RPM
│   │   │   └── users.py          # auth email + crédits
│   │   ├── core/config.py        # clés API + modèles Groq
│   │   ├── db/database.py        # SQLite sur /data
│   │   ├── services/
│   │   │   ├── groq_client.py           # client Groq avec fallback
│   │   │   ├── script_service.py        # génération script + 5 agents
│   │   │   ├── tts_service.py           # edge-tts + gTTS fallback
│   │   │   ├── subtitle_service.py      # sync timestamps
│   │   │   ├── assembler_service.py     # assemblage vidéo MoviePy
│   │   │   ├── scenario_script_service.py   # scénario dialogue
│   │   │   ├── scenario_tts_service.py      # TTS multi-voix
│   │   │   ├── scenario_assembler_service.py # assemblage 100% ffmpeg
│   │   │   ├── background_service.py    # Pexels clips HD
│   │   │   ├── trends_service.py        # tendances multi-réseaux
│   │   │   ├── monetisation_service.py  # analyse monétisation
│   │   │   ├── niche_service.py         # agent niches
│   │   │   ├── video_research_service.py # recherche YouTube API
│   │   │   ├── caption_service.py       # captions TikTok/YouTube/IG
│   │   │   ├── script_analyzer_service.py   # analyse profonde scripts
│   │   │   ├── hook_tester_service.py       # multi-hook tester
│   │   │   ├── persona_service.py           # profil audience
│   │   │   ├── competitor_service.py        # analyse concurrents
│   │   │   └── script_validator_service.py  # validation script
│   │   └── main.py
│   └── requirements.txt
├── frontend/src/
│   ├── components/
│   │   ├── MonetisationAgent.jsx  # agent monétisation
│   │   ├── TrendsAgent.jsx        # agent tendances
│   │   ├── NicheAgent.jsx         # agent niches
│   │   ├── ScenarioForm.jsx       # pipeline scénario
│   │   ├── PipelineForm.jsx       # pipeline viral
│   │   ├── PipelineGallery.jsx    # galerie + prêt à poster
│   │   ├── LandingPage.jsx        # landing page auth
│   │   └── VideoGallery.jsx
│   └── App.jsx                    # 6 onglets
├── Dockerfile
├── railway.toml
└── PROJET.md
```

---

## Prochaines étapes

### Immédiat
- [x] Refonte pipeline vidéo (MoviePy → 100% ffmpeg, CRF 18, 192kbps, loudnorm -14 LUFS)
- [x] Hooks niche sans faux témoignages (contenu honnête et vérifiable)
- [ ] Tester la qualité des vidéos générées après refonte
- [ ] Tester Agent Tendances + Monétisation ensemble → générer contenu ciblé

### Court terme
- [ ] Auto-post YouTube Shorts (OAuth2 YouTube)
- [ ] Auto-post TikTok
- [ ] Scheduler : planifier X vidéos/semaine

### Moyen terme
- [ ] Génération batch (5-10 vidéos d'un coup)
- [ ] Analytics dashboard (suivre performances)
- [ ] Nom de domaine personnalisé

---

## Historique des sessions

### Session 4 — 2026-05-30

**Refonte qualité pipeline vidéo + scripts :**
- assembler_service.py : réécriture complète MoviePy → 100% ffmpeg (CRF 18, 192kbps AAC, loudnorm -14 LUFS, drawtext 90px jaune #FFE600, fond noir semi-transparent, 5 mots/chunk)
- scenario_assembler_service.py : CRF 28→20 fond, 128k→192k audio, luminosité 65%→80%, loudnorm+faststart
- background_service.py : CRF 26/28→20, fade 0.8s→0.5s
- pipeline_service.py : suppression MoviePy (ffprobe), sous-titres 3→5 mots/chunk
- requirements.txt : moviepy/Pillow/numpy supprimés (build plus léger)
- niche_service.py : hooks factuels uniquement, sans faux témoignages
- script_service.py : SYSTEM_PROMPT reécrit (rythme haché, phrases 5-9 mots), prompt oral, température 0.82→0.78, fix SyntaxError f-string Python 3.11, Groq dans run_in_executor
- tts_service.py : vitesse +5%→-3% (voix plus naturelle)

### Session 3 — 2026-05-30
- Agent Monétisation : niche #1 = Immobilier (6500-14400€/mois), #2 = IA (4400-10000€/mois)
- Agent Tendances multi-réseaux : YouTube FR/BE/CA + Google Trends + TikTok + Instagram + Reddit
- Pipeline Scénario complet : dialogue ALEX/SARAH, 2 voix, assemblage 100% ffmpeg
- YouTube Data API v3 configurée et opérationnelle
- Résolution crash démarrage (imports lazy dans pipeline_service)
- Fallback Groq : llama-70b → llama-8b si rate limit
- Première vidéo scénario fonctionnelle : fond Pexels + textes colorés par personnage

### Session 2 — 2026-05-29
- Pipeline complet fonctionnel (Groq + edge-tts + Pexels + sous-titres sync)
- Agent Niches avec hooks + scripts + hashtags
- Preview script avant génération vidéo
- Captions prêt à poster (TikTok/YouTube/Instagram)
- Persistence volume Railway /data
- Voix edge-tts Microsoft Denise Neural

### Session 1 — 2026-05-28
- Initialisation, déploiement Railway, premiers essais pipeline
