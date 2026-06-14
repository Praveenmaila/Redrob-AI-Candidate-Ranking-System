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

def passes_filter(candidate):

    skills = {
        s["name"]
        for s in candidate["skills"]
    }

    years = candidate["profile"]["years_of_experience"]

    ai_count = len(
        skills.intersection(AI_SKILLS)
    )

    return (
        ai_count >= 2
        and years >= 3
    )


if __name__ == "__main__":

    from load_data import load_candidates

    candidates = load_candidates(
        "data/candidates.jsonl"
    )

    filtered = [
        c for c in candidates
        if passes_filter(c)
    ]

    print(
        f"Filtered candidates: {len(filtered)}"
    )
