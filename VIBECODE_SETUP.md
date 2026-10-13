# Vibecode Environment

This workspace is configured project-locally for OpenCode and Antigravity.

## OpenCode

OpenCode config lives in `.opencode/opencode.json`.

Included:

- ECC full OpenCode profile under `.opencode/`
- Superpowers plugin and skill path from `.vibecode/sources/superpowers`
- Mem0 skills shared from `.agents/skills/`
- Cursor rules catalog skill, which searches the local `.mdc` catalog on demand
- Local MCP Memory server with persistent data in `.vibecode/memory/`
- MarkItDown MCP server via `uvx --from markitdown-mcp markitdown-mcp`

Start OpenCode from this workspace root:

```powershell
opencode
```

Useful checks inside OpenCode:

```text
use skill tool to list skills
Tell me about your superpowers
Use the markitdown MCP tool to convert a document to markdown
```

## Antigravity

Antigravity workspace config lives in `.agents/`.

Included:

- ECC Antigravity project profile under `.agents/`
- Superpowers bootstrap plugin at `.agents/plugins/superpowers`
- Official Mem0 skills under `.agents/skills/mem0*/`
- Cursor rules catalog skill under `.agents/skills/cursor-rules-library/`
- Local MCP Memory server with persistent data in `.vibecode/memory/`
- MarkItDown MCP server at `.agents/mcp_config.json`

Open this folder in Antigravity, then inspect Customizations to confirm workspace skills/plugins are active.

Useful checks inside Antigravity:

```text
/using-superpowers
/tdd-workflow
Use the markitdown MCP server to convert a file to markdown
```

## Added repositories and integrations

The following shallow checkouts are kept locally under `.vibecode/sources/`:

- `awesome-cursorrules` is a Cursor `.mdc` rule catalog, not an installable plugin. The `cursor-rules-library` skill searches and adapts a small number of relevant rules when requested.
- `mem0` provides the official Mem0 reference and six official skills. The skills are copied into `.agents/skills/` so both hosts can discover them.
- `mcp-servers` contains MCP reference implementations. Its Memory server is enabled in both hosts as `@modelcontextprotocol/server-memory`; this is a local knowledge-graph store, not the Mem0 SDK or Mem0 cloud service.

The Memory server writes to `.vibecode/memory/memory.jsonl`. The configured path is specific to this Windows workspace and should be updated in both `.opencode/opencode.json` and `.agents/mcp_config.json` if the workspace is moved. No Mem0 account, API key, or cloud connection is created.

Restart OpenCode and Antigravity after configuration changes. In each host, verify that the Mem0 skills and `cursor-rules-library` appear in the available skills, then check that the `memory` MCP server exposes its tools. The server package is fetched by `npx` on first launch, so Node.js/npm and network access are required.

## Updating

Refresh the source checkouts:

```powershell
git -C .vibecode\sources\ECC pull
git -C .vibecode\sources\superpowers pull
git -C .vibecode\sources\awesome-cursorrules pull --ff-only
git -C .vibecode\sources\mem0 pull --ff-only
git -C .vibecode\sources\mcp-servers pull --ff-only
```

After updating Mem0, review and refresh its six copied skill folders in `.agents\skills\` from `.vibecode\sources\mem0\skills\`. Then rebuild/apply ECC:

```powershell
npm.cmd install --prefix .vibecode\sources\ECC
npm.cmd run build:opencode --prefix .vibecode\sources\ECC
$env:OPENCODE_CONFIG_DIR = (Join-Path (Get-Location) '.opencode')
node .vibecode\sources\ECC\scripts\install-apply.js --target opencode --profile full --enable-hooks
node .vibecode\sources\ECC\scripts\install-apply.js --target antigravity --profile full --enable-hooks
```
