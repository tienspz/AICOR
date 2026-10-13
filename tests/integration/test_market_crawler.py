"""Tests for market crawler (Task 5)."""

from aicor.sources.market import MARKET_COLUMNS, fetch_market


def test_market_columns_match_src01():
    """SRC-01 Tier B: market data must have exactly these columns."""
    df = fetch_market("MSFT", period="1mo", offline_fixture=True)
    assert list(df.columns) == MARKET_COLUMNS


def test_market_fixture_has_rows():
    df = fetch_market("GOOGL", period="1mo", offline_fixture=True)
    assert len(df) > 0


def test_market_date_is_date_type():
    df = fetch_market("MSFT", period="1mo", offline_fixture=True)
    from datetime import date
    assert all(isinstance(d, date) for d in df["date"])
