"""Semantic matching utilities: embeddings, caching, and similarity scoring.

Design goals:
- CPU-friendly batching and L2-normalized embeddings for fast cosine via dot-product
- On-disk caching of embeddings per (model, field) with candidate id verification
- Field-level embeddings (headline, summary, career_history) so caller can weight them
- No network calls are performed by this module at ranking time if a local model
  path is provided and model is already available locally.

Typical usage:
    from src.load_data import load_candidates
    candidates = load_candidates("data/candidates.jsonl", schema_path="data/candidate_schema.json")
    embeddings = build_candidate_embeddings(candidates, model_name="all-MiniLM-L6-v2")
    scores = score_against_jd(jd_text, embeddings, field_weights={"summary":0.6, "headline":0.2, "career_history":0.2})

This file includes a small CLI for quick local verification.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from tqdm import tqdm

# Try to import sentence-transformers; if not available or incompatible,
# fall back to a TF-IDF embedding implementation for local testing.
HAS_ST = True
try:
    from sentence_transformers import SentenceTransformer
except Exception:
    HAS_ST = False
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.preprocessing import normalize
    import warnings
    warnings.warn("sentence-transformers import failed; using TF-IDF fallback for embeddings.")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def _ensure_project_root_in_path():
    # Ensure src can import sibling modules when run as script
    root = Path(__file__).resolve().parents[1]
    if str(root) not in os.sys.path:
        os.sys.path.insert(0, str(root))


def _text_from_candidate(candidate: Dict, field: str) -> str:
    profile = candidate.get("profile", {})
    if field == "summary":
        return profile.get("summary", "") or ""
    if field == "headline":
        return profile.get("headline", "") or ""
    if field == "career_history":
        entries = candidate.get("career_history", [])
        parts = []
        for e in entries:
            title = e.get("title", "")
            company = e.get("company", "")
            desc = e.get("description", "")
            parts.append(". ".join([p for p in [title, company, desc] if p]))
        return " \n ".join(parts)
    # default: fallback to profile summary
    return profile.get("summary", "") or ""


def _cache_paths(cache_dir: Path, model_name: str, field: str) -> Tuple[Path, Path]:
    safe_model = model_name.replace("/", "_")
    base = f"emb_{safe_model}_{field}"
    npz = cache_dir / f"{base}.npz"
    meta = cache_dir / f"{base}.meta.json"
    return npz, meta


# Module-level cache so the SentenceTransformer model is loaded only
# once per process. Loading the all-MiniLM-L6-v2 model from disk takes
# ~30-60s; without this cache, both iter_candidate_embeddings and
# score_against_jd would each trigger a full load (~2x slower).
_MODEL_CACHE: Dict[str, object] = {}


def _get_or_load_model(model_name: str = "all-MiniLM-L6-v2", device: str = "cpu"):
    key = f"{model_name}::{device}"
    if key in _MODEL_CACHE:
        return _MODEL_CACHE[key]
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name, device=device)
    _MODEL_CACHE[key] = model
    return model


def _get_embedding_dim(model) -> int:
    """Return the model's embedding dimension, handling the rename in
    sentence-transformers >= 2.7 (get_embedding_dimension replaces
    get_sentence_embedding_dimension)."""
    for attr in ("get_embedding_dimension", "get_sentence_embedding_dimension"):
        try:
            return int(getattr(model, attr)())
        except Exception:
            continue
    return 384  # all-MiniLM-L6-v2 default


def load_model(model_name: str = "all-MiniLM-L6-v2", device: str = "cpu"):
    """Load a SentenceTransformer model or prepare a TF-IDF placeholder.

    Returns a model-like object understood by `embed_texts`. The model
    is cached at module level so repeated calls are O(1).
    """
    logger.info("Loading embedding model '%s' on device=%s (HAS_ST=%s)", model_name, device, HAS_ST)
    if HAS_ST:
        return _get_or_load_model(model_name, device)
    # TF-IDF fallback returns None as placeholder; `embed_texts` will build vectorizers per-call
    return None


def embed_texts(
    model,
    texts: List[str],
    batch_size: int = 128,
) -> np.ndarray:
    """Embed a list of texts using `model.encode`, returning L2-normalized float32 array.

    Returns:
        np.ndarray shape (n_texts, dim)
    """
    if not texts:
        if HAS_ST:
            return np.zeros((0, model.get_sentence_embedding_dimension()), dtype=np.float32)
        return np.zeros((0, 0), dtype=np.float32)

    if HAS_ST:
        all_emb = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            emb = model.encode(batch, batch_size=len(batch), show_progress_bar=False, convert_to_numpy=True)
            all_emb.append(emb.astype(np.float32))
        emb = np.vstack(all_emb)
        # L2 normalize rows
        norms = np.linalg.norm(emb, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        emb = emb / norms
        return emb

    # TF-IDF fallback: build vectorizer and return normalized dense vectors
    vectorizer = TfidfVectorizer(max_features=768)
    X = vectorizer.fit_transform(texts)
    arr = X.toarray().astype(np.float32)
    arr = normalize(arr, norm="l2", axis=1)
    return arr


def build_candidate_embeddings(
    candidates: List[Dict],
    model_name: str = "all-MiniLM-L6-v2",
    fields: Optional[List[str]] = None,
    cache_dir: Optional[Path] = None,
    batch_size: int = 128,
    force_recompute: bool = False,
) -> Dict[str, Dict]:
    """Compute or load embeddings per field for the candidate list.

    Returns a dict mapping field -> {"embeddings": np.ndarray, "candidate_ids": List[str]}
    """
    if fields is None:
        fields = ["summary", "headline", "career_history"]
    if cache_dir is None:
        cache_dir = Path(".cache/embeddings")
    cache_dir.mkdir(parents=True, exist_ok=True)

    model = load_model(model_name)

    candidate_ids = [c["candidate_id"] for c in candidates]

    results: Dict[str, Dict] = {}
    for field in fields:
        npz_path, meta_path = _cache_paths(cache_dir, model_name, field)
        use_cache = npz_path.exists() and meta_path.exists() and not force_recompute
        if use_cache:
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)

                # Validate candidate ids match first
                if meta.get("candidate_ids") != candidate_ids:
                    logger.info("Cache candidate id mismatch for %s, recomputing embeddings", field)
                else:
                    # Determine backend/dimension compatibility
                    meta_backend = meta.get("backend")
                    meta_dim = meta.get("dim")
                    if HAS_ST:
                        # If we have sentence-transformers available, prefer ST embeddings.
                        model_dim = None
                        try:
                            model_dim = model.get_sentence_embedding_dimension()
                        except Exception:
                            model_dim = None

                        # If meta indicates TF-IDF backend but ST is available, treat as mismatch
                        if meta_backend == "tfidf":
                            logger.info("Cache backend tfidf found for %s but ST available; recomputing", field)
                        # If meta indicates ST backend, ensure model name and dim match
                        elif meta_backend == "st":
                            if meta.get("model_name") == model_name and (meta_dim is None or model_dim is None or int(meta_dim) == int(model_dim)):
                                npz = np.load(npz_path, mmap_mode="r")
                                emb = npz["embeddings"]
                                logger.info("Loaded embeddings from cache %s", npz_path)
                                results[field] = {"embeddings": emb, "candidate_ids": candidate_ids}
                                continue
                            else:
                                logger.info("Cache model/dim mismatch for %s, recomputing embeddings", field)
                        else:
                            # Unknown backend recorded; be conservative and recompute
                            logger.info("Unknown cache backend for %s, recomputing embeddings", field)
                    else:
                        # No ST available. Accept TF-IDF caches if present and dims exist.
                        if meta_backend == "tfidf" and meta_dim is not None:
                            try:
                                npz = np.load(npz_path, mmap_mode="r")
                                emb = npz["embeddings"]
                                logger.info("Loaded TF-IDF embeddings from cache %s", npz_path)
                                results[field] = {"embeddings": emb, "candidate_ids": candidate_ids}
                                continue
                            except Exception:
                                logger.info("Failed to load TF-IDF cache for %s, recomputing", field)
                        else:
                            logger.info("Cache backend/states incompatible for %s, recomputing", field)
            except Exception:
                logger.info("Failed to load cache for %s, recomputing", field)

        texts = [_text_from_candidate(c, field) for c in candidates]
        logger.info("Embedding field '%s' for %d candidates (model=%s)", field, len(texts), model_name)

        if HAS_ST:
            emb = embed_texts(model, texts, batch_size=batch_size)
            # persist
            try:
                np.savez_compressed(npz_path, embeddings=emb)
                meta = {
                    "candidate_ids": candidate_ids,
                    "model_name": model_name,
                    "backend": "st",
                    "dim": int(emb.shape[1]),
                }
                with open(meta_path, "w", encoding="utf-8") as f:
                    json.dump(meta, f)
                logger.info("Saved embeddings to %s (dim=%d)", npz_path, emb.shape[1])
            except Exception as exc:
                logger.warning("Failed to save embeddings cache: %s", exc)

            results[field] = {"embeddings": emb, "candidate_ids": candidate_ids}
        else:
            # TF-IDF fallback: build vectorizer here and persist its vocabulary so JD scoring can reuse it
            vectorizer = TfidfVectorizer(max_features=768)
            X = vectorizer.fit_transform(texts)
            arr = X.toarray().astype(np.float32)
            # L2 normalize rows
            from sklearn.preprocessing import normalize

            arr = normalize(arr, norm="l2", axis=1)

            try:
                np.savez_compressed(npz_path, embeddings=arr)
                # Ensure vocabulary indices are plain Python ints (JSON serializable)
                vocab_serializable = {k: int(v) for k, v in vectorizer.vocabulary_.items()}
                meta = {
                    "candidate_ids": candidate_ids,
                    "model_name": model_name,
                    "backend": "tfidf",
                    "vocabulary": vocab_serializable,
                    "dim": int(arr.shape[1]),
                }
                with open(meta_path, "w", encoding="utf-8") as f:
                    json.dump(meta, f)
                logger.info("Saved TF-IDF embeddings+vocab to %s (dim=%d)", npz_path, arr.shape[1])
            except Exception as exc:
                logger.warning("Failed to save TF-IDF cache: %s", exc)

            results[field] = {"embeddings": arr, "candidate_ids": candidate_ids, "vocabulary": vectorizer.vocabulary_}

    return results


def iter_candidate_embeddings(
    candidates: List[Dict],
    model_name: str = "all-MiniLM-L6-v2",
    fields: Optional[List[str]] = None,
    cache_dir: Optional[Path] = None,
    batch_size: int = 64,
    force_recompute: bool = False,
) -> Iterator[Tuple[str, str, np.ndarray]]:
    """Yield (candidate_id, field, embedding) lazily with per-candidate disk cache.

    Designed for a bounded candidate list (e.g., a prefiltered subset of
    size ~prefilter_k). For each (candidate_id, field) pair, the embedding
    is loaded from ``.cache/per_cand_<model>_<cid>_<field>.npy`` if present,
    otherwise computed in batches and saved.

    This means a candidate embedded in a previous run is reused on the
    next run — the cache never invalidates when the candidate set changes
    or prefilter_k changes.
    """
    from sentence_transformers import SentenceTransformer  # local import for lazy load
    if fields is None:
        fields = ["summary", "headline", "career_history"]
    if cache_dir is None:
        cache_dir = Path(".cache/embeddings")
    cache_dir.mkdir(parents=True, exist_ok=True)
    safe_model = model_name.replace("/", "_")
    model = _get_or_load_model(model_name, "cpu")

    def _per_cand_path(cid: str, field: str) -> Path:
        safe_cid = str(cid).replace("/", "_").replace("\\", "_")
        return cache_dir / f"per_cand_{safe_model}_{safe_cid}_{field}.npy"

    # Pass 1: load from disk cache where available, collect missing per field
    missing_per_field: Dict[str, List[Tuple[str, str]]] = {f: [] for f in fields}
    expected_dim = None
    try:
        expected_dim = _get_embedding_dim(model)
    except Exception:
        expected_dim = 384  # all-MiniLM-L6-v2 default
    for c in candidates:
        cid = c.get("candidate_id")
        if cid is None:
            continue
        for field in fields:
            p = _per_cand_path(cid, field)
            if p.exists() and not force_recompute:
                cache_ok = False
                try:
                    arr = np.load(p)
                    # Accept only a 1D float array of the expected dim with
                    # finite values. Anything else (0-d, wrong shape, NaN/Inf,
                    # object dtype, multi-array .npz masquerading as .npy) is
                    # treated as a corrupt cache and is deleted + re-embedded.
                    if (
                        isinstance(arr, np.ndarray)
                        and arr.ndim == 1
                        and arr.shape[0] == expected_dim
                        and np.isfinite(arr).all()
                    ):
                        yield (cid, field, arr.astype(np.float32, copy=False))
                        cache_ok = True
                except Exception as exc:
                    logger.warning(
                        "Corrupt cache file %s (cid=%s field=%s): %s; will recompute",
                        p, cid, field, exc,
                    )
                if not cache_ok:
                    try:
                        p.unlink(missing_ok=True)
                    except Exception:
                        pass
                    text = _text_from_candidate(c, field)
                    missing_per_field[field].append((cid, text))
                continue
            text = _text_from_candidate(c, field)
            missing_per_field[field].append((cid, text))

    # Pass 2: batch-embed missing per field. We do NOT swallow exceptions
    # here: a real failure (OOM, dimension mismatch, broken cache) must
    # propagate to the caller so the user sees a proper error instead of
    # silent zeros. We convert the exception into a clear, structured
    # RuntimeError with the field name, candidate count, and the original
    # cause.
    for field in fields:
        items = missing_per_field[field]
        if not items:
            continue
        cids = [cid for cid, _ in items]
        texts = [t for _, t in items]
        try:
            embs = embed_texts(model, texts, batch_size=batch_size)
        except Exception as exc:
            logger.exception(
                "iter_candidate_embeddings: failed to embed field=%s n=%d",
                field, len(items),
            )
            raise RuntimeError(
                f"Embedding generation failed for field={field!r} "
                f"({len(items)} candidates, model={model_name}): {type(exc).__name__}: {exc}"
            ) from exc
        if embs is None or not isinstance(embs, np.ndarray):
            raise RuntimeError(
                f"Embedding generation returned no array for field={field!r}"
            )
        if embs.ndim != 2 or embs.shape[0] != len(cids):
            raise RuntimeError(
                f"Embedding generation produced unexpected shape for field={field!r}: "
                f"expected (n={len(cids)}, dim={expected_dim}), got {embs.shape}"
            )
        if embs.shape[1] != expected_dim:
            raise RuntimeError(
                f"Embedding dimension mismatch for field={field!r}: "
                f"expected dim={expected_dim}, got dim={embs.shape[1]}"
            )
        for cid, vec in zip(cids, embs):
            p = _per_cand_path(cid, field)
            try:
                np.save(p, vec.astype(np.float32))
            except Exception as exc:
                logger.warning("Failed to persist embedding cache for %s/%s: %s", cid, field, exc)
            yield (cid, field, vec)


def _embed_text_single(model, text: str) -> np.ndarray:
    if HAS_ST:
        emb = model.encode([text], show_progress_bar=False, convert_to_numpy=True)
        # `model.encode` may return either a 2-D (1, dim) or, in some
        # edge cases (empty text, tokenizer issues), a 0-D / 1-D
        # array. Normalize to a 1-D (dim,) vector with defensive
        # fallbacks so downstream code never sees an unexpected shape.
        if not isinstance(emb, np.ndarray):
            emb = np.asarray(emb)
        if emb.ndim == 0:
            emb = emb.reshape(1)
        if emb.ndim == 1:
            # Treat as a single vector already
            arr = emb.astype(np.float32)
        else:
            arr = emb.astype(np.float32)
            if arr.shape[0] != 1:
                arr = arr[:1]
        norm = np.linalg.norm(arr, axis=1, keepdims=True)
        norm[norm == 0] = 1.0
        arr = arr / norm
        return arr[0]
    # TF-IDF fallback: use the same vectorizer strategy as embed_texts for single text
    vectorizer = TfidfVectorizer(max_features=768)
    X = vectorizer.fit_transform([text])
    arr = X.toarray().astype(np.float32)
    norm = np.linalg.norm(arr, axis=1, keepdims=True)
    norm[norm == 0] = 1.0
    arr = arr / norm
    return arr[0]


def score_against_jd(
    jd_text: str,
    candidate_embeddings: Dict[str, np.ndarray],
    model_name: str = "all-MiniLM-L6-v2",
    field_weights: Optional[Dict[str, float]] = None,
    cache_dir: Optional[Path] = None,
    candidates: Optional[List[Dict]] = None,
) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
    """Score candidates against a job description.

    Accepts ``candidate_embeddings`` as a mapping of field name to a 2-D
    ``np.ndarray`` of shape ``(n_candidates, dim)``. This matches the
    output of both the in-memory ``iter_candidate_embeddings`` stacking
    step in ``generate_submission.py`` and the legacy
    ``build_candidate_embeddings`` output (after extracting the
    ``"embeddings"`` array).

    Returns:
        final_scores: np.ndarray shape (n_candidates,)
        per_field_scores: dict field -> np.ndarray shape (n_candidates,)
    """
    if field_weights is None:
        field_weights = {"summary": 0.6, "headline": 0.2, "career_history": 0.2}
    if cache_dir is None:
        cache_dir = Path(".cache/embeddings")

    model = load_model(model_name)
    if HAS_ST:
        jd_emb = _embed_text_single(model, jd_text)
    else:
        # For TF-IDF fallback, we must transform JD into the same vocabulary used
        # when building candidate embeddings. We'll reconstruct a vectorizer per-field
        # from saved meta (vocabulary) and produce per-field jd embeddings.
        jd_emb = None

    per_field_scores: Dict[str, np.ndarray] = {}
    candidate_count = None
    for field, data in candidate_embeddings.items():
        # ---- Strict cache-format validation --------------------------------
        # `score_against_jd` historically expected the legacy
        # `build_candidate_embeddings` shape:  Dict[str, Dict] where each
        # value is {"embeddings": np.ndarray, "candidate_ids": [...]}.
        # The newer `iter_candidate_embeddings` (used by
        # `generate_submission.py`) yields per-field vectors directly, so
        # the caller passes Dict[str, np.ndarray]. We accept BOTH forms
        # for backward compatibility, but anything else is a hard error
        # so we never silently fall through to `data["embeddings"]` on a
        # numpy array (which raises the cryptic
        # "only integers, slices, ellipsis..." IndexError).
        if isinstance(data, dict):
            if "embeddings" not in data:
                raise RuntimeError(
                    f"score_against_jd: expected dict with an 'embeddings' "
                    f"key for field={field!r}, but got keys={list(data.keys())}. "
                    f"Either pass a 2-D np.ndarray directly, or include "
                    f"'embeddings' in the dict."
                )
            emb = data["embeddings"]
        elif isinstance(data, np.ndarray):
            emb = data
        else:
            raise RuntimeError(
                f"score_against_jd: expected embedding cache dict but got "
                f"{type(data).__name__} for field={field!r}. Valid forms: "
                f"(a) 2-D np.ndarray of shape (n_candidates, dim); or "
                f"(b) dict with key 'embeddings' -> 2-D np.ndarray. "
                f"Got value: {data!r:.200}"
            )

        # ---- Shape / dim / finiteness validation ----------------------------
        if not isinstance(emb, np.ndarray):
            raise RuntimeError(
                f"score_against_jd: field={field!r} 'embeddings' is not a "
                f"numpy array (got {type(emb).__name__})."
            )
        if emb.ndim != 2:
            raise RuntimeError(
                f"score_against_jd: field={field!r} 'embeddings' must be "
                f"2-D (n_candidates, dim); got ndim={emb.ndim} shape={emb.shape}."
            )
        if emb.shape[0] == 0:
            raise RuntimeError(
                f"score_against_jd: field={field!r} has zero candidates; "
                f"the candidate list is empty."
            )
        if not np.isfinite(emb).all():
            n_bad = int((~np.isfinite(emb)).sum())
            raise RuntimeError(
                f"score_against_jd: field={field!r} 'embeddings' contains "
                f"{n_bad} non-finite value(s) (NaN/Inf). Delete the per-candidate "
                f"cache (.cache/embeddings/per_cand_*.npy) and re-run with "
                f"--reset-cache, or check the upstream embed_texts() output."
            )
        if candidate_count is None:
            candidate_count = emb.shape[0]
        if HAS_ST:
            # Ensure embedding dimensions align. If they don't, try to rebuild
            # candidate embeddings with the current model (force_recompute) when
            # the caller provided `candidates`. This handles cases where cached
            # embeddings were produced by a different method (e.g., TF-IDF) or
            # an older model, which leads to shape mismatches like
            # (n,513) vs (384,).
            if jd_emb is None:
                # No JD embedding available (shouldn't happen for HAS_ST), fallback
                jd_emb_local = _embed_text_single(model, jd_text) if 'jd_text' in locals() else None
            else:
                jd_emb_local = jd_emb

            if jd_emb_local is None:
                scores = np.zeros((emb.shape[0],), dtype=np.float32)
                per_field_scores[field] = scores
                continue

            if emb.shape[1] != jd_emb_local.shape[0]:
                # Attempt to rebuild candidate embeddings with the current model
                # if we have the original candidate list available to ensure
                # consistent dimensions.
                if candidates is not None:
                    logger.info(
                        "Dimension mismatch for field=%s (cand_dim=%d, jd_dim=%d). Rebuilding embeddings with model=%s",
                        field,
                        emb.shape[1],
                        jd_emb_local.shape[0],
                        model_name,
                    )
                    try:
                        rebuilt = build_candidate_embeddings(
                            candidates,
                            model_name=model_name,
                            cache_dir=Path(cache_dir) if cache_dir is not None else None,
                            fields=[field],
                            force_recompute=True,
                        )
                        emb = rebuilt[field]["embeddings"]
                        candidate_embeddings[field] = emb
                    except Exception:
                        logger.exception("Rebuilding embeddings failed for field=%s", field)

            # If dimensions still mismatch, pad/truncate JD vector to match emb dim
            if emb.shape[1] != jd_emb_local.shape[0]:
                logger.warning(
                    "After rebuild: Dimension mismatch between candidate embeddings (%d) and JD vector (%d) for field=%s; padding/truncating JD vector",
                    emb.shape[1],
                    jd_emb_local.shape[0],
                    field,
                )
                if jd_emb_local.shape[0] < emb.shape[1]:
                    new = np.zeros((emb.shape[1],), dtype=np.float32)
                    new[: jd_emb_local.shape[0]] = jd_emb_local
                    jd_emb_use = new
                else:
                    jd_emb_use = jd_emb_local[: emb.shape[1]]
            else:
                jd_emb_use = jd_emb_local

            # cosine since vectors are normalized: dot product
            scores = emb.dot(jd_emb_use)
            per_field_scores[field] = scores
        else:
            # Reconstruct vectorizer from cache meta to get JD vector in same space
            npz_path, meta_path = _cache_paths(Path(cache_dir), model_name, field)
            jd_vec = None
            try:
                if meta_path.exists():
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    vocab = meta.get("vocabulary")
                    if not vocab:
                        # If vocabulary missing from meta and caller provided candidates,
                        # rebuild TF-IDF embeddings so we have a consistent vocab.
                        if candidates is not None:
                            logger.info(
                                "Rebuilding TF-IDF candidate embeddings for field=%s to generate vocabulary",
                                field,
                            )
                            rebuilt = build_candidate_embeddings(candidates, model_name=model_name, cache_dir=Path(cache_dir) if cache_dir is not None else None, fields=[field], force_recompute=True)
                            # replace emb and meta
                            emb = rebuilt[field]["embeddings"]
                            candidate_embeddings[field]["embeddings"] = emb
                            # reload meta
                            if meta_path.exists():
                                with open(meta_path, "r", encoding="utf-8") as f2:
                                    meta = json.load(f2)
                                vocab = meta.get("vocabulary")

                    if vocab:
                        # Robust token-based JD vector creation to avoid sklearn shape mismatches
                        dim = emb.shape[1]
                        jd_vec = np.zeros((dim,), dtype=np.float32)
                        import re

                        tokens = [t.lower() for t in re.findall(r"\w+", jd_text)]
                        for t in tokens:
                            idx = vocab.get(t)
                            if idx is None:
                                continue
                            if idx < dim:
                                jd_vec[idx] += 1.0
                        n = np.linalg.norm(jd_vec)
                        if n > 0:
                            jd_vec = jd_vec / n
                        else:
                            jd_vec = jd_vec
                    else:
                        jd_vec = None
            except Exception:
                jd_vec = None

            if jd_vec is None:
                # fallback: compute a TF-IDF on JD only (lower quality)
                jd_vec = _embed_text_single(model, jd_text)

            # If dimensions still mismatch, pad/truncate JD vector to match emb dim
            if emb.shape[1] != jd_vec.shape[0]:
                logger.warning(
                    "Dimension mismatch between candidate embeddings (%d) and JD vector (%d) for field=%s; padding/truncating JD vector",
                    emb.shape[1],
                    jd_vec.shape[0],
                    field,
                )
                if jd_vec.shape[0] < emb.shape[1]:
                    new = np.zeros((emb.shape[1],), dtype=np.float32)
                    new[: jd_vec.shape[0]] = jd_vec
                    jd_vec = new
                else:
                    jd_vec = jd_vec[: emb.shape[1]]

            scores = emb.dot(jd_vec)
            per_field_scores[field] = scores

    # combine
    final = np.zeros(candidate_count, dtype=np.float32)
    for field, weight in field_weights.items():
        arr = per_field_scores.get(field)
        if arr is None:
            continue
        final += weight * arr

    return final, per_field_scores


def top_k_candidates(scores: np.ndarray, candidate_ids: List[str], k: int = 10) -> List[Tuple[str, float]]:
    order = np.argsort(-scores)
    top = []
    for idx in order[:k]:
        top.append((candidate_ids[idx], float(scores[idx])))
    return top


def _cli():
    import argparse

    _ensure_project_root_in_path()
    from src.load_data import load_candidates

    parser = argparse.ArgumentParser(description="Quick semantic matching check")
    parser.add_argument("--candidates", required=True, help="Candidates JSONL path")
    parser.add_argument("--schema", required=False, help="JSON Schema path for validation")
    parser.add_argument("--jd", required=True, help="Job description text file path")
    parser.add_argument("--model", default="all-MiniLM-L6-v2", help="SentenceTransformer model name or local path")
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--cache-dir", default=".cache/embeddings")
    args = parser.parse_args()

    candidates = load_candidates(args.candidates, schema_path=args.schema, validate=bool(args.schema))
    with open(args.jd, "r", encoding="utf-8") as f:
        jd_text = f.read()

    embeddings = build_candidate_embeddings(candidates, model_name=args.model, cache_dir=Path(args.cache_dir))
    final_scores, per_field = score_against_jd(jd_text, embeddings, model_name=args.model, cache_dir=Path(args.cache_dir), candidates=candidates)

    ids = [c["candidate_id"] for c in candidates]
    top = top_k_candidates(final_scores, ids, k=args.top)
    print("Top candidates (id, score):")
    for cid, score in top:
        print(cid, f"{score:.4f}")


if __name__ == "__main__":
    _cli()
