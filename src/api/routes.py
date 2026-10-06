"""
AICOR REST API routes (Task BE-05).
Serves precomputed Layer-2 outputs (FR-14: never recalculates E).
SQLite is preferred when data/processed/aicor.db exists; CSV/JSON are the fallback.
"""
import csv
import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.common.config import CLEANED_DATA_DIR, PROCESSED_DATA_DIR

logger = logging.getLogger("aicor.api")
router = APIRouter()

DB_PATH = PROCESSED_DATA_DIR / "aicor.db"
PORTFOLIO_DISCLAIMER = "Công cụ minh họa, không phải khuyến nghị đầu tư."
KEYS = ("MSFT", "OpenAI", "Anthropic")
CID_TO_KEY = {1: "MSFT", 2: "OpenAI", 3: "Anthropic"}


def _num(value: Any) -> Optional[float]:
    if value is None:
        return None
    s = str(value).strip()
    if s == "" or s.lower() in ("none", "nan", "null"):
        return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def _read_csv_rows(csv_file: Path) -> List[Dict[str, Any]]:
    if not csv_file.exists() or csv_file.stat().st_size == 0:
        return []
    with open(csv_file, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _read_json(json_file: Path) -> Optional[Any]:
    if not json_file.exists() or json_file.stat().st_size == 0:
        return None
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def load_facts(company_id: Optional[int] = None, quarter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Loads fact_quarterly from SQLite when available, else from CSV."""
    rows: List[Dict[str, Any]] = []
    if DB_PATH.exists():
        try:
            conn = sqlite3.connect(str(DB_PATH))
            conn.row_factory = sqlite3.Row
            try:
                query = (
                    "SELECT f.company_id, d.name AS company_name, f.quarter, f.rnd_spend,"
                    " f.ai_spend_est, f.est_confidence, f.trends_qavg, f.product_score,"
                    " f.product_ma4q, f.trends_ma4q, f.in_score, f.out_score, f.e_score,"
                    " f.valid_from FROM fact_quarterly f"
                    " LEFT JOIN dim_company d ON d.company_id = f.company_id"
                )
                clauses, params = [], []
                if company_id is not None:
                    clauses.append("f.company_id = ?")
                    params.append(company_id)
                if quarter is not None:
                    clauses.append("f.quarter = ?")
                    params.append(quarter)
                if clauses:
                    query += " WHERE " + " AND ".join(clauses)
                query += " ORDER BY f.quarter, f.company_id"
                rows = [dict(r) for r in conn.execute(query, params).fetchall()]
                if rows:
                    return rows
            finally:
                conn.close()
        except sqlite3.Error as e:
            logger.warning(f"SQLite fact read failed, falling back to CSV: {e}")
    for r in _read_csv_rows(PROCESSED_DATA_DIR / "fact_quarterly.csv"):
        try:
            cid = int(r.get("company_id") or 0)
        except (ValueError, TypeError):
            continue
        if company_id is not None and cid != company_id:
            continue
        if quarter is not None and (r.get("quarter") or "").strip() != quarter:
            continue
        rows.append(
            {
                "company_id": cid,
                "company_name": (r.get("company_name") or "").strip(),
                "quarter": (r.get("quarter") or "").strip(),
                "rnd_spend": _num(r.get("rnd_spend")),
                "ai_spend_est": _num(r.get("ai_spend_est")),
                "est_confidence": (r.get("est_confidence") or "").strip() or None,
                "trends_qavg": _num(r.get("trends_qavg")),
                "product_score": _num(r.get("product_score")),
                "product_ma4q": _num(r.get("product_ma4q")),
                "trends_ma4q": _num(r.get("trends_ma4q")),
                "in_score": _num(r.get("in_score")),
                "out_score": _num(r.get("out_score")),
                "e_score": _num(r.get("e_score")),
                "valid_from": (r.get("valid_from") or "").strip() or None,
            }
        )
    rows.sort(key=lambda x: (x.get("quarter") or "", x.get("company_id") or 0))
    return rows


def load_timeline() -> List[Dict[str, Any]]:
    bundle = _read_json(PROCESSED_DATA_DIR / "timeline_events.json")
    if isinstance(bundle, dict) and isinstance(bundle.get("events"), list):
        return bundle["events"]
    if isinstance(bundle, list):
        return bundle
    # Fallback: build from cleaned CSVs (read-only, no E recalculation)
    from src.computation.exporter import _build_timeline_events

    return _build_timeline_events()


def load_sensitivity(
    quarter: Optional[str] = None, weight_set: Optional[str] = None
) -> List[Dict[str, Any]]:
    rows = []
    for r in _read_csv_rows(PROCESSED_DATA_DIR / "sensitivity_analysis.csv"):
        if quarter is not None and (r.get("quarter") or "").strip() != quarter:
            continue
        if weight_set is not None and (r.get("weight_set") or "").strip() != weight_set:
            continue
        rows.append(r)
    return rows


def load_baseline() -> Dict[str, Any]:
    bundle = _read_json(PROCESSED_DATA_DIR / "portfolio_baseline.json")
    if isinstance(bundle, dict) and "medians" in bundle:
        return bundle
    # Fallback: compute medians from facts (same formula as exporter)
    from statistics import median as _median

    facts = load_facts()
    quarters = sorted({f["quarter"] for f in facts if f.get("quarter")})
    window = quarters[-4:] if len(quarters) >= 4 else quarters
    medians: Dict[str, Optional[float]] = {}
    for cid, key in CID_TO_KEY.items():
        vals = [
            f["e_score"] for f in facts
            if f.get("company_id") == cid and f.get("quarter") in window
            and isinstance(f.get("e_score"), (int, float))
        ]
        medians[key] = round(float(_median(vals)), 3) if vals else None
    return {
        "reference_window": window,
        "method": "median(E) of the 4 most recent quarters per company.",
        "medians": medians,
        "disclaimer": PORTFOLIO_DISCLAIMER,
    }


def get_live_msft_price() -> Dict[str, Any]:
    """Fetches MSFT price via yfinance; falls back to latest cleaned close.

    FR-12: always tags the 15-minute Yahoo delay.
    """
    latency = 15
    try:
        import yfinance as yf

        ticker = yf.Ticker("MSFT")
        hist = ticker.history(period="1d", interval="1m")
        if hist is not None and len(hist) > 0:
            price = float(hist["Close"].iloc[-1])
            return {
                "symbol": "MSFT",
                "price": round(price, 2),
                "currency": "USD",
                "latency_minutes": latency,
                "source": "Yahoo Finance (delayed 15m)",
            }
    except Exception as e:
        logger.warning(f"Live MSFT fetch failed, using cleaned fallback: {e}")
    fallback = None
    for r in reversed(_read_csv_rows(CLEANED_DATA_DIR / "stock_msft_clean.csv")):
        fallback = _num(r.get("close_price"))
        if fallback is not None:
            break
    return {
        "symbol": "MSFT",
        "price": fallback,
        "currency": "USD",
        "latency_minutes": latency,
        "source": "Yahoo Finance (delayed 15m)",
        "stale_fallback": True,
    }


class PortfolioRequest(BaseModel):
    weights: Dict[str, float] = Field(
        ..., description="Keys MSFT/OpenAI/Anthropic, values sum to 1.0"
    )


def _normalize_weights(raw: Dict[str, float]) -> Dict[str, float]:
    mapping = {
        "msft": "MSFT", "microsoft": "MSFT", "1": "MSFT",
        "openai": "OpenAI", "2": "OpenAI",
        "anthropic": "Anthropic", "3": "Anthropic",
    }
    normalized: Dict[str, float] = {}
    for k, v in raw.items():
        key = mapping.get(str(k).strip().lower(), str(k).strip())
        if key not in KEYS:
            raise HTTPException(status_code=422, detail=f"Unknown company key '{k}'. Use MSFT/OpenAI/Anthropic.")
        try:
            normalized[key] = float(v)
        except (ValueError, TypeError):
            raise HTTPException(status_code=422, detail=f"Weight for '{k}' must be numeric.")
    for key in KEYS:
        normalized.setdefault(key, 0.0)
    for key, val in normalized.items():
        if not (0.0 <= val <= 1.0):
            raise HTTPException(status_code=422, detail=f"Weight for '{key}' must be within [0, 1].")
    total = sum(normalized.values())
    if abs(total - 1.0) > 0.001:
        raise HTTPException(status_code=422, detail=f"Weights must sum to 1.0 (got {total:.4f}).")
    return normalized


@router.get("/health")
def health() -> Dict[str, Any]:
    manifest = _read_json(PROCESSED_DATA_DIR / "manifest.json") or {}
    sync_rows = _read_csv_rows(PROCESSED_DATA_DIR / "sync_log.csv")
    last = sync_rows[-1] if sync_rows else {}
    return {
        "status": "ok",
        "system": manifest.get("system", "AICOR"),
        "version": manifest.get("version", "5.1"),
        "last_sync_utc": manifest.get("last_sync_utc"),
        "quarters_count": manifest.get("quarters_count"),
        "quarter_range": manifest.get("quarter_range"),
        "last_sync_event": last or None,
    }


@router.get("/facts")
def facts(company_id: Optional[int] = None, quarter: Optional[str] = None) -> Dict[str, Any]:
    rows = load_facts(company_id=company_id, quarter=quarter)
    return {"count": len(rows), "facts": rows}


@router.get("/events")
def events(type: Optional[str] = None) -> Dict[str, Any]:  # noqa: A002 - query param name
    timeline = load_timeline()
    if type is not None:
        timeline = [e for e in timeline if (e.get("type") or "") == type]
    return {"count": len(timeline), "events": timeline}


@router.get("/sensitivity")
def sensitivity(
    quarter: Optional[str] = None, weight_set: Optional[str] = None
) -> Dict[str, Any]:
    rows = load_sensitivity(quarter=quarter, weight_set=weight_set)
    return {"count": len(rows), "rows": rows}


@router.get("/stock/msft/live")
def stock_msft_live() -> Dict[str, Any]:
    return get_live_msft_price()


@router.post("/simulate-portfolio")
def simulate_portfolio(req: PortfolioRequest) -> Dict[str, Any]:
    weights = _normalize_weights(req.weights)
    baseline = load_baseline()
    medians = baseline.get("medians", {})
    score = 0.0
    for key in KEYS:
        med = _num(medians.get(key))
        if med is None:
            raise HTTPException(
                status_code=422,
                detail=f"Insufficient E data for {key} in the reference window.",
            )
        score += weights[key] * med
    return {
        "weights": weights,
        "medians": medians,
        "reference_window": baseline.get("reference_window"),
        "portfolio_score": round(score, 4),
        "disclaimer": PORTFOLIO_DISCLAIMER,
    }
