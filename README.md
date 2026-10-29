# Funnel Engineering System

**A structured engineering workflow for AI coding agents — debug, repair, review, and verify AI-generated code.**

[![CI](https://github.com/modassarislam37/funnel-engineering-system-github-ready-v5/actions/workflows/ci.yml/badge.svg)](https://github.com/modassarislam37/funnel-engineering-system-github-ready-v5/actions/workflows/ci.yml)
[![MIT licensed](https://img.shields.io/badge/license-MIT-256052)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-586a7a)](manifest.json)
[![22 skills](https://img.shields.io/badge/agent%20skills-22-c85231)](skills)

**[Website](https://modassarislam37.github.io/funnel-engineering-system-github-ready-v5/)** · **[Quickstart](docs/quickstart.md)** · **[Installation](docs/installation.md)** · **[Security](SECURITY.md)** · **[Contributing](CONTRIBUTING.md)**

Funnel Engineering System (FES) v5 is an open-source toolkit for **AI coding agent skills**, **vibe-code repair**, **bug investigation**, **security-aware review**, and **evidence-gated software delivery**. It combines 22 `SKILL.md` workflows with a Python checkpoint engine and installers for six coding-agent environments. It does **not** promise to find all vulnerabilities or automatically guarantee correct code.

## Why use FES?

| Without a structured workflow | With Funnel Engineering System |
|---|---|
| “It looks fixed” | Tests, evidence logs and limitations recorded |
| Unplanned rewrites | Reproduce first; make bounded changes |
| Hidden security assumptions | Static warnings and dedicated review gates |
| One-size-fits-all prompts | Targeted specialist skills and optional Skill Forge |
| Handoff without context | Explicit checkpoints and reviewable delivery notes |

> **Key idea:** Your AI agent can write code. The funnel asks it to demonstrate what was actually verified.

## Quickstart

Requirements: **Python 3.10+ on macOS/Linux**, Git, and an AI coding agent.

```bash
git clone https://github.com/modassarislam37/funnel-engineering-system-github-ready-v5.git
cd funnel-engineering-system-github-ready-v5
python3 tools/validate_package.py
python3 tools/install_portable.py --agent codex --scope user --profile rescue --dry-run
# Review the planned installation, then remove --dry-run:
python3 tools/install_portable.py --agent codex --scope user --profile rescue
```

Replace `codex` with `claude`, `cursor`, `gemini`, `copilot` or `opencode`. The **rescue** profile focuses on debugging and hardening existing applications; use `core` for ordinary development or `full` for every specialist.

In your AI coding agent, open a project you own and request:

```text
Use the funnel-engineer skill and the harden track.
Inspect this project, reproduce bugs, identify security risks,
fix confirmed issues in targeted changes, run regression tests,
and report verified evidence and unresolved problems.
Do not push, deploy or access production secrets.
FES tools: /absolute/path/to/funnel-engineering-system-github-ready-v5/tools
```

## Three skill profiles

| Profile | Skills | Best for |
|---|---:|---|
| `core` | 9 | Features, refactors and routine debugging |
| `rescue` | 11 | Broken AI-generated apps and security-aware reviews |
| `full` | 22 | Broad product, backend, frontend, AI, CI and delivery work |

## Supported coding-agent installers

| Agent | CLI argument | Project skill location |
|---|---|---|
| OpenAI Codex | `codex` | `.agents/skills/` |
| Claude Code | `claude` | `.claude/skills/` |
| Cursor | `cursor` | `.cursor/skills/` |
| Gemini CLI | `gemini` | `.gemini/skills/` |
| GitHub Copilot | `copilot` | `.github/skills/` |
| OpenCode | `opencode` | `.opencode/skills/` |

**Compatibility means installer/path support, not demonstrated equivalent autonomous performance in every host.** Review [compatibility notes](docs/compatibility.md). The `all` shortcut writes to the shared and Claude skill roots—not all six native directories.

## Project map

```text
.github/     Community templates and CI
codex/       Optional Codex role definitions
docs/        Documentation and paper-style landing website
skills/      22 portable SKILL.md definitions
templates/   Policy templates
tests/       Python engineering framework regression tests
tools/       Checkpoint engine, installers, hardening checks, Skill Forge
```

The [website](https://modassarislam37.github.io/funnel-engineering-system-github-ready-v5/) is served from `docs/` with no frontend build step. See [publishing instructions](docs/PUBLISHING.md) for GitHub Pages configuration.

## Engineering assurances and limitations

- Checkpoints, file hashes, evidence logging and bounded recovery are implemented in Python.
- The offline hardening scanner uses **limited heuristics**, not comprehensive static or dynamic analysis, penetration testing, dependency CVE monitoring or a security certification.
- A green test suite verifies the **framework's tested scenarios**, not every real-world app or AI agent.
- Installed skill files refer back to this repository's Python tools; keep your checkout in a stable location.
- Production changes, deployments, live security probing and access to private credentials require authorization.

## Documentation

[Quickstart](docs/quickstart.md) · [Installation](docs/installation.md) · [Architecture](docs/architecture.md) · [Vibe-code hardening](docs/hardening.md) · [Skill Forge](docs/skill-forge.md) · [Compatibility](docs/compatibility.md) · [Evaluation](docs/evaluation.md) · [Operating model](docs/operating-model.md) · [Publishing and SEO](docs/PUBLISHING.md)

## Contributing and development

```bash
python3 -m pip install -r requirements-test.txt
python3 tools/validate_package.py
python3 -m unittest discover -s tests -v
python3 tools/smoke_test.py
python3 tools/hardening_smoke_test.py
python3 -m unittest tests/test_site.py -v
```

See [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). FES is independent of the six agent vendors. **MIT licensed**; maintained by [Modassar Islam](https://github.com/modassarislam37).
