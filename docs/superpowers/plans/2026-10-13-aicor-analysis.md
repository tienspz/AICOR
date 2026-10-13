# AICOR Quantitative Analysis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Compute the features, tests, market outputs, efficiency, regime, sensitivity, robustness and scenario results that answer RQ-01…RQ-07 — while keeping undecided research methodology visibly NULL rather than plausibly filled.

**Architecture:** Feature engineering persists every value with its definition, calculation method, provenance and `config_version`. Analysis selects and aggregates stored features only. Tasks split into two groups: **unblocked** work that needs no research decision, and **held** work whose structure ships with NULL + `reason='pending_decision:<OD-id>'` until the author answers (ADR-0006).

**Tech Stack:** Python 3.14, `numpy`, `scipy`, `pandas`, pytest.

**Spec:** `SPEC.md` §4.5–4.13 · `docs/planning/open_decisions.md` (OD-02, OD-03, OD-04, OD-05, OD-12) · `docs/planning/data_dictionary_and_provenance.md` §3.10–3.12 · ADR-0005, ADR-0006 · `docs/planning/test_and_acceptance_plan.md` §3.5–3.6

**Precondition:** `2026-10-13-aicor-vertical-slice.md` complete.

> **Blocked on author input:** OD-02 (Resource Growth), OD-03 (normalisation + composite weights), OD-04 (regime thresholds), OD-05 (estimator), OD-12 (scenario propagation). Tasks 1, 2, 3, 6 below proceed regardless. Tasks 4, 5, 7 are **held**.

---

## Global Constraints

- **No research parameter is a code literal.** Every threshold, weight, window and normalisation rule is read from `config/research_params.yaml` at runtime and stamped onto the result row as `config_version` (I-6, NFR-03).
- **An unapproved parameter ships as NULL + reason, never as a default.** `reason = "pending_decision:<OD-id>"`. There is no code path that fills these with plausible values (ADR-0006).
- **`n` is ~13, not 21.** FE-01 consumes `t-4` and lags run 0–4. Every analysis row records the true `n_observations`; no row implies more evidence than exists.
- **No significance ranking.** The full lag profile is always reported; no p-value, no "best lag" endpoint, no star markers. Uncertainty travels with every coefficient as a bootstrap CI (OD-05).
- **Any stochastic step takes its seed from `research_params.yaml`** and stores it in `method`, so two runs are byte-identical (NFR-01, `IO_T04`).
- **CAU-01 is machine-enforced.** No produced string may match `caused|causes|led to`. Every result carries `result_class ∈ {observed, derived, association, interpretation, scenario}`.
- **Growth uses `Decimal`; correlation uses `numpy`.** Ratios are decimal fractions, never percent-scaled.
- **Derived quarters are labelled `derived`, never `reported`** (ADR-0005).

---

## Review Focus

| # | Failure mode | Expected behaviour | Pinned in |
|---|---|---|---|
| 1 | **`Resource Growth` silently defaults to CapEx growth**, making the Efficiency column look complete while its denominator was never decided | NULL with `pending_decision:OD-02` | Task 5 |
| 2 | **A near-zero or negative-base denominator yields a huge or absurd ratio** instead of a NULL | Guard returns NULL with the configured threshold echoed in the reason | Task 1 |
| 3 | **The lag analysis reports only the maximum**, manufacturing a causal story from noise | All five lags always returned and displayed together | Task 3 |
| 4 | **A scenario is presented as company guidance** | `assumption_class = ASSUMPTION` on every scenario row | Task 7 |
| 5 | **A CI spanning zero is dropped because it "doesn't support the finding"** | Stored and displayed as uncertainty regardless of direction | Task 3 |

---

### Task 1: Growth features with explained-NULL guards — *Review Focus #2*

**Files:** Create `aicor/features/growth.py`, `tests/unit/test_growth.py`

**Interfaces:**
- Consumes: `config.research_params` key `fe.near_zero_threshold`
- Produces: `yoy(series: Sequence[Decimal], index: int) -> FeatureDraft`, `qoq(series, index) -> FeatureDraft`

- [ ] **Step 1: Write the failing test**

```python
def test_yoy_is_value_t_over_value_t_minus_4() -> None: ...

def test_yoy_is_null_for_the_first_four_quarters() -> None:
    # only 3 prior observations exist
    ...

def test_near_zero_denominator_returns_null_with_the_threshold_in_the_reason() -> None:
    # Review Focus #2
    d = yoy([Decimal("0.001"), Decimal("1")]*5, index=4)
    assert d.value is None
    assert str(settings.fe.near_zero_threshold) in d.reason

def test_negative_base_returns_null_rather_than_a_misleading_ratio() -> None:
    # FCF can be negative (FR-04 / FE-08)
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_growth.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'aicor.features.growth'`

- [ ] **Step 3: Implement `aicor/features/growth.py`**

Both functions return `FeatureDraft`; neither raises and neither clamps or rounds to bypass a guard. The threshold is read from `research_params.yaml` and interpolated into the `reason` string, so the reason is reproducible from the stored config version.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_growth.py -v` → PASS, then `uv run pytest -v` → PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: YoY and QoQ growth with configured near-zero and negative-base guards (FE-01, FE-02, FE-08)"
```

---

### Task 2: Intensity and financial-output features

**Files:** Create `aicor/features/intensity.py` (extend), `aicor/features/outcomes.py`, `tests/unit/test_outcomes.py`

**Interfaces:**
- Consumes: `FinancialQuarterly`
- Produces: `rd_intensity`, `operating_margin`, `revenue_growth_delegate`, `eps_growth`, `volatility`, `maximum_drawdown`

- [ ] **Step 1: Write the failing test**

```python
def test_operating_margin_is_operating_income_over_revenue() -> None: ...
def test_maximum_drawdown_is_non_positive() -> None: ...
def test_forward_quarter_return_is_null_for_the_final_quarter() -> None:
    # OD-15
    assert d.status == "unavailable" and d.reason == "no_subsequent_quarter"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_outcomes.py -v` → FAIL, `ModuleNotFoundError`

- [ ] **Step 3: Implement**

`volatility` uses the standard deviation of daily log returns over the quarter, with the annualisation decision left as `annualize_volatility` in `research_params.yaml` — read, not assumed. OUT-02 outputs are company-level and must never be labelled as AI-attributable.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_outcomes.py -v` → PASS, then `uv run pytest -v` → PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: intensity and financial/market outcome features"
```

---

### Task 3: Lag and input→output analysis — *Review Focus #3 and #5*

**Held pending OD-05 (estimator).** The structure ships now; the estimator selection is a single config switch.

**Files:** Create `aicor/analysis/lag.py`, `aicor/analysis/io.py`, `tests/unit/test_lag_analysis.py`

**Interfaces:**
- Consumes: `features_quarterly`, `research_params` keys `io.estimator`, `io.lags`, `io.bootstrap_resamples`, `io.seed`
- Produces: `AnalysisDraft(analysis_type, metric, value, lag, method, n_observations, ci_low, ci_high, result_class, status, reason)`; `lag_profile(...) -> list[AnalysisDraft]` (length always 5)

- [ ] **Step 1: Write the failing test**

```python
def test_lag_profile_always_contains_lags_zero_through_four() -> None:
    # Review Focus #3 / LAG-01
    assert [a.lag for a in lag_profile(...)] == [0, 1, 2, 3, 4]

def test_n_observations_reflects_the_drop_not_the_window_length() -> None:
    # ~13, not 21 — FE-01 consumes t-4 and the lag consumes another L
    assert row.n_observations == 13

def test_a_ci_spanning_zero_is_stored_not_dropped() -> None:
    # Review Focus #5
    assert row.ci_low < 0 < row.ci_high

def test_identical_seed_produces_identical_results() -> None:
    # IO_T04
    ...

def test_no_produced_string_matches_a_causal_verb() -> None:
    # CAU-01
    assert not re.search(r"caused|causes|led to", row.method + row.metric, re.I)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_lag_analysis.py -v` → FAIL, `ModuleNotFoundError`

- [ ] **Step 3: Implement `aicor/analysis/lag.py` and `aicor/analysis/io.py`**

Read `io.estimator` from config; if it is absent or `pending_approval`, every row is emitted with `status='unavailable'` and `reason='pending_decision:OD-05'` — the code path is real and exercised, but produces no invented number. Once OD-05 is answered, setting the estimator is a config edit with no code change.

- [ ] **Step 4: Run test to verify current state**

Run: `uv run pytest tests/unit/test_lag_analysis.py -v`
Expected: the **guard** tests PASS (profile length 5, `n_observations` == 13, CI stored, no causal verb). The **estimator** tests FAIL with `status='unavailable'` until OD-05 is answered.
**This partial failure is the correct state for a held task and must be reported to the reviewer as held-on-OD-05, not suppressed or worked around.**

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(lag): lag and IO analysis structure; estimator gated on OD-05"
```

---

### Task 4: Efficiency measures

**Held pending OD-02 (Resource Growth).**

**Files:** Create `aicor/analysis/efficiency.py`, `tests/unit/test_efficiency.py`

**Interfaces:**
- Consumes: `research_params` key `efficiency.resource_growth`
- Produces: `efficiency(numerator_growth: Decimal, resource_growth: Decimal | None) -> AnalysisDraft`

- [ ] **Step 1: Write the failing test**

```python
def test_efficiency_is_null_with_pending_decision_when_resource_growth_is_undecided() -> None:
    # Review Focus #1
    assert d.status == "unavailable"
    assert d.reason == "pending_decision:OD-02"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_efficiency.py -v` → FAIL, `ModuleNotFoundError`

- [ ] **Step 3: Implement `aicor/analysis/efficiency.py`**

Read `efficiency.resource_growth`. Absent or `pending_approval` → NULL + reason. Once OD-02 is answered, the three efficiency measures (Revenue, Operating, FCF) divide by the configured series; **no code default exists**.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_efficiency.py -v` → PASS, then `uv run pytest -v` → PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(efficiency): structure shipped with NULL denominator pending OD-02"
```

---

### Task 5: Composite score, sensitivity and robustness

**Held pending OD-03 (normalisation + composite weights).**

**Files:** Create `aicor/analysis/sensitivity.py`, `aicor/analysis/robustness.py`, `tests/unit/test_robustness.py`

**Interfaces:**
- Consumes: `research_params` keys `composite.normalization_method`, `composite.weights`, `sensitivity.weight_sets`
- Produces: `sensitivity_grid(...) -> list[AnalysisDraft]`, `robustness(grid) -> AnalysisDraft` with `robustness ∈ {ROBUST, SENSITIVE}`

- [ ] **Step 1: Write the failing test**

```python
def test_robustness_is_sensitive_when_the_ranking_flips_in_one_configuration() -> None:
    # ROB-01
    assert result.robustness == "SENSITIVE" and "reverses at lag" in result.reason

def test_weights_must_sum_to_one() -> None: ...

def test_grid_covers_lags_zero_through_four_not_zero_one_two_four() -> None:
    # the SRS's own corrected lag list; the original omitted 3
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_robustness.py -v` → FAIL, `ModuleNotFoundError`

- [ ] **Step 3: Implement**

`composite.normalization_method` absent → every composite row NULL + `pending_decision:OD-03`. The weight-sum check runs before any composition and raises on a malformed set, so a bad vector can never reach a result.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_robustness.py -v` → PASS, then `uv run pytest -v` → PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(sensitivity): sensitivity grid and ROB-01 classification, gated on OD-03"
```

---

### Task 6: Market output and event study

**Unblocked.**

**Files:** Create `aicor/analysis/event.py`, `tests/unit/test_event_study.py`, `tests/integration/test_event_study_live.py`

**Interfaces:**
- Consumes: `market_daily`, `AiEvent`, `research_params` keys `evt.window`, `evt.benchmark`, `evt.expected_return_model`
- Produces: `car(event: AiEvent, bars: Sequence[DailyBar], benchmark: Sequence[DailyBar]) -> AnalysisDraft` with `cluster_id`

- [ ] **Step 1: Write the failing test**

```python
def test_car_window_is_exactly_twenty_one_trading_days() -> None:
    # EVT-03
    ...

def test_earnings_event_windows_cannot_overlap() -> None:
    # ~63 trading days apart vs a 21-day window
    assert not clusters_overlap(earnings_events)

def test_clustered_events_are_counted_once_in_aggregate_statistics() -> None:
    # OD-11
    ...

def test_benchmark_identifier_and_version_are_stored_on_the_result() -> None: ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_event_study.py -v` → FAIL, `ModuleNotFoundError`

- [ ] **Step 3: Implement `aicor/analysis/event.py`**

Market-adjusted return vs `^GSPC` (MKT-04 default). Windows that intersect receive a shared `cluster_id` computed here; each event keeps its own CAR while aggregate statistics count the cluster once.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_event_study.py -v` → PASS, then `uv run pytest -v` → PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(events): CAR over the fixed window with overlap clustering (EVT-01..03)"
```

---

### Task 7: Regime and scenarios

**Held pending OD-04 (thresholds) and OD-12 (propagation).**

**Files:** Create `aicor/analysis/regime.py`, `aicor/analysis/scenario.py`, `tests/unit/test_regime.py`, `tests/unit/test_scenario.py`

**Interfaces:**
- Consumes: `research_params` keys `regime.thresholds`, `regime.name_mapping`, `scenario.shocks`
- Produces: `classify_regime(...) -> AnalysisDraft`; `apply_scenario(shocks: ScenarioShocks, row: FinancialQuarterly) -> list[ScenarioDraft]`
- `ScenarioShocks(code: Literal["S1","S2","S3"], assumption: dict[str, Decimal], label: str)` — read from `research_params.yaml`; `label` is always the string `ASSUMPTION`
- `ScenarioDraft(scenario_code: str, assumption_class: Literal["ASSUMPTION"], assumption: dict, financial_effect: Decimal | None, efficiency_effect: Decimal | None, risk_effect: Decimal | None, status: str, reason: str | None, config_version: str)`

- [ ] **Step 1: Write the failing test**

```python
def test_regime_is_null_pending_thresholds() -> None:
    assert d.reason == "pending_decision:OD-04"

def test_every_company_quarter_is_assigned_exactly_one_regime() -> None:
    # partitions all 42 rows
    ...

def test_scenario_effects_needing_an_elasticity_are_null_with_a_reason() -> None:
    # OD-12
    ...

def test_every_scenario_is_labelled_assumption_not_guidance() -> None:
    # Review Focus #4 / SCN-01..03
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_regime.py tests/unit/test_scenario.py -v` → FAIL, `ModuleNotFoundError`

- [ ] **Step 3: Implement**

Arithmetic-only propagation: S1 recomputes `capex_intensity = (capex × 1.20) / revenue` and stops. Anything requiring an invented elasticity is emitted NULL with a reason. `regime.name_mapping` exists because the SRS's third regime name `Efficiency` collides with the EFF-01 measure group (B-06) — the mapping is config, so the rename is a decision, not a code change.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_regime.py tests/unit/test_scenario.py -v` → PASS, then `uv run pytest -v` → PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(regime,scenario): structures shipped NULL-gated on OD-04 and OD-12"
```

---

## Exit Criteria

- [ ] Every unblocked task green against real data
- [ ] Every held task ships **structure with NULL + `pending_decision`**, and no invented value anywhere
- [ ] No produced string matches a causal verb (CAU_T01)
- [ ] `n_observations` is ~13 on lag-4 rows, not 21
- [ ] Identical seed ⇒ byte-identical results (`IO_T04`)
- [ ] Every result row carries `config_version`
- [ ] `weight_version`, `weights`, `normalization_method` persisted wherever a composite exists (`EFF_T02`)

## Explicitly not in this plan

The nine dashboard pages (`web/`). They consume the endpoints delivered by `2026-10-13-aicor-api-contract.md` through the generated client and compute nothing — tracked separately as a frontend plan once the API is complete.