# Universal v5.0 installation and migration

## Preparation

Python 3.10+ on macOS/Linux, an installed supported AI coding agent, and permission to install user/project skills. Keep the downloaded FES package in a stable location. The actual checkpoint engine currently relies on POSIX file locking.

## Preview installation

```bash
python3 tools/install_portable.py --agent all --scope user --profile full --dry-run
```

`--agent` accepts `codex`, `claude`, `cursor`, `gemini`, `copilot`, `opencode`, or `all`.
`--scope` accepts `user` or `project`; project scope requires `--project /absolute/path/to/project`.
`--profile` accepts `core` (9 skills), `rescue` (11) or `full` (22).

## Install / upgrade

```bash
python3 tools/install_portable.py --agent all --scope user --profile full
# On previously installed skills, back up differences before overwriting:
python3 tools/install_portable.py --agent all --scope user --profile full --upgrade
```

A differing existing skill is skipped by default. `--upgrade` preserves prior content with a sibling `.fes-v5-backup-...` directory. Existing symlinks and unsafe targets are refused. `--agent all` writes common `.agents/skills` plus `.claude/skills` (two roots); hosts that read both may show duplicates. Use host-specific install to avoid duplicates. The installer does not alter normal host configuration, install dependencies, download content, or execute target-project scripts.

## Codex-specific optional roles

```bash
python3 tools/install_portable.py --agent codex --scope user --with-codex-roles --dry-run
python3 tools/install_portable.py --agent codex --scope user --with-codex-roles
```

This installs 5 role TOMLs and leaves a **manual** config snippet for you to review. It never edits your existing `.codex/config.toml`. Host support is not tested by the package.

## Use

Open a local application in your agent. Invoke `$funnel-engineer` (Codex) or `/funnel-engineer` (Claude), or ask the other host to use the `funnel-engineer` skill. Provide the location of the retained FES `tools/` directory; skills alone don't install or automatically execute a Python CLI.

## Legacy v4 installer

The old `tools/install.py` remains only to preserve v4 migration tests (21-skill legacy contract); use `tools/install_portable.py` for all v5 installations. Existing JSON task checkpoints and `tools/funnel.py` behavior remain compatible; treat stale source/evidence as needing reverification. Never overwrite a project with uncommitted changes without reviewing the diff first.

See `docs/compatibility.md`, `docs/quickstart.md` and `SECURITY.md`.
