"""
Yahoo Finance Collector for Microsoft (MSFT)
Fetches closing price history and daily quotes using yfinance.
Complies with IF-2 (tags with 15-minute delay note).
"""
import logging
from datetime import datetime
from typing import List, Dict, Any
import yfinance as yf

from src.common.schemas import date_to_quarter
from src.collection.storage import append_to_raw_csv

logger = logging.getLogger("aicor.collector.stock")


def fetch_msft_stock_history(start_date: str = "2022-01-01") -> List[Dict[str, Any]]:
    """
    Fetches daily MSFT closing stock prices from start_date to today.
    """
    logger.info(f"Fetching MSFT stock history since {start_date} via yfinance...")
    ticker = yf.Ticker("MSFT")
    hist = ticker.history(start=start_date)
    
    records = []
    for date_idx, row in hist.iterrows():
        date_str = date_idx.strftime("%Y-%m-%d")
        q = date_to_quarter(date_str)
        close_p = float(row["Close"])
        records.append({
            "company_id": 1,
            "date": date_str,
            "quarter": q,
            "close_price": round(close_p, 2),
            "source_url": "https://finance.yahoo.com/quote/MSFT?latency=15m",
        })
    return records


def run_stock_collector() -> int:
    """Runs the stock collector and appends new prices to stock_msft_raw.csv."""
    try:
        records = fetch_msft_stock_history()
        if records:
            added = append_to_raw_csv("stock_msft", records)
            logger.info(f"Stock collector finished: {added} new rows added.")
            return added
        return 0
    except Exception as e:
        logger.warning(f"Live stock fetch failed: {e}. Pipeline will continue with existing data.")
        return 0
