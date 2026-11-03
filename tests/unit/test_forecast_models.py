"""Model behaviour: determinism, intervals, attribution (FCST-05, FCST-07, FCST-10)."""

import numpy as np
import pandas as pd
import pytest

from aicor.compute.config import load_analysis_config
from aicor.forecast.models import (
    MODEL_NAIVE,
    conformal_half_widths,
    fit_ar1,
    fit_predict,
    fit_ridge,
    predict_ridge,
)
from aicor.forecast.snapshot import FEATURE_COLUMNS, build_samples


@pytest.fixture
def samples(series_frame_fixture):
    return build_samples(series_frame_fixture, config=load_analysis_config())


def test_ridge_is_deterministic(samples):
    train = samples[samples["horizon"] == 0]
    first = fit_ridge(train, alpha_grid=(0.1, 1.0))
    second = fit_ridge(train, alpha_grid=(0.1, 1.0))
    assert first.coefficients == second.coefficients
    assert first.alpha == second.alpha


def test_ridge_contributions_reconstruct_the_prediction(samples):
    train = samples[samples["horizon"] == 0]
    fit = fit_ridge(train, alpha_grid=(0.1, 1.0))
    row = train.iloc[-1]
    prediction, contributions = predict_ridge(fit, row)
    total = sum(float(c["contribution"]) for c in contributions)
    # Contributions are rounded to 6 decimals for display/attribution.
    assert prediction == pytest.approx(fit.intercept + total, abs=1e-5)


def test_attribution_is_ranked_by_absolute_contribution(samples):
    train = samples[samples["horizon"] == 0]
    _, contributions = predict_ridge(fit_ridge(train), train.iloc[0])
    magnitudes = [abs(float(c["contribution"])) for c in contributions]
    assert magnitudes == sorted(magnitudes, reverse=True)


def test_naive_prediction_persists_origin():
    train = pd.DataFrame(
        {
            "target": [1.0, 2.0, 3.0, 2.5],
            "e_lag1": [0.5, 1.5, 2.5, 2.0],
            **{name: 0.0 for name in FEATURE_COLUMNS if name not in {"e_lag1"}},
        }
    )
    row = train.iloc[-1]
    prediction = fit_predict(train, row, model=MODEL_NAIVE)
    assert prediction.value == pytest.approx(float(row["e_lag1"]))


def test_ar1_recovers_a_linear_relationship():
    x = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    train = pd.DataFrame(
        {
            "target": 2.0 + 1.5 * x,
            "e_lag1": x,
            **{name: 0.0 for name in FEATURE_COLUMNS if name != "e_lag1"},
        }
    )
    a, b = fit_ar1(train)
    assert a == pytest.approx(2.0, abs=1e-6)
    assert b == pytest.approx(1.5, abs=1e-6)


def test_conformal_widths_are_monotonic():
    residuals = np.array([0.1, -0.3, 0.4, -0.2, 0.5, -0.6, 0.05, -0.15])
    widths, method = conformal_half_widths(residuals, levels=(0.8, 0.95))
    assert method == "split_conformal"
    assert widths["95"] >= widths["80"] >= 0


def test_conformal_falls_back_and_says_so():
    widths, method = conformal_half_widths(np.array([0.2, -0.1]), levels=(0.8, 0.95))
    assert method == "normal_fallback"
    assert widths["95"] > widths["80"]


def test_predictions_always_carry_intervals(samples):
    train = samples[samples["horizon"] == 0]
    prediction = fit_predict(train, train.iloc[-1], model="ridge")
    assert prediction.interval_low_80 < prediction.value < prediction.interval_high_80
    assert prediction.interval_low_95 <= prediction.interval_low_80
    assert prediction.interval_high_95 >= prediction.interval_high_80
