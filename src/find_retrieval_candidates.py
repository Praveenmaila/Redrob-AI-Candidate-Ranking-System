from load_data import load_candidates

RETRIEVAL_SKILLS = {
    "Embeddings",
    "Vector Search",
    "Information Retrieval",
    "Pinecone",
    "FAISS",
    "RAG",
    "Sentence Transformers"
}

candidates = load_candidates("data/candidates.jsonl")

count = 0

for c in candidates:
    skills = {s["name"] for s in c["skills"]}

    if len(skills.intersection(RETRIEVAL_SKILLS)) >= 2:
        count += 1

print("Candidates with 2+ retrieval skills:", count)