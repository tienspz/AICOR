"""Contract tests for the published analysis artifacts (SPEC §3.10, §3.11)."""

import json

import pandas as pd

from aicor.compute.config import load_analysis_config
from aicor.compute.engine import compute_analysis
from aicor.compute.features import build_feature_matrix, to_long_features
from aicor.pipeline.artifacts import write_analysis_artifacts
from tests.conftest import build_panel, build_products, build_trends

ALLOWED_STATUS = {
    "ok",
    "unavailable",
    "insufficient_window",
    "insufficient_observations",
    "degenerate",
    "insufficient_ma4q_quarters",
}


def _artifacts(tmp_path):
    cfg = load_analysis_config()
    features = build_feature_matrix(build_panel(), build_products(), build_trends(), config=cfg)
    manifest = write_analysis_artifacts(
        features_long=to_long_features(features, cfg),
        analysis=compute_analysis(features, cfg),
        provenance=pd.DataFrame(
            columns=[
                "source_id",
                "company",
                "period_end_date",
                "source_url",
                "filing_date",
                "accession_number",
                "form",
                "source_tier",
                "verification_status",
            ]
        ),
        out_dir=tmp_path,
        config=cfg,
    )
    return cfg, manifest, tmp_path


def test_analysis_results_schema(tmp_path):
    _, _, out = _artifacts(tmp_path)
    df = pd.read_csv(out / "analysis_results.csv")
    required = {
        "analysis_id",
        "company",
        "period_end_date",
        "calendar_quarter",
        "analysis_type",
        "metric",
        "scenario",
        "value",
        "method",
        "confidence",
        "config_version",
        "formula_version",
        "status",
        "reason",
        "n_observations",
        "feature_ids",
        "source_id",
        "source_url",
        "result_class",
    }
    assert required.issubset(set(df.columns))
    assert set(df["metric"]) == {"In", "Out", "E"}
    assert set(df["scenario"]) == {"baseline", "simple", "tech"}
    assert set(df["status"]) <= ALLOWED_STATUS


def test_features_quarterly_schema(tmp_path):
    _, _, out = _artifacts(tmp_path)
    df = pd.read_csv(out / "features_quarterly.csv")
    assert set(df["status"]) <= ALLOWED_STATUS
    assert df["feature_id"].is_unique
    assert df["feature_id"].notna().all()


def test_null_values_have_reasons_and_are_not_zero(tmp_path):
    _, _, out = _artifacts(tmp_path)
    df = pd.read_csv(out / "analysis_results.csv")
    nulls = df[df["value"].isna()]
    assert len(nulls) > 0, "early quarters must be NULL rather than invented"
    assert nulls["reason"].fillna("").str.len().gt(0).all()
    assert not (df["value"] == 0).any(), "E must never be silently replaced by zero"


def test_manifest_hashes_match_files(tmp_path):
    _, manifest, out = _artifacts(tmp_path)
    assert set(manifest["artifacts"]) == {
        "features_quarterly.csv",
        "analysis_results.csv",
        "provenance.csv",
    }
    on_disk = json.loads((out / "analysis_manifest.json").read_text(encoding="utf-8"))
    assert on_disk["artifacts"] == manifest["artifacts"]
    assert on_disk["row_counts"]["analysis_results"] > 0


def test_artifacts_are_byte_identical_across_runs(tmp_path):
    _, first, out_a = _artifacts(tmp_path / "a")
    _, second, out_b = _artifacts(tmp_path / "b")
    assert first["artifacts"] == second["artifacts"]
    assert (out_a / "analysis_results.csv").read_bytes() == (out_b / "analysis_results.csv").read_bytes()
