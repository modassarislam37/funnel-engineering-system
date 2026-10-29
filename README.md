# Funnel Engineering System

**Reusable engineering workflows for AI coding agents.**

[![CI](https://github.com/modassarislam37/funnel-engineering-system-github-ready-v5/actions/workflows/ci.yml/badge.svg)](https://github.com/modassarislam37/funnel-engineering-system-github-ready-v5/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](manifest.json)

FES v5 provides 22 skills, a local Python checkpoint CLI, and installers for six coding agents. Use it to investigate unfamiliar code, build features, repair bugs, review changes, and harden existing applications. Choose a workflow that fits the task; a small edit does not need a full engineering funnel.

Maintained by [Modassar Islam](https://github.com/modassarislam37). Start with the [quickstart](docs/quickstart.md).

## Choose your setup

| Profile | Use it for |
|---|---|
| `core` | Everyday features, bug fixes, reviews, and refactors |
| `rescue` | Investigating and hardening an existing application |
| `full` | All 22 skills, including AI, API, frontend, data, CI, and evaluation |

Clone the repository and validate the package with Python 3.10+:

```bash
git clone https://github.com/modassarislam37/funnel-engineering-system-github-ready-v5.git
cd funnel-engineering-system-github-ready-v5
python3 tools/validate_package.py
```

Choose one agent from the table below. Preview a project installation, then apply it:

```bash
python3 tools/install_portable.py --agent cursor --scope project --project /absolute/path/to/your-project --profile core --dry-run
python3 tools/install_portable.py --agent cursor --scope project --project /absolute/path/to/your-project --profile core
```

Replace `cursor` with your agent. Use `--scope user` without `--project` for a user-wide installation. Existing differing skills are skipped; `--upgrade` backs them up before replacement. Keep this FES checkout at a stable path: installed skills reference its Python tools, which are not copied into the target project.

## Coding agents

| Agent | `--agent` | Project skills | User skills |
|---|---|---|---|
| OpenAI Codex | `codex` | `.agents/skills/` | `~/.agents/skills/` |
| Claude Code | `claude` | `.claude/skills/` | `~/.claude/skills/` |
| Cursor | `cursor` | `.cursor/skills/` | `~/.cursor/skills/` |
| Gemini CLI | `gemini` | `.gemini/skills/` | `~/.gemini/skills/` |
| GitHub Copilot | `copilot` | `.github/skills/` | `~/.copilot/skills/` |
| OpenCode | `opencode` | `.opencode/skills/` | `~/.config/opencode/skills/` |

Each target has filesystem installer tests. Live skill discovery, tool execution, and delegation depend on the host and are not verified across these runtimes. See [compatibility](docs/compatibility.md). Other coding agents can explicitly read `skills/funnel-engineer/SKILL.md` and the relevant specialist files; automatic discovery is not assumed.

`--agent all` installs into two shared roots: `.agents/skills` and `.claude/skills`. It does **not** populate all six native directories. Choose explicit targets when your hosts need their native paths, and check for duplicate discovery.

Optional Codex role TOMLs are available through `--with-codex-roles` with `--agent codex` or `all`. They require manual configuration review and do not create agents by themselves. Other hosts retain their own configuration.

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

## Development

```bash
python3 tools/validate_package.py
python3 -m unittest discover -s tests -v
python3 tools/smoke_test.py
python3 tools/hardening_smoke_test.py
```

See [contributing](CONTRIBUTING.md) and [publishing](docs/PUBLISHING.md). Package validation checks structure; tests check the Python framework. Neither proves live agent effectiveness.
