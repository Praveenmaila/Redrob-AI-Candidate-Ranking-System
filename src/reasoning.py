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


__all__ = ["generate_reasoning"]
