"""Feature construction — the input to ``In``, ``Out`` and ``E`` (SPEC §7).

``build_feature_matrix`` returns one wide row per (company, quarter). All
status columns use the vocabulary from :mod:`aicor.compute.metrics`; the
dashboard renders them so an unavailable value is never mistaken for a zero.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from aicor.compute.config import AnalysisConfig, load_analysis_config
from aicor.compute.metrics import (
    STATUS_INSUFFICIENT_OBSERVATIONS,
    STATUS_INSUFFICIENT_WINDOW,
    STATUS_OK,
    STATUS_UNAVAILABLE,
    ZSeries,
    ma4q,
    product_score,
    rolling_z,
)
from aicor.compute.provenance import availability_frame, sec_facts_url
from aicor.compute.registry import FEATURE_META


def quarter_key(year: int, quarter: int) -> str:
    """Canonical ``YYYYQn`` label from a calendar year and quarter."""
    return f"{int(year)}Q{int(quarter)}"


def quarter_from_date(value) -> str | None:
    """``YYYYQn`` for a date-like value, or ``None`` when unparseable."""
    ts = pd.to_datetime(value, errors="coerce")
    if pd.isna(ts):
        return None
    return quarter_key(ts.year, (ts.month - 1) // 3 + 1)


def _prepare_panel(panel: pd.DataFrame) -> pd.DataFrame:
    """Normalise the analysis-ready panel into the columns the engine needs."""
    df = panel.copy()
    df["period_end_date"] = pd.to_datetime(df["period_end_date"], errors="coerce")
    df = df.dropna(subset=["period_end_date"])

    if "calendar_quarter" in df.columns:
        df["calendar_quarter"] = df.apply(
            lambda r: quarter_key(r["year"], r["calendar_quarter"])
            if pd.notna(r.get("year")) and pd.notna(r.get("calendar_quarter"))
            else quarter_from_date(r["period_end_date"]),
            axis=1,
        )
    else:
        df["calendar_quarter"] = df["period_end_date"].map(quarter_from_date)

    numeric = ["revenue", "rd_expense", "capex", "operating_income", "net_income", "cfo"]
    for col in numeric:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        else:
            df[col] = np.nan

    if "source_id" not in df.columns:
        df["source_id"] = df.apply(
            lambda r: f"SEC-{r['company']}-{pd.Timestamp(r['period_end_date']).date().isoformat()}", axis=1
        )

    return df.sort_values(["company", "period_end_date"]).reset_index(drop=True)


def _product_counts(products: pd.DataFrame | None, config: AnalysisConfig) -> pd.DataFrame:
    """Per (company, quarter) counts of A/B/C announcements."""
    if products is None or products.empty:
        return pd.DataFrame(columns=["company", "calendar_quarter", "count_a", "count_b", "count_c"])

    df = products.copy()
    date_col = "announcement_date" if "announcement_date" in df.columns else "date"
    df["calendar_quarter"] = df[date_col].map(quarter_from_date)
    df = df.dropna(subset=["calendar_quarter"])
    df["company"] = df["company"].astype(str).str.upper()
    df["category"] = df["category"].astype(str).str.upper()

    wide = (
        df.pivot_table(
            index=["company", "calendar_quarter"],
            columns="category",
            values="product_name",
            aggfunc="count",
            fill_value=0,
        )
        .reset_index()
    )
    for cat in ("A", "B", "C"):
        if cat not in wide.columns:
            wide[cat] = 0
    counts = wide.rename(columns={"A": "count_a", "B": "count_b", "C": "count_c"})
    counts = counts[["company", "calendar_quarter", "count_a", "count_b", "count_c"]]
    counts["product_score"] = counts.apply(
        lambda r: product_score(
            {"A": r["count_a"], "B": r["count_b"], "C": r["count_c"]},
            config.product_weights,
        ),
        axis=1,
    )
    return counts


def _trends_quarterly(trends: pd.DataFrame | None, config: AnalysisConfig) -> pd.DataFrame:
    """Mean interest per (company, quarter) using the configured keywords."""
    if trends is None or trends.empty:
        return pd.DataFrame(columns=["company", "calendar_quarter", "trends_score"])

    df = trends.copy()
    if "calendar_quarter" not in df.columns:
        df["calendar_quarter"] = df["date"].map(quarter_from_date)

    rows: list[dict[str, object]] = []
    for company, keywords in config.trends_keywords.items():
        subset = df[df["keyword"].isin(keywords)]
        if subset.empty:
            continue
        grouped = subset.groupby("calendar_quarter")["interest_score"].agg(
            ["mean", "count"]
        )
        for quarter, stats in grouped.iterrows():
            rows.append(
                {
                    "company": company,
                    "calendar_quarter": quarter,
                    "trends_score": float(stats["mean"]),
                    "keyword_count": int(stats["count"]),
                }
            )
    return pd.DataFrame(rows)


def _status_for_missing(series: pd.Series) -> list[str]:
    return [STATUS_OK if pd.notna(v) else STATUS_UNAVAILABLE for v in series]


def _z_dict(result: ZSeries) -> dict[str, list]:
    return {
        "values": list(result.values),
        "status": list(result.status),
        "n_obs": list(result.n_observations),
    }


def build_feature_matrix(
    panel: pd.DataFrame,
    products: pd.DataFrame | None = None,
    trends: pd.DataFrame | None = None,
    *,
    config: AnalysisConfig | None = None,
    provenance: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Build the wide feature matrix: one row per company-quarter.

    The panel defines the analysis quarters. Product/Trends values that fall
    outside those quarters are ignored, so a later crawl can never leak into an
    earlier quarter's features.
    """
    cfg = config or load_analysis_config()
    base = _prepare_panel(panel)
    counts = _product_counts(products, cfg)
    trend_scores = _trends_quarterly(trends, cfg)

    avail = availability_frame(provenance) if provenance is not None else pd.DataFrame()
    avail_lookup = {
        (str(r["company"]), str(r["period_end_date"])): (str(r["available_at"]), str(r["availability_basis"]))
        for _, r in avail.iterrows()
    } if not avail.empty else {}

    prov_lookup = {}
    if provenance is not None and not provenance.empty:
        prov_lookup = {
            str(r["source_id"]): str(r["source_url"])
            for _, r in provenance.iterrows()
        }

    frames: list[pd.DataFrame] = []
    for company, grp in base.groupby("company", sort=True):
        g = grp.sort_values("period_end_date").reset_index(drop=True)
        quarters = list(g["calendar_quarter"])

        company_counts = counts[counts["company"] == company].set_index("calendar_quarter") if not counts.empty else None
        c_a = [int(company_counts.loc[q, "count_a"]) if company_counts is not None and q in company_counts.index else 0 for q in quarters]
        c_b = [int(company_counts.loc[q, "count_b"]) if company_counts is not None and q in company_counts.index else 0 for q in quarters]
        c_c = [int(company_counts.loc[q, "count_c"]) if company_counts is not None and q in company_counts.index else 0 for q in quarters]
        ps = [product_score({"A": a, "B": b, "C": c}, cfg.product_weights) for a, b, c in zip(c_a, c_b, c_c)]

        if trend_scores.empty:
            trends_score = pd.Series([np.nan] * len(quarters), dtype=float)
        else:
            company_trends = trend_scores[trend_scores["company"] == company].set_index("calendar_quarter")
            trends_score = pd.Series(
                [float(company_trends.loc[q, "trends_score"]) if q in company_trends.index else np.nan for q in quarters],
                dtype=float,
            )

        ps_series = pd.Series(ps, dtype=float)
        pm4 = ma4q(ps_series, cfg.ma4q_min_periods)
        tm4 = ma4q(trends_score, cfg.ma4q_min_periods)

        z_in = rolling_z(
            g["rd_expense"],
            window=cfg.zscore_window,
            min_quarters=cfg.zscore_min_quarters,
            min_observations=cfg.zscore_min_observations,
            ddof=cfg.zscore_ddof,
        )
        z_pm = rolling_z(
            pm4,
            window=cfg.zscore_window,
            min_quarters=cfg.zscore_min_quarters,
            min_observations=cfg.zscore_min_observations,
            ddof=cfg.zscore_ddof,
        )
        z_tm = rolling_z(
            tm4,
            window=cfg.zscore_window,
            min_quarters=cfg.zscore_min_quarters,
            min_observations=cfg.zscore_min_observations,
            ddof=cfg.zscore_ddof,
        )

        revenue = g["revenue"] if "revenue" in g.columns else pd.Series([np.nan] * len(g))
        rd = g["rd_expense"]
        capex = g["capex"] if "capex" in g.columns else pd.Series([np.nan] * len(g))

        with np.errstate(divide="ignore", invalid="ignore"):
            rd_intensity = np.where(
                (revenue.notna()) & (revenue != 0) & rd.notna(), rd / revenue, np.nan
            )
            capex_intensity = np.where(
                (revenue.notna()) & (revenue != 0) & capex.notna(), capex / revenue, np.nan
            )

        source_ids = list(g["source_id"])
        period_ends = [pd.Timestamp(d).date().isoformat() for d in g["period_end_date"]]

        frame = pd.DataFrame(
            {
                "company": company,
                "period_end_date": period_ends,
                "calendar_quarter": quarters,
                "count_a": c_a,
                "count_b": c_b,
                "count_c": c_c,
                "product_score": ps,
                "product_ma4q": list(pm4),
                "product_ma4q_status": _status_for_missing(pm4),
                "trends_score": list(trends_score),
                "trends_ma4q": list(tm4),
                "trends_ma4q_status": _status_for_missing(tm4),
                "revenue": list(revenue),
                "rd_expense": list(rd),
                "rd_intensity": rd_intensity,
                "capex": list(capex),
                "capex_intensity": capex_intensity,
                "z_in": list(z_in.values),
                "z_in_status": z_in.status,
                "z_in_n_obs": z_in.n_observations,
                "z_product_ma4q": list(z_pm.values),
                "z_product_ma4q_status": z_pm.status,
                "z_product_ma4q_n_obs": z_pm.n_observations,
                "z_trends_ma4q": list(z_tm.values),
                "z_trends_ma4q_status": z_tm.status,
                "z_trends_ma4q_n_obs": z_tm.n_observations,
                "source_id": source_ids,
                "source_url": [prov_lookup.get(sid, sec_facts_url(company)) for sid in source_ids],
                "config_version": cfg.version,
                "formula_version": cfg.formula_version,
                "feature_set_version": cfg.feature_set_version,
            }
        )

        frame["available_at"] = [
            avail_lookup.get((company, pe), (None, "unknown"))[0] for pe in period_ends
        ]
        frame["availability_basis"] = [
            avail_lookup.get((company, pe), (None, "unknown"))[1] for pe in period_ends
        ]
        # Conservative fallback so a missing provenance row can never make a
        # quarter look "available earlier than it is".
        fallback = pd.to_datetime(frame["period_end_date"]) + pd.Timedelta(days=45)
        frame["available_at"] = frame["available_at"].fillna(fallback.dt.strftime("%Y-%m-%d"))
        frame["available_at_basis"] = np.where(
            frame["availability_basis"].isna() | (frame["availability_basis"] == "unknown"),
            "period_end_plus_45d",
            frame["availability_basis"],
        )
        frame = frame.drop(columns=["availability_basis"])

        frames.append(frame)

    if not frames:
        return pd.DataFrame(columns=list(_EMPTY_COLUMNS))

    return pd.concat(frames, ignore_index=True)


_EMPTY_COLUMNS = (
    "company",
    "period_end_date",
    "calendar_quarter",
    "count_a",
    "count_b",
    "count_c",
    "product_score",
    "product_ma4q",
    "product_ma4q_status",
    "trends_score",
    "trends_ma4q",
    "trends_ma4q_status",
    "revenue",
    "rd_expense",
    "rd_intensity",
    "capex",
    "capex_intensity",
    "z_in",
    "z_in_status",
    "z_in_n_obs",
    "z_product_ma4q",
    "z_product_ma4q_status",
    "z_product_ma4q_n_obs",
    "z_trends_ma4q",
    "z_trends_ma4q_status",
    "z_trends_ma4q_n_obs",
    "source_id",
    "source_url",
    "config_version",
    "formula_version",
    "feature_set_version",
    "available_at",
    "available_at_basis",
)


def to_long_features(features: pd.DataFrame, config: AnalysisConfig | None = None) -> pd.DataFrame:
    """Melt the wide matrix into the SPEC §3.10 ``features_quarterly`` shape."""
    cfg = config or load_analysis_config()
    if features.empty:
        return pd.DataFrame(
            columns=[
                "feature_id",
                "company",
                "period_end_date",
                "calendar_quarter",
                "feature",
                "value",
                "unit",
                "definition",
                "calculation_method",
                "reported_or_derived",
                "proxy",
                "confidence",
                "source_id",
                "source_url",
                "status",
                "reason",
                "config_version",
                "input_feature_ids",
            ]
        )

    status_pairs = {
        "z_in": ("z_in_status", None),
        "z_product_ma4q": ("z_product_ma4q_status", None),
        "z_trends_ma4q": ("z_trends_ma4q_status", None),
        "product_ma4q": ("product_ma4q_status", "insufficient_ma4q_quarters"),
        "trends_ma4q": ("trends_ma4q_status", "trends_unavailable"),
    }

    rows: list[dict[str, object]] = []
    for _, r in features.iterrows():
        for feature in (
            "rd_expense",
            "rd_intensity",
            "capex_intensity",
            "product_score",
            "product_ma4q",
            "trends_score",
            "trends_ma4q",
            "z_in",
            "z_product_ma4q",
            "z_trends_ma4q",
        ):
            meta = FEATURE_META[feature]
            value = r.get(feature)
            value = None if value is None or (isinstance(value, float) and np.isnan(value)) else float(value)

            if feature in status_pairs:
                status_col = status_pairs[feature][0]
                status = str(r.get(status_col, STATUS_OK))
            else:
                status = STATUS_OK if value is not None else STATUS_UNAVAILABLE

            reason = ""
            if status != STATUS_OK:
                reason = {
                    STATUS_UNAVAILABLE: f"{feature}_unavailable_at_source",
                    STATUS_INSUFFICIENT_WINDOW: f"fewer_than_{cfg.zscore_min_quarters}_quarters",
                    STATUS_INSUFFICIENT_OBSERVATIONS: f"fewer_than_{cfg.zscore_min_observations}_observations",
                    "insufficient_ma4q_quarters": "fewer_than_4_quarters_for_ma4q",
                    "degenerate": "std_is_zero",
                }.get(status, f"{feature}_not_usable")

            feature_id = f"{r['company']}-{r['calendar_quarter']}-{feature}"
            rows.append(
                {
                    "feature_id": feature_id,
                    "company": r["company"],
                    "period_end_date": r["period_end_date"],
                    "calendar_quarter": r["calendar_quarter"],
                    "feature": feature,
                    "value": value,
                    "unit": meta["unit"],
                    "definition": meta["definition"],
                    "calculation_method": meta["calculation_method"],
                    "reported_or_derived": meta["reported_or_derived"],
                    "proxy": bool(meta["proxy"]),
                    "confidence": meta["confidence"],
                    "source_id": r["source_id"],
                    "source_url": r["source_url"],
                    "status": status,
                    "reason": reason,
                    "config_version": cfg.version,
                    "input_feature_ids": "|".join(
                        f"{r['company']}-{r['calendar_quarter']}-{src}"
                        for src in meta["source_fields"]
                    ),
                }
            )

    return pd.DataFrame(rows)
