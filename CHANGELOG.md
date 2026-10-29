# Changelog

## v4.0.0 — 2026-10-29

- Retains v3's 16 skills and adds `fes-coordinator` and `fes-recovery`.
- Provides four opt-in Codex subagent role TOMLs with a non-destructive manual config snippet.
- Adds a scriptable CLI with POSIX advisory locking and atomic, private checkpoint writes.
- Fingerprints common source/config files and hashes evidence, logs and reported handoff results.
- Enforces stage ordering, test-result recency (post-G4), and a high-risk security-check category.
- Introduces bounded recovery attempts and downstream invalidation without auto-editing code.
- Provides conservative v3 migration, installer backups, package validation and end-to-end smoke test.
- Clarifies limits: no live subagent run in this package, no continuous background process or automated deployment, no correctness guarantee.
