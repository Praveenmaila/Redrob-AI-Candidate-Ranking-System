from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from datetime import datetime, timezone
import csv
import sys

# Runtime check: ensure `python-multipart` is importable from the same Python
# interpreter used to start the server. FastAPI raises a RuntimeError during
# route analysis if multipart isn't installed; provide a clearer message.
app = FastAPI()

@app.get("/")
async def root():
    return {
        "status": "OK",
        "service": "Redrob AI Candidate Ranking API",
        "endpoint": "/rank",
        "docs": "/docs"
    }
@app.get("/health")
async def health():
    return {"status": "healthy"}
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

PROJECT_ROOT = Path(__file__).resolve().parent
DATASET_UPLOAD_DIR = PROJECT_ROOT / "data" / "uploads"
UPLOAD_CHUNK_SIZE = 1024 * 1024



# Concurrency guard: at most one ranking subprocess at a time. Avoids
# multiple concurrent runs competing for RAM and overwriting STATE.
_RANKING_LOCK = threading.Lock()
_ERROR_MARKERS = (
    "Traceback",
    "ERROR",
    "CRITICAL",
    "FATAL",
    "UnicodeDecodeError",
    "NameError",
    "ValueError",
    "TypeError",
    "KeyError",
    "AttributeError",
    "ImportError",
    "RuntimeError",
    "OSError",
    "IOError",
    "FileNotFoundError",
    "ZeroDivisionError",
    "StopIteration",
    "AssertionError",
)


def _is_error_line(line: str) -> bool:
    return any(m in line for m in _ERROR_MARKERS) or line.startswith("ERR:")


@app.on_event("startup")
async def _startup_banner():
    import logging as _logging
    _logging.basicConfig(level=_logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    _logging.info("Redrob backend API ready on port 8000 (CORS: allow_origins=*)")

# allow CORS from local dev frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import re as _re

STATE = {
    "status": "ready",
    "progressMessage": "idle",
    "pid": None,
    "stage": "idle",
    "stageLabel": "Idle",
    "progressPct": 0,
    "candidatesProcessed": 0,
    "error": None,
    "errorDetails": None,
    "traceback": "",
    "last_stdout": "",
    "last_stderr": "",
    # Internal: rolling buffers used by parse_subprocess_line to reassemble
    # multi-line Python tracebacks across separate stderr lines.
    "_traceback_buf": "",
    "_last_lines": [],  # ring buffer of the last 100 raw lines for context
}

# Ordered, user-visible stage definitions. Keys are stable identifiers the
# frontend uses to render badges; labels are the human-friendly copy shown
# to end users. Pct is the progress percentage the UI should display while
# the stage is active.
STAGES = {
    "idle": {"label": "Idle", "pct": 0},
    "loading_model": {"label": "Loading AI Model", "pct": 5},
    "loading_dataset": {"label": "Loading Candidate Dataset", "pct": 25},
    "building_embeddings": {"label": "Building Candidate Embeddings", "pct": 55},
    "processing_jd": {"label": "Processing Job Description", "pct": 70},
    "semantic_matching": {"label": "Semantic Matching", "pct": 82},
    "ranking": {"label": "Ranking Candidates", "pct": 90},
    "exporting_results": {"label": "Exporting Results", "pct": 96},
    "completed": {"label": "Completed", "pct": 100},
    "error": {"label": "Error", "pct": 0},
}

# Map substrings found in the ranking subprocess output to a stage key.
# Order matters: more specific patterns first.
STAGE_PATTERNS = (
    # Loading model
    ("Loading SentenceTransformer", "loading_model"),
    ("Loading embedding model", "loading_model"),
    ("Loading model", "loading_model"),
    # Loading dataset
    ("Streaming prefilter complete", "loading_dataset"),
    ("Loaded", "loading_dataset"),
    ("Reading candidates", "loading_dataset"),
    ("Loading candidate dataset", "loading_dataset"),
    # Building embeddings
    ("Embedding field", "building_embeddings"),
    ("Building embeddings", "building_embeddings"),
    ("embedding", "building_embeddings"),
    # Processing JD
    ("Processing job description", "processing_jd"),
    ("Reading JD", "processing_jd"),
    # Semantic matching
    ("Semantic matching", "semantic_matching"),
    ("semantic match", "semantic_matching"),
    ("score_against_jd", "semantic_matching"),
    ("Semantic scores computed", "semantic_matching"),
    # Ranking
    ("Ranking candidates", "ranking"),
    ("Streaming prefilter", "ranking"),
    ("Combining scores", "ranking"),
    # Exporting
    ("Wrote", "exporting_results"),
    ("Writing results", "exporting_results"),
    ("Writing submission", "exporting_results"),
    # Completion
    ("Finished: returncode=0", "completed"),
)

# Patterns that indicate a real user-facing failure. Matched against any
# single line from the subprocess so we can replace stack traces with
# friendly copy. Ordered most-specific first.
ERROR_PATTERNS = (
    # --- Loading dataset / file errors
    (("UnicodeDecodeError",), "Failed to load candidate dataset"),
    (("JSONDecodeError",), "Failed to load candidate dataset"),
    (("Expecting value",), "Failed to load candidate dataset"),
    (("FileNotFoundError",), "Failed to load candidate dataset"),
    (("IsADirectoryError",), "Failed to load candidate dataset"),
    (("PermissionError",), "Failed to load candidate dataset"),
    (("OSError",), "Failed to load candidate dataset"),
    (("IOError",), "Failed to load candidate dataset"),
    (("ValueError", "schema"), "Failed to load candidate dataset"),
    (("ValueError", "json"), "Failed to load candidate dataset"),
    # --- Embedding / model errors
    (("ImportError",), "Embedding generation failed"),
    (("ModuleNotFoundError",), "Embedding generation failed"),
    (("ValueError", "embedding"), "Embedding generation failed"),
    (("ValueError", "shape"), "Embedding generation failed"),
    (("ValueError", "dimension"), "Embedding dimension mismatch"),
    (("RuntimeError", "CUDA"), "Embedding generation failed"),
    (("RuntimeError", "out of memory"), "Embedding generation failed"),
    (("MemoryError",), "Embedding generation failed"),
    (("HF_HUB_OFFLINE",), "Embedding generation failed"),
    (("HuggingFace",), "Embedding generation failed"),
    # --- Ranking / generic
    (("NameError",), "Ranking process interrupted"),
    (("AttributeError",), "Ranking process interrupted"),
    (("TypeError",), "Ranking process interrupted"),
    (("IndexError",), "Ranking process interrupted"),
    (("KeyError",), "Ranking process interrupted"),
    (("AssertionError",), "Ranking process interrupted"),
    (("RuntimeError",), "Ranking process interrupted"),
    (("ZeroDivisionError",), "Ranking process interrupted"),
    (("returncode=1",), "Ranking process interrupted"),
    (("Traceback",), "Ranking process interrupted"),
    (("KeyboardInterrupt",), "Ranking process interrupted"),
)

# Regex for extracting the exception type and message from a line that
# ends a Python traceback. Example match: ValueError, "shapes (2000,513)
# and (1,384) not aligned".
_EXCEPTION_RE = _re.compile(
    r"^([A-Z][A-Za-z]*(?:Error|Warning|Exception|Interrupt|MemoryError))\s*:?\s*(.*)$"
)


def _set_stage(stage_key: str, *, candidates: int | None = None, force_pct: int | None = None) -> None:
    info = STAGES.get(stage_key, STAGES["idle"])
    STATE["stage"] = stage_key
    STATE["stageLabel"] = info["label"]
    STATE["progressPct"] = max(STATE.get("progressPct", 0), int(force_pct if force_pct is not None else info["pct"]))
    if candidates is not None:
        STATE["candidatesProcessed"] = max(STATE.get("candidatesProcessed", 0), int(candidates))
    STATE["progressMessage"] = info["label"]


def _set_error(message: str, details: str | None = None, *, stage: str | None = None) -> None:
    info = STAGES["error"]
    STATE["status"] = "error"
    STATE["stage"] = stage or STATE.get("stage", "error")
    STATE["stageLabel"] = info["label"]
    STATE["error"] = message
    STATE["errorDetails"] = details or STATE.get("errorDetails")
    STATE["progressMessage"] = message
    # Promote the rolling traceback buffer to the persistent field.
    tb = STATE.pop("_traceback_buf", "")
    if tb:
        STATE["traceback"] = tb[-4000:]


def parse_subprocess_line(line: str) -> None:
    """Inspect a single line of subprocess output and update structured state.

    Raw output is still captured in last_stdout / last_stderr for backend
    logs; this function only mutates the user-facing fields. A single line
    can advance at most one stage.
    """
    if not line:
        return

    # Maintain a rolling 100-line ring buffer for context, regardless of
    # whether the line looks interesting.
    buf = STATE.get("_last_lines", [])
    buf.append(line)
    STATE["_last_lines"] = buf[-100:]

    # ---- Multi-line traceback assembly -------------------------------------
    # A Python traceback looks like:
    #   Traceback (most recent call last):
    #     File "...", line N, in <func>
    #       <snippet>
    #   <ExceptionType>: <message>
    # We reassemble it as a single block so the frontend can show the
    # full failure location.
    tb_buf = STATE.get("_traceback_buf", "")
    if line.startswith("Traceback (most recent call last):"):
        STATE["_traceback_buf"] = line + "\n"
        return
    if tb_buf:
        # Continuation of a traceback: indented File line, snippet, or the
        # final exception line. Blank line ends the traceback.
        if line.startswith("  ") or line.strip() == "" and STATE.get("_traceback_buf", "").rstrip().endswith(")"):
            STATE["_traceback_buf"] = tb_buf + line + "\n"
            if line.strip() == "":
                STATE["traceback"] = tb_buf[-4000:]
                STATE["_traceback_buf"] = ""
            return
        if not line.startswith(" "):
            # Final exception line (e.g. "ValueError: shapes ... not aligned")
            STATE["_traceback_buf"] = tb_buf + line + "\n"
            STATE["traceback"] = STATE["_traceback_buf"][-4000:]
            STATE["_traceback_buf"] = ""
            # Extract exception type and details for structured error.
            m = _EXCEPTION_RE.match(line.strip())
            if m:
                exc_type, exc_msg = m.group(1), m.group(2).strip()
                # Try to find a friendly label for this exception type.
                friendly, stage_for_error = _lookup_error(exc_type, exc_msg, line)
                if friendly:
                    # Pull the most recent File/line info for errorDetails.
                    details = exc_msg or _extract_file_from_traceback(STATE["traceback"])
                    _set_error(friendly, details, stage=stage_for_error or STATE.get("stage"))
                    return
        return

    # ---- Single-line error detection --------------------------------------
    for markers, friendly in ERROR_PATTERNS:
        if all(m in line for m in markers):
            details = _extract_file_from_traceback(
                STATE.get("traceback", "") + "\n" + line
            ) or line
            _set_error(friendly, details, stage=_stage_for_error(markers))
            return

    # ---- Stage progression -------------------------------------------------
    for needle, stage_key in STAGE_PATTERNS:
        if needle in line:
            count = _extract_count(line)
            _set_stage(stage_key, candidates=count)
            return


def _stage_for_error(markers) -> str:
    """Map an error marker set to the most likely current stage."""
    joined = " ".join(markers).lower()
    if "schema" in joined or "json" in joined or "decode" in joined or "filenotfound" in joined or "oserror" in joined:
        return "loading_dataset"
    if "import" in joined or "module" in joined or "embedding" in joined or "memory" in joined or "huggingface" in joined:
        return "building_embeddings"
    if "dimension" in joined or "shape" in joined or "valueerror" in joined:
        return "building_embeddings"
    return STATE.get("stage", "error")


def _lookup_error(exc_type: str, exc_msg: str, full_line: str):
    """Resolve (exc_type, exc_msg) to (friendly, stage) using ERROR_PATTERNS."""
    for markers, friendly in ERROR_PATTERNS:
        if any(m == exc_type for m in markers) or any(m in full_line for m in markers):
            return friendly, _stage_for_error(markers)
    return None, None


def _extract_file_from_traceback(tb: str) -> str | None:
    """Pull the deepest `File "...", line N` reference from a traceback string."""
    matches = _re.findall(r'File \"([^\"]+)\", line (\d+)', tb)
    if not matches:
        return None
    path, lineno = matches[-1]
    return f"{path}:{lineno}"


def _extract_count(line: str) -> int | None:
    import re
    patterns = (
        r"total_seen\s*=\s*(\d+)",
        r"for\s+(\d+)\s+candidates",
        r"Loaded\s+(\d+)",
        r"Wrote\s+(\d+)",
        r"(\d+)\s+rows",
    )
    for pat in patterns:
        m = re.search(pat, line)
        if m:
            try:
                return int(m.group(1))
            except (ValueError, IndexError):
                return None
    return None


def _format_file_size(size_bytes: int) -> str:
    units = ("B", "KB", "MB", "GB")
    size = float(size_bytes)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{size_bytes} B"


def _safe_dataset_path(dataset_name: str) -> Path:
    if not dataset_name:
        raise HTTPException(status_code=400, detail="Dataset is required")
    if "/" in dataset_name or "\\" in dataset_name:
        raise HTTPException(status_code=400, detail="Invalid dataset name")
    if Path(dataset_name).name != dataset_name:
        raise HTTPException(status_code=400, detail="Invalid dataset name")

    path = (DATASET_UPLOAD_DIR / dataset_name).resolve()
    upload_root = DATASET_UPLOAD_DIR.resolve()
    if path.parent != upload_root:
        raise HTTPException(status_code=400, detail="Invalid dataset path")
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Dataset not found")
    return path


async def _save_upload_file(upload: UploadFile, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = destination.with_suffix(destination.suffix + ".part")
    try:
        with tmp_path.open("wb") as out_file:
            while True:
                chunk = await upload.read(UPLOAD_CHUNK_SIZE)
                if not chunk:
                    break
                out_file.write(chunk)
        tmp_path.replace(destination)
    finally:
        await upload.close()
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


def _dataset_info(path: Path) -> dict:
    stat = path.stat()
    return {
        "name": path.name,
        "size": _format_file_size(stat.st_size),
        "uploaded_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
    }


def run_ranking(candidates_path: Path, jd_path: Path, out_path: Path, extra_args=None):
    STATE["status"] = "running"
    STATE["progressMessage"] = "Starting ranking script"
    STATE["error"] = None
    STATE["errorDetails"] = None
    STATE["traceback"] = ""
    STATE["_traceback_buf"] = ""
    STATE["last_lines"] = []
    STATE["last_stdout"] = ""
    STATE["last_stderr"] = ""
    cmd = [sys.executable, str(PROJECT_ROOT / "scripts" / "generate_submission.py"), "--candidates", str(candidates_path), "--jd", str(jd_path), "--out", str(out_path)]
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
                    # 1) Always keep raw logs in last_stdout / last_stderr for
                    #    the backend console and log file (last 2000 chars).
                    prev = STATE.get(key, "")
                    prev = (prev + "\n" + line)[-2000:]
                    STATE[key] = prev
                    # 2) Convert the line into a structured progress event
                    #    instead of forwarding the raw string to the UI.
                    parse_subprocess_line(prefix + line)
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

        if ret != 0:
            # Promote whatever the parser assembled (traceback + details)
            # to the user-facing error fields. If the parser didn't fire
            # (e.g. subprocess killed by signal), use the stderr tail.
            if not STATE.get("error"):
                tb = STATE.get("traceback", "") or STATE.get("last_stderr", "")
                details = _extract_file_from_traceback(tb) or tb.strip().splitlines()[-1] if tb.strip() else None
                _set_error("Ranking process interrupted", details)
            STATE["status"] = "error"
        else:
            _set_stage("completed", force_pct=100)
            STATE["status"] = "done"
    except Exception as e:
        import traceback as _tb
        tb_text = _tb.format_exc()
        STATE["last_stderr"] = (STATE.get("last_stderr", "") + f"\n{tb_text}")[-2000:]
        _set_error("Ranking process interrupted", _extract_file_from_traceback(tb_text) or str(e))


@app.post("/datasets/upload")
async def upload_dataset(file: UploadFile = File(...)):
    filename = Path(file.filename or "").name
    if not filename:
        raise HTTPException(status_code=400, detail="Dataset filename is required")
    if "/" in (file.filename or "") or "\\" in (file.filename or ""):
        raise HTTPException(status_code=400, detail="Invalid dataset filename")
    if Path(file.filename or "").name != file.filename:
        raise HTTPException(status_code=400, detail="Invalid dataset filename")
    if Path(filename).suffix.lower() not in {".jsonl", ".json", ".csv"}:
        raise HTTPException(status_code=400, detail="Dataset must be .jsonl, .json, or .csv")

    destination = DATASET_UPLOAD_DIR / filename
    await _save_upload_file(file, destination)
    return JSONResponse(_dataset_info(destination))


@app.get("/datasets")
def list_datasets():
    DATASET_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    files = [
        _dataset_info(path)
        for path in DATASET_UPLOAD_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in {".jsonl", ".json", ".csv"}
    ]
    files.sort(key=lambda item: item["uploaded_at"], reverse=True)
    return JSONResponse(files)


@app.post("/rank")
async def rank(jd: UploadFile = File(...), dataset: str = Form(...)):
    timestamp = int(time.time())
    uploads = Path(".uploads")
    uploads.mkdir(exist_ok=True)
    jd_path = uploads / f"jd_{timestamp}.txt"
    cand_path = _safe_dataset_path(dataset)
    out_path = Path("submission_top100.csv")

    await _save_upload_file(jd, jd_path)

    # launch background thread
    t = threading.Thread(target=run_ranking, args=(cand_path, jd_path, out_path), daemon=True)
    t.start()
    STATE["status"] = "running"
    _set_stage("loading_model")
    return JSONResponse({
        "status": "started",
        "stage": STATE["stage"],
        "stageLabel": STATE["stageLabel"],
        "progressPct": STATE["progressPct"],
        "candidatesProcessed": STATE["candidatesProcessed"],
        "progressMessage": STATE["stageLabel"],
    })


@app.get("/health")
def health():
    return JSONResponse({
        "status": STATE.get("status", "unknown"),
        "stage": STATE.get("stage", "idle"),
        "stageLabel": STATE.get("stageLabel", "Idle"),
        "progressPct": int(STATE.get("progressPct", 0)),
        "candidatesProcessed": int(STATE.get("candidatesProcessed", 0)),
        "error": STATE.get("error"),
        "errorDetails": STATE.get("errorDetails"),
        "traceback": STATE.get("traceback", ""),
        "progressMessage": STATE.get("stageLabel") or STATE.get("progressMessage", ""),
        "pid": STATE.get("pid"),
    })


@app.get("/download")
def download():
    path = Path("submission_top100.csv")
    if path.exists():
        return FileResponse(
            path,
            media_type="text/csv",
            filename="submission_top100.csv",
            headers={
                "Content-Disposition": 'attachment; filename="submission_top100.csv"'
            },
        )
    return JSONResponse({"error": "not found"}, status_code=404)


def _parse_reasoning_text(text: str) -> dict:
    """Parse a reasoning string like 'Title with X yrs; Strengths: a, b; Concerns: c.'
    into structured components."""
    import re as _re_local
    title = "Candidate"
    years = 0.0
    strengths = []
    concerns = []

    # Extract title and years
    m = _re_local.match(r'^(.+?)\s+with\s+([\d.]+)\s+yrs', text)
    if m:
        title = m.group(1).strip()
        try:
            years = float(m.group(2))
        except Exception:
            pass

    # Extract strengths
    sm = _re_local.search(r'Strengths:\s*(.+?)(?:;|Concerns:|\.$)', text)
    if sm:
        strengths = [s.strip() for s in sm.group(1).split(',') if s.strip()]

    # Extract concerns
    cm = _re_local.search(r'Concerns:\s*(.+?)(?:\.$|$)', text)
    if cm:
        concerns = [c.strip().rstrip('.') for c in cm.group(1).split(',') if c.strip()]

    # Approximate score breakdowns
    experience_match_pct = int(round(min(100.0, (years / 20.0) * 100.0)))

    ai_count = 0
    am = _re_local.search(r'(\d+)\s+AI\s+skills', text)
    if am:
        ai_count = int(am.group(1))
    assessment = 0.0
    asm = _re_local.search(r'assessments\s*\((\d+)\)', text)
    if asm:
        assessment = float(asm.group(1))
    skill_raw = min(1.0, ai_count / 5.0) * 0.6 + min(1.0, assessment / 100.0) * 0.4
    skill_match_pct = int(round(skill_raw * 100.0))

    return {
        "title": title,
        "years_experience": round(years, 1),
        "strengths": strengths,
        "concerns": concerns,
        "skill_match_pct": max(0, min(100, skill_match_pct)),
        "experience_match_pct": max(0, min(100, experience_match_pct)),
    }


@app.get("/results")
def results():
    """Return structured JSON for the ranked candidates."""
    path = Path("submission_top100.csv")
    if not path.exists():
        return JSONResponse({"error": "No results available yet. Run ranking first."}, status_code=404)

    candidates = []
    scores = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                score_val = float(row.get("score", 0))
                scores.append(score_val)
                reasoning_text = row.get("reasoning", "")
                parsed = _parse_reasoning_text(reasoning_text)

                # Approximate semantic match from score
                semantic_match_pct = int(round(min(100.0, score_val * 100.0 * 0.7)))

                candidates.append({
                    "candidate_id": row.get("candidate_id", ""),
                    "rank": int(row.get("rank", 0)),
                    "score": round(score_val, 4),
                    "semantic_match_pct": max(0, min(100, semantic_match_pct)),
                    "skill_match_pct": parsed["skill_match_pct"],
                    "experience_match_pct": parsed["experience_match_pct"],
                    "key_strengths": parsed["strengths"],
                    "concerns": parsed["concerns"],
                    "title": parsed["title"],
                    "years_experience": parsed["years_experience"],
                    "reasoning": reasoning_text,
                })
    except Exception as exc:
        return JSONResponse({"error": f"Failed to parse results: {exc}"}, status_code=500)

    metadata = {
        "total_candidates": len(candidates),
        "avg_score": round(sum(scores) / len(scores), 4) if scores else 0,
        "max_score": round(max(scores), 4) if scores else 0,
        "min_score": round(min(scores), 4) if scores else 0,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    return JSONResponse({"candidates": candidates, "metadata": metadata})
