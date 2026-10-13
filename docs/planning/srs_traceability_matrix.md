# AICOR — SRS Traceability Matrix

**Status:** Complete · **Date:** 2026-10-13 · **Source of truth:** `SPEC.md` (AICOR-SRS, 1,675 lines)
**Baseline:** greenfield (see `repository_audit.md` §1). No requirement can be *Existing* or *Partial* — verified against an empty tree, not assumed.

**Status legend** — `Missing` not started · `Blocked` cannot start until a named open decision is resolved · `Partial` started with a known gap.
**Priority** — MoSCoW. `SPEC.md` §1.6 states all coded requirements default to **Must** unless marked otherwise; the `[CẦN QUYẾT ĐỊNH]` markers indicate priority needing author review (→ **OD-06**).

---

## 1. Research questions (§2.6)

| ID | Question | Traced requirements | Dashboard | Status |
|---|---|---|---|---|
| RQ-01 | How has AI-related resource intensity changed over time? | FR-02, FR-03, AI-02, FE-03, FE-04 | 02 | Missing |
| RQ-02 | Does higher AI investment accompany measurable output gains? | OUT-01, OUT-02, IO-01, FE-01 | 03 | Blocked (OD-05) |
| RQ-03 | Who converts resources to revenue/FCF more efficiently? | FE-05…FE-07, EFF-01, EFF-02 | 05 | Blocked (OD-02, OD-03) |
| RQ-04 | What lag is observable between investment and output? | LAG-01, LAG-02, IO-01, IO-02 | 04 | Blocked (OD-05) |
| RQ-05 | Do stronger results correspond to abnormal shareholder return? | OUT-03, EVT-01…EVT-03 | 06 | Missing |
| RQ-06 | Is investment efficiency stable across operating states? | REG-01, EFF-01 (rolling) | 07 | Blocked (OD-02, OD-04) |
| RQ-07 | Does the ranking survive perturbation? | SEN-01, ROB-01, DEC-01, DEC-02 | 01, 08 | Blocked (OD-03) |

## 2. Sources & trust (SRC)

| ID | Description | Pri | Module | Data deps | Acceptance test | Status | Notes |
|---|---|---|---|---|---|---|---|
| SRC-01 | Every source assigned a tier (S/A/B/R) | Must | `ingest/registry` | — | No row in `source_registry` with NULL/!="SABR" `source_tier` | Missing | Tier R excluded from financial registry (§3.1) |
| SRC-02 | Tier B market data must not substitute for SEC/company accounting vars | Must | `normalize` | `market_daily` | No accounting metric resolves to a `source_tier='B'` row | Missing | Testable invariant |
| SRC-03 | Every analytical data point traceable to a source | Must | all layers | `source_registry` | `PRV_T01` — 100% of non-NULL feature rows join a `source_id` | Missing | Schema in §5.2 SRC-03 |
| SRC-04 | Source-selection ladder: SEC → company → higher-quality primary → unavailable | Must | `ingest` | — | `SRC_T02` selection rule encoded + unit-tested per branch | Missing | Never fabricate to fill |
| SRC-05 | Missing → `value=NULL, status=unavailable, reason=documented`; never analyst estimates | Must | `normalize` | — | `SRC_T03` — no NULL replaced; every NULL has non-empty `reason` | Missing | Verified-real data only |
| SRC-06 | Confidence HIGH/MEDIUM/LOW per SRC-06 table | Must | `features` | — | `SRC_T04` reported→HIGH, derived→MEDIUM, proxy→LOW, asserted per row | Missing | Rule is checkable, not subjective |
| SRC-07 | Only real, programmatically obtainable data; else out of scope | Must | `ingest` | — | `SRC_T05` — zero mock/fabricated rows; every metric resolves to a live endpoint | Missing | **Drives OD-07** (AI-01/AI-04 already removed) |

## 3. Financial data (FR)

| ID | Description | Pri | Module | Data deps | Acceptance test | Status | Notes |
|---|---|---|---|---|---|---|---|
| FR-01 | Quarterly revenue, USD millions, Tier S | Must | `ingest/sec` | XBRL revenue | `FR_T01` — 21 non-null quarters per company | Missing | **Tag discontinuity — see OD-08** |
| FR-02 | Quarterly R&D expense | Must | `ingest/sec` | `ResearchAndDevelopmentExpense` | `FR_T02` — 21 non-null quarters | Missing | |
| FR-03 | CapEx on one consistent accounting definition | Must | `ingest/sec` | `PaymentsToAcquirePropertyPlantAndEquipment` | `FR_T03` — 21 non-null quarters; `definition` field populated; sign convention stored | Missing | Excludes finance leases → **OD-09** |
| FR-04 | Operating income | Must | `ingest/sec` | `OperatingIncomeLoss` | `FR_T04` — 21 non-null quarters | Missing | |
| FR-05 | FCF = CFO − CapEx; definition stored with value | Must | `features` | `…OperatingActivities` | `FR_T05` — recomputes exactly from stored CFO/CapEx | Missing | |
| FR-06 | MSFT segments: Intelligent Cloud, Azure growth, MS Cloud, PBP revenue | Must | `ingest/ir` | MSFT IR / segment XBRL | `FR_T06` — each segment present or NULL+reason | Missing | Segment XBRL is machine-readable → prefer it over IR scraping |
| FR-07 | GOOGL segments: Google Services / Cloud revenue + operating income | Must | `ingest/sec` | segment XBRL | `FR_T07` — each present or NULL+reason | Missing | Tier S, not A — improves DQ-05 |

## 4. AI measurement (AI)

| ID | Description | Pri | Module | Data deps | Acceptance test | Status | Notes |
|---|---|---|---|---|---|---|---|
| AI-01 | **Removed from scope** — direct AI investment not obtainable quarterly | Must | — | — | No field named "ai_investment" anywhere | Missing | Retained as an ID; guard test asserts absence |
| AI-02 | All AI variables are labelled proxies (`reported=false, derived=true, proxy=true`) | Must | `features` | — | `AI_T01` — every proxy row has the three flags set | Missing | |
| AI-03 | Dashboard shows **"AI Investment Proxy"**, never "AI Investment" | Must | `web/` | — | `AI_T02` — grep-based test over UI strings, 0 violations | Missing | Cheap, high-value guard |
| AI-04 | **Removed from scope** — ai_services_growth, copilot_metric, gemini_metric etc. | Must | — | — | No such field exists | Missing | Resolves B-02 |

## 5. Output variables (OUT)

| ID | Description | Pri | Module | Data deps | Acceptance test | Status | Notes |
|---|---|---|---|---|---|---|---|
| OUT-01 | Business output: azure_growth, microsoft_cloud_growth, intelligent_cloud_growth, productivity_growth / google_cloud_growth, google_cloud_operating_income_growth, google_services_growth | Must | `features` | FR-06, FR-07 | `OUT_T01` — each present or NULL+reason; never mixed with company-level outputs | Missing | Mixed company/segment separation is an explicit acceptance item (§9.2) |
| OUT-02 | Financial output: revenue_growth, operating_income_growth, operating_margin, fcf_growth, eps_growth | Must | `features` | FR-01…FR-05 | `OUT_T02` — all 5 per company-quarter | Missing | Must not be read as AI-attributable |
| OUT-03 | Market output: quarter_return, forward_quarter_return, volatility, maximum_drawdown, abnormal_return | Must | `analysis` | `market_daily` | `OUT_T03` — computed vs `^GSPC`; forward return only where t+1 exists | Missing | Last quarter has no forward return → NULL+reason |

## 6. Feature engineering (FE)

| ID | Description | Pri | Module | Data deps | Acceptance test | Status | Notes |
|---|---|---|---|---|---|---|---|
| FE-01 | YoY growth = V_t/V_t-4 − 1 | Must | `features` | any series | `FE_T01` — formula unit-tested; first 4 quarters NULL+reason | Missing | Consumes 4 quarters → drives n≈13 |
| FE-02 | QoQ growth = V_t/V_t-1 − 1 (seasonality caution) | Must | `features` | any series | `FE_T02` formula tested | Missing | |
| FE-03 | R&D intensity = R&D/Revenue | Must | `features` | FR-01, FR-02 | `FE_T03` | Missing | |
| FE-04 | CapEx intensity = CapEx/Revenue | Must | `features` | FR-01, FR-03 | `FE_T04` | Missing | |
| FE-05 | Revenue efficiency = revenue growth / **Resource Growth** | Must | `features` | — | `FE_T05` | **Blocked (OD-02)** | Denominator undefined |
| FE-06 | Operating efficiency = op income growth / **Resource Growth** | Must | `features` | — | `FE_T06` | **Blocked (OD-02)** | |
| FE-07 | FCF efficiency = FCF growth / **Resource Growth** | Must | `features` | — | `FE_T07` | **Blocked (OD-02)** | FCF can go negative → see §14 |
| FE-08 | Guard: NULL + reason when denominator ≈0 or base ≤0; configurable, versioned threshold | Must | `features` | — | `FE_T08` — synthetic zero/negative/base-zero fixtures all yield NULL+reason | Missing | Threshold in versioned config (NFR-03) |

## 7. Lag, IO & causality (LAG / IO / CAU)

| ID | Description | Pri | Module | Data deps | Acceptance test | Status | Notes |
|---|---|---|---|---|---|---|---|
| LAG-01 | Test lags 0…4 | Must | `analysis` | features | `LAG_T01` — exactly 5 lag values per relationship per company | Missing | |
| LAG-02 | No assumed lag before analysis | Must | `analysis` | — | `LAG_T02` — reported lag is argmax over tested set, not a constant | Missing | |
| IO-01 | Test CapEx Growth→Cloud Growth, R&D Growth→Cloud Growth, R&D Intensity→Revenue Growth, CapEx Intensity→Operating Margin at lags 0–4 | Must | `analysis` | features | `IO_T01` — 4 relationships × 5 lags × 2 companies = 40 results stored | Missing | |
| IO-02 | Statistical method (was unspecified) | Must | `analysis` | — | `IO_T02` — `analysis_results.method` non-empty + documented | **Blocked (OD-05)** | Original SRS left method open |
| CAU-01 | Distinguish association / correlation / temporal / causal; default wording "associated with" | Must | all narrative | — | `CAU_T01` — no output string matches `caused|causes|led to`; `limitations` populated | Missing | Machine-checkable string guard |

## 8. Efficiency, sensitivity, robustness (EFF / SEN / ROB)

| ID | Description | Pri | Module | Data deps | Acceptance test | Status | Notes |
|---|---|---|---|---|---|---|---|
| EFF-01 | Multiple measures: Revenue / Operating / FCF / Market / Rolling efficiency, shown individually before any composite | Must | `analysis` | FE-05…07 | `EFF_T01` — 5 measures present; composite absent at this stage | Missing | Rolling window undefined → OD-10 |
| EFF-02 | Composite = .30 Rev + .30 Op + .25 FCF + .15 Market; store `weight_version`, `weights`, `normalization_method` | Must | `analysis` | EFF-01 | `EFF_T02` — weights sum to 1.00; all 3 version fields persisted | **Blocked (OD-03)** | `normalization_method` undefined; components are incommensurable scales |
| SEN-01 | Sensitivity across outcomes × lags 0–4 × efficiency formulas × weight sets | Must | `analysis` | EFF-01/02 | `SEN_T01` — full grid executed; `SEN-01` §lag already corrected to 0,1,2,3,4 | **Blocked (OD-03)** | Weight sets have no numbers |
| ROB-01 | ROBUST if ranking identical across **all** SEN-01 configs, else SENSITIVE + reason | Must | `analysis` | SEN-01 | `ROB_T01` — status ∈ {ROBUST, SENSITIVE}; reversal reason recorded | **Blocked (OD-03)** | Logic is testable once weights exist |

## 9. Event study (EVT)

| ID | Description | Pri | Module | Data deps | Acceptance test | Status | Notes |
|---|---|---|---|---|---|---|---|
| EVT-01 | 8 mandatory event types + event fields | Must | `ingest/ir` | — | `EVT_T01` — schema present; each event type has ≥1 sourced event or an explicit "none found" record | Missing | Must not pad with invented events |
| EVT-02 | Events only from official company / SEC / regulator sources | Must | `ingest/ir` | `source_registry` | `EVT_T02` — 100% of events have `source_tier='A'` or `'S'` and a resolvable URL | Missing | |
| EVT-03 | Window [-10,+10] trading days; expected return, abnormal return, CAR; benchmark versioned | Must | `analysis` | `market_daily` | `EVT_T03` — CAR over exactly 21 trading days; benchmark id + version stored | Missing | Overlap policy → **OD-11** |

## 10. Regime, scenarios, risk (REG / SCN / RSK)

| ID | Description | Pri | Module | Data deps | Acceptance test | Status | Notes |
|---|---|---|---|---|---|---|---|
| REG-01 | 4 regimes classified from Investment Intensity + Business Output + Financial Efficiency | Must | `analysis` | features | `REG_T01` — every company-quarter assigned exactly one regime with the reason | **Blocked (OD-04)** | No thresholds; 3rd name `Efficiency` collides with EFF-01 group (B-06) |
| SCN-01 | S1 Investment Acceleration: CapEx +20%, R&D +10% | Must | `analysis` | features | `SCN_T01` — emitted, labelled ASSUMPTION not guidance | **Blocked (OD-12)** | Shock magnitudes defined; propagation model undefined |
| SCN-02 | S2 Monetization Slowdown: Cloud Growth −10% | Must | `analysis` | features | `SCN_T02` | **Blocked (OD-12)** | |
| SCN-03 | S3 Productivity Improvement: Revenue/R&D +15% | Must | `analysis` | features | `SCN_T03` | **Blocked (OD-12)** | |

## 11. Risk variables (RSK)

| ID | Description | Pri | Module | Data deps | Acceptance test | Status | Notes |
|---|---|---|---|---|---|---|---|
| RSK-01 | 8 risk variables; **must** distinguish High Investment+High Output from High Investment+Weak Output | Must | `analysis` | features | `RSK_T01` — both states distinguishable in output; every RSK variable present or NULL+reason | Missing | Elevated from "should" to "must" in the SRS as central |

## 12. Decisions (DEC)

| ID | Description | Pri | Module | Data deps | Acceptance test | Status | Notes |
|---|---|---|---|---|---|---|---|
| DEC-01 | Per-company structured result: financial_score, ai_efficiency_score, market_score, risk_score, composite_score, ranking, robustness, confidence | Must | `analysis` | EFF-02, SEN-01 | `DEC_T01` — record shape matches; all sub-scores traceable | **Blocked (OD-03)** | `composite_score` formula undefined; overlaps EFF-02 |
| DEC-02 | Decision record: winner, confidence, robustness, key_drivers, sensitivity, limitations | Must | `analysis` | DEC-01 | `DEC_T02` — all 6 keys non-empty; `limitations` never empty | Missing (depends DEC-01) | |
| DEC-03 | Interpretation rules: prefer conditional phrasing; keep Observed/Derived/Association/Interpretation/Scenario distinct | Must | `analysis`, `web` | — | `DEC_T03` — every conclusion string carries its evidence class | Missing | |

## 13. Dashboard (DSH)

| ID | Description | Pri | Module | Data deps | Acceptance test | Status | Notes |
|---|---|---|---|---|---|---|---|
| DSH-01 | Dashboard reads `features_quarterly`, `analysis_results`, `scenario_results`, `source_registry`, `data_quality_log`; **must not** compute financial figures in the client | Must | `web/` | API | `DSH_T01` — no ratio/growth/statistical computation in frontend source; enforced by lint rule + review | Missing | **Highest-risk architectural invariant** |
| DSH-02 | Exactly 9 pages: 01 Executive Comparison … 09 Evidence & Provenance | Must | `web/` | API | `DSH_T02` — 9 routes, each with loading / error / NULL states | Missing | |

## 14. Data quality (DQ)

| ID | Description | Pri | Module | Data deps | Acceptance test | Status | Notes |
|---|---|---|---|---|---|---|---|
| DQ-01 | Completeness: missing_rate < configurable threshold | Must | `quality` | — | `DQ_T01` — per-company rate computed; breaches logged to `data_quality_log` with severity | Missing | Threshold versioned |
| DQ-02 | Validity: Revenue ≥ 0, CapEx ≥ 0, Shares > 0 | Must | `quality` | — | `DQ_T02` — sign convention normalized at load; violations logged | Missing | Cash-flow statements report CapEx negative → sign normalization required, documented in FR-03 `definition` |
| DQ-03 | No mixing Quarterly with Year-to-Date | Must | `normalize` | — | `DQ_T03` — every stored row declares duration basis; no row mixes | Missing | **This is the YTD→quarterly derivation — OD-13** |
| DQ-04 | Accounting reconciliation `Assets = Liabilities + Equity` | Must | `quality` | XBRL instants | `DQ_T04` — holds within tolerance for all 21 quarters × 2 companies | Missing | Feasible — verified tags present |
| DQ-05 | Cross-source reconciliation SEC vs IR; SEC canonical on conflict | Must | `quality` | — | `DQ_T05` — conflict logged; resolved value carries Tier S | Missing | |

## 15. Provenance & versioning (PRV / NFR / DAT)

| ID | Description | Pri | Module | Acceptance test | Status | Notes |
|---|---|---|---|---|---|---|
| PRV-01 | Every feature carries 12 declared fields (incl. `definition`, `calculation_method`, `reported_or_derived`, `proxy`, `confidence`) | Must | `features` | `PRV_T01` — schema non-null constraints enforced | Missing | |
| NFR-01 | Reproducibility: same inputs + same config version ⇒ same analysis results | Must | all | `NFR_T01` — two clean re-runs byte-compare `analysis_results` | Missing | Needs git (now in place) + pinned deps + raw hashes |
| NFR-02 | Traceability: dashboard number → `source_id` → `source_url` | Must | all | `NFR_T02` — the §9.3 chain walkable end-to-end | Missing | Core acceptance criterion |
| NFR-03 | Config versioning: weights, benchmarks, thresholds, formulas versioned and co-stored with results | Must | all | `NFR_T03` — every result row carries `config_version` | Missing | |
| NFR-04 | Assumption transparency: every conclusion lists its assumptions | Must | `analysis` | `NFR_T04` — DEC-02 `limitations` non-empty | Missing | |
| DAT-01 | Store `period_end_date` as the cross-company join key; `fiscal_period` for display only | Must | `db` | — | `DAT_T01` — MSFT FY26Q3 and GOOGL 2026Q1 (both ending 2026-03-31) join to one calendar quarter | **Blocked (OD-01)** | Design is sound; rule needs confirmation (B-09) |

## 16. Market data (MKT)

| ID | Description | Pri | Module | Acceptance test | Status | Notes |
|---|---|---|---|---|---|---|
| MKT-01 | Yahoo Finance as Tier B provider | Must | `ingest/market` | `MKT_T01` — CSV + library both viable | Missing | **Verified working**, 1,512 bars, no auth |
| MKT-02 | Benchmark = S&P 500 (`^GSPC`) | Must | `ingest/market` | `MKT_T02` — `^GSPC` stored; note it is a price index | Missing | `^NDX` retained as robustness check |
| MKT-03 | Download once, store raw CSV, record `access_date`; never re-fetch per run | Must | `raw` | `MKT_T03` — raw CSV committed + SHA-256 in manifest | Missing | Implemented by raw snapshot layer |
| MKT-04 | Default expected return = market-adjusted vs `^GSPC`; CAR over window | Must | `analysis` | `MKT_T04` — formula unit-tested | Missing | |

---

## 17. Traceability findings (analysis, not implementation gaps)

**F-1 — The Efficiency module has no defined denominator.** FE-05/06/07 divide by "Resource Growth"; EFF-01 then enumerates four *different* efficiencies that all divide by the same undefined term. REG-01 classifies on "Financial Efficiency", which inherits the gap. **FE-05, FE-06, FE-07, EFF-01, EFF-02, REG-01 and RQ-03/RQ-06 are all blocked by this single undefined term.** → **OD-02**

**F-2 — OE-4 quarter alignment makes the comparison structurally correct.** DAT-01's `period_end_date` join key is verified correct against reality: the quarter ending 2026-03-31 is FY26Q3 for MSFT and Q1 2026 for GOOGL. Storing `fiscal_period` as display-only is the right call; only the confirmation is missing. → **OD-01**

**F-3 — Effective sample size is smaller than the window suggests.** 21 quarters, `FE-01` consumes `t-4`, and lags run 0–4. Effective n for a lag-4 YoY relationship ≈ **13** per company (~26 pooled). At n=13 no correlation coefficient reaches conventional significance. → **OD-05**

**F-4 — The canonical source table omits the 10-K, yet Q4 data exists only in the 10-K.** §3.3 lists two 10-Qs and two IR pages. The `~3mo` XBRL duration facts stop at `2026-03-31` while `2026-06-30` appears **only** as a full-year duration. Every fourth quarter of the series is therefore unsourced under §3.3 as written. MSFT FY26Q4 = accession `0001193125-26-323660`, filed 2026-07-29. → **OD-14**

**F-5 — FR-06/FR-07 are over-scoped to IR.** Segment revenue and operating income are XBRL-tagged and machine-readable at Tier S. Preferring SEC/segment XBRL over IR scraping improves DQ-05, SRC-07 reliability, and reproducibility at no cost. → **OD-14**

**F-6 — Event-window overlap is narrower than feared.** `[-10,+10]` = 21 trading days ≈ 1 month; earnings releases are ~63 trading days apart, so **earnings event windows cannot overlap**. Overlap is confined to clustered AI product/partnership announcements. → **OD-11**

**F-7 — "Resource Growth" aside, three separate research-parameter families remain undefined:** normalisation method + composite weights (EFF-02/DEC-01/SEN-01), regime thresholds (REG-01), and scenario propagation (SCN-01…03). Per the brief, **none will be invented** — all are escalated. → **OD-03, OD-04, OD-12**

**F-8 — Spec hygiene.** `SPEC.md` §3.3 references "mục 11 và mục 38" of an original document not present in this repository; those cross-references are unresolvable here. The literal `\1\n*` at §1.3.2 was repaired (commit `6d820aa`).

---

## 18. Summary

Counts below are over the **62 coded requirement IDs** in the SRS (SRC 7, FR 7, AI 4, OUT 3, FE 8, LAG 2, IO 2, CAU 1, EFF 2, SEN 1, ROB 1, EVT 3, REG 1, SCN 3, RSK 1, DEC 3, DSH 2, DQ 5, PRV 1, NFR 4, DAT 1, MKT 4). The 7 `RQ-*` entries in §1 are research questions, tracked separately in §1 above.

| Status | Count | Requirement groups |
|---|---|---|
| Missing (unblocked) | 48 | SRC, FR, OUT, FE-01…04/08, EVT, RSK, DQ, PRV, NFR, DSH, MKT, AI |
| Blocked | 14 | FE-05…07, EFF-01, EFF-02, SEN-01, ROB-01, DEC-01, REG-01, SCN-01…03, IO-02, DAT-01 |
| Partial | 0 | — |

**48 of 62 coded requirements can start immediately. 14 are blocked behind 6 blocking research decisions (OD-01…OD-05, OD-12) that only the research author can settle** — plus OD-06, which is administrative rather than blocking. The unblocked set — SEC ingestion, quarterly derivation, data quality, features FE-01…04/08, market data, and the provenance spine — is exactly the vertical slice in `implementation_roadmap.md`, and none of it depends on the blocked decisions.