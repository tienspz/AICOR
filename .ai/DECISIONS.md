# Decision records

## ADR-0001 — Project-local shared memory

- Date: 2026-10-04
- Context: multiple agents need a common, low-token recovery point.
- Decision: keep canonical instructions in `AGENTS.md` and concise state in `.ai/` files; use `CLAUDE.md` and `GEMINI.md` as adapters.
- Alternatives: duplicate full instructions per agent; rely on chat history.
- Reason: minimizes divergence and supports session recovery.
- Consequences: agents must honor the read order; unsupported agents may only receive the adapter text.

## ADR-0002 — No unverified integration claims

- Date: 2026-10-04
- Context: the workspace has no source tree and several requested tools are not detected.
- Decision: record detected extensions and CLIs, but do not create provider-specific config or claim skills/integrations are installed without evidence.
- Alternatives: generate guessed configuration.
- Reason: avoids broken or unsafe configuration and fabricated support claims.
- Consequences: external authentication/install steps remain pending.
