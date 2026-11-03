"""The analysis config must agree with the documented preprocessing baseline (NFR-03)."""

from pathlib import Path

import yaml

from aicor.compute.config import load_analysis_config


def test_versions_are_declared():
    cfg = load_analysis_config()
    assert cfg.version
    assert cfg.formula_version
    assert cfg.feature_set_version


def test_weights_match_baseline_document():
    cfg = load_analysis_config()
    baseline_path = Path("docs/decisions/baseline.yaml")
    if not baseline_path.exists():  # docs/ is gitignored in some checkouts
        return
    documented = yaml.safe_load(baseline_path.read_text(encoding="utf-8"))
    # docs/decisions/baseline.yaml names the scenarios baseline/sensitivity_1/2;
    # config/analysis.yaml names them baseline/simple/tech.
    names = {"baseline": "baseline", "sensitivity_1": "simple", "sensitivity_2": "tech"}
    for documented_name, weights in documented["weight_configs"].items():
        config_name = names[documented_name]
        assert cfg.weights[config_name]["product"] == weights["product_weight"]
        assert cfg.weights[config_name]["trends"] == weights["trends_weight"]


def test_zscore_and_ma4q_match_baseline_document():
    cfg = load_analysis_config()
    baseline_path = Path("docs/decisions/baseline.yaml")
    if not baseline_path.exists():
        return
    documented = yaml.safe_load(baseline_path.read_text(encoding="utf-8"))
    assert cfg.zscore_window == documented["z_window"]
    assert cfg.ma4q_min_periods == documented["ma4q_min_periods"]


def test_quality_gate_requires_beating_naive():
    cfg = load_analysis_config()
    assert cfg.quality_gate_require_both is True
    assert cfg.forecast_model in {"ridge", "elasticnet", "bayesian_ridge"}
    # SPEC §5 / FCST-05: no deep learning in the baseline.
    assert "deep" not in cfg.forecast_model.lower()
