from load_data import iter_candidates
from feature_engineering import extract_features

it = iter_candidates("data/candidates.jsonl")
try:
    _, first = next(it)
    sample = extract_features(first)
    print(sample)
except StopIteration:
    print("No candidates found")