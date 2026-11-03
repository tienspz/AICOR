"""Metric computation engine: ``In``, ``Out``, ``E`` + weight scenarios (§7.4).

The engine only reads the feature matrix; it never touches raw data. Rows in
which a required component is not ``ok`` produce ``E = NULL`` with an explicit
reason — no zeros, no interpolation (SRC-05, §7.5).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from aicor.compute.config import AnalysisConfig, load_analysis_config
from aicor.compute.metrics import STATUS_OK, combine_out, compute_e, sign_robustness

ANALYSIS_COLUMNS = [
    "analysis_id",
    "company",
    "period_end_date",
    "calendar_quarter",
    "analysis_type",
    "metric",
    "scenario",
    "value",
    "lag",
    "method",
    "confidence",
    "config_version",
    "formula_version",
    "status",
    "reason",
    "n_observations",
    "feature_ids",
    "source_id",
    "source_url",
    "result_class",
]


def _usable(value: float | None, status: str) -> bool:
    return status == STATUS_OK and value is not None and not (isinstance(value, float) and np.isnan(value))


def compute_scenarios(features: pd.DataFrame, config: AnalysisConfig | None = None) -> pd.DataFrame:
    """Wide frame: ``In`` plus ``Out``/``E`` for every configured scenario."""
    cfg = config or load_analysis_config()
    if features.empty:
        return pd.DataFrame()

    rows: list[dict[str, object]] = []
    for _, r in features.iterrows():
        in_value = r.get("z_in")
        in_status = str(r.get("z_in_status", STATUS_OK))
        in_ok = _usable(in_value, in_status)

        row: dict[str, object] = {
            "company": r["company"],
            "period_end_date": r["period_end_date"],
            "calendar_quarter": r["calendar_quarter"],
            "In": float(in_value) if in_ok else np.nan,
            "in_status": in_status if not in_ok else STATUS_OK,
            "in_n_obs": int(r.get("z_in_n_obs") or 0),
            "source_id": r["source_id"],
            "source_url": r["source_url"],
        }

        for scenario, weights in cfg.weights.items():
            zp = r.get("z_product_ma4q")
            zt = r.get("z_trends_ma4q")
            sp = str(r.get("z_product_ma4q_status", STATUS_OK))
            st = str(r.get("z_trends_ma4q_status", STATUS_OK))
            product_ok = _usable(zp, sp)
            trends_ok = _usable(zt, st)

            if product_ok and trends_ok:
                out_value = combine_out(
                    float(zp),
                    float(zt),
                    product_weight=weights["product"],
                    trends_weight=weights["trends"],
                )
                out_status = STATUS_OK
            else:
                out_value = np.nan
                out_status = sp if not product_ok else st

            e_value = compute_e(out_value if out_status == STATUS_OK else None, row["In"] if in_ok else None)
            e_status = STATUS_OK if e_value is not None else (in_status if not in_ok else out_status)

            row[f"Out_{scenario}"] = out_value
            row[f"Out_{scenario}_status"] = out_status
            row[f"E_{scenario}"] = e_value if e_value is not None else np.nan
            row[f"E_{scenario}_status"] = e_status

        scenario_values = [row.get(f"E_{s}") for s in cfg.weights]
        scenario_values = [
            None if v is None or (isinstance(v, float) and np.isnan(v)) else float(v) for v in scenario_values
        ]
        row["E_robustness"] = sign_robustness(scenario_values)
        rows.append(row)

    return pd.DataFrame(rows)


def compute_analysis(features: pd.DataFrame, config: AnalysisConfig | None = None) -> pd.DataFrame:
    """Long-format ``analysis_results`` rows (SPEC §3.11)."""
    cfg = config or load_analysis_config()
    wide = compute_scenarios(features, cfg)
    if wide.empty:
        return pd.DataFrame(columns=ANALYSIS_COLUMNS)

    rows: list[dict[str, object]] = []
    for _, r in wide.iterrows():
        company = r["company"]
        quarter = r["calendar_quarter"]
        in_ok = r["in_status"] == STATUS_OK

        rows.append(
            {
                "analysis_id": f"{company}-{quarter}-In",
                "company": company,
                "period_end_date": r["period_end_date"],
                "calendar_quarter": quarter,
                "analysis_type": "metrics",
                "metric": "In",
                "scenario": "baseline",
                "value": None if not in_ok else float(r["In"]),
                "lag": 0,
                "method": "z16Q(rd_expense)",
                "confidence": "LOW",
                "config_version": cfg.version,
                "formula_version": cfg.formula_version,
                "status": r["in_status"] if not in_ok else STATUS_OK,
                "reason": "" if in_ok else f"z_in_{r['in_status']}",
                "n_observations": int(r["in_n_obs"]),
                "feature_ids": f"{company}-{quarter}-z_in",
                "source_id": r["source_id"],
                "source_url": r["source_url"],
                "result_class": "derived",
            }
        )

        for scenario, weights in cfg.weights.items():
            out_value = r[f"Out_{scenario}"]
            out_status = str(r[f"Out_{scenario}_status"])
            out_ok = out_status == STATUS_OK

            rows.append(
                {
                    "analysis_id": f"{company}-{quarter}-Out-{scenario}",
                    "company": company,
                    "period_end_date": r["period_end_date"],
                    "calendar_quarter": quarter,
                    "analysis_type": "metrics",
                    "metric": "Out",
                    "scenario": scenario,
                    "value": None if not out_ok else float(out_value),
                    "lag": 0,
                    "method": (
                        f"{weights['product']:.1f}*z(product_ma4q) + "
                        f"{weights['trends']:.1f}*z(trends_ma4q)"
                    ),
                    "confidence": "LOW",
                    "config_version": cfg.version,
                    "formula_version": cfg.formula_version,
                    "status": out_status,
                    "reason": "" if out_ok else f"component_{out_status}",
                    "n_observations": int(min(r.get("in_n_obs") or 0, 16)),
                    "feature_ids": f"{company}-{quarter}-z_product_ma4q|{company}-{quarter}-z_trends_ma4q",
                    "source_id": r["source_id"],
                    "source_url": r["source_url"],
                    "result_class": "derived",
                }
            )

            e_value = r[f"E_{scenario}"]
            e_status = str(r[f"E_{scenario}_status"])
            e_ok = e_status == STATUS_OK and pd.notna(e_value)

            rows.append(
                {
                    "analysis_id": f"{company}-{quarter}-E-{scenario}",
                    "company": company,
                    "period_end_date": r["period_end_date"],
                    "calendar_quarter": quarter,
                    "analysis_type": "metrics",
                    "metric": "E",
                    "scenario": scenario,
                    "value": None if not e_ok else float(e_value),
                    "lag": 0,
                    "method": "Out - In",
                    "confidence": "LOW",
                    "config_version": cfg.version,
                    "formula_version": cfg.formula_version,
                    "status": e_status if not e_ok else STATUS_OK,
                    "reason": "" if e_ok else f"insufficient_component_{e_status}",
                    "n_observations": int(min(r.get("in_n_obs") or 0, 16)),
                    "feature_ids": f"{company}-{quarter}-Out-{scenario}|{company}-{quarter}-In",
                    "source_id": r["source_id"],
                    "source_url": r["source_url"],
                    "result_class": "derived",
                }
            )

    return pd.DataFrame(rows, columns=ANALYSIS_COLUMNS)


def series_frame(features: pd.DataFrame, config: AnalysisConfig | None = None) -> pd.DataFrame:
    """Feature matrix joined with the baseline ``In``/``Out``/``E`` columns.

    This is the frame the Pulse engine consumes: one row per (company, quarter)
    with both the inputs and the published metric values.
    """
    cfg = config or load_analysis_config()
    wide = compute_scenarios(features, cfg)
    if wide.empty or features.empty:
        base = features.copy()
        for col in ("In", "Out", "E"):
            base[col] = np.nan
        base["E_status"] = "unavailable"
        base["E_robustness"] = None
        return base

    scenario_cols: list[str] = []
    for scenario in cfg.weights:
        scenario_cols.extend(
            [
                f"Out_{scenario}",
                f"E_{scenario}",
                f"E_{scenario}_status",
            ]
        )

    merge_cols = [
        "company",
        "calendar_quarter",
        "In",
        "E_robustness",
        *scenario_cols,
    ]
    merged = features.merge(wide[merge_cols], on=["company", "calendar_quarter"], how="left")
    # Keep the per-scenario columns for DSH-04 and expose baseline aliases for
    # the Pulse engine and the compact 12-quarter table.
    merged["Out"] = merged["Out_baseline"]
    merged["E"] = merged["E_baseline"]
    merged["E_status"] = merged["E_baseline_status"]
    return merged


def baseline_e_series(features: pd.DataFrame, config: AnalysisConfig | None = None) -> pd.DataFrame:
    """Compact (company, quarter, E/Out/In) frame used by the Pulse engine."""
    cfg = config or load_analysis_config()
    wide = compute_scenarios(features, cfg)
    if wide.empty:
        return pd.DataFrame(columns=["company", "calendar_quarter", "period_end_date", "In", "Out", "E", "status", "source_id", "source_url"])

    out = pd.DataFrame(
        {
            "company": wide["company"],
            "calendar_quarter": wide["calendar_quarter"],
            "period_end_date": wide["period_end_date"],
            "In": wide["In"],
            "Out": wide["Out_baseline"],
            "E": wide["E_baseline"],
            "status": wide["E_baseline_status"],
            "E_robustness": wide["E_robustness"],
            "source_id": wide["source_id"],
            "source_url": wide["source_url"],
        }
    )
    return out
