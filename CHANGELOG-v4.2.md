# Funnel v4.2 — 2026-10-29

- Added `harden` track for AI-generated and legacy app rescue, with all eight gates and automatic high-risk classification.
- Added `fes-vibe-hardening` and `fes-evaluation` specialist skills (total 21).
- Added `tools/hardening.py`, offline static heuristic source audit, before/after compare, live re-scan gate, no secret values in findings, and bounded scope.
- Enforced `hardening` check kind for high-risk implementation tasks; it must use this package's checker against the target repo, in addition to recorded `test` and `security` checks.
- Added `tools/inventory.py` and `tools/evaluation.py` (scorer of provided paired trials; does not launch agents).
- Corrected five Codex role TOMLs with required name/description/instructions; removed unsupported sandbox overrides; added security auditor role.
- Upgraded installer to back up existing same-name Codex role files as well as skills, without touching main Codex configuration.
- Added test coverage for stale audits, forged report contents, secret leakage, oversized files, role upgrades, and hardening quality gate.
- Preserved v4.1 Skill Forge, task tracks, command logs, and checkpoint model. No live production app or Codex end-to-end agent benchmarks have been executed.
