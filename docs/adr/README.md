# AICOR — Architecture Decision Records

Numbered ADRs for decisions that are expensive to reverse, would otherwise be re-litigated, or that constrain future contributors.

| ADR | Title | Status | Date | Decider |
|---|---|---|---|---|
| [0001](0001-technology-stack.md) | Technology stack | Accepted | 2026-10-13 | Research author |
| [0002](0002-version-control-for-provenance.md) | Version control as the substrate for provenance | Accepted | 2026-10-13 | Research author |
| [0003](0003-api-first-sec-ingestion.md) | API-first SEC ingestion over HTML scraping | Accepted | 2026-10-13 | Agent 0 |
| [0004](0004-period-aware-tag-resolution.md) | Period-aware XBRL tag resolution, failing loudly | Accepted | 2026-10-13 | Agent 0 |
| [0005](0005-cumulative-to-quarterly-derivation.md) | Cumulative-to-quarterly derivation, uniform for both companies | Accepted | 2026-10-13 | Agent 0 |
| [0006](0006-research-parameters-are-config-not-code.md) | Research parameters are versioned config, not code — and not invented | Accepted | 2026-10-13 | Agent 0 |

## Format

Each ADR records **Context → Decision → Alternatives considered → Consequences**. Context carries the evidence that made the decision necessary; Consequences are recorded in both directions, because a decision whose costs are not written down is a decision that will be second-guessed without information.

## Status values

`Proposed` · `Accepted` · `Superseded by ADR-NNNN` · `Deprecated`

## When to write a new ADR

- A choice that would be expensive to reverse (stack, database, ingestion strategy, join semantics).
- A choice that conflicts with an existing convention or with injected tooling guidance (see 0001 vs. the harness's Node/Express instructions).
- A constraint discovered from evidence rather than preference (0004, 0005 both originate from measured SEC data).
- A decision that separates observed fact from research assumption (0006).

Research methodology questions are **not** ADRs on their own — they live in `../planning/open_decisions.md` and only become ADRs once the author decides. ADR-0006 exists precisely to keep that boundary from eroding.

## Index of planning documents

| Document | Purpose |
|---|---|
| `../planning/repository_audit.md` | What the repository actually contained; defects found and fixed |
| `../planning/installed_skills_audit.md` | Skills on disk, their roles, and the conflicts between them |
| `../planning/srs_traceability_matrix.md` | All 62 coded requirements with status, acceptance test, and blockers (14 blocked) |
| `../planning/open_decisions.md` | 15 decisions: 7 research (6 blocking + 1 administrative), 8 engineering (proceeding) |
| `../planning/system_architecture.md` | Twelve layers, invariants, data flow, dependency graph |
| `../planning/data_dictionary_and_provenance.md` | Tables, the 12 PRV-01 fields, tag registry, derivation rules |
| `../planning/api_contracts.md` | Endpoints, envelope, null semantics, endpoint→requirement map |
| `../planning/multi_agent_work_plan.md` | 22 tasks, ownership, shared-file conflicts, sequence |
| `../planning/implementation_roadmap.md` | 8 stages, gates, critical path, rollback |
| `../planning/test_and_acceptance_plan.md` | TEST-ID register and the four acceptance gates |
| `../planning/risk_register.md` | 22 scored risks, each with observed evidence |