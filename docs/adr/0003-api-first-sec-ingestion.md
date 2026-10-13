# ADR-0003 · API-first SEC ingestion over HTML scraping

- **Status:** Accepted
- **Date:** 2026-10-13
- **Deciders:** Agent 0
- **Affects:** T-08, T-09, T-12, T-13

## Context

The SRS's §3.3 canonical sources point at filing **documents** — HTML files on `sec.gov/Archives`. The naive implementation is to open each 10-Q/10-K and parse its tables.

Phase 1 verification established what those documents actually are:

| Document | Verified size |
|---|---|
| MSFT 10-Q, period 2026-03-31 | **7.7 MB** |
| GOOGL 10-Q, period 2026-06-30 | **2.5 MB** |

For a 21-quarter × 2-company window that is roughly 20 large documents, each needing HTML table parsing whose output varies with formatting, column ordering and sign conventions.

Meanwhile SEC publishes **structured** endpoints, both verified working during Phase 1:

- `data.sec.gov/submissions/CIK##########.json` — authoritative index of form type, accession number, period, filing date, primary document
- `data.sec.gov/api/xbrl/companyconcept/CIK##########/us-gaap/{tag}.json` — structured facts, each carrying `start`, `end`, `val`, `form`, `accn`, `fy`, `fp`, `filed`

The `submissions` endpoint was already used in Phase 1 to **confirm the SRS's own accession numbers**, and the `companyconcept` endpoint produced the entire feasibility analysis.

## Decision

**Ingest from the structured SEC APIs. Never parse filing HTML for financial statement values.**

1. **Discover** filings via `submissions` API; populate the `filing` table with accession, form, period, filing date, document name.
2. **Fetch facts** via `companyconcept`, one request per `(company, tag)`.
3. **HTML is a fallback only** — for narrative content, risk factors, and event descriptions (EVT-02), where no structured equivalent exists.

## Consequences

**Positive**
- Deterministic parsing: `start`/`end`/`val` carry the duration basis explicitly, which is exactly what DQ-03 needs. HTML parsing would have to *infer* whether a column is quarterly or year-to-date — the single most error-prone step in the whole pipeline.
- Every fact arrives with its `accn`, so attribution to a real filing is structural (invariant I-4), not reconstructed.
- Volume drops from ~20 multi-MB documents to a few hundred KB of JSON.
- **Accession numbers are discovered, not hard-coded.** This is what made it possible to *prove* the SRS's accessions correct in Phase 1; a hard-coded list would have rotted silently at the next filing.

**Negative**
- XBRL tagging is inconsistent between issuers and across time — this is precisely the risk recorded as R-01/R-12 and as ADR-0004. The API removes parsing risk but **replaces** it with tag-resolution risk, which must be managed explicitly rather than assumed away.
- Narrative/segment commentary needed for EVT-02 still requires fetching HTML.
- SEC rate limits (~10 req/s, mandatory User-Agent) become a real constraint — mitigated by a token-bucket limiter and backoff.

## Rejected alternative

Parse the filing HTML directly. Rejected: the 7.7 MB documents are large, their table layouts are presentation-dependent, and — decisively — they do not carry the duration basis as machine-readable metadata, which is the field DQ-03 exists to police.