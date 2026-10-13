"""Integration tests for the SEC XBRL crawler (Task 4).

Uses fixture data by default; live tests require ``-m live``.
"""

from datetime import date

import pytest

from aicor.sources.sec import TagResolutionError, resolve_metric


# ---------- Fixture: mimics GOOGL companyfacts structure ----------

@pytest.fixture
def fixture_googl_facts() -> dict:
    """Simplified GOOGL companyfacts with tag switch at 2025-03-31."""
    return {
        "facts": {
            "us-gaap": {
                # Old tag used before 2025-03-31
                "Revenue": {
                    "units": {
                        "USD": [
                            {"end": "2024-12-31", "val": 96469000000},
                            {"end": "2024-09-30", "val": 88268000000},
                        ]
                    }
                },
                # New tag used from 2025-03-31 onward
                "Revenues": {
                    "units": {
                        "USD": [
                            {"end": "2026-03-31", "val": 102500000000},
                            {"end": "2025-12-31", "val": 98700000000},
                        ]
                    }
                },
            }
        }
    }


@pytest.fixture
def fixture_msft_facts() -> dict:
    """Simplified MSFT companyfacts."""
    return {
        "facts": {
            "us-gaap": {
                "Revenues": {
                    "units": {
                        "USD": [
                            {"end": "2024-06-30", "val": 64727000000},
                            {"end": "2024-03-31", "val": 61858000000},
                        ]
                    }
                },
                "ResearchAndDevelopmentExpense": {
                    "units": {
                        "USD": [
                            {"end": "2024-06-30", "val": 7854000000},
                        ]
                    }
                },
            }
        }
    }


# ---------- Offline tests ----------

def test_resolve_googl_revenue_tag_switch(fixture_googl_facts):
    """GOOGL changed XBRL tag between periods; resolver must pick the right one."""
    # Pre-switch: 'Revenue' works
    v1, tag1 = resolve_metric(
        fixture_googl_facts, ["Revenues", "Revenue"], date(2024, 12, 31)
    )
    # Post-switch: 'Revenues' works
    v2, tag2 = resolve_metric(
        fixture_googl_facts, ["Revenues", "Revenue"], date(2026, 3, 31)
    )
    assert tag1 == "Revenue"   # old tag
    assert tag2 == "Revenues"  # new tag
    assert v1 == 96469000000
    assert v2 == 102500000000


def test_resolve_metric_fail_loud_empty_facts():
    """Empty facts → TagResolutionError, NOT silent NULL (ADR-0004)."""
    with pytest.raises(TagResolutionError):
        resolve_metric({}, ["Revenues"], date(2026, 3, 31))


def test_resolve_metric_fail_loud_no_tag_match(fixture_googl_facts):
    """If no tag candidate has data for the period → TagResolutionError."""
    with pytest.raises(TagResolutionError):
        resolve_metric(
            fixture_googl_facts,
            ["NonExistentTag"],
            date(2024, 12, 31),
        )


def test_resolve_metric_fail_loud_wrong_period(fixture_googl_facts):
    """Tag exists but period doesn't match → TagResolutionError."""
    with pytest.raises(TagResolutionError):
        resolve_metric(
            fixture_googl_facts,
            ["Revenue"],
            date(2020, 1, 1),  # way before any data
        )


def test_resolve_msft_rd(fixture_msft_facts):
    val, tag = resolve_metric(
        fixture_msft_facts,
        ["ResearchAndDevelopmentExpense"],
        date(2024, 6, 30),
    )
    assert val == 7854000000
    assert tag == "ResearchAndDevelopmentExpense"
