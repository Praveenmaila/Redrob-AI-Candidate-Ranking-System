import json
from pathlib import Path
p=Path('.cache/embeddings')
for f in sorted(p.glob('*.meta.json')):
    try:
        data=json.loads(f.read_text(encoding='utf-8'))
        print(f.name, list(data.keys()))
        if 'vocabulary' in data:
            try:
                print('vocab_len=', len(data['vocabulary']))
            except Exception:
                print('vocab present but non-serializable')
    except Exception as e:
        print('ERR', f.name, e)
