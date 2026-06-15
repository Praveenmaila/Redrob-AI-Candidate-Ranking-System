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

**Experiments & Configuration**

- **Root Cause (dimension mismatch):** cached embeddings were produced by a TF‑IDF fallback (vocabulary-based dim, e.g. 513) while later runs used a SentenceTransformers model (384 dims). The code previously lacked explicit cache backend/dimension metadata so incompatible caches were reused, causing dot‑product shape errors.

- **Fixes implemented:** `src/semantic_match.py` now records `backend` (`st` or `tfidf`) and `dim` in `.meta.json`, validates candidate ids, backend and dimension on load, and automatically recomputes incompatible caches. `.npz` files are loaded with `mmap_mode='r'` to reduce memory pressure.

- **Semantic integration:** `src/ranker.py` now accepts `jd_text` and optional semantic parameters (weight, model, cache_dir, prefilter_k, prefilter_skill_weight, semantic_field_weights). When enabled the pipeline:
  - computes baseline `candidate_score()` for all candidates
  - prefilters top‑N candidates by a cheap baseline+skill overlap score (configurable `prefilter_k`)
  - computes per‑field embeddings for the prefiler set and scores the JD with `score_against_jd`
  - normalizes semantic cosine scores to [0,1] and combines with baseline using `semantic.weight`

- **Config knobs (where to change):**
  - **File / Setting:** `src/ranker.py` / `DEFAULT_CONFIG['semantic']`
  - **Key:** `weight` — semantic contribution (0.0–1.0)
  - **Key:** `model` — sentence‑transformer model name / local path
  - **Key:** `cache_dir` — embeddings cache path
  - **Key:** `prefilter_k` — number of candidates to embed for semantic scoring (0 = disable prefilter)
  - **Key:** `prefilter_skill_weight` — balance between baseline and skill overlap in prefilter
  - **Argument-level:** `rank_candidates(..., semantic_field_weights={...})` to change per-field JD weights

- **Recommended default values for experiments:**
  - `semantic.weight = 0.3..0.6` (start with 0.5)
  - `prefilter_k = 1000..3000` for 100k dataset on CPU; use GPU or larger prefilter if available
  - per-field JD weights (start): `{"summary":0.65, "career_history":0.25, "headline":0.10}`

- **Quick experiment commands:**
  - Sweep semantic weights on small data:
    ```bash
    python scripts/experiment_weights.py --semantic-weights 0,0.25,0.5,0.75,1.0
    ```
  - Produce a Top‑100 submission (prefilter 2000, semantic=0.5):
    ```powershell
    Remove-Item -Recurse -Force .cache\embeddings\*
    python -c "from src.load_data import load_candidates; from src.ranker import rank_candidates, write_submission_csv; cand=load_candidates('data/candidates.jsonl', validate=False); jd=open('data/sample_jd.txt').read(); rows=rank_candidates(cand, top_k=100, jd_text=jd, semantic_weight=0.5, semantic_model='all-MiniLM-L6-v2', semantic_cache_dir='.cache/embeddings', prefilter_k=2000); write_submission_csv(rows, 'submission_top100.csv')"
    python src/validator.py submission_top100.csv
    ```

- **Performance tips:**
  - Use `prefilter_k` to avoid embedding all 100k candidates on CPU; embedding scales linearly with candidates × model_dim.
  - If a GPU is available, increase `batch_size` in `semantic_match.embed_texts` and prefer GPU device when calling `load_model(..., device='cuda')`.
  - Keep `.cache/embeddings/` persisted between experiments; delete only when changing model/backend.

- **Explainability notes:** the final CSV includes a `reasoning` column assembled by `src/reasoning.py` (fallbacks provided). The system also preserves per-field semantic scores for audit if needed.

**Reproducibility checklist (to produce validated submission)**

- Clear stale embeddings: remove `.cache/embeddings/*` if you changed model or see cache mismatch logs.
- Run a controlled experiment on `candidates_small.jsonl` with `scripts/experiment_weights.py` to pick a semantic weight.
- Run a full submission generation with recommended `prefilter_k` and validate with `src/validator.py`.
- Commit changes and the `methodology.md` summary to the repository.

**Next actions**

- Run a full-scale run with `prefilter_k=2000` and `semantic.weight=0.5` to produce `submission_top100.csv` and inspect top candidates.
- Write short ablation notes (precision@10/20) for the final `methodology.md` after running full experiments.
- Optionally remove `streamlit` from `requirements.txt` and delete `app/streamlit_app.py` if UI not required.
