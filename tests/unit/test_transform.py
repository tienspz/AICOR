"""Tests for transformation module (Task 9).

Key invariant: Q4 = FY − 9M, NEVER the raw 3M fact for the 4th quarter.
"""

import pandas as pd
import pytest

from aicor.preprocess.transform import (
    DerivationError,
    align_calendar,
    normalize_units,
    period_end_to_calendar_quarter,
    ytd_to_quarterly,
)


def test_q4_never_uses_3m_fact():
    """Q4 must be FY − 9M (SPEC §6.2)."""
    q = ytd_to_quarterly({"3M": 10.0, "6M": 22.0, "9M": 35.0, "FY": 50.0})
    assert q == {"Q1": 10.0, "Q2": 12.0, "Q3": 13.0, "Q4": 15.0}


def test_ytd_raises_without_fy():
    with pytest.raises(DerivationError, match="FY"):
        ytd_to_quarterly({"3M": 10.0, "6M": 22.0, "9M": 35.0})


def test_ytd_raises_without_9m():
    with pytest.raises(DerivationError, match="9M"):
        ytd_to_quarterly({"3M": 10.0, "6M": 22.0, "FY": 50.0})


def test_align_calendar_adds_quarter():
    df = pd.DataFrame({
        "period_end_date": ["2024-06-30", "2024-12-31"],
        "company": ["MSFT", "GOOGL"],
    })
    out = align_calendar(df)
    assert "calendar_quarter" in out.columns
    assert "year" in out.columns
    # June 30 → Q2, Dec 31 → Q4
    assert out.loc[0, "calendar_quarter"] == 2
    assert out.loc[1, "calendar_quarter"] == 4


def test_align_calendar_msft_googl_same_quarter():
    """MSFT FY Q4 (Jun 30) and GOOGL Q2 (Jun 30) both → calendar Q2."""
    df = pd.DataFrame({
        "period_end_date": ["2024-06-30", "2024-06-30"],
        "company": ["MSFT", "GOOGL"],
        "fiscal_period": ["FY24-Q4", "2024-Q2"],  # display only
    })
    out = align_calendar(df)
    assert out.loc[0, "calendar_quarter"] == out.loc[1, "calendar_quarter"]


def test_period_end_to_calendar_quarter():
    from datetime import date
    assert period_end_to_calendar_quarter(date(2024, 6, 30)) == (2024, 2)
    assert period_end_to_calendar_quarter(date(2024, 12, 31)) == (2024, 4)
    assert period_end_to_calendar_quarter(date(2024, 3, 31)) == (2024, 1)
    assert period_end_to_calendar_quarter(date(2024, 9, 30)) == (2024, 3)


def test_normalize_units_raw_to_millions():
    df = pd.DataFrame({"revenue": [64_727_000_000.0]})
    out = normalize_units(df)
    assert abs(out.loc[0, "revenue"] - 64_727.0) < 0.01
