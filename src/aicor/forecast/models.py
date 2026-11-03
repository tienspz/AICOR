"""Baseline and main models for ĐV-ĐR forecast layer (FCST-05).

Deliberately small: naive, pooled AR(1) and a ridge regression implemented in
NumPy. No deep learning — ``N`` is at most a few dozen observations (SPEC §5).
Everything here is deterministic given the training rows.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import NormalDist

import numpy as np
import pandas as pd

from aicor.forecast.snapshot import FEATURE_COLUMNS

MODEL_NAIVE = "naive"
MODEL_AR1 = "ar1"
MODEL_RIDGE = "ridge"


@dataclass
class RidgeFit:
    """Fitted ridge model plus everything needed to explain a prediction."""

    feature_names: list[str]
    means: dict[str, float]
    stds: dict[str, float]
    coefficients: list[float]          # standardized space
    intercept: float
    alpha: float
    n_train: int
    imputation: dict[str, float] = field(default_factory=dict)
    alpha_scores: dict[str, float] = field(default_factory=dict)


@dataclass
class Prediction:
    model: str
    value: float
    interval_low_80: float | None = None
    interval_high_80: float | None = None
    interval_low_95: float | None = None
    interval_high_95: float | None = None
    interval_method: str = "split_conformal"
    contributions: list[dict[str, object]] = field(default_factory=list)
    alpha: float | None = None


def _feature_matrix(df: pd.DataFrame, names: list[str]) -> np.ndarray:
    # ``copy=True``: pandas may return a read-only view, and imputation writes in place.
    return df[names].to_numpy(dtype=float, copy=True)


def _impute_column(values: np.ndarray, fill: float) -> np.ndarray:
    out = values.copy()
    mask = np.isnan(out)
    if mask.any():
        out[mask] = fill
    return out


def fit_naive(train: pd.DataFrame, origin_row: pd.Series) -> float:
    """Seasonal-naive baseline: persist the origin quarter's ``E``."""
    return float(origin_row["e_lag1"])


def fit_ar1(train: pd.DataFrame) -> tuple[float, float]:
    """Pooled AR(1): ``E_target = a + b * E_origin``."""
    x = train["e_lag1"].to_numpy(dtype=float)
    y = train["target"].to_numpy(dtype=float)
    if len(x) < 2 or np.nanstd(x) == 0:
        return float(np.nanmean(y)) if len(y) else 0.0, 0.0
    b, a = np.polyfit(x, y, 1)
    return float(a), float(b)


def _ridge_solve(x: np.ndarray, y: np.ndarray, alpha: float) -> tuple[np.ndarray, float]:
    x_mean = x.mean(axis=0)
    y_mean = float(y.mean())
    xs = x - x_mean
    ys = y - y_mean
    gram = xs.T @ xs + alpha * np.eye(xs.shape[1])
    try:
        coef = np.linalg.solve(gram, xs.T @ ys)
    except np.linalg.LinAlgError:  # pragma: no cover - singular only with duplicate columns
        coef = np.linalg.pinv(gram) @ (xs.T @ ys)
    return coef, y_mean


def _time_ordered_folds(n: int, k: int = 3) -> list[tuple[np.ndarray, np.ndarray]]:
    """Expanding-window folds over chronologically sorted rows."""
    folds: list[tuple[np.ndarray, np.ndarray]] = []
    if n < 6:
        return folds
    block = max(1, n // (k + 1))
    for i in range(1, k + 1):
        train_end = block * (i + 1)
        if train_end >= n:
            break
        folds.append((np.arange(0, train_end), np.arange(train_end, min(train_end + block, n))))
    return folds


def fit_ridge(
    train: pd.DataFrame,
    *,
    feature_names: list[str] | None = None,
    alpha_grid: tuple[float, ...] = (0.01, 0.1, 1.0, 10.0),
) -> RidgeFit:
    """Fit ridge with median imputation and train-only standardization.

    ``alpha`` is chosen by chronological expanding-window validation *inside*
    the training block — the test fold is never consulted (FCST-06).
    """
    names = list(feature_names or FEATURE_COLUMNS)
    ordered = train.sort_values(["target_quarter", "company"]).reset_index(drop=True)
    raw = _feature_matrix(ordered, names)

    imputation = {}
    for j, name in enumerate(names):
        col = raw[:, j]
        imputation[name] = float(np.nanmedian(col)) if np.isfinite(col).any() else 0.0
        raw[:, j] = _impute_column(col, imputation[name])

    y = ordered["target"].to_numpy(dtype=float)

    best_alpha = float(alpha_grid[0])
    best_score = float("inf")
    scores: dict[str, float] = {}
    for alpha in alpha_grid:
        maes: list[float] = []
        for tr_idx, te_idx in _time_ordered_folds(len(y)):
            x_tr = raw[tr_idx]
            y_tr = y[tr_idx]
            mu = x_tr.mean(axis=0)
            sd = x_tr.std(axis=0, ddof=1)
            sd = np.where(sd == 0, 1.0, sd)
            xs = (x_tr - mu) / sd
            coef, intercept = _ridge_solve(xs, y_tr, alpha)
            pred = ((raw[te_idx] - mu) / sd) @ coef + intercept
            maes.append(float(np.mean(np.abs(pred - y[te_idx]))))
        score = float(np.mean(maes)) if maes else float("inf")
        scores[f"{alpha:g}"] = round(score, 6)
        if score < best_score:
            best_score, best_alpha = score, float(alpha)

    means = raw.mean(axis=0)
    stds = raw.std(axis=0, ddof=1)
    stds = np.where(stds == 0, 1.0, stds)
    x_std = (raw - means) / stds
    coef, intercept = _ridge_solve(x_std, y, best_alpha)

    return RidgeFit(
        feature_names=names,
        means={n: float(v) for n, v in zip(names, means)},
        stds={n: float(v) for n, v in zip(names, stds)},
        coefficients=[float(c) for c in coef],
        intercept=float(intercept),
        alpha=best_alpha,
        n_train=len(ordered),
        imputation=imputation,
        alpha_scores=scores,
    )


def predict_ridge(fit: RidgeFit, row: pd.Series) -> tuple[float, list[dict[str, object]]]:
    """Predict one row and return standardized-space contributions."""
    z_values: list[float] = []
    raw_values: list[float] = []
    for name in fit.feature_names:
        value = row.get(name, np.nan)
        value = fit.imputation.get(name, 0.0) if pd.isna(value) else float(value)
        raw_values.append(value)
        z_values.append((value - fit.means[name]) / fit.stds[name])

    z = np.array(z_values)
    coef = np.array(fit.coefficients)
    pred = float(fit.intercept + z @ coef)

    contributions = [
        {
            "feature": name,
            "value": round(raw_values[i], 6),
            "contribution": round(float(coef[i] * z[i]), 6),
            "direction": "up" if coef[i] * z[i] > 0 else "down",
        }
        for i, name in enumerate(fit.feature_names)
    ]
    contributions.sort(key=lambda c: abs(float(c["contribution"])), reverse=True)
    return pred, contributions


def conformal_half_widths(
    residuals: np.ndarray,
    levels: tuple[float, ...] = (0.8, 0.95),
) -> tuple[dict[str, float], str]:
    """Split-conformal absolute-residual quantiles with a finite-sample correction.

    Falls back to a normal approximation (flagged) when fewer than three
    calibration residuals exist — the caller surfaces that flag on the
    dashboard, it is never silently upgraded to a conformal interval.
    """
    res = np.asarray([r for r in residuals if np.isfinite(r)], dtype=float)
    widths: dict[str, float] = {}
    if len(res) < 3:
        sigma = float(np.std(res, ddof=1)) if len(res) > 1 else 0.0
        normal = NormalDist()
        for level in levels:
            q = normal.inv_cdf(0.5 + level / 2)
            widths[_level_key(level)] = float(sigma * q)
        return widths, "normal_fallback"

    abs_res = np.sort(np.abs(res))
    n = len(abs_res)
    for level in levels:
        # ceil((n+1) * level) / n keeps the interval conservative for small n.
        rank = int(np.ceil((n + 1) * level)) - 1
        rank = min(max(rank, 0), n - 1)
        widths[_level_key(level)] = float(abs_res[rank])
    return widths, "split_conformal"


def _level_key(level: float) -> str:
    return f"{round(level * 100)}"


def calibration_residuals(
    train: pd.DataFrame,
    *,
    feature_names: list[str] | None = None,
    window: int = 8,
) -> np.ndarray:
    """Residuals on the last *window* training rows from a chronological split.

    The calibration block is strictly later than the fit block, so the
    residuals are out-of-sample for the model that produced them.
    """
    ordered = train.sort_values(["target_quarter", "company"]).reset_index(drop=True)
    n = len(ordered)
    if n < 5:
        return np.array([])

    k = min(window, max(2, n // 3))
    fit_block = ordered.iloc[: n - k]
    calib_block = ordered.iloc[n - k :]
    if len(fit_block) < 3:
        return np.array([])

    fit = fit_ridge(fit_block, feature_names=feature_names)
    residuals = []
    for _, row in calib_block.iterrows():
        pred, _ = predict_ridge(fit, row)
        residuals.append(float(row["target"]) - pred)
    return np.array(residuals)


def fit_predict(
    train: pd.DataFrame,
    origin_row: pd.Series,
    *,
    model: str,
    feature_names: list[str] | None = None,
    alpha_grid: tuple[float, ...] = (0.01, 0.1, 1.0, 10.0),
    interval_levels: tuple[float, ...] = (0.8, 0.95),
    conformal_window: int = 8,
) -> Prediction:
    """Predict with one model and attach calibrated intervals."""
    if model == MODEL_NAIVE:
        value = fit_naive(train, origin_row)
        residual_series = train["target"].to_numpy(dtype=float) - train["e_lag1"].to_numpy(dtype=float)
        widths, method = conformal_half_widths(residual_series, interval_levels)
        return _naive_prediction(value, widths, method, model=MODEL_NAIVE)

    if model == MODEL_AR1:
        a, b = fit_ar1(train)
        value = float(a + b * float(origin_row["e_lag1"]))
        residuals = []
        for _, row in train.iterrows():
            residuals.append(float(row["target"]) - (a + b * float(row["e_lag1"])))
        widths, method = conformal_half_widths(np.array(residuals), interval_levels)
        return _naive_prediction(value, widths, method, model=MODEL_AR1)

    if model != MODEL_RIDGE:
        raise ValueError(f"Unknown model {model!r}; expected one of naive/ar1/ridge")

    fit = fit_ridge(train, feature_names=feature_names, alpha_grid=alpha_grid)
    value, contributions = predict_ridge(fit, origin_row)
    residuals = calibration_residuals(train, feature_names=feature_names, window=conformal_window)
    widths, method = conformal_half_widths(residuals, interval_levels)
    pred = _naive_prediction(value, widths, method, model=MODEL_RIDGE)
    pred.contributions = contributions
    pred.alpha = fit.alpha
    return pred


def _interval_kwargs(widths: dict[str, float], value: float) -> dict[str, float]:
    return {
        "interval_low_80": value - widths.get("80", 0.0),
        "interval_high_80": value + widths.get("80", 0.0),
        "interval_low_95": value - widths.get("95", 0.0),
        "interval_high_95": value + widths.get("95", 0.0),
    }


def _naive_prediction(
    value: float,
    widths: dict[str, float],
    method: str,
    *,
    model: str = MODEL_NAIVE,
) -> Prediction:
    return Prediction(
        model=model,
        value=value,
        interval_method=method,
        **_interval_kwargs(widths, value),
    )
