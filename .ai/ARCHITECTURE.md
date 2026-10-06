# Architecture

The intended AICOR boundary is:

1. Raw source connectors (SEC EDGAR, yfinance, Google Trends, official blogs/changelogs).
2. Validated append-only data and provenance manifests.
3. Python processing and precomputed metrics/results.
4. SQLite persistence and JSON/CSV exchange.
5. React presentation of precomputed results.
6. CI and deployment.

This is a provisional boundary based on the supplied project brief. Confirm paths, schemas, and interfaces against `PROJECT_SPEC_CMU.md` and source code before implementation.
