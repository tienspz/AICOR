# Vibe Code skills

This folder is the tracked source of truth for a small, portable skill set. Each
skill follows the Agent Skills `SKILL.md` format and avoids IDE-specific
variables, mandatory packages, and bundled executables.

## Included skills

| Skill | Use it for | Source and selection |
| --- | --- | --- |
| `design-taste-frontend` | Creating or refining a distinctive web page or product UI | Portable adaptation of the main Taste Skill discussed in the [Cuong Me AI article](https://cuongmeai.com/tai-lieu/8-skill-thiet-ke-web-cho-claude). The upstream [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) was reported at 109,138 stars on 2026-11-03 and is MIT-licensed. This edition keeps the design workflow while leaving out upstream scripts and browser/runtime assumptions. |
| `web-design-guidelines` | Reviewing an existing web interface for usability, accessibility, responsive behavior, and visual consistency | A portable review wrapper referencing Vercel's [web-design-guidelines skill](https://github.com/vercel-labs/agent-skills/tree/main/skills/web-design-guidelines) and its [published rules](https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md). The official [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) repository was reported at 33,449 stars on 2026-11-03. The wrapper does not copy Vercel's skill text; it can use the live rules when network access is available. |
| `observability-and-instrumentation` | Instrumenting Python crawlers, data-processing pipelines, scheduled jobs, and a future API so failures and artifact freshness are diagnosable | Adapted for this repository from [Addy Osmani's agent skill](https://github.com/addyosmani/agent-skills/tree/main/skills/observability-and-instrumentation). The upstream repo was reported at 112,946 stars on 2026-11-03 and is MIT-licensed. The adaptation emphasizes existing `SyncRecord`, JSONL logs, SHA-256 manifests, and GitHub Actions; it does not add telemetry vendors or copy upstream reference files. |

The linked article groups skills, command-line tools, and reference files
together. Skills in this bundle are selected to complement capabilities already
installed in `.agents/skills/`; they are not a replacement for the existing
Python, FastAPI, API-design, testing, or security skills. The observability
adaptation targets this repository's Python data pipeline and GitHub Actions,
not an assumed HTTP backend. Reassess the backend skill selection if a separate
dashboard API is added.

The design skill creates a direction and the review skill checks the result.
This repository already has browser-testing skills such as `browser-qa` and
`e2e-testing`; no extra Playwright CLI or package installation is needed.

## IDE integration

| IDE / agent | Skill location |
| --- | --- |
| GitHub Copilot in VS Code | `.agents/skills/` |
| Antigravity | `.agents/skills/` (documented for the Antigravity App) |
| OpenCode | `.agents/skills/` (also supported natively; `.opencode/skills/` is an alternative) |
| Freebuff | Use the standard source bundle below. Automatic `.agents/skills/` discovery depends on Freebuff supporting the Agent Skills convention; use `--destination` if it requires another location. |

See the official [VS Code](https://code.visualstudio.com/docs/agent-customization/agent-skills),
[Antigravity](https://antigravity.google/docs/skills), and
[OpenCode](https://opencode.ai/docs/skills/) skill documentation. VS Code,
Antigravity App, and OpenCode document support for `.agents/skills/`.
Freebuff's native skill directory could not be verified from authoritative
documentation, so this setup does not claim automatic discovery there.

## Install and verify

Run from the repository root in PowerShell:

```powershell
python scripts\sync_vibe_skills.py
python scripts\sync_vibe_skills.py --check
```

By default, the script copies the skills into `.agents/skills/`. To export them
to another IDE's configured skill directory:

```powershell
python scripts\sync_vibe_skills.py --destination "C:\path\to\your\skills"
```

The script uses only the Python standard library. It validates skill metadata,
keeps the canonical files in this folder, never deletes files, and refuses to
overwrite an existing skill with different contents. The local `.agents/`
installation is ignored by Git in this repository; edit the canonical source
here and re-run the script to update it.
