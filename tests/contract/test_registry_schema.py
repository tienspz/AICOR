"""Contract tests for source_registry schema (Task 3).

Verifies: SRC-01 tier validation, SyncRecord fields, SHA-256.
"""

import tempfile
from pathlib import Path

import pytest

from aicor.sources import SourceRecord, SyncRecord, sha256_file, write_sync_log


# ---------- SourceRecord ----------

def _make_record(**overrides):
    """Build a valid SourceRecord, overriding specific fields."""
    defaults = dict(
        source_id="SEC-MSFT-revenue-2024Q1",
        company="MSFT",
        metric="revenue",
        source_type="sec_xbrl",
        source_tier="S",
        source_url="https://data.sec.gov/api/xbrl/companyfacts/CIK0000789019.json",
        reporting_period="2024-Q1",
    )
    defaults.update(overrides)
    return SourceRecord(**defaults)


def test_registry_rejects_tier_r():
    """Tier R is reference-only and must NOT appear in the registry (SRC-01)."""
    with pytest.raises(ValueError, match="source_tier"):
        _make_record(source_tier="R")


def test_registry_rejects_invalid_tier():
    with pytest.raises(ValueError):
        _make_record(source_tier="X")


def test_registry_accepts_valid_tiers():
    for tier in ("S", "A", "B"):
        rec = _make_record(source_tier=tier)
        assert rec.source_tier == tier


def test_source_record_frozen():
    rec = _make_record()
    with pytest.raises(AttributeError):
        rec.company = "GOOGL"  # type: ignore[misc]


# ---------- SyncRecord ----------

def test_sync_record_has_16_fields():
    """§6.7 specifies 16 sync fields."""
    sr = SyncRecord()
    # dataclass fields count
    from dataclasses import fields
    assert len(fields(sr)) == 16


def test_sync_log_write_creates_file(tmp_path):
    rec = SyncRecord(source_type="sec_xbrl", company="MSFT", sync_status="success")
    write_sync_log(rec, log_dir=tmp_path)
    log_file = tmp_path / "sync_log.jsonl"
    assert log_file.exists()
    import json
    data = json.loads(log_file.read_text().strip())
    assert data["company"] == "MSFT"
    assert data["sync_status"] == "success"


# ---------- SHA-256 ----------

def test_sha256_file_deterministic(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("hello world")
    h1 = sha256_file(f)
    h2 = sha256_file(f)
    assert h1 == h2
    assert len(h1) == 64  # hex digest length
