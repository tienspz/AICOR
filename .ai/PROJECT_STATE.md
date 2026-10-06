# Project state

- Phase: Phase 5 — Data Pipeline Completed (Layer 1 & Layer 2)
- Milestone: Full pipeline built, tested, and operational. All raw, cleaned, and processed datasets stored in CSV format conforming strictly to CMU SRS v5.1.
- Completed:
  - Phase 1: CSV schemas and data models (`src/common/schemas.py`, `src/common/config.py`).
  - Phase 2: Anti-ban & resilience engine (`src/common/resilience.py`, token bucket rate limiter, retry with backoff).
  - Phase 3: Layer 1 Collectors (`src/collection/`) for SEC EDGAR 10-Q, Google Trends, Yahoo Finance, product launches, funding, relationships, and append-only CSV writer (`storage.py`).
  - Phase 4: Baseline historical seeds (2022-Q1 to 2026-Q2) generated in `data/seeds/` and bootstrapped into `data/raw/*.csv` (159 records).
  - Phase 5: Layer 2 Cleaner & Validator (`src/cleaning/cleaner.py`), 159 valid records cleaned and exported to `data/cleaned/*.csv`.
  - Phase 6: Layer 2 Computation Engine (`src/computation/`), within-company z-score normalization, rolling 4Q moving averages, $E = Out - In$, 3-weight sensitivity analysis, exported to `data/processed/fact_quarterly.csv`, `sensitivity_analysis.csv`, and `manifest.json` (54 quarterly facts).
  - Phase 7: Unified CLI runner (`run_pipeline.py`) and GitHub Actions workflows (`fast_rhythm.yml`, `slow_rhythm.yml`).
  - Test suite: 20/20 pytest unit tests passing.
- In progress: Ready for Layer 3 (React Web App / Display) if requested.
- Pending: React UI implementation consuming `data/processed/fact_quarterly.csv`.
- Known issues: workspace is not a Git repository.
- Last verified checks: 20 pytest unit tests passing; CLI clean and compute modes verified; `data/processed/fact_quarterly.csv` and `data/processed/manifest.json` generated and verified.
- Architecture status: Layer 1 (Collection) and Layer 2 (Computation) are fully implemented, verified, and operational.


