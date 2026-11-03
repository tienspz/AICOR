"""Point-in-time feature snapshots and sample construction (FCST-02, PIPE-03).

A snapshot is the only thing the model may read. Each sample records the
availability date of every feature input so a test can prove that no feature
was published after the snapshot's ``as_of_date``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from aicor.compute.config import AnalysisConfig, load_analysis_config

FEATURE_COLUMNS: tuple[str, ...] = (
    "e_lag1",
    "e_lag2",
    "out_lag1",
    "in_lag1",
    "rd_intensity_lag1",
    "capex_intensity_lag1",
    "product_ma4q_lag1",
    "trends_ma4q_lag1",
    "is_msft",
    "target_quarter_num",
)

FEATURE_LABELS: dict[str, str] = {
    "e_lag1": "E (quý gốc)",
    "e_lag2": "E (quý trước quý gốc)",
    "out_lag1": "Out (quý gốc)",
    "in_lag1": "In (quý gốc)",
    "rd_intensity_lag1": "R&D / Revenue",
    "capex_intensity_lag1": "CapEx / Revenue",
    "product_ma4q_lag1": "Product MA4Q",
    "trends_ma4q_lag1": "Trends MA4Q",
    "is_msft": "Company dummy (MSFT=1)",
    "target_quarter_num": "Target calendar quarter (seasonality)",
}

HORIZON_LABELS: dict[int, str] = {
    0: "Nowcast — quý hiện tại chưa có 10-Q",
    1: "Forecast — quý kế tiếp",
}


class PointInTimeError(Exception):
    """Raised when a feature would use data published after ``as_of_date``."""


def quarter_to_index(quarter: str) -> int:
    """``2025Q3`` → absolute quarter index (for ordering and seasonality)."""
    year, q = quarter.split("Q")
    return int(year) * 4 + (int(q) - 1)


def index_to_quarter(index: int) -> str:
    """Absolute quarter index → ``YYYYQn``."""
    return f"{index // 4}Q{index % 4 + 1}"


def target_quarter(origin_quarter: str, horizon: int) -> str:
    """Target quarter for a horizon: ``h=0`` → origin+1, ``h=1`` → origin+2.

    ``h=0`` is the quarter that is currently unreported (the nowcast window);
    ``h=1`` is the following quarter. Both are steps ahead of the last
    *published* quarter, which is what ``forecast_origin`` records.
    """
    return index_to_quarter(quarter_to_index(origin_quarter) + 1 + int(horizon))


@dataclass
class FeatureSnapshot:
    """Immutable snapshot of what the model may see."""

    as_of_date: str
    vintage_id: str
    feature_set_version: str
    config_version: str
    rows: pd.DataFrame = field(default_factory=pd.DataFrame)
    origins: list[str] = field(default_factory=list)

    @property
    def max_feature_available_at(self) -> str | None:
        if self.rows.empty or "feature_available_at" not in self.rows.columns:
            return None
        return str(self.rows["feature_available_at"].max())


def _series_by_quarter(features: pd.DataFrame, company: str) -> pd.DataFrame:
    g = features[features["company"] == company].copy()
    g["quarter_index"] = g["calendar_quarter"].map(quarter_to_index)
    return g.sort_values("quarter_index").reset_index(drop=True)


def build_samples(
    features: pd.DataFrame,
    *,
    config: AnalysisConfig | None = None,
    horizons: tuple[int, ...] | None = None,
) -> pd.DataFrame:
    """Build pooled training/evaluation samples from the feature matrix.

    A sample exists when the origin has a published ``E`` and the target
    quarter has a published ``E``. Features always come from the origin or
    earlier; the target value is used for learning/evaluation only.
    """
    cfg = config or load_analysis_config()
    horizons = horizons or cfg.forecast_horizons

    if features.empty:
        return pd.DataFrame(columns=["sample_id", "company", "horizon", *FEATURE_COLUMNS])

    rows: list[dict[str, object]] = []
    for company in sorted(features["company"].unique()):
        g = _series_by_quarter(features, company)
        by_index = {int(r["quarter_index"]): r for _, r in g.iterrows()}

        for _, origin in g.iterrows():
            if pd.isna(origin.get("In")) or pd.isna(origin.get("Out_baseline", origin.get("Out"))):
                continue
            origin_quarter = str(origin["calendar_quarter"])
            origin_index = int(origin["quarter_index"])

            prev = by_index.get(origin_index - 1)
            for horizon in horizons:
                target = by_index.get(origin_index + 1 + int(horizon))
                if target is None or pd.isna(target.get("E")):
                    continue
                if pd.isna(origin.get("E")):
                    continue

                rows.append(
                    {
                        "sample_id": f"{company}-{origin_quarter}-h{horizon}",
                        "company": company,
                        "horizon": int(horizon),
                        "origin_quarter": origin_quarter,
                        "origin_index": origin_index,
                        "target_quarter": str(target["calendar_quarter"]),
                        "target_index": int(target["quarter_index"]),
                        "target": float(target["E"]),
                        "e_lag1": float(origin["E"]),
                        "e_lag2": float(prev["E"]) if prev is not None and pd.notna(prev.get("E")) else np.nan,
                        "out_lag1": float(origin.get("Out_baseline", origin.get("Out"))),
                        "in_lag1": float(origin["In"]),
                        "rd_intensity_lag1": float(origin["rd_intensity"]) if pd.notna(origin.get("rd_intensity")) else np.nan,
                        "capex_intensity_lag1": float(origin["capex_intensity"]) if pd.notna(origin.get("capex_intensity")) else np.nan,
                        "product_ma4q_lag1": float(origin["product_ma4q"]) if pd.notna(origin.get("product_ma4q")) else np.nan,
                        "trends_ma4q_lag1": float(origin["trends_ma4q"]) if pd.notna(origin.get("trends_ma4q")) else np.nan,
                        "is_msft": 1.0 if company == "MSFT" else 0.0,
                        "target_quarter_num": float(int(str(target["calendar_quarter"]).split("Q")[1])),
                        "origin_available_at": str(origin.get("available_at") or ""),
                        "feature_available_at": str(origin.get("available_at") or ""),
                        "target_available_at": str(target.get("available_at") or ""),
                        "source_id": str(origin.get("source_id", "")),
                        "source_url": str(origin.get("source_url", "")),
                        "data_status": str(origin.get("E_status", "ok")),
                    }
                )

    return pd.DataFrame(rows)


def build_snapshot(
    features: pd.DataFrame,
    *,
    config: AnalysisConfig | None = None,
    as_of_date: str | None = None,
    horizons: tuple[int, ...] | None = None,
    vintage_id: str = "raw-snapshot",
) -> FeatureSnapshot:
    """Build the inference snapshot at the latest published quarter.

    ``as_of_date`` defaults to the newest feature row's ``available_at``: the
    date on which the origin quarter's filing became public. Any sample whose
    feature inputs were published later is rejected (point-in-time guard).
    """
    cfg = config or load_analysis_config()
    samples = build_samples(features, config=cfg, horizons=horizons)
    if samples.empty:
        return FeatureSnapshot(
            as_of_date=as_of_date or "",
            vintage_id=vintage_id,
            feature_set_version=cfg.feature_set_version,
            config_version=cfg.version,
        )

    cutoff = as_of_date or str(features["available_at"].dropna().max())
    # An explicitly earlier ``as_of`` means the caller is asking for a snapshot
    # the data cannot support — that is a blocking error, not a silent filter.
    assert_point_in_time(samples, cutoff)
    allowed = samples[samples["feature_available_at"] <= cutoff].copy()

    origins = sorted(allowed["origin_quarter"].unique())
    latest_origin = origins[-1] if origins else ""
    rows = allowed[allowed["origin_quarter"] == latest_origin].reset_index(drop=True)

    return FeatureSnapshot(
        as_of_date=cutoff,
        vintage_id=vintage_id,
        feature_set_version=cfg.feature_set_version,
        config_version=cfg.version,
        rows=rows,
        origins=origins,
    )


def assert_point_in_time(samples: pd.DataFrame, as_of_date: str) -> None:
    """Fail loudly if any feature input post-dates *as_of_date* (FCST-02)."""
    if samples.empty:
        return
    late = samples[samples["feature_available_at"] > as_of_date]
    if not late.empty:
        offending = late[["sample_id", "feature_available_at"]].head(5).to_dict("records")
        raise PointInTimeError(
            f"{len(late)} sample(s) use data published after as_of_date={as_of_date}: {offending}"
        )


def snapshot_population(samples: pd.DataFrame) -> dict[str, object]:
    """Summary used on the dashboard to disclose sample size honestly."""
    if samples.empty:
        return {"n_samples": 0, "n_companies": 0, "quarters": [], "per_horizon": {}}
    return {
        "n_samples": len(samples),
        "n_companies": int(samples["company"].nunique()),
        "quarters": sorted(samples["target_quarter"].unique().tolist()),
        "per_horizon": {
            str(h): int((samples["horizon"] == h).sum()) for h in sorted(samples["horizon"].unique())
        },
    }
