"""
AICOR Pre-computed Web JSON Bundles Exporter (Task BE-04)
Implements FR-14 (React reads precomputed data, never recalculates E)
and NFR-01 (page load < 3s via small static JSON).

Outputs in data/processed/:
- chart_series.json
- timeline_events.json
- portfolio_baseline.json
"""
import csv
import json
import logging
import math
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Dict, List, Optional

from src.common.config import CLEANED_DATA_DIR, PROCESSED_DATA_DIR
from src.collection.storage import get_sync_timestamp

logger = logging.getLogger("aicor.exporter")

KEY_BY_COMPANY_ID = {1: "MSFT", 2: "OpenAI", 3: "Anthropic"}
NAMES = {1: "Microsoft", 2: "OpenAI", 3: "Anthropic"}
PORTFOLIO_DISCLAIMER = "Công cụ minh họa, không phải khuyến nghị đầu tư."


def _num(value: object) -> Optional[float]:
    if value is None:
        return None
    s = str(value).strip()
    if s == "" or s.lower() in ("none", "nan", "null"):
        return None
    try:
        v = float(s)
    except (ValueError, TypeError):
        return None
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v


def _read_csv(csv_file: Path) -> List[Dict]:
    if not csv_file.exists() or csv_file.stat().st_size == 0:
        return []
    with open(csv_file, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _build_chart_series(fact_rows: List[Dict]) -> Dict:
    quarters = sorted({(r.get("quarter") or "").strip() for r in fact_rows if r.get("quarter")})
    companies: Dict[str, Dict] = {}
    for cid, key in KEY_BY_COMPANY_ID.items():
        series = []
        for r in sorted(
            [x for x in fact_rows if str(x.get("company_id")).strip() == str(cid)],
            key=lambda x: x.get("quarter", ""),
        ):
            series.append(
                {
                    "quarter": (r.get("quarter") or "").strip(),
                    "in_score": _num(r.get("in_score")),
                    "out_score": _num(r.get("out_score")),
                    "e_score": _num(r.get("e_score")),
                    "rnd_spend": _num(r.get("rnd_spend")),
                    "ai_spend_est": _num(r.get("ai_spend_est")),
                    "est_confidence": (r.get("est_confidence") or "").strip() or None,
                    "trends_qavg": _num(r.get("trends_qavg")),
                    "product_score": _num(r.get("product_score")),
                    "product_ma4q": _num(r.get("product_ma4q")),
                    "trends_ma4q": _num(r.get("trends_ma4q")),
                    "valid_from": (r.get("valid_from") or "").strip() or None,
                }
            )
        companies[key] = {"company_id": cid, "name": NAMES[cid], "series": series}
    return {
        "generated_at": get_sync_timestamp(),
        "quarters": quarters,
        "companies": companies,
        "note": "E = Out - In là chênh lệch tương đối so với lịch sử của chính công ty, không phải ROI.",
    }


def _build_timeline_events() -> List[Dict]:
    events: List[Dict] = []
    for r in _read_csv(CLEANED_DATA_DIR / "events_launch_clean.csv"):
        try:
            cid = int(r.get("company_id") or 0)
        except (ValueError, TypeError):
            continue
        events.append(
            {
                "date": (r.get("launch_date") or "").strip(),
                "quarter": (r.get("quarter") or "").strip(),
                "type": "launch",
                "company_id": cid,
                "company_name": (r.get("company_name") or NAMES.get(cid, "")).strip(),
                "title": (r.get("product_name") or "").strip(),
                "category": (r.get("category") or "").strip().upper() or None,
                "points": _num(r.get("points")),
                "source_url": (r.get("source_url") or "").strip(),
            }
        )
    for r in _read_csv(CLEANED_DATA_DIR / "events_funding_clean.csv"):
        try:
            cid = int(r.get("company_id") or 0)
        except (ValueError, TypeError):
            continue
        events.append(
            {
                "date": (r.get("funding_date") or "").strip(),
                "quarter": (r.get("quarter") or "").strip(),
                "type": "funding",
                "company_id": cid,
                "company_name": (r.get("company_name") or NAMES.get(cid, "")).strip(),
                "title": f"Funding round {r.get('funding_date', '')}".strip(),
                "amount": _num(r.get("amount")),
                "valuation": _num(r.get("valuation")),
                "source_url": (r.get("source_url") or "").strip(),
            }
        )
    for r in _read_csv(CLEANED_DATA_DIR / "events_relationship_clean.csv"):
        events.append(
            {
                "date": (r.get("event_date") or "").strip(),
                "quarter": (r.get("quarter") or "").strip(),
                "type": "relationship",
                "company_id": None,
                "company_name": None,
                "title": (r.get("parties") or "").strip(),
                "parties": (r.get("parties") or "").strip(),
                "rel_type": (r.get("rel_type") or "").strip(),
                "quote": (r.get("quote") or "").strip() or None,
                "source_url": (r.get("source_url") or "").strip(),
            }
        )
    events.sort(key=lambda e: (e.get("date") or "", e.get("type") or ""))
    return events


def _build_portfolio_baseline(fact_rows: List[Dict]) -> Dict:
    quarters = sorted({(r.get("quarter") or "").strip() for r in fact_rows if r.get("quarter")})
    window = quarters[-4:] if len(quarters) >= 4 else quarters
    medians: Dict[str, Optional[float]] = {}
    for cid, key in KEY_BY_COMPANY_ID.items():
        vals = [
            _num(r.get("e_score"))
            for r in fact_rows
            if str(r.get("company_id")).strip() == str(cid)
            and (r.get("quarter") or "").strip() in window
        ]
        vals = [v for v in vals if v is not None]
        medians[key] = round(float(median(vals)), 3) if vals else None
    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "reference_window": window,
        "method": "median(E) of the 4 most recent quarters per company; "
        "portfolio score = sum(w_c * median(E_c)).",
        "medians": medians,
        "disclaimer": PORTFOLIO_DISCLAIMER,
    }


def export_web_json_bundles(processed_dir: Optional[Path] = None) -> Dict[str, str]:
    """Reads fact_quarterly.csv + cleaned events and writes 3 static JSON bundles.

    NaN/Inf/empty numerics are converted to null so React can JSON.parse safely.
    Returns {bundle_name: file_path_str}.
    """
    out_dir = Path(processed_dir) if processed_dir is not None else PROCESSED_DATA_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    fact_rows = _read_csv(out_dir / "fact_quarterly.csv")
    chart = _build_chart_series(fact_rows)
    timeline = _build_timeline_events()
    baseline = _build_portfolio_baseline(fact_rows)

    outputs = {
        "chart_series": out_dir / "chart_series.json",
        "timeline_events": out_dir / "timeline_events.json",
        "portfolio_baseline": out_dir / "portfolio_baseline.json",
    }
    payloads = {
        "chart_series": chart,
        "timeline_events": {
            "generated_at": get_sync_timestamp(),
            "count": len(timeline),
            "events": timeline,
        },
        "portfolio_baseline": baseline,
    }
    for name, path in outputs.items():
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payloads[name], f, ensure_ascii=False, indent=2, allow_nan=False)
        logger.info(f"Wrote {path.name} ({len(json.dumps(payloads[name], ensure_ascii=False))} chars).")

    return {name: str(path) for name, path in outputs.items()}
