# Handoff

- Last updated: 2026-10-06
- Objective: All 5 backend extension tasks (BE-01 through BE-05) implemented, verified, and pushed.
- Branch: `main` tracking `origin/main`.
- Current phase: Phase 6 — Backend Extensions Complete (SQLite + JSON + Scrapers + EDGAR monitor + FastAPI).
- Completed:
  - BE-01 (P0): `src/computation/db.py` — 6-table SQLite engine per SRS 3.4; `sync_csv_to_sqlite()` integrated at end of `run_computation_pipeline()`; `data/processed/aicor.db` live with 54 fact_quarterly rows.
  - BE-04 (P0): `src/computation/exporter.py` — `chart_series.json`, `timeline_events.json` (33 events, date-sorted), `portfolio_baseline.json` (median E 4Q + Vietnamese disclaimer, NaN→null); pipeline-integrated.
  - BE-02 (P1): `src/collection/scrapers/blog_scraper.py` — OpenAI/Anthropic/MSFT feeds, Appendix A A/B/C keyword rubric, append-only via `storage.append_to_raw_csv()`, resilience rate-limit + retry.
  - BE-03 (P1): `src/collection/edgar_monitor.py` — SEC Atom poll for CIK 0000789019, `check_new_filings()` offline-safe, auto-sync path (EDGAR extract → clean → compute), `.github/workflows/edgar_sync.yml` weekly Monday 00:00 UTC.
  - BE-05 (P2): `src/api/main.py` + `src/api/routes.py` — `/api/health|facts|events|sensitivity|stock/msft/live` (15m latency tag, cleaned-price fallback), `/api/simulate-portfolio` (weights sum 1.0±0.001, median-E-4Q scoring), CORS `*`; `fastapi/uvicorn/httpx` added to `requirements.txt`.
  - Workflows `fast_rhythm.yml`/`slow_rhythm.yml` updated to commit `*.json` + `*.db` artifacts.
  - Verified: `pytest` 35/35 passing (20 pre-existing + 15 new); `python run_pipeline.py --mode compute` regenerates DB + JSONs; live `check_new_filings()` ran clean (False); Python 3.11 compatible (typing.Optional, no new syntax).
- Exact next action:
  - Layer 3 React Display (AICOR-020, still READY): consume `data/processed/chart_series.json`, `timeline_events.json`, `portfolio_baseline.json` + `manifest.json`; must not recalculate E (FR-14).
  - Optional: verify first `edgar_sync.yml` weekly run on GitHub Actions.
