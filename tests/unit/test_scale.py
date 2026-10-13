"""Tests for scaling/normalization module (Task 11).

Key invariants:
- std=0 → z=0, status="degenerate" (§7.5)
- <4 quarters → MA4Q returns NaN (§7.2)
"""

import numpy as np
import pandas as pd

from aicor.preprocess.scale import flag_outliers, ma4q, minmax_16q, zscore_16q


def test_zscore_degenerate():
    """§7.5: constant series → std=0 → z=0, status='degenerate'."""
    s = pd.Series([5.0] * 16)
    z, st = zscore_16q(s)
    assert (z == 0.0).all()
    assert (st == "degenerate").all()


def test_ma4q_strict_minimum():
    """§7.2: fewer than 4 quarters → NaN (no short MA)."""
    s = pd.Series([1.0, 2.0, 3.0])
    result = ma4q(s)
    assert result.isna().all()


def test_ma4q_4_quarters():
    s = pd.Series([1.0, 2.0, 3.0, 4.0])
    result = ma4q(s)
    assert pd.notna(result.iloc[-1])
    assert abs(result.iloc[-1] - 2.5) < 1e-10


def test_zscore_insufficient_window():
    """§7.3: <16 observations → value computed + 'insufficient_window' flag."""
    s = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    z, st = zscore_16q(s, window=16)
    # Values should be computed (not NaN)
    assert pd.notna(z.iloc[-1])
    # But flagged as insufficient
    assert (st == "insufficient_window").any()


def test_zscore_normal():
    """Normal z-score with full window."""
    np.random.seed(42)
    s = pd.Series(np.random.normal(100, 10, 20))
    z, st = zscore_16q(s, window=16)
    # Last few should have status "ok" (full 16 observations)
    assert st.iloc[-1] == "ok"
    # z-scores should be roughly in [-3, 3] for normal data
    assert z.iloc[-1] > -4 and z.iloc[-1] < 4


def test_minmax_16q():
    s = pd.Series(range(20), dtype=float)
    normed = minmax_16q(s)
    # Last value should be close to 1.0 (max in window)
    assert abs(normed.iloc[-1] - 1.0) < 1e-10


def test_flag_outliers_returns_bool():
    s = pd.Series([1, 2, 3, 4, 5, 100, 6, 7, 8], dtype=float)
    flags = flag_outliers(s)
    assert flags.dtype == bool
    # The jump to 100 should be flagged
    assert flags.iloc[5] == True  # noqa: E712
