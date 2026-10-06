# AICOR skills registry

Phase 3 status and the compatibility matrix are maintained in [.ai/SKILLS_REGISTRY.md](./.ai/SKILLS_REGISTRY.md).

Installed and filesystem-verified:

- Vercel: `vercel-composition-patterns`, `vercel-react-best-practices`, `web-design-guidelines`.
- OpenAI/Codex: `playwright`, `security-best-practices`.
- Superpowers plugin `6.4.2`; Claude Code reports it enabled.
- GitHub Spec Kit CLI `1.1.1.dev0`; this is a **Workflow / CLI tool**, not an Agent Skill.

Installation is distinct from live discovery and skill invocation. Current blockers/limits: `Codex CLI not installed / not available on PATH`; Claude skill invocation was blocked because the CLI is not logged in; Antigravity's documented custom skill directory is absent. OpenCode's embedded CLI is present and passed harmless version/help checks. See [.ai/ENVIRONMENT.md](./.ai/ENVIRONMENT.md) for runtime checks and [.ai/HANDOFF.md](./.ai/HANDOFF.md) for the next action.
