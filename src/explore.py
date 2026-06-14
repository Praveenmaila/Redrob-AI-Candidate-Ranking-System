from load_data import load_candidates
from collections import Counter

candidates = load_candidates("data/candidates.jsonl")

print(f"Total Candidates: {len(candidates)}")

first = candidates[0]

print("\nTop-level keys:")
print(first.keys())

print("\nProfile Keys:")
print(first["profile"].keys())

print("\nRedrob Signal Keys:")
print(first["redrob_signals"].keys())

skills_count = []

for c in candidates[:1000]:
    skills_count.append(len(c["skills"]))

print("\nAverage Skills (first 1000 candidates):")
print(sum(skills_count) / len(skills_count))