# AICOR — Installed Skills Audit

**Status:** Complete · **Date:** 2026-10-13
**Scope:** every skill actually present on disk. Names were verified against `SKILL.md` frontmatter, not inferred from documentation.

---

## 1. Where skills live

| Root | Mechanism | Count | Status |
|---|---|---|---|
| `.opencode/skills/` | ECC full OpenCode profile | ~250 | Active |
| `.vibecode/sources/superpowers/skills/` | Loaded via plugin (`plugin: ../.vibecode/sources/superpowers`) | 14 | Active |
| `.agents/skills/` | Antigravity host (mem0 + cursor rules) | ~8 | Not used by this session |
| `.vibecode/sources/mem0/skills/` | Vendored reference | 6 | Not applicable |

**Important:** three skills the brief's plan depends on (`writing-plans`, `subagent-driven-development`, `dispatching-parallel-agents`) are **not** in `.opencode/skills/` but **are** installed via the superpowers plugin. A naive scan of one directory produces a false "not installed".

## 2. Skills that govern AICOR

### Process skills — applied first, they set the method

| Skill | Location | Applied by | Use at |
|---|---|---|---|
| `brainstorming` | superpowers | Agent 0 | Requirements & stack decisions (done — gate held) |
| `writing-plans` | superpowers | Agent 0 | Turning the approved plan into ordered tasks |
| `subagent-driven-development` | superpowers | Agent 0 | Per-task implementer + independent reviewer loop |
| `dispatching-parallel-agents` | superpowers | Agent 0 | Fanning out independent tasks after interface freeze |
| `verification-before-completion` | superpowers | Agent 5 | Gate: no task is "done" without evidence |

### Architecture & decisions

| Skill | Location | Applied by | Use at |
|---|---|---|---|
| `architecture-decision-records` | `.opencode/skills` | Agent 0 | Every open decision in `open_decisions.md` |
| `hexagonal-architecture` | `.opencode/skills` | Agent 0 | Separating domain logic from SEC/Yahoo I/O |
| `blueprint` | `.opencode/skills` | Agent 0 | Multi-session dependency graph & parallel-step detection |
| `contract-first` | `.opencode/skills` | Agent 3 (owns) / Agent 4 (consumes) | `openapi.yaml` as the single authoritative contract |
| `intent-driven-development` | `.opencode/skills` | Agent 0 | Turning B-01…B-09 into verifiable acceptance criteria |

### Data engineering

| Skill | Location | Applied by |
|---|---|---|
| `api-connector-builder` | `.opencode/skills` | Agent 1 — SEC / IR / Yahoo connectors must match one pattern |
| `data-scraper-agent` | `.opencode/skills` | Agent 1 — scheduled collection + raw snapshots (partial fit; see §5) |
| `data-throughput-accelerator` | `.opencode/skills` | Agent 1 — ingest/backfill accounting (row-count + hash proof) |
| `regex-vs-llm-structured-text` | `.opencode/skills` | Agent 1 — **IR page parsing**: regex-first, escalate only low-confidence items |

### Quantitative research

| Skill | Location | Applied by | Note |
|---|---|---|---|
| `python-patterns` | `.opencode/skills` | Agents 1, 2 | typing, numerics hygiene |
| `pytorch-patterns` | `.opencode/skills` | — | **Not applicable** — no neural models in scope |
| `research-ops` | `.opencode/skills` | Agents 0, 1 | Evidence-first; blocks fabricated citations |

### Backend / data

| Skill | Location | Applied by |
|---|---|---|
| `fastapi-patterns` | `.opencode/skills` | Agent 3 — Pydantic v2, DI, async, httpx/pytest |
| `api-design` | `.opencode/skills` | Agent 3 — REST naming, status codes, error shape |
| `postgres-patterns` | `.opencode/skills` | Agent 3 — schema, indexes, query plans |
| `database-migrations` | `.opencode/skills` | Agent 3 — forward-only, reversible migrations |
| `error-handling` | `.opencode/skills` | Agent 3 — typed errors, retries, circuit breaking |
| `backend-patterns` | `.opencode/skills` ⚠️ | Agent 3 — **see conflict C-1** |
| `security-review` | `.opencode/skills` | Agent 5 — secrets, API exposure |

### Frontend

| Skill | Location | Applied by |
|---|---|---|
| `react-patterns` | `.opencode/skills` | Agent 4 |
| `frontend-patterns` | `.opencode/skills` ⚠️ | Agent 4 — **see conflict C-1** |
| `nextjs-turbopack` | `.opencode/skills` | Agent 4 |
| `frontend-a11y` | `.opencode/skills` | Agent 4 — keyboard/screen-reader across 9 pages |
| `frontend-design-direction` | `.opencode/skills` | Agent 4 — dashboard legibility |

### Testing & audit

| Skill | Location | Applied by |
|---|---|---|
| `python-testing` | `.opencode/skills` | Agent 5 — pytest, fixtures, parametrize |
| `react-testing` | `.opencode/skills` | Agent 4/5 |
| `e2e-testing` | `.opencode/skills` | Agent 5 — Playwright for the 9 pages |
| `test-collaboration` | `.opencode/skills` | Agent 5 — TEST-ID registry |
| `module-regression` | `.opencode/skills` | Agent 5 — downstream regression ledger |
| `production-audit` | `.opencode/skills` | Agent 5 — pre-acceptance audit |
| `security-review` | `.opencode/skills` | Agent 5 |
| `test-driven-development` | superpowers | Agents 1–3 — write the failing test first |

## 3. Conflicting instructions

| # | Conflict | Resolution |
|---|---|---|
| **C-1** | `backend-patterns` / `frontend-patterns` / `api-design` are injected as **standing instructions** and default to Node/Express/Next.js. The chosen stack is Python/FastAPI/Postgres/Next.js. | Frontend half of `frontend-patterns` **applies** (Next.js). Backend half of `backend-patterns` **does not apply** — FastAPI is authoritative. Recorded in ADR-0001. |
| **C-2** | `gateguard` (PreToolUse fact-forcing gate) can deny first write attempts until concrete facts are presented. | Expected behaviour, not a defect. Satisfy it by citing importers/schemas. |
| **C-3** | `tdd-workflow` (injected) vs `test-driven-development` (superpowers) overlap. | Use superpowers `test-driven-development` as primary; `python-testing`/`react-testing` supply stack-specific patterns. |
| **C-4** | `delivery-gate` stop-hook may block completion pending learning capture. | Satisfy via `growth-log`; do not bypass. |
| **C-5** | `.agents/rules/*.md` is an Angular/ArkTS catalog. | Ignored — wrong framework. |
| **C-6** | ~240 installed skills vs. one project. | Severe context cost. Only the ~30 above are used. |

## 4. Priority order

1. **Process skills** — `brainstorming` → `writing-plans` → `subagent-driven-development` / `dispatching-parallel-agents` → `verification-before-completion`.
2. **Domain skills**, scoped to the owning agent per §2.
3. **Explicitly suppressed:** `pytorch-patterns` (no ML models), all Angular/ArkTS rules, all `frontend-slides` / `video-editing` / `taste*` / `videodb` / `manim-video` families (irrelevant), and the Node-backend half of `backend-patterns`.

## 5. Fit gaps — skills that only partially apply

| Skill | Gap |
|---|---|
| `data-scraper-agent` | Assumes GitHub Actions + Notion/Sheets/Supabase sinks and an LLM enrichment step. AICOR needs a **local, deterministic, non-LLM** pipeline writing into Postgres with SHA-256 raw manifests. Take the *snapshot + provenance* ideas; discard the schedule/LLM/store half. |
| `benchmark` / `benchmark-optimization-loop` | Written for web Core Web Vitals and API latency. The AICOR analogue is **pipeline reproducibility and row-count accounting**, which `data-throughput-accelerator` covers better. |
| `contract-first` | Designed for JSON Schema/OpenAPI round-trips with consumer type generation. Applies to `web/` ↔ FastAPI. Does **not** extend to the analytical pipeline, which needs its own governed artifact schema (§ `data_dictionary_and_provenance.md`). |

## 6. Constraint honoured

No skill was installed, removed, or modified. `config-gc` and `agent-sort` would reduce the ~250-skill surface, but that is **not authorized** by the brief ("Do not install additional skills unless explicitly authorized") and is recorded as an optional recommendation only.