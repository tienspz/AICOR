# AICOR — API Contract Rationale

**Status:** Proposed · **Date:** 2026-10-13

> ## The authoritative artifact is `docs/openapi.yaml`
>
> This document contains **no payload examples and no field-level schemas.** Per skill `contract-first`, the same payload shape must not be maintained independently in a wiki, prose document, mock file and provider code — copies drift, and the copy that survives longest is the one nobody regenerates.
>
> Everything structural lives in `docs/openapi.yaml`. Pydantic models (`aicor/api/schemas_generated.py`) and the TypeScript client (`web/src/generated/api.ts`) are **generated** from it. A CI check fails if FastAPI's emitted schema diverges.
>
> **This document carries what a schema cannot:** why the API is shaped this way, and what each endpoint is for.

---

## 1. Consumer jobs

`contract-first` requires the consumer to state its needs before the provider exists. These are the dashboard's actual jobs.

| Job | Page | Needed because |
|---|---|---|
| Show CapEx/Revenue for MSFT with a link to its SEC filing | 02 | A reviewer must be able to pick any number and trace it (§9.3) |
| Show MSFT and Alphabet on one calendar axis despite different fiscal years | 01, 02 | FY26Q3 and 2026Q1 both end 2026-03-31; the labels collide (DAT-01) |
| Render "not yet reported" as such, with the reason | all | SRC-05 requires an explained absence, not a blank cell |
| Show all five lags together, never one "best" lag | 04 | LAG-02 forbids an assumed lag; a single number manufactures a causal story |
| Show a CI that spans zero as uncertainty, not as a finding | 04, 05 | n ≈ 13; the honest answer is usually "not distinguishable" |
| Let a reviewer read every DQ failure without a shell | 09 | `data_quality_log` exists to be legible to a human |
| Show a scenario labelled ASSUMPTION | 08 | SCN-01…03 forbid presenting these as company guidance |
| Refuse to show a decision that has no limitations | 01 | NFR-04; the likeliest way to lose the caveat is to omit it |

## 2. Contract principles

| # | Principle | SRS |
|---|---|---|
| **C-1** | **The API computes nothing.** No ratio, growth rate, correlation or aggregation. Every such value was computed in layer 8/9 and persisted. | DSH-01 |
| **C-2** | Every payload carries provenance. A response that cannot be traced to a `source_id` is a defect. | PRV-01, NFR-02 |
| **C-3** | **NULL is a value.** Delivered as `value: null` with `status` and `reason`. Never omitted, never zero. | SRC-05 |
| **C-4** | `config_version` is echoed on any response influenced by a research parameter. | NFR-03 |
| **C-5** | Identifiers are **opaque strings**. Never coerced to numbers anywhere. | precision safety |
| **C-6** | No secret, credential or internal path appears in any response. | security |

> **C-1 is the contract expression of architecture invariant I-1.** If the API does not compute, the frontend cannot compute — which makes DSH-01 structurally true rather than a review convention. It is enforced by a source-inspection test (`API_T03`) and an ESLint rule in `web/`.

## 3. Endpoints and their contract rationale

Full request/response schemas: `docs/openapi.yaml`.

| Endpoint | Contract rationale |
|---|---|
| `GET /api/v1/companies` | Two issuers with different fiscal-year-end metadata. Display-only fact, no computation. |
| `GET /api/v1/companies/{id}/coverage` | **Load-bearing.** Tells the UI which quarters exist *and why others don't*, so absence is rendered from fact rather than inferred from a gap in a chart. Without this the frontend guesses, and guessing is how a "not yet reported" quarter becomes an invisible one. |
| `GET /api/v1/companies/{id}/financials` | Must expose `capex_definition` and `period_basis`, because the client must never infer either. Returns quarterly rows keyed by `period_end_date`; `fiscal_period` is display-only. |
| `GET /api/v1/companies/{id}/features` | The slice's core. Every row carries definition, calculation method, provenance and `status`/`reason`. |
| `GET /api/v1/companies/{id}/segments` | Segment revenue and operating income, preferred from segment XBRL (Tier S) over IR scraping (OD-14). |
| `GET /api/v1/companies/{id}/events` | Events with `cluster_id` so overlapping `[-10,+10]` windows are visibly grouped and counted once (OD-11). |
| `GET /api/v1/events/{event_id}/car` | Returns the stored CAR with its window bounds and the benchmark id+version that produced it, so a reviewer can see the event study's inputs. |
| `GET /api/v1/analysis` | Stored results with `method`, `n_observations` and bootstrap CIs. |
| `GET /api/v1/analysis/lag-profile` | **Always returns all five lags together.** Refuses a subset. This is the contract-level expression of LAG-02: a client cannot be handed one lag in isolation. |
| `GET /api/v1/companies/{id}/scenarios` | Every record carries `assumption_class`, enum-constrained to the single value `ASSUMPTION`, so an unlabelled scenario is un-representable. |
| `GET /api/v1/decision` | DEC-01 and DEC-02 records. **`limitations` is non-nullable** — the handler returns 500 rather than emit a confident answer with no caveats. |
| `GET /api/v1/provenance/{source_id}` | The NFR-02 walk: tier, URL, access date, verification status, XBRL tag, period basis, filing accession, raw SHA-256, and every derived feature and result id. |
| `GET /api/v1/data-quality` | DQ-01…DQ-05 with `expected` and `actual`, so a failure is reviewable without re-running the pipeline. |

## 4. Endpoint → requirement → dashboard map

| Endpoint | Requirement | Page |
|---|---|---|
| `/companies`, `/companies/{id}/coverage` | DAT-01, DQ-01, SRC-05 | all |
| `/companies/{id}/financials` | FR-01…FR-05, DAT-01 | 01, 02 |
| `/companies/{id}/features` | FE-01…FE-08, OUT-01…OUT-03, PRV-01 | 02, 03 |
| `/companies/{id}/segments` | FR-06, FR-07, OUT-01 | 03 |
| `/analysis?type=io`, `/analysis/lag-profile` | LAG-01, LAG-02, IO-01, IO-02 | 04 |
| `/analysis?type=efficiency` | EFF-01, EFF-02 | 05 |
| `/companies/{id}/events`, `/events/{id}/car` | EVT-01…EVT-03, OUT-03 | 06 |
| `/analysis?type=regime` | REG-01 | 07 |
| `/companies/{id}/scenarios`, `/analysis?type=risk` | SCN-01…SCN-03, RSK-01 | 08 |
| `/provenance/{source_id}`, `/data-quality` | SRC-01…SRC-07, DQ-01…DQ-05, NFR-02 | 09 |
| `/decision` | DEC-01…DEC-03, ROB-01, NFR-04 | 01 |

## 5. Errors

Uniform envelope, defined once in the contract:

- **400** malformed parameter
- **404** unknown company, feature, analysis type or event
- **422** semantically invalid — for example `lag` outside 0–4
- **500** unexpected; carries a `trace_id` and **never** a stack trace, SQL fragment or internal path

## 6. Frontend rules

1. The **generated client is the only** way `web/` reaches the API. No hand-written request paths.
2. `web/` performs **no arithmetic** on API data. No ratios, growth rates, sums, averages, standard deviations, or date arithmetic on financial values. Percent signs, currency symbols and thousand separators are display formatting and live only in `format.ts`. Enforced by an ESLint rule plus `DSH_T01`.
3. Loading, error, NULL-with-reason and empty states are implemented for **every** endpoint.
4. No secret or internal path is bundled into the client.

## 7. Open items

| # | Item | Status |
|---|---|---|
| API-1 | Pagination shape | Offset/limit with deterministic `ORDER BY`. The dataset is 21 quarters × 2 companies; cursor pagination would be premature. Revisit only if a response exceeds ~500 rows. |
| API-2 | Cache headers | Values change only on re-run, so a long `max-age` is acceptable; invalidation keys on `pipeline_run_id`. |
| API-3 | Auth | None — the API serves public filings only. Recorded as an accepted NFR gap (OD-06); must be revisited if deployed beyond localhost. |
| API-4 | Generator pinning | `datamodel-code-generator` and `openapi-typescript` are pinned and run with least privilege: no network, no secrets, write access only to their two generated paths. |