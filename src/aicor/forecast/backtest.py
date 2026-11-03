"""Rolling-origin backtest (FCST-06, FCST-07, FCST-08).

Folds are strictly chronological: training rows are every sample whose target
is earlier than the fold's target quarter. Nothing from the fold's target
quarter (or later) can influence the model. Metrics are reported pooled and
per company, and empirical interval coverage is measured for each level.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from aicor.compute.config import AnalysisConfig, load_analysis_config
from aicor.forecast.models import (
    MODEL_AR1,
    MODEL_NAIVE,
    MODEL_RIDGE,
    fit_predict,
)

MODEL_FAMILY = (MODEL_NAIVE, MODEL_AR1, MODEL_RIDGE)


def _metrics(actual: np.ndarray, predicted: np.ndarray, baseline: np.ndarray) -> dict[str, float]:
    if len(actual) == 0:
        return {
            "n": 0.0,
            "mae": float("nan"),
            "rmse": float("nan"),
            "directional_accuracy": float("nan"),
        }
    errors = predicted - actual
    direction_actual = np.sign(actual - baseline)
    direction_pred = np.sign(predicted - baseline)
    comparable = direction_actual != 0
    directional = (
        float(np.mean(direction_actual[comparable] == direction_pred[comparable])) if comparable.any() else float("nan")
    )
    return {
        "n": float(len(actual)),
        "mae": float(np.mean(np.abs(errors))),
        "rmse": float(np.sqrt(np.mean(errors**2))),
        "directional_accuracy": directional,
    }


def rolling_origin_backtest(
    samples: pd.DataFrame,
    *,
    config: AnalysisConfig | None = None,
    min_train: int | None = None,
) -> dict[str, object]:
    """Run the pooled rolling-origin backtest.

    Returns ``{"folds": DataFrame, "metrics": {...}, "n_folds": {...},
    "coverage": {...}}``. Empty input yields an explicitly empty report rather
    than a silent zero — the caller renders "insufficient evidence".
    """
    cfg = config or load_analysis_config()
    min_train_samples = min_train if min_train is not None else cfg.min_train_samples
    levels = cfg.interval_levels

    empty = {
        "folds": pd.DataFrame(
            columns=[
                "horizon",
                "target_quarter",
                "company",
                "model",
                "actual",
                "predicted",
                "interval_low_80",
                "interval_high_80",
                "interval_low_95",
                "interval_high_95",
                "baseline",
                "n_train",
            ]
        ),
        "metrics": {},
        "n_folds": {},
        "coverage": {},
        "min_train": min_train_samples,
        "available": False,
        "reason": "no_samples",
    }
    if samples.empty:
        return empty

    fold_rows: list[dict[str, object]] = []
    n_folds: dict[str, int] = {}

    for horizon in sorted(samples["horizon"].unique()):
        subset = samples[samples["horizon"] == horizon].sort_values("target_index")
        target_quarters = sorted(subset["target_quarter"].unique())
        count = 0
        for target_q in target_quarters:
            train = subset[subset["target_quarter"] < target_q]
            test = subset[subset["target_quarter"] == target_q]
            if len(train) < min_train_samples or test.empty:
                continue

            # Small guard against leakage: every training target must be older.
            assert train["target_index"].max() < test["target_index"].min()

            for _, row in test.iterrows():
                baseline = float(row["e_lag1"])
                for model in MODEL_FAMILY:
                    try:
                        pred = fit_predict(
                            train,
                            row,
                            model=model,
                            alpha_grid=cfg.alpha_grid,
                            interval_levels=levels,
                            conformal_window=cfg.conformal_window,
                        )
                    except Exception as exc:  # noqa: BLE001 - one model failure must not abort the fold
                        fold_rows.append(
                            {
                                "horizon": int(horizon),
                                "target_quarter": target_q,
                                "company": row["company"],
                                "model": model,
                                "actual": float(row["target"]),
                                "predicted": float("nan"),
                                "baseline": baseline,
                                "n_train": len(train),
                                "error": str(exc),
                            }
                        )
                        continue

                    fold_rows.append(
                        {
                            "horizon": int(horizon),
                            "target_quarter": target_q,
                            "company": row["company"],
                            "model": model,
                            "actual": float(row["target"]),
                            "predicted": float(pred.value),
                            "interval_low_80": pred.interval_low_80,
                            "interval_high_80": pred.interval_high_80,
                            "interval_low_95": pred.interval_low_95,
                            "interval_high_95": pred.interval_high_95,
                            "interval_method": pred.interval_method,
                            "baseline": baseline,
                            "n_train": len(train),
                        }
                    )
            count += 1
        n_folds[str(horizon)] = count

    folds = pd.DataFrame(fold_rows)
    if folds.empty:
        return empty | {"n_folds": n_folds, "reason": "insufficient_folds"}

    metrics: dict[str, dict[str, dict[str, float]]] = {}
    coverage: dict[str, dict[str, dict[str, float]]] = {}

    for horizon in sorted(folds["horizon"].unique()):
        hf = folds[(folds["horizon"] == horizon) & folds["predicted"].notna()]
        if hf.empty:
            continue
        horizon_key = str(int(horizon))
        metrics[horizon_key] = {}
        coverage[horizon_key] = {}

        groups: dict[str, pd.DataFrame] = {"pooled": hf}
        for company in sorted(hf["company"].unique()):
            groups[company] = hf[hf["company"] == company]

        for group_name, group in groups.items():
            metrics[horizon_key][group_name] = {}
            coverage[horizon_key][group_name] = {}
            for model in MODEL_FAMILY:
                mf = group[group["model"] == model]
                if mf.empty:
                    continue
                actual = mf["actual"].to_numpy(dtype=float)
                predicted = mf["predicted"].to_numpy(dtype=float)
                baseline = mf["baseline"].to_numpy(dtype=float)
                metrics[horizon_key][group_name][model] = _metrics(actual, predicted, baseline)

                for level in levels:
                    key = f"{round(level * 100)}"
                    lo = mf[f"interval_low_{key}"].to_numpy(dtype=float)
                    hi = mf[f"interval_high_{key}"].to_numpy(dtype=float)
                    inside = (actual >= lo) & (actual <= hi)
                    coverage[horizon_key][group_name][f"{model}_{key}"] = {
                        "coverage": float(np.mean(inside)),
                        "n": float(len(mf)),
                    }

    return {
        "folds": folds,
        "metrics": metrics,
        "n_folds": n_folds,
        "coverage": coverage,
        "min_train": min_train_samples,
        "available": True,
        "reason": "",
    }


def quality_gate(
    backtest: dict[str, object],
    *,
    config: AnalysisConfig | None = None,
    model: str | None = None,
) -> dict[str, object]:
    """FCST-08: may the primary model carry the "forecast" label?

    Compares pooled MAE and RMSE against the naive baseline for every horizon.
    ``require_both`` (default) demands both to improve; otherwise either one.
    """
    cfg = config or load_analysis_config()
    primary = model or cfg.forecast_model
    metrics = backtest.get("metrics") or {}
    if not metrics:
        return {
            "passed": False,
            "reason": "no_backtest_metrics",
            "checks": [],
            "primary_model": primary,
            "baseline_model": MODEL_NAIVE,
        }

    checks: list[dict[str, object]] = []
    passed = True
    for horizon_key, by_group in metrics.items():
        pooled = by_group.get("pooled", {})
        model_metrics = pooled.get(primary)
        naive_metrics = pooled.get(MODEL_NAIVE)
        if not model_metrics or not naive_metrics:
            checks.append(
                {
                    "horizon": int(horizon_key),
                    "status": "missing",
                    "detail": "primary or baseline metrics unavailable",
                }
            )
            passed = False
            continue

        mae_better = model_metrics["mae"] < naive_metrics["mae"]
        rmse_better = model_metrics["rmse"] < naive_metrics["rmse"]
        horizon_passed = (mae_better and rmse_better) if cfg.quality_gate_require_both else (mae_better or rmse_better)
        checks.append(
            {
                "horizon": int(horizon_key),
                "status": "pass" if horizon_passed else "fail",
                "model_mae": round(float(model_metrics["mae"]), 6),
                "naive_mae": round(float(naive_metrics["mae"]), 6),
                "model_rmse": round(float(model_metrics["rmse"]), 6),
                "naive_rmse": round(float(naive_metrics["rmse"]), 6),
                "n": int(model_metrics["n"]),
            }
        )
        passed = passed and horizon_passed

    return {
        "passed": bool(passed),
        "reason": "" if passed else "primary_model_does_not_beat_naive",
        "checks": checks,
        "primary_model": primary,
        "baseline_model": MODEL_NAIVE,
        "require_both": cfg.quality_gate_require_both,
    }
