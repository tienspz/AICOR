"""
AICOR Data Cleaning & Validation Subsystem
Reads raw CSVs from data/raw/, validates mandatory fields and formats,
categorizes products and relationships, logs invalid rows to sync_log,
and saves standardized clean datasets into data/cleaned/*.csv.
"""
import os
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

from src.common.config import RAW_DATA_DIR, CLEANED_DATA_DIR, PROCESSED_DATA_DIR
from src.common.schemas import (
    CLEANED_SCHEMAS,
    DEDUPLICATION_KEYS,
    date_to_quarter,
    validate_quarter_format,
    validate_product_category,
    validate_relationship_types,
    validate_confidence_level,
)
from src.collection.storage import log_sync_event

logger = logging.getLogger("aicor.cleaner")


def clean_rnd_msft(raw_rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """Cleans and validates Microsoft R&D expense records."""
    cleaned = []
    dropped = 0
    for r in raw_rows:
        try:
            cid = int(r.get("company_id", 1))
            cname = r.get("company_name", "Microsoft").strip() or "Microsoft"
            filing_date = r.get("filing_date", "").strip()
            q = r.get("quarter", "").strip() or date_to_quarter(filing_date)
            if not validate_quarter_format(q):
                q = date_to_quarter(filing_date)

            rnd = float(r.get("rnd_spend", 0))
            if rnd <= 0:
                dropped += 1
                continue

            cleaned.append({
                "company_id": cid,
                "company_name": cname,
                "filing_date": filing_date,
                "quarter": q,
                "rnd_spend": rnd,
                "source_url": r.get("source_url", "").strip(),
            })
        except Exception as e:
            logger.warning(f"Dropping malformed rnd_msft record {r}: {e}")
            dropped += 1
    return cleaned, dropped


def clean_ai_spend_est(raw_rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """Cleans and validates AI spend estimation records."""
    cleaned = []
    dropped = 0
    for r in raw_rows:
        try:
            cid = int(r.get("company_id", 0))
            cname = r.get("company_name", "").strip()
            q = r.get("quarter", "").strip()
            if not validate_quarter_format(q):
                dropped += 1
                continue

            spend = float(r.get("ai_spend_est", 0))
            if spend <= 0:
                dropped += 1
                continue

            conf = validate_confidence_level(r.get("est_confidence", "medium"))

            cleaned.append({
                "company_id": cid,
                "company_name": cname,
                "quarter": q,
                "ai_spend_est": spend,
                "est_confidence": conf,
                "source_url": r.get("source_url", "").strip(),
            })
        except Exception as e:
            logger.warning(f"Dropping malformed ai_spend_est record {r}: {e}")
            dropped += 1
    return cleaned, dropped


def clean_events_launch(raw_rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """Cleans and validates product launch records, calculating rubric points (Appendix A)."""
    cleaned = []
    dropped = 0
    for r in raw_rows:
        try:
            cid = int(r.get("company_id", 0))
            cname = r.get("company_name", "").strip()
            ldate = r.get("launch_date", "").strip()
            pname = r.get("product_name", "").strip()
            if not ldate or not pname:
                dropped += 1
                continue

            q = r.get("quarter", "").strip() or date_to_quarter(ldate)
            if not validate_quarter_format(q):
                q = date_to_quarter(ldate)

            cat = r.get("category", "").strip().upper()
            points = validate_product_category(cat)

            cleaned.append({
                "company_id": cid,
                "company_name": cname,
                "launch_date": ldate,
                "quarter": q,
                "product_name": pname,
                "category": cat,
                "points": points,
                "source_url": r.get("source_url", "").strip(),
                "coder": r.get("coder", "AICOR").strip(),
            })
        except Exception as e:
            logger.warning(f"Dropping malformed events_launch record {r}: {e}")
            dropped += 1
    return cleaned, dropped


def clean_events_funding(raw_rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """Cleans and validates funding event records."""
    cleaned = []
    dropped = 0
    for r in raw_rows:
        try:
            cid = int(r.get("company_id", 0))
            cname = r.get("company_name", "").strip()
            fdate = r.get("funding_date", "").strip()
            amt = float(r.get("amount", 0))
            if not fdate or amt <= 0:
                dropped += 1
                continue

            q = r.get("quarter", "").strip() or date_to_quarter(fdate)
            val = float(r.get("valuation", 0)) if r.get("valuation") else ""

            cleaned.append({
                "company_id": cid,
                "company_name": cname,
                "funding_date": fdate,
                "quarter": q,
                "amount": amt,
                "valuation": val,
                "source_url": r.get("source_url", "").strip(),
            })
        except Exception as e:
            logger.warning(f"Dropping malformed events_funding record {r}: {e}")
            dropped += 1
    return cleaned, dropped


def clean_events_relationship(raw_rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """Cleans and validates tripartite relationship records (Appendix B)."""
    cleaned = []
    dropped = 0
    for r in raw_rows:
        try:
            edate = r.get("event_date", "").strip()
            parties = r.get("parties", "").strip()
            rel_type = r.get("rel_type", "").strip()
            if not edate or not parties or not rel_type:
                dropped += 1
                continue

            q = r.get("quarter", "").strip() or date_to_quarter(edate)
            validated_types = validate_relationship_types(rel_type)

            cleaned.append({
                "event_date": edate,
                "quarter": q,
                "parties": parties,
                "rel_type": ", ".join(validated_types),
                "quote": r.get("quote", "").strip(),
                "source_url": r.get("source_url", "").strip(),
            })
        except Exception as e:
            logger.warning(f"Dropping malformed events_relationship record {r}: {e}")
            dropped += 1
    return cleaned, dropped


def clean_trends(raw_rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """Cleans and validates Google Trends interest scores (0-100 scale)."""
    cleaned = []
    dropped = 0
    for r in raw_rows:
        try:
            cid = int(r.get("company_id", 0))
            cname = r.get("company_name", "").strip()
            dt = r.get("date", "").strip()
            val = float(r.get("trend_value", -1))
            if not dt or val < 0:
                dropped += 1
                continue

            # Clamp between 0 and 100
            val = min(100.0, max(0.0, val))
            q = r.get("quarter", "").strip() or date_to_quarter(dt)

            cleaned.append({
                "company_id": cid,
                "company_name": cname,
                "date": dt,
                "quarter": q,
                "trend_value": val,
            })
        except Exception as e:
            logger.warning(f"Dropping malformed trends record {r}: {e}")
            dropped += 1
    return cleaned, dropped


def clean_stock_msft(raw_rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """Cleans and validates Microsoft stock prices."""
    cleaned = []
    dropped = 0
    for r in raw_rows:
        try:
            cid = int(r.get("company_id", 1))
            dt = r.get("date", "").strip()
            price = float(r.get("close_price", 0))
            if not dt or price <= 0:
                dropped += 1
                continue

            q = r.get("quarter", "").strip() or date_to_quarter(dt)
            cleaned.append({
                "company_id": cid,
                "date": dt,
                "quarter": q,
                "close_price": round(price, 2),
                "source_url": r.get("source_url", "").strip(),
            })
        except Exception as e:
            logger.warning(f"Dropping malformed stock record {r}: {e}")
            dropped += 1
    return cleaned, dropped


CLEANER_DISPATCH = {
    "rnd_msft": clean_rnd_msft,
    "ai_spend_est": clean_ai_spend_est,
    "events_launch": clean_events_launch,
    "events_funding": clean_events_funding,
    "events_relationship": clean_events_relationship,
    "trends": clean_trends,
    "stock_msft": clean_stock_msft,
}


def run_data_cleaner(
    raw_dir: Optional[Path] = None,
    cleaned_dir: Optional[Path] = None,
) -> Dict[str, Dict[str, int]]:
    """
    Reads all raw CSVs, applies cleaning routines, writes standardized CSVs
    to data/cleaned/*.csv, and records sync metrics in sync_log.csv.
    """
    in_dir = raw_dir or RAW_DATA_DIR
    out_dir = cleaned_dir or CLEANED_DATA_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    summary = {}
    total_valid = 0
    total_dropped = 0

    for table_name, clean_func in CLEANER_DISPATCH.items():
        raw_file = in_dir / f"{table_name}_raw.csv"
        clean_file = out_dir / f"{table_name}_clean.csv"

        if not raw_file.exists():
            logger.warning(f"Raw file {raw_file.name} does not exist. Skipping.")
            summary[table_name] = {"valid": 0, "dropped": 0}
            continue

        with open(raw_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            raw_rows = list(reader)

        cleaned_rows, dropped_count = clean_func(raw_rows)

        # Deduplicate cleaned rows by key columns
        fieldnames = CLEANED_SCHEMAS[table_name]
        key_fields = DEDUPLICATION_KEYS.get(table_name, [fieldnames[0]])
        seen_keys = set()
        deduped_rows = []
        for row in cleaned_rows:
            key_t = tuple(str(row.get(k, "")).strip() for k in key_fields)
            if key_t not in seen_keys:
                seen_keys.add(key_t)
                deduped_rows.append(row)

        # Write clean CSV
        with open(clean_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(deduped_rows)

        logger.info(f"Cleaned {table_name}: {len(deduped_rows)} valid rows saved, {dropped_count} dropped.")
        summary[table_name] = {"valid": len(deduped_rows), "dropped": dropped_count}
        total_valid += len(deduped_rows)
        total_dropped += dropped_count

    # Log event
    log_sync_event(
        rhythm="clean",
        status="success" if total_dropped == 0 else "warning",
        rows_added=total_valid,
        error=f"{total_dropped} rows dropped due to schema validation" if total_dropped > 0 else "",
    )

    return summary
