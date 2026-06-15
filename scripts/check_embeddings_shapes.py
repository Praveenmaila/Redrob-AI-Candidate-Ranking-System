from pathlib import Path
import sys
root = Path(__file__).resolve().parents[1]
src_path = root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from load_data import load_candidates
import semantic_match

def main():
    candidates = load_candidates('data/candidates.jsonl', validate=False)
    print('Loaded candidates:', len(candidates))
    embs = semantic_match.build_candidate_embeddings(candidates, cache_dir=Path('.cache/embeddings'))
    model = semantic_match.load_model()
    jd_text = Path('data/sample_jd.txt').read_text(encoding='utf-8') if Path('data/sample_jd.txt').exists() else ''
    if semantic_match.HAS_ST:
        jd_emb = semantic_match._embed_text_single(model, jd_text)
        print('JD emb shape:', jd_emb.shape)
    else:
        print('HAS_ST False; JD emb not computed here')
    for f,d in embs.items():
        print(f'Field {f} emb shape: {d["embeddings"].shape}')

if __name__ == '__main__':
    main()
