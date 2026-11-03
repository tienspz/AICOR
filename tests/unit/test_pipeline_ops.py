"""Run lock and retry behaviour (Phase 4 automation safety)."""

import os
import time

import pytest

from aicor.pipeline.ops import PipelineLockError, pipeline_lock, with_retries


def test_lock_prevents_concurrent_runs(tmp_path):
    path = tmp_path / "pipeline.lock"
    with pipeline_lock(path, run_id="run-a"), pytest.raises(PipelineLockError), pipeline_lock(path, run_id="run-b"):
        pass
    assert not path.exists(), "lock must be released even on the happy path"


def test_lock_is_released_after_failure(tmp_path):
    path = tmp_path / "pipeline.lock"
    with pytest.raises(RuntimeError), pipeline_lock(path, run_id="run-a"):
        raise RuntimeError("boom")
    assert not path.exists()


def test_stale_lock_is_reclaimed(tmp_path):
    path = tmp_path / "pipeline.lock"
    path.write_text('{"run_id": "crashed", "pid": 1}', encoding="utf-8")
    old = time.time() - 7200
    os.utime(path, (old, old))
    with pipeline_lock(path, stale_seconds=60, run_id="run-new"):
        assert path.exists()


def test_retry_succeeds_after_transient_failures():
    attempts = {"count": 0}

    def flaky():
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise TimeoutError("transient")
        return "ok"

    assert with_retries(flaky, retries=3, base_delay=0.001) == "ok"
    assert attempts["count"] == 3


def test_retry_reraises_after_exhaustion():
    def always_fails():
        raise ConnectionError("down")

    with pytest.raises(ConnectionError):
        with_retries(always_fails, retries=2, base_delay=0.001)
