# Handoff

- Last updated: 2026-10-06
- Objective: Full stack complete — Layer 1 (Collection), Layer 2 (Computation + API), Layer 3 (React Display) all implemented, verified, and pushed.
- Branch: `main` tracking `origin/main`.
- Current phase: Phase 7 — Layer 3 React Display Complete (AICOR-020 DONE).
- Completed:
  - AICOR-020: `frontend/` — Vite 6 + React 19 + TypeScript + Tailwind v4 + Recharts + lucide-react (122 packages, 0 vulnerabilities). 8 components per FRONTEND_LAYER3_PLAN.md: Header (MSFT live badge + 15m latency label + sync status + methodology button), MetricCards (latest E/In/Out, spend, low-confidence warning), EChartViewer (3 E-lines, E=0 reference, quarter tooltip with events), InOutBreakdownChart (per-company In vs Out), RawMetricsChart (product/trends/spend selector), TimelineViewer (33 events, launch/funding/relationship filters), PortfolioSimulator (3 sliders locked to 100%, median-E scoring, mandatory amber disclaimer), MethodologyModal (formula, E meaning, D.1–D.8 limits), Footer (manifest UTC + local sync time).
  - Invariants kept: FR-14 (all scores rendered verbatim from JSON; portfolio score uses only precomputed medians), FR-09/FR-10 (slider lock + disclaimer), FR-12 (latency label), no ROI/causality language.
  - Dual-mode: static JSON default (`public/data/`, `base './'` portable, `.nojekyll`, `sync-data.mjs` + `prebuild` hook); live MSFT price via FastAPI with 4s-timeout silent fallback.
  - Backend untouched: `pytest` still 35/35.
  - Verified: `tsc -b` clean, `vite build` success in 11.3s (dist: 624KB JS / 188KB gzip incl. recharts), `vite preview` smoke test HTTP 200 on index + manifest + chart_series.
- Exact next action:
  - Optional: `cd frontend && npm run dev` for visual review; deploy `frontend/dist` to GitHub Pages/Vercel (IF-6); future pipeline runs refresh JSONs via `npm run sync-data`.
