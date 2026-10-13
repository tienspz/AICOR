# AICOR Data Spine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the evidence spine — SEC filing discovery, immutable raw storage, period-aware XBRL tag resolution, cumulative-to-quarterly derivation, and executable data-quality checks — so that 21 quarters of real financial data for MSFT and GOOGL exist in PostgreSQL with complete provenance.

**Architecture:** API-first ingestion (ADR-0003) into a content-addressed immutable raw layer (I-2). Facts are attributed to real filing accessions (I-4), resolved to a logical metric **per period** (ADR-0004), derived from cumulative durations by one uniform algorithm used for both companies (ADR-0005), then checked by DQ-01…DQ-05. A missing tag **fails loudly**; it never skips.

**Tech Stack:** Python 3.14, `uv`, SQLAlchemy 2.x, Alembic, PostgreSQL 16, pytest, httpx, pydantic-settings.

**Spec:** `SPEC.md` (AICOR-SRS) §3.1–3.6, §4.1, §5.1, §6.2 · `docs/planning/system_architecture.md` §3–5 · `docs/planning/data_dictionary_and_provenance.md` · ADRs 0003, 0004, 0005 · `docs/planning/test_and_acceptance_plan.md` §3.1–3.4

---

## Global Constraints

- **Python 3.14.** Package manager is `uv`; `uv.lock` is committed and is the reproducibility anchor (NFR-01).
- **Money unit: USD millions.** Store `Decimal`, never `float`. Ratios, growth rates and returns are **decimal fractions** (`0.3725` = 37.25 %), never percent-scaled.
- **`capex` is stored positive.** Sign normalisation happens before derivation; the raw sign survives only in the raw snapshot. DQ-02 depends on this.
- **`capex` definition = cash purchases of property and equipment** (`PaymentsToAcquirePropertyPlantAndEquipment`), **excluding finance leases**; the definition string is stored on every row (FR-03, OD-09).
- **The join key across companies is `period_end_date`.** `fiscal_period` is display-only (DAT-01, I-5). Both companies have 21 quarter-ends: `2021-06-30` … `2026-06-30`.
- **SEC User-Agent is mandatory** and must identify the project and a contact address. SEC allows ≤10 requests/second; the client enforces a token bucket and exponential backoff with jitter on 429/5xx.
- **Never fabricate, never estimate, never interpolate.** A value that cannot be sourced is `NULL` + `status` + `reason` (SRC-05). A missing tag for a required quarter is an **ERROR that fails the run**, never a skip (ADR-0004).
- **The raw layer is write-once.** `write_raw()` refuses to overwrite an existing hash (I-2).
- **No research parameter may be a code literal.** Anything numeric that expresses a research judgement lives in `config/research_params.yaml` with a `config_version` (I-6, ADR-0006). This plan introduces **no** such parameter — it only reads `dq.tolerance_assets_liab_equity` and `rate_limit.requests_per_second`.
- **No secrets in code or logs.** `DATABASE_URL` and `SEC_USER_AGENT` come from the environment via `pydantic-settings`.

---

## Review Focus

The five failure modes below are implied by the spec, are the most likely to bite, and are each pinned to a named task by a named test.

| # | Failure mode | Expected behaviour | Pinned in |
|---|---|---|---|
| 1 | **Alphabet's ASC 606 revenue tag stops at `2025-03-31`** while `Revenues` continues — a per-company tag silently loses 5 quarters with no error | Resolution is per `(company, period)`; unresolved required quarter raises | Task 7 |
| 2 | **Q4 has no 10-Q**, so no 3-month cash-flow fact exists for any company; `2026-06-30` exists only as an FY duration | Q4 = `FY − 9M`; Q4 is never populated from a 3-month fact | Task 8 |
| 3 | **Cash-flow statements report CapEx negative**, so a naive load makes `capex >= 0` (DQ-02) fail on correct data | Sign normalised at load, before derivation | Task 9 |
| 4 | **MSFT's fiscal year runs Jul–Jun**, so its Q1 is Jul–Sep; treating fiscal quarter as calendar quarter mislabels every period | Fiscal quarter derived from `period_end_date` + `fiscal_year_end` | Task 8 |
| 5 | **Yahoo omits non-trading days and can return a null `adjclose`**; an interpolating or unvalidated load produces plausible-but-wrong returns | Missing dates recorded, not filled; `adjusted_close` non-null asserted per bar | Task 11 |

---

## File Structure

```
aicor/
  settings.py              # pydantic-settings; all env access in one place
  db/
    session.py             # engine + session_scope
    models.py              # SQLAlchemy ORM models
  raw/
    store.py               # content-addressed write-once store
    manifest.py            # raw_manifest repository
  ingest/
    ratelimit.py           # token bucket + backoff
    connectors/
      sec.py               # submissions + companyconcept
      market.py            # Yahoo chart API
    normalize/
      tags.py              # metric -> candidate tag table + per-period resolver
      signs.py             # sign convention
    derive/
      durations.py         # period_basis classification + quarterly algebra
  quality/
    checks.py              # DQ-01..DQ-05
  cli.py                   # pipeline entrypoints
migrations/                # Alembic
tests/
  conftest.py
  integration/
  unit/
config/research_params.yaml
docker-compose.yml
```

---

### Task 1: Green test harness, settings, and a reachable database

The first task's deliverable is a **passing test suite and a reachable database**, not an empty scaffold. Everything later depends on it.

**Files:**
- Create: `pyproject.toml`, `docker-compose.yml`, `.env.example`, `aicor/settings.py`, `aicor/db/session.py`, `tests/conftest.py`, `tests/integration/test_database.py`

**Interfaces:**
- Consumes: nothing (first task)
- Produces:
  - `aicor.settings.Settings` — pydantic-settings; fields `database_url: str`, `sec_user_agent: str`, `raw_dir: Path`
  - `aicor.db.session.get_engine() -> Engine`
  - `aicor.db.session.session_scope() -> Iterator[Session]` (context manager, commits on success, rolls back on exception)
  - `tests/conftest.py` fixture `db_session: Session`

- [ ] **Step 1: Write the failing test**

`tests/integration/test_database.py`:

```python
def test_session_scope_can_round_trip_a_query(db_session: Session) -> None:
    with session_scope() as session:
        assert session.execute(text("SELECT 1")).scalar_one() == 1
```

`tests/test_settings.py`:

```python
def test_settings_require_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError):
        Settings()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/ -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'aicor'`

- [ ] **Step 3: Implement `aicor/settings.py` and `aicor/db/session.py`**

`Settings` subclasses `BaseSettings` with `model_config = SettingsConfigDict(env_file=".env")`. Fields as listed above; no defaults for `database_url` and `sec_user_agent` so a missing value fails loudly at startup.

`get_engine()` builds `create_engine(settings.database_url, pool_pre_ping=True)`, cached with `functools.lru_cache`. `session_scope()` is a `@contextmanager` yielding a `Session`, committing on clean exit and rolling back on exception.

- [ ] **Step 4: Run test to verify it passes**

Run: `docker compose up -d db && uv run pytest tests/ -v`
Expected: PASS
Then run the **full suite**: `uv run pytest -v` → PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock docker-compose.yml .env.example aicor/ tests/
git commit -m "feat: project skeleton with green test harness and DB connection"
```

---

### Task 2: Migration 0001 — `companies`, `filing`, `raw_manifest`

**Migrations follow TDD** (author decision, 2026-10-13): a migration is not a declaration, it is a constraint that must be proven to reject bad data.

**Files:**
- Create: `migrations/versions/0001_registry.py`, `aicor/db/models.py` (these three models only), `tests/integration/test_migration_0001.py`

**Interfaces:**
- Consumes: `aicor.db.session.session_scope`, `Settings`
- Produces: `aicor.db.models.Company`, `Filing`, `RawManifest` — tables `companies`, `filing`, `raw_manifest`

- [ ] **Step 1: Write the failing test**

```python
def test_filing_rejects_a_period_before_its_filing_date(db_session: Session) -> None:
    # a 10-Q cannot be filed before the period it reports
    ...

def test_raw_manifest_rejects_duplicate_sha256(db_session: Session) -> None:
    # identity of a raw snapshot is its hash; two rows cannot share one
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/integration/test_migration_0001.py -v`
Expected: FAIL — `UndefinedTable` (relation `"filing"` does not exist)

- [ ] **Step 3: Implement the Alembic revision `0001`**

Three tables per `data_dictionary_and_provenance.md` §3.1–3.4. Required constraints:

- `companies.company_id` PK, `cik` unique
- `filing.accession_number` PK; CHECK `(form IN ('10-Q','10-K'))`; CHECK `(filing_date >= period_end)`
- `raw_manifest.sha256` unique; `byte_size` NOT NULL

ORM models mirror the columns with `Mapped[...]` annotations.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run alembic upgrade head && uv run pytest tests/ -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add migrations/ aicor/db/models.py tests/integration/test_migration_0001.py
git commit -m "feat: migration 0001 registry tables with constraints proven by test"
```

---

### Task 3: Migration 0002 — quarterly facts and provenance tables

**Files:**
- Create: `migrations/versions/0002_quarterly_facts.py`, tests

**Interfaces:**
- Consumes: `Company` (Task 2)
- Produces: `FinancialQuarterly`, `SegmentsQuarterly`, `MarketDaily`, `AiEvent`; migration `0002`

- [ ] **Step 1: Write the failing test**

```python
def test_financial_quarterly_rejects_two_rows_for_one_calendar_quarter(db_session) -> None:
    # DAT-01 / I-5: (company_id, period_end_date) must be unique, so MSFT FY26Q3
    # and GOOGL 2026Q1 both ending 2026-03-31 cannot collide on one company
    ...

def test_financial_quarterly_rejects_negative_capex(db_session) -> None:
    # DQ-02
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/integration/test_migration_0002.py -v`
Expected: FAIL — `UndefinedTable`

- [ ] **Step 3: Implement revision `0002`**

`financial_quarterly`: composite PK `(company_id, period_end_date)`; columns per dictionary §3.5 including `fiscal_period`, `calendar_quarter`, `capex_definition`; CHECK `capex >= 0`, CHECK `revenue >= 0`; nullable value columns paired with NOT NULL `status`, and `reason` required when `status <> 'ok'`.
`market_daily`: PK `(company_id, date)`, `adjusted_close` nullable, `volume`.
`ai_events`: `event_id` PK, `cluster_id` nullable (OD-11), `window_start`/`window_end` nullable.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run alembic upgrade head && uv run pytest -v` → PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: migration 0002 quarterly facts, enforcing the calendar-quarter join key"
```

---

### Task 4: Content-addressed raw store and manifest

**Files:**
- Create: `aicor/raw/store.py`, `aicor/raw/manifest.py`, `tests/unit/test_raw_store.py`

**Interfaces:**
- Consumes: `Settings.raw_dir`, `RawManifest` (Task 2)
- Produces:
  - `RawRef(raw_id: str, sha256: str, storage_path: Path)`
  - `write_raw(data: bytes, *, source_id: str, ext: str) -> RawRef` — **write-once**; identical bytes return the existing `RawRef` without rewriting
  - `read_raw(sha256: str) -> bytes`

- [ ] **Step 1: Write the failing test**

```python
def test_write_raw_is_idempotent_for_identical_bytes(tmp_path: Path) -> None: ...
def test_write_raw_never_overwrites_an_existing_hash(tmp_path: Path) -> None: ...
def test_modified_bytes_produce_a_new_sha256(tmp_path: Path) -> None: ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_raw_store.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'aicor.raw'`

- [ ] **Step 3: Implement `aicor/raw/store.py`**

Layout: `raw_dir / sha256[:2] / f"{sha256}.{ext}"`. If the file exists, read and compare bytes; identical → return existing `RawRef` (no write, no duplicate manifest row); different → that is a hash collision and must raise. Otherwise write atomically (temp file + rename) and insert the manifest row.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_raw_store.py -v` → PASS, then `uv run pytest -v` → PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: write-once content-addressed raw store with SHA-256 manifest"
```

---

### Task 5: Rate limiter and SEC `submissions` connector

**Files:**
- Create: `aicor/ingest/ratelimit.py`, `aicor/ingest/connectors/sec.py`, `tests/unit/test_ratelimit.py`, `tests/integration/test_sec_submissions.py`

**Interfaces:**
- Consumes: `Settings.sec_user_agent`, `write_raw`, `Filing`, `Company`
- Produces:
  - `FilingRef(cik, form, period_end, filing_date, accession_number, primary_document)`
  - `SecClient(settings: Settings)` with `submissions(cik: str) -> list[FilingRef]` and `company_concept(cik: str, tag: str) -> list[XbrlFact]` (`company_concept` lands in Task 6)
  - `XbrlFact(start: date | None, end: date, val: Decimal, unit: str, accession_number: str, form: str)` — declared here, populated in Task 6

- [ ] **Step 1: Write the failing test**

```python
def test_token_bucket_blocks_requests_over_the_configured_rate() -> None: ...
def test_client_retries_with_backoff_on_429(monkeypatch) -> None: ...
```

`tests/integration/test_sec_submissions.py` — the regression guard for ADR-0003/I-4:

```python
@pytest.mark.live
def test_discovers_the_two_accessions_named_in_the_srs() -> None:
    filings = SecClient(settings).submissions("0000789019")
    ref = next(f for f in filings if f.accession_number == "0001193125-26-191507")
    assert (ref.period_end, ref.form) == (date(2026, 3, 31), "10-Q")

@pytest.mark.live
def test_discovers_the_alphabet_accession_named_in_the_srs() -> None:
    filings = SecClient(settings).submissions("0001652044")
    assert any(f.accession_number == "0001652044-26-000071" and f.period_end == date(2026, 6, 30)
               for f in filings)
```

> These two assertions pin **ADR-0003**: filings are discovered from the API, never hard-coded. If a hard-coded list were used instead, this test would pass vacuously — so also assert the count of 10-Q/10-K filings in the 2021-06-30…2026-06-30 range is non-zero and derived from the response.

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_ratelimit.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'aicor.ingest'`

- [ ] **Step 3: Implement**

`ratelimit.py`: `TokenBucket(rate: float, capacity: float)` with `acquire()`. Rate read from `config/research_params.yaml` key `rate_limit.requests_per_second`, **never** a literal (I-6).

`sec.py`: `SecClient` sends `User-Agent: settings.sec_user_agent` on every request; wraps each response body in `write_raw(...)` before parsing; retries on 429/5xx with exponential backoff + jitter; parses `filings.recent` zipped across `form`, `filingDate`, `reportDate`, `accessionNumber`, `primaryDocument` into `FilingRef`, reading older shards when present.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_ratelimit.py -v` → PASS
Run: `uv run pytest tests/integration/test_sec_submissions.py -v -m live` → PASS (requires network)
Then `uv run pytest -v` → PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: SEC submissions connector with rate limiting and discovery-based accessions"
```

---

### Task 6: SEC `companyconcept` connector

**Files:**
- Create: `tests/integration/test_sec_company_concept.py`, extend `aicor/ingest/connectors/sec.py`

**Interfaces:**
- Consumes: `SecClient`, `write_raw`, `XbrlFact` (Task 5), `Filing`
- Produces: `SecClient.company_concept(cik: str, tag: str) -> list[XbrlFact]`; every fact carries the `accession_number` it came from

- [ ] **Step 1: Write the failing test**

```python
@pytest.mark.live
def test_every_fact_is_attributable_to_a_known_filing() -> None:
    facts = SecClient(settings).company_concept("0001652044", "Revenues")
    known = {f.accession_number for f in SecClient(settings).submissions("0001652044")}
    assert facts and all(f.accession_number in known for f in facts)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/integration/test_sec_company_concept.py -v -m live`
Expected: FAIL — `AttributeError: 'SecClient' object has no attribute 'company_concept'`

- [ ] **Step 3: Implement `company_concept`**

GET `https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{tag}.json`. Wrap the body in `write_raw`. Parse `units` → each entry into `XbrlFact` with `start`/`end`/`val`/`unit`/`accn`/`form`. `val` → `Decimal(str(...))` (never float). Attach the SEC-provided `User-Agent` via the shared client.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/integration/test_sec_company_concept.py -v -m live` → PASS
Then `uv run pytest -v` → PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: SEC companyconcept connector with fact-level filing attribution"
```

---

### Task 7: Period-aware tag resolution — *Review Focus #1*

**Files:**
- Create: `aicor/ingest/normalize/tags.py`, `tests/unit/test_tag_resolution.py`

**Interfaces:**
- Consumes: `XbrlFact`
- Produces:
  - `ResolvedTag(company_id, metric, tag, period_end, source_id)`
  - `TagResolutionError(company_id, metric, period_end, tried: tuple[str, ...])`
  - `CANDIDATE_TAGS: dict[str, tuple[str, ...]]` — metric → ordered candidates (dictionary §6)
  - `resolve_tag(company_id: str, metric: str, period_end: date, facts_by_tag: Mapping[str, Sequence[XbrlFact]]) -> ResolvedTag`

- [ ] **Step 1: Write the failing test**

```python
def test_falls_back_to_secondary_tag_when_primary_stops_reporting() -> None:
    # Review Focus #1: GOOGL's ASC 606 tag has no fact for 2026-06-30
    facts = {"RevenueFromContractWithCustomerExcludingAssessedTax": [], "Revenues": [_fact(end=date(2026, 6, 30))]}
    assert resolve_tag("GOOGL", "revenue", date(2026, 6, 30), facts).tag == "Revenues"

def test_raises_instead_of_skipping_when_no_tag_reports_the_period() -> None:
    with pytest.raises(TagResolutionError):
        resolve_tag("GOOGL", "revenue", date(2026, 6, 30), {"Revenues": []})

@pytest.mark.live
def test_yields_21_non_null_revenue_quarters_per_company() -> None:
    # FR_T01
    assert len(resolve_all("MSFT", "revenue", WINDOW)) == 21
    assert len(resolve_all("GOOGL", "revenue", WINDOW)) == 21
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_tag_resolution.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'aicor.ingest.normalize'`

- [ ] **Step 3: Implement `aicor/ingest/normalize/tags.py`**

`CANDIDATE_TAGS` carries, for `revenue`, the ordered tuple `("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueNet")` — one shared tuple for both companies, because **resolution is per period, not per company** (ADR-0004). `resolve_tag` picks the first candidate with at least one fact whose `end == period_end`; if none, raises `TagResolutionError` carrying the candidate list. No caller may catch it and continue.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_tag_resolution.py -v` → PASS
Run: `uv run pytest tests/unit/test_tag_resolution.py -v -m live` → PASS (FR_T01)
Then `uv run pytest -v` → PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: per-period XBRL tag resolution that fails loudly on a missing tag"
```

---

### Task 8: Cumulative-to-quarterly derivation — *Review Focus #2 and #4*

**Files:**
- Create: `aicor/ingest/derive/durations.py`, `tests/unit/test_quarterly_derivation.py`

**Interfaces:**
- Consumes: `XbrlFact`, `ResolvedTag`
- Produces:
  - `PeriodBasis = Literal["3M", "6M", "9M", "FY", "instant"]`
  - `classify_duration(start: date, end: date) -> PeriodBasis`
  - `fiscal_quarter(period_end: date, fiscal_year_end_month_day: str) -> int` — MSFT `"06-30"` → Q1 for a Sep period end
  - `derive_quarter(facts: Sequence[XbrlFact], fiscal_year_end: str) -> Decimal` — Q1=`3M`, Q2=`6M−3M`, Q3=`9M−6M`, Q4=`FY−9M`

- [ ] **Step 1: Write the failing test**

```python
def test_q4_is_annual_minus_nine_months() -> None: ...          # Review Focus #2
def test_q4_is_never_sourced_from_a_three_month_fact() -> None: ...   # Review Focus #2
def test_msft_fiscal_q1_is_the_july_to_september_period() -> None: ...  # Review Focus #4
def test_q2_equals_six_months_minus_three_months() -> None: ...
@pytest.mark.live
def test_msft_direct_three_month_facts_agree_with_derived_values() -> None:
    # DER_T06
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_quarterly_derivation.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'aicor.ingest.derive'`

- [ ] **Step 3: Implement `aicor/ingest/derive/durations.py`**

`classify_duration` maps day-span to basis: 80–100 → `3M`, 170–200 → `6M`, 250–290 → `9M`, 350–380 → `FY`, no `start` → `instant`. `fiscal_quarter` computes the offset from `fiscal_year_end_month_day` to `period_end` modulo 4. `derive_quarter` requires exactly the durations its quarter needs and raises `DurationNotAvailable(missing)` rather than substituting — which is what makes "Q4 never from a 3-month fact" structurally true.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_quarterly_derivation.py -v` → PASS
Run: `uv run pytest tests/unit/test_quarterly_derivation.py -v -m live` → PASS (DER_T06)
Then `uv run pytest -v` → PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: uniform cumulative-to-quarterly derivation for both companies"
```

---

### Task 9: Sign normalisation — *Review Focus #3*

**Files:**
- Create: `aicor/ingest/normalize/signs.py`, `tests/unit/test_signs.py`

**Interfaces:**
- Consumes: `XbrlFact`
- Produces: `CAPEX_SIGN_FLIP: frozenset[str] = frozenset({"PaymentsToAcquirePropertyPlantAndEquipment"})`; `normalise_sign(metric: str, value: Decimal) -> Decimal`

- [ ] **Step 1: Write the failing test**

```python
def test_capex_reported_negative_is_stored_positive() -> None:
    # Review Focus #3: cash-flow statements present CapEx as an outflow
    assert normalise_sign("capex", Decimal("-5000")) == Decimal("5000")

def test_revenue_sign_is_left_alone() -> None:
    assert normalise_sign("revenue", Decimal("5000")) == Decimal("5000")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_signs.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement `signs.py`**

Flip the sign only for metrics whose SEC tag is an investing-outflow line. Returns `Decimal` unchanged otherwise. The stored `capex_definition` string records that finance leases are excluded, so a reader can see both the sign convention and the scope.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_signs.py -v` → PASS, then `uv run pytest -v` → PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: normalise CapEx sign to positive before derivation (DQ-02)"
```

---

### Task 10: Data-quality checks DQ-01…DQ-05

**Files:**
- Create: `aicor/quality/checks.py`, `aicor/quality/log.py`, `tests/unit/test_dq_checks.py`, `tests/integration/test_dq_against_real_data.py`

**Interfaces:**
- Consumes: `FinancialQuarterly`, `config.research_params`
- Produces:
  - `DqResult(check_id: str, company_id: str, period_end: date, status: Literal["pass","fail","warn"], severity: Literal["INFO","WARN","ERROR"], expected, actual, description)`
  - `check_completeness(rows) -> list[DqResult]`, `check_validity(row) -> DqResult`, `check_period_basis(row) -> DqResult`, `check_balance_identity(row) -> DqResult`, `check_source_reconciliation(...) -> list[DqResult]`

- [ ] **Step 1: Write the failing test**

```python
def test_balance_identity_holds_for_a_valid_row() -> None: ...
def test_balance_identity_fails_on_a_corrupted_row() -> None: ...   # R5: checks must be able to fail
def test_validity_rejects_negative_capex() -> None: ...
@pytest.mark.live
def test_balance_identity_holds_for_all_42_company_quarters() -> None:  # DQ_T04
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_dq_checks.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'aicor.quality'`

- [ ] **Step 3: Implement `aicor/quality/checks.py`**

`check_balance_identity` computes `assets − (liabilities + equity)` and compares against `dq.tolerance_assets_liab_equity` read from `research_params.yaml` (not a literal). `check_validity` enforces `revenue >= 0`, `capex >= 0`, `shares > 0`. `check_period_basis` rejects any row whose `period_basis` is missing or is `6M`/`9M` on a stored quarterly row. Every result carries `expected` and `actual` so a failure is reviewable without re-running (dictionary §3.13).

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_dq_checks.py -v` → PASS
Run: `uv run pytest tests/integration/test_dq_against_real_data.py -v -m live` → PASS (DQ_T04 over 42 rows)
Then `uv run pytest -v` → PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: DQ-01..DQ-05 as executable checks with expected/actual evidence"
```

---

### Task 11: Yahoo market connector — *Review Focus #5*

**Files:**
- Create: `aicor/ingest/connectors/market.py`, `tests/integration/test_market_connector.py`

**Interfaces:**
- Consumes: `Settings`, `write_raw`, `Company`
- Produces:
  - `DailyBar(date: date, open, high, low, close, adjusted_close, volume)`
  - `MarketClient(settings: Settings)` with `history(symbol: str, start: date, end: date) -> list[DailyBar]` and `save_csv(symbol, bars, path: Path) -> RawRef`
  - `read_csv(path: Path) -> list[DailyBar]`
  - `MISSING_TRADING_DATES: frozenset` — observed gaps, recorded not filled

- [ ] **Step 1: Write the failing test**

```python
def test_second_run_does_not_refetch(monkeypatch, tmp_path) -> None:
    # MKT_T03: download once
    ...

def test_adjusted_close_is_present_for_every_bar(tmp_path) -> None:   # Review Focus #5
    bars = read_csv(fixture_csv)
    assert all(b.adjusted_close is not None for b in bars)

@pytest.mark.live
def test_fetches_msft_googl_and_sp500() -> None: ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/integration/test_market_connector.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'aicor.ingest.connectors.market'`

- [ ] **Step 3: Implement `aicor/ingest/connectors/market.py`**

Call `https://query1.finance.yahoo.com/v8/finance/chart/{symbol}` (verified working without authentication). Parse `chart.result[0]` → `timestamp[]`, `indicators.quote[0]`, `indicators.adjclose[0]`. Write the CSV through `save_csv` so it lands in the raw store with a SHA-256 and an `access_date`. Non-trading days are **absent from the source and are not synthesised**; any gap detected against the expected exchange calendar is recorded. `^GSPC` is stored with `adjusted_close = close`, and that limitation is written to `source_registry`.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/integration/test_market_connector.py -v` → PASS (the non-live tests; the `live` test needs network)
Then `uv run pytest -v` → PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: Yahoo market connector with download-once snapshot and adjusted_close assertion"
```

---

## Exit Criteria

- `uv run pytest -v` is green on the **full suite**, including `-m live`.
- `FR_T01`: 21 non-null revenue quarters for **both** companies.
- `DER_T04`/`DER_T05`: Q4 = `FY − 9M`, never a 3-month fact.
- `DQ_T04`: `Assets = Liabilities + Equity` within tolerance for all 42 company-quarters.
- Every raw byte is content-addressed with a committed manifest hash.
- No accession number is hard-coded anywhere in the source tree.
- Coverage ≥80% overall and **100% on `aicor/ingest/normalize/`, `aicor/ingest/derive/`, `aicor/quality/`** (critical path).

## Hand-off

Next plan: `2026-10-13-aicor-vertical-slice.md`.