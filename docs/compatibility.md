# AI agent compatibility matrix and limitations — 29 October 2026

Portability means **instruction-format compatibility**, not identical runtimes. Check the links for revisions before shipping.

| Agent | Documented native skill directory | Notes |
|---|---|---|
| Codex | `.agents/skills` | Invoke `$funnel-engineer`; optional `.codex/agents` role configs are Codex-only |
| Claude Code | `.claude/skills` | Invoke `/funnel-engineer`; role TOMLs do not apply |
| Cursor | `.cursor/skills` or `.agents/skills` | Skill discovery does not by itself provide subagent orchestration |
| Gemini CLI | `.gemini/skills` or `.agents/skills` | Can activate skills; CLI availability and permissions depend on host |
| GitHub Copilot | `.github/skills` or `.agents/skills` | Support varies among CLI, VS Code and cloud environments |
| OpenCode | `.opencode/skills` or `.agents/skills` | Skill tool must be enabled/allowed; respects host permission configuration |

The `--agent all` installer writes to two locations: `.agents/skills` (most) and `.claude/skills`. If a host also reads the other root, identical duplicate names may show in selectors. Prefer `--agent <host>` for host-targeted installations.

## Sources
- OpenAI Codex: https://learn.chatgpt.com/docs/build-skills
- Anthropic Claude Code: https://code.claude.com/docs/en/skills
- Cursor: https://cursor.com/help/customization/skills
- Gemini CLI: https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/using-agent-skills.md
- GitHub Copilot: https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills
- OpenCode: https://opencode.ai/docs/skills
- Open Agent Skills standard: https://agentskills.io

## Portability rules
- Keep required YAML fields `name` and `description` identical to the skill folder and purpose.
- Never include host-specific APIs as a prerequisite for core funnel execution.
- Use explicit filesystem path to the Python CLI. A skill does not automatically install or execute CLI tooling.
- For skill generation, use `--host shared` to write `.agents/skills` or `--host claude|cursor|gemini|copilot|opencode` for the native project skill directory.
- Never assume the role files in `codex/agents/` run in another host.
- For hosted/cloud agents, project skills must be in a workspace the host actually receives. Local user-level installation may not be shared with cloud workers.
- Always report whether the host ran tests and whether a separate reviewer actually participated.
