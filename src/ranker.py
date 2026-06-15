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
src_dir = root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from feature_engineering import extract_features
import behavioral_score
import honeypot_detector
import semantic_match
import numpy as np
import re

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
    "semantic": {
        "weight": 0.0,
        "model": "all-MiniLM-L6-v2",
        "cache_dir": ".cache/embeddings",
        "prefilter_k": 0,
        "prefilter_skill_weight": 0.3,
    },
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


def rank_candidates(
    candidates: List[Dict[str, Any]],
    top_k: int = 100,
    jd_text: str | None = None,
    semantic_weight: float | None = None,
    semantic_model: str | None = None,
    semantic_cache_dir: str | None = None,
    prefilter_k: int | None = None,
    prefilter_skill_weight: float | None = None,
    semantic_field_weights: Dict[str, float] | None = None,
) -> List[Dict[str, Any]]:
    """Score and rank candidates, returning top_k rows with candidate_id, rank, score, reasoning.

    Optional semantic integration: if `jd_text` is provided and semantic weight > 0,
    the function will compute semantic similarity for a prefiler subset and combine
    it with the baseline `candidate_score` using the configured weight.
    """

    # Load semantic config defaults from CONFIG if not provided
    sem_cfg = CONFIG.get("semantic", {}) or {}
    if semantic_weight is None:
        semantic_weight = float(sem_cfg.get("weight", 0.0))
    if semantic_model is None:
        semantic_model = str(sem_cfg.get("model", "all-MiniLM-L6-v2"))
    if semantic_cache_dir is None:
        semantic_cache_dir = str(sem_cfg.get("cache_dir", ".cache/embeddings"))
    if prefilter_k is None:
        prefilter_k = int(sem_cfg.get("prefilter_k", 0))
    if prefilter_skill_weight is None:
        prefilter_skill_weight = float(sem_cfg.get("prefilter_skill_weight", 0.3))

    # Compute baseline scores for all candidates
    baseline = []
    for c in candidates:
        try:
            sc = candidate_score(c)
        except Exception:
            logger.exception("Failed to score candidate %s; assigning score 0", c.get("candidate_id"))
            sc = 0.0
        baseline.append(float(sc))

    baseline_arr = np.array(baseline, dtype=float)

    final_scores = baseline_arr.copy()

    # If semantic not requested or no JD provided, skip semantic step
    w = float(semantic_weight)
    if w > 0.0 and jd_text:
        # Prefilter by baseline + skill overlap to limit expensive embedding work
        jd_tokens = set(re.findall(r"\w+", jd_text.lower()))
        overlap_counts = []
        for c in candidates:
            skills = [s.get("name", "") for s in (c.get("skills") or [])]
            skill_set = {s.lower() for s in skills if s}
            overlap_counts.append(len(skill_set & jd_tokens))
        overlap_arr = np.array(overlap_counts, dtype=float)
        max_ov = float(max(1.0, overlap_arr.max()))
        overlap_norm = overlap_arr / max_ov

        alpha = float(prefilter_skill_weight)
        prefilter_score = (1.0 - alpha) * baseline_arr + alpha * overlap_norm

        # choose indices
        n = len(candidates)
        pre_k = int(prefilter_k)
        if pre_k <= 0 or pre_k >= n:
            pre_indices = list(range(n))
        else:
            pre_indices = list(np.argsort(-prefilter_score)[:pre_k])

        # Build embeddings for prefiltered candidates and compute semantic scores
        candidates_pref = [candidates[i] for i in pre_indices]
        embeddings = semantic_match.build_candidate_embeddings(candidates_pref, model_name=semantic_model, cache_dir=Path(semantic_cache_dir))
        sem_scores_pref, _ = semantic_match.score_against_jd(
            jd_text,
            embeddings,
            model_name=semantic_model,
            field_weights=semantic_field_weights,
            cache_dir=Path(semantic_cache_dir),
            candidates=candidates_pref,
        )
        sem_norm_pref = (np.array(sem_scores_pref, dtype=float) + 1.0) / 2.0

        # Combine for prefiltered candidates
        for idx_local, global_idx in enumerate(pre_indices):
            final_scores[global_idx] = w * float(sem_norm_pref[idx_local]) + (1.0 - w) * baseline_arr[global_idx]

    # Build rows for sorting
    rows = []
    for i, c in enumerate(candidates):
        rows.append({"candidate_id": c.get("candidate_id"), "score": float(final_scores[i]), "candidate": c})

    # Sort primarily by score (descending) and break ties by candidate_id (ascending).
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
