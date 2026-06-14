"""Feature engineering for Redrob Ranking System.

Provides deterministic, testable functions to compute core ranking features:
- Skill Match Score
- Experience Match Score
- Title Match Score
- Industry Match Score
- Education Score
- GitHub Score
- Assessment Score

The main entrypoint is `build_features(candidates, jd_parsed, ...)` which returns
a `pandas.DataFrame` with one row per candidate and numeric features normalized
to the [0, 1] range where appropriate.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import math
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from src import semantic_match

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


PROFICIENCY_WEIGHT = {
    "beginner": 0.5,
    "intermediate": 0.75,
    "advanced": 0.9,
    "expert": 1.0,
}


def _safe_get(d: Dict, path: List[str], default=None):
    cur = d
    for p in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(p)
        if cur is None:
            return default
    return cur


def compute_github_score(redrob_signals: Dict) -> float:
    score = redrob_signals.get("github_activity_score", -1)
    if score is None or score < 0:
        return 0.0
    return float(max(0.0, min(100.0, score)) / 100.0)


def compute_assessment_score(redrob_signals: Dict, jd_skills: Optional[List[str]] = None) -> float:
    assessments = redrob_signals.get("skill_assessment_scores", {}) or {}
    if not assessments:
        return 0.0
    if jd_skills:
        vals = []
        for s in jd_skills:
            v = assessments.get(s)
            if v is not None:
                vals.append(float(v))
        if vals:
            return float(np.mean(vals) / 100.0)
    # fallback to mean of all assessments
    return float(np.mean(list(assessments.values())) / 100.0)


def compute_experience_match(profile: Dict, jd_min_experience_years: Optional[float]) -> float:
    years = profile.get("years_of_experience")
    if years is None or jd_min_experience_years is None:
        return 0.0
    try:
        years = float(years)
        req = float(jd_min_experience_years)
    except Exception:
        return 0.0
    if req <= 0:
        return 1.0
    # full score if candidate meets or exceeds requirement; partial otherwise
    return float(min(1.0, years / req))


def compute_education_score(education: List[Dict]) -> float:
    if not education:
        return 0.0
    # prefer highest tier present
    tier_score = {"tier_1": 1.0, "tier_2": 0.8, "tier_3": 0.6, "tier_4": 0.4, "unknown": 0.5}
    best = 0.0
    for e in education:
        t = e.get("tier", "unknown")
        best = max(best, tier_score.get(t, 0.5))
    return float(best)


def compute_industry_match(candidate_industry: str, jd_industries: Optional[List[str]], model=None) -> float:
    if not jd_industries:
        return 0.0
    if not candidate_industry:
        return 0.0
    # exact match (case-insensitive)
    for ind in jd_industries:
        if ind and candidate_industry.strip().lower() == ind.strip().lower():
            return 1.0
    # fallback to semantic similarity between industry strings
    if model is None:
        model = semantic_match.load_model()
    cand_emb = semantic_match._embed_text_single(model, candidate_industry)
    jd_embs = np.vstack([semantic_match._embed_text_single(model, j) for j in jd_industries])
    sims = jd_embs.dot(cand_emb)
    return float(float(np.max(sims)))


def compute_title_match(candidate: Dict, jd_titles: Optional[List[str]], model=None) -> float:
    if not jd_titles:
        return 0.0
    titles = []
    profile = candidate.get("profile", {})
    cur_title = profile.get("current_title")
    if cur_title:
        titles.append(cur_title)
    # add career history titles
    for e in candidate.get("career_history", []):
        t = e.get("title")
        if t:
            titles.append(t)
    if not titles:
        return 0.0
    if model is None:
        model = semantic_match.load_model()
    jd_embs = np.vstack([semantic_match._embed_text_single(model, j) for j in jd_titles])
    cand_embs = np.vstack([semantic_match._embed_text_single(model, t) for t in titles])
    # compute max similarity between any candidate title and any jd title
    sims = cand_embs.dot(jd_embs.T)
    return float(float(np.max(sims)))


def compute_skill_match_score(
    candidate: Dict,
    jd_skills: List[str],
    model=None,
    top_k: int = 5,
) -> float:
    skills = candidate.get("skills", []) or []
    if not skills or not jd_skills:
        return 0.0
    skill_names = [s.get("name", "") for s in skills]
    if not any(skill_names):
        return 0.0
    if model is None:
        model = semantic_match.load_model()

    # embed jd skills and candidate skill names
    jd_emb = semantic_match.embed_texts(model, jd_skills, batch_size=64)
    cand_emb = semantic_match.embed_texts(model, skill_names, batch_size=64)

    # similarity matrix (jd_skills x cand_skills)
    sims = jd_emb.dot(cand_emb.T)
    # metadata vectors
    endorsements = np.array([s.get("endorsements", 0) for s in skills], dtype=float)
    max_end = float(max(1.0, endorsements.max()))
    endorsements_norm = np.log1p(endorsements) / math.log1p(max_end)
    profs = np.array([PROFICIENCY_WEIGHT.get(s.get("proficiency", "beginner"), 0.5) for s in skills], dtype=float)
    durations = np.array([s.get("duration_months", 0) for s in skills], dtype=float)
    max_dur = float(max(1.0, durations.max()))
    durations_norm = durations / max_dur

    meta_score = 0.6 * profs + 0.2 * endorsements_norm + 0.2 * durations_norm

    # For each jd skill, take best candidate skill match weighted by meta_score
    best_per_jd = sims * meta_score[np.newaxis, :]
    best_vals = best_per_jd.max(axis=1)
    # average over jd skills
    final = float(np.mean(best_vals))
    return final


def build_features(
    candidates: List[Dict],
    jd_parsed: Dict,
    model_name: str = "all-MiniLM-L6-v2",
    cache_dir: Optional[Path] = None,
) -> pd.DataFrame:
    """Build a feature table for candidates given a parsed JD.

    jd_parsed should contain keys: `required_skills` (list), `preferred_skills` (list),
    `min_experience_years` (number), `titles` (list), `industries` (list).
    """
    if cache_dir is None:
        cache_dir = Path(".cache/embeddings")

    # prepare model
    model = semantic_match.load_model(model_name)

    # ensure embeddings exist for titles and other fields if needed (semantic_match handles caching)
    candidate_embeddings = semantic_match.build_candidate_embeddings(candidates, model_name=model_name, cache_dir=cache_dir)

    rows = []
    jd_skills = jd_parsed.get("required_skills", []) + jd_parsed.get("preferred_skills", [])
    jd_titles = jd_parsed.get("titles", [])
    jd_industries = jd_parsed.get("industries", [])
    min_exp = jd_parsed.get("min_experience_years")

    for cand in candidates:
        cid = cand.get("candidate_id")
        profile = cand.get("profile", {})
        redrob = cand.get("redrob_signals", {}) or {}

        skill_match = compute_skill_match_score(cand, jd_skills, model=model)
        experience = compute_experience_match(profile, min_exp)
        title_match = compute_title_match(cand, jd_titles, model=model)
        industry = compute_industry_match(profile.get("current_industry", ""), jd_industries, model=model)
        education = compute_education_score(cand.get("education", []))
        github = compute_github_score(redrob)
        assessment = compute_assessment_score(redrob, jd_skills)

        rows.append(
            {
                "candidate_id": cid,
                "skill_match": float(skill_match),
                "experience_match": float(experience),
                "title_match": float(title_match),
                "industry_match": float(industry),
                "education_score": float(education),
                "github_score": float(github),
                "assessment_score": float(assessment),
            }
        )

    df = pd.DataFrame(rows)
    # fill missing numeric values with 0
    df = df.fillna(0.0)
    return df


__all__ = [
    "build_features",
    "compute_skill_match_score",
    "compute_experience_match",
    "compute_title_match",
    "compute_industry_match",
    "compute_education_score",
    "compute_github_score",
    "compute_assessment_score",
]
AI_SKILLS = {
    "Embeddings",
    "Vector Search",
    "Information Retrieval",
    "LLMs",
    "LangChain",
    "Pinecone",
    "FAISS",
    "RAG",
    "Fine-tuning LLMs",
    "Sentence Transformers",
    "Hugging Face Transformers"
}

RETRIEVAL_SKILLS = {
    "Embeddings",
    "Vector Search",
    "Information Retrieval",
    "Pinecone",
    "FAISS",
    "RAG",
    "Sentence Transformers"
}


def extract_features(candidate):

    profile = candidate["profile"]
    signals = candidate["redrob_signals"]

    skills = {
        s["name"]
        for s in candidate["skills"]
    }

    ai_count = len(
        skills.intersection(AI_SKILLS)
    )

    retrieval_count = len(
        skills.intersection(RETRIEVAL_SKILLS)
    )

    job_count = len(
        candidate["career_history"]
    )

    years = profile["years_of_experience"]

    durations = [
        s.get("duration_months", 0)
        for s in candidate["skills"]
    ]

    assessments = signals[
        "skill_assessment_scores"
    ]

    avg_assessment = (
        sum(assessments.values()) /
        len(assessments)
        if assessments
        else 0
    )

    return {

        "years_experience": years,

        "ai_skill_count": ai_count,

        "retrieval_skill_count":
        retrieval_count,

        "github_score":
        max(
            0,
            signals[
                "github_activity_score"
            ]
        ),

        "response_rate":
        signals[
            "recruiter_response_rate"
        ],

        "profile_completeness":
        signals[
            "profile_completeness_score"
        ],

        "notice_period":
        signals[
            "notice_period_days"
        ],

        "saved_by_recruiters":
        signals[
            "saved_by_recruiters_30d"
        ],

        "interview_completion":
        signals[
            "interview_completion_rate"
        ],

        "avg_assessment":
        avg_assessment,

        "avg_skill_duration":
        (
            sum(durations)
            / len(durations)
            if durations
            else 0
        ),

        "stability":
        (
            years / job_count
            if job_count
            else 0
        ),

        "open_to_work":
        int(
            signals[
                "open_to_work_flag"
            ]
        )
    }
    