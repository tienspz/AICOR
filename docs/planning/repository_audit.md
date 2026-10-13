# AICOR — Repository Audit

**Status:** Complete · **Date:** 2026-10-13 · **Baseline commit:** `4736be1`
**Method:** direct filesystem inspection + live API probes. Every claim below cites a path or a command result.

---

## 1. Headline finding

**AICOR is greenfield.** The dispatch brief assumed an existing implementation to preserve and audit. There is none. The repository contained exactly two documents and an AI-assistant harness. No requirement can be marked *Existing* or *Partial*; all are *Missing*.

## 2. Repository inventory (as found)

Root listing of `D:\Learning\DangHoc\DAFBE\7_AICOR`:

| Path | Bytes | Classification |
|---|---:|---|
| `.gitignore` | 120 | Defect — see §4 |
| `SPEC.md` | 61,010 | **AICOR SRS** (Vietnamese), 1,675 lines — the requirements baseline |
| `VIBECODE_SETUP.md` | 3,630 | Harness documentation (not a project document) |
| `.agents/` | — | Antigravity/ECC harness, ignored |
| `.opencode/` | — | OpenCode/ECC harness, ignored |
| `.vibecode/` | — | Vendored sources (superpowers, mem0, ECC), ignored |

### Verified absences
No `package.json`, `pyproject.toml`, `requirements.txt`, `poetry.lock`, `Makefile`, `Dockerfile`, no `src/`, `app/`, `api/`, `db/`, `tests/`, `docs/`, `notebooks/`, no SQL or migrations, no CI workflow, no `.env` or `.env.example`, no API contract, no ADR directory, no data files.

### Technology stack
**None.** The SRS (§1–10, Appendix A/B) specifies requirements, sources, and a conceptual block diagram (§8) but never names a language, framework, database, or package manager. There is therefore no "existing technology" to remain compatible with; the stack became a decision, recorded as [ADR-0001](adr/0001-technology-stack.md).

## 3. Local toolchain (verified)

| Tool | Status | Note |
|---|---|---|
| Python | **3.14.7** | target runtime |
| Node | **v24.14.0** | target frontend runtime |
| `uv` | present | `C:\Users\ACER\.local\bin\uv.exe` — dependency + venv management |
| `git` | present | but directory was **not a repository** |
| `pnpm` | not installed | npm is available; either is acceptable |
| `duckdb`, `psql` | not installed | Postgres chosen; will be provisioned (see ADR-0001) |

## 4. Defects found and resolved during audit

| # | Defect | Evidence | Resolution |
|---|---|---|---|
| D-1 | `.gitignore` line 7 was `*.md` — excluded `SPEC.md` **and every future ADR/plan/decisional record** | `.gitignore` as found | Removed `*.md`; narrowed to harness dirs + build/secret/raw-document paths |
| D-2 | Directory was not under version control (`fatal: not a git repository`) | `git status` | `git init`; first commit `4736be1` |
| D-3 | `SPEC.md:95` contained literal `\1\n*` before the "dữ liệu giả (mock)" bullet, breaking the §1.3.2 list | `grep` over decoded file — exactly 1 backslash occurrence in the whole file | Removed the stray escape; commit `6d820aa`. **No requirement wording changed.** |

### Checked and found sound
- **Encoding.** Suspected mojibake, then disproved: all 12 codepoints outside ASCII+Vietnamese are legitimate (`─ │ ┌ ┐ └ ┘ ┬`, `↓ →`, `×`, `−`, `ị`, `ệ`). `SPEC.md` is valid, correctly-encoded UTF-8 (51,016 chars). The mangling seen in shell output was a PowerShell console-codepage artifact only. **No re-encoding performed** — attempting it would risk altering requirements text.
- **Secrets.** No `.env`, no credentials, no keys found in the project tree. Harness config carries only a local MCP memory path.
- **Oversized files.** None in the project tree. `ecc-install-state.json` is 427 KB (`.agents/`) / 659 KB (`.opencode/`) — harness artifacts, ignored.

## 5. Harness constraints that affect implementation

| Item | Finding | Impact |
|---|---|---|
| `opencode.json` `instructions` | Lists `AGENTS.md` and `CONTRIBUTING.md` — **neither exists** at project root | Minor: instruction resolution falls through; do not rely on them |
| MCP `memory` server | `MEMORY_FILE_PATH` is an **absolute Windows path** (`D:\Learning\DangHoc\DAFBE\7_AICOR\.vibecode\memory\memory.jsonl`) | Breaks if the workspace moves; documented in `VIBECODE_SETUP.md` |
| Injected global instructions | `backend-patterns`, `frontend-patterns`, `api-design`, `e2e-testing`, `verification-loop`, `coding-standards`, `security-review` are loaded as **standing instructions** | These default to a **Node/Express/Next.js** stack and will bias implementation away from the chosen Python analytics stack unless consciously overridden — see ADR-0001 |
| `.agents/rules/` | ~Angular/ArkTS rule catalog | Irrelevant to AICOR; ignore |
| Skills installed | ~250 (ECC) + superpowers | Use selectively; see `installed_skills_audit.md` |

## 6. External data reality check (verified, not assumed)

All 13 URLs in SRS §1.5 and §3.3 return HTTP 200. The two gating SEC documents were additionally checked against SEC's own filing index and are **authentic**:

| SRS claim | SEC index says | Verdict |
|---|---|---|
| MSFT 10-Q, period 2026-03-31, acc. `000119312526191507`, `msft-20260331.htm` | filed 2026-04-29, acc. `0001193125-26-191507`, period 2026-03-31 | **Confirmed** |
| GOOGL 10-Q, period 2026-06-30, acc. `000165204426000071`, `goog-20260630.htm` | filed 2026-07-23, acc. `0001652044-26-000071`, period 2026-06-30 | **Confirmed** |

**Feasible data window — better than the SRS assumed.** Actual revenue period-ends, enumerated from SEC XBRL:

> **21 consecutive calendar quarters, `2021-06-30` → `2026-06-30`, identical for both MSFT and GOOGL.**

SRS requires 16–20, so the target is satisfiable. All of `Assets`, `Liabilities`, `StockholdersEquity`, `CommonStockSharesOutstanding`, `EarningsPerShareDiluted`, `ResearchAndDevelopmentExpense`, `PaymentsToAcquirePropertyPlantAndEquipment`, `NetCashProvidedByUsedInOperatingActivities`, `OperatingIncomeLoss`, `NetIncomeLoss` are present across that window for both companies — so **DQ-04 (`Assets = Liabilities + Equity`) is verifiable against real data**.

**Market data — programmatic access confirmed without authentication.** `query1.finance.yahoo.com/v8/finance/chart/{symbol}` returned **1,512 daily bars each with `adjclose` present** for `MSFT`, `GOOGL` and `^GSPC`, spanning 2020-09-14 → 2026-09-21. No crumb/cookie flow required. This removes the principal MKT-01 tooling risk.

## 7. Implementation status and baseline

- **Implemented features:** none.
- **Test suite:** none. **Baseline test result: does not exist.** No green baseline is claimed.
- **Baseline checks that were run:** filesystem inventory; git status; HTTP probe of 13 SRS URLs; SEC `submissions` index reconciliation; XBRL `companyconcept` duration/period analysis; Yahoo chart API retrieval.

## 8. Reuse assessment

No existing implementation to reuse. However, two **verified external assets** should be reused rather than re-derived:

1. **SEC `companyconcept` / `companyfacts` APIs** — structured XBRL, already proven to carry every metric the SRS needs. Avoids HTML scraping of 7.7 MB filings.
2. **SEC `submissions` API** — authoritative accession/period index, used above to verify the SRS's own URLs. Should be the mechanism that discovers filings rather than hard-coded accession numbers.

The correct pattern is therefore *API-first, HTML-fallback*, not *scrape the 10-Q*.