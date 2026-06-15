from fastapi import FastAPI, UploadFile, File, BackgroundTasks
import sys

# Runtime check: ensure `python-multipart` is importable from the same Python
# interpreter used to start the server. FastAPI raises a RuntimeError during
# route analysis if multipart isn't installed; provide a clearer message.
try:
    import multipart  # type: ignore
except Exception:
    raise RuntimeError(
        "Missing dependency 'python-multipart'.\n"
        "Install it into the Python environment you're using to run uvicorn.\n"
        "Example (with venv activated):\n"
        f"  {sys.executable} -m pip install python-multipart\n\n"
        "Then start the server with the same Python interpreter to ensure the\n"
        "reloader uses the correct environment:\n"
        f"  {sys.executable} -m uvicorn backend_api:app --reload --host 0.0.0.0 --port 8000\n"
    )
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path
import threading
import subprocess
import time
import os

app = FastAPI()

# allow CORS from local dev frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATE = {"status": "ready", "progressMessage": "idle", "pid": None}


def run_ranking(candidates_path: Path, jd_path: Path, out_path: Path, extra_args=None):
    STATE["status"] = "running"
    STATE["progressMessage"] = "Starting ranking script"
    cmd = ["python", str(Path("scripts/generate_submission.py")), "--candidates", str(candidates_path), "--jd", str(jd_path), "--out", str(out_path)]
    if extra_args:
        cmd.extend(extra_args)
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
        STATE["progressMessage"] = "Finished: returncode=%s" % proc.returncode
        STATE["status"] = "done" if proc.returncode == 0 else "error"
        # store last logs
        STATE["last_stdout"] = proc.stdout
        STATE["last_stderr"] = proc.stderr
    except Exception as e:
        STATE["status"] = "error"
        STATE["progressMessage"] = f"Exception: {e}"


@app.post("/rank")
async def rank(jd: UploadFile = File(...), candidates: UploadFile = File(...)):
    timestamp = int(time.time())
    uploads = Path(".uploads")
    uploads.mkdir(exist_ok=True)
    jd_path = uploads / f"jd_{timestamp}.txt"
    cand_path = uploads / f"candidates_{timestamp}.jsonl"
    out_path = Path("submission_top100.csv")

    # save files
    with jd_path.open("wb") as f:
        f.write(await jd.read())
    with cand_path.open("wb") as f:
        f.write(await candidates.read())

    # launch background thread
    t = threading.Thread(target=run_ranking, args=(cand_path, jd_path, out_path), daemon=True)
    t.start()
    STATE["status"] = "running"
    STATE["progressMessage"] = "Ranking started"
    return JSONResponse({"status": "started", "progressMessage": STATE["progressMessage"]})


@app.get("/health")
def health():
    return JSONResponse({"status": STATE.get("status", "unknown"), "progressMessage": STATE.get("progressMessage", "")})


@app.get("/download")
def download():
    path = Path("submission_top100.csv")
    if path.exists():
        return FileResponse(path, media_type="text/csv", filename=path.name)
    return JSONResponse({"error": "not found"}, status_code=404)
