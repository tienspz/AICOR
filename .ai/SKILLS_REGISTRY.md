# Skills and runtime compatibility registry

Audit date: 2026-10-05. This is a read-only Phase 3 validation. No skill was installed, removed, upgraded, or copied, and no project source was changed. A discoverable path does not prove that a live agent loaded or used a skill.

## Installed skill files and plugin

| Name | Source repository | Installed path | `SKILL.md` | Local version | Commit | Intended agent | Discovery evidence |
|---|---|---|---|---|---|---|---|
| `vercel-composition-patterns` | [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) | `C:\Users\ACER\.agents\skills\vercel-composition-patterns\SKILL.md`; `C:\Users\ACER\.claude\skills\vercel-composition-patterns\SKILL.md` | Present in both paths | `1.0.0` (frontmatter) | Not recorded in local install | Agent Skills-compatible agents; local copies target Codex/OpenAI, Claude Code, and OpenCode discovery paths | Files and frontmatter verified; live skill invocation not verified |
| `vercel-react-best-practices` | [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) | `C:\Users\ACER\.agents\skills\vercel-react-best-practices\SKILL.md`; `C:\Users\ACER\.claude\skills\vercel-react-best-practices\SKILL.md` | Present in both paths | `1.0.0` (frontmatter) | Not recorded in local install | Agent Skills-compatible agents; local copies target Codex/OpenAI, Claude Code, and OpenCode discovery paths | Files and frontmatter verified; live skill invocation not verified |
| `web-design-guidelines` | [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) | `C:\Users\ACER\.agents\skills\web-design-guidelines\SKILL.md`; `C:\Users\ACER\.claude\skills\web-design-guidelines\SKILL.md` | Present in both paths | `1.0.0` (frontmatter) | Not recorded in local install | Agent Skills-compatible agents; local copies target Codex/OpenAI, Claude Code, and OpenCode discovery paths | Files and frontmatter verified; live skill invocation not verified |
| `playwright` | [openai/skills](https://github.com/openai/skills) | `C:\Users\ACER\.codex\skills\playwright\SKILL.md` | Present | No version/commit recorded in local skill metadata | Not recorded in local install | Codex / OpenAI ChatGPT IDE extension | File verified; Codex CLI absent; live selection not verified |
| `security-best-practices` | [openai/skills](https://github.com/openai/skills) | `C:\Users\ACER\.codex\skills\security-best-practices\SKILL.md` | Present | No version/commit recorded in local skill metadata | Not recorded in local install | Codex / OpenAI ChatGPT IDE extension | File verified; Codex CLI absent; live selection not verified |
| Superpowers plugin | [obra/superpowers](https://github.com/obra/superpowers) | `C:\Users\ACER\.claude\plugins\cache\superpowers-marketplace\superpowers\6.4.2` | Plugin cache present | `6.4.2` (Claude Code plugin listing) | Not recorded in local plugin listing | Claude Code | `claude plugin list` reports enabled; actual skill invocation not verified |

No local source commit was found for the Vercel skills, OpenAI skills, or Superpowers plugin. The Vercel `1.0.0` value is the `SKILL.md` frontmatter version, not a Git commit.

## Compatibility matrix

Cells contain only the requested status values. `PARTIAL` means there is evidence for some relevant capability or supported discovery path, but live/runtime use is unverified or incomplete.

| Capability | OpenAI/Codex | Claude Code | OpenCode | Antigravity | Freebuff | 9Router |
|---|---|---|---|---|---|---|
| Shared `AGENTS.md` | PARTIAL | PARTIAL | UNKNOWN | UNKNOWN | UNKNOWN | UNSUPPORTED |
| Vercel Skills | PARTIAL | PARTIAL | PARTIAL | BLOCKED | UNKNOWN | UNSUPPORTED |
| OpenAI Skills | PARTIAL | UNSUPPORTED | UNSUPPORTED | UNSUPPORTED | UNKNOWN | UNSUPPORTED |
| Superpowers plugin | UNSUPPORTED | VERIFIED | UNKNOWN | UNSUPPORTED | UNKNOWN | UNSUPPORTED |
| Spec Kit as an Agent Skill | UNSUPPORTED | UNSUPPORTED | UNSUPPORTED | UNSUPPORTED | UNSUPPORTED | UNSUPPORTED |
| MCP | UNKNOWN | PARTIAL | PARTIAL | PARTIAL | UNKNOWN | UNSUPPORTED |
| Shared `.ai/` memory | PARTIAL | PARTIAL | UNKNOWN | UNKNOWN | UNKNOWN | UNSUPPORTED |

## Discovery details and limitations

- **OpenAI/Codex:** both OpenAI skills exist under `~/.codex/skills`; Vercel skills exist under `~/.agents/skills`. OpenAI's Codex documentation describes both the user `~/.agents/skills` location and skill support in its IDE extension. The VS Code `openai.chatgpt` extension is installed, but no live skills panel/session was validated. Exact CLI result: `Codex CLI not installed / not available on PATH`.
- **Claude Code:** all three Vercel skills are under `~/.claude/skills`, a Claude Code skills location. `claude plugin list` confirms Superpowers `6.4.2`, user scope, enabled. A read-only `claude -p` skill invocation was attempted from `%TEMP%` and returned `Not logged in · Please run /login`; authentication was not attempted. Therefore actual Vercel skill loading and Superpowers skill execution remain untested.
- **OpenCode:** Desktop and embedded CLI are installed at `C:\Users\ACER\AppData\Local\Programs\@opencodedesktop`; version `2.0.14`. The CLI's `--version` and `--help` both succeeded. Official OpenCode skills documentation lists global `~/.agents/skills`, so the three Vercel directories are eligible for discovery. The active OpenCode skill list was not queried. A prior log-permission failure did not reproduce in the current safe version/help checks; no permission change was made.
- **Antigravity:** app version `2.19.1`; Antigravity IDE version `2.5.5`. Built-in skills exist under `C:\Users\ACER\.gemini\antigravity\builtin\skills`. Its documented global custom directory `C:\Users\ACER\.gemini\config\skills` is absent. Antigravity documentation also describes project-scoped `<project-root>\.agents\skills`, but this workspace has no such directory; the installed Vercel copies are in the user-level `C:\Users\ACER\.agents\skills`, which is not documented as Antigravity's global path. Thus the current third-party skills are not verified discoverable by Antigravity. To use compatible skills, put only individually reviewed skills in its documented global directory or a project-scoped `.agents\skills` (if appropriate); do not bulk-copy them. An MCP config file exists, but its server connection was not tested.
- **Freebuff:** Desktop version `0.0.158` is installed; no `freebuff` CLI is on PATH. Its official repository describes its own coding-agent runtime and says Desktop can run locally installed Claude Code and Codex agents. The reviewed local and official evidence does not establish that Freebuff imports shared Agent Skills, accepts arbitrary OpenAI-compatible endpoints, or supports MCP. Those capabilities remain UNKNOWN, not assumed unsupported.
- **9Router:** no local executable, package, or endpoint was detected. The official repository describes an API/model router with an OpenAI-compatible `/v1` endpoint and model/provider selection/fallback. It is not an agent runtime, Agent Skill host, or MCP capability; those skill/MCP classifications are UNSUPPORTED.

## Spec Kit classification

`C:\Users\ACER\.local\bin\specify.exe` is installed. `specify version` reports `1.1.1.dev0`; `specify --help` succeeded and lists workflow/setup commands. Spec Kit is a **Workflow / CLI tool**, not an Agent Skill. Its execution was smoke-tested; no project was initialized.

## Smoke-test summary

| Check | Result |
|---|---|
| Skill and plugin files/paths | Verified on disk for all five skills and the Superpowers plugin |
| Claude Code version and plugin listing | Succeeded; Superpowers is enabled |
| Claude actual Vercel skill invocation | Blocked by unauthenticated CLI; no login attempted |
| OpenCode embedded CLI `--version` and `--help` | Succeeded (`2.0.14`); no skill invocation attempted |
| Spec Kit `version` and `--help` | Succeeded (`1.1.1.dev0`); no project initialized |
| Codex CLI | Not installed / not available on PATH |
| Antigravity external-skill discovery | Blocked by absent documented custom skill directory |
| Freebuff and 9Router skill runtime | Not verified / unsupported as detailed above |

The environment is **not fully skill-ready or runtime-verified**. Paths and installation evidence are not equivalent to actual agent selection and execution.

## Official references

- [OpenAI/Codex Skills](https://developers.openai.com/codex/skills/)
- [Claude Code Skills](https://code.claude.com/docs/en/skills)
- [Claude Code Plugins](https://code.claude.com/docs/en/plugins)
- [OpenCode Skills](https://opencode.ai/docs/skills/)
- [OpenCode MCP](https://opencode.ai/docs/mcp-servers/)
- [Antigravity Skills](https://codelabs.developers.google.com/getting-started-with-antigravity-skills?hl=en)
- [Freebuff](https://github.com/CodebuffAI/freebuff)
- [9Router](https://github.com/decolua/9router)
