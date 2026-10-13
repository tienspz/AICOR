"""Tests for features metadata (Task 10)."""

from aicor.preprocess.features import FEATURE_REGISTRY, FeatureMeta


def test_all_features_have_required_metadata():
    """§6.1: every derived feature must have method + source + confidence."""
    for name, meta in FEATURE_REGISTRY.items():
        assert meta.name == name
        assert meta.definition, f"{name} missing definition"
        assert meta.calculation_method, f"{name} missing calculation_method"
        assert meta.reported_or_derived in ("reported", "derived")
        assert meta.confidence in ("HIGH", "MEDIUM", "LOW")


def test_rd_intensity_flagged_as_proxy():
    """SRC-06: R&D is a proxy with LOW confidence."""
    rd = FEATURE_REGISTRY["rd_intensity"]
    assert rd.proxy is True
    assert rd.confidence == "LOW"


def test_is_msft_is_derived():
    meta = FEATURE_REGISTRY["is_msft"]
    assert meta.reported_or_derived == "derived"
    assert not meta.proxy
