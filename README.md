# Redrob AI — Candidate Ranking System

> AI-powered candidate ranking system that analyzes 100,000 resumes, extracts skills, computes semantic similarity against job descriptions, and ranks the top 100 candidates with explainable AI reasoning.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Next.js Frontend                         │
│  ┌─────────┐  ┌──────────┐  ┌───────────┐  ┌───────────────┐  │
│  │  Upload  │  │ Progress │  │  Results  │  │  Candidate    │  │
│  │  Cards   │  │  Panel   │  │  Table    │  │  Modal        │  │
│  └────┬─────┘  └────┬─────┘  └────┬──────┘  └───────────────┘  │
│       └──────────────┴─────────────┘                            │
│                      │  direct FastAPI calls                    │
└──────────────────────┼──────────────────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                              │
│  /datasets   │  POST /rank  │  /health/results/download          │
│              │               │                │                  │
│  ┌───────────┴───────────────┴────────────────┘                  │
│  │           Ranking Pipeline (subprocess)                       │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │
│  │  │  Load    │→ │  Build   │→ │ Semantic  │→ │   Rank &     │ │
│  │  │ Dataset  │  │Embeddings│  │ Matching  │  │  Export CSV   │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────┘ │
│  └──────────────────────────────────────────────────────────────│
└──────────────────────────────────────────────────────────────────┘
              │
    ┌─────────┴──────────┐
    │   Core Modules     │
    │  ┌───────────────┐ │
    │  │ ranker.py      │ │  Multi-signal scoring (behavioral, availability,
    │  │ semantic_match │ │  assessment, GitHub, experience, AI skills)
    │  │ feature_eng    │ │  + SentenceTransformer semantic embeddings
    │  │ reasoning.py   │ │  + Honeypot detection & penalty
    │  │ behavioral.py  │ │  + Deterministic, factual reasoning
    │  │ honeypot.py    │ │
    │  └───────────────┘ │
    └────────────────────┘
```

## Methodology

### Scoring Pipeline

The ranking combines **6 scoring components** with configurable YAML weights:

| Component | Weight | Signal Source |
|-----------|--------|--------------|
| Behavioral Score | 0.45 | Recruiter response rate, interview completion, profile completeness, saved count, recency |
| Availability | 0.15 | Notice period, open-to-work flag, recent activity |
| Assessment Score | 0.15 | Skill assessment scores (normalized 0-100) |
| GitHub Activity | 0.10 | GitHub activity score |
| Experience | 0.10 | Years of experience (capped at 20 years scale) |
| AI Skill Boost | 0.05 | Count of AI-relevant skills (RAG, LLMs, Transformers, etc.) |

**Honeypot penalty** (weight: 0.25) detects and penalizes suspicious/inconsistent profiles.

### Semantic Matching

- **Model:** `all-MiniLM-L6-v2` via SentenceTransformers (384-dim embeddings)
- **TF-IDF fallback** when transformer unavailable (CPU-only reproducibility)
- **Per-field embeddings:** summary (0.6), career_history (0.25), headline (0.15)
- **Prefilter:** Top 2,000 candidates by baseline + skill overlap before expensive embedding
- **Final score:** `0.5 × semantic + 0.5 × baseline`

### Explainability

Each ranked candidate includes:
- Factual reasoning citing only candidate data (title, years, skills, assessments)
- Strengths and concerns extracted deterministically
- Score breakdowns (semantic match %, skill match %, experience match %)

## Quick Start

### Prerequisites
- Python 3.11+ with pip
- Node.js 18+ with npm

### Backend

```powershell
# From repo root
python -m venv .venv
& ".venv/Scripts/Activate.ps1"
pip install -r requirements.txt

# Start API server
python -m uvicorn backend_api:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
# Opens at http://localhost:3000
```

### Dataset Management Workflow

The frontend talks directly to FastAPI using `NEXT_PUBLIC_BACKEND_TARGET` and does not proxy uploads through Next.js.

1. Upload a candidate dataset once from the dashboard. The frontend sends it to `POST /datasets/upload`, and FastAPI streams it to `data/uploads/`.
2. Select a saved dataset from the dashboard dropdown. The list comes from `GET /datasets`.
3. Upload only the job description when running ranking. `POST /rank` receives multipart fields `jd=<file>` and `dataset=<saved filename>`.
4. Polling and outputs stay unchanged: `GET /health`, `GET /results`, and `GET /download`.

### Docker (One Command)

```powershell
docker compose up --build
# Backend → http://localhost:8000
# Frontend → http://localhost:3000
```

### Run Ranking Pipeline Directly

```powershell
python scripts/generate_submission.py \
  --candidates data/candidates.jsonl \
  --jd data/sample_jd.txt \
  --out submission_top100.csv \
  --prefilter-k 2000 \
  --semantic-weight 0.5
```

## Metrics

| Metric | Value |
|--------|-------|
| Dataset Size | 100,000 candidates (475 MB JSONL) |
| Load Time | ~112s |
| Embedding Time | ~28s |
| Ranking Time | ~6s |
| **Total Pipeline** | **~149s** |
| Top Score | 0.8064 |
| Score Range | 0.57 – 0.81 |
| Validation Errors | 0 |

## Evaluation

- **Validation:** `src/validator.py` enforces CSV schema, 100 rows, score ordering, and tie-break rules
- **Reproducibility:** Deterministic scoring with YAML-configurable weights; TF-IDF fallback ensures CPU-only reproducibility
- **Honeypot detection:** Penalizes suspicious candidates with profile inconsistencies
- **Tie-breaking:** Scores rounded to 4 decimals, then `candidate_id` ascending

## Project Structure

```
├── backend_api.py          # FastAPI server (upload, progress, results, download)
├── scripts/
│   ├── generate_submission.py  # End-to-end ranking pipeline
│   ├── smoke_rank.py       # Quick ranking smoke test
│   └── e2e_small_test.py   # E2E test with metrics
├── src/
│   ├── ranker.py           # Multi-signal scoring engine
│   ├── semantic_match.py   # SentenceTransformer embeddings + TF-IDF fallback
│   ├── feature_engineering.py  # Feature extraction (skills, GitHub, assessments)
│   ├── behavioral_score.py # Platform engagement scoring
│   ├── honeypot_detector.py # Suspicious profile detection
│   ├── reasoning.py        # Deterministic explanation generation
│   ├── load_data.py        # JSONL loading + validation
│   └── validator.py        # Submission CSV validation
├── config/
│   └── ranker_config.yaml  # Configurable scoring weights
├── frontend/               # Next.js 15 app with glassmorphism UI
│   ├── src/
│   │   ├── app/            # Pages (dashboard, results)
│   │   ├── components/     # UI components (upload, table, modal)
│   │   └── hooks/          # React hooks (useRanking)
│   └── vercel.json         # Vercel deployment config
├── data/                   # Candidate dataset + JD + schema
├── Dockerfile.backend      # Python 3.11 + PyTorch CPU backend image
├── Dockerfile.frontend     # Next.js standalone frontend image
├── docker-compose.yml      # Multi-service orchestration
├── render.yaml             # Render Blueprint for backend deploy
├── .env.example            # Environment variable template
├── methodology.md          # Detailed methodology documentation
└── submission_top100.csv   # Generated output
```

## Deployment

### Docker Compose (Recommended)

```bash
docker compose up --build -d
```

Both services are orchestrated with health checks. The frontend proxies API calls to the backend container automatically.

| Service | Port | Health Check |
|---------|------|-------------|
| Backend | 8000 | `GET /health` |
| Frontend | 3000 | `GET /` |

### Frontend (Vercel)

1. Connect the `frontend/` directory to Vercel
2. Set environment variable: `NEXT_PUBLIC_BACKEND_TARGET=https://your-backend.onrender.com`
3. Deploy — Vercel auto-detects the Next.js framework from `vercel.json`

### Backend (Render)

1. Connect the repo to Render
2. The `render.yaml` Blueprint auto-configures the service:
   - Python 3.11, PyTorch CPU-only
   - Start command: `uvicorn backend_api:app --host 0.0.0.0 --port $PORT`
   - Health check: `/health`

### Environment Variables

See [`.env.example`](.env.example) for the full list. Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_BACKEND_TARGET` | `http://localhost:8000` | Browser-reachable FastAPI URL |
| `PORT` | `8000` | Backend listen port |
| `PYTHONUNBUFFERED` | `1` | Flush Python logs immediately |

## License

Built for the Redrob Hackathon. All candidate data is synthetic.
