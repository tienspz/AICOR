"""Google Trends crawler with circuit-breaker (RQ-02, Tier B).

Implements: SPEC §6.4, §7.4 (TrendsUnavailable fallback).
Single historical query — never concatenates different 0–100 scales.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from aicor.config import get_settings
from aicor.sources import SyncRecord, append_manifest, sha256_file, write_sync_log

try:
    from pytrends.request import TrendReq
except ImportError:  # pragma: no cover
    TrendReq = None  # type: ignore


# ---------- Exceptions ----------

class TrendsUnavailable(Exception):
    """Raised when pytrends fails — caller falls back to adjusted weights (§7.4)."""


# ---------- Default (provisional) config ----------

TRENDS_CONFIG_PROVISIONAL = {
    "version": "v1-provisional",
    "provisional": True,
    "keywords": ["Microsoft AI", "Azure AI", "Google AI", "Gemini"],
    "geo": "US",
    "timeframe": "2022-01-01 2026-10-13",
    "search_type": "web",
}


def fetch_trends(
    keywords: list[str],
    geo: str,
    timeframe: str,
    *,
    offline_fixture: bool = False,
) -> pd.DataFrame:
    """Fetch Google Trends interest-over-time data.

    Returns a DataFrame with columns ``[date, keyword, interest_score]``.

    On ANY pytrends exception → raises :class:`TrendsUnavailable`
    so the caller can fall back to adjusted weight (§7.4).
    """
    if offline_fixture:
        return _fixture_trends(keywords)

    try:
        if TrendReq is None:
            raise TrendsUnavailable("pytrends is not installed")

        pytrends = TrendReq(hl="en-US", tz=360)
        pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo=geo)
        iot = pytrends.interest_over_time()

        if iot.empty:
            raise TrendsUnavailable("pytrends returned empty interest_over_time")

        # Drop "isPartial" column if present
        if "isPartial" in iot.columns:
            iot = iot.drop(columns=["isPartial"])

        # Reshape wide → long
        iot = iot.reset_index()
        iot = iot.melt(id_vars=["date"], var_name="keyword", value_name="interest_score")
        iot["date"] = pd.to_datetime(iot["date"]).dt.date
        return iot

    except TrendsUnavailable:
        raise
    except Exception as exc:
        raise TrendsUnavailable(f"pytrends failed: {exc}") from exc


def save_trends_csv(
    df: pd.DataFrame,
    settings=None,
) -> Path:
    """Save trends data to ``data/raw/trends/trends.csv``."""
    if settings is None:
        settings = get_settings()

    raw_dir = Path(settings.data_dir) / "raw" / "trends"
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / "trends.csv"
    df.to_csv(path, index=False)

    sha = sha256_file(path)
    retrieved_at = datetime.now(timezone.utc).isoformat()
    append_manifest(
        raw_dir / "manifest.csv",
        filename="trends.csv",
        sha256=sha,
        source_url="pytrends",
        retrieved_at=retrieved_at,
    )
    write_sync_log(
        SyncRecord(
            source_type="trends",
            company="ALL",
            started_at=retrieved_at,
            finished_at=datetime.now(timezone.utc).isoformat(),
            sync_status="success",
            records_fetched=len(df),
            records_new=len(df),
            raw_file_path=str(path),
            raw_sha256=sha,
        ),
        log_dir=settings.data_dir,
    )
    return path


def _fixture_trends(keywords: list[str]) -> pd.DataFrame:
    """Tiny deterministic fixture for offline tests."""
    from datetime import date

    rows = []
    for i, kw in enumerate(keywords):
        rows.append({"date": date(2024, 1, 7), "keyword": kw, "interest_score": 50 + i * 10})
        rows.append({"date": date(2024, 1, 14), "keyword": kw, "interest_score": 55 + i * 10})
    return pd.DataFrame(rows, columns=["date", "keyword", "interest_score"])


def main() -> None:
    settings = get_settings()
    cfg = TRENDS_CONFIG_PROVISIONAL
    print(f"Fetching trends for {cfg['keywords']}...")
    try:
        df = fetch_trends(cfg["keywords"], cfg["geo"], cfg["timeframe"])
        save_trends_csv(df, settings=settings)
        print(f"Saved {len(df)} trends rows")
    except TrendsUnavailable as exc:
        print(f"Trends unavailable (circuit-breaker tripped): {exc}")


if __name__ == "__main__":
    main()
