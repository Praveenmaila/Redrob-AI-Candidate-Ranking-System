Methodology — Redrob AI Candidate Ranking System

Overview

- Goal: CPU-only, reproducible candidate ranking that outputs a validated top-100 CSV and deterministic, factual per-candidate reasoning.
- Constraints: No network calls at ranking time, runtime target < 5 minutes when possible (full run measured), deterministic TF-IDF fallback when transformer model unavailable.

Pipeline (stages)

- Load: `src/load_data.py` validates `data/candidates.jsonl`.
- Semantic matching: `src/semantic_match.py` uses `sentence-transformers` if available, otherwise TF-IDF fallback. Embeddings cached per-field in `.cache/embeddings/` with metadata (vocabulary as JSON-serializable ints and `dim`).
- Feature engineering: `src/feature_engineering.py` builds numeric features (skill match, title/industry match, experience, assessments, github signals).
- Behavioral scoring: `src/behavioral_score.py` computes availability and recruiter-response style signals.
- Honeypot detection: `src/honeypot_detector.py` penalizes suspicious candidates.
- Ranking: `src/ranker.py` composes features and signals with YAML-configurable weights to produce final scores and writes `submission_top100.csv`.
- Reasoning: `src/reasoning.py` emits deterministic, factual explanations referencing only candidate facts.
- Validation: `src/validator.py` enforces CSV schema, 100 rows, score ordering, and tie-break rules.

Reproducibility notes

- TF-IDF fallback ensures CPU-only reproducible embeddings; caches include `vocabulary` and `dim` to avoid shape mismatches.
- Tie-breaking uses scores rounded to 4 decimals then `candidate_id` ascending to match validator expectations.

Full-run metrics (executed: `scripts/e2e_full_test.py`)

- n_candidates: 100000
- load_time_s: 112.1385
- embeddings_time_s: 27.6790
- feature_build_time_s: 2.8648
- ranking_time_s: 6.4144
- total_time_s: 149.1103
- validation_errors: []

Top candidate

- `CAND_0018499` — score 0.8064 (see `submission_top100.csv`)

Reproduce locally

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1    # Windows PowerShell
pip install -r requirements.txt
python scripts/e2e_full_test.py
```

Next steps

- Add `methodology.md` expansion with evaluation plots and ablations.
- Build a `app/streamlit_app.py` for interactive exploration (not started).
- Optionally add `psutil`-based peak-memory measurement to `scripts/e2e_full_test.py`.
