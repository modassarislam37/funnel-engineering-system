# Five-minute start

1. Clone this repository into a stable folder using `git clone https://github.com/modassarislam37/funnel-engineering-system-github-ready-v5.git`. Python 3.10+ required.
2. Run `python3 tools/install_portable.py --agent <codex|claude|cursor|gemini|copilot|opencode|all> --scope user --profile rescue --dry-run`.
3. Run the same command without `--dry-run` to install. Restart the host if it does not discover skills immediately.
4. Open an app project you own with a clean Git snapshot; do not provide production secrets. Give the agent the FES folder's **absolute** path.
5. Prompt: "Use funnel-engineer and the harden track. Find and fix confirmed bugs and security issues, run tests, document evidence, and report remaining risks. No deployment or external systems."
6. Check that the resulting claims cite actual CLI results; continue debugging until tests pass or documented BLOCKED.

To generate a missing narrow project skill, first initialize the project task and then use `tools/skill_engine.py` with `forge --host shared` (or another native host directory using `--host <host>`). Skill generation is not proof of effectiveness.
