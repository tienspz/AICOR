# AICOR — API Contracts

**Status:** Proposed · **Date:** 2026-10-13
**Authority:** `docs/openapi.yaml` is the single machine-checkable contract (`contract-first`). This document is its human-readable specification; **on conflict, the OpenAPI file wins** and any divergence is a bug.

---

## 1. Contract principles

| # | Principle | SRS |
|---|---|---|
| **C-1** | **Read-only over stored values.** The API never computes a financial or analytical figure. Every ratio, growth rate and statistic was computed in layer 8/9 and persisted first. | DSH-01 |
| **C-2** | **Every payload is provenance-carrying.** A response that cannot be traced to a `source_id` is a defect. | PRV-01, NFR-02 |
| **C-3** | **NULL is a value.** Absent data is returned as `value: null` + `status` + `reason`, never omitted, never zero, never silently dropped. | SRC-05 |
| **C-4** | **Versioned config is echoed.** Any response influenced by research parameters returns `config_version`. | NFR-03 |
| **C-5** | **No secrets.** No API key, credential, or internal path appears in any response. | security |

> C-1 is the contract expression of architecture invariant I-1. It makes DSH-01's "dashboard must not compute financial figures" **structurally impossible to violate** rather than a review convention: if the API does not compute, the frontend cannot compute.

## 2. Common envelope

```json
{
  "data": { },
  "meta": {
    "config_version": "cfg-2026-10-13.1",
    "generated_at": "2026-10-13T09:12:44Z",
    "pipeline_run_id": "run-8f3c1a",
    "count": 21
  },
  "links": { "self": "/api/v1/..." }
}
```

Errors:

```json
{
  "error": {
    "code": "PERIOD_NOT_ALIGNED",
    "message": "No company-quarter matches period_end_date=2026-03-31",
    "trace_id": "tr_9a2f",
    "details": { "requested": "2026-03-31", "available_from": "2021-06-30", "available_to": "2026-06-30" }
  }
}
```

| Status | Used for |
|---|---|
| 400 | malformed parameter |
| 404 | unknown company / feature / analysis type |
| 422 | semantically invalid (e.g. `lag` outside 0–4) |
| 500 | unexpected — `trace_id` correlates to the logs |

## 3. Endpoints

### 3.1 Companies and coverage

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/companies` | Both companies + fiscal-year-end metadata |
| GET | `/api/v1/companies/{company_id}/coverage` | **Which quarters actually exist**, per feature — backs every NULL state in the UI |

```json
GET /api/v1/companies/MSFT/coverage
{
  "data": {
    "company_id": "MSFT",
    "fiscal_year_end": "06-30",
    "quarters_available": 21,
    "range": { "from": "2021-06-30", "to": "2026-06-30" },
    "by_metric": {
      "revenue":    { "available": 21, "missing": [] },
      "capex":      { "available": 21, "missing": [] },
      "rd_expense": { "available": 21, "missing": [] },
      "forward_1_quarter_abnormal_return": {
        "available": 20,
        "missing": ["2026-06-30"],
        "reason": "no_subsequent_quarter"
      }
    }
  }
}
```

> This endpoint is what makes the dashboard's loading/empty/NULL states honest: the UI knows *in advance* which values will be NULL and why, instead of inferring absence from a gap in a chart.

### 3.2 Features — `GET /api/v1/companies/{id}/features`

Query: `feature` (repeatable), `from`, `to`, `calendar_quarter`, `include_nulls=true`

```json
{
  "data": [
    {
      "feature_id": "MSFT_CAPEX_INTENSITY_2025Q4",
      "company_id": "MSFT",
      "period_end_date": "2025-03-31",
      "fiscal_period": "FY25Q3",
      "calendar_quarter": "2025Q1",
      "feature": "capex_intensity",
      "value": 0.3725,
      "unit": "ratio",
      "definition": "CapEx divided by quarterly revenue",
      "calculation_method": "capex / revenue",
      "reported_or_derived": "derived",
      "proxy": false,
      "confidence": "MEDIUM",
      "status": "ok",
      "reason": null,
      "source": {
        "source_id": "MSFT_SEC_XBRL_2025Q3",
        "source_tier": "S",
        "source_url": "https://www.sec.gov/Archives/edgar/data/789019/…/msft-20250331.htm",
        "verification_status": "verified",
        "xbrl_tag": "PaymentsToAcquirePropertyPlantAndEquipment",
        "period_basis": "9M"
      },
      "input_feature_ids": ["MSFT_CAPEX_2025Q3", "MSFT_REVENUE_2025Q3"]
    },
    {
      "feature_id": "MSFT_FCF_EFFICIENCY_2024Q2",
      "value": null,
      "status": "unavailable",
      "reason": "denominator_near_zero: |resource_growth|=0.0003 < threshold 0.005",
      "unit": "ratio",
      "calculation_method": "fcf_growth / resource_growth",
      "source": null
    }
  ],
  "meta": { "config_version": "cfg-2026-10-13.1", "count": 42 }
}
```

**Note the second record.** It demonstrates C-3: a NULL is delivered with its machine-readable reason, and with **no invented value**. FR-08/FE-08's threshold arrives from config and is echoed in the reason string, so the reason is reproducible.

### 3.3 Financial facts — `GET /api/v1/companies/{id}/financials`

Returns `financial_quarterly` rows keyed by `period_end_date`, with `capex_definition` and `period_basis` exposed so the UI never needs to infer either.

### 3.4 Segments — `GET /api/v1/companies/{id}/segments`

`?segment=intelligent_cloud` etc. Powers dashboard page 03 and OUT-01.

### 3.5 Analysis results — `GET /api/v1/analysis`

Query: `type` (`lag|io|efficiency|event|regime|sensitivity|robustness|risk`), `company_id`, `metric`, `lag` (0–4), `from`, `to`

```json
{
  "data": [
    {
      "analysis_id": "an_MSFT_IO_capex_growth__cloud_growth_lag2",
      "company_id": "MSFT",
      "period_end_date": null,
      "analysis_type": "io",
      "metric": "capex_growth → intelligent_cloud_growth",
      "value": 0.41,
      "lag": 2,
      "method": "spearman_rank_correlation; bootstrap_ci_percentile; n=13; seed=20261013",
      "n_observations": 13,
      "ci_low": -0.22,
      "ci_high": 0.78,
      "result_class": "association",
      "confidence": "LOW",
      "status": "ok",
      "config_version": "cfg-2026-10-13.1",
      "feature_ids": ["MSFT_CAPEX_GROWTH", "MSFT_INTELLIGENT_CLOUD_GROWTH"],
      "interpretation_guard": "association_only"
    }
  ]
}
```

> `n_observations: 13`, the bootstrap CI, and `result_class: "association"` are the machine-readable form of CAU-01 and OD-05. The CI spanning zero is the honest result — it is displayed as uncertainty, not suppressed, and never as a finding.

### 3.6 Lag profile — `GET /api/v1/analysis/lag-profile`

Returns **all five lags for one relationship at once**.

```json
{ "data": { "relationship": "capex_growth → intelligent_cloud_growth",
  "company_id": "MSFT",
  "lags": [ {"lag":0,"value":0.12,"ci_low":-0.45,"ci_high":0.61},
            {"lag":1,"value":0.28,"ci_low":-0.31,"ci_high":0.74},
            {"lag":2,"value":0.41,"ci_low":-0.22,"ci_high":0.78},
            {"lag":3,"value":0.30,"ci_low":-0.34,"ci_high":0.76},
            {"lag":4,"value":0.19,"ci_low":-0.42,"ci_high":0.68} ] } }
```

> Required by LAG-02: the client can never see a single "best lag" in isolation, which is exactly the failure mode that manufactures a causal story. All five are always returned together.

### 3.7 Events — `GET /api/v1/companies/{id}/events`

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/companies/{id}/events` | Events with `event_date`, `event_type`, `source_id`, `tier` |
| GET | `/api/v1/events/{event_id}/car` | Expected return, AR, CAR, window bounds, benchmark id + version |

`cluster_id` is exposed so overlapping `[-10,+10]` windows are visibly grouped and counted once in aggregates (OD-11 / EVT-03).

### 3.8 Scenarios — `GET /api/v1/companies/{id}/scenarios`

Each record carries `scenario_code` ∈ `S1|S2|S3`, the full `assumption` JSON, and per-effect `status`/`reason`. A `label: "ASSUMPTION"` discriminator is **mandatory** in the payload — SCN-01…03 forbid presenting these as company guidance.

### 3.9 Decisions — `GET /api/v1/decision`

Returns DEC-01's per-company record and DEC-02's decision record: `winner`, `confidence`, `robustness` (`ROBUST`/`SENSITIVE`), `key_drivers`, `sensitivity`, `limitations`.

> **`limitations` is non-nullable.** A decision record without limitations is invalid and the endpoint returns 500 — a deliberate forcing function for NFR-04, because the most likely way to lose the sample-size caveat is simply to omit the field.

### 3.10 Provenance — `GET /api/v1/provenance/{source_id}`

The NFR-02 endpoint. Returns the full walk: tier, URL, access date, verification status, XBRL tag, period basis, filing accession + form + filing date, raw `sha256`, and every `feature_id` / `analysis_id` derived from it.

### 3.11 Data quality — `GET /api/v1/data-quality`

DQ-01…DQ-05 results with `expected`, `actual`, `severity`. Powers dashboard page 09 so a reviewer can see *what failed* without shell access.

## 4. Endpoint → requirement → dashboard map

| Endpoint | Requirement | Page |
|---|---|---|
| `/companies/{id}/coverage` | DQ-01, SRC-05 | all |
| `/companies/{id}/financials` | FR-01…05, DAT-01 | 01, 02 |
| `/companies/{id}/features` | FE-01…08, OUT-01…03, PRV-01 | 02, 03 |
| `/companies/{id}/segments` | FR-06, FR-07, OUT-01 | 03 |
| `/analysis?type=io`, `/analysis/lag-profile` | LAG-01, LAG-02, IO-01, IO-02 | 04 |
| `/analysis?type=efficiency` | EFF-01, EFF-02 | 05 |
| `/companies/{id}/events`, `/events/{id}/car` | EVT-01…03, OUT-03 | 06 |
| `/analysis?type=regime` | REG-01 | 07 |
| `/companies/{id}/scenarios`, `/analysis?type=risk` | SCN-01…03, RSK-01 | 08 |
| `/provenance/{id}`, `/data-quality` | SRC-01…07, DQ-01…05, NFR-02 | 09 |
| `/decision` | DEC-01…03, ROB-01, NFR-04 | 01 |

## 5. Frontend contract rules

1. The generated OpenAPI client is the **only** way `web/` reaches the API. No hand-written `fetch` paths.
2. **`web/` performs no arithmetic on API data.** No ratios, growth rates, sums, averages, standard deviations, or date arithmetic on financial values. Dates may be formatted for display; numbers may not be transformed. Enforced by an ESLint rule plus review gate `DSH_T01`.
3. **Display formatting only** — percent signs, currency symbols, thousand separators are presentation, not computation, and live in a single `format.ts`.
4. Loading, error, NULL-with-reason and empty states are implemented for **every** endpoint, not just the happy path (DSH-02).
5. No secret, token, or internal filesystem path is bundled into the client (I-7).

## 6. Open items

| # | Item | Status |
|---|---|---|
| API-1 | Pagination shape for `features` (21 quarters × N features is small; `analysis` may be larger) | Offset/limit + total count; revisit only if a response exceeds ~500 rows |
| API-2 | Cache headers | Values are pipeline-derived and change only on re-run → long `max-age` acceptable; invalidate by `pipeline_run_id` |
| API-3 | Auth | None. Serves public filings only. Recorded as an accepted NFR gap (OD-06) — must be confirmed if the deployment leaves localhost |
| API-4 | `analysis` filter combinations | Full grid is small (5 lags × ~4 relationships × 2 companies); no cursor pagination needed |