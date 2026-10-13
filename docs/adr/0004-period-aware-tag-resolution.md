# ADR-0004 · Period-aware XBRL tag resolution, failing loudly

- **Status:** Accepted
- **Date:** 2026-10-13
- **Deciders:** Agent 0
- **Affects:** T-09, T-12, FR-01, SRC-07, R-01, R-12
- **Addresses:** `open_decisions.md` OD-08

## Context

Phase 1 verification of SEC `companyconcept` established that XBRL tag usage is **not stable across companies or over time**:

| Company | Tag | Coverage |
|---|---|---|
| MSFT | `RevenueFromContractWithCustomerExcludingAssessedTax` | 2016-06-30 → 2026-06-30 ✅ |
| MSFT | `Revenues` | **ends 2010-12-31** (legacy) |
| GOOGL | `RevenueFromContractWithCustomerExcludingAssessedTax` | **stops 2025-03-31** ❌ |
| GOOGL | `Revenues` | covers the window through 2026-06-30 ✅ |

This is the highest-severity data defect found in Phase 1, and it is **silent**.

A pipeline that binds one tag per company — the obvious implementation — resolves Alphabet's revenue to the ASC 606 tag and gets a series that **stops at 2025-03-31**. The pipeline raises no error. It produces a shorter chart. A reviewer sees a gap and may not notice it is an artefact of tag selection rather than a missing filing.

The mirror case is also real: MSFT's `Revenues` tag died in 2010, so a pipeline that picked `Revenues` for MSFT would return nothing at all for the study window.

Both companies report **21 consecutive calendar quarter-ends** (2021-06-30 → 2026-06-30) in reality — so the truncation is purely a resolution artefact and is fully detectable.

## Decision

**Resolve tags per `(company_id, period_end_date)`, never per company. Record what was used. Fail loudly, never skip.**

1. Each logical metric carries an ordered list of candidate tags (see `data_dictionary_and_provenance.md` §6).
2. For each `(company, period)`, select the **first candidate tag that actually reports that period**.
3. Record the selected tag in `source_registry.xbrl_tag` — so the choice is auditable per observation, not just per code path.
4. If **no** candidate tag reports a required quarter, write `status='error'`, `severity=ERROR` to `data_quality_log`, and **fail the run**.
5. Acceptance test `FR_T01` asserts **21 non-null revenue quarters for each company**, so the guard is continuous rather than one-off.

## Alternatives considered

| Option | Why rejected |
|---|---|
| One hard-coded tag per company | The defect this ADR exists to prevent — silently truncates Alphabet by 5 quarters |
| A global preference list applied uniformly | Same failure, different shape; MSFT and GOOGL need *different* tags for the *same* period |
| Skip missing quarters with a warning | **Worst option.** Converts a loud failure into a quiet gap, and DQ-01's completeness rate would still look acceptable |
| Fall back to filing HTML | Rejected by ADR-0003; reintroduces parsing ambiguity |
| Treat XBRL as trustworthy | It is machine-readable and therefore *silently* wrong-able (R-12). DQ-04's `Assets = Liabilities + Equity` check exists as an independent arithmetic verification |

## Consequences

**Positive**
- Both companies yield the full 21-quarter series from a single uniform rule.
- The chosen tag is recorded per observation, so a reviewer can see *why* a value was sourced the way it was.
- A genuine data gap becomes an ERROR that blocks the pipeline, rather than a silent hole that survives to the dashboard.

**Negative**
- More requests than a single-tag approach (a few extra per metric — negligible).
- Requires a candidate-tag table that must be maintained as SEC taxonomy evolves. This is accepted; the failure mode is a **loud** ERROR, not a quiet wrong answer.
- Slightly more complex code than a tag lookup, which is the correct trade: the simplicity alternative is precisely what hides the defect.

## Verification

`FR_T01` (21 non-null quarters per company) and `SRC_T06` (the connector independently rediscovers the two verified SRS accessions) together close this risk. Neither is satisfied by a passing unit test alone — both run against live SEC data.