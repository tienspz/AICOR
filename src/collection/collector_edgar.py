"""
SEC EDGAR 10-Q Collector for Microsoft (CIK: 0000789019)
Pulls R&D expense numbers from SEC EDGAR XBRL company facts API.
Respects SEC rate limits (<= 10 req/s) and User-Agent policy (IF-1).
"""
import logging
from typing import List, Dict, Any
import requests

from src.common.config import SEC_RATE_LIMIT_DELAY
from src.common.resilience import create_sec_session, sec_rate_limiter, retry_with_backoff
from src.common.schemas import date_to_quarter
from src.collection.storage import append_to_raw_csv

logger = logging.getLogger("aicor.collector.edgar")

MSFT_CIK = "0000789019"
FACTS_URL = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{MSFT_CIK}.json"


@retry_with_backoff(max_retries=3, initial_delay=1.0)
def fetch_msft_facts() -> Dict[str, Any]:
    """Fetches Microsoft XBRL facts JSON from SEC EDGAR."""
    sec_rate_limiter.wait()
    session = create_sec_session()
    resp = session.get(FACTS_URL, timeout=15)
    resp.raise_for_status()
    return resp.json()


def parse_rnd_facts(facts_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parses R&D expense from SEC XBRL facts JSON.
    US-GAAP tag: ResearchAndDevelopmentExpense
    """
    results = []
    try:
        us_gaap = facts_json.get("facts", {}).get("us-gaap", {})
        rnd_data = us_gaap.get("ResearchAndDevelopmentExpense", {}).get("units", {}).get("USD", [])
    except Exception as e:
        logger.error(f"Error accessing us-gaap ResearchAndDevelopmentExpense in facts: {e}")
        return []

    for item in rnd_data:
        form = item.get("form", "")
        # Filter for quarterly 10-Q and annual 10-K
        if form in ("10-Q", "10-K"):
            end_date = item.get("end", "")
            filed_date = item.get("filed", "") or end_date
            val = item.get("val")
            if val is not None and end_date:
                try:
                    q = date_to_quarter(end_date)
                    results.append({
                        "company_id": 1,
                        "company_name": "Microsoft",
                        "filing_date": filed_date,
                        "quarter": q,
                        "rnd_spend": float(val),
                        "source_url": f"https://www.sec.gov/edgar/browse/?CIK={MSFT_CIK}",
                    })
                except Exception:
                    continue

    return results


def run_edgar_collector() -> int:
    """Runs the SEC EDGAR 10-Q collector and appends new rows to rnd_msft_raw.csv."""
    logger.info("Starting SEC EDGAR R&D collector for Microsoft...")
    try:
        facts = fetch_msft_facts()
        records = parse_rnd_facts(facts)
        if records:
            added = append_to_raw_csv("rnd_msft", records)
            logger.info(f"EDGAR collector finished: {added} new rows added.")
            return added
        else:
            logger.warning("No R&D records extracted from EDGAR facts.")
            return 0
    except Exception as e:
        logger.warning(f"Live EDGAR fetch failed (likely rate-limited or offline): {e}. Pipeline will rely on seed/cache.")
        return 0
