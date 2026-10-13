"""Project-wide configuration and constants.

Sources: SPEC §3.3 (canonical URLs), §12 (tech stack), NFR-06/07.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


# ---------- constants (SPEC §0 Quyết định 1) ----------

COMPANY_CIK: dict[str, str] = {
    "MSFT": "789019",
    "GOOGL": "1652044",
}

COMPANY_TICKERS: list[str] = ["MSFT", "GOOGL"]

# Canonical SEC XBRL URLs (SPEC §3.3)
SEC_COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_padded}.json"

# Rate-limiting (NFR-07): SEC asks ≤10 req/s
REQUESTS_PER_SEC: int = 10
REQUEST_DELAY: float = 1.0 / REQUESTS_PER_SEC


# ---------- settings ----------

@dataclass(frozen=True)
class Settings:
    """Runtime settings — read from env, never hardcoded secrets (NFR-06)."""

    sec_user_agent: str = "AICOR-research/1.0 (contact: repo README)"
    companies: dict[str, str] = field(default_factory=lambda: dict(COMPANY_CIK))
    requests_per_sec: int = REQUESTS_PER_SEC
    data_dir: str = "data"


def get_settings(env: dict[str, str] | None = None) -> Settings:
    """Build settings from *env* (defaults to ``os.environ``).

    >>> s = get_settings(env={})
    >>> "AICOR" in s.sec_user_agent
    True
    """
    if env is None:
        env = dict(os.environ)

    sec_ua = env.get("SEC_USER_AGENT")
    return Settings(
        sec_user_agent=sec_ua.strip() if sec_ua and sec_ua.strip() else Settings.sec_user_agent,
        data_dir=env.get("AICOR_DATA_DIR", Settings.data_dir),
    )
