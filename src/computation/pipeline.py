"""
AICOR Computation Pipeline Orchestrator
Coordinates Phase 6: Aggregates cleaned data, runs calculations, runs sensitivity analysis,
and persists results to:
- data/processed/fact_quarterly.csv
- data/processed/sensitivity_analysis.csv
- data/processed/manifest.json
- data/processed/sync_log.csv
"""
import csv
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from src.common.config import CLEANED_DATA_DIR, PROCESSED_DATA_DIR
from src.common.schemas import PROCESSED_SCHEMAS
from src.collection.storage import log_sync_event, get_sync_timestamp
from src.computation.aggregator import aggregate_quarterly_data
from src.computation.calculator import calculate_indices
from src.computation.sensitivity import run_sensitivity_analysis
from src.computation.db import sync_csv_to_sqlite
from src.computation.exporter import export_web_json_bundles
logger = logging.getLogger("aicor.computation.pipeline")


def run_computation_pipeline(
    cleaned_dir: Optional[Path] = None,
    processed_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Executes Layer 2 computation pipeline from cleaned CSVs to processed CSVs.
    """
    in_dir = cleaned_dir or CLEANED_DATA_DIR
    out_dir = processed_dir or PROCESSED_DATA_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Starting computation pipeline...")

    # 1. Quarterly Aggregation (Product Score = 3A + 2B + 1C, Rolling 4Q MAs)
    fact_dict = aggregate_quarterly_data(cleaned_dir=in_dir)

    # 2. Sensitivity Analysis (calculated on deep copies)
    sensitivity_rows = run_sensitivity_analysis(fact_dict)

    # 3. Baseline Index Calculation (Default weights 0.6 / 0.4)
    fact_dict = calculate_indices(fact_dict, w_product=0.6, w_trends=0.4)

    # 4. Save fact_quarterly.csv
    fact_rows = list(fact_dict.values())
    # Sort by quarter then company_id
    fact_rows.sort(key=lambda r: (r["quarter"], r["company_id"]))

    fact_file = out_dir / "fact_quarterly.csv"
    with open(fact_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=PROCESSED_SCHEMAS["fact_quarterly"])
        writer.writeheader()
        writer.writerows(fact_rows)
    logger.info(f"Wrote {len(fact_rows)} rows to {fact_file.name}.")

    # 5. Save sensitivity_analysis.csv
    sens_file = out_dir / "sensitivity_analysis.csv"
    with open(sens_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=PROCESSED_SCHEMAS["sensitivity_analysis"])
        writer.writeheader()
        writer.writerows(sensitivity_rows)
    logger.info(f"Wrote {len(sensitivity_rows)} rows to {sens_file.name}.")

    # 6. Generate manifest.json (FR-11, UC-3)
    quarters = sorted(list(set(r["quarter"] for r in fact_rows)))
    manifest_data = {
        "system": "AICOR",
        "version": "5.1",
        "last_sync_utc": get_sync_timestamp(),
        "status": "success",
        "quarters_count": len(quarters),
        "quarter_range": {
            "start": quarters[0] if quarters else "",
            "end": quarters[-1] if quarters else "",
        },
        "companies": [
            {"id": 1, "name": "Microsoft", "ticker": "MSFT"},
            {"id": 2, "name": "OpenAI", "ticker": ""},
            {"id": 3, "name": "Anthropic", "ticker": ""},
        ],
        "default_weights": {"product": 0.6, "trends": 0.4},
        "artifacts": {
            "fact_quarterly_csv": "data/processed/fact_quarterly.csv",
            "sensitivity_analysis_csv": "data/processed/sensitivity_analysis.csv",
            "sync_log_csv": "data/processed/sync_log.csv",
            "sqlite_db": "data/processed/aicor.db",
            "chart_series_json": "data/processed/chart_series.json",
            "timeline_events_json": "data/processed/timeline_events.json",
            "portfolio_baseline_json": "data/processed/portfolio_baseline.json",
        }
    }
    manifest_file = out_dir / "manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)
    logger.info(f"Updated {manifest_file.name}.")

    # 7. Sync cleaned + processed CSVs into SQLite (BE-01, FR-11/3.4)
    try:
        sqlite_counts = sync_csv_to_sqlite(out_dir / "aicor.db")
        logger.info(f"SQLite sync completed: {sqlite_counts}")
    except Exception as e:
        logger.warning(f"SQLite sync skipped/failed (keeping CSV outputs): {e}")
        sqlite_counts = {}

    # 8. Export pre-computed JSON bundles for React (BE-04, FR-14/NFR-01)
    try:
        json_bundles = export_web_json_bundles(out_dir)
        logger.info(f"JSON bundles exported: {list(json_bundles.keys())}")
    except Exception as e:
        logger.warning(f"JSON bundle export skipped/failed (keeping CSV outputs): {e}")
        json_bundles = {}

    # 9. Record sync_log.csv
    log_sync_event(
        rhythm="compute",
        status="success",
        rows_added=len(fact_rows),
        target_dir=out_dir,
    )

    return {
        "fact_rows_count": len(fact_rows),
        "sensitivity_rows_count": len(sensitivity_rows),
        "quarters": quarters,
        "manifest": manifest_data,
        "sqlite_counts": sqlite_counts,
        "json_bundles": json_bundles,
    }
