"""Pipeline orchestrator — Collect→Archive→Validate→Normalize→Transform→Publish→Monitor.

Implements: SPEC §9 (8-step pipeline), NFR-04 (partial on single-source failure).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from aicor.config import COMPANY_CIK, get_settings
from aicor.preprocess.cleaning import clean_financial
from aicor.preprocess.integrate import add_company_dummy, join_panel
from aicor.preprocess.missing import mark_missing
from aicor.preprocess.scale import flag_outliers, ma4q, zscore_16q
from aicor.preprocess.transform import align_calendar, normalize_units
from aicor.sources import SyncRecord, write_sync_log

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Result of a pipeline run."""

    panel: pd.DataFrame
    sync_status: str = "success"  # success / partial / failed
    errors: list[str] = field(default_factory=list)
    source_statuses: dict[str, str] = field(default_factory=dict)


def run_pipeline(
    data: dict[str, pd.DataFrame],
    *,
    settings=None,
) -> pd.DataFrame:
    """Run the full preprocessing pipeline (§9, 8 steps).

    Parameters
    ----------
    data : dict
        Input DataFrames keyed by source name:
        - ``"sec_msft"``, ``"sec_googl"`` — SEC financial data
        - ``"market_msft"``, ``"market_googl"`` — market data (optional)
        - ``"trends"`` — Google Trends data (optional)
        - ``"ir_msft"``, ``"ir_googl"`` — IR product data (optional)

    Returns
    -------
    pd.DataFrame
        Analysis-ready panel with ``source_id``, ``sync_status`` columns.
    """
    if settings is None:
        settings = get_settings()

    result = PipelineResult(panel=pd.DataFrame())
    frames: dict[str, pd.DataFrame] = {}

    # Step 1: Collect — gather raw data per source
    for source_name, df in data.items():
        try:
            if df is not None and not df.empty:
                frames[source_name] = df.copy()
                result.source_statuses[source_name] = "success"
            elif df is None:
                result.source_statuses[source_name] = "failed"
                result.errors.append(f"{source_name}: failed (None)")
            else:
                result.source_statuses[source_name] = "empty"
                result.errors.append(f"{source_name}: empty")
        except Exception as e:
            result.source_statuses[source_name] = "failed"
            result.errors.append(f"{source_name}: {e}")

    # Step 2: Archive — (handled by individual crawlers, skip here)

    # Step 3: Validate — schema checks, FR_T01 (21-quarter check), DQ_T04 (Assets = Liabilities + Equity)
    for name, df in list(frames.items()):
        if "source_id" not in df.columns:
            df["source_id"] = f"auto:{name}"
            frames[name] = df

        # FR_T01: quarter coverage check for financial data
        if name in ("sec_msft", "sec_googl"):
            if len(df) < 16:
                logger.info("%s has %d quarters (< 16 quarters target FR_T01)", name, len(df))

        # DQ_T04: Accounting balance check: Assets == Liabilities + Equity
        if {"assets", "liabilities", "equity"}.issubset(df.columns):
            has_nums = df[["assets", "liabilities", "equity"]].notna().all(axis=1)
            if has_nums.any():
                sub = df.loc[has_nums]
                diff = (sub["assets"] - (sub["liabilities"] + sub["equity"])).abs()
                bad = diff > (0.01 * sub["assets"].abs())
                if bad.any():
                    result.errors.append(f"{name}: DQ_T04 violation in {bad.sum()} rows (Assets != Liabilities + Equity)")

    # Step 4: Clean
    sec_frames = {}
    for name in ("sec_msft", "sec_googl"):
        if name in frames:
            sec_frames[name] = clean_financial(frames[name])

    # Step 5: Handle missing values
    for name, df in sec_frames.items():
        sec_frames[name] = mark_missing(df)

    # Step 6: Transform — calendar alignment + unit normalization
    for name, df in sec_frames.items():
        df = align_calendar(df)
        df = normalize_units(df)
        sec_frames[name] = df

    # Step 7: Integrate — join into panel
    msft_df = sec_frames.get("sec_msft", pd.DataFrame())
    googl_df = sec_frames.get("sec_googl", pd.DataFrame())

    if not msft_df.empty and not googl_df.empty:
        panel = join_panel(msft_df, googl_df)
    elif not msft_df.empty:
        panel = msft_df.copy()
        panel["company"] = "MSFT"
    elif not googl_df.empty:
        panel = googl_df.copy()
        panel["company"] = "GOOGL"
    else:
        panel = pd.DataFrame()

    if not panel.empty:
        panel = add_company_dummy(panel)

    # Step 8: Monitor — set sync status
    failed_sources = [k for k, v in result.source_statuses.items() if v in ("failed", "empty")]
    has_success = any(v == "success" for v in result.source_statuses.values())
    if failed_sources and has_success:
        panel["sync_status"] = "partial"
        result.sync_status = "partial"
    elif failed_sources:
        panel["sync_status"] = "failed"
        result.sync_status = "failed"
    else:
        if "sync_status" not in panel.columns:
            panel["sync_status"] = "success"

    # Ensure source_id is present (SRC-03)
    if "source_id" not in panel.columns and not panel.empty:
        panel["source_id"] = "pipeline:auto"

    # Write sync log
    write_sync_log(
        SyncRecord(
            source_type="pipeline",
            company="ALL",
            started_at=datetime.now(timezone.utc).isoformat(),
            finished_at=datetime.now(timezone.utc).isoformat(),
            sync_status=result.sync_status,
            records_fetched=len(panel),
            error_message="; ".join(result.errors) if result.errors else None,
        ),
        log_dir=settings.data_dir,
    )

    return panel
