"""Deterministic artifact writers (NFR-01, NFR-03).

Everything the dashboard reads is produced here and nowhere else. CSV output
is written with a fixed column order, no index and ``\\n`` line endings so two
runs on the same snapshot are byte-identical.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from aicor.compute.config import AnalysisConfig, load_analysis_config

ANALYSIS_MANIFEST = "analysis_manifest.json"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def write_csv(df: pd.DataFrame, path: str | Path, columns: list[str] | None = None) -> Path:
    """Write *df* with a stable column order and LF endings."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    out = df.copy()
    if columns:
        for col in columns:
            if col not in out.columns:
                out[col] = None
        out = out[columns]
    out.to_csv(target, index=False, lineterminator="\n")
    return target


def write_json(payload: Any, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=_json_default) + "\n",
        encoding="utf-8",
    )
    return target


def _json_default(value: Any):
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, float) and math.isnan(value):
        return None
    return str(value)


def write_analysis_artifacts(
    *,
    features_long: pd.DataFrame,
    analysis: pd.DataFrame,
    provenance: pd.DataFrame,
    out_dir: str | Path = "data/processed",
    config: AnalysisConfig | None = None,
) -> dict[str, Any]:
    """Write ``features_quarterly.csv`` + ``analysis_results.csv`` + manifest."""
    cfg = config or load_analysis_config()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    features_path = write_csv(features_long, out / "features_quarterly.csv")
    analysis_path = write_csv(analysis, out / "analysis_results.csv")
    provenance_path = write_csv(
        provenance,
        out / "provenance.csv",
        columns=[
            "source_id",
            "company",
            "period_end_date",
            "source_url",
            "filing_date",
            "accession_number",
            "form",
            "source_tier",
            "verification_status",
        ],
    )

    manifest = {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "config_version": cfg.version,
        "formula_version": cfg.formula_version,
        "feature_set_version": cfg.feature_set_version,
        "row_counts": {
            "features_quarterly": len(features_long),
            "analysis_results": len(analysis),
            "provenance": len(provenance),
        },
        "artifacts": {
            path.name: sha256_file(path)
            for path in (features_path, analysis_path, provenance_path)
        },
    }
    write_json(manifest, out / ANALYSIS_MANIFEST)
    return manifest


def write_pulse_artifacts(
    *,
    results: pd.DataFrame,
    alerts: pd.DataFrame,
    folds: pd.DataFrame,
    coverage: pd.DataFrame,
    model_card: dict[str, Any],
    model_card_md: str,
    out_dir: str | Path = "data/processed",
    config: AnalysisConfig | None = None,
) -> dict[str, Any]:
    """Write the Pulse artifacts plus the model registry entry."""
    cfg = config or load_analysis_config()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    results_path = write_csv(results, out / "forecast_results.csv")
    alerts_path = write_csv(alerts, out / "alert_log.csv")
    folds_path = write_csv(folds, out / "forecast_backtest.csv")
    coverage_path = write_csv(coverage, out / "forecast_coverage.csv")
    card_path = write_json(model_card, out / "model_registry.json")
    (out / "model_card.md").write_text(model_card_md, encoding="utf-8")

    manifest = {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "config_version": cfg.version,
        "feature_set_version": cfg.feature_set_version,
        "model_version": model_card.get("model_version"),
        "row_counts": {
            "forecast_results": len(results),
            "alert_log": len(alerts),
            "forecast_backtest": len(folds),
        },
        "artifacts": {
            path.name: sha256_file(path)
            for path in (results_path, alerts_path, folds_path, coverage_path, card_path)
        },
        "model_card_hash": sha256_bytes(
            json.dumps(model_card, sort_keys=True, default=str).encode()
        ),
    }
    write_json(manifest, out / "pulse_manifest.json")
    return manifest
