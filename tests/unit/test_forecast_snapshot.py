"""Point-in-time guard and sample construction (FCST-02, NFR-09)."""

import pandas as pd
import pytest

from aicor.compute.config import load_analysis_config
from aicor.forecast.snapshot import (
    FEATURE_COLUMNS,
    PointInTimeError,
    assert_point_in_time,
    build_samples,
    build_snapshot,
    index_to_quarter,
    quarter_to_index,
    target_quarter,
)


def test_quarter_helpers_are_inverse():
    assert target_quarter("2026Q2", 0) == "2026Q3"
    assert target_quarter("2026Q2", 1) == "2026Q4"
    assert index_to_quarter(quarter_to_index("2025Q1")) == "2025Q1"


def test_samples_targets_are_strictly_after_origin(series_frame_fixture):
    samples = build_samples(series_frame_fixture, config=load_analysis_config())
    assert not samples.empty
    assert (samples["target_index"] > samples["origin_index"]).all()
    assert (samples["target_index"] - samples["origin_index"]).isin([1, 2]).all()


def test_sample_features_come_from_origin_only(series_frame_fixture):
    samples = build_samples(series_frame_fixture, config=load_analysis_config())
    series = series_frame_fixture
    for _, sample in samples.iterrows():
        origin = series[
            (series["company"] == sample["company"]) & (series["calendar_quarter"] == sample["origin_quarter"])
        ].iloc[0]
        target = series[
            (series["company"] == sample["company"]) & (series["calendar_quarter"] == sample["target_quarter"])
        ].iloc[0]
        assert sample["e_lag1"] == pytest.approx(origin["E"])
        assert sample["out_lag1"] == pytest.approx(origin["Out"])
        assert sample["target"] == pytest.approx(target["E"])
        # Feature availability must never post-date the target's own publication
        # and must be the origin's publication date.
        assert sample["feature_available_at"] == origin["available_at"]
        assert sample["feature_available_at"] <= sample["target_available_at"]


def test_feature_columns_are_bounded():
    from aicor.forecast.pulse import MODEL_ID  # noqa: F401  (import sanity)

    assert len(FEATURE_COLUMNS) <= 10


def test_point_in_time_guard_rejects_future_features():
    frame = pd.DataFrame(
        [{"sample_id": "MSFT-2026Q2-h1", "feature_available_at": "2026-08-01"}]
    )
    with pytest.raises(PointInTimeError):
        assert_point_in_time(frame, "2026-07-01")


def test_point_in_time_guard_allows_earlier_features():
    frame = pd.DataFrame([{"sample_id": "x", "feature_available_at": "2026-06-01"}])
    assert_point_in_time(frame, "2026-07-01")  # must not raise


def test_snapshot_uses_latest_origin_and_no_future_rows(series_frame_fixture):
    snapshot = build_snapshot(series_frame_fixture, config=load_analysis_config())
    assert snapshot.rows["origin_quarter"].nunique() == 1
    assert snapshot.max_feature_available_at <= snapshot.as_of_date
    assert snapshot.vintage_id


def test_snapshot_rejects_an_earlier_as_of(series_frame_fixture):
    with pytest.raises(PointInTimeError):
        build_snapshot(series_frame_fixture, config=load_analysis_config(), as_of_date="2021-01-01")
