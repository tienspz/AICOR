"""
AICOR CSV Schemas and Validation Contracts
Defines column schemas for Raw, Cleaned, and Processed CSV files,
with validation logic conforming to CMU SRS v5.1.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.common.config import (
    COMPANIES,
    PRODUCT_CATEGORY_POINTS,
    VALID_RELATIONSHIP_TYPES,
    VALID_CONFIDENCE_LEVELS,
)

# Standard CSV Headers
RAW_SCHEMAS = {
    "rnd_msft": [
        "company_id", "company_name", "filing_date", "quarter", "rnd_spend", "source_url"
    ],
    "ai_spend_est": [
        "company_id", "company_name", "quarter", "ai_spend_est", "est_confidence", "source_url"
    ],
    "events_launch": [
        "company_id", "company_name", "launch_date", "quarter", "product_name", "category", "points", "source_url", "coder"
    ],
    "events_funding": [
        "company_id", "company_name", "funding_date", "quarter", "amount", "valuation", "source_url"
    ],
    "events_relationship": [
        "event_date", "quarter", "parties", "rel_type", "quote", "source_url"
    ],
    "trends": [
        "company_id", "company_name", "date", "quarter", "trend_value"
    ],
    "stock_msft": [
        "company_id", "date", "quarter", "close_price", "source_url"
    ],
}

CLEANED_SCHEMAS = {
    "rnd_msft": RAW_SCHEMAS["rnd_msft"],
    "ai_spend_est": RAW_SCHEMAS["ai_spend_est"],
    "events_launch": RAW_SCHEMAS["events_launch"],
    "events_funding": RAW_SCHEMAS["events_funding"],
    "events_relationship": RAW_SCHEMAS["events_relationship"],
    "trends": RAW_SCHEMAS["trends"],
    "stock_msft": RAW_SCHEMAS["stock_msft"],
}

PROCESSED_SCHEMAS = {
    "fact_quarterly": [
        "company_id", "company_name", "quarter",
        "rnd_spend", "ai_spend_est", "est_confidence",
        "trends_qavg", "product_score", "product_ma4q", "trends_ma4q",
        "in_score", "out_score", "e_score", "valid_from"
    ],
    "sensitivity_analysis": [
        "quarter", "weight_set", "product_weight", "trends_weight",
        "msft_out", "openai_out", "anthropic_out",
        "msft_e", "openai_e", "anthropic_e",
        "ranking_order", "is_stable"
    ],
    "sync_log": [
        "run_at", "rhythm", "status", "rows_added", "error"
    ],
}

# Key columns used for natural key deduplication in append-only storage
DEDUPLICATION_KEYS = {
    "rnd_msft": ["company_id", "quarter"],
    "ai_spend_est": ["company_id", "quarter"],
    "events_launch": ["company_id", "launch_date", "product_name"],
    "events_funding": ["company_id", "funding_date"],
    "events_relationship": ["event_date", "parties", "rel_type"],
    "trends": ["company_id", "date"],
    "stock_msft": ["company_id", "date"],
    "fact_quarterly": ["company_id", "quarter"],
    "sync_log": ["run_at", "rhythm"],
}


def date_to_quarter(date_str: str) -> str:
    """
    Converts a date string (YYYY-MM-DD or YYYY-MM) to a standard quarter string YYYY-Qn.
    Raises ValueError if date format is invalid.
    """
    if not date_str:
        raise ValueError("Empty date string cannot be converted to quarter.")
    date_str = str(date_str).strip()
    
    # If already in YYYY-Qn format
    if len(date_str) == 7 and date_str[4:6] == "-Q" and date_str[6] in "1234":
        return date_str


    try:
        if len(date_str) == 7: # YYYY-MM
            dt = datetime.strptime(date_str, "%Y-%m")
        else:
            dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
        quarter_num = (dt.month - 1) // 3 + 1
        return f"{dt.year}-Q{quarter_num}"
    except Exception as e:
        raise ValueError(f"Invalid date format '{date_str}': {e}")


def validate_quarter_format(quarter_str: str) -> bool:
    """Checks whether a string matches YYYY-Qn format."""
    if not quarter_str or len(quarter_str) != 7:
        return False
    parts = quarter_str.split("-Q")
    if len(parts) != 2:
        return False
    year_str, q_num = parts
    return year_str.isdigit() and len(year_str) == 4 and q_num in {"1", "2", "3", "4"}


def validate_product_category(category: str) -> float:
    """
    Validates category A, B, or C and returns corresponding rubric points (Phụ lục A).
    """
    cat = str(category).strip().upper()
    if cat not in PRODUCT_CATEGORY_POINTS:
        raise ValueError(f"Invalid product category '{category}'. Must be 'A', 'B', or 'C'.")
    return PRODUCT_CATEGORY_POINTS[cat]


def validate_relationship_types(rel_type_str: str) -> List[str]:
    """
    Validates relationship types string, e.g. 'invest', 'partner + compete'.
    Returns list of valid cleaned relationship types.
    """
    if not rel_type_str:
        raise ValueError("Empty relationship type.")
    
    types = [t.strip().lower() for t in str(rel_type_str).replace("+", ",").split(",") if t.strip()]
    for t in types:
        if t not in VALID_RELATIONSHIP_TYPES:
            raise ValueError(f"Invalid relationship type '{t}'. Allowed: {VALID_RELATIONSHIP_TYPES}")
    return types


def validate_confidence_level(level: str) -> str:
    """Validates estimation confidence level (high, medium, low)."""
    lvl = str(level).strip().lower()
    if lvl not in VALID_CONFIDENCE_LEVELS:
        raise ValueError(f"Invalid confidence level '{level}'. Must be 'high', 'medium', or 'low'.")
    return lvl
