"""Dashboard payload assembly (Phase 3).

Everything the UI shows is copied from a published artifact here. The browser
performs no arithmetic on research metrics — it formats and renders (DSH-01).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import numpy as np
import pandas as pd

from aicor.compute.config import AnalysisConfig
from aicor.forecast.pulse import PulseRun, coverage_frame
from aicor.pipeline.ops import freshness_snapshot

COMPANY_META = {
    "MSFT": {
        "name": "Microsoft Corporation",
        "ticker": "MSFT",
        "exchange": "NASDAQ",
        "fiscal_year_end": "06-30",
        "cik": "789019",
    },
    "GOOGL": {
        "name": "Alphabet Inc.",
        "ticker": "GOOGL",
        "exchange": "NASDAQ",
        "fiscal_year_end": "12-31",
        "cik": "1652044",
    },
}

DISCLAIMERS = {
    "e_score": (
        "E = Out − In là chỉ số tương đối để quan sát xu hướng và độ nhạy trọng số. "
        "E không phải ROI, không phải lợi nhuận và không chứng minh quan hệ nhân quả."
    ),
    "experimental": (
        "AICOR Pulse là lớp thử nghiệm: kết quả có khoảng tin cậy, as-of date và model version. "
        "Không phải khuyến nghị đầu tư."
    ),
    "attribution": (
        "Driver attribution mô tả yếu tố đóng góp trong mô hình, không phải quan hệ nhân quả."
    ),
    "provenance": (
        "Mỗi giá trị truy vết được về source_id → source_url (SEC filing). "
        "Giá trị không đủ điều kiện được để NULL kèm lý do, không điền 0."
    ),
}


def _clean(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        value = float(value)
    if isinstance(value, float):
        return None if (np.isnan(value) or np.isinf(value)) else round(value, 6)
    if isinstance(value, (pd.Timestamp,)):
        return value.date().isoformat()
    if value is pd.NaT:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, (int, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): _clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean(v) for v in value]
    return str(value)


def _series_rows(series: pd.DataFrame, company: str) -> list[dict[str, Any]]:
    g = series[series["company"] == company].copy()
    rows: list[dict[str, Any]] = []
    for _, r in g.iterrows():
        rows.append(
            _clean(
                {
                    "quarter": r["calendar_quarter"],
                    "period_end_date": r["period_end_date"],
                    "available_at": r.get("available_at"),
                    "In": r.get("In"),
                    "Out": r.get("Out"),
                    "E": r.get("E"),
                    "E_simple": r.get("E_simple"),
                    "E_tech": r.get("E_tech"),
                    "robustness": r.get("E_robustness"),
                    "status": r.get("E_status"),
                    "product_score": r.get("product_score"),
                    "product_ma4q": r.get("product_ma4q"),
                    "trends_score": r.get("trends_score"),
                    "trends_ma4q": r.get("trends_ma4q"),
                    "rd_expense": r.get("rd_expense"),
                    "rd_intensity": r.get("rd_intensity"),
                    "capex_intensity": r.get("capex_intensity"),
                    "z_in": r.get("z_in"),
                    "z_product_ma4q": r.get("z_product_ma4q"),
                    "z_trends_ma4q": r.get("z_trends_ma4q"),
                    "z_in_status": r.get("z_in_status"),
                    "z_in_n_obs": r.get("z_in_n_obs"),
                    "source_id": r.get("source_id"),
                    "source_url": r.get("source_url"),
                }
            )
        )
    return rows


def _events_payload(products: pd.DataFrame, limit: int = 220) -> list[dict[str, Any]]:
    if products is None or products.empty:
        return []
    df = products.copy()
    df["announcement_date"] = pd.to_datetime(df["announcement_date"], errors="coerce")
    df = df.dropna(subset=["announcement_date"]).sort_values("announcement_date", ascending=False)
    df = df.head(limit)
    out: list[dict[str, Any]] = []
    for _, r in df.iterrows():
        out.append(
            _clean(
                {
                    "date": r["announcement_date"].date().isoformat(),
                    "company": r.get("company"),
                    "name": r.get("product_name"),
                    "category": r.get("category"),
                    "rationale": r.get("category_rationale"),
                    "review_status": r.get("review_status"),
                    "source_url": r.get("source_url"),
                    "description": (str(r.get("description") or ""))[:280],
                }
            )
        )
    return out


def _market_payload(market: pd.DataFrame, latest_quarter: str | None) -> dict[str, list[dict[str, Any]]]:
    if market is None or market.empty:
        return {}
    out: dict[str, list[dict[str, Any]]] = {}
    for company, g in market.groupby("company"):
        g = g.sort_values("calendar_quarter")
        # Never show context from a quarter later than the analysis as-of
        # quarter: it would read as information the model actually had.
        if latest_quarter:
            g = g[g["calendar_quarter"] <= latest_quarter]
        out[str(company)] = [
            _clean({"quarter": r["calendar_quarter"], "adj_close": r.get("adj_close"), "volume": r.get("volume")})
            for _, r in g.iterrows()
        ]
    return out


def _status_payload(
    *,
    series: pd.DataFrame,
    provenance: pd.DataFrame,
    sync_entries: list[dict[str, Any]],
    data_status: str,
) -> dict[str, Any]:
    coverage: dict[str, Any] = {}
    for company, g in series.groupby("company"):
        ok = int(g["E"].notna().sum())
        coverage[str(company)] = {
            "quarters_in_panel": len(g),
            "quarters_with_E": ok,
            "quarters_with_insufficient_window": int((g.get("E_status") == "insufficient_window").sum()),
            "first_quarter": str(g["calendar_quarter"].iloc[0]) if len(g) else None,
            "last_quarter": str(g["calendar_quarter"].iloc[-1]) if len(g) else None,
            "missing_reasons": sorted({str(s) for s in g.get("E_status", pd.Series(dtype=str)).dropna().unique()}),
        }

    provenance_rows = []
    if provenance is not None and not provenance.empty:
        df = provenance.copy()
        df = df[pd.to_datetime(df["period_end_date"], errors="coerce") >= pd.Timestamp("2021-01-01")]
        df = df.sort_values(["company", "period_end_date"]).tail(60)
        provenance_rows = [
            _clean(
                {
                    "source_id": r["source_id"],
                    "company": r["company"],
                    "period_end_date": r["period_end_date"],
                    "source_url": r["source_url"],
                    "filing_date": r.get("filing_date"),
                    "accession_number": r.get("accession_number"),
                    "form": r.get("form"),
                    "tier": r.get("source_tier"),
                    "verification_status": r.get("verification_status"),
                }
            )
            for _, r in df.iterrows()
        ]

    return {
        "data_status": data_status,
        "coverage": coverage,
        "recent_sync": [
            _clean(
                {
                    "source_type": e.get("source_type"),
                    "company": e.get("company"),
                    "status": e.get("sync_status"),
                    "finished_at": e.get("finished_at"),
                    "records_fetched": e.get("records_fetched"),
                    "error_message": e.get("error_message"),
                }
            )
            for e in reversed(sync_entries)
        ],
        "provenance": provenance_rows,
        "freshness": {},
    }


def _pulse_payload(pulse: PulseRun | None) -> dict[str, Any]:
    if pulse is None:
        return {
            "available": False,
            "status": "unavailable",
            "reason": "pulse_not_run",
            "results": [],
            "alerts": [],
            "gate": {},
            "metrics": {},
            "coverage": [],
            "model_card": {},
            "population": {},
        }

    metrics = (pulse.backtest or {}).get("metrics") or {}
    return _clean(
        {
            "available": pulse.status != "failed",
            "status": pulse.status,
            "reason": pulse.reason,
            "run_id": pulse.run_id,
            "model_id": pulse.model_id,
            "model_version": pulse.model_version,
            "as_of_date": pulse.as_of_date,
            "forecast_origin": pulse.forecast_origin,
            "generated_at": pulse.generated_at,
            "results": pulse.results,
            "alerts": pulse.alerts,
            "gate": pulse.gate,
            "metrics": metrics,
            "n_folds": (pulse.backtest or {}).get("n_folds", {}),
            "coverage": coverage_frame(pulse.backtest or {}).to_dict("records"),
            "model_card": pulse.model_card,
            "population": pulse.population,
            "disclaimer": DISCLAIMERS["experimental"],
            "attribution_note": DISCLAIMERS["attribution"],
        }
    )


def build_dashboard_payload(
    *,
    series: pd.DataFrame,
    provenance: pd.DataFrame,
    products: pd.DataFrame,
    market: pd.DataFrame,
    pulse: PulseRun | None,
    config: AnalysisConfig,
    run_id: str,
    data_status: str,
    sync_entries: list[dict[str, Any]],
) -> dict[str, Any]:
    """Assemble the immutable dashboard payload."""
    generated_at = datetime.now(UTC).isoformat(timespec="seconds")
    quarters = sorted(series["calendar_quarter"].unique().tolist()) if not series.empty else []
    latest_quarter = quarters[-1] if quarters else None

    status = _status_payload(
        series=series,
        provenance=provenance,
        sync_entries=sync_entries,
        data_status=data_status,
    )
    status["freshness"] = freshness_snapshot(
        generated_at=generated_at,
        latest_data_quarter=latest_quarter,
        data_status=data_status,
        sync_entries=sync_entries,
    )

    return {
        "meta": _clean(
            {
                "schema_version": config.schema_version,
                "run_id": run_id,
                "generated_at": generated_at,
                "config_version": config.version,
                "formula_version": config.formula_version,
                "feature_set_version": config.feature_set_version,
                "as_of_quarter": latest_quarter,
                "quarters": quarters,
                "companies": [{"id": k, **v} for k, v in COMPANY_META.items()],
                "weights": config.weights,
                "zscore": {
                    "window": config.zscore_window,
                    "min_quarters": config.zscore_min_quarters,
                    "min_observations": config.zscore_min_observations,
                    "method": (
                        "z16Q: cửa sổ 16 quý gần nhất, tính riêng từng công ty; "
                        "chưa đủ 16 quý thì ghi status=insufficient_window và không dùng cho E."
                    ),
                },
                "methodology": {
                    "In": "In = z16Q(R&D theo quý) — proxy cho đầu tư AI, không phải chi tiêu AI được công bố.",
                    "Out": "Out = w_product × z(Product MA4Q) + w_trends × z(Trends MA4Q).",
                    "E": "E = Out − In. Chỉ số tương đối, không phải ROI.",
                    "product_score": "Product Score = 3×A + 2×B + 1×C theo rubric v1-provisional.",
                    "ma4q": "MA4Q: trung bình động 4 quý, bắt buộc đủ 4 quý.",
                    "units": "Tiền tệ: USD millions. z-score: không đơn vị. Ratio: thập phân (0.12 = 12%).",
                },
                "disclaimers": DISCLAIMERS,
                "freshness_note": "UI tự kiểm tra manifest mỗi 30 giây để phát hiện bản publish mới.",
            }
        ),
        "series": {
            company: _series_rows(series, company) for company in sorted(series["company"].unique())
        } if not series.empty else {},
        "events": _events_payload(products),
        "market": _market_payload(market, latest_quarter),
        "status": _clean(status),
        "pulse": _pulse_payload(pulse),
    }
