"""
Tests for Task BE-04: Pre-computed Web JSON Bundles Exporter.
"""
import csv
import json
import math

from src.computation.exporter import export_web_json_bundles


def _write_fact_csv(path):
    fieldnames = [
        "company_id", "company_name", "quarter", "rnd_spend", "ai_spend_est",
        "est_confidence", "trends_qavg", "product_score", "product_ma4q",
        "trends_ma4q", "in_score", "out_score", "e_score", "valid_from",
    ]
    rows = []
    for cid, cname in [(1, "Microsoft"), (2, "OpenAI"), (3, "Anthropic")]:
        for i, q in enumerate(["2025-Q3", "2025-Q4", "2026-Q1", "2026-Q2"]):
            rows.append(
                {
                    "company_id": cid, "company_name": cname, "quarter": q,
                    "rnd_spend": 1000 + i if cid == 1 else "",
                    "ai_spend_est": "" if cid == 1 else 500 + i * 10,
                    "est_confidence": "high", "trends_qavg": 10 + i,
                    "product_score": i, "product_ma4q": i * 0.5,
                    "trends_ma4q": 10 + i, "in_score": 0.1 * i,
                    "out_score": 0.2 * i, "e_score": 0.1 * i,
                    "valid_from": "2026-06-30",
                }
            )
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _assert_no_nan(obj):
    if isinstance(obj, float):
        assert not (math.isnan(obj) or math.isinf(obj))
    elif isinstance(obj, dict):
        for v in obj.values():
            _assert_no_nan(v)
    elif isinstance(obj, list):
        for v in obj:
            _assert_no_nan(v)


def test_export_web_json_bundles_structure(tmp_path):
    _write_fact_csv(tmp_path / "fact_quarterly.csv")
    result = export_web_json_bundles(tmp_path)
    assert set(result.keys()) == {"chart_series", "timeline_events", "portfolio_baseline"}

    with open(tmp_path / "chart_series.json", encoding="utf-8") as f:
        chart = json.load(f)
    assert set(chart["companies"].keys()) == {"MSFT", "OpenAI", "Anthropic"}
    for key in ("MSFT", "OpenAI", "Anthropic"):
        assert len(chart["companies"][key]["series"]) == 4
    assert chart["quarters"] == ["2025-Q3", "2025-Q4", "2026-Q1", "2026-Q2"]
    _assert_no_nan(chart)

    with open(tmp_path / "timeline_events.json", encoding="utf-8") as f:
        timeline = json.load(f)
    assert "events" in timeline and isinstance(timeline["events"], list)
    dates = [e.get("date") or "" for e in timeline["events"]]
    assert dates == sorted(dates)
    _assert_no_nan(timeline)

    with open(tmp_path / "portfolio_baseline.json", encoding="utf-8") as f:
        baseline = json.load(f)
    assert baseline["reference_window"] == ["2025-Q3", "2025-Q4", "2026-Q1", "2026-Q2"]
    assert set(baseline["medians"].keys()) == {"MSFT", "OpenAI", "Anthropic"}
    assert "không phải khuyến nghị đầu tư" in baseline["disclaimer"]
    _assert_no_nan(baseline)
