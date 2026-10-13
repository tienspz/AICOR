# ADR-0005 · Cumulative-to-quarterly derivation, uniform for both companies

- **Status:** Accepted
- **Date:** 2026-10-13
- **Deciders:** Agent 0
- **Affects:** T-13, DQ-03, FR-03, FR-05
- **Addresses:** `open_decisions.md` OD-13 · SRS §4.3.1, DQ-03

## Context

US GAAP cash-flow and income statements are cumulative from the fiscal-year start: a Q2 10-Q shows three- and six-month columns, a Q3 shows three-, six- and nine-month. Q4 is never separately reported, because **no 10-Q is filed for the fourth quarter of any fiscal year**.

Phase 1 measured how this actually affects the two study companies — the count of directly-reported 3-month cash-flow duration facts within the 2021-06-30 → 2026-06-30 window:

| Company | CapEx | CFO | R&D |
|---|---:|---:|---:|
| MSFT | 14 | 14 | 14 |
| **GOOGL** | **5** | **5** | 14 |

Alphabet's cash-flow statements are essentially cumulative-only. Additionally, across **both** companies the latest 3-month fact ends at `2026-03-31`, while `2026-06-30` appears **only as a full-year duration**.

So the two companies differ substantially in whether a direct quarterly figure exists, and neither offers one for Q4.

## Decision

**Implement one cumulative-to-standalone-quarter derivation, used for both companies. Use MSFT's directly-reported figures as an independent cross-check, never as the primary path.**

| Fiscal quarter | Derivation | Required durations |
|---|---|---|
| Q1 | `= 3M` | 3M |
| Q2 | `= 6M − 3M` | 6M, 3M |
| Q3 | `= 9M − 6M` | 9M, 6M |
| **Q4** | **`= FY − 9M`** | FY, 9M |

Supporting rules:

1. Every fact carries `period_basis ∈ {3M, 6M, 9M, FY, instant}` — the field DQ-03 polices.
2. Where a directly-reported 3-month fact exists, compare it against the derived value. Agreement within tolerance → proceed. **Disagreement → `data_quality_log` at severity ERROR; the row is kept and flagged, never silently accepted.**
3. Q4 is never populated from a 3-month fact, because none exists.
4. Sign normalisation (CapEx → positive) happens **before** derivation, so the algebra is signed consistently.

## Alternatives considered

| Option | Why rejected |
|---|---|
| Use direct 3-month facts where present, derive otherwise | Two code paths, each correct for only one company; the branch condition becomes an invisible source of per-company inconsistency, and it cannot cover Q4 for either company |
| Derive for Alphabet, use direct facts for MSFT | Makes the two companies methodologically different, which undermines the comparison the whole project exists to make |
| Use annual and 9-month figures without deriving Q4 | Loses 5 of 21 quarters per company — fails the 16–20 quarter requirement |
| Trust the annual figure as Q4 | Would substitute an annual total for a quarter and inflate Q4 — a silent, severe accounting error |

## Consequences

**Positive**
- One correct path for both companies, so cross-company comparison rests on a single method.
- Q4 exists for every year, giving the full 21 quarters.
- MSFT's direct facts provide a genuine independent check on the derivation — a self-validating pipeline rather than a self-consistent one.
- `period_basis` makes DQ-03 testable instead of aspirational.

**Negative**
- The derivation is error-prone by hand; it demands unit tests on all four formulas including the FY−9M case, and a test proving Q4 is never sourced from a 3-month fact.
- MSFT fiscal quarters run July–June, so its "Q1" is Jul–Sep; a fiscal-boundary test is required, not optional.
- A derived value is no longer a *reported* value. Per SRS §1.4 and AI-02 semantics, derived quarters must be labelled `derived`, not `reported` — otherwise the system overstates its own directness.

## Verification

`DER_T01`–`DER_T04` (each formula), `DER_T05` (Q4 never reads a 3-month fact), `DER_T06` (MSFT's 14 direct quarters agree), `DER_T07` (`period_basis` always set), `DER_T09` (MSFT fiscal boundary). All against live SEC data.