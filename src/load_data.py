import json

def load_candidates(path):
    candidates = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            candidates.append(json.loads(line))

    return candidates


if __name__ == "__main__":
    candidates = load_candidates("data/candidates.jsonl")

    print(f"Loaded {len(candidates)} candidates")
    print("First Candidate:", candidates[0]["candidate_id"])