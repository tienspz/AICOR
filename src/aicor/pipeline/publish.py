"""Atomic, versioned publishing of dashboard data (PIPE-02, Phase 4).

Layout under ``web/data``::

    manifest.json          ← the only mutable pointer, replaced atomically
    runs/<run_id>.json     ← immutable payload, one per pipeline run

A reader fetches ``manifest.json`` first and then the exact ``path`` it names.
Because the payload file is never rewritten in place, a reader can never
observe a half-written dataset, and the checksum lets the UI verify what it got.
"""

from __future__ import annotations

import json
import logging
import math
import os
import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aicor.pipeline.artifacts import sha256_bytes

logger = logging.getLogger(__name__)

MANIFEST_SCHEMA = "aicor-dashboard-manifest/v1"


def _atomic_write(path: Path, payload: str) -> None:
    """Write *payload* to *path* atomically (same filesystem, fsync'd)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-", suffix=path.suffix)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(payload)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    except Exception:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise


def publish_dashboard(
    payload: dict[str, Any],
    *,
    run_id: str,
    out_dir: str | Path = "web/data",
    freshness: dict[str, Any] | None = None,
    keep_versions: int = 5,
) -> dict[str, Any]:
    """Publish *payload* as an immutable version and flip the manifest."""
    out = Path(out_dir)
    runs_dir = out / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=_default)
    digest = sha256_bytes(body.encode())
    run_path = runs_dir / f"{run_id}.json"

    _atomic_write(run_path, body)

    published_at = datetime.now(UTC).isoformat(timespec="seconds")
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "dataset_version": digest,
        "run_id": run_id,
        "path": f"runs/{run_id}.json",
        "published_at": published_at,
        "bytes": len(body.encode()),
        "config_version": payload.get("meta", {}).get("config_version"),
        "as_of_quarter": payload.get("meta", {}).get("as_of_quarter"),
        "freshness": freshness or {},
    }
    payload_json = json.dumps(manifest, indent=2, ensure_ascii=False, default=_default) + "\n"
    _atomic_write(out / "manifest.json", payload_json)

    _prune_versions(runs_dir, keep=keep_versions, current=run_path)
    logger.info(
        "publish: run=%s version=%s bytes=%s",
        run_id,
        digest[:12],
        len(body),
    )
    return manifest


def _prune_versions(runs_dir: Path, *, keep: int, current: Path) -> None:
    """Keep the newest *keep* payloads (plus the current one); drop the rest."""
    files = sorted(runs_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for stale in files[keep:]:
        if stale == current:
            continue
        try:
            stale.unlink()
        except OSError:  # pragma: no cover - best effort
            logger.warning("publish: could not prune %s", stale)


def read_manifest(out_dir: str | Path = "web/data") -> dict[str, Any] | None:
    """Return the current manifest, or ``None`` when nothing is published."""
    path = Path(out_dir) / "manifest.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.warning("publish: manifest is not valid JSON: %s", path)
        return None


def verify_published(payload: dict[str, Any], manifest: dict[str, Any]) -> bool:
    """Confirm a payload matches the manifest checksum (used by tests/ops)."""
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=_default)
    return sha256_bytes(body.encode()) == manifest.get("dataset_version")


def _default(value: Any):
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, float) and math.isnan(value):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def clear_versions(out_dir: str | Path = "web/data") -> None:
    """Remove published payloads (test helper; never called by the pipeline)."""
    runs_dir = Path(out_dir) / "runs"
    if runs_dir.exists():
        shutil.rmtree(runs_dir)
