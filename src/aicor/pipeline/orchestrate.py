"""Pipeline orchestration: preprocess → compute → forecast → publish → monitor.

One entry point so a scheduled worker and a local developer run exactly the
same sequence. A failure in the Pulse layer never removes the descriptive
metrics; a failure before compute is reported, not hidden.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd

from aicor.compute.config import AnalysisConfig, load_analysis_config
from aicor.compute.engine import compute_analysis, series_frame
from aicor.compute.features import build_feature_matrix, to_long_features
from aicor.compute.provenance import build_provenance
from aicor.forecast.model_card import model_card_markdown
from aicor.forecast.pulse import (
    PulseRun,
    backtest_frame,
    coverage_frame,
    results_frame,
    run_pulse,
)
from aicor.pipeline.artifacts import (
    write_analysis_artifacts,
    write_json,
    write_pulse_artifacts,
)
from aicor.pipeline.dashboard_data import build_dashboard_payload
from aicor.pipeline.ops import (
    LOGGER_NAME,
    freshness_snapshot,
    read_sync_log,
    write_health,
)
from aicor.pipeline.publish import publish_dashboard

logger = logging.getLogger(LOGGER_NAME)


@dataclass
class CycleResult:
    """Outcome of one analysis+publish cycle."""

    run_id: str
    status: str = "failed"            # success | partial | failed
    stages: dict[str, str] = field(default_factory=dict)
    artifacts: dict[str, Any] = field(default_factory=dict)
    manifest: dict[str, Any] | None = None
    health: dict[str, Any] | None = None
    pulse: PulseRun | None = None
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status,
            "stages": self.stages,
            "artifacts": self.artifacts,
            "manifest": self.manifest,
            "warnings": self.warnings,
            "pulse": {
                "status": self.pulse.status if self.pulse else "not_run",
                "reason": self.pulse.reason if self.pulse else None,
                "model_version": self.pulse.model_version if self.pulse else None,
                "quality_gate_passed": bool(self.pulse.gate.get("passed")) if self.pulse else None,
            },
        }


def new_run_id() -> str:
    return f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}-{uuid4().hex[:6]}"


def load_processed(data_dir: str | Path = "data") -> dict[str, pd.DataFrame]:
    """Load the processed layer written by the preprocessing stage."""
    proc = Path(data_dir) / "processed"
    out: dict[str, pd.DataFrame] = {}
    for key, name in (
        ("panel", "panel_quarterly.csv"),
        ("products", "ai_products.csv"),
        ("trends", "google_trends_quarterly.csv"),
        ("market", "market_quarterly.csv"),
    ):
        path = proc / name
        if path.exists():
            out[key] = pd.read_csv(path)
    return out


def _panel_status(panel: pd.DataFrame) -> str:
    if panel is None or panel.empty:
        return "failed"
    if "sync_status" not in panel.columns:
        return "success"
    values = set(panel["sync_status"].dropna().astype(str))
    if "failed" in values:
        return "failed"
    if "partial" in values or "empty" in values:
        return "partial"
    return "success"


def run_analysis_cycle(
    *,
    data_dir: str | Path = "data",
    out_dir: str | Path = "data/processed",
    publish_dir: str | Path = "web/data",
    config: AnalysisConfig | None = None,
    publish: bool = True,
    run_id: str | None = None,
) -> CycleResult:
    """Compute metrics, run Pulse, write artifacts and publish atomically."""
    cfg = config or load_analysis_config()
    rid = run_id or new_run_id()
    result = CycleResult(run_id=rid)
    started = time.perf_counter()

    loaded = load_processed(data_dir)
    panel = loaded.get("panel", pd.DataFrame())
    products = loaded.get("products", pd.DataFrame())
    trends = loaded.get("trends", pd.DataFrame())
    market = loaded.get("market", pd.DataFrame())

    if panel is None or panel.empty:
        result.stages["load"] = "failed"
        result.status = "failed"
        result.warnings.append("panel_quarterly.csv missing or empty — run the preprocessing stage first")
        result.health = _write_health(
            result,
            data_dir=data_dir,
            latest_quarter=None,
            data_status="failed",
            sync_entries=read_sync_log(data_dir),
            warnings=result.warnings,
            duration=time.perf_counter() - started,
        )
        return result

    result.stages["load"] = "ok"

    provenance = build_provenance(data_dir)
    features = build_feature_matrix(panel, products, trends, config=cfg, provenance=provenance)
    features_long = to_long_features(features, cfg)
    analysis = compute_analysis(features, cfg)
    series = series_frame(features, cfg)
    result.stages["compute"] = "ok"

    result.artifacts["analysis"] = write_analysis_artifacts(
        features_long=features_long,
        analysis=analysis,
        provenance=provenance,
        out_dir=out_dir,
        config=cfg,
    )

    pulse: PulseRun | None = None
    try:
        pulse = run_pulse(series, config=cfg, run_id=rid)
        result.pulse = pulse
        result.stages["forecast"] = pulse.status
        if pulse.status == "failed":
            result.warnings.append(f"pulse failed: {pulse.reason}")
        elif pulse.status == "insufficient_evidence":
            result.warnings.append(f"pulse is experimental (gate not passed): {pulse.reason}")
        result.artifacts["pulse"] = write_pulse_artifacts(
            results=results_frame(pulse.results),
            alerts=pd.DataFrame(pulse.alerts),
            folds=backtest_frame(pulse.backtest),
            coverage=coverage_frame(pulse.backtest),
            model_card=pulse.model_card,
            model_card_md=model_card_markdown(pulse.model_card),
            out_dir=out_dir,
            config=cfg,
        )
    except Exception as exc:  # pragma: no cover - defensive: E must survive
        logger.exception("orchestrate: pulse stage failed")
        result.stages["forecast"] = "failed"
        result.warnings.append(f"pulse stage failed: {exc}")
        write_pulse_artifacts(
            results=results_frame([]),
            alerts=pd.DataFrame(),
            folds=backtest_frame({}),
            coverage=coverage_frame({}),
            model_card={"model_version": None, "limitations": [], "quality_gate": {"passed": False}},
            model_card_md="# Model card unavailable\n\nPulse stage failed; see pipeline health.\n",
            out_dir=out_dir,
            config=cfg,
        )

    data_status = _panel_status(panel)
    sync_entries = read_sync_log(data_dir)

    if publish:
        payload = build_dashboard_payload(
            series=series,
            provenance=provenance,
            products=products,
            market=market,
            pulse=pulse,
            config=cfg,
            run_id=rid,
            data_status=data_status,
            sync_entries=sync_entries,
        )
        latest_quarter = payload["meta"]["as_of_quarter"]
        freshness = freshness_snapshot(
            generated_at=payload["meta"]["generated_at"],
            latest_data_quarter=latest_quarter,
            data_status=data_status,
            sync_entries=sync_entries,
        )
        result.manifest = publish_dashboard(
            payload,
            run_id=rid,
            out_dir=publish_dir,
            freshness=freshness,
            keep_versions=cfg.keep_versions,
        )
        result.stages["publish"] = "ok"
    else:
        result.stages["publish"] = "skipped"

    result.status = "success" if data_status == "success" else "partial"
    if pulse is None or pulse.status == "failed":
        result.status = "partial" if result.status != "failed" else result.status

    result.health = _write_health(
        result,
        data_dir=data_dir,
        latest_quarter=str(series["calendar_quarter"].max()) if not series.empty else None,
        data_status=data_status,
        sync_entries=sync_entries,
        warnings=result.warnings,
        duration=time.perf_counter() - started,
    )
    write_json(
        {**result.as_dict(), "health_path": "quality/health.json"},
        Path(data_dir) / "pipeline_manifest.json",
    )
    logger.info(
        "cycle: run=%s status=%s pulse=%s manifest=%s",
        rid,
        result.status,
        pulse.status if pulse else "not_run",
        (result.manifest or {}).get("dataset_version", "")[:12],
    )
    return result


def _write_health(
    result: CycleResult,
    *,
    data_dir: str | Path,
    latest_quarter: str | None,
    data_status: str,
    sync_entries: list[dict[str, Any]],
    warnings: list[str],
    duration: float,
) -> dict[str, Any]:
    payload = {
        "run_id": result.run_id,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "status": result.status,
        "stages": result.stages,
        "duration_seconds": round(duration, 3),
        "latest_data_quarter": latest_quarter,
        "data_status": data_status,
        "warnings": warnings,
        "freshness": freshness_snapshot(
            generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
            latest_data_quarter=latest_quarter,
            data_status=data_status,
            sync_entries=sync_entries,
        ),
    }
    write_health(payload, path=Path(data_dir) / "quality" / "health.json")
    return payload
