"""Tests for integrate module (Task 10)."""

import pandas as pd

from aicor.preprocess.integrate import (
    add_company_dummy,
    capex_intensity,
    event_type_dummies,
    join_panel,
    product_score,
    rd_intensity,
)


def test_product_score_formula():
    """§7.1: product_score = 3*A + 2*B + 1*C."""
    assert product_score({"A": 2, "B": 1, "C": 3}) == 3 * 2 + 2 * 1 + 1 * 3


def test_product_score_empty():
    assert product_score({}) == 0


def test_event_type_dummies_columns():
    dummies = event_type_dummies(["funding", "partnership", "funding"])
    assert "event_funding" in dummies.columns
    assert "event_partnership" in dummies.columns


def test_join_panel_no_label_encoding():
    """Slide 8/9: company must NOT be label-encoded (non-tree-like model)."""
    msft = pd.DataFrame({"period_end_date": ["2024-06-30"], "revenue": [64727.0]})
    googl = pd.DataFrame({"period_end_date": ["2024-06-30"], "revenue": [88268.0]})
    panel = join_panel(msft, googl)
    assert "company_id_int" not in panel.columns
    assert "company" in panel.columns


def test_add_company_dummy():
    panel = pd.DataFrame({"company": ["MSFT", "GOOGL", "MSFT"]})
    out = add_company_dummy(panel)
    assert list(out["is_msft"]) == [1, 0, 1]


def test_rd_intensity_formula():
    assert abs(rd_intensity(5000.0, 50000.0) - 0.1) < 1e-10


def test_rd_intensity_missing():
    assert rd_intensity(None, 50000.0) is None
    assert rd_intensity(5000.0, None) is None
    assert rd_intensity(5000.0, 0.0) is None


def test_capex_intensity():
    assert abs(capex_intensity(10000.0, 50000.0) - 0.2) < 1e-10
