"""Source registry and sync-log contracts.

Implements: SPEC SRC-01/03 (§8.1 bảng 2, 11), §6.7 field list.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4


# ---------- SourceRecord ----------

VALID_TIERS = {"S", "A", "B"}
VALID_SOURCE_TYPES = {"sec_xbrl", "market", "trends", "ir_blog", "ir_event"}


@dataclass(frozen=True)
class SourceRecord:
    """One provenance entry in the source registry (SRC-01).

    ``source_tier`` must be one of S / A / B — Tier R is reference-only and
    MUST NOT appear in the registry (SRC-01).
    """

    source_id: str
    company: str
    metric: str
    source_type: str
    source_tier: Literal["S", "A", "B"]
    source_url: str
    reporting_period: str
    filing_date: str | None = None
    access_date: str | None = None
    primary_or_secondary: str = "primary"
    verification_status: str = "unverified"
    xbrl_tag: str | None = None
    period_basis: str | None = None

    def __post_init__(self) -> None:
        if self.source_tier not in VALID_TIERS:
            raise ValueError(
                f"source_tier must be one of {VALID_TIERS!r}, got {self.source_tier!r}"
            )


# ---------- SyncRecord ----------

VALID_SYNC_STATUSES = {"success", "partial", "failed"}


@dataclass
class SyncRecord:
    """One row in the sync log (§6.7, 16 fields)."""

    run_id: str = field(default_factory=lambda: uuid4().hex[:12])
    source_type: str = ""
    company: str = ""
    started_at: str = ""
    finished_at: str = ""
    sync_status: str = "success"
    records_fetched: int = 0
    records_new: int = 0
    records_updated: int = 0
    records_skipped: int = 0
    error_message: str | None = None
    raw_file_path: str | None = None
    raw_sha256: str | None = None
    manifest_path: str | None = None
    config_version: str | None = None
    missing_reason: str | None = None


def write_sync_log(
    record: SyncRecord,
    log_dir: str | Path = "data",
) -> SyncRecord:
    """Append *record* as a JSON line to ``sync_log.jsonl``."""
    log_path = Path(log_dir) / "sync_log.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(record), default=str) + "\n")
    return record


# ---------- SHA-256 ----------

def sha256_file(path: str | Path) -> str:
    """Return the hex SHA-256 digest for *path* (NFR-01)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------- Manifest helpers ----------

def append_manifest(
    manifest_path: str | Path,
    *,
    filename: str,
    sha256: str,
    source_url: str,
    retrieved_at: str | None = None,
) -> None:
    """Append one row to a CSV manifest (NFR-01)."""
    import csv

    mp = Path(manifest_path)
    write_header = not mp.exists() or mp.stat().st_size == 0
    mp.parent.mkdir(parents=True, exist_ok=True)
    with open(mp, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(["filename", "sha256", "source_url", "retrieved_at"])
        w.writerow([
            filename,
            sha256,
            source_url,
            retrieved_at or datetime.now(timezone.utc).isoformat(),
        ])
