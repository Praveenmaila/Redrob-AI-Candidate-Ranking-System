"""Generate concise, factual, audit-ready explanations for candidate rankings.

This module only references fields present on the candidate object and
deterministic computed features to avoid hallucination. The output is a
short natural-language string listing strengths and concerns.
"""
from __future__ import annotations

from typing import Dict, Any, Optional

from feature_engineering import extract_features
import honeypot_detector


def _fmt_pct(x: Optional[float]) -> str:
    try:
        return f"{float(x):.0%}"
    except Exception:
        return "n/a"


def generate_reasoning(candidate: Dict[str, Any], score: Optional[float] = None) -> str:
    """Produce a short, factual reasoning string for `candidate`.

    Includes: title, years, 1-2 strengths, 0-2 concerns. Uses only candidate
    fields and deterministic feature outputs.
    """
    profile = candidate.get("profile", {})
    title = profile.get("current_title") or "Candidate"
    years = profile.get("years_of_experience")
    try:
        years_f = float(years)
        years_s = f"{years_f:.1f} yrs"
    except Exception:
        years_s = "n/a"

    feats = extract_features(candidate)
    ai_count = int(feats.get("ai_skill_count", 0))
    avg_assessment = float(feats.get("avg_assessment", 0.0))
    github = float(feats.get("github_score", 0.0))

    signals = candidate.get("redrob_signals", {}) or {}
    resp = signals.get("recruiter_response_rate")
    resp_s = _fmt_pct(resp)

    strengths = []
    concerns = []

    if ai_count >= 1:
        strengths.append(f"{ai_count} AI skills")
    if avg_assessment >= 70:
        strengths.append(f"strong assessments ({avg_assessment:.0f})")
    if github > 0:
        strengths.append(f"github activity {int(github)}")
    if resp is not None and float(resp) >= 0.6:
        strengths.append(f"high recruiter response {resp_s}")

    # Concerns
    honeypot_pen = honeypot_detector.compute_honeypot_penalty(candidate)
    if honeypot_pen >= 0.25:
        concerns.append("possible profile inconsistencies")
    if resp is None or float(resp) < 0.2:
        concerns.append("low recruiter response")
    notice = signals.get("notice_period_days")
    try:
        if notice is not None and int(notice) > 60 and not signals.get("open_to_work_flag"):
            concerns.append("long notice period")
    except Exception:
        pass

    # Compose short sentence
    parts = []
    parts.append(f"{title} with {years_s}")
    if strengths:
        parts.append("Strengths: " + ", ".join(strengths))
    if concerns:
        parts.append("Concerns: " + ", ".join(concerns))

    return "; ".join(parts) + "."


def generate_structured_reasoning(
    candidate: Dict[str, Any],
    score: Optional[float] = None,
    semantic_score: Optional[float] = None,
) -> Dict[str, Any]:
    """Produce a structured dict with title, years, strengths, concerns, and
    approximate score-component breakdowns.

    The percentage breakdowns are derived from the same normalized component
    values already computed by ``candidate_score()`` so they are deterministic
    and auditable.
    """
    profile = candidate.get("profile", {})
    title = profile.get("current_title") or "Candidate"
    years = profile.get("years_of_experience")
    try:
        years_f = float(years)
    except Exception:
        years_f = 0.0

    feats = extract_features(candidate)
    ai_count = int(feats.get("ai_skill_count", 0))
    avg_assessment = float(feats.get("avg_assessment", 0.0))
    github = float(feats.get("github_score", 0.0))

    signals = candidate.get("redrob_signals", {}) or {}
    resp = signals.get("recruiter_response_rate")

    # ---- Strengths / concerns (same logic as generate_reasoning) ----------
    strengths: list[str] = []
    concerns: list[str] = []

    if ai_count >= 1:
        strengths.append(f"{ai_count} AI skills")
    if avg_assessment >= 70:
        strengths.append(f"Strong assessments ({avg_assessment:.0f})")
    if github > 0:
        strengths.append(f"GitHub activity {int(github)}")
    if resp is not None and float(resp) >= 0.6:
        strengths.append(f"High recruiter response {_fmt_pct(resp)}")

    honeypot_pen = honeypot_detector.compute_honeypot_penalty(candidate)
    if honeypot_pen >= 0.25:
        concerns.append("Possible profile inconsistencies")
    if resp is None or float(resp or 0) < 0.2:
        concerns.append("Low recruiter response")
    notice = signals.get("notice_period_days")
    try:
        if notice is not None and int(notice) > 60 and not signals.get("open_to_work_flag"):
            concerns.append("Long notice period")
    except Exception:
        pass

    # ---- Approximate score breakdowns (normalized 0-100) ------------------
    # Experience match: years / 20 (same scale as ranker years_scale)
    experience_match_pct = int(round(min(100.0, (years_f / 20.0) * 100.0)))

    # Skill match: based on AI skill count / 5 scale + assessment contribution
    skill_raw = min(1.0, ai_count / 5.0) * 0.6 + min(1.0, avg_assessment / 100.0) * 0.4
    skill_match_pct = int(round(skill_raw * 100.0))

    # Semantic match: use the provided semantic_score if available (cosine similarity
    # normalized to [0,1] by the caller). Otherwise estimate from score components.
    if semantic_score is not None:
        semantic_match_pct = int(round(float(semantic_score) * 100.0))
    else:
        # Fallback estimate: use score minus baseline components contribution
        semantic_match_pct = int(round(min(100.0, (score or 0.0) * 100.0 * 0.7)))

    return {
        "title": title,
        "years_experience": round(years_f, 1),
        "strengths": strengths,
        "concerns": concerns,
        "semantic_match_pct": max(0, min(100, semantic_match_pct)),
        "skill_match_pct": max(0, min(100, skill_match_pct)),
        "experience_match_pct": max(0, min(100, experience_match_pct)),
    }


__all__ = ["generate_reasoning", "generate_structured_reasoning"]
