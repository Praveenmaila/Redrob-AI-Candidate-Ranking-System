import sys
from pathlib import Path
import json

# Ensure project root on sys.path
root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from src.load_data import load_candidates
from src.ranker import rank_candidates

candidates = load_candidates('data/candidates_small.jsonl', validate=False)
jd = Path('data/sample_jd.txt').read_text(encoding='utf-8')
rows = rank_candidates(candidates, top_k=10, jd_text=jd, semantic_weight=0.5, semantic_model='all-MiniLM-L6-v2', semantic_cache_dir='.cache/embeddings', prefilter_k=100)
print(json.dumps(rows, indent=2))
