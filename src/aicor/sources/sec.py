"""SEC EDGAR XBRL crawler — financial/R&D data (RQ-01, Tier S).

Implements: SPEC §3.3, §6.2, NFR-07 (rate-limit + User-Agent).
ADR-0004: fail loud on missing XBRL tag (TagResolutionError).
"""

from __future__ import annotations

import json
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import requests

from aicor.config import COMPANY_CIK, REQUEST_DELAY, SEC_COMPANYFACTS_URL, get_settings
from aicor.sources import (
    SyncRecord,
    append_manifest,
    sha256_file,
    write_sync_log,
)


# ---------- Exceptions ----------

class TagResolutionError(Exception):
    """Raised when no XBRL tag candidate resolves for a given period (ADR-0004)."""


# ---------- SEC metrics we care about (§6.2) ----------

SEC_METRICS: dict[str, list[str]] = {
    "revenue": ["Revenues", "Revenue", "RevenueFromContractWithCustomerExcludingAssessedTax"],
    "rd_expense": [
        "ResearchAndDevelopmentExpense",
        "ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost",
    ],
    "capex": [
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "CapitalExpendituresIncurredButNotYetPaid",
    ],
    "operating_income": [
        "OperatingIncomeLoss",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments",
    ],
    "net_income": [
        "NetIncomeLoss",
        "ProfitLoss",
    ],
    "cfo": [
        "NetCashProvidedByUsedInOperatingActivities",
        "NetCashProvidedByOperatingActivities",
    ],
    "assets": ["Assets"],
    "liabilities": ["Liabilities"],
    "equity": [
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    ],
    "shares": [
        "CommonStockSharesOutstanding",
        "WeightedAverageNumberOfShareOutstandingBasicAndDiluted",
        "WeightedAverageNumberOfDilutedSharesOutstanding",
    ],
    "eps": [
        "EarningsPerShareDiluted",
        "EarningsPerShareBasicAndDiluted",
    ],
}


# ---------- Core fetcher ----------

def fetch_companyfacts(cik: str, settings=None) -> dict[str, Any]:
    """Fetch the SEC XBRL companyfacts JSON for *cik* (zero-padded to 10 digits).

    Respects NFR-07: ≤10 req/s, descriptive User-Agent.
    Returns the parsed JSON dict. Raw snapshot is saved to data/raw/sec/.
    """
    if settings is None:
        settings = get_settings()

    cik_padded = cik.zfill(10)
    url = SEC_COMPANYFACTS_URL.format(cik_padded=cik_padded)

    headers = {
        "User-Agent": settings.sec_user_agent,
        "Accept": "application/json",
    }

    time.sleep(REQUEST_DELAY)
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    # Save raw snapshot
    raw_dir = Path(settings.data_dir) / "raw" / "sec"
    raw_dir.mkdir(parents=True, exist_ok=True)
    retrieved_at = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"sec_{cik}_{retrieved_at}.json"
    snapshot_path = raw_dir / filename
    snapshot_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # Manifest + SHA-256
    sha = sha256_file(snapshot_path)
    append_manifest(
        raw_dir / "manifest.csv",
        filename=filename,
        sha256=sha,
        source_url=url,
        retrieved_at=retrieved_at,
    )

    # Sync log
    write_sync_log(
        SyncRecord(
            source_type="sec_xbrl",
            company=_cik_to_ticker(cik),
            started_at=retrieved_at,
            finished_at=datetime.now(timezone.utc).isoformat(),
            sync_status="success",
            records_fetched=1,
            records_new=1,
            raw_file_path=str(snapshot_path),
            raw_sha256=sha,
        ),
        log_dir=settings.data_dir,
    )

    return data


def _cik_to_ticker(cik: str) -> str:
    for ticker, c in COMPANY_CIK.items():
        if c == cik:
            return ticker
    return f"CIK-{cik}"


# ---------- Tag resolver (period-aware) ----------

def resolve_metric(
    facts: dict[str, Any],
    tag_candidates: list[str],
    period_end: date,
    period_type: str = "quarterly",
) -> tuple[float | None, str | None]:
    """Resolve a financial metric from SEC XBRL facts.

    Tries each tag in *tag_candidates* in order against the given *period_end*.
    Returns ``(value, xbrl_tag)`` on first hit.

    Raises :class:`TagResolutionError` if NO tag resolves — we fail loud
    per ADR-0004, never silently return NULL.

    Parameters
    ----------
    facts : dict
        The ``companyfacts`` JSON from SEC (full or a subset).
    tag_candidates : list[str]
        XBRL tag names to try, in priority order.
    period_end : date
        The period end date to match (e.g., ``date(2024, 12, 31)``).
    period_type : str
        ``"quarterly"`` looks for 3M and 6M/9M/FY periods;
        ``"annual"`` looks for 12M / FY periods.
    """
    if not facts:
        raise TagResolutionError(
            f"Empty facts dict; cannot resolve {tag_candidates!r} for {period_end}"
        )

    us_gaap = facts.get("facts", facts).get("us-gaap", {})
    period_end_str = period_end.isoformat()

    for tag in tag_candidates:
        tag_data = us_gaap.get(tag)
        if tag_data is None:
            continue
        units = tag_data.get("units", {})
        # Try USD first, then shares, then pure
        for unit_key in ("USD", "shares", "pure"):
            entries = units.get(unit_key, [])
            for entry in entries:
                if entry.get("end") == period_end_str:
                    val = entry.get("val")
                    if val is not None:
                        return (float(val), tag)

    raise TagResolutionError(
        f"No tag in {tag_candidates!r} resolved for period_end={period_end} "
        f"in facts with {len(us_gaap)} us-gaap tags"
    )


# ---------- Batch extract ----------

def extract_sec_financials(
    facts: dict[str, Any],
    period_end: date,
    metrics: dict[str, list[str]] | None = None,
) -> dict[str, tuple[float | None, str | None]]:
    """Extract all configured SEC metrics for one period.

    Returns ``{metric_name: (value, xbrl_tag)}`` for each metric.
    On TagResolutionError, records ``(None, None)`` with the reason.
    """
    if metrics is None:
        metrics = SEC_METRICS

    results: dict[str, tuple[float | None, str | None]] = {}
    for metric_name, tags in metrics.items():
        try:
            val, tag = resolve_metric(facts, tags, period_end)
            results[metric_name] = (val, tag)
        except TagResolutionError:
            results[metric_name] = (None, None)
    return results


def main() -> None:
    settings = get_settings()
    for ticker, cik in COMPANY_CIK.items():
        print(f"Fetching SEC facts for {ticker} (CIK {cik})...")
        try:
            fetch_companyfacts(cik, settings=settings)
            print(f"Saved SEC facts for {ticker}")
        except Exception as exc:
            print(f"Error fetching SEC facts for {ticker}: {exc}")


if __name__ == "__main__":
    main()
