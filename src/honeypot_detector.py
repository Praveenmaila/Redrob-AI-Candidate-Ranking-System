"""Honeypot detection and penalty scoring.

Detects suspicious candidate profiles using heuristic checks:
- impossible employment timelines (overlapping roles with unrealistic hours)
- expert skills with near-zero duration
- unrealistic experience claims vs career history
- missing profile elements combined with extreme claims

The main function `compute_honeypot_penalty(candidate)` returns a penalty
in [0,1] where 0=no penalty and 1=maximum penalty.
"""

from __future__ import annotations

from typing import Dict
import math


def _overlap_months(entry1: Dict, entry2: Dict) -> int:
    try:
        s1 = entry1.get("start_date")
        e1 = entry1.get("end_date") or entry1.get("start_date")
        s2 = entry2.get("start_date")
        e2 = entry2.get("end_date") or entry2.get("start_date")
        # parse year-month naive: YYYY-MM-DD -> YYYY-MM
        y1 = int(s1[:4])
        m1 = int(s1[5:7])
        y1e = int(e1[:4])
        m1e = int(e1[5:7])
        y2 = int(s2[:4])
        m2 = int(s2[5:7])
        y2e = int(e2[:4])
        m2e = int(e2[5:7])
    except Exception:
        return 0

    start1 = y1 * 12 + m1
    end1 = y1e * 12 + m1e
    start2 = y2 * 12 + m2
    end2 = y2e * 12 + m2e

    overlap = max(0, min(end1, end2) - max(start1, start2))
    return overlap


def compute_honeypot_penalty(candidate: Dict) -> float:
    penalty = 0.0
    history = candidate.get("career_history", [])

    # 1) Check for overlapping roles with significant overlap (>6 months)
    for i in range(len(history)):
        for j in range(i + 1, len(history)):
            ov = _overlap_months(history[i], history[j])
            if ov >= 6:
                # overlapping substantial tenure is suspicious
                penalty += 0.25

    # 2) Expert skills with near-zero duration
    skills = candidate.get("skills", []) or []
    for s in skills:
        prof = s.get("proficiency")
        dur = s.get("duration_months", 0) or 0
        if prof == "expert" and dur < 6:
            penalty += 0.15

    # 3) Claimed years_of_experience inconsistent with career history total
    profile = candidate.get("profile", {})
    claimed = profile.get("years_of_experience")
    try:
        claimed = float(claimed)
    except Exception:
        claimed = None

    total_months = 0
    for e in history:
        total_months += int(e.get("duration_months", 0) or 0)
    total_years = total_months / 12.0 if total_months > 0 else 0.0

    if claimed is not None and total_years > 0:
        if claimed - total_years > 3.0:
            # claimed significantly larger than history
            penalty += 0.2

    # 4) Missing or minimal descriptions while claiming high seniority
    senior_titles = ["senior", "lead", "principal", "manager", "director"]
    high_title = any(t for t in [profile.get("current_title", "")] if any(k in t.lower() for k in senior_titles))
    long_history = total_years >= 5.0
    descriptions = sum(1 for e in history if (e.get("description") or "").strip())
    if high_title and long_history and descriptions < max(1, len(history) // 3):
        penalty += 0.15

    # Cap to [0,1]
    penalty = max(0.0, min(1.0, penalty))
    return float(penalty)


__all__ = ["compute_honeypot_penalty"]
