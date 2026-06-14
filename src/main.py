from load_data import load_candidates
from feature_engineering import extract_features

candidates = load_candidates("data/candidates.jsonl")

sample = extract_features(candidates[0])

print(sample)