# AICOR Phase 2 — Multi-agent environment audit

Audit date: 2026-10-04. Scope was read-only discovery and documentation. No AICOR source code was implemented and no previously installed skill was reinstalled.

## 1. Detected tools

- VS Code `1.140.0` with OpenAI ChatGPT/Codex-related, Gemini Code Assist, ZenMux, and DeepSeek Copilot extensions.
- Claude Code `2.1.185`.
- Gemini CLI `0.35.0`.
- OpenCode Desktop `2.0.14` with embedded CLI binary.
- Freebuff Desktop `0.0.158`.
- Antigravity `2.19.1` and Antigravity IDE `2.5.5`.
- Git `2.56.0`, Node `24.14.0`, npm/npx `11.9.0`, uv `0.11.22`, PowerShell `5.1.26100.9444`.

## 2. Not detected or blocked

- Codex CLI: not on PATH; Codex skills exist but live CLI loading is not testable.
- OpenCode CLI: embedded binary exists, but `--version` is blocked by log-file permission failure.
- Freebuff CLI: no PATH command; Desktop is present.
- 9Router: no local installation evidence.
- Python version, pip, pnpm, SQLite CLI: not verified/not detected as recorded in [.ai/ENVIRONMENT.md](./.ai/ENVIRONMENT.md).

## 3. Skills actually installed

- Vercel: `vercel-composition-patterns`, `vercel-react-best-practices`, `web-design-guidelines`.
- OpenAI/Codex: `playwright`, `security-best-practices`.
- Claude Code: Superpowers `6.4.2`, enabled user plugin.
- Spec Kit `1.1.1.dev0`: CLI/workflow, not an Agent Skill.

Paths, commits, and compatibility are in [.ai/SKILLS_REGISTRY.md](./.ai/SKILLS_REGISTRY.md).

## 4. Skill compatibility matrix

The matrix is maintained in [.ai/SKILLS_REGISTRY.md](./.ai/SKILLS_REGISTRY.md). Key result: Vercel skills are shared-discovery candidates for OpenCode through `~/.agents/skills`; Antigravity needs an adapter/copy into its documented `~/.gemini/config/skills`; Freebuff/9Router depend on an upstream agent.

## 5. OpenAI/Codex

OpenAI skills are physically present, and the official OpenAI documentation describes `SKILL.md` directories and restart-based discovery. Codex CLI is not detected, so runtime recognition is UNKNOWN. OpenAI docs MCP is not configured locally. No API key was printed or changed.

## 6. OpenCode

OpenCode Desktop is installed at `C:/Users/ACER/AppData/Local/Programs/@opencodedesktop` version `2.0.14`. Its embedded CLI exists but cannot open `C:/Users/ACER/.local/share/opencode/log/opencode.log` in this sandbox. Official docs identify `~/.agents/skills` as an external skill path and `opencode.json` as the MCP/config mechanism. No project config was created.

## 7. Antigravity

Antigravity and Antigravity IDE are installed. Built-in skills exist under `C:/Users/ACER/.gemini/antigravity/builtin/skills` and the MCP config exists at `C:/Users/ACER/.gemini/config/mcp_config.json` with one server entry. The official custom skill directory `C:/Users/ACER/.gemini/config/skills` is absent, so Vercel skills are not claimed as natively discovered there.

## 8. Freebuff

Freebuff Desktop is installed and is an AI coding agent/desktop runtime built on Codebuff. The official repository describes local Claude Code/Codex connectivity, but no native Agent Skills, MCP, OpenAI-compatible custom endpoint, or Freebuff CLI was verified locally. It therefore depends on the upstream agent for skill support.

## 9. 9Router

No local 9Router installation was found. Its official repository describes a local API router, not a skill runtime, with a documented OpenAI-compatible `/v1` endpoint when installed. No endpoint, provider, model alias, credential, fallback, or tool-call configuration was created or assumed.

## 10. Gemini

Gemini CLI package `0.35.0` and Antigravity products are present. Direct PowerShell `.ps1` invocation is blocked by execution policy; the `.cmd` shim did not produce a usable version response in this sandbox. No global policy was changed. Antigravity built-in skill/MCP files were discovered independently.

## 11. MCP status

Antigravity MCP config exists. OpenCode supports MCP but is blocked at startup by log permissions. VS Code supports MCP, but no project MCP file exists. No MCP server was changed.

## 12. Persistent memory

The shared memory files remain present in [.ai/](./.ai/), with updated environment, skill compatibility, MCP, state, and handoff records. [AGENTS.md](./AGENTS.md) remains the canonical project instruction file.

## 13. Blockers

- No AICOR source or `PROJECT_SPEC_CMU.md` exists in the workspace.
- Workspace is not a Git repository.
- OpenCode CLI cannot write its log under the current sandbox permissions.
- Antigravity custom skill directory is absent.
- Codex CLI is not on PATH.
- Freebuff CLI and 9Router are not installed.
- Runtime skill-trigger smoke tests were not run.

## 14. Exact next actions

1. Restart/reload Codex, Claude, OpenCode, Antigravity, Gemini, and VS Code agent sessions so skill discovery can refresh.
2. In OpenCode, resolve the user-level log permission issue, then run its read-only version/config checks.
3. In Antigravity, use its official skill manager or documented `~/.gemini/config/skills` path; do not copy blindly.
4. If 9Router is later intentionally installed, configure only its official endpoint/provider flow and record the actual state.
5. Place the AICOR source and `PROJECT_SPEC_CMU.md` into the workspace before any project build, architecture, or dependency work.

Official references: [OpenAI Skills](https://developers.openai.com/api/docs/guides/tools-skills), [VS Code custom instructions](https://code.visualstudio.com/docs/agent-customization/custom-instructions), [VS Code MCP](https://code.visualstudio.com/docs/agent-customization/mcp-servers), [OpenCode skill configuration](https://github.com/anomalyco/opencode/blob/dev/packages/core/src/plugin/skill/customize-opencode.md), [Antigravity skills](https://codelabs.developers.google.com/getting-started-with-antigravity-skills?hl=en), [Freebuff](https://github.com/CodebuffAI/freebuff), and [9Router](https://github.com/decolua/9router).
