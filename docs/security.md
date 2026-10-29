# Trust boundaries

This is a **local developer toolkit**, not a general-purpose vulnerability scanner or security certification.

- The `hardening.py scan` operation reads only selected source extensions and Git-index *filenames* of tracked environment files. It deliberately excludes `.env` contents and redacts all source snippets from findings. It does not execute repository code or call the network.
- Running build/test/security commands via `funnel.py run` **does execute** those target commands. Review untrusted `package.json` scripts, Python build hooks, CI scripts and dependency installation before execution. Use an isolated disposable environment and no production credentials for suspicious projects.
- `hardening.py gate` recomputes static signals and compares with the saved report. A passing gate proves only that its particular patterns were not present in inspected sources at that point. It is NOT a check for current dependency CVEs, runtime authorization, cloud configuration, or cross-user data access.
- A check logged with `--kind security` can still be a mislabeled command; the gate adds a constrained source-bound `--kind hardening` evidence requirement to high-risk implementation tracks. Human reviewer responsibility remains.
- Findings are heuristics, with explicit confidence; lack of a finding is not proof that a vulnerability does not exist. Disappeared source patterns can be caused by moving code or obfuscation, not necessarily remediation.
- Skill Forge-created instructions may be untrustworthy. They are project-local, bounded, structural-validated, and must be reviewed before executing unusual instructions. No arbitrary untrusted skills should be installed globally.
- Codex subagent TOML files define role guidance, not isolation or permission escalation. Agents share permissions from the parent environment. The installation never automatically modifies trusted parent config.
- No external network scanning, real user-account testing, credential validation, data extraction, deletion, paid service, production migration or deployment without separate explicit authority.
- The static analyzer does not detect active malware or malicious package install hooks. Do not use this system as a substitute for professional security assessments for high-risk systems.

Use OWASP ASVS 5.0 for scoped verification requirements, and OWASP WSTG for authorized, safe test planning. When blockers remain, report them; do not declare the project secure.
