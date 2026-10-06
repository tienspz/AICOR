"""
Unit tests for CSV schemas, date conversion, and validation contracts.
"""
import pytest
from src.common.schemas import (
    date_to_quarter,
    validate_quarter_format,
    validate_product_category,
    validate_relationship_types,
    validate_confidence_level,
    RAW_SCHEMAS,
    PROCESSED_SCHEMAS,
)


def test_date_to_quarter():
    assert date_to_quarter("2022-01-15") == "2022-Q1"
    assert date_to_quarter("2022-03-31") == "2022-Q1"
    assert date_to_quarter("2022-04-01") == "2022-Q2"
    assert date_to_quarter("2023-09-20") == "2023-Q3"
    assert date_to_quarter("2024-12-31") == "2024-Q4"
    assert date_to_quarter("2025-Q2") == "2025-Q2"


def test_date_to_quarter_invalid():
    with pytest.raises(ValueError):
        date_to_quarter("invalid-date")
    with pytest.raises(ValueError):
        date_to_quarter("")


def test_validate_quarter_format():
    assert validate_quarter_format("2022-Q1") is True
    assert validate_quarter_format("2026-Q4") is True
    assert validate_quarter_format("2022-Q5") is False
    assert validate_quarter_format("202-Q1") is False
    assert validate_quarter_format("2022Q1") is False


def test_validate_product_category():
    assert validate_product_category("A") == 3.0
    assert validate_product_category("b") == 2.0
    assert validate_product_category("C") == 1.0
    with pytest.raises(ValueError):
        validate_product_category("D")


def test_validate_relationship_types():
    assert validate_relationship_types("invest") == ["invest"]
    assert set(validate_relationship_types("partner + compete")) == {"partner", "compete"}
    with pytest.raises(ValueError):
        validate_relationship_types("unknown_rel")


def test_validate_confidence_level():
    assert validate_confidence_level("high") == "high"
    assert validate_confidence_level("Medium") == "medium"
    assert validate_confidence_level("LOW") == "low"
    with pytest.raises(ValueError):
        validate_confidence_level("guessed")


def test_schema_definitions():
    assert "rnd_spend" in PROCESSED_SCHEMAS["fact_quarterly"]
    assert "product_score" in PROCESSED_SCHEMAS["fact_quarterly"]
    assert "e_score" in PROCESSED_SCHEMAS["fact_quarterly"]
    assert "filing_date" in RAW_SCHEMAS["rnd_msft"]
