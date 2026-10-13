# ADR-0002 · Version control as the substrate for provenance

- **Status:** Accepted
- **Date:** 2026-10-13
- **Deciders:** research author (approved)
- **Affects:** all tasks
- **Supersedes:** nothing — corrects a defect found at audit

## Context

Repository discovery found two defects that together undermine the project's two central requirements.

1. `.gitignore` line 7 was `*.md`. That pattern excludes `SPEC.md` **and every future ADR, planning document and decision record**. The system's audit trail is written almost entirely in Markdown, so the ignore rule would have silently discarded exactly the artefacts NFR-02 (traceability) and NFR-03 (config versioning) depend on.
2. The directory was **not a git repository at all** — `git status` returned `fatal: not a git repository`.

NFR-01 (reproducibility: same inputs + same config ⇒ same results) is unverifiable without version control. A reviewer cannot diff two pipeline runs, cannot confirm the configuration that produced a result, and cannot detect an untracked change to a research parameter.

There is a legitimate counter-argument: raw SEC filings are multi-megabyte HTML (the two verified filings are 7.7 MB and 2.5 MB), and committing them would bloat the repository.

## Decision

**Initialise version control and stop ignoring Markdown.** Commits `4736be1` and `6d820aa`.

- `.gitignore` narrowed to harness directories (`.agents/`, `.opencode/`, `.vibecode/`), Python/Node build artefacts, secrets, and large raw documents.
- Markdown is tracked. `SPEC.md`, ADRs and planning documents are versioned.
- **Raw document binaries stay ignored** (`data/raw/sec_documents/`, `data/raw/ir_documents/`). Provenance for them is preserved by the committed `raw_manifest`, which stores SHA-256 + source URL + retrieval timestamp. The manifest is the tracked artefact; the bytes are reproducible from the source.
- **Raw market CSVs are tracked** — they are small, and MKT-03 requires download-once reproducibility, which is most defensible when the exact snapshot is under version control.
- `.env` is ignored; only `.env.example` (names, no values) is tracked.

## Consequences

**Positive**
- The audit trail becomes verifiable rather than asserted.
- `research_params.yaml` gains a history — essential because research parameters are the artefacts most likely to be silently tuned after seeing results (see ADR-0006).
- Reproducibility gains a reference point: `NFR_T01` compares two runs recorded against a known commit.

**Negative**
- Repository grows with planning documents and CSV snapshots (bounded — tens of MB at most).
- Raw SEC HTML is not in git, so a reviewer wanting byte-level verification must trust `raw_manifest` hashes or re-fetch. Mitigated by recording the discovered accession number, which pins the exact document.

## Rejected alternative

Keep raw HTML in git for maximal auditability. Rejected: multi-MB binary churn on every re-fetch for no analytical benefit, when the manifest already pins identity by SHA-256 and by accession number.