"""Unit tests for the rubric classifier (Task 7)."""

from aicor.sources.ir import IrItem, classify_abc, load_rubric


def test_rubric_loads():
    rubric = load_rubric()
    assert rubric["version"].startswith("v1")
    assert "categories" in rubric
    assert set(rubric["categories"].keys()) == {"A", "B", "C"}


def test_rubric_weights():
    rubric = load_rubric()
    assert rubric["categories"]["A"]["score_weight"] == 3
    assert rubric["categories"]["B"]["score_weight"] == 2
    assert rubric["categories"]["C"]["score_weight"] == 1


def test_classify_returns_rationale():
    item = IrItem("Test", "2024-01-01", "Some description", "https://x.com/t")
    cat, rationale = classify_abc(item)
    assert isinstance(rationale, str)
    assert len(rationale) > 0
