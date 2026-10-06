# AICOR shared agent instructions

This file is the canonical project entry point for coding agents.

## Start of session

Read `.ai/MEMORY_INDEX.md` and `.ai/PROJECT_STATE.md`, then read `.ai/HANDOFF.md`, the relevant task in `.ai/TASKS.md`, and the authoritative `PROJECT_SPEC_CMU.md` when it exists. Inspect Git status before editing.

## Scope and source of truth

Do not change business logic, formulas, database structure, or project scope during environment setup. Treat `PROJECT_SPEC_CMU.md` as authoritative. Preserve raw data and append-only history. Never fabricate data, credentials, model availability, test results, or integration support.

`E = Out - In` is an outcome difference, not ROI or profit and does not prove causality. Z-scores are calculated within each company's historical series. React consumes precomputed results and must not recalculate `E`.

## Security and quality

Never print or commit secrets. Use environment variables or official secret stores. Prefer small, reviewable changes, explicit provenance, validation, and reproducible commands. Record meaningful decisions and actual verification results in `.ai/`.

## End of session

Update `.ai/HANDOFF.md`, `.ai/PROJECT_STATE.md`, `.ai/TASKS.md`, and `.ai/CHANGELOG.md` when appropriate. State exactly what was verified and the next action.
