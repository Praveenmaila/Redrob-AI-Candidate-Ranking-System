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
    STATE["last_stdout"] = ""
    STATE["last_stderr"] = ""
    cmd = [sys.executable, str(Path("scripts/generate_submission.py")), "--candidates", str(candidates_path), "--jd", str(jd_path), "--out", str(out_path)]
    if extra_args:
        cmd.extend(extra_args)
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        STATE["pid"] = proc.pid

        # read stdout/stderr lines and update STATE so frontend can poll progress
        def stream_reader(pipe, key, prefix=""):
            try:
                for line in iter(pipe.readline, ""):
                    if not line:
                        break
                    line = line.rstrip("\n")
                    # append to last_stdout/last_stderr (keep last ~2000 chars)
                    prev = STATE.get(key, "")
                    prev = (prev + "\n" + line)[-2000:]
                    STATE[key] = prev
                    STATE["progressMessage"] = prefix + line
            finally:
                try:
                    pipe.close()
                except Exception:
                    pass

        threads = []
        if proc.stdout:
            t = threading.Thread(target=stream_reader, args=(proc.stdout, "last_stdout", "") , daemon=True)
            t.start()
            threads.append(t)
        if proc.stderr:
            t2 = threading.Thread(target=stream_reader, args=(proc.stderr, "last_stderr", "ERR: "), daemon=True)
            t2.start()
            threads.append(t2)

        ret = proc.wait()
        # wait briefly for readers to finish
        for t in threads:
            t.join(timeout=0.5)

        STATE["progressMessage"] = f"Finished: returncode={ret}"
        STATE["status"] = "done" if ret == 0 else "error"
    except Exception as e:
        STATE["status"] = "error"
        STATE["progressMessage"] = f"Exception: {e}"
        STATE["last_stderr"] = STATE.get("last_stderr", "") + f"\nException: {e}"


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
    # return recent logs (truncated) to help debugging
    return JSONResponse({
        "status": STATE.get("status", "unknown"),
        "progressMessage": STATE.get("progressMessage", ""),
        "pid": STATE.get("pid"),
        "last_stdout_tail": STATE.get("last_stdout", "")[-2000:],
        "last_stderr_tail": STATE.get("last_stderr", "")[-2000:],
    })


@app.get("/download")
def download():
    path = Path("submission_top100.csv")
    if path.exists():
        return FileResponse(path, media_type="text/csv", filename=path.name)
    return JSONResponse({"error": "not found"}, status_code=404)
