"""
Tests for Task BE-01: SQLite Database Engine & CSV-to-SQLite sync.
Uses a temp .db file but reads the real cleaned/processed CSVs (read-only).
"""
import sqlite3

from src.computation.db import init_database, populate_dim_companies, sync_csv_to_sqlite


def test_init_database_creates_six_tables(tmp_path):
    db_file = tmp_path / "aicor.db"
    conn = init_database(db_file)
    try:
        tables = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    finally:
        conn.close()
    assert {
        "dim_company",
        "fact_quarterly",
        "event_launch",
        "event_funding",
        "event_relationship",
        "sync_log",
    }.issubset(tables)


def test_populate_dim_companies_is_idempotent(tmp_path):
    db_file = tmp_path / "aicor.db"
    conn = init_database(db_file)
    try:
        populate_dim_companies(conn)
        populate_dim_companies(conn)
        rows = conn.execute(
            "SELECT company_id, name, ticker FROM dim_company ORDER BY company_id"
        ).fetchall()
    finally:
        conn.close()
    assert rows == [(1, "Microsoft", "MSFT"), (2, "OpenAI", None), (3, "Anthropic", None)]


def test_sync_csv_to_sqlite_loads_fact_quarterly(tmp_path):
    db_file = tmp_path / "aicor.db"
    counts = sync_csv_to_sqlite(db_file)
    assert counts["fact_quarterly"] >= 54
    assert counts["dim_company"] == 3

    conn = sqlite3.connect(str(db_file))
    try:
        n = conn.execute("SELECT COUNT(*) FROM fact_quarterly").fetchone()[0]
        assert n >= 54
        sample = conn.execute(
            "SELECT company_id, quarter, in_score, out_score, e_score "
            "FROM fact_quarterly WHERE company_id = 1 ORDER BY quarter LIMIT 1"
        ).fetchone()
        assert sample is not None and len(sample) == 5
    finally:
        conn.close()
