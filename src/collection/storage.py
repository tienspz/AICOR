"""
AICOR Append-Only CSV Storage Engine
Implements FR-13: preserves raw data in append-only mode, prevents duplicates
via natural key hashing/matching, and records operations in sync_log.csv.
"""
import os
import csv
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.common.config import RAW_DATA_DIR, PROCESSED_DATA_DIR
from src.common.schemas import RAW_SCHEMAS, DEDUPLICATION_KEYS, PROCESSED_SCHEMAS

logger = logging.getLogger("aicor.storage")


def get_sync_timestamp() -> str:
    """Returns current UTC ISO timestamp."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def append_to_raw_csv(
    table_name: str,
    new_rows: List[Dict[str, Any]],
    target_dir: Optional[Path] = None,
) -> int:
    """
    Appends new rows to a raw CSV table in an append-only, idempotent manner.
    - If the file does not exist, it creates it with the schema header.
    - If it exists, existing natural keys are loaded so only truly new rows are appended.
    Returns the count of actually added rows.
    """
    if not new_rows:
        return 0

    if table_name not in RAW_SCHEMAS:
        raise ValueError(f"Unknown raw table '{table_name}'. Allowed: {list(RAW_SCHEMAS.keys())}")

    directory = target_dir or RAW_DATA_DIR
    directory.mkdir(parents=True, exist_ok=True)
    csv_file = directory / f"{table_name}_raw.csv"

    fieldnames = RAW_SCHEMAS[table_name]
    key_fields = DEDUPLICATION_KEYS.get(table_name, [fieldnames[0]])

    existing_keys = set()
    file_exists = csv_file.exists() and csv_file.stat().st_size > 0

    if file_exists:
        with open(csv_file, mode="r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key_tuple = tuple(str(row.get(k, "")).strip() for k in key_fields)
                existing_keys.add(key_tuple)

    rows_to_append = []
    for r in new_rows:
        key_tuple = tuple(str(r.get(k, "")).strip() for k in key_fields)
        if key_tuple not in existing_keys:
            # Clean and ensure all fields are present
            cleaned_row = {field: r.get(field, "") for field in fieldnames}
            rows_to_append.append(cleaned_row)
            existing_keys.add(key_tuple)

    if not rows_to_append:
        logger.info(f"No new records to append to {csv_file.name}. (All {len(new_rows)} were existing duplicates).")
        return 0

    mode = "a" if file_exists else "w"
    with open(csv_file, mode=mode, encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows_to_append)

    logger.info(f"Appended {len(rows_to_append)} new records to {csv_file.name}.")
    return len(rows_to_append)


def log_sync_event(
    rhythm: str,
    status: str,
    rows_added: int = 0,
    error: str = "",
    target_dir: Optional[Path] = None,
) -> None:
    """
    Appends a run execution entry to sync_log.csv (FR-11, UC-4).
    """
    directory = target_dir or PROCESSED_DATA_DIR
    directory.mkdir(parents=True, exist_ok=True)
    log_file = directory / "sync_log.csv"

    fieldnames = PROCESSED_SCHEMAS["sync_log"]
    file_exists = log_file.exists() and log_file.stat().st_size > 0

    entry = {
        "run_at": get_sync_timestamp(),
        "rhythm": rhythm,
        "status": status,
        "rows_added": rows_added,
        "error": error,
    }

    mode = "a" if file_exists else "w"
    with open(log_file, mode=mode, encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(entry)

    logger.info(f"Recorded sync event: rhythm={rhythm}, status={status}, rows_added={rows_added}")
