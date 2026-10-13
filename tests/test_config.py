"""Tests for aicor.config (Task 2)."""

from aicor.config import COMPANY_CIK, get_settings


def test_settings_require_user_agent():
    """SPEC §5: SEC yêu cầu UA phù hợp."""
    s = get_settings(env={})
    assert "AICOR" in s.sec_user_agent


def test_company_cik_locked():
    """SPEC §0 Quyết định 1: chỉ MSFT và GOOGL."""
    assert COMPANY_CIK == {"MSFT": "789019", "GOOGL": "1652044"}


def test_settings_override_from_env():
    s = get_settings(env={"SEC_USER_AGENT": "Custom/2.0 (test)"})
    assert s.sec_user_agent == "Custom/2.0 (test)"
    # Empty string should safely fallback to default
    s_empty = get_settings(env={"SEC_USER_AGENT": ""})
    assert "AICOR" in s_empty.sec_user_agent
    s_whitespace = get_settings(env={"SEC_USER_AGENT": "   "})
    assert "AICOR" in s_whitespace.sec_user_agent


def test_settings_frozen():
    s = get_settings(env={})
    try:
        s.sec_user_agent = "hacked"  # type: ignore[misc]
        assert False, "Settings should be frozen"
    except AttributeError:
        pass
