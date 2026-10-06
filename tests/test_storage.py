"""
Unit tests for storage.py (Append-only and deduplication).
"""
import pytest
import csv
from src.collection.storage import append_to_raw_csv, log_sync_event


def test_append_to_raw_csv_and_deduplication(tmp_path):
    table = "rnd_msft"
    rows_batch_1 = [
        {"company_id": "1", "company_name": "Microsoft", "filing_date": "2022-04-26", "quarter": "2022-Q1", "rnd_spend": "5600000000", "source_url": "sec.gov/1"},
        {"company_id": "1", "company_name": "Microsoft", "filing_date": "2022-07-26", "quarter": "2022-Q2", "rnd_spend": "6800000000", "source_url": "sec.gov/2"},
    ]

    # First write
    added_1 = append_to_raw_csv(table, rows_batch_1, target_dir=tmp_path)
    assert added_1 == 2

    # Second write with exact duplicates
    added_2 = append_to_raw_csv(table, rows_batch_1, target_dir=tmp_path)
    assert added_2 == 0

    # Third write with 1 existing and 1 new
    rows_batch_2 = [
        {"company_id": "1", "company_name": "Microsoft", "filing_date": "2022-07-26", "quarter": "2022-Q2", "rnd_spend": "6800000000", "source_url": "sec.gov/2"},
        {"company_id": "1", "company_name": "Microsoft", "filing_date": "2022-10-25", "quarter": "2022-Q3", "rnd_spend": "6600000000", "source_url": "sec.gov/3"},
    ]
    added_3 = append_to_raw_csv(table, rows_batch_2, target_dir=tmp_path)
    assert added_3 == 1

    # Verify total rows in file
    csv_file = tmp_path / "rnd_msft_raw.csv"
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) == 3
        quarters = [r["quarter"] for r in reader]
        assert quarters == ["2022-Q1", "2022-Q2", "2022-Q3"]


def test_log_sync_event(tmp_path):
    log_sync_event("fast", "success", rows_added=15, target_dir=tmp_path)
    log_sync_event("slow", "failed", rows_added=0, error="API timeout", target_dir=tmp_path)

    log_file = tmp_path / "sync_log.csv"
    assert log_file.exists()
    with open(log_file, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        assert len(rows) == 2
        assert rows[0]["rhythm"] == "fast"
        assert rows[0]["status"] == "success"
        assert rows[0]["rows_added"] == "15"
        assert rows[1]["status"] == "failed"
        assert rows[1]["error"] == "API timeout"
