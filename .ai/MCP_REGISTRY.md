# MCP capability and configuration audit

Audit date: 2026-10-05. Read-only validation only. No MCP servers, credentials, or configuration were added, removed, or changed. The Antigravity config was parsed only to count server entries; names and values were not printed.

## Compatibility status

| Capability | OpenAI/Codex | Claude Code | OpenCode | Antigravity | Freebuff | 9Router |
|---|---|---|---|---|---|---|
| MCP support/configuration | UNKNOWN | PARTIAL | PARTIAL | PARTIAL | UNKNOWN | UNSUPPORTED |

`PARTIAL` means capability or config presence is evidenced, but an actual server connection/tool call was not tested.

## Evidence

- **Antigravity — PARTIAL:** `C:\Users\ACER\.gemini\config\mcp_config.json` exists and contains one server entry. The configuration values and server name were deliberately not read or disclosed; connection status is untested.
- **OpenCode — PARTIAL:** official docs support local and remote MCP servers configured in OpenCode config. The embedded CLI safely passed `--version` and `--help`, but no MCP server list or tool call was run. An existing `C:\Users\ACER\.config\opencode\service.json` is not treated as proof of MCP configuration.
- **Claude Code — PARTIAL:** Claude Code supports MCP in its documented plugin/config ecosystem. This audit did not inspect private user config or test a server; an actual Claude model invocation was blocked by the CLI's unauthenticated state.
- **OpenAI/Codex — UNKNOWN:** Codex CLI is not on PATH. The VS Code OpenAI ChatGPT extension is present, but no active MCP server/connection was tested.
- **Freebuff — UNKNOWN:** reviewed local and official evidence did not establish native MCP configuration or a successful MCP connection.
- **9Router — UNSUPPORTED:** it is an API/model router, not an MCP client/agent runtime.
- **Workspace — no MCP config created:** no `.mcp.json`, `.vscode/mcp.json`, or other project MCP file was added.

No server names, URLs, headers, keys, or environment variable values were displayed. See `.ai/ENVIRONMENT.md` for the runtime inventory and `.ai/SKILLS_REGISTRY.md` for the full skill compatibility matrix.
