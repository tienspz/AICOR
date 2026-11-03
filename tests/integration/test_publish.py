"""Atomic, versioned publishing (Phase 4 acceptance)."""

import json

from aicor.pipeline.publish import (
    publish_dashboard,
    read_manifest,
    verify_published,
)


def test_first_publish_creates_manifest(tmp_path):
    payload = {"meta": {"config_version": "v1", "as_of_quarter": "2026Q2"}, "series": {}}
    manifest = publish_dashboard(payload, run_id="run-1", out_dir=tmp_path)
    assert manifest["path"] == "runs/run-1.json"
    assert manifest["dataset_version"]
    assert verify_published(payload, manifest) is True
    assert read_manifest(tmp_path)["run_id"] == "run-1"


def test_manifest_points_at_the_latest_run_and_payloads_are_immutable(tmp_path):
    first = {"meta": {"config_version": "v1", "as_of_quarter": "2026Q1"}, "value": 1}
    second = {"meta": {"config_version": "v1", "as_of_quarter": "2026Q2"}, "value": 2}
    publish_dashboard(first, run_id="run-1", out_dir=tmp_path)
    first_bytes = (tmp_path / "runs" / "run-1.json").read_bytes()

    publish_dashboard(second, run_id="run-2", out_dir=tmp_path)
    assert (tmp_path / "runs" / "run-1.json").read_bytes() == first_bytes
    assert read_manifest(tmp_path)["path"] == "runs/run-2.json"
    assert read_manifest(tmp_path)["as_of_quarter"] == "2026Q2"


def test_no_manifest_before_first_publish(tmp_path):
    assert read_manifest(tmp_path) is None


def test_old_versions_are_pruned(tmp_path):
    for index in range(6):
        publish_dashboard(
            {"meta": {"config_version": "v1", "as_of_quarter": f"2025Q{index + 1}"}, "i": index},
            run_id=f"run-{index}",
            out_dir=tmp_path,
            keep_versions=2,
        )
    remaining = sorted(p.name for p in (tmp_path / "runs").glob("*.json"))
    assert len(remaining) <= 3
    assert read_manifest(tmp_path)["run_id"] == "run-5"


def test_manifest_file_is_valid_json(tmp_path):
    publish_dashboard({"meta": {"config_version": "v1"}}, run_id="run-1", out_dir=tmp_path)
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema"] == "aicor-dashboard-manifest/v1"
    assert "published_at" in manifest
