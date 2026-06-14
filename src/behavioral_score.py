"""Behavioral and availability scoring for Redrob Ranking System.

Provides deterministic, auditable scoring functions that convert platform
engagement signals into normalized scores in [0,1]. These are CPU-only
and avoid any external dependencies beyond the Python stdlib and numpy.
"""

from __future__ import annotations

from datetime import datetime
import math
from typing import Dict, Optional

import numpy as np


def _safe_get_num(d: Dict, key: str, default: float = 0.0) -> float:
    v = d.get(key, default)
    try:
        return float(v)
    except Exception:
        return float(default)


def _days_since(date_str: Optional[str]) -> Optional[int]:
    if not date_str:
        return None
    try:
        dt = datetime.fromisoformat(date_str)
    except Exception:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
            return None
    delta = datetime.utcnow() - dt
    return max(0, delta.days)


def _log_norm(x: float, scale: float = 10.0) -> float:
    # Map non-negative x to (0,1] using log1p with provided scale
    if x <= 0:
        return 0.0
    return float(min(1.0, math.log1p(x) / math.log1p(scale)))


def compute_behavioral_score(signals: Dict) -> float:
    """Compute a normalized behavioral score from `redrob_signals`.

    Inputs supported (expected in `signals`):
    - recruiter_response_rate (0-1)
    - interview_completion_rate (0-1)
    - offer_acceptance_rate (-1..1 with -1 meaning no history)
    - profile_completeness_score (0-100)
    - saved_by_recruiters_30d (int)
    - search_appearance_30d (int)
    - profile_views_received_30d (int)
    - connection_count (int)
    - endorsements_received (int)

    Returns a float in [0,1].
    """
    rrr = _safe_get_num(signals, "recruiter_response_rate", 0.0)
    icr = _safe_get_num(signals, "interview_completion_rate", 0.0)
    oar = _safe_get_num(signals, "offer_acceptance_rate", -1.0)
    completeness = _safe_get_num(signals, "profile_completeness_score", 0.0) / 100.0
    saved = _safe_get_num(signals, "saved_by_recruiters_30d", 0.0)
    search_app = _safe_get_num(signals, "search_appearance_30d", 0.0)
    views = _safe_get_num(signals, "profile_views_received_30d", 0.0)
    conn = _safe_get_num(signals, "connection_count", 0.0)
    endors = _safe_get_num(signals, "endorsements_received", 0.0)

    # Normalize log-like signals
    saved_n = _log_norm(saved, scale=20.0)
    search_n = _log_norm(search_app, scale=50.0)
    views_n = _log_norm(views, scale=200.0)
    conn_n = _log_norm(conn, scale=500.0)
    endors_n = _log_norm(endors, scale=50.0)

    # Normalize offer acceptance: -1 => unknown -> treat as 0.5 neutral
    if oar < 0:
        oar_n = 0.5
    else:
        # map [-1,1] -> [0,1]
        oar_n = float((oar + 1.0) / 2.0)

    # recency effect: last_active_date closer -> higher score
    last_active = signals.get("last_active_date")
    days = _days_since(last_active)
    if days is None:
        recency = 0.5
    else:
        # exponential decay over ~90 days
        recency = float(math.exp(-days / 90.0))

    # Open to work boosts engagement relevance
    open_flag = 1.0 if signals.get("open_to_work_flag") else 0.0

    # Weighted aggregation (weights chosen to emphasize responsiveness and recent activity)
    weights = {
        "recruiter_response_rate": 0.18,
        "interview_completion_rate": 0.12,
        "offer_acceptance_rate": 0.12,
        "profile_completeness": 0.08,
        "saved": 0.12,
        "search": 0.08,
        "views": 0.05,
        "connections": 0.04,
        "endorsements": 0.04,
        "recency": 0.10,
        "open_to_work": 0.07,
    }

    score = 0.0
    score += weights["recruiter_response_rate"] * float(max(0.0, min(1.0, rrr)))
    score += weights["interview_completion_rate"] * float(max(0.0, min(1.0, icr)))
    score += weights["offer_acceptance_rate"] * float(max(0.0, min(1.0, oar_n)))
    score += weights["profile_completeness"] * float(max(0.0, min(1.0, completeness)))
    score += weights["saved"] * saved_n
    score += weights["search"] * search_n
    score += weights["views"] * views_n
    score += weights["connections"] * conn_n
    score += weights["endorsements"] * endors_n
    score += weights["recency"] * recency
    score += weights["open_to_work"] * open_flag

    # ensure in [0,1]
    return float(max(0.0, min(1.0, score)))


def compute_availability_score(signals: Dict) -> float:
    """Compute availability score using notice period, activity and openness.

    Logic:
    - Shorter notice -> higher availability
    - Open to work flag increases availability
    - Recent activity increases availability
    - Willing to relocate slightly increases availability
    """
    notice = signals.get("notice_period_days")
    try:
        notice = None if notice is None else int(notice)
    except Exception:
        notice = None

    if notice is None:
        notice_score = 0.5
    else:
        # linear decay up to 90 days
        notice_score = float(max(0.0, min(1.0, 1.0 - (notice / 90.0))))

    open_flag = 1.0 if signals.get("open_to_work_flag") else 0.0

    last_active = signals.get("last_active_date")
    days = _days_since(last_active)
    if days is None:
        recency = 0.5
    else:
        recency = float(math.exp(-days / 60.0))

    relocate = 1.0 if signals.get("willing_to_relocate") else 0.0

    # Weighted
    score = 0.0
    score += 0.5 * notice_score
    score += 0.2 * open_flag
    score += 0.25 * recency
    score += 0.05 * relocate

    return float(max(0.0, min(1.0, score)))


__all__ = ["compute_behavioral_score", "compute_availability_score"]
