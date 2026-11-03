"""Model card generation (FCST-11, NFR-11).

The card is written next to the artifacts and linked from DSH-07. It states the
target, features, training window, hyperparameters (including the seed), the
backtest metrics, the interval method, the known limits and an artifact hash so
a rerun with the same inputs can be compared byte-for-byte.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import pandas as pd

from aicor.compute.config import AnalysisConfig

LIMITATIONS = [
    "N rất nhỏ: tối đa vài chục quan sát pooled sau khi z16Q đủ cửa sổ; kết quả nhạy với lựa chọn feature.",
    "R&D là proxy cho đầu tư AI, không phải chi tiêu AI được công bố riêng.",
    "Google Trends là chỉ số tương đối, phụ thuộc bộ từ khóa và địa lý đã chốt.",
    "Mô hình tuyến tính, không có deep learning (SPEC §5, FCST-05).",
    "Forecast không biết sự kiện sản phẩm tương lai; chủ yếu dựa trên momentum và seasonality.",
    "Driver attribution là yếu tố đóng góp trong mô hình, KHÔNG phải quan hệ nhân quả.",
    "Đây là thử nghiệm nghiên cứu, không phải khuyến nghị đầu tư.",
]


def _hash_payload(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


def build_model_card(
    *,
    run_id: str,
    model_id: str,
    model_version: str,
    config: AnalysisConfig,
    gate: dict[str, Any],
    backtest: dict[str, Any],
    samples: pd.DataFrame,
    as_of_date: str,
) -> dict[str, Any]:
    """Build the model card dict (also rendered to Markdown by :func:`model_card_markdown`)."""
    train_quarters = sorted(samples["target_quarter"].unique().tolist()) if not samples.empty else []
    metrics = (backtest.get("metrics") or {}).get("0", {}).get("pooled", {})

    core = {
        "model_id": model_id,
        "model_version": model_version,
        "config_version": config.version,
        "feature_set_version": config.feature_set_version,
        "target": config.forecast_target,
        "horizons": list(config.forecast_horizons),
        "features": list(config.__dict__.get("features", []) or []),
        "alpha_grid": list(config.alpha_grid),
        "random_state": config.random_state,
        "n_samples": len(samples),
    }
    artifact_hash = _hash_payload(core)

    return {
        **core,
        "run_id": run_id,
        "as_of_date": as_of_date,
        "as_of_policy": (
            "Mọi feature chỉ dùng dữ liệu có available_at <= as_of_date; "
            "giá trị target chỉ dùng để huấn luyện/đánh giá."
        ),
        "features": [
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
        ],
        "training_window": {
            "first_target_quarter": train_quarters[0] if train_quarters else None,
            "last_target_quarter": train_quarters[-1] if train_quarters else None,
            "n_quarters": len(train_quarters),
        },
        "hyperparameters": {
            "alpha_grid": list(config.alpha_grid),
            "conformal_window": config.conformal_window,
            "random_state": config.random_state,
            "standardization": "train-only mean/std, median imputation",
        },
        "interval_method": {
            "levels": list(config.interval_levels),
            "method": "split-conformal on chronological calibration block; normal fallback if <3 residuals",
        },
        "backtest_metrics_h0_pooled": metrics,
        "quality_gate": gate,
        "coverage": (backtest.get("coverage") or {}).get("0", {}).get("pooled", {}),
        "limitations": LIMITATIONS,
        "artifact_hash": artifact_hash,
        "disclaimer": "Experimental research output — không phải khuyến nghị đầu tư.",
    }


def model_card_markdown(card: dict[str, Any]) -> str:
    """Render the card as Markdown for ``docs``/repository review."""
    lines = [
        f"# Model card — {card['model_id']} ({card['model_version']})",
        "",
        f"- **Run:** `{card['run_id']}`",
        f"- **As of:** {card['as_of_date']}",
        f"- **Config version:** `{card['config_version']}`",
        f"- **Feature set:** `{card['feature_set_version']}`",
        f"- **Target:** `{card['target']}` · horizons {card['horizons']}",
        f"- **Samples:** {card['n_samples']}",
        f"- **Artifact hash:** `{card['artifact_hash']}`",
        "",
        "## As-of policy",
        card["as_of_policy"],
        "",
        "## Features",
        *[f"- `{f}`" for f in card["features"]],
        "",
        "## Hyperparameters",
        "```json",
        json.dumps(card["hyperparameters"], indent=2, ensure_ascii=False),
        "```",
        "",
        "## Backtest (h=0, pooled)",
    ]
    metrics = card.get("backtest_metrics_h0_pooled") or {}
    if metrics:
        lines += ["| Model | n | MAE | RMSE | Directional accuracy |", "| --- | --- | --- | --- | --- |"]
        for model, m in metrics.items():
            lines.append(
                f"| {model} | {int(m['n'])} | {m['mae']:.4f} | {m['rmse']:.4f} | "
                f"{m['directional_accuracy'] if m['directional_accuracy'] == m['directional_accuracy'] else 'n/a'} |"
            )
    else:
        lines.append("_Không có metric backtest (chưa đủ mẫu)._")

    gate = card.get("quality_gate") or {}
    lines += [
        "",
        "## Quality gate (FCST-08)",
        f"**Passed:** {gate.get('passed')} — {gate.get('reason') or 'ok'}",
        "",
        "```json",
        json.dumps(gate.get("checks", []), indent=2, ensure_ascii=False),
        "```",
        "",
        "## Interval method",
        f"{card['interval_method']['method']} · levels {card['interval_method']['levels']}",
        "",
        "## Limits",
        *[f"- {item}" for item in card["limitations"]],
        "",
        f"_{card['disclaimer']}_",
        "",
    ]
    return "\n".join(lines)
