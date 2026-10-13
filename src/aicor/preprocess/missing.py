"""Missing-value policy — NULL + status + reason, NEVER fill zero.

Implements: Lecture 07 slide 4/5, SPEC SRC-05/SRC-07.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


# Canonical missing reasons (§6.1, SRC-05)
MISSING_REASONS = {
    "no_10q_q4_derived_later",
    "tag_absent",
    "trends_unavailable",
    "ir_pending_review",
    "source_not_yet_filed",
    "insufficient_data",
    "degenerate_std",
}


def mark_missing(
    df: pd.DataFrame,
    value_columns: list[str] | None = None,
    reason_col: str = "reason",
    status_col: str = "status",
    default_reason: str = "tag_absent",
) -> pd.DataFrame:
    """Mark missing values with ``status='unavailable'`` and a reason.

    NEVER fills 0 — SRC-05: ``value = NULL``, ``status = unavailable``,
    ``reason`` must be non-empty.

    Parameters
    ----------
    df : DataFrame
        Input data (copied, not mutated).
    value_columns : list[str] | None
        Columns to inspect for NaN/None. If None, inspects all numeric columns.
    reason_col, status_col : str
        Column names for the reason and status annotations.
    default_reason : str
        Default reason when the original reason is unknown.
    """
    df = df.copy()

    if value_columns is None:
        value_columns = list(df.select_dtypes(include=["number"]).columns)

    if status_col not in df.columns:
        df[status_col] = "available"
    if reason_col not in df.columns:
        df[reason_col] = ""

    for idx in df.index:
        for col in value_columns:
            if col in df.columns and pd.isna(df.at[idx, col]):
                df.at[idx, status_col] = "unavailable"
                # Preserve existing reason if set; otherwise use default
                existing = df.at[idx, reason_col]
                if not existing or (isinstance(existing, str) and not existing.strip()):
                    df.at[idx, reason_col] = default_reason

    return df
