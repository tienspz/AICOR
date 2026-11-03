"""Tests for the In/Out/E engine and the feature matrix (SPEC §7.4)."""

import numpy as np
import pandas as pd
import pytest

from aicor.compute.config import load_analysis_config
from aicor.compute.engine import ANALYSIS_COLUMNS, compute_analysis, compute_scenarios, series_frame
from aicor.compute.features import build_feature_matrix, to_long_features


@pytest.fixture
def features(synthetic_processed):
    from tests.conftest import build_panel, build_products, build_trends

    cfg = load_analysis_config()
    return build_feature_matrix(
        build_panel(), build_products(), build_trends(), config=cfg
    )


def test_feature_matrix_has_one_row_per_company_quarter(features):
    assert len(features) == 40
    assert features.groupby("company").size().to_dict() == {"GOOGL": 20, "MSFT": 20}


def test_z_scores_are_unusable_before_window(features):
    early = features[features["calendar_quarter"] == "2021Q1"].iloc[0]
    assert early["z_in_status"] == "insufficient_window"
    assert np.isnan(early["z_in"])


def test_e_equals_out_minus_in(series_frame_fixture):
    rows = series_frame_fixture.dropna(subset=["E"])
    assert len(rows) > 0
    for _, row in rows.iterrows():
        assert row["E"] == pytest.approx(row["Out"] - row["In"], abs=1e-9)


def test_out_matches_configured_weights(features):
    cfg = load_analysis_config()
    scenarios = compute_scenarios(features, cfg)
    usable = scenarios.dropna(subset=["Out_baseline"])
    assert len(usable) > 0
    for _, row in usable.iterrows():
        source = features[
            (features["company"] == row["company"]) & (features["calendar_quarter"] == row["calendar_quarter"])
        ].iloc[0]
        expected = 0.6 * source["z_product_ma4q"] + 0.4 * source["z_trends_ma4q"]
        assert row["Out_baseline"] == pytest.approx(expected, abs=1e-9)


def test_scenarios_differ_but_share_in(features):
    scenarios = compute_scenarios(features, load_analysis_config()).dropna(subset=["E_baseline"])
    # Product-heavy weighting gives a different E than equal weighting here.
    assert not scenarios["E_baseline"].equals(scenarios["E_tech"])
    assert scenarios["E_simple"].notna().all()


def test_e_is_null_when_a_component_is_missing():
    cfg = load_analysis_config()
    panel = pd.DataFrame(
        {
            "period_end_date": pd.date_range("2025-01-31", periods=16, freq="QE-JAN").astype(str),
            "company": "MSFT",
            "source_id": [f"SEC-MSFT-{i}" for i in range(16)],
            "revenue": 1000.0,
            "rd_expense": np.linspace(100, 200, 16),
            "capex": 100.0,
            "year": 2025,
            "calendar_quarter": [((i % 4) + 1) for i in range(16)],
        }
    )
    features = build_feature_matrix(panel, None, None, config=cfg)
    scenarios = compute_scenarios(features, cfg)
    # No Trends data at all -> Out and E must stay NULL, never 0.
    assert scenarios["Out_baseline"].isna().all()
    assert scenarios["E_baseline"].isna().all()


def test_analysis_schema_and_status_vocabulary(features):
    analysis = compute_analysis(features, load_analysis_config())
    assert list(analysis.columns) == ANALYSIS_COLUMNS
    assert set(analysis["status"]) <= {
        "ok",
        "unavailable",
        "insufficient_window",
        "insufficient_observations",
        "degenerate",
    }
    ok_rows = analysis[analysis["status"] == "ok"]
    assert ok_rows["value"].notna().all()
    null_rows = analysis[analysis["value"].isna()]
    assert (null_rows["reason"] != "").all(), "NULL rows must carry a reason (SRC-05)"


def test_analysis_provenance_columns_populated(features):
    analysis = compute_analysis(features, load_analysis_config())
    assert analysis["source_id"].str.startswith("SEC-").all()
    assert analysis["source_url"].str.startswith("https://").all()
    assert analysis["config_version"].nunique() == 1
    assert analysis["formula_version"].nunique() == 1


def test_long_features_follow_spec_schema(features):
    long = to_long_features(features, load_analysis_config())
    required = {
        "feature_id",
        "company",
        "period_end_date",
        "feature",
        "value",
        "unit",
        "definition",
        "calculation_method",
        "reported_or_derived",
        "proxy",
        "confidence",
        "source_id",
        "status",
        "reason",
        "config_version",
        "input_feature_ids",
    }
    assert required.issubset(set(long.columns))
    nulls = long[long["value"].isna()]
    assert (nulls["reason"] != "").all()


def test_computation_is_deterministic(synthetic_processed):
    from tests.conftest import build_panel, build_products, build_trends

    cfg = load_analysis_config()
    first = compute_analysis(build_feature_matrix(build_panel(), build_products(), build_trends(), config=cfg), cfg)
    second = compute_analysis(build_feature_matrix(build_panel(), build_products(), build_trends(), config=cfg), cfg)
    pd.testing.assert_frame_equal(first, second)


def test_series_frame_distinguishes_missing_from_zero(features):
    series = series_frame(features, load_analysis_config())
    early = series[series["calendar_quarter"] == "2021Q1"]
    assert early["E"].isna().all()
    assert (early["E_status"] == "insufficient_window").all()


def test_series_frame_exposes_every_scenario(features):
    series = series_frame(features, load_analysis_config())
    for column in (
        "Out_baseline",
        "Out_simple",
        "Out_tech",
        "E_baseline",
        "E_simple",
        "E_tech",
        "E_baseline_status",
        "E_simple_status",
        "E_tech_status",
    ):
        assert column in series.columns, f"missing scenario column {column}"

    usable = series.dropna(subset=["E_baseline", "E_simple", "E_tech"])
    assert not usable.empty, "fixture must contain at least one fully usable quarter"
    assert not usable["E_baseline"].equals(usable["E_simple"])
    assert not usable["E_baseline"].equals(usable["E_tech"])


def test_series_frame_keeps_baseline_aliases(features):
    series = series_frame(features, load_analysis_config())
    usable = series.dropna(subset=["E"])
    assert usable["E"].tolist() == usable["E_baseline"].tolist()
    assert usable["Out"].tolist() == usable["Out_baseline"].tolist()
    assert usable["E_status"].tolist() == usable["E_baseline_status"].tolist()


def test_series_frame_does_not_claim_sensitivity_without_scenarios():
    cfg = load_analysis_config()
    panel = pd.DataFrame(
        {
            "period_end_date": pd.date_range("2025-01-31", periods=16, freq="QE-JAN").astype(str),
            "company": "MSFT",
            "source_id": [f"SEC-MSFT-{i}" for i in range(16)],
            "revenue": 1000.0,
            "rd_expense": np.linspace(100, 200, 16),
            "capex": 100.0,
            "year": 2025,
            "calendar_quarter": [((i % 4) + 1) for i in range(16)],
        }
    )
    features = build_feature_matrix(panel, None, None, config=cfg)
    series = series_frame(features, cfg)
    assert series["E"].isna().all()
    assert series["E_robustness"].isna().all(), "missing E must not be labelled SENSITIVE"
