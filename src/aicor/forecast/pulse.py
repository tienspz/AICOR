"""ĐV-ĐR forecast layer — controlled nowcast/forecast run (FCST-01 … FCST-12).

One run produces: feature snapshot → per-company point estimates with 80/95
intervals → driver attribution → quality gate verdict → alerts → model card.
If anything is missing the run degrades to ``insufficient_evidence``; it never
blocks the descriptive ``E`` pipeline (PIPE-04, NFR-12).
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import numpy as np
import pandas as pd

from aicor.compute.config import AnalysisConfig, load_analysis_config
from aicor.forecast.alerts import alert_precision, evaluate_alerts
from aicor.forecast.backtest import quality_gate, rolling_origin_backtest
from aicor.forecast.model_card import build_model_card
from aicor.forecast.models import MODEL_AR1, MODEL_NAIVE, MODEL_RIDGE, fit_predict
from aicor.forecast.snapshot import (
    FEATURE_COLUMNS,
    FEATURE_LABELS,
    HORIZON_LABELS,
    build_samples,
    index_to_quarter,
    quarter_to_index,
    snapshot_population,
)

logger = logging.getLogger(__name__)

MODEL_ID = "aicor-pulse"


@dataclass
class PulseRun:
    """Everything one Pulse run produced, ready to be written as artifacts."""

    run_id: str
    model_id: str
    model_version: str
    as_of_date: str
    forecast_origin: str
    status: str                       # ok | insufficient_evidence | failed
    config_version: str
    feature_set_version: str
    generated_at: str
    results: list[dict[str, Any]] = field(default_factory=list)
    alerts: list[dict[str, Any]] = field(default_factory=list)
    samples: pd.DataFrame = field(default_factory=pd.DataFrame)
    backtest: dict[str, Any] = field(default_factory=dict)
    gate: dict[str, Any] = field(default_factory=dict)
    coverage: dict[str, Any] = field(default_factory=dict)
    model_card: dict[str, Any] = field(default_factory=dict)
    population: dict[str, Any] = field(default_factory=dict)
    reason: str = ""


def _model_version(config: AnalysisConfig) -> str:
    payload = (
        f"{config.version}|{config.feature_set_version}|{config.forecast_model}|"
        f"{','.join(f'{a:g}' for a in config.alpha_grid)}|{config.forecast_target}"
    )
    return f"pulse-{hashlib.sha256(payload.encode()).hexdigest()[:8]}"


def _inference_row(origin: pd.Series, prev: pd.Series | None, horizon: int) -> dict[str, Any]:
    origin_quarter = str(origin["calendar_quarter"])
    target = index_to_quarter(quarter_to_index(origin_quarter) + 1 + horizon)
    return {
        "company": origin["company"],
        "origin_quarter": origin_quarter,
        "target_quarter": target,
        "e_lag1": float(origin["E"]),
        "e_lag2": float(prev["E"]) if prev is not None and pd.notna(prev.get("E")) else np.nan,
        "out_lag1": float(origin["Out"]),
        "in_lag1": float(origin["In"]),
        "rd_intensity_lag1": float(origin["rd_intensity"]) if pd.notna(origin.get("rd_intensity")) else np.nan,
        "capex_intensity_lag1": (
            float(origin["capex_intensity"]) if pd.notna(origin.get("capex_intensity")) else np.nan
        ),
        "product_ma4q_lag1": float(origin["product_ma4q"]) if pd.notna(origin.get("product_ma4q")) else np.nan,
        "trends_ma4q_lag1": float(origin["trends_ma4q"]) if pd.notna(origin.get("trends_ma4q")) else np.nan,
        "is_msft": 1.0 if origin["company"] == "MSFT" else 0.0,
        "target_quarter_num": float(target.split("Q")[1]),
    }


def _latest_origins(series: pd.DataFrame) -> dict[str, tuple[pd.Series, pd.Series | None]]:
    """Latest published quarter per company, plus the quarter before it."""
    out: dict[str, tuple[pd.Series, pd.Series | None]] = {}
    for company in sorted(series["company"].unique()):
        g = series[series["company"] == company].copy()
        g["quarter_index"] = g["calendar_quarter"].map(quarter_to_index)
        g = g.sort_values("quarter_index").reset_index(drop=True)
        published = g[g["E"].notna()]
        if published.empty:
            continue
        origin = published.iloc[-1]
        prev_idx = len(g) - 2
        prev = g.iloc[prev_idx] if prev_idx >= 0 else None
        out[company] = (origin, prev)
    return out


def run_pulse(
    series: pd.DataFrame,
    *,
    config: AnalysisConfig | None = None,
    run_id: str | None = None,
    vintage_id: str = "raw-snapshot",
) -> PulseRun:
    """Execute a full Pulse run on the merged analysis series."""
    cfg = config or load_analysis_config()
    rid = run_id or f"pulse-{uuid4().hex[:10]}"
    version = _model_version(cfg)
    generated_at = datetime.now(UTC).isoformat(timespec="seconds")

    try:
        samples = build_samples(series, config=cfg)
    except Exception as exc:  # pragma: no cover - defensive, must not break E
        logger.exception("pulse: sample construction failed")
        return PulseRun(
            run_id=rid,
            model_id=MODEL_ID,
            model_version=version,
            as_of_date="",
            forecast_origin="",
            status="failed",
            config_version=cfg.version,
            feature_set_version=cfg.feature_set_version,
            generated_at=generated_at,
            reason=f"sample_build_failed: {exc}",
        )

    if samples.empty:
        return PulseRun(
            run_id=rid,
            model_id=MODEL_ID,
            model_version=version,
            as_of_date="",
            forecast_origin="",
            status="insufficient_evidence",
            config_version=cfg.version,
            feature_set_version=cfg.feature_set_version,
            generated_at=generated_at,
            reason="no_published_E_samples",
            population=snapshot_population(samples),
        )

    backtest = rolling_origin_backtest(samples, config=cfg)
    gate = quality_gate(backtest, config=cfg)
    origins = _latest_origins(series)
    forecast_origin = max((str(o["calendar_quarter"]) for o, _ in origins.values()), default="")
    as_of = max((str(o.get("available_at") or "") for o, _ in origins.values()), default="")

    results: list[dict[str, Any]] = []
    gate_passed = bool(gate.get("passed"))

    for company, (origin, prev) in origins.items():
        for horizon in cfg.forecast_horizons:
            row_dict = _inference_row(origin, prev, horizon)
            target_quarter = row_dict["target_quarter"]
            # Same horizon only: mixing h=0 and h=1 would double-count the same
            # target quarter with a different information set.
            train = samples[(samples["horizon"] == horizon) & (samples["target_quarter"] < target_quarter)]

            base_payload = {
                "run_id": rid,
                "company": company,
                "forecast_origin": str(origin["calendar_quarter"]),
                "target_period": target_quarter,
                "horizon": int(horizon),
                "horizon_label": HORIZON_LABELS.get(int(horizon), ""),
                "model_id": MODEL_ID,
                "model_version": version,
                "as_of_date": str(origin.get("available_at") or ""),
                "feature_set_version": cfg.feature_set_version,
                "config_version": cfg.version,
                "vintage_id": vintage_id,
                "n_train": len(train),
                "source_id": str(origin.get("source_id", "")),
                "source_url": str(origin.get("source_url", "")),
            }

            if len(train) < cfg.min_train_samples:
                results.append(
                    {
                        **base_payload,
                        "forecast_result_id": f"{rid}-{company}-h{horizon}",
                        "point": None,
                        "interval_low_80": None,
                        "interval_high_80": None,
                        "interval_low_95": None,
                        "interval_high_95": None,
                        "interval_method": "not_computed",
                        "status": "insufficient_evidence",
                        "reason": f"train_rows_{len(train)}_below_{cfg.min_train_samples}",
                        "attribution": [],
                        "quality_gate_passed": gate_passed,
                    }
                )
                continue

            row_series = pd.Series(row_dict)
            try:
                prediction = fit_predict(
                    train,
                    row_series,
                    model=cfg.forecast_model,
                    alpha_grid=cfg.alpha_grid,
                    interval_levels=cfg.interval_levels,
                    conformal_window=cfg.conformal_window,
                )
                naive_prediction = fit_predict(
                    train,
                    row_series,
                    model=MODEL_NAIVE,
                    interval_levels=cfg.interval_levels,
                )
                ar1_prediction = fit_predict(
                    train,
                    row_series,
                    model=MODEL_AR1,
                    interval_levels=cfg.interval_levels,
                )
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception("pulse: model fit failed for %s h%s", company, horizon)
                results.append(
                    {
                        **base_payload,
                        "forecast_result_id": f"{rid}-{company}-h{horizon}",
                        "point": None,
                        "interval_low_80": None,
                        "interval_high_80": None,
                        "interval_low_95": None,
                        "interval_high_95": None,
                        "interval_method": "not_computed",
                        "status": "insufficient_evidence",
                        "reason": f"model_error: {exc}",
                        "attribution": [],
                        "quality_gate_passed": gate_passed,
                    }
                )
                continue

            top_drivers = [
                {
                    "feature": c["feature"],
                    "label": FEATURE_LABELS.get(str(c["feature"]), str(c["feature"])),
                    "value": c["value"],
                    "contribution": c["contribution"],
                    "direction": c["direction"],
                }
                for c in prediction.contributions[:3]
            ]

            results.append(
                {
                    **base_payload,
                    "forecast_result_id": f"{rid}-{company}-h{horizon}",
                    "point": round(float(prediction.value), 6),
                    "interval_low_80": round(float(prediction.interval_low_80), 6),
                    "interval_high_80": round(float(prediction.interval_high_80), 6),
                    "interval_low_95": round(float(prediction.interval_low_95), 6),
                    "interval_high_95": round(float(prediction.interval_high_95), 6),
                    "interval_method": prediction.interval_method,
                    "status": "ok" if gate_passed else "insufficient_evidence",
                    "label": "forecast" if gate_passed else "experimental_insufficient_evidence",
                    "reason": "" if gate_passed else "quality_gate_not_passed",
                    "attribution": top_drivers,
                    "quality_gate_passed": gate_passed,
                    "baseline_point": round(float(naive_prediction.value), 6),
                    "ar1_point": round(float(ar1_prediction.value), 6),
                    "alpha": prediction.alpha,
                    "display_point": gate_passed,
                    "experimental": True,
                }
            )

    last_published_e = {
        company: (float(origin["E"]) if pd.notna(origin.get("E")) else None)
        for company, (origin, _) in origins.items()
    }
    alerts = evaluate_alerts(
        results,
        run_id=rid,
        config=cfg,
        gate_passed=gate_passed,
        last_published_e=last_published_e,
    )

    card = build_model_card(
        run_id=rid,
        model_id=MODEL_ID,
        model_version=version,
        config=cfg,
        gate=gate,
        backtest=backtest,
        samples=samples,
        as_of_date=as_of,
    )

    return PulseRun(
        run_id=rid,
        model_id=MODEL_ID,
        model_version=version,
        as_of_date=as_of,
        forecast_origin=forecast_origin,
        status="ok" if gate_passed else "insufficient_evidence",
        config_version=cfg.version,
        feature_set_version=cfg.feature_set_version,
        generated_at=generated_at,
        results=results,
        alerts=alerts,
        samples=samples,
        backtest=backtest,
        gate=gate,
        coverage=backtest.get("coverage", {}),
        model_card=card,
        population=snapshot_population(samples),
        reason="" if gate_passed else "quality_gate_not_passed",
    )


def results_frame(results: list[dict[str, Any]]) -> pd.DataFrame:
    """Flatten Pulse results into the ``forecast_results`` artifact."""
    columns = [
        "forecast_result_id",
        "run_id",
        "company",
        "forecast_origin",
        "target_period",
        "horizon",
        "model_id",
        "model_version",
        "as_of_date",
        "feature_set_version",
        "config_version",
        "point",
        "interval_low_80",
        "interval_high_80",
        "interval_low_95",
        "interval_high_95",
        "interval_method",
        "status",
        "reason",
        "quality_gate_passed",
        "n_train",
        "baseline_point",
        "ar1_point",
        "alpha",
        "source_id",
        "source_url",
    ]
    if not results:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(results).reindex(columns=columns)


def backtest_frame(backtest: dict[str, Any]) -> pd.DataFrame:
    folds = backtest.get("folds")
    if folds is None or len(folds) == 0:
        return pd.DataFrame(
            columns=["horizon", "target_quarter", "company", "model", "actual", "predicted", "baseline", "n_train"]
        )
    return folds


def coverage_frame(backtest: dict[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for horizon, groups in (backtest.get("coverage") or {}).items():
        for group, entries in groups.items():
            for key, payload in entries.items():
                model, level = key.rsplit("_", 1)
                rows.append(
                    {
                        "horizon": int(horizon),
                        "group": group,
                        "model": model,
                        "level": int(level) / 100.0,
                        "coverage": payload["coverage"],
                        "n": payload["n"],
                    }
                )
    return pd.DataFrame(rows)


__all__ = [
    "FEATURE_COLUMNS",
    "MODEL_RIDGE",
    "PulseRun",
    "alert_precision",
    "backtest_frame",
    "coverage_frame",
    "results_frame",
    "run_pulse",
]
