# Changelog

## 2026-10-04

- Added shared agent instructions and project-local memory files.
- Recorded Windows tool discovery and integration limitations.
- Confirmed no source code or business logic was changed.

## 2026-10-04 — GitHub skills

- Installed three Vercel Agent Skills, two OpenAI/Codex skills, Superpowers for Claude Code, and Spec Kit CLI.
- Updated registries with source commits, paths, hashes, agents, and verification status.
- Recorded unsupported or unverified runtimes without creating guessed configuration.

## 2026-10-04 — Phase 2 audit

- Corrected environment discovery to include locally installed OpenCode, Freebuff, and Antigravity desktop products.
- Added runtime classifications, official capability references, skill compatibility matrix, and MCP audit.
- Recorded OpenCode log permission, Antigravity custom skill path, Gemini PowerShell, Codex CLI, and 9Router limitations.

## 2026-10-05 — Phase 3 read-only validation

- Verified all five requested `SKILL.md` files and their local paths; recorded Vercel metadata versions and noted that local source commit IDs are unavailable.
- Confirmed Claude Code lists Superpowers `6.4.2` as enabled. A read-only Claude skill invocation was blocked because the CLI is not logged in; no login was attempted.
- Verified OpenCode embedded CLI `2.0.14` and Spec Kit `1.1.1.dev0` using harmless version/help commands. The earlier OpenCode logging-permission blocker did not reproduce.
- Confirmed Antigravity `2.19.1` / IDE `2.5.5`, missing documented custom skill directory, and MCP config presence without exposing values.
- Confirmed Freebuff Desktop `0.0.158` and clarified its agent-runtime role; recorded 9Router as an API/model router, not a skill runtime.
- Updated skills, environment, MCP, and handoff records. No source, skill files, configuration, permissions, credentials, or dependency manifests were changed.

## 2026-10-06 — Phase 4 Data Pipeline Planning (CMU SRS v5.1)

- Read and verified authoritative `PROJECT_SPEC_CMU.md` (41.5 KB, 1,142 lines).
- Analyzed all functional requirements (FR-01 to FR-14), data dictionary schemas (section 3.4), and Appendices A through F.
- Applied `obra/superpowers` workflow (`brainstorming` & `writing-plans`) to clarify user requirements: full pipeline (Layer 1 Collection + Layer 2 Computation), automated scheduler with anti-ban rate limiting, deterministic baseline seed fixtures + incremental crawler.
- Created comprehensive implementation plan artifact `pipeline_crawl_clean_plan.md` broken down into 6 actionable phases with TDD verification criteria.
- Updated `.ai/PROJECT_STATE.md`, `.ai/TASKS.md`, and `.ai/HANDOFF.md`.

## 2026-10-06 — Phase 5 Data Pipeline Implementation & Verification (All Data in CSV)

- Created directory scaffolding: `data/raw/`, `data/cleaned/`, `data/processed/`, `data/seeds/`, `src/common/`, `src/collection/`, `src/cleaning/`, `src/computation/`, `src/scripts/`, `tests/`.
- Implemented `src/common/config.py` and `src/common/schemas.py` with validation and date-to-quarter conversion.
- Implemented `src/common/resilience.py`: Token bucket rate limiting (SEC EDGAR compliant, Google Trends delays), exponential backoff with jitter on HTTP 429/5xx.
- Implemented `src/collection/storage.py`: Append-only CSV storage with natural key deduplication (FR-13) and `sync_log.csv` recorder.
- Implemented Collectors: `collector_edgar.py` (SEC 10-Q), `collector_stock.py` (Yahoo Finance MSFT), `collector_trends.py` (Google Trends), `collector_events.py` (launches A/B/C rubric, funding, relationships, spend estimates).
- Generated baseline seed fixtures (`data/seeds/*.csv`) and bootstrapped 159 rows into `data/raw/*.csv` (2022-Q1 to 2026-Q2).
- Implemented `src/cleaning/cleaner.py`: Cleaned and exported 159 records to `data/cleaned/*.csv`.
- Implemented `src/computation/`: `aggregator.py` (Product score = 3A+2B+1C, rolling 4Q MAs), `calculator.py` (within-company z-score with std=0 guard, $E = Out - In$), `sensitivity.py` (3 weight presets evaluation), `pipeline.py` (exported 54 records to `data/processed/fact_quarterly.csv`, `sensitivity_analysis.csv`, and `manifest.json`).
- Implemented unified CLI `run_pipeline.py` and GitHub Actions workflows (`fast_rhythm.yml`, `slow_rhythm.yml`).
- Tested with 20/20 passing pytest unit tests.
- Fixed missing `Optional` import in `src/cleaning/cleaner.py` and `src/computation/aggregator.py` for Python 3.11 compatibility on GitHub Actions.
- Formulated `BACKEND_EXTENSION_PLAN.md` detailing 5 extension tasks (BE-01 SQLite Engine, BE-02 Blog Scraper, BE-03 EDGAR Monitor, BE-04 JSON Bundles Exporter, BE-05 FastAPI Service) and ready-to-use prompts for OpenCode and Freebuff.

## 2026-10-06 — Phase 6 Backend Extensions Implementation (BE-01 through BE-05)

- Implemented BE-01: `src/computation/db.py` (6 tables per SRS 3.4, `init_database`, `populate_dim_companies`, `sync_csv_to_sqlite` with INSERT OR REPLACE facts + idempotent event resync) and wired into `run_computation_pipeline()`; live `data/processed/aicor.db` holds 54 fact_quarterly rows.
- Implemented BE-04: `src/computation/exporter.py` (`chart_series.json` MSFT/OpenAI/Anthropic series, `timeline_events.json` 33 date-sorted events, `portfolio_baseline.json` median-E-4Q + "minh hoa, khong phai khuyen nghi dau tu" disclaimer, NaN→null) and wired into pipeline.
- Implemented BE-02: `src/collection/scrapers/blog_scraper.py` (OpenAI/Anthropic/Microsoft feeds, Appendix A keyword rubric, AI filter for MSFT feed, resilience rate-limit + retry, append-only storage) with mock-feed tests.
- Implemented BE-03: `src/collection/edgar_monitor.py` (SEC Atom poll CIK 0000789019, `check_new_filings()` offline-safe, auto-sync EDGAR→clean→compute, `log_sync_event` rhythm edgar) + `.github/workflows/edgar_sync.yml` (weekly Mon 00:00 UTC); live check ran clean.
- Implemented BE-05: `src/api/main.py` + `src/api/routes.py` (health/facts/events/sensitivity/stock-msft-live with 15m latency tag and cleaned-price fallback/simulate-portfolio sum=1.0±0.001 median-E scoring, CORS *); added `fastapi/uvicorn/httpx` to `requirements.txt`.
- Updated `fast_rhythm.yml`/`slow_rhythm.yml` to commit `*.json` + `*.db` artifacts; extended pipeline manifest artifacts and CLI output listing.
- Verified: `pytest` 35/35 passing (20 pre-existing + 15 new: test_db 3, test_exporter 1, test_scrapers 3, test_edgar_monitor 3, test_api 5); Python 3.11 compatible (typing.Optional, stdlib XML, no new syntax); math logic untouched (E = Out − In, within-company z, std=0→0).
- Updated `.ai/TASKS.md` (BE tasks → DONE, AICOR-020 React remains READY), `.ai/HANDOFF.md`, `.ai/PROJECT_STATE.md`.

## 2026-10-06 — Phase 7 Layer 3 React Display (AICOR-020)

- Scaffolded `frontend/` manually (deterministic, no interactive `npm create`): Vite 6 + React 19 + TS + Tailwind v4 + Recharts + lucide-react; `npm install` clean (122 packages, 0 vulnerabilities).
- Implemented `src/types/aicor.ts` (bundle contracts matching exporter output), `src/services/dataService.ts` (static-JSON default + FastAPI live-stock fallback with 4s abort, money/score formatters), and 8 components: Header, MetricCards, EChartViewer, InOutBreakdownChart, RawMetricsChart, TimelineViewer, PortfolioSimulator, MethodologyModal, Footer, plus `App.tsx` tab layout.
- Kept invariants: FR-14 (verbatim JSON values; portfolio uses precomputed medians only), FR-09/FR-10 (100%-locked sliders + amber disclaimer), FR-12 (15-minute latency label), Vietnamese UI, no ROI/causality wording.
- Added `scripts/sync-data.mjs` + `prebuild` hook, `base './'` portable build, `public/.nojekyll`, `frontend/README.md`; `.gitignore` covers `frontend/node_modules/` + `frontend/dist/`; committed `public/data/*.json` so the app runs standalone.
- Verified: `tsc -b` clean, `vite build` success in 11.3s, `vite preview` smoke test HTTP 200 on `/`, `/data/manifest.json`, `/data/chart_series.json`; backend `pytest` still 35/35 (untouched).
- Updated `.ai/TASKS.md` (AICOR-020 → DONE, READY empty), `.ai/HANDOFF.md`, `.ai/PROJECT_STATE.md`.



