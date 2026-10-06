"""
AICOR Main Pipeline Orchestrator CLI
Unified command-line interface to run crawling, cleaning, computation, or full sync.
Usage:
  python run_pipeline.py --mode seed
  python run_pipeline.py --mode crawl --rhythm fast
  python run_pipeline.py --mode crawl --rhythm slow
  python run_pipeline.py --mode clean
  python run_pipeline.py --mode compute
  python run_pipeline.py --mode full
"""
import sys
import argparse
import logging
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.common.config import RAW_DATA_DIR, CLEANED_DATA_DIR, PROCESSED_DATA_DIR
from src.scripts.bootstrap_seeds import bootstrap_raw_data_from_seeds
from src.cleaning.cleaner import run_data_cleaner
from src.computation.pipeline import run_computation_pipeline
from src.collection.collector_stock import run_stock_collector
from src.collection.collector_trends import run_trends_collector
from src.collection.collector_edgar import run_edgar_collector
from src.collection.storage import log_sync_event

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("aicor.cli")


def run_crawlers(rhythm: str = "all") -> int:
    """Executes collectors based on rhythm: fast (6h), slow (24h), edgar, or all."""
    logger.info(f"Executing crawlers for rhythm='{rhythm}'...")
    total_added = 0

    if rhythm in ("fast", "all"):
        logger.info("--- Running Fast Rhythm Collectors (Stock, Google Trends) ---")
        try:
            total_added += run_stock_collector()
        except Exception as e:
            logger.error(f"Error in stock collector: {e}")
            log_sync_event("fast", "failed", error=str(e))

        try:
            total_added += run_trends_collector()
        except Exception as e:
            logger.error(f"Error in trends collector: {e}")
            log_sync_event("fast", "failed", error=str(e))

    if rhythm in ("edgar", "all"):
        logger.info("--- Running SEC EDGAR 10-Q Collector ---")
        try:
            total_added += run_edgar_collector()
        except Exception as e:
            logger.error(f"Error in EDGAR collector: {e}")
            log_sync_event("edgar", "failed", error=str(e))

    if rhythm in ("slow", "all"):
        logger.info("--- Running Slow Rhythm (Daily updates) ---")
        # Ensure raw directory is bootstrapped if empty
        if not (RAW_DATA_DIR / "events_launch_raw.csv").exists():
            bootstrap_raw_data_from_seeds()

    logger.info(f"Crawlers completed. Total {total_added} new records appended to raw CSVs.")
    return total_added


def main():
    parser = argparse.ArgumentParser(description="AICOR End-to-End Data Pipeline CLI")
    parser.add_argument(
        "--mode",
        choices=["seed", "crawl", "clean", "compute", "full"],
        default="full",
        help="Pipeline mode to execute: seed, crawl, clean, compute, or full",
    )
    parser.add_argument(
        "--rhythm",
        choices=["fast", "slow", "edgar", "all"],
        default="all",
        help="Crawling rhythm: fast (6h), slow (24h), edgar (10-Q), or all",
    )
    args = parser.parse_args()

    logger.info(f"=== Starting AICOR Pipeline [mode={args.mode}, rhythm={args.rhythm}] ===")

    if args.mode == "seed":
        bootstrap_raw_data_from_seeds()

    elif args.mode == "crawl":
        run_crawlers(rhythm=args.rhythm)

    elif args.mode == "clean":
        run_data_cleaner()

    elif args.mode == "compute":
        run_computation_pipeline()

    elif args.mode == "full":
        # 1. Bootstrap seeds if raw is empty
        if not (RAW_DATA_DIR / "rnd_msft_raw.csv").exists():
            logger.info("Raw data directory empty. Bootstrapping baseline seeds...")
            bootstrap_raw_data_from_seeds()

        # 2. Run crawlers to fetch recent incremental points
        run_crawlers(rhythm=args.rhythm)

        # 3. Clean raw CSVs into data/cleaned/*.csv
        logger.info("--- Cleaning & Validating Raw Data ---")
        clean_res = run_data_cleaner()

        # 4. Run Computation Pipeline into data/processed/fact_quarterly.csv
        logger.info("--- Running Layer 2 Computation Engine ---")
        comp_res = run_computation_pipeline()

        logger.info("=== Full Pipeline Completed Successfully ===")
        logger.info(f"Processed {comp_res['fact_rows_count']} quarterly fact records.")
        logger.info(f"Quarters covered: {comp_res['quarters'][0]} to {comp_res['quarters'][-1]}")
        logger.info("Outputs:")
        logger.info("  - data/raw/*.csv")
        logger.info("  - data/cleaned/*.csv")
        logger.info("  - data/processed/fact_quarterly.csv")
        logger.info("  - data/processed/sensitivity_analysis.csv")
        logger.info("  - data/processed/sync_log.csv")
        logger.info("  - data/processed/manifest.json")


if __name__ == "__main__":
    main()
