"""Generate Top-K submission combining semantic matching and existing signals.

Usage:
    python scripts/generate_submission.py --candidates data/candidates.jsonl --jd data/sample_jd.txt --out submission_top100.csv

This script:
- Loads candidates
- Builds/loads embeddings (SentenceTransformers or TF-IDF fallback)
- Computes semantic similarity scores against JD
- Computes existing ranker scores
- Combines semantic and ranker scores using a configurable weight
- Writes Top-K CSV suitable for submission
"""
from __future__ import annotations

import argparse
from pathlib import Path
import json

# Ensure repo src on path
import sys
root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.insert(0, str(root))
src_dir = root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from src.load_data import load_candidates
from src import semantic_match
from src import ranker
from src.reasoning import generate_reasoning


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", default="data/candidates.jsonl")
    parser.add_argument("--jd", default="data/sample_jd.txt")
    parser.add_argument("--out", default="submission_top100.csv")
    parser.add_argument("--top", type=int, default=100)
    parser.add_argument("--model", default="all-MiniLM-L6-v2")
    parser.add_argument("--cache-dir", default=".cache/embeddings")
    parser.add_argument("--semantic-weight", type=float, default=0.5, help="Weight for semantic score in final aggregation (0..1)")
    parser.add_argument("--prefilter-k", type=int, default=2000, help="Number of candidates to keep for expensive semantic scoring (0=disable)")
    parser.add_argument("--prefilter-skill-weight", type=float, default=0.3, help="Weight of skill-overlap in prefilter score (0..1)")
    args = parser.parse_args()

    # Load candidates and JD
    candidates = load_candidates(args.candidates, schema_path="data/candidate_schema.json", validate=False)
    jd_text = Path(args.jd).read_text(encoding="utf-8")

    # Compute baseline ranker score for each candidate (cheap)
    import numpy as np
    import re

    baseline_scores = [ranker.candidate_score(c) for c in candidates]
    baseline_arr = np.array(baseline_scores, dtype=float)

    # Prefilter: compute simple skill-overlap with JD tokens
    jd_tokens = set(re.findall(r"\w+", jd_text.lower()))
    overlap_counts = []
    for c in candidates:
        skills = [s.get("name", "") for s in (c.get("skills") or [])]
        skill_set = {s.lower() for s in skills if s}
        overlap = len(skill_set & jd_tokens)
        overlap_counts.append(overlap)
    overlap_arr = np.array(overlap_counts, dtype=float)
    # normalize overlap
    max_ov = float(max(1.0, overlap_arr.max()))
    overlap_norm = overlap_arr / max_ov

    alpha = float(args.prefilter_skill_weight)
    prefilter_score = (1.0 - alpha) * baseline_arr + alpha * overlap_norm

    # Decide which candidates to score semantically
    pre_k = int(args.prefilter_k)
    if pre_k <= 0 or pre_k >= len(candidates):
        pre_indices = list(range(len(candidates)))
    else:
        pre_indices = list(np.argsort(-prefilter_score)[:pre_k])

    # Build embeddings only for prefiltered candidates
    candidates_pref = [candidates[i] for i in pre_indices]
    embeddings = semantic_match.build_candidate_embeddings(candidates_pref, model_name=args.model, cache_dir=Path(args.cache_dir))

    # Compute semantic scores only for prefiltered candidates
    sem_scores_pref, per_field = semantic_match.score_against_jd(jd_text, embeddings, model_name=args.model, cache_dir=Path(args.cache_dir), candidates=candidates_pref)
    sem_norm_pref = (sem_scores_pref + 1.0) / 2.0

    # Combine final scores for prefiltered candidates and keep baseline for others
    w = float(args.semantic_weight)
    final = np.array(baseline_arr, dtype=float)
    for idx_local, global_idx in enumerate(pre_indices):
        final[global_idx] = w * float(sem_norm_pref[idx_local]) + (1.0 - w) * baseline_arr[global_idx]

    # Build top-k over all candidates using final score.
    # Tie-break rule: higher score first, then candidate_id ascending.
    ids = [c["candidate_id"] for c in candidates]
    # Create list of (score, candidate_id, index) and sort by (-score, candidate_id)
    keyed = [(float(final[i]), ids[i], i) for i in range(len(ids))]
    # Sort by rounded score (4 decimals) descending, then candidate_id ascending to match validator.
    keyed.sort(key=lambda t: (-round(t[0], 4), t[1]))

    rows = []
    for rank_idx, (_, cid, idx) in enumerate(keyed[: args.top]):
        score = float(final[int(idx)])
        reason = generate_reasoning(candidates[int(idx)], score)
        rows.append({"candidate_id": cid, "rank": rank_idx + 1, "score": score, "reasoning": reason})

    # Write CSV using ranker helper
    ranker.write_submission_csv(rows, args.out)
    print(f"Wrote {len(rows)} rows to {args.out}")


if __name__ == "__main__":
    main()
