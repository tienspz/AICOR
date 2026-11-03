"""Shared deterministic fixtures for the Phase 2 / 2.5 test suite."""

from __future__ import annotations

import pandas as pd
import pytest

QUARTER_ENDS = pd.date_range("2021-03-31", periods=20, freq="QE-DEC")
KEYWORDS = {"MSFT": ["Microsoft AI", "Azure AI"], "GOOGL": ["Google AI", "Gemini"]}


def quarter_label(ts: pd.Timestamp) -> str:
    return f"{ts.year}Q{(ts.month - 1) // 3 + 1}"


def build_panel() -> pd.DataFrame:
    """20 quarters per company with a non-degenerate R&D series."""
    rows = []
    for company, offset in (("MSFT", 0), ("GOOGL", 1500)):
        for i, ts in enumerate(QUARTER_ENDS):
            revenue = 40000 + 900 * i + offset
            rd = 5000 + 180 * i + offset * 0.4 + (60 if i % 3 == 0 else 0)
            rows.append(
                {
                    "period_end_date": ts.date().isoformat(),
                    "company": company,
                    "source_id": f"SEC-{company}-{ts.date().isoformat()}",
                    "revenue": float(revenue),
                    "rd_expense": float(rd),
                    "capex": float(3000 + 90 * i),
                    "operating_income": float(revenue * 0.3),
                    "net_income": float(revenue * 0.2),
                    "cfo": float(revenue * 0.35),
                    "year": ts.year,
                    "calendar_quarter": (ts.month - 1) // 3 + 1,
                    "unit_scale": "millions",
                    "sync_status": "success",
                    "status": "available",
                }
            )
    return pd.DataFrame(rows)


def build_products() -> pd.DataFrame:
    rows = []
    for company in ("MSFT", "GOOGL"):
        for i, ts in enumerate(QUARTER_ENDS):
            for k in range((i % 3) + 1):
                rows.append(
                    {
                        "product_name": f"{company} product {i}-{k}",
                        "announcement_date": (ts - pd.Timedelta(days=10)).date().isoformat(),
                        "description": "AI announcement",
                        "source_url": f"https://example.invalid/{company}/{i}/{k}",
                        "category": ["A", "B", "C"][k % 3],
                        "category_rationale": "fixture",
                        "review_status": "reviewed",
                        "company": company,
                    }
                )
    return pd.DataFrame(rows)


def build_trends() -> pd.DataFrame:
    rows = []
    for company, keywords in KEYWORDS.items():
        for i, ts in enumerate(QUARTER_ENDS):
            for keyword in keywords:
                rows.append(
                    {
                        "calendar_quarter": quarter_label(ts),
                        "keyword": keyword,
                        "interest_score": float(10 + 1.5 * i + (3 if company == "MSFT" else 6)),
                    }
                )
    return pd.DataFrame(rows)


def build_market() -> pd.DataFrame:
    rows = []
    for company, base in (("MSFT", 300.0), ("GOOGL", 120.0)):
        for i, ts in enumerate(QUARTER_ENDS):
            rows.append(
                {
                    "calendar_quarter": quarter_label(ts),
                    "company": company,
                    "adj_close": base + i * 4.0,
                    "volume": float(1_000_000 + i * 1000),
                }
            )
    return pd.DataFrame(rows)


def write_processed(data_dir, *, panel=None, products=None, trends=None, market=None) -> None:
    proc = data_dir / "processed"
    proc.mkdir(parents=True, exist_ok=True)
    (panel if panel is not None else build_panel()).to_csv(proc / "panel_quarterly.csv", index=False)
    (products if products is not None else build_products()).to_csv(proc / "ai_products.csv", index=False)
    (trends if trends is not None else build_trends()).to_csv(proc / "google_trends_quarterly.csv", index=False)
    (market if market is not None else build_market()).to_csv(proc / "market_quarterly.csv", index=False)


@pytest.fixture
def synthetic_processed(tmp_path):
    """Write a synthetic processed layer into a temp data dir."""
    write_processed(tmp_path)
    return tmp_path


@pytest.fixture
def series_frame_fixture(synthetic_processed):
    """Feature+metric series built from the synthetic processed layer."""
    from aicor.compute.config import load_analysis_config
    from aicor.compute.engine import series_frame
    from aicor.compute.features import build_feature_matrix

    cfg = load_analysis_config()
    proc = synthetic_processed / "processed"
    features = build_feature_matrix(
        pd.read_csv(proc / "panel_quarterly.csv"),
        pd.read_csv(proc / "ai_products.csv"),
        pd.read_csv(proc / "google_trends_quarterly.csv"),
        config=cfg,
    )
    return series_frame(features, cfg)
