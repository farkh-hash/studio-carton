# Sunny Surprise — Studio Carton

## Liens
- **Site** : https://sunny-surprise-production-fec2.up.railway.app
- **GitHub** : https://github.com/farkh-hash/studio-carton
- **Railway Dashboard** : https://railway.com/project/95000de6-f31c-4134-a555-e984b9bf412c

---

## Objectif du projet
Créer des chaînes TikTok/YouTube/Instagram automatisées avec du contenu viral en français.
Générer des vidéos de qualité à grande échelle pour construire une audience et monétiser.

---

## Stack technique
- **Backend** : FastAPI (Python 3.11) + aiosqlite
- **Frontend** : React 19 + Vite
- **Déploiement** : Railway (Dockerfile multi-stage)
- **DB** : SQLite sur Volume Railway persistant `/data`
- **IA Script** : Groq (Llama 3.3 70B)
- **TTS** : edge-tts (Microsoft Denise Neural FR) + fallback gTTS
- **Vidéo fond** : Pexels API (clips HD)
- **Assemblage** : ffmpeg + MoviePy

---

## Variables d'environnement Railway

| Variable | Statut | Usage |
|---|---|---|
| `GROQ_API_KEY` | ✅ | Scripts IA |
| `PEXELS_API_KEY` | ✅ | Fond vidéo |
| `ANTHROPIC_API_KEY` | ❌ (inutilisé) | Remplacé par Groq |
| `ELEVENLABS_API_KEY` | ❌ (inutilisé) | Remplacé par edge-tts |
| `STRIPE_SECRET_KEY` | ⚠️ Non configuré | Paiements (optionnel) |

---

## Fonctionnalités implémentées

### Pipeline Vidéo ✅
1. **Agent Niches** → analyse 10 niches, génère hooks + scripts + hashtags par plateforme
2. **Génération script** → Groq Llama 3.3 avec formules hooks viraux prouvées
3. **Preview script** → voir/modifier avant de lancer la vidéo
4. **TTS edge-tts** → voix Microsoft Denise Neural française naturelle
5. **Sous-titres synchronisés** → timestamps mot par mot via edge-tts WordBoundary
6. **Fond vidéo Pexels** → clips HD liés au sujet via ffmpeg
7. **Assemblage MoviePy** → 9:16 1080x1920, sous-titres jaunes, overlay 30%
8. **Prêt à poster** → captions TikTok/YouTube/Instagram + hashtags + meilleur horaire

### Infrastructure ✅
- Volume Railway persistant `/data` (DB + vidéos survivent aux redémarrages)
- Auth email + crédits utilisateurs
- Stripe Checkout (prêt, clés manquantes)

---

## Données de recherche virales (2025-2026)

### Règles d'or pour aller viral
- **80% du succès = les 3 premières secondes** (hook)
- **Objectif rétention** : 70%+ à 3s, 60% à 15s, 50% à 30s
- **Durée optimale** : 20-25s (max viral), 60s+ pour Creator Rewards
- **Fréquence** : 3-5x/semaine TikTok, 1-3x/semaine YouTube Shorts
- **Sous-titres** : synchronisés mot par mot, blanc + contour noir = standard 2025

### Niches les plus rentables (RPM réel)
| Niche | Multiplicateur | Monétisation |
|---|---|---|
| Finance/Business | 10x | Affiliate ClickBank 50-75% + brand deals 1500-5000€ |
| Santé premium | 8x | TikTok Shop 15-20% + supplements affiliate |
| IA & outils | 6x | SaaS affiliate 20-40% récurrent |
| Création contenu | 6x | Formation + coaching |
| Dev personnel | 5x | Formations + brand deals |

### TikTok Creator Rewards 2025
- Finance/Tech/Santé : $0.40-1.00+/1000 vues
- Contenu général : $0.05-0.15/1000 vues
- Prérequis : vidéos > 1 minute, audience qualifiée

### Stratégie monétisation
- **3+ sources de revenus** = 5-6x plus de revenus
- Sources : Creator Rewards + Affiliate + Brand deals + Produit propre
- CTA optimal : question spécifique + spoken + text, dernières 3-5 secondes

### Types de hooks validés (taux rétention)
1. **Transformationnel** : "Je suis passé de X à Y en Z jours"
2. **Déclaration audacieuse négative** : 1.3-1.8x plus performant que positif
3. **Question curiosité** : crée un "curiosity gap"
4. **Nombre précis** : "73%" >> "la plupart"
5. **Contre-intuitif** : contredit la sagesse conventionnelle

---

## Structure du projet
```
studio-carton/
├── backend/
│   ├── app/
│   │   ├── api/routes/
│   │   │   ├── health.py
│   │   │   ├── videos.py
│   │   │   ├── prompts.py
│   │   │   ├── pipeline.py      # génération + preview-script + captions
│   │   │   ├── niches.py        # agent niches + génération script depuis niche
│   │   │   └── users.py         # auth email + crédits + Stripe
│   │   ├── core/config.py
│   │   ├── db/database.py       # SQLite sur volume /data
│   │   ├── schemas/
│   │   ├── services/
│   │   │   ├── script_service.py    # hooks viraux + structures par durée
│   │   │   ├── tts_service.py       # edge-tts + timestamps + fallback gTTS
│   │   │   ├── subtitle_service.py  # sync par mot ou fallback égal
│   │   │   ├── assembler_service.py # MoviePy 9:16 + sous-titres jaunes
│   │   │   ├── background_service.py# Pexels clips via ffmpeg
│   │   │   ├── niche_service.py     # analyse niches + données monétisation
│   │   │   ├── caption_service.py   # captions TikTok/YouTube/Instagram
│   │   │   └── pipeline_service.py  # orchestrateur async
│   │   └── main.py
│   └── requirements.txt
├── frontend/src/
│   ├── components/
│   │   ├── LandingPage.jsx      # landing page + auth
│   │   ├── NicheAgent.jsx       # agent niches avec scripts + monétisation
│   │   ├── PipelineForm.jsx     # form + preview script + hooks
│   │   ├── PipelineGallery.jsx  # galerie + prêt à poster
│   │   ├── GeneratorForm.jsx
│   │   └── VideoGallery.jsx
│   ├── api/client.js
│   └── App.jsx
├── Dockerfile
├── railway.toml
└── PROJET.md
```

---

## Prochaines étapes prioritaires

### Court terme
- [ ] Auto-post YouTube Shorts (YouTube Data API)
- [ ] Auto-post TikTok
- [ ] Scheduler (planifier X vidéos/semaine)
- [ ] Dashboard analytics (suivre les performances)

### Moyen terme
- [ ] Génération batch optimisée
- [ ] Musique de fond intégrée
- [ ] Nom de domaine personnalisé

### Long terme
- [ ] Auto-post Instagram Reels
- [ ] A/B testing hooks automatique
- [ ] Analytics par niche pour optimiser

---

## Historique des sessions

### Session 1 — 2026-05-28
- Initialisation, déploiement Railway, premiers essais

### Session 2 — 2026-05-29
- Pipeline complet fonctionnel
- Remplacement Anthropic → Groq, ElevenLabs → edge-tts → gTTS
- Fond vidéo Pexels via ffmpeg
- Agent Niches avec hooks + scripts + hashtags
- Preview script avant génération vidéo
- Captions prêt à poster (TikTok/YouTube/Instagram)
- Persistence volume Railway /data
- Voix edge-tts Microsoft Denise Neural ✅
- Sous-titres synchronisés mot par mot via WordBoundary ✅
- Recherche virale : données RPM, hooks, niches, monétisation intégrées
