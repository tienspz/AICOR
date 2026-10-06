"""
Unit tests for Calculator and Sensitivity Engine.
"""
import pytest
from src.computation.calculator import (
    compute_z_score,
    calculate_mean_and_std,
    calculate_indices,
)
from src.computation.sensitivity import run_sensitivity_analysis


def test_zero_variance_guard():
    # If all values are identical, std is 0 -> z-score must be 0.0
    mean_val, std_val = calculate_mean_and_std([100.0, 100.0, 100.0])
    assert std_val == 0.0
    z = compute_z_score(100.0, mean_val, std_val)
    assert z == 0.0


def test_formula_e_numerical():
    # From CMU SRS C.6: If In = 0.8 and Out = 1.3, then E = 1.3 - 0.8 = +0.5
    In = 0.8
    Out = 1.3
    E = round(Out - In, 3)
    assert E == 0.5


def test_calculate_indices_integration():
    mock_fact = {
        (1, "2022-Q1"): {"company_id": 1, "company_name": "Microsoft", "rnd_spend": 5000, "product_ma4q": 10.0, "trends_ma4q": 20.0},
        (1, "2022-Q2"): {"company_id": 1, "company_name": "Microsoft", "rnd_spend": 7000, "product_ma4q": 20.0, "trends_ma4q": 30.0},
        (2, "2022-Q1"): {"company_id": 2, "company_name": "OpenAI", "ai_spend_est": 100, "product_ma4q": 5.0, "trends_ma4q": 15.0},
        (2, "2022-Q2"): {"company_id": 2, "company_name": "OpenAI", "ai_spend_est": 300, "product_ma4q": 15.0, "trends_ma4q": 25.0},
        (3, "2022-Q1"): {"company_id": 3, "company_name": "Anthropic", "ai_spend_est": 50, "product_ma4q": 2.0, "trends_ma4q": 10.0},
        (3, "2022-Q2"): {"company_id": 3, "company_name": "Anthropic", "ai_spend_est": 150, "product_ma4q": 8.0, "trends_ma4q": 20.0},
    }

    res = calculate_indices(mock_fact, w_product=0.6, w_trends=0.4)
    # Check that in_score, out_score, e_score are computed
    for k, v in res.items():
        assert "in_score" in v
        assert "out_score" in v
        assert "e_score" in v
        assert round(v["out_score"] - v["in_score"], 3) == v["e_score"]


def test_sensitivity_analysis():
    mock_fact = {
        (1, "2022-Q1"): {"company_id": 1, "company_name": "Microsoft", "rnd_spend": 5000, "product_ma4q": 10.0, "trends_ma4q": 20.0},
        (1, "2022-Q2"): {"company_id": 1, "company_name": "Microsoft", "rnd_spend": 7000, "product_ma4q": 20.0, "trends_ma4q": 30.0},
        (2, "2022-Q1"): {"company_id": 2, "company_name": "OpenAI", "ai_spend_est": 100, "product_ma4q": 5.0, "trends_ma4q": 15.0},
        (2, "2022-Q2"): {"company_id": 2, "company_name": "OpenAI", "ai_spend_est": 300, "product_ma4q": 15.0, "trends_ma4q": 25.0},
        (3, "2022-Q1"): {"company_id": 3, "company_name": "Anthropic", "ai_spend_est": 50, "product_ma4q": 2.0, "trends_ma4q": 10.0},
        (3, "2022-Q2"): {"company_id": 3, "company_name": "Anthropic", "ai_spend_est": 150, "product_ma4q": 8.0, "trends_ma4q": 20.0},
    }

    rows = run_sensitivity_analysis(mock_fact)
    assert len(rows) == 2 * 3  # 2 quarters * 3 weight presets
    for r in rows:
        assert "ranking_order" in r
        assert "is_stable" in r
