"""Transformation / Reshaping — YTD→Q, calendar alignment, unit normalization.

Implements: Lecture 07 slide 3/5, SPEC §6.2, §7.2, DAT-01.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import numpy as np
import pandas as pd


# ---------- Exceptions ----------

class DerivationError(Exception):
    """Raised when a required input for derivation is missing."""


# ---------- YTD → Quarterly ----------

def ytd_to_quarterly(ytd: dict[str, float]) -> dict[str, float]:
    """Convert YTD cumulative figures to standalone quarterly figures.

    Input keys: ``"3M"``, ``"6M"``, ``"9M"``, ``"FY"``
    Output keys: ``"Q1"``, ``"Q2"``, ``"Q3"``, ``"Q4"``

    Q4 is ALWAYS ``FY − 9M`` — never the raw 3M fact for the 4th quarter.
    Raises :class:`DerivationError` if ``FY`` or ``9M`` is missing.
    """
    if "FY" not in ytd or ytd["FY"] is None:
        raise DerivationError("Cannot derive Q4 without FY value")
    if "9M" not in ytd or ytd["9M"] is None:
        raise DerivationError("Cannot derive Q4 without 9M value")

    q1 = ytd.get("3M")
    if q1 is None:
        raise DerivationError("Cannot derive Q1 without 3M value")

    q2 = ytd.get("6M")
    if q2 is None:
        raise DerivationError("Cannot derive Q2 without 6M value")

    return {
        "Q1": q1,
        "Q2": q2 - q1,
        "Q3": ytd["9M"] - q2,
        "Q4": ytd["FY"] - ytd["9M"],
    }


# ---------- Calendar alignment (DAT-01) ----------

# MSFT fiscal year ends June 30 → Q1=Jul-Sep, Q2=Oct-Dec, Q3=Jan-Mar, Q4=Apr-Jun
# GOOGL fiscal year = calendar year → Q1=Jan-Mar, Q2=Apr-Jun, Q3=Jul-Sep, Q4=Oct-Dec
# DAT-01: period_end_date is the cross-comparison key, fiscal_period is display only.

def align_calendar(df: pd.DataFrame) -> pd.DataFrame:
    """Add ``period_end_date``, ``calendar_quarter``, ``year`` columns.

    Derives from existing date column (``period_end_date`` or ``end_date``).
    This is the join key for cross-company comparison (DAT-01).
    """
    df = df.copy()

    # Find the date column
    date_col = None
    for candidate in ("period_end_date", "end_date", "date"):
        if candidate in df.columns:
            date_col = candidate
            break

    if date_col is None:
        return df  # no date to align

    # Ensure datetime
    df[date_col] = pd.to_datetime(df[date_col])

    # Derive calendar_quarter and year from the actual date
    df["period_end_date"] = df[date_col]
    df["year"] = df[date_col].dt.year
    # Calendar quarter based on month
    df["calendar_quarter"] = df[date_col].dt.quarter

    return df


def period_end_to_calendar_quarter(period_end: date) -> tuple[int, int]:
    """Return (year, calendar_quarter) from a period_end date.

    >>> period_end_to_calendar_quarter(date(2024, 6, 30))
    (2024, 2)
    >>> period_end_to_calendar_quarter(date(2024, 12, 31))
    (2024, 4)
    """
    return (period_end.year, (period_end.month - 1) // 3 + 1)


# ---------- Unit normalization ----------

def normalize_units(df: pd.DataFrame, target_scale: str = "millions") -> pd.DataFrame:
    """Normalize monetary values to USD millions.

    Looks for a ``unit_scale`` column to determine current scale.
    If absent, assumes values are already in raw USD (divides by 1_000_000).
    """
    df = df.copy()
    monetary_cols = [
        "revenue", "rd_expense", "capex", "operating_income", "net_income",
        "cfo", "assets", "liabilities", "equity",
    ]

    if "unit_scale" in df.columns:
        for idx in df.index:
            scale = df.at[idx, "unit_scale"]
            divisor = _scale_to_divisor(scale, target_scale)
            for col in monetary_cols:
                if col in df.columns and pd.notna(df.at[idx, col]):
                    df.at[idx, col] = df.at[idx, col] / divisor
    else:
        # Assume raw USD → millions
        for col in monetary_cols:
            if col in df.columns:
                df[col] = df[col] / 1_000_000

    if "unit_scale" not in df.columns:
        df["unit_scale"] = target_scale

    return df


def _scale_to_divisor(current: str, target: str) -> float:
    """Return the divisor to convert *current* scale to *target* scale."""
    scales = {
        "raw": 1,
        "thousands": 1_000,
        "millions": 1_000_000,
        "billions": 1_000_000_000,
    }
    current_val = scales.get(str(current).lower(), 1)
    target_val = scales.get(str(target).lower(), 1_000_000)
    return current_val / target_val
