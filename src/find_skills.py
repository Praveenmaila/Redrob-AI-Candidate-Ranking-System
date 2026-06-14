from load_data import load_candidates
from collections import Counter

candidates = load_candidates("data/candidates.jsonl")

counter = Counter()

for c in candidates:
    for skill in c["skills"]:
        counter[skill["name"]] += 1

with open("output/skills_frequency.txt", "w", encoding="utf-8") as f:
    for skill, count in counter.most_common():
        f.write(f"{skill}: {count}\n")

print("Saved to output/skills_frequency.txt")