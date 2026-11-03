"""Alert rules for AICOR Pulse (FCST-09).

Rules are evaluated only on **valid, gated** forecast results. A suppressed
result still produces a row in ``alert_log`` with ``status='suppressed'`` and a
reason, so an auditor can see that alerts were considered, not skipped.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from aicor.compute.config import AnalysisConfig

ALERT_COLUMNS = [
    "alert_id",
    "company",
    "target_period",
    "horizon",
    "rule_id",
    "severity",
    "message",
    "as_of_date",
    "model_run_id",
    "forecast_result_id",
    "status",
    "triggered_at",
    "observed_value",
    "threshold",
]


def _alert_id(run_id: str, company: str, target: str, horizon: int, rule: str) -> str:
    digest = hashlib.sha256(f"{run_id}|{company}|{target}|{horizon}|{rule}".encode()).hexdigest()[:12]
    return f"ALT-{digest}"


def evaluate_alerts(
    results: list[dict[str, object]],
    *,
    run_id: str,
    config: AnalysisConfig,
    gate_passed: bool,
    last_published_e: dict[str, float | None] | None = None,
) -> list[dict[str, object]]:
    """Evaluate the three FCST-09 rules.

    * ``interval_crosses_zero`` — the 80% interval of E straddles 0.
    * ``e_below_threshold`` — the point estimate is below ``alert_e_threshold``.
    * ``nowcast_deviation`` — nowcast E deviates from the last published E.

    Returns ``alert_log`` rows (triggered and non-triggered are distinguished by
    ``status``: ``open``, ``closed``, ``suppressed``).
    """
    now = datetime.now(UTC).isoformat(timespec="seconds")
    rows: list[dict[str, object]] = []
    published = last_published_e or {}

    for result in results:
        company = str(result.get("company"))
        target = str(result.get("target_period"))
        horizon = int(result.get("horizon", 0))
        point = result.get("point")
        low80 = result.get("interval_low_80")
        high80 = result.get("interval_high_80")

        rules: list[tuple[str, bool, str, str, float | None]] = []

        crosses = (
            point is not None
            and low80 is not None
            and high80 is not None
            and float(low80) <= 0.0 <= float(high80)
        )
        if point is None or low80 is None or high80 is None:
            interval_message = "Không có interval 80% (kết quả không đủ dữ liệu) — không xét rule này."
        else:
            interval_message = (
                f"Khoảng 80% của E [{float(low80):.2f}; {float(high80):.2f}] cắt 0 — "
                "không phân biệt được dấu của E."
            )
        rules.append(
            (
                "interval_crosses_zero",
                crosses,
                interval_message,
                config.alert_severity.get("interval_crosses_zero", "WARN"),
                0.0,
            )
        )

        below = point is not None and float(point) < config.alert_e_threshold
        rules.append(
            (
                "e_below_threshold",
                below,
                (
                    f"E dự báo {float(point):.2f} thấp hơn ngưỡng {config.alert_e_threshold:.2f}."
                    if point is not None
                    else "Không có point estimate để so ngưỡng."
                ),
                config.alert_severity.get("e_below_threshold", "CRITICAL"),
                config.alert_e_threshold,
            )
        )

        if horizon == 0:
            last_e = published.get(company)
            deviation = None
            if last_e is not None and point is not None:
                deviation = abs(float(point) - float(last_e))
            triggers = deviation is not None and deviation > config.alert_nowcast_deviation
            rules.append(
                (
                    "nowcast_deviation",
                    bool(triggers),
                    (
                        f"Nowcast lệch {deviation:.2f} so với E công bố gần nhất ({float(last_e):.2f})."
                        if deviation is not None
                        else "Không có E công bố gần nhất để so sánh."
                    ),
                    config.alert_severity.get("nowcast_deviation", "INFO"),
                    config.alert_nowcast_deviation,
                )
            )

        for rule_id, triggered, message, severity, threshold in rules:
            if not gate_passed:
                status = "suppressed"
                message = (
                    "Bị chặn: quality gate (FCST-08) không đạt — alert không được đánh giá "
                    "trên kết quả chưa đủ tin cậy."
                )
            elif triggered:
                status = "open"
            else:
                status = "closed"

            rows.append(
                {
                    "alert_id": _alert_id(run_id, company, target, horizon, rule_id),
                    "company": company,
                    "target_period": target,
                    "horizon": horizon,
                    "rule_id": rule_id,
                    "severity": severity if gate_passed else "INFO",
                    "message": message,
                    "as_of_date": result.get("as_of_date"),
                    "model_run_id": run_id,
                    "forecast_result_id": result.get("forecast_result_id"),
                    "status": status,
                    "triggered_at": now,
                    "observed_value": point,
                    "threshold": threshold,
                }
            )

    return rows


def alert_precision(backtest_folds, threshold: float = -0.25) -> dict[str, object]:
    """Precision of the binary ``e_below_threshold`` rule on the backtest.

    A triggered fold is a true positive when the realised E also falls below
    the threshold. Fewer than three triggers are reported as "insufficient
    evidence" instead of a precision number that would overstate confidence.
    """
    if backtest_folds is None or len(backtest_folds) == 0:
        return {"n_triggers": 0, "precision": None, "status": "insufficient_evidence"}

    hinge = backtest_folds[backtest_folds.get("model") == "naive"] if "model" in backtest_folds else backtest_folds
    triggers = hinge[hinge["predicted"] < threshold]
    if triggers.empty:
        return {"n_triggers": 0, "precision": None, "status": "no_triggers"}
    hits = (triggers["actual"] < threshold).sum()
    if len(triggers) < 3:
        return {
            "n_triggers": len(triggers),
            "precision": None,
            "status": "insufficient_evidence",
        }
    return {
        "n_triggers": len(triggers),
        "precision": float(hits) / float(len(triggers)),
        "status": "reported",
    }
