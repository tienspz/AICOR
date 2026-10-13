# AICOR — Test & Acceptance Plan

**Status:** Proposed · **Date:** 2026-10-13
**Authority:** implements SRS §9.1 (verification matrix) and §9.3 (Definition of Done).

---

## 1. Non-negotiable testing rules

| # | Rule | Why |
|---|---|---|
| **R-1** | **No mock data in any acceptance path.** Tests assert against real SEC/XBRL/Yahoo data. | SRC-07. A mock-satisfying test proves nothing about a provenance system. |
| **R-2** | **No task is complete without executed evidence.** A passing claim requires recorded output, not an assertion. | §9.1, NFR-01 |
| **R-3** | **Every requirement ID maps to ≥1 TEST-ID.** Bidirectional coverage is audited in Stage 6. | CMU/SEI traceability |
| **R-4** | **A NULL with a reason passes; a NULL without one fails.** Absence must always be explained. | SRC-05 |
| **R-5** | **DST/DST edge cases are tested with deliberately wrong fixtures**, not only correct data. | DQ-02/03/04 |
| **R-6** | **QA owns no production code**, so it can never rubber-stamp its own work. | Independence (layer 12) |
| **R-7** | **Deterministic re-runs.** Any stochastic step takes a seed from `research_params.yaml`. | NFR-01 |

## 2. Test layers

| Layer | Scope | Owner | Gate |
|---|---|---|---|
| Unit | Tag resolution, YTD algebra, formulas, NULL guards | Agents 1–3 (in-module) | Stage 3, 4 |
| Integration | Connector ↔ raw store ↔ DB; cross-checks | Agent 1 | Stage 3 |
| Contract | OpenAPI consumer/provider | Agents 3 + 5 | Stage 5 |
| Data quality | DQ-01…05 as executable assertions over real data | Agent 5 | Stage 3 |
| E2E | Playwright over 9 pages incl. NULL/error states | Agent 5 | Stage 5 |
| Audit | Traceability walk, reproducibility re-run, security | Agent 5 | Stage 6 |
| Acceptance | SRS §9.2 checklist + §9.3 chain | Agent 5 + reviewer | Stage 7 |

---

## 3. TEST-ID register

### 3.1 Sources (SRC)

| TEST-ID | Assertion | Type |
|---|---|---|
| SRC_T01 | Every `source_registry` row has a tier ∈ {S,A,B}; Tier R absent from the financial registry | unit |
| SRC_T02 | Source-selection ladder encoded and each branch unit-tested (SEC → company → higher-quality primary → unavailable) | unit |
| SRC_T03 | No NULL is filled; every NULL carries a non-empty `reason` | integration |
| SRC_T04 | Confidence mapping per SRC-06: reported→HIGH, derived→MEDIUM, proxy→LOW | unit |
| SRC_T05 | Zero mock/fabricated rows in the analytical path; every metric resolves to a live endpoint | audit |
| SRC_T06 | **T-08 regression:** the SEC `submissions` connector independently discovers `0001193125-26-191507` (MSFT, 2026-03-31) and `0001652044-26-000071` (GOOGL, 2026-06-30) | integration, live |

### 3.2 Financial data (FR)

| TEST-ID | Assertion | Type |
|---|---|---|
| FR_T01 | **21 non-null revenue quarters per company** — the anti-truncation guard (OD-08) | integration, live |
| FR_T02 | 21 non-null `rd_expense` quarters per company | integration |
| FR_T03 | 21 non-null `capex` quarters; `capex >= 0`; `capex_definition` populated | integration |
| FR_T04 | 21 non-null `operating_income` quarters | integration |
| FR_T05 | `fcf == cfo - capex` exactly, for every row | unit + integration |
| FR_T06 | Each MSFT segment present or NULL+reason | integration |
| FR_T07 | Each GOOGL segment present or NULL+reason | integration |
| FR_T08 | `source_id` present on every non-NULL financial row | unit |

### 3.3 Period derivation (DQ-03 / OD-13) — *highest-risk area*

| TEST-ID | Assertion | Type |
|---|---|---|
| DER_T01 | Q1 = 3M | unit |
| DER_T02 | Q2 = 6M − 3M | unit |
| DER_T03 | Q3 = 9M − 6M | unit |
| DER_T04 | **Q4 = FY − 9M**, including a known-value fixture | unit |
| DER_T05 | **No Q4 is ever populated from a 3-month fact** (none exists) | integration |
| DER_T06 | MSFT's 14 directly-reported 3-month quarters agree with derived values within tolerance | integration, live |
| DER_T07 | Every fact carries `period_basis` ∈ {3M,6M,9M,FY,instant} | unit |
| DER_T08 | A deliberately mis-tagged duration is rejected, not silently accepted | unit |
| DER_T09 | MSFT fiscal-year boundary handled correctly (FY Q1 = Jul–Sep) | unit |

### 3.4 Data quality (DQ)

| TEST-ID | Assertion | Type |
|---|---|---|
| DQ_T01 | Completeness rate computed per company/feature; breaches logged with severity | unit |
| DQ_T02 | Validity: `revenue ≥ 0`, `capex ≥ 0`, `shares > 0`; a negative-raw-CapEx fixture normalises correctly | unit |
| DQ_T03 | No quarterly/YTD mixing | integration |
| DQ_T04 | **`Assets − (Liabilities + Equity)` within tolerance for all 42 company-quarters** | integration, live |
| DQ_T05 | SEC-vs-IR conflict logged; resolved value retains Tier S | integration |
| DQ_T06 | A corrupted fixture **fails** each check (proves the check can fail) | unit |

### 3.5 Features (FE)

| TEST-ID | Assertion | Type |
|---|---|---|
| FE_T01 | `YoY = V_t/V_t-4 − 1`; first 4 quarters NULL+reason | unit |
| FE_T02 | `QoQ = V_t/V_t-1 − 1` | unit |
| FE_T03 | `R&D/Revenue` correct | unit |
| FE_T04 | `CapEx/Revenue` correct | unit |
| FE_T05–07 | Efficiency formulas correct — **BLOCKED pending OD-02** | unit (held) |
| FE_T08 | **NULL guards:** zero denominator, near-zero denominator, negative base, FCF sign change → all yield NULL+reason; **no clamping, no rounding to bypass** | unit |
| FE_T09 | Threshold value used is read from versioned config, not a literal | unit |

### 3.6 Analysis

| TEST-ID | Assertion | Type |
|---|---|---|
| LAG_T01 | Exactly 5 lags (0–4) per relationship per company | unit |
| LAG_T02 | Reported lag derives from the tested profile, never a constant | unit |
| IO_T01 | 4 relationships × 5 lags × 2 companies = **40 results** | integration |
| IO_T02 | Every result has non-empty `method` | unit |
| IO_T03 | **`n_observations ≈ 13`** matches the FE-01 + lag drop rule | unit |
| IO_T04 | Deterministic: identical seed → byte-identical results across runs | integration |
| CAU_T01 | **Zero output strings match `caused|causes|led to`**; every `result_class` present | unit (string guard) |
| EFF_T01 | Five efficiency measures present; **composite absent until EFF-02 approved** | unit |
| EFF_T02 | Weights sum to 1.00; `weight_version`, `weights`, `normalization_method` all persisted | unit |
| SEN_T01 | Full sensitivity grid executed; lags are 0,1,2,3,4 (**not** the original 0,1,2,4) | unit |
| ROB_T01 | Status ∈ {ROBUST, SENSITIVE}; a synthetic ranking reversal yields SENSITIVE + reason | unit |
| EVT_T01 | Event schema present; each of the 8 types has ≥1 sourced event **or** an explicit "none found" | integration |
| EVT_T02 | 100% of events have Tier A/S + resolvable URL | integration |
| EVT_T03 | CAR spans exactly 21 trading days; benchmark id + version stored | unit |
| EVT_T04 | **Overlapping windows are grouped by `cluster_id`** and counted once in aggregates | unit |
| EVT_T05 | Earnings windows provably do **not** overlap (~63 trading days apart vs a 21-day window) | unit |
| REG_T01 | Every company-quarter assigned exactly one regime, with reason; **BLOCKED pending OD-04** | unit (held) |
| SCN_T01–03 | Scenarios emitted, labelled ASSUMPTION, not guidance | unit |
| SCN_T04 | Effects requiring an invented elasticity are **NULL + reason**, never estimated | unit |
| RSK_T01 | All 8 risk variables present or NULL+reason | unit |
| RSK_T02 | High Investment+High Output is distinguishable from High Investment+Weak Output | unit |
| DEC_T01 | DEC-01 record matches the specified shape; every sub-score traceable | unit |
| DEC_T02 | `limitations` non-empty | unit |
| DEC_T03 | Every conclusion carries its `result_class` | unit |

### 3.7 Provenance & non-functional

| TEST-ID | Assertion | Type |
|---|---|---|
| PRV_T01 | All 12 PRV-01 fields present and non-null where required | unit |
| PRV_T02 | `input_feature_ids` populated for every derived feature | unit |
| NFR_T01 | **Reproducibility:** two clean runs byte-compare `analysis_results` | integration |
| NFR_T02 | **Traceability:** §9.3 chain walkable for one number per dashboard page | audit |
| NFR_T03 | Every result row carries `config_version` | unit |
| NFR_T04 | Every conclusion lists its assumptions | unit |
| MKT_T01 | Market data retrieved for MSFT, GOOGL, `^GSPC` | integration |
| MKT_T02 | `^GSPC` stored; price-index limitation documented | unit |
| MKT_T03 | Raw CSV + SHA-256 in manifest; **second run does not re-fetch** | integration |
| MKT_T04 | Market-adjusted return formula correct | unit |
| MKT_T05 | **`adjusted_close` non-null for every bar** (voids OUT-03/EVT-03 otherwise) | integration |

### 3.8 API & dashboard

| TEST-ID | Assertion | Type |
|---|---|---|
| API_T01 | `openapi.yaml` validates; generated client compiles | contract |
| API_T02 | Provider responses match the OpenAPI schema for every endpoint | contract |
| API_T03 | **No endpoint performs aggregation** — a source-inspection test | audit |
| API_T04 | NULL always delivered as `{value:null, status, reason}` | unit |
| API_T05 | `decision.limitations` is non-nullable (500 if absent) | unit |
| API_T06 | `error` envelope shape + correct status codes (400/404/422/500) | unit |
| API_T07 | No secret or internal path in any response | security |
| DSH_T01 | **Zero arithmetic on API data in `web/`** — ESLint rule + source inspection | audit |
| DSH_T02 | Exactly 9 routes; every route has loading/error/NULL/empty states | E2E |
| AI_T02 | **Zero occurrences of "AI Investment" without the "Proxy" qualifier** in UI strings | unit (grep) |
| AI_T01 | Every proxy row has `reported=false, derived=true, proxy=true` | unit |
| AI_T03 | No field named `ai_investment` exists anywhere in the schema | unit |
| A11Y_T01 | axe passes on all 9 pages | E2E |
| A11Y_T02 | Full keyboard navigation of every page | E2E |
| E2E_T01 | Playwright covers each of the 9 pages' happy path | E2E |
| E2E_T02 | A NULL-with-reason renders a reason, never a blank or a zero | E2E |

---

## 4. Acceptance gates

### Gate A — Slice (before any breadth)

| # | Criterion |
|---|---|
| A1 | MSFT `2025-03-31`: Revenue, R&D, CapEx present with Tier S `source_id` |
| A2 | `CapEx/Revenue` computed in the pipeline and stored — **not** in the frontend |
| A3 | API returns it with full provenance |
| A4 | One dashboard panel renders it, clickable to `source_url` |
| A5 | **§9.3 chain: panel → analysis → feature → calculation → raw file → `source_id` → `source_url` → SEC filing** |
| A6 | A reviewer reproduces the value on a clean re-run |
| A7 | `DQ_T04` passes for this quarter |
| A8 | No mock data anywhere in the path |

### Gate B — Stage 3 (data spine)

`FR_T01` · `FR_T02` · `FR_T03` · `FR_T04` · `DER_T01…T09` · `DQ_T01…T06` · `SRC_T06` · `MKT_T03` · `MKT_T05` — **all pass against live data**.

### Gate C — Stage 5 (product)

`API_T01…T07` · `DSH_T01` · `DSH_T02` · `AI_T02` · `E2E_T01` · `E2E_T02` · `A11Y_T01` · `A11Y_T02`.

### Gate D — Stage 7 (acceptance, SRS §9.2 + §9.3)

Every §9.2 checklist item evidenced; §9.3 walkable for **one number on each of the 9 pages**; `NFR_T01` reproducibility double-run byte-identical; zero mock rows; every NULL explained; no invented research parameters; every conclusion carrying `limitations`.

---

## 5. Coverage verification

Stage 6 runs a bidirectional coverage audit:

```
for each requirement_id in the SRS register:
    assert exists test where requirement_id ∈ test.requirement_ids
for each test in the suite:
    assert test.requirement_ids ⊆ known requirement_ids   # no orphan tests
```

Both directions must be clean. A requirement with no test, or a test with no requirement, is an audit finding.

---

## 6. Test data policy

| Rule | Detail |
|---|---|
| Real data only in acceptance paths | Raw snapshots are immutable, so tests read the same bytes every run |
| Fixtures for edge cases | Degenerate cases (zero denominator, negative base, FCF sign change, truncated tags) require **synthetic fixtures** — but they test *guard behaviour*, not data correctness, so they never satisfy an acceptance criterion on their own |
| Live-network tests | Tagged `live`, run in CI and locally; skipped only with an explicit, documented reason |
| Isolation | Tests never write to the production raw store (I-2) |
| Determinism | Fixed seeds from `research_params.yaml`; no wall-clock or locale dependence in assertions |