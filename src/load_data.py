"""Data loading and validation utilities for Redrob Ranking System.

This module provides robust, reproducible, and CPU-only friendly
functions to stream-load candidate JSONL files, validate them against
a JSON Schema, and persist filtered subsets. It intentionally avoids
network calls and heavy side-effects so it is safe to run during the
competition ranking pipeline.

Public functions:
- `load_schema(schema_path)` -> dict
- `iter_candidates(file_path)` -> Iterator[dict]
- `validate_candidate(candidate, schema)` -> List[str]
- `load_candidates(...)` -> List[dict]
- `save_jsonl(candidates, out_path)` -> None
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple

import jsonschema

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def load_schema(schema_path: Path | str) -> Dict:
    """Load a JSON schema from `schema_path`.

    Args:
        schema_path: Path to JSON schema file.

    Returns:
        Parsed JSON schema as a dict.
    """
    p = Path(schema_path)
    if not p.exists():
        raise FileNotFoundError(f"Schema file not found: {p}")
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def iter_candidates(file_path: Path | str) -> Iterator[Tuple[int, Dict]]:
    """Yield (line_number, candidate_dict) from a JSONL file.

    This is memory efficient and validates that each line is valid JSON.
    """
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(f"Candidates file not found: {p}")
    with p.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                candidate = json.loads(line)
            except json.JSONDecodeError as exc:
                logger.warning("Skipping invalid JSON at %s:%d -> %s", p, i, exc)
                continue
            yield i, candidate


def validate_candidate(candidate: Dict, schema: Dict) -> List[str]:
    """Validate a single candidate dict against the provided JSON Schema.

    Returns a list of human-readable error messages (empty if valid).
    """
    validator = jsonschema.Draft7Validator(schema)
    errors = []
    for err in validator.iter_errors(candidate):
        # Build a short, stable message
        path = ".".join([str(p) for p in err.path]) or "<root>"
        errors.append(f"{path}: {err.message}")
    return errors


def load_candidates(
    file_path: Path | str,
    schema_path: Optional[Path | str] = None,
    validate: bool = True,
    max_records: Optional[int] = None,
    skip_invalid: bool = True,
) -> List[Dict]:
    """Load candidates from a JSONL file with optional schema validation.

    Args:
        file_path: Path to candidates JSONL.
        schema_path: Optional path to JSON Schema used for validation.
        validate: If True and `schema_path` provided, validate each record.
        max_records: If set, stop after this many valid records.
        skip_invalid: If True, skip invalid records; otherwise raise on first invalid.

    Returns:
        List of validated candidate dicts (or raw dicts if validation disabled).
    """
    schema = None
    if validate and schema_path is not None:
        schema = load_schema(schema_path)

    results: List[Dict] = []
    total = 0
    invalid = 0

    for i, candidate in iter_candidates(file_path):
        total += 1
        if validate and schema is not None:
            errors = validate_candidate(candidate, schema)
            if errors:
                invalid += 1
                logger.debug("Candidate at line %d failed validation: %s", i, errors)
                if not skip_invalid:
                    raise ValueError(f"Invalid candidate at line {i}: {errors}")
                continue

        results.append(candidate)
        if max_records is not None and len(results) >= max_records:
            break

    logger.info(
        "Loaded %d valid candidates (total read: %d, skipped invalid: %d) from %s",
        len(results),
        total,
        invalid,
        file_path,
    )
    return results


def save_jsonl(candidates: List[Dict], out_path: Path | str) -> None:
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for cand in candidates:
            f.write(json.dumps(cand, ensure_ascii=False) + "\n")


def _cli_main() -> None:
    parser = argparse.ArgumentParser(description="Load and validate candidates JSONL")
    parser.add_argument("file", help="Candidates JSONL file path")
    parser.add_argument("--schema", help="JSON Schema path to validate candidates")
    parser.add_argument("--max", type=int, help="Maximum valid candidates to load")
    parser.add_argument("--out", help="Optional output JSONL path for valid records")
    args = parser.parse_args()

    candidates = load_candidates(args.file, schema_path=args.schema, validate=bool(args.schema), max_records=args.max)
    print(f"Loaded {len(candidates)} valid candidates")
    if args.out:
        save_jsonl(candidates, args.out)
        print(f"Saved valid candidates to {args.out}")


if __name__ == "__main__":
    _cli_main()
