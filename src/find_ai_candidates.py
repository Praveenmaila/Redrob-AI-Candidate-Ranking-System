from load_data import load_candidates

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

candidates = load_candidates("data/candidates.jsonl")

count = 0

for c in candidates:
    skills = {s["name"] for s in c["skills"]}

    if len(skills.intersection(AI_SKILLS)) >= 3:
        count += 1

print("Candidates with 3+ AI skills:", count)
