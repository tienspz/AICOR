# AICOR — Risk Register

**Status:** Live · **Date:** 2026-10-13
**Scoring:** Likelihood × Impact, each 1–5. `Sev = L × I`. Critical ≥ 15 · High 10–14 · Medium 5–9 · Low ≤ 4.
**Every "Evidence" entry is an observed fact from Phase 1 verification — not a prediction.**

---

## 1. Ranked register

| ID | Risk | L | I | Sev | Evidence | Mitigation | Owner | Status |
|---|---|:-:|:-:|:-:|---|---|---|:-:|
| **R-01** | **Alphabet revenue series silently truncates.** GOOGL's ASC 606 tag stops at 2025-03-31 while `Revenues` carries 2026-06-30. A per-company hard-coded tag loses 5 quarters with no error raised. | 4 | 4 | **16** | Verified from SEC `companyconcept` | Period-aware tag resolver (OD-08); hard fail on unresolved quarter; `FR_T01` asserts 21 non-null quarters | Agent 1 | Open — **Critical** |
| **R-02** | **"Resource Growth" is undefined**, so FE-05…07, EFF-01/02, REG-01 and RQ-03/RQ-06 cannot be built. | 5 | 4 | **20** | No SRS requirement defines it | Escalated as **OD-02**; Option C recommended. **Not worked around** | Agent 0 → author | Open — **Critical** |
| **R-03** | **Research parameters get invented.** EFF-02 normalisation, DEC-01 composite weights, SEN-01 weight sets, REG-01 thresholds, SCN propagation are all unspecified. | 4 | 5 | **20** | SRS B-03/B-04/B-06 mark them open | `research_params.yaml` with `pending_approval` (I-6); Agent 0 is sole approver; structure ships with NULL until decided | Agent 0 | Open — **Critical** |
| **R-04** | **Small sample produces false confidence.** 21 quarters, FE-01 consumes `t-4`, lags 0–4 ⇒ n≈13 per company. At n=13 nothing reaches conventional significance. | 5 | 4 | **20** | Computed from window size and lag range | Bootstrap CIs; no p-value ranking; full 5-lag profiles; `limitations` non-nullable; CAU-01 string guard | Agent 2 | Open — **Critical** |
| **R-05** | **Q4 has no source.** No 10-Q exists for Q4, so no 3-month cash-flow fact exists for either company; every 4th quarter exists only as `FY − 9M`. SRS §3.3 lists no 10-K at all. | 4 | 4 | **16** | `~3mo` facts stop at 2026-03-31; `2026-06-30` appears only as FY | `DER_T05` proves Q4 never reads a 3-month fact; 10-K added to the registry via `submissions` API (OD-14) | Agent 1 | Mitigated by design |
| **R-06** | **DSH-01 violated** — frontend computes financial figures, breaking provenance. | 4 | 4 | **16** | Architecture risk; 9 pages of derived display | API returns stored values only (C-1); ESLint rule + source-inspection audit `DSH_T01`/`API_T03` | Agent 4/5 | Mitigated by design |
| **R-07** | **Fabricated AI data** (Copilot / Gemini / "AI investment") to fill AI-01/AI-04 gaps. | 3 | 5 | **15** | SRS removed these but the pressure to fill them persists | AI-01/AI-04 hold; `AI_T03` asserts no `ai_investment` field; `AI_T02` string guard; SRC-05/07 | Agent 5 | Mitigated |
| **R-08** | **Provenance lacks a foundation** — no VCS and `*.md` gitignored, so decisions and manifests would be untracked. | 5 | 4 | **20** | `.gitignore` line 7; `git status` → not a repository | **RESOLVED** in commits `4736be1`, `6d820aa` | Agent 0 | **Closed** |
| **R-09** | **Yahoo Finance data instability / ToS.** Not an official source; terms are personal/educational; prices can be adjusted retroactively. | 4 | 3 | **12** | SRS §3.6 states this limitation | Download-once snapshot + SHA-256 + `access_date` (MKT-03); limitation documented in the report; `^NDX` retained as a robustness check | Agent 1 | Accepted + mitigated |
| **R-10** | **SEC rate limiting or outage** blocks ingestion. | 3 | 3 | **9** | SEC enforces ~10 req/s and a required User-Agent | Token-bucket ≤10 req/s, identified UA, exponential backoff with jitter; failures → `status='unavailable'` + reason, never fabricated | Agent 1 | Mitigated |
| **R-11** | **IR page layout changes** break operating-metric extraction. | 4 | 3 | **12** | MSFT/GOOGL IR pages are scraped HTML | Prefer **segment XBRL (Tier S)** over scraping (OD-14); regex-first with confidence; low-confidence → manual queue; fixture regression tests | Agent 1 | Mitigated |
| **R-12** | **Wrong XML tags or units** silently produce plausible but wrong numbers. | 3 | 5 | **15** | XBRL is machine-readable and therefore silently wrong-able | `period_basis` on every fact; `source_registry.xbrl_tag` records what was actually used; DQ-04 `A = L + E` as an independent arithmetic check | Agent 1 | Mitigated |
| **R-13** | **Causal over-claiming.** SRS language drifts from "associated with" to "caused". | 4 | 5 | **20** | RQ framing plus the tempting lag selection | CAU-01 string guard `caused|causes|led to`; `result_class` on every result; `limitations` non-nullable; DEC-03 phrasing rules | Agent 5 | Mitigated |
| **R-14** | **Backend skill conflict** — injected Node/Express instructions bias a Python stack. | 4 | 2 | **8** | `backend-patterns`, `frontend-patterns`, `api-design` are standing instructions | ADR-0001 records FastAPI as authoritative; frontend half of `frontend-patterns` still applies (Next.js) | Agent 0 | Mitigated |
| **R-15** | **Effort ballooned by the ~250 installed skills.** | 4 | 2 | **8** | Inventory in `installed_skills_audit.md` | Explicit priority order + suppression list; `agent-sort`/`config-gc` offered but **not applied** (unauthorized) | Agent 0 | Accepted |
| **R-16** | **No baseline test result exists**, so regressions have no reference point. | 3 | 3 | **9** | No test suite at Stage 0 | Stage 1 creates the suite; `NFR_T01` double-run becomes the reproducibility baseline | Agent 5 | Mitigated |
| **R-17** | **Regime `Efficiency` name collides** with the EFF-01 measure group, confusing reviewer and reader. | 3 | 2 | **6** | SRS B-06 | Rename proposed → `Conversion Gain` in **OD-04**, pending author | Agent 0 | Escalated |
| **R-18** | **Event data too sparse** to produce a meaningful CAR series. | 3 | 3 | **9** | Tier A AI events are discretionary announcements | "None found" record rather than invention; earnings events (abundant, quarterly) as the backbone; clustering policy (OD-11) | Agent 2 | Mitigated |
| **R-19** | **API exposed beyond localhost** with no auth. | 2 | 4 | **8** | No auth in scope (public filings only) | Explicitly recorded as an accepted NFR gap (OD-06); must be confirmed if deployed off-localhost | Agent 0 | Accepted |
| **R-20** | **Windows/PowerShell environment friction** (console codepage mangling, missing `pnpm`/`psql`). | 3 | 1 | **3** | Observed during discovery | Prefer Python/uv; `docker-compose` for Postgres; UTF-8 enforced in all file I/O | Agent 1 | Accepted |
| **R-21** | **Dead cross-references** — SPEC §3.3 cites "mục 11 và mục 38" of a document absent here. | 3 | 1 | **3** | Observed | Recorded in the traceability matrix §17 F-8; resolved against the SEC `submissions` API instead | Agent 0 | Documented |
| **R-22** | **Postgres unavailable** locally, blocking Stage 1. | 2 | 3 | **6** | `psql` not installed; no running server found | `docker-compose.yml` verified running before Stage 3 exit | Agent 3 | Mitigated |

---

## 2. Critical risks in one line each

- **R-01** Alphabet's revenue will quietly lose 5 quarters unless tag resolution is per-period. → hard-fail + `FR_T01`.
- **R-02/R-03** The Efficiency, Regime and Robustness modules cannot be honestly built until the author settles 6 research decisions. → escalated, not guessed.
- **R-04/R-13** With n≈13 the honest answer is weak evidence, and the design must make weakness visible rather than hide it. → bootstrap CIs, no p-value ranking, mandatory `limitations`.
- **R-05** Every fourth quarter exists only as `FY − 9M`, and the SRS never lists a 10-K. → `DER_T05` + 10-K via the submissions API.
- **R-07/R-12** Machine-readable data is silently wrong-able; and the removed AI metrics create pressure to fabricate. → DQ-04 as an independent arithmetic check, plus `AI_T02`/`AI_T03` guards.

## 3. Risk-driven test requirements

| Risk | Mandatory test |
|---|---|
| R-01 | `FR_T01` — 21 non-null revenue quarters per company |
| R-05 | `DER_T04`, `DER_T05`, `DER_T06` |
| R-06 | `DSH_T01`, `API_T03` |
| R-07 | `AI_T01`, `AI_T02`, `AI_T03` |
| R-12 | `DQ_T02`, `DQ_T03`, `DQ_T04` |
| R-13 | `CAU_T01` string guard; `API_T05` non-nullable `limitations` |
| R-04 | `IO_T03` (`n_observations`), `IO_T04` (determinism) |
| R-08 | `NFR_T01` reproducibility double-run |

## 4. Watchlist — not yet risks

| Item | Why it is not yet a risk | Becomes a risk if |
|---|---|---|
| `research_params.yaml` grows unwieldy | Starts with a handful of approved parameters | It starts absorbing unapproved values — check `pending_approval` counts at every Stage 4 review |
| Analysis grid size | 5 lags × 4 relationships × 2 companies is small | Extra relationships or per-quarter windows are added |
| Frontend bundle growth | 9 pages, small payloads | Charts move data processing client-side — a direct I-1 violation |

## 5. Review cadence

| When | Review |
|---|---|
| End of Stage 3 | R-01, R-05, R-12 — re-score against real DQ output |
| End of Stage 4 | R-02, R-03, R-04, R-13 — re-score once research decisions land |
| End of Stage 5 | R-06, R-19 |
| End of Stage 6 | Full register re-score; every "Mitigated" must cite a **passing test**, not an intention |

**Rule:** no risk may be marked *Mitigated* without a named, executed test. An unevidenced mitigation is an open risk with better branding.