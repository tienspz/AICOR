# ADR-0006 · Research parameters are versioned config, not code — and not invented

- **Status:** Accepted
- **Date:** 2026-10-13
- **Deciders:** Agent 0
- **Affects:** T-05, T-16…T-19, EFF-01, EFF-02, SEN-01, ROB-01, REG-01, SCN-01…03, IO-02
- **Addresses:** `open_decisions.md` OD-02, OD-03, OD-04, OD-05, OD-12

## Context

The SRS leaves a specific and consequential set of research parameters undefined. Its own Appendix B marks them open, and the dispatch brief states the rule explicitly: *"Do not invent arbitrary weights without documenting and obtaining approval for research assumptions."*

The undefined set:

| Parameter | Needed by | Note |
|---|---|---|
| `Resource Growth` definition | FE-05, FE-06, FE-07, EFF-01, REG-01 | **Not defined anywhere** — the efficiency denominator itself |
| `normalization_method` | EFF-02 | Weights given (0.30/0.30/0.25/0.15) but components are incommensurable — ratios of growth rates vs. an abnormal *return* in percent |
| `composite_score` formula | DEC-01 | A *different* four-part composite, including a risk component EFF-02 lacks; no formula at all |
| SEN-01 weight sets | SEN-01, ROB-01 | Named (`Baseline`…`Risk-heavy`) with no numbers |
| Regime thresholds | REG-01 | Four regimes, no decision table; and the name `Efficiency` collides with the EFF-01 measure group |
| Estimation method | IO-02 | No method named |
| Scenario propagation | SCN-01…03 | Shocks are specified; how they propagate is not |

The temptation is concrete. Each value is a single number in a config file. Writing `0.5` looks like progress, builds no error, and produces a dashboard. But those numbers *are* the research methodology — the weights in EFF-02 decide which company's efficiency is declared higher, and the normalisation method decides whether MSFT's larger magnitudes dominate the comparison. Silently choosing them would put **unattributed invented methodology** at the centre of the project's headline answer.

## Decision

**Research parameters live in `config/research_params.yaml`, versioned, and cannot be invented.**

1. **Single location.** No research parameter is ever a code literal (architecture invariant I-6).
2. **Every result row carries `config_version`** (NFR-03), so a conclusion can always be traced to the parameter set that produced it.
3. **`pending_approval: true` gate.** Agent 2 may add a parameter to make structure runnable, but only Agent 0 may promote it. This makes an unresolved research decision *visible in the data* rather than hidden in a diff.
4. **Blocked modules ship as structure with NULL values** plus `reason='pending_decision:<OD-id>'`. They are never filled with plausible defaults.
5. **Escalate, do not assume.** Each undefined parameter is raised in `open_decisions.md` with options, consequences, and a stated recommendation — so the author can approve or overrule in one line rather than reverse-engineer the intent.

## Alternatives considered

| Option | Why rejected |
|---|---|
| Pick defensible defaults and document them afterwards | Produces a working system whose methodology was chosen by an implementer, not a researcher. The documentation is an apology, not a justification |
| Compute only what is unambiguous and silently drop the rest | Drops 14 of 62 requirements with no visible trace. Explicit NULLs + reasons is honest; silence is not |
| Ask the author for every parameter up front | Blocks all 62 requirements on 7 answers, when 48 are independently buildable now. The unblocked data spine must not wait on methodology |
| Hard-code parameters with a comment explaining the choice | Violates I-6 and NFR-03: parameter changes then lack version history, so post-hoc tuning after seeing results becomes undetectable — the precise failure mode that erodes a research claim |

## Consequences

**Positive**
- No fabricated methodology can reach a dashboard; a missing decision is a visible NULL, not a plausible number.
- Every conclusion is traceable to an approved, versioned parameter set.
- The data spine (SEC ingestion → derivation → quality → features) proceeds in parallel with the research decisions, so the long pole is not artificially extended.
- Parameter history under git makes post-hoc tuning reviewable — which is how a reader can verify the numbers were not chosen after seeing the outcome.

**Negative**
- 14 of 62 requirements ship incomplete until OD-01…OD-06 and OD-12 are answered. This is the intended trade and is stated in `srs_traceability_matrix.md` §18.
- The `pending_approval` gate adds a workflow step.
- Some dashboards (05 Efficiency, 07 Regimes, 08 Scenarios) will render partially empty on first run, with each empty cell explaining which decision is blocking it. This is the correct behaviour, and it is far preferable to a plausible-looking fabricated number.

## Verification

The gate is enforced structurally: `EFF_T02` asserts `weight_version`, `weights` and `normalization_method` are persisted; `SCN_T04` asserts effects requiring an invented elasticity are NULL + reason; `API_T05` makes `decision.limitations` non-nullable. Stage 6 audits that no unapproved parameter reached a stored result.