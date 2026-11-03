"""Primitive metric functions for Phase 2 (SPEC §7.1–§7.5).

Every function is pure and deterministic: same input → same output, no
global state and no look-ahead. Status strings are the contract that the
dashboard renders; ``ok`` is the only status that may feed ``E``.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

STATUS_OK = "ok"
STATUS_UNAVAILABLE = "unavailable"
STATUS_INSUFFICIENT_WINDOW = "insufficient_window"
STATUS_INSUFFICIENT_OBSERVATIONS = "insufficient_observations"
STATUS_DEGENERATE = "degenerate"
STATUS_INSUFFICIENT_QUARTERS = "insufficient_ma4q_quarters"

USABLE_STATUSES = {STATUS_OK}


@dataclass(frozen=True)
class ZSeries:
    """Result of a rolling z-score: values + per-quarter status + n_obs."""

    values: np.ndarray
    status: list[str]
    n_observations: list[int]
    window: int
    min_quarters: int


def ma4q(values: pd.Series, min_periods: int = 4) -> pd.Series:
    """Strict 4-quarter moving average (SPEC §7.2).

    Returns NaN when fewer than *min_periods* quarters are available — a
    shorter window would silently change what the indicator means.
    """
    return values.rolling(window=4, min_periods=min_periods).mean()


def product_score(counts: dict[str, int], weights: dict[str, int] | None = None) -> int:
    """``3*A + 2*B + 1*C`` (SPEC §7.1). Counts for absent categories are 0."""
    w = weights or {"A": 3, "B": 2, "C": 1}
    return int(sum(int(w.get(cat, 0)) * int(count) for cat, count in counts.items()))


def rolling_z(
    values: pd.Series | np.ndarray,
    *,
    window: int = 16,
    min_quarters: int = 16,
    min_observations: int = 4,
    ddof: int = 1,
) -> ZSeries:
    """Trailing-window z-score with explicit status (SPEC §7.3, §7.5).

    Semantics
    ---------
    * The window is the trailing *window* quarters of the series (rows), not
      "the last N non-null values" — otherwise a sparse feature would quietly
      draw on quarters far outside the advertised window.
    * ``values[i]`` is NaN → ``unavailable``.
    * Fewer than *min_quarters* quarters of history → ``insufficient_window``
      and **no value** (NaN): SPEC §7.3 forbids using it for ``E``/forecast.
    * Fewer than *min_observations* non-null values inside the window →
      ``insufficient_observations`` and no value.
    * ``std == 0`` → ``degenerate``, emitted as ``z = 0`` per §7.5 and never
      treated as usable.
    """
    series = pd.Series(values, dtype="float64") if not isinstance(values, pd.Series) else values.astype("float64")
    arr = series.to_numpy(dtype=float)
    z = np.full(arr.shape, np.nan, dtype=float)
    status: list[str] = []
    n_obs: list[int] = []

    for i, current in enumerate(arr):
        lo = max(0, i - window + 1)
        window_vals = arr[lo : i + 1]
        available = window_vals[~np.isnan(window_vals)]
        n = int(available.size)
        n_obs.append(n)

        if np.isnan(current):
            status.append(STATUS_UNAVAILABLE)
            continue
        if (i - lo + 1) < min_quarters:
            status.append(STATUS_INSUFFICIENT_WINDOW)
            continue
        if n < max(2, min_observations):
            status.append(STATUS_INSUFFICIENT_OBSERVATIONS)
            continue

        std = float(available.std(ddof=ddof)) if n > ddof else float("nan")
        if np.isnan(std) or std == 0.0:
            z[i] = 0.0
            status.append(STATUS_DEGENERATE)
            continue

        z[i] = (current - float(available.mean())) / std
        status.append(STATUS_OK)

    return ZSeries(
        values=z,
        status=status,
        n_observations=n_obs,
        window=window,
        min_quarters=min_quarters,
    )


def combine_out(
    z_product: float,
    z_trends: float,
    *,
    product_weight: float,
    trends_weight: float,
) -> float:
    """``Out = w_product * z(Product MA4Q) + w_trends * z(Trends MA4Q)``."""
    return product_weight * float(z_product) + trends_weight * float(z_trends)


def compute_e(out_value: float | None, in_value: float | None) -> float | None:
    """``E = Out - In``; NULL whenever an input is not usable (SPEC §7.5)."""
    if out_value is None or in_value is None:
        return None
    if np.isnan(out_value) or np.isnan(in_value):
        return None
    return float(out_value) - float(in_value)


def sign_robustness(values: list[float | None]) -> str:
    """Classify a quarter as ``ROBUST`` / ``SENSITIVE`` across scenarios.

    ``ROBUST`` — all available scenarios agree on the sign of ``E``.
    ``SENSITIVE`` — at least one scenario disagrees (or fewer than 2 usable).
    This is a sensitivity description, never a statistical test.
    """
    usable = [float(v) for v in values if v is not None and not np.isnan(v)]
    if len(usable) < 2:
        return "SENSITIVE"
    signs = {1 if v > 0 else -1 if v < 0 else 0 for v in usable}
    return "ROBUST" if len(signs) == 1 else "SENSITIVE"
