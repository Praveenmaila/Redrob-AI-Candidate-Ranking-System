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
import heapq
import logging
import re

import numpy as np

# Ensure repo src on path
import sys
root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.insert(0, str(root))
src_dir = root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from src.load_data import read_text_smart, load_candidates, iter_valid_candidates
from src import semantic_match
from src import ranker
from src.reasoning import generate_reasoning

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


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

    # Read JD once (small, in-memory is fine)
    jd_text = read_text_smart(args.jd)
    jd_tokens = set(re.findall(r"\w+", jd_text.lower()))

    pre_k = int(args.prefilter_k)
    alpha = float(args.prefilter_skill_weight)

    # STREAMING PASS: compute baseline + skill overlap per-candidate and
    # maintain a min-heap of size pre_k based on the blended prefilter score.
    # This avoids ever materializing the full candidate list in memory.
    heap: List[Tuple[float, int, Dict, float]] = []
    tie_counter = 0
    total_seen = 0
    overlap_max_seen = 0.0

    for c in iter_valid_candidates(
        args.candidates,
        schema_path="data/candidate_schema.json",
        validate=False,
    ):
        total_seen += 1
        try:
            base = float(ranker.candidate_score(c))
        except Exception:
            base = 0.0
        skills = [s.get("name", "") for s in (c.get("skills") or [])]
        skill_set = {s.lower() for s in skills if s}
        overlap = float(len(skill_set & jd_tokens))
        overlap_max_seen = max(overlap_max_seen, overlap)
        norm = overlap / max(1.0, overlap_max_seen)
        prefilter_score = (1.0 - alpha) * base + alpha * norm
        item = (prefilter_score, tie_counter, c, overlap)
        tie_counter += 1
        if pre_k <= 0 or len(heap) < pre_k:
            heapq.heappush(heap, item)
        else:
            if prefilter_score > heap[0][0]:
                heapq.heapreplace(heap, item)

    logger.info(
        "Streaming prefilter complete: total_seen=%d, heap_size=%d, max_overlap=%.0f",
        total_seen, len(heap), overlap_max_seen,
    )

    # Fallback: no prefilter budget, stream the file again through the
    # heap-based ranker (baseline only).
    if pre_k <= 0:
        ranked = ranker.rank_candidates_stream(
            iter_valid_candidates(
                args.candidates,
                schema_path="data/candidate_schema.json",
                validate=False,
            ),
            top_k=args.top,
        )
        ranker.write_submission_csv(ranked, args.out)
        print(f"Wrote {len(ranked)} rows to {args.out}")
        return

    # IN-MEMORY PASS (bounded at pre_k candidates): build embeddings for the
    # prefiltered subset and combine baseline + semantic.
    drained = sorted(heap, key=lambda t: -t[0])
    cand_subset = [t[2] for t in drained]

    embeddings = semantic_match.build_candidate_embeddings(
        cand_subset,
        model_name=args.model,
        cache_dir=Path(args.cache_dir),
    )
    sem_scores_pref, _ = semantic_match.score_against_jd(
        jd_text,
        embeddings,
        model_name=args.model,
        cache_dir=Path(args.cache_dir),
        candidates=cand_subset,
    )
    sem_norm_pref = (sem_scores_pref + 1.0) / 2.0

    w = float(args.semantic_weight)
    baseline_pref = np.array(
        [float(ranker.candidate_score(c)) for c in cand_subset],
        dtype=float,
    )
    final_pref = w * sem_norm_pref.astype(float) + (1.0 - w) * baseline_pref

    rows = sorted(
        zip(final_pref.tolist(), cand_subset),
        key=lambda t: (-round(t[0], 4), t[1].get("candidate_id") or ""),
    )[: args.top]

    out_rows = []
    for rank_idx, (score, c) in enumerate(rows):
        reason = generate_reasoning(c, score)
        out_rows.append({
            "candidate_id": c.get("candidate_id"),
            "rank": rank_idx + 1,
            "score": float(score),
            "reasoning": reason,
        })

    ranker.write_submission_csv(out_rows, args.out)
    print(f"Wrote {len(out_rows)} rows to {args.out}")


if __name__ == "__main__":
    main()
