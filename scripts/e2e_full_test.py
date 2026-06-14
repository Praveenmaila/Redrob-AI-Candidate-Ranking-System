"""End-to-end full pipeline test on data/candidates.jsonl.

Measures wall-clock time for each stage and writes metrics to
`scripts/e2e_full_metrics.json`.
"""
from __future__ import annotations

import time
import json
import sys
from pathlib import Path

# Ensure project root and src on path
root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.insert(0, str(root))
src_dir = root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from src.load_data import load_candidates
from src import semantic_match
from src import feature_engineering
from src import ranker
from src import validator


def main():
    out_metrics = {}
    t0 = time.perf_counter()

    cand_path = Path("data/candidates.jsonl")
    schema = Path("data/candidate_schema.json")

    t = time.perf_counter()
    candidates = load_candidates(str(cand_path), schema_path=str(schema), validate=True)
    out_metrics["n_candidates"] = len(candidates)
    out_metrics["load_time_s"] = time.perf_counter() - t

    # Build/load embeddings
    t = time.perf_counter()
    embeddings = semantic_match.build_candidate_embeddings(candidates, model_name="all-MiniLM-L6-v2", cache_dir=Path(".cache/embeddings"))
    out_metrics["embeddings_time_s"] = time.perf_counter() - t

    # Build features (jd_parsed minimal)
    t = time.perf_counter()
    jd_parsed = {"required_skills": [], "preferred_skills": [], "min_experience_years": None, "titles": [], "industries": []}
    features_df = feature_engineering.build_features(candidates, jd_parsed, cache_dir=Path(".cache/embeddings"))
    out_metrics["feature_build_time_s"] = time.perf_counter() - t
    out_metrics["n_features"] = features_df.shape[0]

    # Ranking
    t = time.perf_counter()
    ranked = ranker.rank_candidates(candidates, top_k=100)
    out_metrics["ranking_time_s"] = time.perf_counter() - t

    # Write CSV
    t = time.perf_counter()
    out_csv = Path("submission_top100_full.csv")
    ranker.write_submission_csv(ranked, str(out_csv))
    out_metrics["write_time_s"] = time.perf_counter() - t

    # Validate
    t = time.perf_counter()
    errors = validator.validate_submission(str(out_csv))
    out_metrics["validation_time_s"] = time.perf_counter() - t
    out_metrics["validation_errors"] = errors

    out_metrics["total_time_s"] = time.perf_counter() - t0

    metrics_path = Path("scripts/e2e_full_metrics.json")
    metrics_path.write_text(json.dumps(out_metrics, indent=2), encoding="utf-8")

    print(json.dumps(out_metrics, indent=2))


if __name__ == "__main__":
    main()
