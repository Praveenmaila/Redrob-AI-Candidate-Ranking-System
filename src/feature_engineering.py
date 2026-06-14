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
    