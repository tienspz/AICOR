# ADR-0001 · Technology stack

- **Status:** Accepted
- **Date:** 2026-10-13
- **Deciders:** research author (approved)
- **Affects:** all tasks

## Context

The SRS specifies requirements, data sources and a conceptual architecture (§8), but **never names a language, framework, database, or package manager**. Repository discovery confirmed this is a genuine gap rather than a discovery failure: the repository is greenfield, containing only `SPEC.md`, `VIBECODE_SETUP.md` and the assistant harness.

So there is no "existing technology" to remain compatible with, and the stack is a decision rather than a constraint.

The workload is: XBRL parsing and arithmetic, cross-company quarterly accounting, statistics on a ~42-row panel, a read-only API, and a 9-page dashboard.

Two additional forces:

1. The harness injects `backend-patterns`, `frontend-patterns` and `api-design` as **standing instructions**, all defaulting to a Node/Express/Next.js stack.
2. Local toolchain: Python 3.14.7, Node v24.14.0, `uv`, `git`. No `psql`, no `pnpm`, no DuckDB.

## Decision

**Python 3.14 + FastAPI + PostgreSQL + Next.js.**

| Layer | Choice | Rationale |
|---|---|---|
| Language | Python 3.14 | XBRL/XBRL-JSON, numeric work and statistics are native; `uv` gives pinned, reproducible environments |
| API | FastAPI + Pydantic v2 | Native Pydantic schema reuse → machine-checkable contracts (`contract-first`) |
| Database | PostgreSQL | PRV-01 needs a real relational provenance model with FK integrity across `source_registry` → features → analysis. DuckDB was considered and rejected (weaker FK enforcement, poor concurrent-write fit for parallel ingestion) |
| Frontend | Next.js + React | 9 pages, server rendering, mature charting; and it is the one place where the injected `frontend-patterns` guidance is correct |

**Tooling:** `uv` for Python; npm for Node; PostgreSQL via `docker-compose.yml`.

## Alternatives considered

| Option | Why rejected |
|---|---|
| DuckDB instead of Postgres | Faster for a 42-row dataset, but PRV-01's provenance spine depends on FK integrity, and parallel ingestion would contend for a single writer |
| Streamlit, single app | Fastest to the slice, but conflicts with DSH-01's read-only-from-database contract and with the Agent 3/4 split |
| All-TypeScript (Node API + Next.js) | Avoids a polyglot repo, but is a materially weaker fit for XBRL parsing and statistics |
| Django | Batteries-included, but heavier than needed; FastAPI's schema-first contract generation is the higher-value property here |

## Consequences

**Positive**
- `contract-first` is genuinely satisfiable — one Pydantic/OpenAPI source of truth.
- The analytics stack matches the SRS's own emphasis on reproducibility (`uv.lock` + versioned config).
- The Node-framework bias of the injected instructions is neutralised for the backend while remaining useful for the frontend.

**Negative**
- Polyglot repo (Python + TypeScript) — two dependency trees, two test runners.
- PostgreSQL must be provisioned; it is not currently installed locally.
- **The injected `backend-patterns` instructions are overridden for the backend.** This is a deliberate, recorded departure and must be re-stated to any agent that later touches backend code, or it will drift back toward Express.

## Compliance note

This ADR resolves the SRS's silence. It does **not** resolve any research question; `open_decisions.md` OD-01…OD-06 and OD-12 remain open.