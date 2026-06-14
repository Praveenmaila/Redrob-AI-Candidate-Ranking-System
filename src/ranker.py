"""Ranking utilities: combine behavioral, availability, feature, and honeypot signals
to produce a final candidate score and top-K submission CSV.

Public functions:
- `candidate_score(candidate) -> float` : returns a normalized score in [0,1]
- `rank_candidates(candidates, top_k=100) -> list[dict]` : returns ranked rows
- `write_submission_csv(rows, out_path)` : writes CSV with candidate_id,rank,score,reasoning

This module aims for deterministic, auditable scoring using only candidate data.
"""

from __future__ import annotations

from typing import List, Dict, Any
import csv
import math
import logging

import os
import sys
from pathlib import Path

# Ensure project root is on sys.path so modules using `from src import ...` resolve
root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from feature_engineering import extract_features
import behavioral_score
import honeypot_detector

# Load configurable weights from YAML (optional)
DEFAULT_CONFIG = {
    "components": {
        "behavioral": 0.45,
        "availability": 0.15,
        "assessment": 0.15,
        "github": 0.10,
        "years": 0.10,
        "ai_boost": 0.05,
    },
    "honeypot_penalty_weight": 0.25,
    "ai_boost_scale": 5.0,
    "years_scale": 20.0,
}


def load_config(path: str = None) -> Dict[str, Any]:
    p = Path(path) if path else Path("config/ranker_config.yaml")
    if not p.exists():
        return DEFAULT_CONFIG
    try:
        import yaml

        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        # merge defaults for missing keys
        cfg = DEFAULT_CONFIG.copy()
        comp = cfg["components"].copy()
        comp.update((data.get("components") or {}))
        cfg.update(data)
        cfg["components"] = comp
        return cfg
    except Exception:
        logger.warning("Failed to load YAML config %s; using defaults", p)
        return DEFAULT_CONFIG


# load once
CONFIG = load_config()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def _safe_get(d: Dict, key: str, default=0.0):
    try:
        return d.get(key, default)
    except Exception:
        return default


def candidate_score(candidate: Dict[str, Any]) -> float:
    """Compute an overall score for a single candidate in [0,1].

    The score combines platform behavioral signals, availability, assessment and
    github signals, experience and an AI-skill boost, and subtracts any honeypot
    penalty. Designed to be simple, explainable, and deterministic.
    """
    feats = extract_features(candidate)

    signals = candidate.get("redrob_signals", {}) or {}

    behavioral = behavioral_score.compute_behavioral_score(signals)
    availability = behavioral_score.compute_availability_score(signals)

    # normalize features from extract_features
    years = float(_safe_get(candidate.get("profile", {}), "years_of_experience", feats.get("years_experience", 0.0)))
    years_scale = float(CONFIG.get("years_scale", DEFAULT_CONFIG["years_scale"]))
    years_norm = float(max(0.0, min(1.0, years / years_scale)))

    github_raw = float(feats.get("github_score", 0.0))
    github_norm = float(max(0.0, min(1.0, github_raw / 100.0)))

    assessment_raw = float(feats.get("avg_assessment", 0.0))
    assessment_norm = float(max(0.0, min(1.0, assessment_raw / 100.0)))

    ai_count = int(feats.get("ai_skill_count", 0))
    ai_scale = float(CONFIG.get("ai_boost_scale", DEFAULT_CONFIG["ai_boost_scale"]))
    ai_boost = float(max(0.0, min(1.0, ai_count / ai_scale)))

    honeypot_pen = float(honeypot_detector.compute_honeypot_penalty(candidate))

    # Weighted aggregation (configurable)
    comp = CONFIG.get("components", DEFAULT_CONFIG["components"]) or DEFAULT_CONFIG["components"]
    score = 0.0
    score += float(comp.get("behavioral", 0.45)) * behavioral
    score += float(comp.get("availability", 0.15)) * availability
    score += float(comp.get("assessment", 0.15)) * assessment_norm
    score += float(comp.get("github", 0.10)) * github_norm
    score += float(comp.get("years", 0.10)) * years_norm
    score += float(comp.get("ai_boost", 0.05)) * ai_boost

    # subtract penalty (configurable)
    hp_w = float(CONFIG.get("honeypot_penalty_weight", DEFAULT_CONFIG["honeypot_penalty_weight"]))
    score -= float(hp_w) * honeypot_pen

    # clamp to [0,1]
    score = float(max(0.0, min(1.0, score)))
    return score


def _build_reasoning(candidate: Dict[str, Any], score: float) -> str:
    try:
        from reasoning import generate_reasoning

        return generate_reasoning(candidate, score)
    except Exception:
        # fallback to minimal inline explanation
        profile = candidate.get("profile", {})
        title = profile.get("current_title") or "Candidate"
        years = profile.get("years_of_experience")
        try:
            years_f = float(years)
            years_s = f"{years_f:.1f} yrs"
        except Exception:
            years_s = "n/a"
        return f"{title} with {years_s}."


def rank_candidates(candidates: List[Dict[str, Any]], top_k: int = 100) -> List[Dict[str, Any]]:
    """Score and rank candidates, returning top_k rows with candidate_id, rank, score, reasoning."""
    rows = []
    for c in candidates:
        cid = c.get("candidate_id")
        try:
            sc = candidate_score(c)
        except Exception:
            logger.exception("Failed to score candidate %s; assigning score 0", cid)
            sc = 0.0
        rows.append({"candidate_id": cid, "score": float(sc), "candidate": c})

    # Sort primarily by score (descending) and break ties by candidate_id (ascending).
    # Use rounded score to 4 decimals to match CSV formatting used when writing.
    rows.sort(key=lambda r: (-round(r["score"], 4), r["candidate_id"]))
    top = []
    for i, r in enumerate(rows[:top_k]):
        rank = i + 1
        cid = r["candidate_id"]
        score = r["score"]
        reasoning = _build_reasoning(r["candidate"], score)
        top.append({"candidate_id": cid, "rank": rank, "score": score, "reasoning": reasoning})
    return top


def write_submission_csv(rows: List[Dict[str, Any]], out_path: str) -> None:
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for r in rows:
            writer.writerow([r["candidate_id"], r["rank"], f"{r['score']:.4f}", r["reasoning"]])


if __name__ == "__main__":
    import argparse
    from src.load_data import load_candidates

    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--out", default="submission_top100.csv")
    parser.add_argument("--top", type=int, default=100)
    args = parser.parse_args()

    cand = load_candidates(args.candidates, validate=False)
    ranked = rank_candidates(cand, top_k=args.top)
    write_submission_csv(ranked, args.out)
    print(f"Wrote {len(ranked)} rows to {args.out}")
