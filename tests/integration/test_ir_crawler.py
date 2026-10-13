"""Tests for IR crawler (Task 7)."""

import pytest

from aicor.sources.ir import IrItem, classify_abc, dedup_ir_items, load_rubric


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
