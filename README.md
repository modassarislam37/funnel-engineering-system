# Funnel Engineering System Universal v5.0

**Build, rescue, test and harden AI-generated applications using reusable Agent Skills across multiple coding agents.**

FES Universal takes the existing v4.2 engineering funnel and adds a cross-host installer, portable Skill Forge paths, three skill bundles, explicit host capability boundaries and public, community-friendly documentation. It retains the actual Python evidence-gate CLI, source-bound security checks, bounded failure recovery, 5 optional **Codex-only** role TOMLs, and the original regression tests.

## Supported installation targets

| Coding agent | Project skill location | User skill location | Tested here |
|---|---|---|---|
| OpenAI Codex | `.agents/skills/` | `~/.agents/skills/` | Filesystem install only |
| Claude Code | `.claude/skills/` | `~/.claude/skills/` | Filesystem install only |
| Cursor | `.cursor/skills/` | `~/.cursor/skills/` | Filesystem install only |
| Gemini CLI | `.gemini/skills/` | `~/.gemini/skills/` | Filesystem install only |
| GitHub Copilot | `.github/skills/` | `~/.copilot/skills/` | Filesystem install only |
| OpenCode | `.opencode/skills/` | `~/.config/opencode/skills/` | Filesystem install only |

These paths follow the product documentation linked in `docs/compatibility.md`. **The SKILL.md files are portable; agent runtimes, tool permissions, skill-discovery refresh and subagents are not interchangeable.** No live host integration is claimed. Other agents can use the files manually if they support instructions, but are not tested/adapted here.

## Install (Python 3.10+; macOS/Linux)

Extract the ZIP, open Terminal in its top-level directory:

```bash
python3 tools/validate_package.py
python3 -m unittest discover -s tests -v
python3 tools/install_portable.py --agent all --scope user --profile rescue --dry-run
python3 tools/install_portable.py --agent all --scope user --profile rescue
```

`--agent all` uses **two shared roots**: `.agents/skills` (Codex, Cursor, Gemini, Copilot, OpenCode) and `.claude/skills` (Claude). Some hosts can discover both and may display duplicates. For no duplication, use one target-specific `--agent`. Do not edit both installed copies independently. Existing differing files are skipped unless you opt into `--upgrade`, which creates per-skill backups.

To install all skills in a single project:

```bash
python3 tools/install_portable.py --agent cursor --scope project --project /path/to/project --profile full
```

For Codex-only optional subagent TOMLs:

```bash
python3 tools/install_portable.py --agent codex --scope user --with-codex-roles --dry-run
```

No host config is silently merged. Optional role files don't automatically create real subagents; verify what your host actually supports.

## What to say to your agent

> Use the `funnel-engineer` skill. Audit and repair this existing AI-generated application using the `harden` track. Inspect repository rules and git status, identify root causes, fix confirmed bugs and vulnerabilities, add regression tests, run relevant actual checks, and report unresolved risks. Do not deploy, push, read production credentials, or run intrusive checks. Use the local FES tools at `/path/to/fes/tools` and follow G0–G7.

Invocation varies: Codex `$funnel-engineer`, Claude Code `/funnel-engineer`, other hosts via their skill selection or natural-language request. When skill discovery is unavailable, explicitly ask the agent to read the installed `SKILL.md` file.

## Open source and contributing

Released under the [MIT License](LICENSE). Contributions are welcome: see [CONTRIBUTING.md](CONTRIBUTING.md), [Code of Conduct](CODE_OF_CONDUCT.md), and [Security Policy](SECURITY.md).

**New to this project?** Try [the quickstart](docs/quickstart.md). If you want to publish your own fork, see [docs/PUBLISHING.md](docs/PUBLISHING.md).

This project is independent and not affiliated with Codex, Claude Code, Cursor, Gemini, GitHub Copilot, OpenCode or Orbyn. The reusable Agent Skills pattern is supported to varying degrees by each host. It is not verified end-to-end across all six runtimes.

## How to help

Open issues with reproductions, submit narrow PRs with tests, or contribute a skill that addresses a demonstrated gap. **Do not** submit third-party project code, credentials, customer data, or sensitive vulnerability details.

## Honest limits

The hardening scanner is an offline heuristic, not full SAST/DAST, a dependency-CVE subscription, penetration testing, or proof of security. Agents can miss bugs; verified fixes remain scoped to executed checks. The installer never executes project code, downloads plugins, changes main host config, or starts agents. Python tooling currently requires POSIX file locking (macOS/Linux); on Windows use a supported Unix-like environment if available. The portable installer itself is cross-platform Python, but the checkpoint engine has POSIX assumptions.

**Tests:** original v4.2 suite plus new portable-install tests. `TESTING-v5.md` reports the actual results from the current build.

## Publish this distribution to GitHub

To upload the complete source to the designated **empty** repository, run `python3 tools/publish_to_github.py --dry-run` followed by `python3 tools/publish_to_github.py` from the extracted release directory. See [publishing instructions](docs/PUBLISHING.md).
