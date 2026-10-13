"""Integration / Join + Dummy + Derived features.

Implements: Lecture 07 slide 3/5, 5–8/9, SPEC §7.1, §8.3.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


# ---------- Panel join (§8.2, DAT-01) ----------

def join_panel(
    msft: pd.DataFrame,
    googl: pd.DataFrame,
) -> pd.DataFrame:
    """Join MSFT and GOOGL quarterly DataFrames into a panel.

    Join key: ``period_end_date`` (DAT-01).
    Append-only — never overwrites existing rows (§8.2).
    """
    msft = msft.copy()
    googl = googl.copy()

    if "company" not in msft.columns:
        msft["company"] = "MSFT"
    if "company" not in googl.columns:
        googl["company"] = "GOOGL"

    panel = pd.concat([msft, googl], ignore_index=True)

    # Ensure no label-encoding for company — use dummy instead
    if "company_id_int" in panel.columns:
        panel = panel.drop(columns=["company_id_int"])

    return panel


# ---------- Company dummy (slide 5/9: k−1 = 1 dummy) ----------

def add_company_dummy(panel: pd.DataFrame) -> pd.DataFrame:
    """Add ``is_msft`` binary dummy (k−1 = 1 dummy for 2 companies, slide 5/9).

    Does NOT add label-encoded integer — that would be incorrect for
    linear models (slide 8/9: non-tree-like → use one-hot/dummy).
    """
    panel = panel.copy()
    panel["is_msft"] = (panel["company"] == "MSFT").astype(int)
    return panel


# ---------- Product score (§7.1) ----------

def product_score(counts: dict[str, int]) -> int:
    """Compute product score: ``3*A + 2*B + 1*C`` (§7.1).

    Parameters
    ----------
    counts : dict
        Mapping of category to count, e.g. ``{"A": 2, "B": 1, "C": 3}``.
    """
    weights = {"A": 3, "B": 2, "C": 1}
    return sum(weights.get(cat, 0) * count for cat, count in counts.items())


# ---------- Derived intensity ratios (slide 3/9: derived variable) ----------

def rd_intensity(rd: float | None, revenue: float | None) -> float | None:
    """R&D intensity = R&D / Revenue (derived, §6.2).

    Returns None if either input is missing — per SRC-05 (never fabricate).
    Metadata: ``proxy=true, confidence="LOW"`` (SRC-06).
    """
    if rd is None or revenue is None or revenue == 0:
        return None
    return rd / revenue


def capex_intensity(capex: float | None, revenue: float | None) -> float | None:
    """CapEx intensity = CapEx / Revenue (§7.4 Could).

    Returns None if either input is missing.
    """
    if capex is None or revenue is None or revenue == 0:
        return None
    return capex / revenue


# ---------- Event type dummies (slide 8/9: one-hot, NOT label-encoding) ----------

def event_type_dummies(events: list[str]) -> pd.DataFrame:
    """Create one-hot dummy columns for event types.

    Uses ``event_`` prefix for column names.
    NEVER uses label-encoding — slide 8/9: Out is linear (non-tree-like),
    so ordinal encoding would introduce false ordering.
    """
    df = pd.DataFrame({"event_type": events})
    dummies = pd.get_dummies(df["event_type"], prefix="event", dtype=int)
    return dummies
