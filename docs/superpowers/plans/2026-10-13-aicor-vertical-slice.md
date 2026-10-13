# AICOR Vertical Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove one number is traceable from a real SEC filing to a dashboard pixel — Microsoft, quarter ending `2025-03-31`, `CapEx/Revenue` — reproducing the SRS §9.3 chain end to end.

**Architecture:** Contract-first (skill `contract-first`). The dashboard's consumer jobs are written first; `docs/openapi.yaml` is the single authoritative boundary artifact; Pydantic models and the TypeScript client are both **generated** from it, so neither side hand-maintains a copy of the payload shape. The API returns **stored values only** — it computes nothing — which is what makes DSH-01 structurally true rather than a review convention.

**Tech Stack:** FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic, `datamodel-code-generator`, `openapi-typescript`, Next.js 15 + React, Vitest, Playwright, pytest.

**Spec:** `SPEC.md` §4.1, §4.5 (FE-04), §5.2 (PRV-01), §6.2, §9.3 · `docs/planning/system_architecture.md` §7 · `docs/planning/data_dictionary_and_provenance.md` §3.5, §3.10 · ADR-0001, ADR-0002, ADR-0006 · `docs/planning/test_and_acceptance_plan.md` Gate A

---

## Global Constraints

- **`docs/openapi.yaml` is the only authoritative description of the API payload shape.** `api_contracts.md` carries rationale and the endpoint→requirement map; it must **not** contain payload examples. Any second copy of a payload shape is a defect.
- **The API performs no aggregation, no ratio, no growth rate.** `CapEx/Revenue` is computed in the feature layer and persisted; the endpoint selects it. A response that computes something is a contract violation (DSH-01, C-1).
- **Every payload carries provenance.** `source_id`, `source_tier`, `source_url`, `verification_status`, `xbrl_tag`, `period_basis`, `config_version` travel with the value.
- **NULL is a value.** Returned as `{"value": null, "status": "...", "reason": "..."}`. Never omitted, never zero, never defaulted.
- **Identifiers are opaque strings.** `feature_id`, `source_id`, `accession_number` are strings and must never be coerced to numbers anywhere in the pipeline or the client.
- **Money: USD millions. Ratios and growth: decimal fractions.** The client renders; it never rescales.
- **`period_end_date` is the join key**; `fiscal_period` is display-only (DAT-01).
- **Slice scope is fixed:** MSFT, `period_end_date = 2025-03-31`, fiscal label `FY25Q3`, 10-Q accession `0001193125-25-061046`. Revenue, R&D, CapEx, `CapEx/Revenue`. Nothing else ships in this plan.
- **`web/` may not compute.** No arithmetic on API data anywhere in the frontend — display formatting only. Guarded by an ESLint rule and a source-inspection test (DSH_T01).
- **No secrets reach the browser.** No environment variable other than a base URL is exposed to the client.

---

## Review Focus

| # | Failure mode | Expected behaviour | Pinned in |
|---|---|---|---|
| 1 | **A NULL with no reason renders as a blank cell or a `0`**, which reads as "zero investment" | NULL renders with its machine-readable reason, never a zero | Task 6 |
| 2 | **Frontend computes `capex / revenue` itself** because the value is inconvenient to select | Client has no arithmetic on API data; lint rule fails the build | Task 6 |
| 3 | **BigInt `feature_id`/`source_id` loses precision in JS** — a rounded ID still looks valid | IDs stay strings end to end | Task 4, Task 5 |
| 4 | **`docs/openapi.yaml` and the FastAPI-emitted schema drift** after a provider edit | CI diffs emitted vs canonical and fails on any difference | Task 5 |
| 5 | **The §9.3 chain has a manual step** — provenance is reconstructable but not machine-resolvable | `/provenance/{source_id}` returns the whole walk in one response | Task 4 |

---

## File Structure

```
docs/openapi.yaml                      # AUTHORITATIVE boundary artifact
aicor/api/
  schemas_generated.py                 # GENERATED from openapi.yaml — do not edit
  app.py                               # app factory
  dependencies.py                      # DbDep type alias
  routers/
    features.py
    provenance.py
  services/
    feature_service.py                 # selects stored rows; computes nothing
web/
  src/generated/api.ts                 # GENERATED from openapi.yaml — do not edit
  src/lib/format.ts                    # the ONLY place numbers are formatted
  src/app/.../page.tsx
tests/
  contract/
  e2e/
migrations/versions/0003_features.py
```

---

### Task 1: Migration 0003 — `features_quarterly`, `analysis_results`, `data_quality_log`

**Files:**
- Create: `migrations/versions/0003_features.py`, `tests/integration/test_migration_0003.py`, extend `aicor/db/models.py`

**Interfaces:**
- Consumes: `FinancialQuarterly`, `Company` (data-spine Tasks 2–3)
- Produces: `FeatureRecord`, `AnalysisResult`, `DataQualityLog`; migration `0003`

- [ ] **Step 1: Write the failing test**

```python
def test_feature_rejects_null_value_without_a_reason(db_session) -> None:
    # SRC-05 / R4: absence must always be explained
    ...

def test_feature_requires_definition_and_calculation_method(db_session) -> None:
    # PRV-01
    ...

def test_feature_is_unique_per_company_quarter_and_feature(db_session) -> None:
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/integration/test_migration_0003.py -v`
Expected: FAIL — `UndefinedTable` (relation `"features_quarterly"` does not exist)

- [ ] **Step 3: Implement revision `0003`**

`features_quarterly`: PK `feature_id`; unique `(company_id, period_end_date, feature)`; FK to `source_registry.source_id`; NOT NULL `definition`, `calculation_method`, `reported_or_derived`, `confidence`, `status`, `config_version`; `input_feature_ids` JSONB; CHECK `(status = 'ok' OR reason IS NOT NULL)` — **the schema itself enforces that a NULL carries a reason.**

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run alembic upgrade head && uv run pytest -v` → PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: migration 0003 feature store enforcing NULL-with-reason at the schema level"
```

---

### Task 2: Feature computation — `CapEx/Revenue`

**Files:**
- Create: `aicor/features/intensity.py`, `aicor/features/base.py`, `tests/unit/test_capex_intensity.py`

**Interfaces:**
- Consumes: `FinancialQuarterly` (data-spine Task 9 output), `config.research_params`
- Produces:
  - `FeatureDraft(feature: str, value: Decimal | None, unit: str, definition: str, calculation_method: str, reported_or_derived: Literal["reported","derived","proxy"], proxy: bool, confidence: Literal["HIGH","MEDIUM","LOW"], status: str, reason: str | None, input_feature_ids: tuple[str, ...])`
  - `capex_intensity(capex: Decimal, revenue: Decimal) -> FeatureDraft`
  - `build_feature_id(company_id: str, feature: str, period_end: date) -> str` → `"{company_id}_{feature}_{YYYY}Qn"`

- [ ] **Step 1: Write the failing test**

```python
def test_capex_intensity_is_capex_divided_by_revenue() -> None: ...

def test_zero_revenue_yields_null_with_a_reason_not_an_error() -> None:
    d = capex_intensity(Decimal("1000"), Decimal("0"))
    assert d.value is None
    assert d.reason == "revenue_zero"

def test_result_is_labelled_derived_and_never_reported() -> None:
    d = capex_intensity(Decimal("1000"), Decimal("4000"))
    assert d.reported_or_derived == "derived"
    assert d.calculation_method == "capex / revenue"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_capex_intensity.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'aicor.features'`

- [ ] **Step 3: Implement `aicor/features/intensity.py`**

`capex_intensity` returns a `FeatureDraft`; it never raises on a zero denominator — it returns NULL plus reason, because SRC-05 requires an explained absence rather than an exception that halts the pipeline. `confidence = MEDIUM` per SRC-06 (derived). `unit = "ratio"`. The division uses `Decimal`, and `capex` arrives already sign-normalised from the data-spine plan.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_capex_intensity.py -v` → PASS, then `uv run pytest -v` → PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: capex_intensity feature with explained-NULL semantics (FE-04)"
```

---

### Task 3: Consumer jobs, then the authoritative contract

`contract-first` requires the consumer to state what it needs before the provider exists. Task 6 (the dashboard) is written here as its job list; the schema below exists to satisfy it.

**Files:**
- Create: `docs/openapi.yaml`, `docs/planning/api_contracts.md` (rewrite), `tests/contract/test_openapi_valid.py`

**Interfaces:**
- Consumes: `FeatureDraft` (Task 2), `SourceRegistry`
- Produces: `docs/openapi.yaml` with paths `GET /api/v1/companies/{company_id}/features` and `GET /api/v1/provenance/{source_id}`

- [ ] **Step 1: Write the failing test**

```python
def test_openapi_is_valid_and_declares_the_two_slice_endpoints() -> None: ...

def test_feature_schema_declares_null_with_reason_not_bare_null() -> None:
    # C-3: value, status and reason are all required properties
    ...

def test_feature_schema_carries_every_provenance_field() -> None:
    # PRV-01 + NFR-02
    required = {"source_id","source_tier","source_url","verification_status",
                "xbrl_tag","period_basis","definition","calculation_method",
                "reported_or_derived","confidence","config_version","status","reason"}
    assert required <= set(schemas["Feature"].get("required", []))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/contract/test_openapi_valid.py -v`
Expected: FAIL — `FileNotFoundError: docs/openapi.yaml`

- [ ] **Step 3: Write `docs/openapi.yaml`, then rewrite `api_contracts.md`**

The contract declares, for `Feature`: `feature_id` (string), `company_id`, `period_end_date` (date), `fiscal_period`, `calendar_quarter`, `feature`, `value` (`number | null`), `unit`, `definition`, `calculation_method`, `reported_or_derived`, `proxy`, `confidence`, `status`, `reason` (`string | null`), and a nested `source` object with the provenance fields above.

**`api_contracts.md` is rewritten in the same step** to contain only: the consumer-job list, the endpoint→requirement→dashboard map, and design rationale. **All JSON payload examples are deleted from it**, because the OpenAPI file is the single source of truth and a second copy can drift.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/contract/test_openapi_valid.py -v` → PASS, then `uv run pytest -v` → PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: authoritative openapi.yaml plus consumer jobs; remove duplicate payloads from api_contracts.md"
```

---

### Task 4: Generate schemas and client from the contract

**Files:**
- Create: `aicor/api/schemas_generated.py`, `web/src/generated/api.ts`, `scripts/generate_api.sh`, `tests/contract/test_generated_is_current.py`

**Interfaces:**
- Consumes: `docs/openapi.yaml` (Task 3)
- Produces: `aicor.api.schemas_generated.Feature`, `ProvenanceResponse`, `ApiError`; `web/src/generated/api.ts`

- [ ] **Step 1: Write the failing test**

```python
def test_generated_python_is_current_with_the_contract() -> None:
    # regenerating must produce no diff
    ...

def test_generated_ts_is_current_with_the_contract() -> None:
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/contract/test_generated_is_current.py -v`
Expected: FAIL — generated files absent

- [ ] **Step 3: Implement `scripts/generate_api.sh` and run it**

Pin both generators. `datamodel-code-generator` → `aicor/api/schemas_generated.py`; `openapi-typescript` → `web/src/generated/api.ts`. Per `contract-first`, generators run with least privilege: no network, no secrets, and write access only to those two paths. **Both generated files carry a header marking them generated — a hand edit must be impossible to merge silently.**

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/contract/test_generated_is_current.py -v` → PASS, then `uv run pytest -v` → PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: generate Pydantic schemas and TS client from the single authoritative contract"
```

---

### Task 5: FastAPI providers that match the contract

**Files:**
- Create: `aicor/api/app.py`, `aicor/api/dependencies.py`, `aicor/api/routers/features.py`, `aicor/api/routers/provenance.py`, `aicor/api/services/feature_service.py`, `tests/contract/test_provider_matches_contract.py`

**Interfaces:**
- Consumes: `Feature`, `ProvenanceResponse` (Task 4), `FeatureRecord`
- Produces: `GET /api/v1/companies/{company_id}/features` and `GET /api/v1/provenance/{source_id}`; `FeatureService.list_features(company_id, feature, session) -> list[FeatureRecord]`

- [ ] **Step 1: Write the failing test**

```python
async def test_features_endpoint_matches_the_contract(client) -> None:
    r = await client.get("/api/v1/companies/MSFT/features?feature=capex_intensity")
    assert r.status_code == 200
    validate(r.json(), contract["paths"][...])   # runtime validation, not just types

async def test_null_value_is_returned_with_status_and_reason(client) -> None:
    # C-3
    ...

async def test_provenance_returns_the_whole_section_9_3_walk(client) -> None:
    # Review Focus #5
    ...

async def test_no_endpoint_performs_aggregation() -> None:
    # DSH-01 / API_T03 — source inspection of the service layer
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/contract/test_provider_matches_contract.py -v`
Expected: FAIL — 404 (route does not exist)

- [ ] **Step 3: Implement the routers**

App factory with `lifespan`; `DbDep = Annotated[AsyncSession, Depends(get_db)]`; `response_model` declared on **every** route. `FeatureService` performs `SELECT` and row→schema mapping only — it must contain no division, no percentage, no aggregation. Deterministic ordering: `.order_by(FinancialQuarterly.period_end_date)`.

A CI check compares FastAPI's emitted `app.openapi()` against `docs/openapi.yaml` and fails on any difference (Review Focus #4).

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/contract/test_provider_matches_contract.py -v` → PASS, then `uv run pytest -v` → PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: read-only providers validated against the contract; no aggregation in the API"
```

---

### Task 6: Dashboard panel that renders without computing — *Review Focus #1 and #2*

**Files:**
- Create: `web/src/lib/format.ts`, `web/src/components/ProvenanceLink.tsx`, `web/src/components/FeaturePanel.tsx`, the page, `web/eslint.config.js`, `web/src/__tests__/FeaturePanel.test.tsx`, `web/tests/e2e/slice.spec.ts`

**Interfaces:**
- Consumes: generated `web/src/generated/api.ts` (Task 4)
- Produces: `formatRatio(value: number | null): string`, `formatUsdMillions(value: number | null): string`, `formatPercent(value: number | null): string`

- [ ] **Step 1: Write the failing tests**

```tsx
it("renders a reason, not a zero, when the value is null", () => {
  render(<FeaturePanel feature={{ value: null, status: "unavailable",
                                reason: "denominator_near_zero" }} />)
  expect(screen.getByText(/denominator_near_zero/)).toBeInTheDocument()
  expect(screen.queryByText("0")).not.toBeInTheDocument()   // Review Focus #1
})
```

```ts
// Review Focus #2 — a lint rule, not a review convention
it("fails the build if client code does arithmetic on API data", () => {
  const r = runEslint("web/src/**/*.tsx")
  expect(r.errorCount).toBe(0)
})
```

E2E: click a headline number → the provenance panel shows `source_url` and `accession_number`.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && npm run test` → FAIL (component missing); `npm run lint` → FAIL (no rule yet)

- [ ] **Step 3: Implement the panel and the lint rule**

`format.ts` is the only module permitted to touch a numeric value, and only to append `%` or group thousands. The ESLint rule bans arithmetic operators on identifiers whose name matches API response shapes, and bans any import of a statistics or math helper in `web/src/`. `ProvenanceLink` calls `/api/v1/provenance/{source_id}` and renders `source_url` plus `verification_status`.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd web && npm run test` → PASS; `npm run lint` → PASS
Run: `npx playwright test tests/e2e/slice.spec.ts` → PASS
Then `uv run pytest -v` → PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: dashboard panel renders stored values only, with a lint guard against client computation"
```

---

### Task 7: Provenance walk and reproducibility double-run

**Files:**
- Create: `tests/audit/test_section_9_3_chain.py`, `tests/audit/test_reproducibility.py`, `docs/planning/slice_acceptance.md`

**Interfaces:**
- Consumes: everything above
- Produces: `docs/planning/slice_acceptance.md` — the recorded evidence for Gate A

- [ ] **Step 1: Write the failing test**

```python
def test_every_value_on_the_panel_resolves_to_a_sec_filing() -> None:
    # SRS 9.3: Dashboard -> Analysis Result -> Feature -> Calculation ->
    #           Raw Data -> Source ID -> Source URL -> SEC disclosure
    ...

def test_two_clean_runs_produce_identical_analysis_rows() -> None:
    # NFR-01 / NFR_T01
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/audit/ -v`
Expected: FAIL — provenance does not yet resolve end to end

- [ ] **Step 3: Implement the audit and record the evidence**

Walk the chain from the rendered feature value through `input_feature_ids`, the raw snapshot's SHA-256, `source_registry.source_url`, and the filing accession. Re-run the pipeline into a second schema and compare `features_quarterly` and `analysis_results` row by row. Write the actual output — accession number, URL, SHA-256, computed value — into `docs/planning/slice_acceptance.md`.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest -v` → PASS; `uv run pytest tests/audit/ -v` → PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "test: prove the SRS 9.3 provenance chain and NFR-01 reproducibility for the slice"
```

---

## Exit Criteria — Gate A

- [ ] A1 — MSFT `2025-03-31`: Revenue, R&D, CapEx present with a Tier S `source_id`
- [ ] A2 — `CapEx/Revenue` computed in the feature layer and stored, **not** in the client
- [ ] A3 — the API returns it with full provenance
- [ ] A4 — one panel renders it, clickable to `source_url`
- [ ] A5 — **§9.3 chain walks end to end**, evidenced in `slice_acceptance.md`
- [ ] A6 — a reviewer reproduces the value on a clean re-run (NFR-01)
- [ ] A7 — `DQ_T04` passes for this quarter
- [ ] A8 — no mock data anywhere in the path
- [ ] `docs/openapi.yaml` is the only payload definition; `api_contracts.md` contains no payload example

## Hand-off

Next plans: `2026-10-13-aicor-api-contract.md` (remaining endpoints), `2026-10-13-aicor-analysis.md` (blocked on OD-02/03/04/05/12).