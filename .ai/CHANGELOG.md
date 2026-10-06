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



