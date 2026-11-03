"""End-to-end compute → forecast → publish cycle (Phase 2 → Phase 4)."""

import json

import pandas as pd

from aicor.pipeline import orchestrate
from aicor.pipeline.orchestrate import run_analysis_cycle
from aicor.pipeline.publish import read_manifest, verify_published


def _run(tmp_path, **kwargs):
    return run_analysis_cycle(
        data_dir=tmp_path,
        out_dir=tmp_path / "processed",
        publish_dir=tmp_path / "web" / "data",
        **kwargs,
    )


def test_cycle_produces_all_artifacts(synthetic_processed):
    result = _run(synthetic_processed)
    assert result.status == "success", result.warnings
    proc = synthetic_processed / "processed"
    for name in (
        "features_quarterly.csv",
        "analysis_results.csv",
        "provenance.csv",
        "forecast_results.csv",
        "forecast_backtest.csv",
        "forecast_coverage.csv",
        "alert_log.csv",
        "model_registry.json",
        "model_card.md",
        "analysis_manifest.json",
        "pulse_manifest.json",
    ):
        assert (proc / name).exists(), f"missing artifact {name}"

    assert result.stages["compute"] == "ok"
    assert result.stages["publish"] == "ok"


def test_published_payload_verifies_against_manifest(synthetic_processed):
    result = _run(synthetic_processed)
    publish_dir = synthetic_processed / "web" / "data"
    manifest = read_manifest(publish_dir)
    payload = json.loads((publish_dir / manifest["path"]).read_text(encoding="utf-8"))
    assert verify_published(payload, manifest) is True
    assert payload["meta"]["run_id"] == result.run_id
    assert payload["meta"]["as_of_quarter"] == "2025Q4"


def test_cycle_is_deterministic_for_analysis_artifacts(synthetic_processed):
    proc = synthetic_processed / "processed"
    first = _run(synthetic_processed)
    first_results = pd.read_csv(proc / "forecast_results.csv")

    second = _run(synthetic_processed)
    second_results = pd.read_csv(proc / "forecast_results.csv")

    # Byte-identical metric artifacts (NFR-01).
    assert first.artifacts["analysis"]["artifacts"] == second.artifacts["analysis"]["artifacts"]

    # Forecast numbers must reproduce; run_id/timestamps legitimately differ.
    numeric = [
        "company",
        "target_period",
        "horizon",
        "point",
        "interval_low_80",
        "interval_high_80",
        "interval_low_95",
        "interval_high_95",
        "status",
    ]
    pd.testing.assert_frame_equal(first_results[numeric], second_results[numeric])


def test_pulse_failure_does_not_destroy_metric_artifacts(synthetic_processed, monkeypatch):
    def explode(*args, **kwargs):
        raise RuntimeError("simulated model failure")

    monkeypatch.setattr(orchestrate, "run_pulse", explode)
    result = _run(synthetic_processed)

    proc = synthetic_processed / "processed"
    assert (proc / "analysis_results.csv").exists()
    assert not pd.read_csv(proc / "analysis_results.csv").empty
    assert result.stages["forecast"] == "failed"
    assert any("pulse stage failed" in warning for warning in result.warnings)
    assert result.status in {"partial", "success"}


def test_missing_panel_fails_cleanly(tmp_path):
    result = run_analysis_cycle(
        data_dir=tmp_path,
        out_dir=tmp_path / "processed",
        publish_dir=tmp_path / "web" / "data",
    )
    assert result.status == "failed"
    assert result.stages["load"] == "failed"
    health = json.loads((tmp_path / "quality" / "health.json").read_text(encoding="utf-8"))
    assert health["status"] == "failed"


def test_health_file_records_stage_timings(synthetic_processed):
    _run(synthetic_processed)
    health = json.loads((synthetic_processed / "quality" / "health.json").read_text(encoding="utf-8"))
    assert health["stages"]["compute"] == "ok"
    assert health["duration_seconds"] >= 0
    assert health["freshness"]["sla"] == "none"
