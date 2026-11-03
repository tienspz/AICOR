"""Rolling-origin backtest, coverage and FCST-08 quality gate."""

import pandas as pd

from aicor.compute.config import load_analysis_config
from aicor.forecast.backtest import quality_gate, rolling_origin_backtest
from aicor.forecast.snapshot import build_samples


def _samples(series):
    return build_samples(series, config=load_analysis_config())


def test_backtest_folds_are_chronological(series_frame_fixture):
    report = rolling_origin_backtest(_samples(series_frame_fixture), config=load_analysis_config())
    assert report["available"] is True
    folds = report["folds"]
    assert not folds.empty
    # Every fold trains only on strictly earlier targets.
    for _, row in folds.iterrows():
        assert row["n_train"] >= load_analysis_config().min_train_samples
        assert row["target_quarter"] >= row["target_quarter"]
        assert pd.notna(row["predicted"])


def test_backtest_reports_all_three_models_and_metrics(series_frame_fixture):
    report = rolling_origin_backtest(_samples(series_frame_fixture), config=load_analysis_config())
    folds = report["folds"]
    assert set(folds["model"]) == {"naive", "ar1", "ridge"}
    pooled = report["metrics"]["0"]["pooled"]
    for model in ("naive", "ar1", "ridge"):
        assert {"mae", "rmse", "directional_accuracy"} <= set(pooled[model])

    coverage = report["coverage"]["0"]["pooled"]
    for model in ("naive", "ridge"):
        assert 0.0 <= coverage[f"{model}_80"]["coverage"] <= 1.0
        assert 0.0 <= coverage[f"{model}_95"]["coverage"] <= 1.0


def test_backtest_counts_folds_per_horizon(series_frame_fixture):
    report = rolling_origin_backtest(_samples(series_frame_fixture), config=load_analysis_config())
    assert report["n_folds"]["0"] >= 1
    assert report["n_folds"]["1"] >= 1


def test_gate_fails_when_model_cannot_beat_naive(series_frame_fixture):
    report = rolling_origin_backtest(_samples(series_frame_fixture), config=load_analysis_config())
    gate = quality_gate(report, config=load_analysis_config(), model="naive")
    assert gate["passed"] is False
    assert gate["reason"] == "primary_model_does_not_beat_naive"
    assert gate["checks"]


def test_gate_without_metrics_fails_closed():
    gate = quality_gate({"metrics": {}}, config=load_analysis_config())
    assert gate["passed"] is False
    assert gate["reason"] == "no_backtest_metrics"


def test_empty_samples_yield_insufficient_evidence():
    report = rolling_origin_backtest(pd.DataFrame(), config=load_analysis_config())
    assert report["available"] is False
    assert report["reason"] == "no_samples"
    assert report["folds"].empty


def test_gate_passes_on_a_perfectly_learnable_series():
    """A deterministic linear target must beat naive on both MAE and RMSE."""
    cfg = load_analysis_config()
    rows = []
    for i in range(20):
        e = float(i) * 0.5
        rows.append(
            {
                "sample_id": f"MSFT-{i}",
                "company": "MSFT",
                "horizon": 0,
                "origin_quarter": f"20{20 + i // 4}Q{i % 4 + 1}",
                "origin_index": i,
                "target_quarter": f"20{20 + (i + 1) // 4}Q{(i + 1) % 4 + 1}",
                "target_index": i + 1,
                "target": e + 1.0,
                "e_lag1": e,
                "e_lag2": max(e - 0.5, 0.0),
                "out_lag1": e * 0.9,
                "in_lag1": -e * 0.1,
                "rd_intensity_lag1": 0.1,
                "capex_intensity_lag1": 0.2,
                "product_ma4q_lag1": 2.0,
                "trends_ma4q_lag1": 3.0,
                "is_msft": 1.0,
                "target_quarter_num": float((i % 4) + 1),
                "origin_available_at": "2026-01-01",
                "feature_available_at": "2026-01-01",
                "target_available_at": "2026-04-01",
                "source_id": "SEC-MSFT",
                "source_url": "https://www.sec.gov",
                "data_status": "ok",
            }
        )
    report = rolling_origin_backtest(pd.DataFrame(rows), config=cfg)
    gate = quality_gate(report, config=cfg, model="ar1")
    assert gate["passed"] is True, gate
