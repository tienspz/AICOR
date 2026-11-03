---
name: observability-and-instrumentation
description: Make Python data crawlers, ETL pipelines, scheduled jobs, and APIs diagnosable with structured logs, run and source status, provenance, and actionable failure signals. Use when adding or reviewing production I/O, retries, pipeline monitoring, or operational telemetry.
---

# Observability and Instrumentation

Instrument the workload that exists; do not assume that a data project needs an
always-on server, hosted telemetry vendor, metrics database, or distributed
tracing. A scheduled Python pipeline and a request-driven API have different
operational questions and need different signals.

## When to activate

- Adding or changing a crawler, external data connector, transformation,
  scheduled workflow, or published artifact.
- Investigating incomplete or stale dashboard data, missing source evidence,
  or a failed scheduled run.
- Adding a real HTTP API or service that needs request-level observability.

For API contracts, use `api-design` and `contract-first`. For ordinary
application security, use `security-review`. Do not implement backend API or
database infrastructure solely to add observability to a static dashboard.

## Start with operational questions

Before adding telemetry, identify the questions the operator or dashboard
reviewer needs answered. For a scheduled data pipeline, prefer:

1. Did the scheduled workflow and each expected source finish?
2. Is the resulting dataset current for the source's expected cadence?
3. Was each source `success`, `partial`, or `failed`, and why?
4. How many records were fetched, new, updated, or skipped?
5. Can each published value be traced through its source ID and URL to the
   raw artifact and its checksum?
6. Did the run preserve valid data from healthy sources when another source
   failed?

For a real HTTP API, also identify questions about request rate, error rate,
latency, correlation, and downstream dependency failures. Do not instrument
API-only signals in a repository that has no API.

## Use the repository's existing signals first

For AICOR, reuse the existing operational record and provenance conventions:

- `SyncRecord` and `write_sync_log` in `src/aicor/sources/__init__.py`.
- The append-only `data/sync_log.jsonl` and `manifest.csv` records.
- `run_id`, `source_type`, `company`, `sync_status`, record counts,
  `error_message`, raw artifact path and SHA-256, configuration version, and
  missing-data reason.
- Python's standard `logging` module for diagnostic messages.
- GitHub Actions run status and job logs for scheduled-workflow operations.
- Generated processed artifacts for dashboard freshness and data status.

Before adding another logger, log file, status vocabulary, or telemetry
dependency, check whether these existing records can answer the operational
question. Keep manifest provenance and run telemetry distinct: the manifest
identifies source artifacts; the sync log describes work and its outcome.

## Instrument a pipeline or scheduled job

1. **Give each invocation a stable run ID.** Create it at the entry point and
   propagate it to source-level records, pipeline records, and diagnostic log
   messages for that invocation.
2. **Record truthful timestamps.** Capture `started_at` before work starts and
   `finished_at` when it ends. Do not fill both fields at the end of the run.
   Use timezone-aware UTC timestamps.
3. **Record bounded, useful facts.** Include source type, company or explicit
   aggregate scope, outcome, relevant record counts, artifact references,
   checksum, configuration version, and a concise failure or missing-data
   reason when applicable. Distinguish no data from a successful empty result
   if the source contract treats them differently.
4. **Preserve partial success.** Isolate source failures where the pipeline
   allows it, retain valid outputs from healthy sources, and report
   `partial` rather than claiming the entire run succeeded. A total failure
   must remain visibly failed.
5. **Log at the operation boundary.** Use Python's module-level `logging`
   methods for actionable diagnostic context. Include the run ID and source
   identity; use exception context for failures. Avoid a success-shaped fallback
   that hides a failed crawl or incomplete artifact.
6. **Keep the run record complete.** Finalize the outcome on normal completion
   and on handled failure. If an exception prevents the normal finalizer from
   running, re-raise it after recording whatever failure evidence can be safely
   written. Do not swallow logging or persistence errors silently.
7. **Make workflow results inspectable.** Ensure CI and scheduled workflows
   fail on conditions defined as fatal, retain clear step names and useful
   output, and make the generated artifacts available to the dashboard or
   reviewer. Do not expose credentials in workflow output.

## Structured logs and privacy

Prefer stable fields and event meanings over inconsistent prose. A useful
pipeline event can carry `event`, `run_id`, `source_type`, `company`,
`sync_status`, elapsed duration, and a bounded error category. Keep detailed
exception information in operator-visible logs while keeping user-facing
messages safe and concise.

Never log API keys, access tokens, passwords, authorization headers, full
environment dumps, or sensitive raw payloads. Treat upstream HTML, error
responses, and dataset contents as untrusted data: log a bounded summary or
approved identifier, not the entire response. Preserve the existing
`source_url` and `raw_sha256` provenance needed to reproduce a result without
copying large source bodies into logs.

## Add telemetry only when it answers a question

- **Scheduled jobs and crawlers:** run summaries, source-level outcomes,
  duration, record counts, freshness, retry counts, and artifact/checksum
  references are usually sufficient. GitHub Actions provides the execution
  history; avoid building a second scheduler or log platform without a clear
  operational need.
- **Static dashboards:** publish data status and freshness alongside the
  processed artifacts. The page should read prepared data; it should not crawl
  external sources or require runtime secrets in the browser.
- **A future HTTP API:** add request IDs and structured request/exception
  logging first. Consider request-rate, error-rate, and latency metrics only
  when the deployed service and its operator need them. Use bounded labels
  such as route template, method, and status class; never use raw URLs, IDs,
  query values, or error messages as metric labels.
- **Distributed tracing:** add only when there are real service boundaries or
  downstream calls whose latency cannot be understood with run and request
  logs. Do not introduce tracing libraries for a single local pipeline by
  default.
- **Alerts:** alert on actionable symptoms such as repeated scheduled-run
  failure, stale required artifacts, or persistent source unavailability.
  Link an alert to a first diagnostic step. Do not alert on every transient
  error or a single expected unavailable source.

## Verify the telemetry

- [ ] A successful run can be found by run ID and shows its real start/end
      times, outcome, and output artifact.
- [ ] A simulated source failure yields an explicit source failure and the
      correct overall `partial` or `failed` status.
- [ ] Healthy-source artifacts are retained when a separate source fails.
- [ ] Record counts, missing-data reasons, source provenance, and checksum
      match the produced data.
- [ ] A missing or stale required artifact is distinguishable from a healthy
      current dataset by the consumer.
- [ ] Logs do not contain credentials, full upstream responses, or unapproved
      sensitive data.
- [ ] A telemetry write failure is surfaced or explicitly handled; it is not
      silently presented as a successful run.
- [ ] New metrics and traces, if justified, are verified from emitted output
      and have bounded dimensions.

Use the repository's existing pytest and GitHub Actions checks. Test
observable behavior and failure states; do not assert only internal logger
calls when the resulting sync record, artifact, or workflow status can be
checked directly.

## Source and adaptation

This skill is an original, repository-specific adaptation informed by Addy
Osmani's `observability-and-instrumentation` skill:

https://github.com/addyosmani/agent-skills/tree/main/skills/observability-and-instrumentation

The upstream repository reported 112,946 stars on 2026-11-03. Its source is
MIT-licensed; see the accompanying `LICENSE`. This adaptation is narrowed to
Python crawlers, data pipelines, provenance, and scheduled GitHub Actions. It
does not include upstream scripts or reference files.
