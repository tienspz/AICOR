"""Tests for missing-value policy (Task 8).

Core invariant: value = NULL, status = 'unavailable', reason non-empty.
NEVER fill zero (SRC-05).
"""

import numpy as np
import pandas as pd

from aicor.preprocess.missing import mark_missing


def test_missing_never_zero_filled():
    """SRC-05: missing data → NULL + 'unavailable' + reason."""
    df = pd.DataFrame({"rd_expense": [None]})
    out = mark_missing(df, value_columns=["rd_expense"], reason_col="reason")
    assert pd.isna(out.loc[0, "rd_expense"])  # still NULL, not 0
    assert out.loc[0, "status"] == "unavailable"
    assert out.loc[0, "reason"] != ""


def test_available_data_not_touched():
    df = pd.DataFrame({"rd_expense": [1000.0]})
    out = mark_missing(df, value_columns=["rd_expense"])
    assert out.loc[0, "rd_expense"] == 1000.0
    assert out.loc[0, "status"] == "available"


def test_multiple_missing_columns():
    df = pd.DataFrame({
        "revenue": [100.0, np.nan],
        "rd_expense": [np.nan, 50.0],
    })
    out = mark_missing(df, value_columns=["revenue", "rd_expense"])
    # Row 0: rd_expense missing
    assert out.loc[0, "status"] == "unavailable"
    # Row 1: revenue missing
    assert out.loc[1, "status"] == "unavailable"
