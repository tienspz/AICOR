# AICOR API Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the authoritative contract from the slice's two endpoints to the full read-only API that all nine dashboard pages consume, keeping `docs/openapi.yaml` the single source of truth and the API computation-free.

**Architecture:** Contract-first throughout. The contract is authored once and both the Pydantic models and the TypeScript client are generated from it; a CI drift check fails if FastAPI's emitted schema diverges. Every endpoint returns stored rows only — this is what makes DSH-01 structurally true.

**Tech Stack:** FastAPI, Pydantic v2, `datamodel-code-generator`, `openapi-typescript`, SQLAlchemy 2.x, pytest, httpx.

**Spec:** `SPEC.md` §6.2, §4.14 (DSH-01, DSH-02), §5.2 · `docs/planning/api_contracts.md` · `docs/planning/data_dictionary_and_provenance.md` · `docs/planning/test_and_acceptance_plan.md` §3.8

**Precondition:** `2026-10-13-aicor-vertical-slice.md` complete. This plan adds endpoints; it does not re-litigate the two that already work.

---

## Global Constraints

- **`docs/openapi.yaml` stays the single authoritative artifact.** No wiki page, mock file, or provider serializer may restate a payload shape.
- **The API computes nothing.** No division, percentage, growth rate, correlation, or aggregation anywhere in `aicor/api/`. A test inspects the source and fails if arithmetic appears.
- **NULL is delivered as `{value: null, status, reason}`** — never omitted, never zero.
- **`decision.limitations` is non-nullable.** A decision record without limitations is invalid and the endpoint returns 500. This is a deliberate forcing function for NFR-04, because the likeliest way to lose the sample-size caveat is to omit the field.
- **`config_version` is echoed on every response** influenced by a research parameter (NFR-03).
- **`coverage` endpoint is authoritative for which quarters exist**, so the UI knows in advance which cells will be NULL and why instead of inferring absence from a gap in a chart.
- **Error envelope:** `{"error": {"code", "message", "details", "trace_id"}}` with 400 malformed, 404 unknown resource, 422 semantically invalid, 500 unexpected. Stack traces and SQL text never appear.
- **Identifiers stay opaque strings** end to end (Review Focus #3 in the slice plan).
- **Pagination:** offset/limit with deterministic `ORDER BY` — the dataset is small (21 quarters × 2 companies), so offset is correct here and cursor would be premature.

---

## Review Focus

| # | Failure mode | Expected behaviour | Pinned in |
|---|---|---|---|
| 1 | **The UI guesses which quarters exist** and renders an empty chart instead of "not yet reported" | `/coverage` returns the true available/missing map with reasons | Task 2 |
| 2 | **`decision.limitations` comes back empty** because the pipeline had none to give | Endpoint 500s rather than returning a confident decision with no caveats | Task 5 |
| 3 | **The lag endpoint returns only the "best" lag**, so the client is structurally unable to show LAG-02's full profile | `/analysis/lag-profile` always returns all five lags together | Task 4 |
| 4 | **A scenario renders as if it were company guidance** | Every scenario carries an `assumption_class` of `"ASSUMPTION"` in the payload | Task 6 |
| 5 | **Contract drift after a provider edit** — FastAPI's emitted schema diverges from the canonical file | CI diffs them and fails | Task 7 |

---

### Task 1: `GET /api/v1/companies` and `GET /api/v1/companies/{id}/financials`

**Files:** Create `aicor/api/routers/companies.py`, `tests/contract/test_companies_contract.py`; modify `docs/openapi.yaml`

**Interfaces:**
- Consumes: `Company`, `FinancialQuarterly`
- Produces: `CompanyResponse`, `FinancialQuarterlyResponse`; the two paths

- [ ] **Step 1: Write the failing test**

```python
async def test_financials_response_exposes_capex_definition_and_period_basis(client) -> None:
    # FR-03 / DQ-03: the client must never have to infer either
    ...

async def test_fiscal_period_is_returned_but_calendar_quarter_is_the_key(client) -> None:
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/contract/test_companies_contract.py -v`
Expected: FAIL — 404

- [ ] **Step 3: Extend the contract, regenerate, then implement**

Add both paths and schemas to `docs/openapi.yaml`, run `scripts/generate_api.sh`, then write the router as a plain `SELECT` with `.order_by(period_end_date)`. Regenerating before implementing is what keeps the contract authoritative.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/contract/test_companies_contract.py -v` → PASS, then `uv run pytest -v` → PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: companies and financials endpoints, contract-first"
```

---

### Task 2: `GET /api/v1/companies/{id}/coverage` — *Review Focus #1*

**Files:** Create `aicor/api/routers/coverage.py`, `tests/contract/test_coverage_contract.py`; modify `docs/openapi.yaml`

**Interfaces:**
- Consumes: `FeatureRecord`, `FinancialQuarterly`
- Produces: `CoverageResponse(quarters_available, range, by_metric: dict[str, MetricCoverage])`; `MetricCoverage(available: int, missing: list[str], reason: str | None)`

- [ ] **Step 1: Write the failing test**

```python
async def test_coverage_reports_missing_forward_return_with_a_reason(client) -> None:
    # OD-15: the final quarter has no forward return
    assert cov.by_metric["forward_1_quarter_abnormal_return"].reason == "no_subsequent_quarter"

async def test_coverage_never_claims_a_quarter_that_has_no_row(client) -> None:
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/contract/test_coverage_contract.py -v`
Expected: FAIL — 404

- [ ] **Step 3: Extend the contract, regenerate, implement**

One `GROUP BY` per metric; `missing` is the set difference against the full 21-quarter calendar grid, never a guess.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/contract/test_coverage_contract.py -v` → PASS, then `uv run pytest -v` → PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: coverage endpoint so the UI knows which values are NULL and why"
```

---

### Task 3: `GET /api/v1/companies/{id}/segments` and `/events`

**Files:** Create `aicor/api/routers/segments.py`, `aicor/api/routers/events.py`, tests; modify `docs/openapi.yaml`

**Interfaces:**
- Consumes: `SegmentsQuarterly`, `AiEvent`
- Produces: `SegmentResponse`, `EventResponse(event_id, event_date, event_type, tier, source_id, cluster_id, window_start, window_end)`; `GET /api/v1/events/{event_id}/car`

- [ ] **Step 1: Write the failing test**

```python
async def test_every_event_carries_tier_a_or_s_and_a_resolvable_source(client) -> None:
    # EVT_T02
    ...

async def test_overlapping_windows_share_a_cluster_id(client) -> None:
    # OD-11
    ...

async def test_car_reports_its_window_bounds_and_benchmark_version(client) -> None:
    # EVT-03
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/contract/test_events_contract.py -v` → FAIL, 404

- [ ] **Step 3: Extend the contract, regenerate, implement**

`cluster_id` is selected, never computed here. `car` returns the stored values with `window_start`/`window_end` and the benchmark id+version that produced them.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/contract/test_events_contract.py -v` → PASS, then `uv run pytest -v` → PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: segments and events endpoints with cluster grouping exposed"
```

---

### Task 4: `GET /api/v1/analysis` and `/analysis/lag-profile` — *Review Focus #3*

**Files:** Create `aicor/api/routers/analysis.py`, `tests/contract/test_analysis_contract.py`; modify `docs/openapi.yaml`

**Interfaces:**
- Consumes: `AnalysisResult`
- Produces: `AnalysisResponse(analysis_id, analysis_type, metric, value, lag, method, n_observations, ci_low, ci_high, result_class, confidence, status, config_version, feature_ids)`; `LagProfileResponse(relationship, company_id, lags: list[LagPoint])`

- [ ] **Step 1: Write the failing test**

```python
async def test_lag_profile_always_returns_all_five_lags_together(client) -> None:
    # Review Focus #3 / LAG-02: a client must never see one lag in isolation
    assert [p.lag for p in body["lags"]] == [0, 1, 2, 3, 4]

async def test_analysis_rows_carry_n_observations_and_ci(client) -> None:
    # n is ~13, not 21 — the response must not imply more evidence than exists
    assert body["data"][0]["n_observations"] == 13
    assert body["data"][0]["ci_low"] is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/contract/test_analysis_contract.py -v` → FAIL, 404

- [ ] **Step 3: Extend the contract, regenerate, implement**

Both routes are `SELECT`s. The lag-profile route refuses to return a subset: if any lag row is missing it returns the missing lag with `status`/`reason`, never a silently shortened profile.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/contract/test_analysis_contract.py -v` → PASS, then `uv run pytest -v` → PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: analysis endpoints returning the full five-lag profile with CIs and n"
```

---

### Task 5: `GET /api/v1/decision` — *Review Focus #2*

**Files:** Create `aicor/api/routers/decision.py`, `tests/contract/test_decision_contract.py`; modify `docs/openapi.yaml`

**Interfaces:**
- Consumes: `AnalysisResult`, `ScenarioResult`
- Produces: `DecisionResponse(winner, confidence, robustness, key_drivers, sensitivity, limitations)`; `DEC-01` per-company record

- [ ] **Step 1: Write the failing test**

```python
async def test_decision_without_limitations_is_an_error_not_a_confident_answer(client) -> None:
    # Review Focus #2 / NFR-04
    assert r.status_code == 500

async def test_decision_reports_robustness_and_its_reason(client) -> None:
    # ROB-01
    assert body["robustness"] in {"ROBUST", "SENSITIVE"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/contract/test_decision_contract.py -v` → FAIL, 404

- [ ] **Step 3: Extend the contract, regenerate, implement**

`limitations` is declared non-nullable in the contract **and** the handler raises when the stored record's list is empty. Both layers, because the contract alone documents intent while the handler enforces it.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/contract/test_decision_contract.py -v` → PASS, then `uv run pytest -v` → PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: decision endpoint that refuses to answer without limitations"
```

---

### Task 6: `GET /api/v1/companies/{id}/scenarios` and `/data-quality` — *Review Focus #4*

**Files:** Create `aicor/api/routers/scenarios.py`, `aicor/api/routers/quality.py`, tests; modify `docs/openapi.yaml`

**Interfaces:**
- Consumes: `ScenarioResult`, `DataQualityLog`
- Produces: `ScenarioResponse(scenario_code, assumption_class, assumption, financial_effect, efficiency_effect, risk_effect, status, reason)`; `DqCheckResponse(check_id, status, severity, expected, actual, description)`

- [ ] **Step 1: Write the failing test**

```python
async def test_every_scenario_is_labelled_an_assumption(client) -> None:
    # Review Focus #4 / SCN-01..03
    assert all(s["assumption_class"] == "ASSUMPTION" for s in body["data"])

async def test_scenario_effects_needing_an_elasticity_are_null_with_a_reason(client) -> None:
    # OD-12
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/contract/test_scenarios_contract.py -v` → FAIL, 404

- [ ] **Step 3: Extend the contract, regenerate, implement**

`assumption_class` is a required, enum-constrained property with the single value `ASSUMPTION`, so a consumer cannot receive an unlabelled scenario. The data-quality route surfaces `expected`/`actual` so a reviewer can re-verify a failure without shell access.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/contract/test_scenarios_contract.py -v` → PASS, then `uv run pytest -v` → PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: scenarios and data-quality endpoints; scenarios cannot arrive unlabelled"
```

---

### Task 7: Contract drift gate — *Review Focus #5*

**Files:** Create `tests/contract/test_no_drift.py`, `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: `docs/openapi.yaml`, `app.openapi()`
- Produces: a CI job that fails on drift

- [ ] **Step 1: Write the failing test**

```python
def test_emitted_openapi_matches_the_authoritative_artifact() -> None:
    # Review Focus #5
    assert app.openapi() == yaml.safe_load(Path("docs/openapi.yaml").read_text())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/contract/test_no_drift.py -v`
Expected: FAIL on any field the provider added without a contract change

- [ ] **Step 3: Implement the gate**

Wire the drift test, the generator freshness tests (Task 4 of the slice plan) and the full `pytest` suite into CI. CI runs `-m live` on a schedule, not on every push, and the schedule is documented so a skipped live run is never mistaken for a pass.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest -v` → PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "ci: fail on OpenAPI drift between the contract and the provider"
```

---

## Exit Criteria

- [ ] All ten endpoints in the contract return stored values only
- [ ] `docs/openapi.yaml` is the only payload definition anywhere in the repo
- [ ] Generated Pydantic and TypeScript files are current and marked generated
- [ ] `api_contracts.md` contains no payload example
- [ ] No arithmetic exists in `aicor/api/` — proven by source inspection, not review
- [ ] Every response carries `config_version` where a research parameter applies
- [ ] Full suite green

## Hand-off

`2026-10-13-aicor-analysis.md`.