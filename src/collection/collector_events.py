"""
AICOR Events & Spending Collector
Scrapes / collects:
1. Product launch announcements (categorized A/B/C per Appendix A)
2. Funding rounds & valuations
3. Tripartite relationship events (invest/partner/compete/statement per Appendix B)
4. AI spend estimates for OpenAI & Anthropic (with confidence tags per Appendix C.4)
"""
import logging
from typing import List, Dict, Any

from src.common.schemas import (
    date_to_quarter,
    validate_product_category,
    validate_relationship_types,
    validate_confidence_level,
)
from src.collection.storage import append_to_raw_csv

logger = logging.getLogger("aicor.collector.events")


def record_launch_event(
    company_id: int,
    company_name: str,
    launch_date: str,
    product_name: str,
    category: str,
    source_url: str,
    coder: str = "AICOR_BOT",
) -> Dict[str, Any]:
    """Formats and validates a product launch event record."""
    points = validate_product_category(category)
    quarter = date_to_quarter(launch_date)
    return {
        "company_id": company_id,
        "company_name": company_name,
        "launch_date": launch_date,
        "quarter": quarter,
        "product_name": product_name.strip(),
        "category": category.upper(),
        "points": points,
        "source_url": source_url,
        "coder": coder,
    }


def record_funding_event(
    company_id: int,
    company_name: str,
    funding_date: str,
    amount: float,
    valuation: float,
    source_url: str,
) -> Dict[str, Any]:
    """Formats and validates a funding event record."""
    quarter = date_to_quarter(funding_date)
    return {
        "company_id": company_id,
        "company_name": company_name,
        "funding_date": funding_date,
        "quarter": quarter,
        "amount": float(amount),
        "valuation": float(valuation) if valuation else "",
        "source_url": source_url,
    }


def record_relationship_event(
    event_date: str,
    parties: str,
    rel_type: str,
    quote: str,
    source_url: str,
) -> Dict[str, Any]:
    """Formats and validates a tripartite relationship event record."""
    validate_relationship_types(rel_type)
    quarter = date_to_quarter(event_date)
    return {
        "event_date": event_date,
        "quarter": quarter,
        "parties": parties.strip(),
        "rel_type": rel_type.strip(),
        "quote": quote.strip(),
        "source_url": source_url,
    }


def record_spend_estimate(
    company_id: int,
    company_name: str,
    quarter: str,
    ai_spend_est: float,
    est_confidence: str,
    source_url: str,
) -> Dict[str, Any]:
    """Formats and validates an estimated AI spend entry."""
    conf = validate_confidence_level(est_confidence)
    return {
        "company_id": company_id,
        "company_name": company_name,
        "quarter": quarter,
        "ai_spend_est": float(ai_spend_est),
        "est_confidence": conf,
        "source_url": source_url,
    }
