"""Quick experiments sweeping semantic weight and printing top-10 candidates.

Usage:
    python scripts/experiment_weights.py --semantic-weights 0,0.25,0.5,0.75,1.0
    python scripts/experiment_weights.py --semantic-weights 0,0.5 --field-weights '{"summary":0.7,"headline":0.15,"career_history":0.15}'

Defaults to `data/candidates_small.jsonl` for fast runs.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from src.load_data import load_candidates
from src.ranker import rank_candidates


def parse_list(s: str):
    return [float(x) for x in s.split(",") if x.strip()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--semantic-weights", default="0,0.25,0.5,0.75,1.0")
    parser.add_argument("--field-weights", default=None, help="JSON string of field weights, e.g. '{\"summary\":0.6,...}'")
    parser.add_argument("--candidates", default="data/candidates_small.jsonl")
    parser.add_argument("--jd", default="data/sample_jd.txt")
    parser.add_argument("--top", type=int, default=10)
    args = parser.parse_args()

    s_weights = parse_list(args.semantic_weights)
    if args.field_weights:
        fw = json.loads(args.field_weights)
    else:
        fw = None

    candidates = load_candidates(args.candidates, validate=False)
    jd = Path(args.jd).read_text(encoding="utf-8")

    for w in s_weights:
        print(f"\n--- Semantic weight = {w} ---")
        rows = rank_candidates(candidates, top_k=args.top, jd_text=jd, semantic_weight=w, semantic_field_weights=fw or None, prefilter_k=200)
        for r in rows:
            print(f"{r['rank']:2d}. {r['candidate_id']}  {r['score']:.4f}  {r['reasoning']}")


if __name__ == "__main__":
    main()
