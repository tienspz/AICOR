"""Provenance links for analysis rows (SRC-03, NFR-02).

Builds ``source_id → source_url`` from the immutable SEC snapshots already in
``data/raw/sec/``. Nothing is invented: if no filing accession can be found,
the SEC company-facts URL for that CIK is used and ``verification_status``
records the weaker link.
"""

from __future__ import annotations

import glob
import json
from pathlib import Path

import pandas as pd

from aicor.config import COMPANY_CIK

SEC_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_padded}.json"
SEC_FILING_INDEX_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/"


def sec_facts_url(company: str) -> str:
    """Tier S company-facts endpoint for *company* (SPEC §3.3)."""
    cik = COMPANY_CIK.get(company.upper(), "")
    return SEC_FACTS_URL.format(cik_padded=str(cik).zfill(10))


def sec_filing_url(company: str, accession: str | None) -> str:
    """Filing index URL for an accession number, else the company-facts URL."""
    cik = COMPANY_CIK.get(company.upper(), "")
    if accession:
        return SEC_FILING_INDEX_URL.format(cik=cik, accession=accession.replace("-", ""))
    return sec_facts_url(company)


def _latest_snapshot(sec_dir: Path, cik: str) -> Path | None:
    matches = sorted(glob.glob(str(sec_dir / f"sec_{cik}_*.json")))
    return Path(matches[-1]) if matches else None


def build_provenance(data_dir: str | Path = "data") -> pd.DataFrame:
    """Return per-quarter provenance rows for both companies.

    Columns: ``source_id, company, period_end_date, source_url, filing_date,
    accession_number, form, source_tier, verification_status``.

    An empty frame is returned when the raw layer is absent (tests/offline),
    and callers fall back to the canonical company-facts URL.
    """
    sec_dir = Path(data_dir) / "raw" / "sec"
    rows: list[dict[str, object]] = []

    for company, cik in COMPANY_CIK.items():
        snapshot = _latest_snapshot(sec_dir, cik)
        if snapshot is None:
            continue

        try:
            facts = json.loads(snapshot.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue

        us_gaap = facts.get("facts", facts).get("us-gaap", {})
        best: dict[str, dict[str, str]] = {}
        for tag_data in us_gaap.values():
            units = tag_data.get("units", {}) if isinstance(tag_data, dict) else {}
            for entries in units.values():
                for entry in entries or []:
                    accn = entry.get("accn")
                    end = entry.get("end")
                    form = entry.get("form")
                    filed = entry.get("filed")
                    if not accn or not end or form not in ("10-Q", "10-K"):
                        continue
                    # ``available_at`` must be the FIRST filing that reported the
                    # period: a later 10-K that restates it does not make the
                    # number retroactively available earlier than it was.
                    current = best.get(end)
                    if current is None or str(filed or "") < str(current.get("filed") or ""):
                        best[end] = {"accn": accn, "filed": str(filed or ""), "form": str(form)}

        for end, info in sorted(best.items()):
            rows.append(
                {
                    "source_id": f"SEC-{company}-{end}",
                    "company": company,
                    "period_end_date": end,
                    "source_url": sec_filing_url(company, info["accn"]),
                    "filing_date": info["filed"] or None,
                    "accession_number": info["accn"],
                    "form": info["form"],
                    "source_tier": "S",
                    "verification_status": "verified",
                }
            )

    if not rows:
        return pd.DataFrame(
            columns=[
                "source_id",
                "company",
                "period_end_date",
                "source_url",
                "filing_date",
                "accession_number",
                "form",
                "source_tier",
                "verification_status",
            ]
        )

    return pd.DataFrame(rows).drop_duplicates(subset=["source_id"]).reset_index(drop=True)


def availability_frame(provenance: pd.DataFrame, *, lag_days: int = 45) -> pd.DataFrame:
    """Derive ``available_at`` per (company, period_end_date).

    Uses the filing date when it is known. When it is not, a conservative
    ``period_end + lag_days`` proxy is used and labelled as such so a
    point-in-time check can never mistake a proxy for a fact.
    """
    if provenance is None or provenance.empty:
        return pd.DataFrame(columns=["company", "period_end_date", "available_at", "availability_basis"])

    df = provenance[["company", "period_end_date", "filing_date"]].copy()
    period_end = pd.to_datetime(df["period_end_date"], errors="coerce")
    filing = pd.to_datetime(df["filing_date"], errors="coerce")
    proxy = period_end + pd.Timedelta(days=lag_days)
    available = filing.fillna(proxy)
    df["available_at"] = available.dt.strftime("%Y-%m-%d")
    df["availability_basis"] = filing.notna().map({True: "filing_date", False: "period_end_plus_45d"})
    return df.drop_duplicates(subset=["company", "period_end_date"]).reset_index(drop=True)
