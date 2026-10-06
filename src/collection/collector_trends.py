"""
Google Trends Collector for Microsoft AI, OpenAI, and Anthropic
Uses pytrends with mandatory rate-limiting delays and jitter to prevent HTTP 429 IP bans.
Complies with IF-3 and NFR-02.
"""
import time
import logging
from typing import List, Dict, Any
from pytrends.request import TrendReq

from src.common.config import TRENDS_MIN_DELAY
from src.common.resilience import trends_rate_limiter, retry_with_backoff
from src.common.schemas import date_to_quarter
from src.collection.storage import append_to_raw_csv

logger = logging.getLogger("aicor.collector.trends")

# Canonical search terms for the 3 companies
COMPANY_KEYWORDS = {
    1: ("Microsoft", "Microsoft AI"),
    2: ("OpenAI", "OpenAI"),
    3: ("Anthropic", "Anthropic"),
}


def fetch_trends_data(timeframe: str = "2022-01-01 2026-09-30") -> List[Dict[str, Any]]:
    """
    Fetches interest over time for Microsoft AI, OpenAI, Anthropic with rate limiting.
    """
    records = []
    pytrend = TrendReq(hl="en-US", tz=0, timeout=(10, 25))

    for company_id, (comp_name, kw) in COMPANY_KEYWORDS.items():
        logger.info(f"Querying Google Trends for {comp_name} ('{kw}')...")
        trends_rate_limiter.wait()
        
        try:
            pytrend.build_payload(kw_list=[kw], timeframe=timeframe, geo="")
            df = pytrend.interest_over_time()
            if not df.empty and kw in df.columns:
                for date_idx, row in df.iterrows():
                    date_str = date_idx.strftime("%Y-%m-%d")
                    val = float(row[kw])
                    records.append({
                        "company_id": company_id,
                        "company_name": comp_name,
                        "date": date_str,
                        "quarter": date_to_quarter(date_str),
                        "trend_value": val,
                    })
        except Exception as e:
            logger.warning(f"Failed to query trends for {comp_name}: {e}. (Will rely on seed/cache).")
            continue

    return records


def run_trends_collector() -> int:
    """Runs the Google Trends collector and appends new rows to trends_raw.csv."""
    try:
        records = fetch_trends_data()
        if records:
            added = append_to_raw_csv("trends", records)
            logger.info(f"Google Trends collector finished: {added} new rows added.")
            return added
        return 0
    except Exception as e:
        logger.warning(f"Live Google Trends fetch encountered an error: {e}")
        return 0
