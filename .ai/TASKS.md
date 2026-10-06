# Tasks

## BACKLOG

None.

## READY

- AICOR-020 — Build Layer 3 Display (React Web App) consuming `data/processed/fact_quarterly.csv` and `manifest.json`. Priority: P1. Acceptance: Interactive 3-company quarterly E-score chart, In/Out breakdown, event timeline overlay, illustrative portfolio allocation tool (FR-09, FR-10), without recalculating E in React.

## IN_PROGRESS

None.

## BLOCKED

- AICOR-005 — Smoke-test installed skills in supported agents. Priority: P1. Blocked/partial: actual Claude skill invocation requires login, Codex CLI is unavailable. Acceptance: each supported agent recognizes the expected skill. Verify: harmless prompt/session discovery; see `.ai/SKILLS_REGISTRY.md`.

## DONE

- AICOR-000 — Create shared agent memory and governance files. Priority: P0. Acceptance: memory index, state, handoff, tasks, decisions, and setup evidence exist. Verify: file inventory.
- AICOR-001 — Restore project source and authoritative specification. Priority: P0. Acceptance: `PROJECT_SPEC_CMU.md` verified and read in workspace. Verify: file inspection.
- AICOR-002 — Analyze React/Python/SQLite architecture and design pipeline plan. Priority: P1. Acceptance: Comprehensive data pipeline plan created in `pipeline_crawl_clean_plan.md` using superpowers:writing-plans. Verify: verified against CMU SRS v5.1.
- AICOR-006 — Install genuine GitHub skills and Spec Kit workflow tooling. Priority: P0. Acceptance: source/path/version evidence recorded. Verify: registry and filesystem checks.
- AICOR-007 — Audit OpenCode, Freebuff, Antigravity, Gemini, VS Code, MCP, and 9Router without project-code changes. Priority: P1. Acceptance: accurate status and official capability evidence. Verify: audit report and memory files.
- AICOR-010 — Data Pipeline Foundation, Directory Scaffolding & CSV Schemas (`src/common/schemas.py`, directory setup). Priority: P0. Acceptance: Directory tree (`data/raw/`, `data/cleaned/`, `data/processed/`, `src/`, `tests/`), requirements.txt, CSV data contracts & schemas matching CMU spec. Verify: 11 tests passing.
- AICOR-011 — Implement Rate Limiter & Anti-ban Resilience Engine (`src/common/resilience.py`). Priority: P1. Acceptance: Token bucket, exponential backoff with jitter on 429/5xx, SEC EDGAR compliance. Verify: 4 tests passing.
- AICOR-012 — Implement Layer 1 Data Collectors & Append-only Raw CSV Storage (`src/collection/`). Priority: P1. Acceptance: 7 sources covered, append-only CSV writer with deduplication (FR-13) saving to `data/raw/*.csv`. Verify: 2 storage tests passing.
- AICOR-013 — Curate and build Seed Baseline Fixtures (`data/seeds/*.csv`, `src/scripts/bootstrap_seeds.py`). Priority: P1. Acceptance: Deterministic CSV data from 2022-Q1 to 2026-Q2 for all 3 companies. Verify: 159 rows bootstrapped into raw CSVs.
- AICOR-014A — Implement Layer 2 Data Cleaner & Validation (`src/cleaning/cleaner.py`). Priority: P1. Acceptance: Mandatory validation, rubric categorization, export cleaned CSVs to `data/cleaned/*.csv`. Verify: 3 tests passing, 159 cleaned rows saved.
- AICOR-014B — Implement Layer 2 Computation & Final Quarterly Fact CSV (`src/computation/`). Priority: P1. Acceptance: 4Q MA, within-company z-score with std=0 guard, E = Out - In, 3-weight sensitivity analysis, export to `data/processed/fact_quarterly.csv`. Verify: 4 tests passing, 54 quarterly facts produced.
- AICOR-015 — Configure GitHub Actions & CLI Runner for Auto-crawl (`.github/workflows/`, `run_pipeline.py`). Priority: P2. Acceptance: Fast rhythm (6h), slow rhythm (24h), SEC EDGAR trigger, local CLI. Verify: CLI test passing.




