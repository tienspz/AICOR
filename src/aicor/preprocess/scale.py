"""Scaling / Normalization + Outlier detection.

Implements: Lecture 07 slide 4/5, 5/5, SPEC §7.2–§7.3, §7.5.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


# ---------- MA4Q (§7.2: 4-quarter moving average) ----------

def ma4q(
    s: pd.Series,
    min_periods: int = 4,
) -> pd.Series:
    """4-quarter moving average. Returns NaN when fewer than *min_periods* values.

    §7.2: MA4Q requires exactly 4 quarters. No shorter window allowed.
    """
    return s.rolling(window=4, min_periods=min_periods).mean()


# ---------- Min-max 16Q (Trends normalization) ----------

def minmax_16q(s: pd.Series) -> pd.Series:
    """Min-max normalize over a rolling 16-quarter window.

    For Trends data — maps to [0, 1] within the window.
    """
    rolling_min = s.rolling(window=16, min_periods=1).min()
    rolling_max = s.rolling(window=16, min_periods=1).max()
    denom = rolling_max - rolling_min
    # Avoid division by zero
    denom = denom.replace(0, np.nan)
    return (s - rolling_min) / denom


# ---------- Z-score 16Q (§7.3, §7.5) ----------

def zscore_16q(
    s: pd.Series,
    window: int = 16,
) -> tuple[pd.Series, pd.Series]:
    """Rolling z-score over *window* quarters.

    Returns ``(z_scores, status_series)`` where:
    - ``status = "ok"`` — normal z-score computed
    - ``status = "degenerate"`` — ``std == 0`` → ``z = 0`` (§7.5: no division by zero)
    - ``status = "insufficient_window"`` — fewer than *window* observations
      (value still computed with available data + flag for retrospective review §7.3)

    Uses ``ddof=1`` (sample std).
    """
    rolling_mean = s.rolling(window=window, min_periods=1).mean()
    rolling_std = s.rolling(window=window, min_periods=1).std(ddof=1)

    z = pd.Series(np.zeros(len(s)), index=s.index, dtype=float)
    status = pd.Series("ok", index=s.index)

    for i in range(len(s)):
        count = s.iloc[max(0, i - window + 1):i + 1].notna().sum()
        std_val = rolling_std.iloc[i]
        mean_val = rolling_mean.iloc[i]

        if pd.isna(s.iloc[i]):
            z.iloc[i] = np.nan
            status.iloc[i] = "unavailable"
        elif std_val == 0 or pd.isna(std_val):
            z.iloc[i] = 0.0
            status.iloc[i] = "degenerate"
        else:
            z.iloc[i] = (s.iloc[i] - mean_val) / std_val
            if count < window:
                status.iloc[i] = "insufficient_window"
            else:
                status.iloc[i] = "ok"

    return z, status


# ---------- Outlier detection (IQR on QoQ-delta) ----------

def flag_outliers(
    s: pd.Series,
    method: str = "iqr",
    iqr_multiplier: float = 1.5,
) -> pd.Series:
    """Flag outliers using IQR on quarter-over-quarter delta.

    Returns a boolean Series (True = outlier).

    NOTE: Outliers are FLAGGED into ``data_quality_log``, NEVER deleted
    (Lecture 07 slide p16 — "outlier vs noise": restatement with new filing
    is legitimate; parse error is noise. Both are flagged, not removed).
    """
    delta = s.diff()

    q1 = delta.quantile(0.25)
    q3 = delta.quantile(0.75)
    iqr = q3 - q1

    lower = q1 - iqr_multiplier * iqr
    upper = q3 + iqr_multiplier * iqr

    return (delta < lower) | (delta > upper)
