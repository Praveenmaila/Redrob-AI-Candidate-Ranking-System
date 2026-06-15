# redrob-ai-candidate-ranking

## Running the dev API (for the frontend)

The project includes a minimal FastAPI dev server `backend_api.py` that exposes `/rank`, `/health`, and `/download` to help local frontend development.

1. Activate your virtualenv (if you use one):

```powershell
# from repo root on Windows PowerShell (example)
& ".venv/Scripts/Activate.ps1"
```

2. Install dependencies (ensure `python-multipart` is installed in the same interpreter):

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

3. Start the API server using the same Python interpreter so the reloader uses the same environment:

```powershell
python -m uvicorn backend_api:app --reload --host 0.0.0.0 --port 8000
```

If you see an error about `python-multipart`, run the install command above and make sure you started `uvicorn` with the same `python` (the README examples above explicitly use `python -m uvicorn` to avoid accidental global `uvicorn` executables).
