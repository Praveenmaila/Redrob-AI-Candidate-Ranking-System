from pathlib import Path
import sys

src = Path('data/candidates.jsonl')
out = Path('data/candidates_small.jsonl')
count = int(sys.argv[1]) if len(sys.argv) > 1 else 500
with src.open('r', encoding='utf-8') as f_in, out.open('w', encoding='utf-8') as f_out:
    for i, line in enumerate(f_in):
        if i >= count:
            break
        f_out.write(line)
print(f'Wrote {min(count, i+1)} lines to {out}')
