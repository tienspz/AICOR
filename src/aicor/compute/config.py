"""Versioned configuration for the metric engine and ĐV-ĐR forecast layer (NFR-03).

Reads ``config/analysis.yaml``. Deterministic defaults are embedded so the
engine still runs (with recorded defaults) if the file is missing — but the
loaded ``config_version`` always travels with every artifact.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG_PATH = Path("config/analysis.yaml")

DEFAULT_WEIGHTS: dict[str, dict[str, float]] = {
    "baseline": {"product": 0.6, "trends": 0.4},
    "simple": {"product": 0.5, "trends": 0.5},
    "tech": {"product": 0.7, "trends": 0.3},
}

DEFAULT_KEYWORDS: dict[str, list[str]] = {
    "MSFT": ["Microsoft AI", "Azure AI"],
    "GOOGL": ["Google AI", "Gemini"],
}


@dataclass(frozen=True)
class AnalysisConfig:
    """Immutable analytical configuration."""

    version: str = "aicor-analysis-v1"
    formula_version: str = "metrics-v1"
    feature_set_version: str = "features-v1"

    zscore_window: int = 16
    zscore_min_quarters: int = 16
    zscore_min_observations: int = 4
    zscore_ddof: int = 1

    ma4q_min_periods: int = 4

    product_weights: dict[str, int] = field(default_factory=lambda: {"A": 3, "B": 2, "C": 1})

    trends_keywords: dict[str, list[str]] = field(default_factory=lambda: dict(DEFAULT_KEYWORDS))

    weights: dict[str, dict[str, float]] = field(default_factory=lambda: dict(DEFAULT_WEIGHTS))

    forecast_model: str = "ridge"
    forecast_horizons: tuple[int, ...] = (0, 1)
    forecast_target: str = "E"
    min_train_samples: int = 4
    alpha_grid: tuple[float, ...] = (0.01, 0.1, 1.0, 10.0)
    interval_levels: tuple[float, ...] = (0.8, 0.95)
    conformal_window: int = 8
    random_state: int = 42
    quality_gate_require_both: bool = True

    alert_e_threshold: float = -0.25
    alert_nowcast_deviation: float = 0.75
    alert_severity: dict[str, str] = field(
        default_factory=lambda: {
            "interval_crosses_zero": "WARN",
            "e_below_threshold": "CRITICAL",
            "nowcast_deviation": "INFO",
        }
    )

    schema_version: str = "dashboard-v1"
    keep_versions: int = 5
    source_path: str = "defaults"

    @property
    def baseline_weights(self) -> dict[str, float]:
        return self.weights.get("baseline", {"product": 0.6, "trends": 0.4})


def _as_float_map(raw: Any, default: dict[str, float]) -> dict[str, float]:
    if not isinstance(raw, dict):
        return dict(default)
    out: dict[str, float] = {}
    for key, val in raw.items():
        try:
            out[str(key)] = float(val)
        except (TypeError, ValueError):
            continue
    return out or dict(default)


def load_analysis_config(path: str | Path | None = None) -> AnalysisConfig:
    """Load ``config/analysis.yaml`` into an :class:`AnalysisConfig`.

    Missing or partial files fall back to the documented defaults; the
    ``source_path`` field records where the values came from.
    """
    cfg_path = Path(path) if path else DEFAULT_CONFIG_PATH
    if not cfg_path.exists():
        return AnalysisConfig()

    with open(cfg_path, encoding="utf-8") as fh:
        raw: dict[str, Any] = yaml.safe_load(fh) or {}

    z = raw.get("zscore") or {}
    ma = raw.get("ma4q") or {}
    ps = raw.get("product_score") or {}
    tr = raw.get("trends") or {}
    fc = raw.get("forecast") or {}
    al = raw.get("alerts") or {}
    pub = raw.get("publish") or {}

    weights_raw = raw.get("weights") or {}
    weights = {
        str(name): _as_float_map(vals, DEFAULT_WEIGHTS.get(name, {"product": 0.5, "trends": 0.5}))
        for name, vals in weights_raw.items()
    } or dict(DEFAULT_WEIGHTS)

    keywords_raw = tr.get("keywords") or {}
    keywords = {
        str(company): [str(k) for k in kws]
        for company, kws in keywords_raw.items()
        if isinstance(kws, list) and kws
    } or dict(DEFAULT_KEYWORDS)

    product_weights = {str(k): int(v) for k, v in ps.items()} or {"A": 3, "B": 2, "C": 1}

    horizons = tuple(int(h) for h in fc.get("horizons", [0, 1]))
    levels = tuple(float(x) for x in fc.get("interval_levels", [0.8, 0.95]))
    alphas = tuple(float(a) for a in fc.get("alpha_grid", [0.01, 0.1, 1.0, 10.0]))

    gate = fc.get("quality_gate") or {}

    return AnalysisConfig(
        version=str(raw.get("version", AnalysisConfig.version)),
        formula_version=str(raw.get("formula_version", AnalysisConfig.formula_version)),
        feature_set_version=str(raw.get("feature_set_version", AnalysisConfig.feature_set_version)),
        zscore_window=int(z.get("window", 16)),
        zscore_min_quarters=int(z.get("min_quarters", 16)),
        zscore_min_observations=int(z.get("min_observations", 4)),
        zscore_ddof=int(z.get("ddof", 1)),
        ma4q_min_periods=int(ma.get("min_periods", 4)),
        product_weights=product_weights,
        trends_keywords=keywords,
        weights=weights,
        forecast_model=str(fc.get("model", "ridge")),
        forecast_horizons=horizons or (0, 1),
        forecast_target=str(fc.get("target", "E")),
        min_train_samples=int(fc.get("min_train_samples", 4)),
        alpha_grid=alphas or (0.01, 0.1, 1.0, 10.0),
        interval_levels=levels or (0.8, 0.95),
        conformal_window=int(fc.get("conformal_window", 8)),
        random_state=int(fc.get("random_state", 42)),
        quality_gate_require_both=bool(gate.get("require_both", True)),
        alert_e_threshold=float(al.get("e_threshold", -0.25)),
        alert_nowcast_deviation=float(al.get("nowcast_deviation", 0.75)),
        alert_severity={
            "interval_crosses_zero": str((al.get("severity") or {}).get("interval_crosses_zero", "WARN")),
            "e_below_threshold": str((al.get("severity") or {}).get("e_below_threshold", "CRITICAL")),
            "nowcast_deviation": str((al.get("severity") or {}).get("nowcast_deviation", "INFO")),
        },
        schema_version=str(pub.get("schema_version", "dashboard-v1")),
        keep_versions=int(pub.get("keep_versions", 5)),
        source_path=str(cfg_path),
    )
