"""
AICOR SEC EDGAR 10-Q Filing Monitor (Task BE-03)
Implements FR-03: polls the SEC Atom feed for Microsoft CIK 0000789019,
detects 10-Q filings newer than the latest local rnd_msft record, and
optionally triggers R&D extraction + clean + recompute.

All HTTP goes through src.common.resilience (SEC rate limiter + retry).
"""
import csv
import logging
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Optional, Tuple

import requests

from src.common.config import RAW_DATA_DIR, SEC_USER_AGENT
from src.common.resilience import create_sec_session, retry_with_backoff, sec_rate_limiter
from src.collection.storage import log_sync_event

logger = logging.getLogger("aicor.edgar_monitor")

MSFT_CIK = "0000789019"
ATOM_URL = (
    "https://www.sec.gov/cgi-bin/browse-edgar"
    "?action=getcurrent&CIK=0000789019&type=10-Q&output=atom"
)


@retry_with_backoff(max_retries=3, initial_delay=2.0)
def fetch_edgar_atom() -> str:
    """Downloads the SEC current-filings Atom feed for MSFT 10-Q."""
    sec_rate_limiter.wait()
    session = create_sec_session()
    session.headers.update({"Host": "www.sec.gov", "User-Agent": SEC_USER_AGENT})
    resp = session.get(ATOM_URL, timeout=20)
    resp.raise_for_status()
    return resp.text


def parse_atom_latest(atom_xml: str) -> Optional[Tuple[str, str]]:
    """Returns (filing_date, filing_url) of the newest <entry>, or None.

    Filing date prefers <updated>, falls back to <published>, then to a
    YYYY-MM-DD inside <id>/<link>. Entries without any date are skipped.
    """
    try:
        root = ET.fromstring(atom_xml)
    except ET.ParseError as e:
        logger.warning(f"Unparseable SEC Atom XML: {e}")
        return None

    entries = [el for el in root.iter() if el.tag.endswith("entry")]
    dated: list = []
    for entry in entries:
        updated, published, link = "", "", ""
        for child in entry:
            local = child.tag.split("}")[-1]
            if local == "updated":
                updated = (child.text or "").strip()
            elif local == "published":
                published = (child.text or "").strip()
            elif local == "link":
                href = child.attrib.get("href", "").strip() or (child.text or "").strip()
                if href and not link:
                    link = href
        raw_date = updated or published
        m = re.search(r"(\d{4}-\d{2}-\d{2})", raw_date)
        if m:
            dated.append((m.group(1), link))
    if not dated:
        return None
    dated.sort(key=lambda x: x[0])
    return dated[-1]


def get_latest_local_filing_date(raw_dir: Optional[Path] = None) -> Optional[str]:
    """Returns max filing_date in data/raw/rnd_msft_raw.csv, or None if empty."""
    csv_file = (raw_dir or RAW_DATA_DIR) / "rnd_msft_raw.csv"
    if not csv_file.exists() or csv_file.stat().st_size == 0:
        return None
    latest: Optional[str] = None
    with open(csv_file, "r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            d = (row.get("filing_date") or "").strip()[:10]
            if re.match(r"^\d{4}-\d{2}-\d{2}$", d) and (latest is None or d > latest):
                latest = d
    return latest


def check_new_filings(
    atom_xml: Optional[str] = None,
    raw_dir: Optional[Path] = None,
) -> bool:
    """True when the SEC feed has a 10-Q newer than local data. Offline-safe (False)."""
    try:
        xml_text = atom_xml if atom_xml is not None else fetch_edgar_atom()
    except (requests.exceptions.RequestException, Exception) as e:
        logger.warning(f"EDGAR Atom fetch failed (keeping prior data): {e}")
        return False
    latest_remote = parse_atom_latest(xml_text)
    if latest_remote is None:
        return False
    remote_date = latest_remote[0]
    local_date = get_latest_local_filing_date(raw_dir)
    if local_date is None:
        return True
    return remote_date > local_date


def run_edgar_monitor(auto_sync: bool = True, raw_dir: Optional[Path] = None) -> Dict[str, object]:
    """Checks for new 10-Q; when found and auto_sync, re-runs EDGAR extract + pipeline.

    Heavy imports are deferred so `check_new_filings()` stays lightweight.
    """
    has_new = check_new_filings(raw_dir=raw_dir)
    result: Dict[str, object] = {"has_new_filing": has_new, "synced": False, "rows_added": 0}
    if not has_new:
        logger.info("EDGAR monitor: no new 10-Q filing.")
        return result
    if not auto_sync:
        return result
    try:
        from src.collection.collector_edgar import run_edgar_collector
        from src.cleaning.cleaner import run_data_cleaner
        from src.computation.pipeline import run_computation_pipeline

        added = run_edgar_collector()
        run_data_cleaner()
        run_computation_pipeline()
        log_sync_event("edgar", "success", rows_added=added)
        result.update({"synced": True, "rows_added": added})
        logger.info(f"EDGAR monitor: synced new 10-Q ({added} R&D rows).")
    except Exception as e:
        log_sync_event("edgar", "failed", error=str(e))
        logger.error(f"EDGAR auto-sync failed: {e}")
        result["error"] = str(e)
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(run_edgar_monitor(auto_sync=True))
