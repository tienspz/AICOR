"""Market data crawler via yfinance (DSH-06, Tier B).

Implements: SPEC §6.6, SRC-01/08/09.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from aicor.config import COMPANY_TICKERS, get_settings
from aicor.sources import SyncRecord, append_manifest, sha256_file, write_sync_log


# Required columns per SRC-01 Tier B
MARKET_COLUMNS = ["date", "open", "high", "low", "close", "adj_close", "volume"]


def fetch_market(
    ticker: str,
    period: str = "5y",
    *,
    offline_fixture: bool = False,
    settings=None,
) -> pd.DataFrame:
    """Fetch historical market data for *ticker*.

    Returns a DataFrame with columns matching :data:`MARKET_COLUMNS`.
    If ``offline_fixture`` is True, returns a small synthetic fixture
    (for unit tests that must not hit the network).
    """
    if offline_fixture:
        return _fixture_df(ticker)

    import yfinance as yf

    if settings is None:
        settings = get_settings()

    tk = yf.Ticker(ticker)
    hist = tk.history(period=period, auto_adjust=False)

    if hist.empty:
        raise ValueError(f"yfinance returned no data for {ticker!r}")

    df = hist.reset_index()
    # Normalize column names to our schema
    col_map = {
        "Date": "date",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Adj Close": "adj_close",
        "Volume": "volume",
    }
    df = df.rename(columns=col_map)
    # Keep only required columns
    for col in MARKET_COLUMNS:
        if col not in df.columns:
            df[col] = None
    df = df[MARKET_COLUMNS]
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df


def save_market_csv(
    df: pd.DataFrame,
    ticker: str,
    settings=None,
) -> Path:
    """Save market data as CSV to ``data/raw/market/{ticker}.csv``."""
    if settings is None:
        settings = get_settings()

    raw_dir = Path(settings.data_dir) / "raw" / "market"
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"{ticker}.csv"
    df.to_csv(path, index=False)

    sha = sha256_file(path)
    retrieved_at = datetime.now(timezone.utc).isoformat()
    append_manifest(
        raw_dir / "manifest.csv",
        filename=f"{ticker}.csv",
        sha256=sha,
        source_url=f"yfinance:{ticker}",
        retrieved_at=retrieved_at,
    )
    write_sync_log(
        SyncRecord(
            source_type="market",
            company=ticker,
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


def _fixture_df(ticker: str) -> pd.DataFrame:
    """Tiny deterministic fixture for offline tests."""
    from datetime import date

    rows = [
        {
            "date": date(2024, 1, 2),
            "open": 100.0,
            "high": 105.0,
            "low": 99.0,
            "close": 103.0,
            "adj_close": 102.5,
            "volume": 1000000,
        },
        {
            "date": date(2024, 1, 3),
            "open": 103.0,
            "high": 107.0,
            "low": 102.0,
            "close": 106.0,
            "adj_close": 105.5,
            "volume": 1100000,
        },
    ]
    return pd.DataFrame(rows, columns=MARKET_COLUMNS)


def main() -> None:
    settings = get_settings()
    for ticker in COMPANY_TICKERS:
        print(f"Fetching market data for {ticker}...")
        try:
            df = fetch_market(ticker, period="5y", settings=settings)
            save_market_csv(df, ticker, settings=settings)
            print(f"Saved {len(df)} market rows for {ticker}")
        except Exception as exc:
            print(f"Error fetching market data for {ticker}: {exc}")


if __name__ == "__main__":
    main()
