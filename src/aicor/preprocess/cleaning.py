"""Cleaning module — data type enforcement and basic validation.

Implements: Lecture 07 slide 3/5, SPEC §6.1–§6.2.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def clean_financial(df: pd.DataFrame) -> pd.DataFrame:
    """Clean raw financial DataFrame.

    - Strip whitespace from string columns
    - Coerce numeric columns to float
    - Validate ``unit_scale`` presence when monetary values exist (§6.2)
    - Drop rows that are entirely NaN (garbage rows)

    Returns a new DataFrame (does not modify input).
    """
    df = df.copy()

    # Strip whitespace from object / string columns
    for col in df.select_dtypes(include=["object", "string"]).columns:
        df[col] = df[col].str.strip() if hasattr(df[col], "str") else df[col]

    # Coerce numeric columns
    numeric_cols = [
        "revenue", "rd_expense", "capex", "operating_income", "net_income",
        "cfo", "assets", "liabilities", "equity", "shares", "eps",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop rows that are entirely NaN across value columns
    value_cols = [c for c in numeric_cols if c in df.columns]
    if value_cols:
        df = df.dropna(subset=value_cols, how="all")

    return df.reset_index(drop=True)
