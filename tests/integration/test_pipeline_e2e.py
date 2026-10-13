"""End-to-end pipeline tests (Task 12).

Uses fixture data for 4 quarters to test the full Collect→Monitor flow.
"""

import numpy as np
import pandas as pd
import pytest

from aicor.pipeline.run import run_pipeline


@pytest.fixture
def sample_4q() -> dict[str, pd.DataFrame]:
    """4-quarter fixture data for MSFT and GOOGL."""
    dates = ["2024-03-31", "2024-06-30", "2024-09-30", "2024-12-31"]

    msft = pd.DataFrame({
        "period_end_date": dates,
        "revenue": [61858e6, 64727e6, 65585e6, 69632e6],
        "rd_expense": [7600e6, 7854e6, 7900e6, 8100e6],
        "capex": [11000e6, 13000e6, 14000e6, 15600e6],
        "source_id": [f"SEC-MSFT-{d}" for d in dates],
    })

    googl = pd.DataFrame({
        "period_end_date": dates,
        "revenue": [80539e6, 84742e6, 88268e6, 96469e6],
        "rd_expense": [11000e6, 11500e6, 12000e6, 12800e6],
        "capex": [12000e6, 13000e6, 13200e6, 14300e6],
        "source_id": [f"SEC-GOOGL-{d}" for d in dates],
    })

    return {
        "sec_msft": msft,
        "sec_googl": googl,
    }


def test_e2e_panel_provenance_complete(sample_4q, tmp_path):
    """SRC-03, NFR-02: every row must have source_id."""
    from aicor.config import Settings

    settings = Settings(data_dir=str(tmp_path))
    panel = run_pipeline(sample_4q, settings=settings)
    assert panel["source_id"].notna().all()


def test_e2e_partial_on_source_failure(sample_4q, tmp_path):
    """NFR-04: 1 source fails → partial, other data preserved."""
    from aicor.config import Settings

    # Simulate trends failure
    sample_4q["trends"] = None  # type: ignore

    settings = Settings(data_dir=str(tmp_path))
    panel = run_pipeline(sample_4q, settings=settings)

    # Panel should still have SEC data
    assert len(panel) > 0
    # At least one row should be partial (because trends failed)
    assert (panel["sync_status"] == "partial").any()


def test_e2e_panel_has_company_dummy(sample_4q, tmp_path):
    from aicor.config import Settings

    settings = Settings(data_dir=str(tmp_path))
    panel = run_pipeline(sample_4q, settings=settings)
    assert "is_msft" in panel.columns
    assert set(panel["is_msft"].unique()) == {0, 1}


def test_e2e_panel_no_label_encoding(sample_4q, tmp_path):
    from aicor.config import Settings

    settings = Settings(data_dir=str(tmp_path))
    panel = run_pipeline(sample_4q, settings=settings)
    assert "company_id_int" not in panel.columns
