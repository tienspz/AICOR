"""Tests for the metric primitives (SPEC §7.1, §7.2, §7.3, §7.5)."""

import numpy as np
import pandas as pd
import pytest

from aicor.compute.metrics import (
    STATUS_DEGENERATE,
    STATUS_INSUFFICIENT_OBSERVATIONS,
    STATUS_INSUFFICIENT_WINDOW,
    STATUS_OK,
    STATUS_UNAVAILABLE,
    combine_out,
    compute_e,
    ma4q,
    product_score,
    rolling_z,
    sign_robustness,
)


def test_product_score_uses_rubric_weights():
    assert product_score({"A": 2, "B": 1, "C": 3}) == 6 + 2 + 3
    assert product_score({"A": 0, "B": 0, "C": 0}) == 0


def test_ma4q_strict_four_quarters():
    series = pd.Series([1.0, 2.0, 3.0])
    assert ma4q(series).isna().all()

    series = pd.Series([1.0, 2.0, 3.0, 4.0, 6.0])
    rolling = ma4q(series)
    assert pytest.approx(rolling.iloc[-1]) == (2 + 3 + 4 + 6) / 4


def test_rolling_z_flags_insufficient_window_and_emits_no_value():
    values = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    result = rolling_z(values, window=16, min_quarters=16)
    assert result.status[0] == STATUS_INSUFFICIENT_WINDOW
    assert np.isnan(result.values[0])
    assert all(status == STATUS_INSUFFICIENT_WINDOW for status in result.status)


def test_rolling_z_ok_once_window_is_full():
    values = pd.Series(np.arange(1, 21, dtype=float))
    result = rolling_z(values, window=16, min_quarters=16)
    assert result.status[14] == STATUS_INSUFFICIENT_WINDOW
    assert result.status[15] == STATUS_OK
    assert result.n_observations[15] == 16
    # Value is (16 - mean(1..16)) / std(1..16, ddof=1) — the newest point of a ramp.
    window = np.arange(1, 17, dtype=float)
    assert result.values[15] == pytest.approx((16 - window.mean()) / window.std(ddof=1))


def test_rolling_z_uses_trailing_window_not_expanding_history():
    values = pd.Series([1.0] * 16 + [10.0] * 4)
    result = rolling_z(values, window=16, min_quarters=16)
    # Only the last 16 values may enter mean/std; the first four 1.0s drop out.
    window = np.array([1.0] * 14 + [10.0] * 2)
    expected = (10.0 - window.mean()) / window.std(ddof=1)
    assert result.status[17] == STATUS_OK
    assert result.values[17] == pytest.approx(expected)
    assert result.n_observations[17] == 16


def test_rolling_z_degenerate_std_zero():
    values = pd.Series([5.0] * 16)
    result = rolling_z(values, window=16, min_quarters=16)
    assert result.status[-1] == STATUS_DEGENERATE
    assert result.values[-1] == 0.0


def test_rolling_z_unavailable_value():
    values = pd.Series([np.nan] + [1.0 + i for i in range(15)])
    result = rolling_z(values, window=16, min_quarters=16)
    assert result.status[0] == STATUS_UNAVAILABLE
    assert np.isnan(result.values[0])


def test_rolling_z_insufficient_observations():
    values = pd.Series([np.nan] * 14 + [1.0, 2.0])
    result = rolling_z(values, window=16, min_quarters=16, min_observations=4)
    assert result.status[-1] == STATUS_INSUFFICIENT_OBSERVATIONS
    assert np.isnan(result.values[-1])


def test_combine_out_and_compute_e():
    out = combine_out(1.0, -0.5, product_weight=0.6, trends_weight=0.4)
    assert out == pytest.approx(0.4)
    assert compute_e(out, 0.1) == pytest.approx(0.3)
    assert compute_e(None, 0.1) is None
    assert compute_e(float("nan"), 0.1) is None


def test_sign_robustness():
    assert sign_robustness([1.0, 2.0, 0.5]) == "ROBUST"
    assert sign_robustness([1.0, -0.2, 0.5]) == "SENSITIVE"
    assert sign_robustness([None, 1.0]) is None
    assert sign_robustness([None, None, None]) is None
