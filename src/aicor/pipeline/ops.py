"""Operational helpers: run lock, retry/backoff, structured logs, health (Phase 4).

These exist so automation is safe to schedule: a second run cannot overlap the
first, transient failures are retried with backoff, and every stage leaves a
machine-readable record of what happened.
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
import random
import socket
import time
from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypeVar

T = TypeVar("T")

LOGGER_NAME = "aicor"


class PipelineLockError(RuntimeError):
    """Raised when another pipeline run holds the lock."""


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


@contextlib.contextmanager
def pipeline_lock(
    path: str | Path = "data/.pipeline.lock",
    *,
    stale_seconds: int = 3600,
    run_id: str | None = None,
) -> Iterator[Path]:
    """Exclusive run lock with stale-lock recovery.

    A lock older than *stale_seconds* is treated as abandoned (the runner was
    killed) and reclaimed — otherwise a crashed job would block every later
    scheduled run.
    """
    lock_path = Path(path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    if lock_path.exists():
        try:
            age = time.time() - lock_path.stat().st_mtime
            payload = json.loads(lock_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            age, payload = stale_seconds + 1, {}

        if age < stale_seconds:
            raise PipelineLockError(
                f"pipeline lock held by run {payload.get('run_id', '?')} "
                f"(pid {payload.get('pid', '?')}, {int(age)}s old) at {lock_path}"
            )
        logging.getLogger(LOGGER_NAME).warning(
            "lock: reclaiming stale lock %s (%ss old, run %s)", lock_path, int(age), payload.get("run_id")
        )

    write_lock(lock_path, run_id=run_id)
    try:
        yield lock_path
    finally:
        with contextlib.suppress(FileNotFoundError):
            lock_path.unlink()


def write_lock(lock_path: Path, *, run_id: str | None = None) -> None:
    payload = {
        "run_id": run_id or f"pid-{os.getpid()}",
        "pid": os.getpid(),
        "host": socket.gethostname(),
        "started_at": _now(),
    }
    lock_path.write_text(json.dumps(payload), encoding="utf-8")


def with_retries[T](
    fn: Callable[[], T],
    *,
    retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    jitter: float = 0.25,
    logger: logging.Logger | None = None,
    description: str = "operation",
) -> T:
    """Call *fn* with exponential backoff + jitter on transient exceptions.

    The final failure is re-raised so the caller decides whether a single
    source failing degrades to ``partial`` (NFR-04) or aborts the run.
    """
    log = logger or logging.getLogger(LOGGER_NAME)
    last_exc: Exception | None = None

    for attempt in range(1, retries + 1):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - caller classifies the failure
            last_exc = exc
            if attempt == retries:
                break
            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            delay += random.uniform(0, delay * jitter)
            log.warning(
                "retry: %s failed (attempt %s/%s): %s — sleeping %.2fs",
                description,
                attempt,
                retries,
                exc,
                delay,
            )
            time.sleep(delay)

    assert last_exc is not None
    raise last_exc


def configure_logging(level: str = "INFO", log_file: str | Path | None = "data/logs/pipeline.jsonl") -> logging.Logger:
    """Configure a JSON-lines logger without leaking secrets (NFR-06)."""
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.propagate = False

    for handler in list(logger.handlers):
        logger.removeHandler(handler)

    stream = logging.StreamHandler()
    stream.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(stream)

    if log_file:
        path = Path(log_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(path, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(file_handler)

    return logger


def log_event(logger: logging.Logger, event: str, **fields: Any) -> None:
    """Emit one structured event as a JSON line (no secrets, no payloads)."""
    payload = {"ts": _now(), "event": event, **fields}
    logger.info(json.dumps(payload, ensure_ascii=False, default=str))


def read_sync_log(data_dir: str | Path = "data", limit: int = 12) -> list[dict[str, Any]]:
    """Return the most recent sync-log entries, newest last."""
    path = Path(data_dir) / "sync_log.jsonl"
    if not path.exists():
        return []
    entries: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries[-limit:]


def freshness_snapshot(
    *,
    generated_at: str,
    latest_data_quarter: str | None,
    data_status: str,
    sync_entries: list[dict[str, Any]],
) -> dict[str, Any]:
    """Describe how old the displayed dataset is, without claiming an SLA."""
    last_sync = None
    for entry in reversed(sync_entries):
        finished = entry.get("finished_at")
        if finished:
            last_sync = finished
            break

    return {
        "generated_at": generated_at,
        "latest_data_quarter": latest_data_quarter,
        "last_source_sync_at": last_sync,
        "data_status": data_status,
        "sla": "none",
        "note": (
            "Dashboard đọc artifact đã publish; độ mới phụ thuộc lịch chạy pipeline. "
            "Không có SLA uptime nào được cam kết."
        ),
    }


def write_health(payload: dict[str, Any], path: str | Path = "data/quality/health.json") -> Path:
    """Write the run health file atomically."""
    from aicor.pipeline.publish import _atomic_write  # local import avoids a cycle

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write(target, json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n")
    return target


def read_health(path: str | Path = "data/quality/health.json") -> dict[str, Any] | None:
    target = Path(path)
    if not target.exists():
        return None
    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
