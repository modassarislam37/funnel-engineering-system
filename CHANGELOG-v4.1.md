# v4.1.0 — Self-Extending Skill Forge (October 29, 2026)

- Added `fes-skill-forge` as an on-demand 19th specialist.
- Added `tools/skill_engine.py`: inventory, lexical search suggestions, bounded automatic project-only instruction skill creation, and SHA-256 receipt verification.
- Master orchestrator now assesses missing specialist skills before substantial implementation and explicitly applies a generated skill in the same session.
- Enforced max 2 generated skills per task and prevented overwriting or escaping project paths.
- Integrated generated skill receipt checking into `funnel.py verify` and report validation.
- Updated installer to create version-specific upgrade backups and config snippet without altering Codex main config.
- Preserved all v4 checkpoint schemas, roles, task tracks, and gate semantics.
- Added dedicated security/forge docs, comprehensive regression tests and a same-session CLI test.

No AI model is embedded in the CLI. Codex supplies the task analysis and proposed procedure; the CLI supplies safe local file operations and structural checks.
