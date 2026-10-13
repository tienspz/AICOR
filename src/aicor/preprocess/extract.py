"""Extract quarterly financial metrics from raw SEC XBRL snapshots.

Implements: SPEC §6.2 (Tier S metrics), §6.2 Q4 = FY - 9M calculation.
"""

from __future__ import annotations

import datetime
import glob
import json
from pathlib import Path
from typing import Any

import pandas as pd

from aicor.config import get_settings

SEC_METRIC_TAGS: dict[str, list[str]] = {
    "revenue": [
        "Revenues",
        "Revenue",
        "RevenueFromContractWithCustomerExcludingAssessedTax",
    ],
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
}


def extract_quarterly_financials_from_facts(
    facts_data: dict[str, Any],
    company: str,
    start_date: str = "2021-01-01",
) -> pd.DataFrame:
    """Extract quarterly financial records from SEC XBRL facts JSON.

    Parameters
    ----------
    facts_data : dict
        Parsed JSON from SEC EDGAR facts.
    company : str
        Company ticker, e.g. "MSFT" or "GOOGL".
    start_date : str
        Minimum period end date to consider.

    Returns
    -------
    pd.DataFrame
        Table with quarterly periods and financial metrics.
    """
    us_gaap = facts_data.get("facts", facts_data).get("us-gaap", {})

    def _get_entries(metric: str) -> list[dict[str, Any]]:
        combined: list[dict[str, Any]] = []
        for tag in SEC_METRIC_TAGS.get(metric, []):
            if tag in us_gaap and "units" in us_gaap[tag] and "USD" in us_gaap[tag]["units"]:
                combined.extend(us_gaap[tag]["units"]["USD"])
        return combined

    # Identify all quarter end dates via Assets entries
    assets_entries = _get_entries("assets")
    quarter_ends = sorted(
        list(
            set(
                x["end"]
                for x in assets_entries
                if x.get("form") in ("10-Q", "10-K") and x.get("end", "") >= start_date
            )
        )
    )

    rows: list[dict[str, Any]] = []
    for end_str in quarter_ends:
        row: dict[str, Any] = {
            "period_end_date": end_str,
            "company": company,
            "source_id": f"SEC-{company}-{end_str}",
        }

        for metric in SEC_METRIC_TAGS:
            is_duration = metric not in ("assets", "liabilities", "equity")
            val: float | None = None

            # Pool entries across all candidate tags for this metric (ADR-0004 period-aware & cross-tag)
            all_entries = []
            for tag in SEC_METRIC_TAGS.get(metric, []):
                if tag in us_gaap and "units" in us_gaap[tag] and "USD" in us_gaap[tag]["units"]:
                    all_entries.extend(us_gaap[tag]["units"]["USD"])

            matching = [
                x
                for x in all_entries
                if x.get("end") == end_str
                and x.get("form") in ("10-Q", "10-K")
                and x.get("val") is not None
            ]

            if not is_duration:
                if matching:
                    matching.sort(key=lambda x: x.get("filed", ""), reverse=True)
                    val = float(matching[0]["val"])
            else:
                # 1. Check for explicit 3M duration (~80 to 105 days)
                three_m = []
                for x in matching:
                    start = x.get("start")
                    if start:
                        days = (
                            datetime.date.fromisoformat(end_str)
                            - datetime.date.fromisoformat(start)
                        ).days
                        if 80 <= days <= 105:
                            three_m.append(x)

                if three_m:
                    three_m.sort(key=lambda x: x.get("filed", ""), reverse=True)
                    val = float(three_m[0]["val"])
                else:
                    # 2. Check for Q4 calculation: FY - 9M per SPEC §6.2
                    fy_entries = [
                        x
                        for x in matching
                        if x.get("fp") == "FY"
                        or (
                            x.get("start")
                            and 345
                            <= (
                                datetime.date.fromisoformat(end_str)
                                - datetime.date.fromisoformat(x.get("start"))
                            ).days
                            <= 375
                        )
                    ]
                    valid_9m = [
                        x
                        for x in all_entries
                        if x.get("form") == "10-Q"
                        and x.get("val") is not None
                        and 60
                        <= (
                            datetime.date.fromisoformat(end_str)
                            - datetime.date.fromisoformat(x["end"])
                        ).days
                        <= 105
                        and (
                            x.get("start")
                            and 250
                            <= (
                                datetime.date.fromisoformat(x["end"])
                                - datetime.date.fromisoformat(x["start"])
                            ).days
                            <= 290
                        )
                    ]

                    if fy_entries and valid_9m:
                        fy_entries.sort(key=lambda x: x.get("filed", ""), reverse=True)
                        valid_9m.sort(key=lambda x: x.get("filed", ""), reverse=True)
                        val = float(fy_entries[0]["val"]) - float(valid_9m[0]["val"])
                    elif matching:
                        # 3. Fallback to latest matching value if none of the above
                        matching.sort(key=lambda x: x.get("filed", ""), reverse=True)
                        val = float(matching[0]["val"])

            row[metric] = val

        rows.append(row)

    return pd.DataFrame(rows)


def load_and_extract_sec_snapshots(
    data_dir: str | Path | None = None,
) -> dict[str, pd.DataFrame]:
    """Load latest SEC JSON snapshots from data/raw/sec/ and extract DataFrames."""
    if data_dir is None:
        data_dir = get_settings().data_dir

    sec_dir = Path(data_dir) / "raw" / "sec"
    results: dict[str, pd.DataFrame] = {}

    for ticker, cik in [("MSFT", "789019"), ("GOOGL", "1652044")]:
        matches = sorted(glob.glob(str(sec_dir / f"sec_{cik}_*.json")))
        if not matches:
            continue
        latest_file = matches[-1]
        with open(latest_file, encoding="utf-8") as f:
            facts = json.load(f)
        df = extract_quarterly_financials_from_facts(facts, company=ticker)
        results[f"sec_{ticker.lower()}"] = df

    return results
