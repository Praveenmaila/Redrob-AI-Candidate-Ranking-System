import importlib

modules = [
    'numpy', 'pandas', 'sklearn', 'torch', 'sentence_transformers', 'yaml', 'psutil'
]

for m in modules:
    try:
        mod = importlib.import_module(m)
        ver = getattr(mod, '__version__', None)
        print(f"{m}: {ver}")
    except Exception as e:
        print(f"ERR {m}: {e}")
