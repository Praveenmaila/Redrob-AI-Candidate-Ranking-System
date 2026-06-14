from load_data import load_candidates
import json

candidates = load_candidates(
    "data/candidates.jsonl"
)

candidate = candidates[0]

print(json.dumps(
    candidate,
    indent=2
)[:10000])
