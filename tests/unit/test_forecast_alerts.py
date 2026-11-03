"""Alert rules and gating (FCST-09, NFR-15)."""

from aicor.compute.config import load_analysis_config
from aicor.forecast.alerts import alert_precision, evaluate_alerts

CFG = load_analysis_config()


def _result(**overrides):
    base = {
        "company": "MSFT",
        "target_period": "2026Q3",
        "horizon": 0,
        "point": -0.8,
        "interval_low_80": -1.6,
        "interval_high_80": -0.1,
        "as_of_date": "2026-07-29",
        "forecast_result_id": "R-1",
        "quality_gate_passed": True,
    }
    base.update(overrides)
    return base


def test_alerts_are_suppressed_when_gate_fails():
    alerts = evaluate_alerts([_result()], run_id="run-1", config=CFG, gate_passed=False)
    assert alerts
    assert {a["status"] for a in alerts} == {"suppressed"}
    assert all("quality gate" in a["message"] for a in alerts)


def test_e_below_threshold_rule_triggers():
    alerts = evaluate_alerts([_result(point=-0.9)], run_id="run-1", config=CFG, gate_passed=True)
    rule = next(a for a in alerts if a["rule_id"] == "e_below_threshold")
    assert rule["status"] == "open"
    assert rule["severity"] == "CRITICAL"


def test_interval_crossing_zero_triggers():
    alerts = evaluate_alerts(
        [_result(point=0.1, interval_low_80=-0.5, interval_high_80=0.8)],
        run_id="run-1",
        config=CFG,
        gate_passed=True,
    )
    rule = next(a for a in alerts if a["rule_id"] == "interval_crosses_zero")
    assert rule["status"] == "open"
    rule_b = next(a for a in alerts if a["rule_id"] == "e_below_threshold")
    assert rule_b["status"] == "closed"


def test_nowcast_deviation_rule_uses_last_published_e():
    alerts = evaluate_alerts(
        [_result(point=0.5, interval_low_80=-0.2, interval_high_80=1.0)],
        run_id="run-1",
        config=CFG,
        gate_passed=True,
        last_published_e={"MSFT": -1.0},
    )
    rule = next(a for a in alerts if a["rule_id"] == "nowcast_deviation")
    assert rule["status"] == "open"
    assert rule["severity"] == "INFO"


def test_alert_ids_are_deterministic_and_auditable():
    first = evaluate_alerts([_result()], run_id="run-1", config=CFG, gate_passed=True)
    second = evaluate_alerts([_result()], run_id="run-1", config=CFG, gate_passed=True)
    assert [a["alert_id"] for a in first] == [a["alert_id"] for a in second]
    for alert in first:
        assert alert["model_run_id"] == "run-1"
        assert alert["forecast_result_id"] == "R-1"
        assert alert["as_of_date"] == "2026-07-29"


def test_binary_alert_precision_reports_insufficient_evidence_below_three_triggers():
    import pandas as pd

    folds = pd.DataFrame(
        [
            {"model": "naive", "predicted": -0.5, "actual": -0.4},
            {"model": "naive", "predicted": 0.5, "actual": 0.6},
        ]
    )
    report = alert_precision(folds, threshold=-0.25)
    assert report["status"] == "insufficient_evidence"
    assert report["precision"] is None
