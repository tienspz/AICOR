"""Tests for IR crawler (Task 7 & Research Blogs Tier A)."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from aicor.config import Settings
from aicor.sources.ir import (
    GRES_FEED_URL,
    IR_FEEDS,
    MSR_FEED_URL,
    IrItem,
    _parse_date,
    classify_abc,
    dedup_ir_items,
    load_rubric,
    main as ir_main,
)


@pytest.fixture
def ir_items_dup():
    """Two items with the same URL (different trailing slash)."""
    return [
        IrItem(
            product_name="Copilot Launch",
            announcement_date="2024-03-15",
            description="Microsoft launches Copilot GA",
            source_url="https://blogs.microsoft.com/copilot-ga/",
        ),
        IrItem(
            product_name="Copilot Launch (dup)",
            announcement_date="2024-03-15",
            description="Same page, different trailing slash",
            source_url="https://blogs.microsoft.com/copilot-ga",
        ),
    ]


def test_rubric_rejects_duplicate_url(ir_items_dup):
    """SPEC §6.3: no counting duplicates across pages."""
    out = dedup_ir_items(ir_items_dup)
    assert len(out) == 1
    cat, rationale = classify_abc(out[0])
    assert cat in ("A", "B", "C")
    assert rationale  # non-empty


def test_classify_abc_a_launch():
    item = IrItem("Copilot", "2024-03-15", "General availability launch", "https://x.com/a")
    cat, _ = classify_abc(item)
    assert cat == "A"


def test_classify_abc_b_preview():
    item = IrItem("Azure AI", "2024-04-01", "Public preview of new model", "https://x.com/b")
    cat, _ = classify_abc(item)
    assert cat == "B"


def test_classify_abc_c_default():
    item = IrItem("Paper", "2024-05-01", "Research findings on efficiency", "https://x.com/c")
    cat, _ = classify_abc(item)
    assert cat == "C"


def test_dedup_preserves_order():
    items = [
        IrItem("A", "2024-01-01", "desc A", "https://x.com/a"),
        IrItem("B", "2024-01-02", "desc B", "https://x.com/b"),
        IrItem("A dup", "2024-01-01", "desc A dup", "https://x.com/A"),  # same normalized
    ]
    out = dedup_ir_items(items)
    assert len(out) == 2
    assert out[0].product_name == "A"
    assert out[1].product_name == "B"


def test_ir_feeds_include_research_blogs():
    assert IR_FEEDS["MSFT"][-1] == MSR_FEED_URL
    assert IR_FEEDS["GOOGL"][-1] == GRES_FEED_URL
    assert len(IR_FEEDS["MSFT"]) == 3 and len(IR_FEEDS["GOOGL"]) == 3


def test_research_paper_classifies_as_c():
    item = IrItem(
        "Efficient Transformers",
        "2024-05-01",
        "Research findings on attention efficiency",
        "https://research.google/blog/efficient-transformers/",
    )
    assert classify_abc(item)[0] == "C"


def test_dedup_same_story_different_blog():
    items = [
        IrItem("Gemini update", "2024-06-01", "d1", "https://blog.google/gemini-update/"),
        IrItem("Gemini Update! ", "2024-06-01", "d2", "https://research.google/blog/gemini-update/"),
    ]
    assert len(dedup_ir_items(items)) == 1


def test_parse_date_iso_and_rfc822():
    assert _parse_date("2024-06-01T10:00:00Z") == _parse_date("Sat, 01 Jun 2024 10:00:00 GMT")
    assert _parse_date("2024-06-01") == "2024-06-01"


def test_feed_failure_isolates_per_feed(monkeypatch, tmp_path):
    """NFR-04: If 1 feed fails, other feeds succeed and get saved."""
    from aicor.sources import ir

    test_settings = Settings(data_dir=str(tmp_path / "data"))

    def mock_scrape(feed_url, settings=None):
        if "azure" in feed_url:
            raise ConnectionError("Simulated feed failure")
        return [
            IrItem(
                product_name=f"Product from {feed_url}",
                announcement_date="2024-06-01",
                description="General announcement",
                source_url=f"{feed_url}/item1",
            )
        ]

    monkeypatch.setattr(ir, "get_settings", lambda: test_settings)
    monkeypatch.setattr(ir, "scrape_ir_blog", mock_scrape)
    monkeypatch.setattr(ir, "load_historical_milestones", lambda c, settings=None: [])

    # Run main()
    ir_main()

    # Verify CSV files are saved for both MSFT and GOOGL despite Azure feed failure
    msft_csv = tmp_path / "data" / "raw" / "ir" / "ir_msft.csv"
    googl_csv = tmp_path / "data" / "raw" / "ir" / "ir_googl.csv"
    assert msft_csv.exists()
    assert googl_csv.exists()


@pytest.mark.live
def test_live_research_feeds_accessible():
    import feedparser

    f1 = feedparser.parse(GRES_FEED_URL)
    assert len(f1.entries) > 0
    f2 = feedparser.parse(MSR_FEED_URL)
    assert len(f2.entries) > 0
