from feature_engineering import extract_features


def experience_score(years):

    if 5 <= years <= 9:
        return 100

    if 3 <= years < 5:
        return 80

    if 9 < years <= 12:
        return 70

    return 40


def notice_score(days):

    if days <= 30:
        return 100

    if days <= 60:
        return 80

    if days <= 90:
        return 50

    return 20


def candidate_score(candidate):

    f = extract_features(candidate)

    score = 0

    score += (
        f["ai_skill_count"] * 8
    )

    score += (
        f["retrieval_skill_count"] * 12
    )

    score += (
        experience_score(
            f["years_experience"]
        ) * 0.25
    )

    score += (
        f["github_score"] * 0.15
    )

    score += (
        f["response_rate"]
        * 100
        * 0.15
    )

    score += (
        f["interview_completion"]
        * 100
        * 0.10
    )

    score += (
        f["avg_assessment"]
        * 0.10
    )

    score += (
        notice_score(
            f["notice_period"]
        ) * 0.10
    )

    score += (
        f["saved_by_recruiters"]
        * 0.5
    )

    return round(score, 2)