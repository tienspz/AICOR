"""
AICOR SQLite Database Engine (Task BE-01)
Implements CMU SRS v5.1 Section 3.4: persists cleaned CSVs + processed
fact_quarterly into data/processed/aicor.db (6 tables).

Tables: dim_company, fact_quarterly, event_launch, event_funding,
        event_relationship, sync_log.
"""
import csv
import logging
import sqlite3
from pathlib import Path
from typing import Dict, Optional

from src.common.config import CLEANED_DATA_DIR, PROCESSED_DATA_DIR

logger = logging.getLogger("aicor.db")

DEFAULT_DB_PATH = PROCESSED_DATA_DIR / "aicor.db"

DDL_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS dim_company (
        company_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        ticker TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_quarterly (
        company_id INTEGER NOT NULL,
        quarter TEXT NOT NULL,
        rnd_spend REAL,
        ai_spend_est REAL,
        est_confidence TEXT CHECK(est_confidence IN ('high', 'medium', 'low', NULL)),
        trends_qavg REAL,
        product_score REAL,
        product_ma4q REAL,
        trends_ma4q REAL,
        in_score REAL,
        out_score REAL,
        e_score REAL,
        valid_from DATE NOT NULL,
        PRIMARY KEY (company_id, quarter),
        FOREIGN KEY (company_id) REFERENCES dim_company(company_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS event_launch (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        launch_date DATE NOT NULL,
        quarter TEXT NOT NULL,
        product_name TEXT NOT NULL,
        category TEXT CHECK(category IN ('A', 'B', 'C')),
        points REAL NOT NULL,
        source_url TEXT NOT NULL,
        coder TEXT NOT NULL,
        FOREIGN KEY (company_id) REFERENCES dim_company(company_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS event_funding (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        funding_date DATE NOT NULL,
        quarter TEXT NOT NULL,
        amount REAL NOT NULL,
        valuation REAL,
        source_url TEXT NOT NULL,
        FOREIGN KEY (company_id) REFERENCES dim_company(company_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS event_relationship (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_date DATE NOT NULL,
        quarter TEXT NOT NULL,
        parties TEXT NOT NULL,
        rel_type TEXT NOT NULL,
        quote TEXT,
        source_url TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS sync_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_at TIMESTAMP NOT NULL,
        rhythm TEXT NOT NULL,
        status TEXT NOT NULL,
        rows_added INTEGER DEFAULT 0,
        error TEXT
    )
    """,
]


def _resolve_db_path(db_path: Optional[Path] = None) -> Path:
    p = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def init_database(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Creates the 6 AICOR tables if they do not exist. Returns open connection."""
    p = _resolve_db_path(db_path)
    conn = sqlite3.connect(str(p))
    conn.execute("PRAGMA foreign_keys = ON")
    for ddl in DDL_STATEMENTS:
        conn.execute(ddl)
    conn.commit()
    return conn


def populate_dim_companies(conn: sqlite3.Connection) -> None:
    """Inserts the 3 canonical companies (idempotent via INSERT OR IGNORE)."""
    conn.executemany(
        "INSERT OR IGNORE INTO dim_company (company_id, name, ticker) VALUES (?, ?, ?)",
        [(1, "Microsoft", "MSFT"), (2, "OpenAI", None), (3, "Anthropic", None)],
    )
    conn.commit()


def _to_float(value: object) -> Optional[float]:
    if value is None:
        return None
    s = str(value).strip()
    if s == "" or s.lower() in ("none", "nan", "null"):
        return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def _read_csv_rows(csv_file: Path) -> list:
    if not csv_file.exists() or csv_file.stat().st_size == 0:
        return []
    with open(csv_file, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def sync_csv_to_sqlite(db_path: Optional[Path] = None) -> Dict[str, int]:
    """Reads cleaned CSVs + processed fact_quarterly/sync_log into SQLite.

    Event tables are fully re-synced (DELETE + INSERT) so repeated runs stay
    idempotent despite AUTOINCREMENT keys. fact_quarterly uses
    INSERT OR REPLACE on its (company_id, quarter) natural key.
    Returns {table_name: row_count_after_sync}.
    """
    p = _resolve_db_path(db_path)
    conn = init_database(p)
    try:
        populate_dim_companies(conn)
        counts: Dict[str, int] = {}

        # --- fact_quarterly (from processed) ---
        fact_rows = _read_csv_rows(PROCESSED_DATA_DIR / "fact_quarterly.csv")
        for r in fact_rows:
            conn.execute(
                """INSERT OR REPLACE INTO fact_quarterly
                (company_id, quarter, rnd_spend, ai_spend_est, est_confidence,
                 trends_qavg, product_score, product_ma4q, trends_ma4q,
                 in_score, out_score, e_score, valid_from)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    int(r.get("company_id") or 0),
                    (r.get("quarter") or "").strip(),
                    _to_float(r.get("rnd_spend")),
                    _to_float(r.get("ai_spend_est")),
                    (r.get("est_confidence") or "").strip().lower() or None,
                    _to_float(r.get("trends_qavg")),
                    _to_float(r.get("product_score")),
                    _to_float(r.get("product_ma4q")),
                    _to_float(r.get("trends_ma4q")),
                    _to_float(r.get("in_score")),
                    _to_float(r.get("out_score")),
                    _to_float(r.get("e_score")),
                    (r.get("valid_from") or "").strip(),
                ),
            )
        conn.commit()
        counts["fact_quarterly"] = conn.execute("SELECT COUNT(*) FROM fact_quarterly").fetchone()[0]

        # --- event_launch (from cleaned) ---
        conn.execute("DELETE FROM event_launch")
        launch_rows = _read_csv_rows(CLEANED_DATA_DIR / "events_launch_clean.csv")
        for r in launch_rows:
            conn.execute(
                """INSERT INTO event_launch
                (company_id, launch_date, quarter, product_name, category, points, source_url, coder)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    int(r.get("company_id") or 0),
                    (r.get("launch_date") or "").strip(),
                    (r.get("quarter") or "").strip(),
                    (r.get("product_name") or "").strip(),
                    (r.get("category") or "").strip().upper(),
                    _to_float(r.get("points")) or 0.0,
                    (r.get("source_url") or "").strip(),
                    (r.get("coder") or "AICOR").strip(),
                ),
            )
        conn.commit()
        counts["event_launch"] = conn.execute("SELECT COUNT(*) FROM event_launch").fetchone()[0]

        # --- event_funding (from cleaned) ---
        conn.execute("DELETE FROM event_funding")
        funding_rows = _read_csv_rows(CLEANED_DATA_DIR / "events_funding_clean.csv")
        for r in funding_rows:
            conn.execute(
                """INSERT INTO event_funding
                (company_id, funding_date, quarter, amount, valuation, source_url)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    int(r.get("company_id") or 0),
                    (r.get("funding_date") or "").strip(),
                    (r.get("quarter") or "").strip(),
                    _to_float(r.get("amount")) or 0.0,
                    _to_float(r.get("valuation")),
                    (r.get("source_url") or "").strip(),
                ),
            )
        conn.commit()
        counts["event_funding"] = conn.execute("SELECT COUNT(*) FROM event_funding").fetchone()[0]

        # --- event_relationship (from cleaned) ---
        conn.execute("DELETE FROM event_relationship")
        rel_rows = _read_csv_rows(CLEANED_DATA_DIR / "events_relationship_clean.csv")
        for r in rel_rows:
            conn.execute(
                """INSERT INTO event_relationship
                (event_date, quarter, parties, rel_type, quote, source_url)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    (r.get("event_date") or "").strip(),
                    (r.get("quarter") or "").strip(),
                    (r.get("parties") or "").strip(),
                    (r.get("rel_type") or "").strip(),
                    (r.get("quote") or "").strip(),
                    (r.get("source_url") or "").strip(),
                ),
            )
        conn.commit()
        counts["event_relationship"] = conn.execute(
            "SELECT COUNT(*) FROM event_relationship"
        ).fetchone()[0]

        # --- sync_log (from processed sync_log.csv; append-only mirror) ---
        conn.execute("DELETE FROM sync_log")
        sync_rows = _read_csv_rows(PROCESSED_DATA_DIR / "sync_log.csv")
        for r in sync_rows:
            try:
                rows_added = int(float(str(r.get("rows_added") or 0)))
            except (ValueError, TypeError):
                rows_added = 0
            conn.execute(
                """INSERT INTO sync_log (run_at, rhythm, status, rows_added, error)
                VALUES (?, ?, ?, ?, ?)""",
                (
                    (r.get("run_at") or "").strip(),
                    (r.get("rhythm") or "").strip(),
                    (r.get("status") or "").strip(),
                    rows_added,
                    (r.get("error") or "").strip(),
                ),
            )
        conn.commit()
        counts["sync_log"] = conn.execute("SELECT COUNT(*) FROM sync_log").fetchone()[0]
        counts["dim_company"] = conn.execute("SELECT COUNT(*) FROM dim_company").fetchone()[0]

        logger.info(f"Synced CSVs to SQLite {p.name}: {counts}")
        return counts
    finally:
        conn.close()
