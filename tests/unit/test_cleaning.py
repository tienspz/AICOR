"""Tests for cleaning module (Task 8)."""

import numpy as np
import pandas as pd

from aicor.preprocess.cleaning import clean_financial


def test_clean_coerces_numeric():
    df = pd.DataFrame({"revenue": ["1000", "2000", "bad"], "name": ["a", "b", "c"]})
    out = clean_financial(df)
    assert out["revenue"].dtype == np.float64
    # "bad" → NaN, but row has "name" so it stays (not all-NaN in value cols)


def test_clean_strips_whitespace():
    df = pd.DataFrame({"revenue": [100.0], "name": ["  MSFT  "]})
    out = clean_financial(df)
    assert out["name"].iloc[0] == "MSFT"


def test_clean_drops_all_nan_rows():
    df = pd.DataFrame({
        "revenue": [100.0, np.nan],
        "rd_expense": [50.0, np.nan],
    })
    out = clean_financial(df)
    assert len(out) == 1
