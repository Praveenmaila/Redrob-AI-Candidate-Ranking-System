from load_data import load_candidates
from filter_candidates import passes_filter
from ranker import candidate_score

candidates = load_candidates(
    "data/candidates.jsonl"
)

filtered = [
    c for c in candidates
    if passes_filter(c)
]

scores = []

for c in filtered:

    scores.append(
        (
            c["candidate_id"],
            candidate_score(c)
        )
    )

scores.sort(
    key=lambda x: x[1],
    reverse=True
)

for row in scores[:20]:
    print(row)