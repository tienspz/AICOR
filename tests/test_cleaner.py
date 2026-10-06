"""
Unit tests for data cleaner module.
"""
import pytest
from src.cleaning.cleaner import (
    clean_rnd_msft,
    clean_events_launch,
    clean_trends,
    clean_ai_spend_est,
    run_data_cleaner,
)


def test_clean_rnd_msft():
    raw = [
        {"company_id": "1", "company_name": "Microsoft", "filing_date": "2022-04-26", "quarter": "2022-Q1", "rnd_spend": "5600000000", "source_url": "sec.gov"},
        {"company_id": "1", "company_name": "Microsoft", "filing_date": "invalid-date", "quarter": "", "rnd_spend": "-100", "source_url": ""},  # Should drop
    ]
    cleaned, dropped = clean_rnd_msft(raw)
    assert len(cleaned) == 1
    assert dropped == 1
    assert cleaned[0]["quarter"] == "2022-Q1"
    assert cleaned[0]["rnd_spend"] == 5600000000.0


def test_clean_events_launch():
    raw = [
        {"company_id": "2", "company_name": "OpenAI", "launch_date": "2023-03-14", "quarter": "2023-Q1", "product_name": "GPT-4", "category": "A", "source_url": "url1", "coder": "AUDIT"},
        {"company_id": "2", "company_name": "OpenAI", "launch_date": "2023-08-28", "quarter": "2023-Q3", "product_name": "Enterprise", "category": "b", "source_url": "url2"},
        {"company_id": "2", "company_name": "OpenAI", "launch_date": "2023-10-01", "quarter": "2023-Q4", "product_name": "", "category": "C"},  # Should drop: no name
    ]
    cleaned, dropped = clean_events_launch(raw)
    assert len(cleaned) == 2
    assert dropped == 1
    assert cleaned[0]["points"] == 3.0
    assert cleaned[1]["points"] == 2.0


def test_clean_trends():
    raw = [
        {"company_id": "1", "company_name": "Microsoft", "date": "2023-05-15", "quarter": "2023-Q2", "trend_value": "45.5"},
        {"company_id": "2", "company_name": "OpenAI", "date": "2023-05-15", "quarter": "2023-Q2", "trend_value": "150.0"},  # Should clamp to 100
        {"company_id": "3", "company_name": "Anthropic", "date": "", "quarter": "", "trend_value": "20"},  # Should drop: no date
    ]
    cleaned, dropped = clean_trends(raw)
    assert len(cleaned) == 2
    assert dropped == 1
    assert cleaned[0]["trend_value"] == 45.5
    assert cleaned[1]["trend_value"] == 100.0
