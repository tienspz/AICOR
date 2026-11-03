"""Dashboard payload contract (Phase 3): every DSH view has its data, JSON-safe."""

import json

import pytest

from aicor.pipeline.orchestrate import run_analysis_cycle


@pytest.fixture
def payload(synthetic_processed):
    run_analysis_cycle(
        data_dir=synthetic_processed,
        out_dir=synthetic_processed / "processed",
        publish_dir=synthetic_processed / "web" / "data",
    )
    manifest = json.loads((synthetic_processed / "web" / "data" / "manifest.json").read_text(encoding="utf-8"))
    return json.loads((synthetic_processed / "web" / "data" / manifest["path"]).read_text(encoding="utf-8"))


def test_payload_is_strict_json(payload):
    # allow_nan=False fails on NaN/Infinity, which would break the browser.
    json.dumps(payload, allow_nan=False)


def test_meta_contains_methodology_and_disclaimers(payload):
    meta = payload["meta"]
    assert meta["schema_version"] == "dashboard-v1"
    assert {"In", "Out", "E", "ma4q", "units"} <= set(meta["methodology"])
    assert "ROI" in meta["disclaimers"]["e_score"]
    assert meta["zscore"]["min_quarters"] == 16
    assert {company["id"] for company in meta["companies"]} == {"MSFT", "GOOGL"}


def test_series_cover_every_quarter_with_provenance(payload):
    for company in ("MSFT", "GOOGL"):
        rows = payload["series"][company]
        assert len(rows) == 20
        assert all(row["source_id"].startswith("SEC-") for row in rows)
        assert all(row["source_url"].startswith("https://") for row in rows)
        assert any(row["E"] is None for row in rows), "early quarters must be NULL, not zero"
        assert any(row["E"] is not None for row in rows)


def test_dsh03_and_dsh06_data_present(payload):
    assert payload["events"], "timeline needs events"
    assert {event["category"] for event in payload["events"]} <= {"A", "B", "C"}
    assert payload["market"]["MSFT"], "market context needs price rows"


def test_dsh05_status_section(payload):
    status = payload["status"]
    assert status["data_status"] in {"success", "partial", "failed"}
    assert status["coverage"]["MSFT"]["quarters_in_panel"] == 20
    assert "freshness" in status
    assert status["freshness"]["sla"] == "none"


def test_dsh07_pulse_section_is_complete(payload):
    pulse = payload["pulse"]
    assert pulse["available"] is True
    assert pulse["gate"]["checks"], "gate must report per-horizon checks"
    assert pulse["results"], "pulse must emit results for audit even when gated"
    for result in pulse["results"]:
        assert result["model_version"]
        assert result["as_of_date"]
        assert result["interval_low_80"] is not None or result["status"] == "insufficient_evidence"
        assert result["quality_gate_passed"] in (True, False)
    assert pulse["model_card"]["artifact_hash"]
    assert pulse["model_card"]["limitations"]
    assert "không phải khuyến nghị đầu tư" in pulse["disclaimer"].lower()


def test_attribution_is_labelled_as_non_causal(payload):
    note = payload["pulse"]["attribution_note"].lower()
    assert "nhân quả" in note
    assert "không phải" in note


def test_dsh04_scenarios_are_exposed(payload):
    for company in ("MSFT", "GOOGL"):
        rows = payload["series"][company]
        assert any(row["E_simple"] is not None for row in rows)
        assert any(row["E_tech"] is not None for row in rows)
        usable = [row for row in rows if row["E"] is not None]
        assert any(row["E"] != row["E_simple"] for row in usable)
        assert any(row["E"] != row["E_tech"] for row in usable)


def test_series_delta_uses_previous_valid_quarter(payload):
    rows = payload["series"]["MSFT"]
    valid = [row for row in rows if row["E"] is not None]
    assert valid[0]["E_delta_prev"] is None
    assert valid[0]["prev_quarter"] is None
    for previous, current in zip(valid, valid[1:]):
        assert current["prev_quarter"] == previous["quarter"]
        assert current["E_delta_prev"] == pytest.approx(current["E"] - previous["E"], abs=1e-6)


def test_coverage_reasons_exclude_ok_and_quarters_are_sorted(payload):
    for company in ("MSFT", "GOOGL"):
        coverage = payload["status"]["coverage"][company]
        assert "ok" not in coverage["missing_reasons"]
        quarters = [row["quarter"] for row in payload["series"][company]]
        assert quarters == sorted(quarters)
        assert coverage["first_quarter"] == quarters[0]
        assert coverage["last_quarter"] == quarters[-1]
        assert coverage["first_valid_quarter"] == next(
            row["quarter"] for row in payload["series"][company] if row["E"] is not None
        )


def test_meta_exposes_forecast_parameters_and_market_method(payload):
    forecast = payload["meta"]["forecast"]
    assert forecast["conformal_window"] == 8
    assert forecast["interval_levels"] == [0.8, 0.95]
    assert forecast["model"]
    assert forecast["horizons"] == [0, 1]
    assert "trung bình" in payload["meta"]["methodology"]["market"].lower()
