"""Scheduled collection with per-source isolation and retries (NFR-04, PIPE-01).

Each crawler runs in its own subprocess so a crash or a hung socket in one
source cannot take the others down. Transient failures are retried with
exponential backoff; a permanently failing source is recorded as ``failed``
and the cycle continues with the data already collected.
"""

from __future__ import annotations

import logging
import subprocess
import sys
import time
from datetime import UTC, datetime
from typing import Any

from aicor.pipeline.ops import LOGGER_NAME, with_retries

logger = logging.getLogger(LOGGER_NAME)

SOURCES: dict[str, str] = {
    "sec": "aicor.sources.sec",
    "market": "aicor.sources.market",
    "trends": "aicor.sources.trends",
    "ir": "aicor.sources.ir",
}


def run_source(module: str, *, timeout: int = 900, retries: int = 2) -> dict[str, Any]:
    """Run one crawler module in a subprocess, with retries."""

    def _invoke() -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-m", module],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

    started = time.perf_counter()
    try:
        proc = with_retries(
            _invoke,
            retries=retries,
            base_delay=5.0,
            max_delay=60.0,
            description=module,
        )
        ok = proc.returncode == 0
        return {
            "module": module,
            "status": "success" if ok else "failed",
            "returncode": proc.returncode,
            "stdout_tail": (proc.stdout or "")[-1200:],
            "stderr_tail": (proc.stderr or "")[-1200:],
            "duration_seconds": round(time.perf_counter() - started, 3),
            "finished_at": datetime.now(UTC).isoformat(timespec="seconds"),
        }
    except subprocess.TimeoutExpired as exc:
        logger.error("collect: %s timed out after %ss", module, timeout)
        return {
            "module": module,
            "status": "failed",
            "error": f"timeout after {timeout}s: {exc}",
            "duration_seconds": round(time.perf_counter() - started, 3),
            "finished_at": datetime.now(UTC).isoformat(timespec="seconds"),
        }
    except Exception as exc:  # noqa: BLE001 - one source must not abort the rest
        logger.error("collect: %s failed: %s", module, exc)
        return {
            "module": module,
            "status": "failed",
            "error": str(exc),
            "duration_seconds": round(time.perf_counter() - started, 3),
            "finished_at": datetime.now(UTC).isoformat(timespec="seconds"),
        }


def collect_all(*, only: list[str] | None = None, retries: int = 2) -> dict[str, Any]:
    """Run every configured crawler; never raises for a single source failure."""
    selected = only or list(SOURCES)
    results: dict[str, Any] = {}
    for name in selected:
        module = SOURCES.get(name)
        if module is None:
            results[name] = {"status": "skipped", "error": f"unknown source {name!r}"}
            continue
        logger.info("collect: running %s", name)
        results[name] = run_source(module, retries=retries)

    statuses = [r.get("status") for r in results.values()]
    overall = "success"
    if any(s == "failed" for s in statuses) and any(s == "success" for s in statuses):
        overall = "partial"
    elif statuses and all(s == "failed" for s in statuses):
        overall = "failed"

    return {
        "status": overall,
        "sources": results,
        "finished_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
