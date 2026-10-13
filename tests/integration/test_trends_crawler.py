"""Tests for trends crawler circuit breaker (Task 6)."""

from unittest.mock import patch

import pytest

from aicor.sources.trends import TrendsUnavailable, fetch_trends


def test_trends_circuit_breaker_falls_back():
    """Any pytrends exception → TrendsUnavailable (§7.4 weight fallback)."""
    with patch(
        "aicor.sources.trends.TrendReq",
        side_effect=Exception("Google blocked us"),
    ):
        # fetch_trends should wrap ALL exceptions into TrendsUnavailable
        with pytest.raises(TrendsUnavailable):
            fetch_trends(["Microsoft AI"], "US", "2022-01-01 2026-10-13")


def test_trends_fixture_returns_correct_shape():
    df = fetch_trends(
        ["Microsoft AI", "Google AI"], "US", "2022-01-01 2026-10-13",
        offline_fixture=True,
    )
    assert list(df.columns) == ["date", "keyword", "interest_score"]
    assert len(df) == 4  # 2 keywords × 2 time points


def test_trends_fixture_keywords_preserved():
    kws = ["Azure AI", "Gemini"]
    df = fetch_trends(kws, "US", "2022-01-01 2026-10-13", offline_fixture=True)
    assert set(df["keyword"].unique()) == set(kws)
