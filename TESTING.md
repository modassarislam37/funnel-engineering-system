# Funnel Engineering System v4.2 — Test record (29 October 2026)

## Executed checks

- `python3 -m unittest discover -s tests -q`: **69 tests passed**.
- `python3 tools/validate_package.py`: **PASS** (manifest, 21 skills, 5 role TOMLs with required fields, tools).
- `python3 tools/smoke_test.py`: **PASS**, disposable normal-build flow G0–G7 and two real Python application tests.
- `python3 tools/hardening_smoke_test.py`: **PASS**, deliberately broken local app, failing unit test, bounded recovery, corrected code, a fresh static heuristic scan, and G0–G7 hardening check. The smoke-test "security" check reuses the limited static gate; it is **not** an independent security review.
- Installer integration tests confirm backing up previously installed role TOMLs and skills and preserving existing main Codex configuration.
- Negative tests confirm blocked: missing/stale report, tampered JSON findings, high-severity static findings, no scanned source, oversized file, security command labeled as a no-op, wrong tool/target for hardening, project path escape, and security scanner secret-value leakage.

## What was not tested

- No real Codex session was driven to autonomously discover, fix, or secure a production application. Actual role delegation and skill activation remain host-dependent.
- No real external codebase, production environment, browser automation, cloud service, dependency CVE database or penetration test was used.
- No real baseline-vs-Funnel paired benchmark was run. `tools/evaluation.py` scores supplied measurements only.
- No claim is made that an offline heuristic scanner discovers all bugs/security vulnerabilities or that passing tests proves the absence of risk.
- Python CLI tests ran on the available Linux container, **not on the user's Mac**. The tools are designed for macOS/Linux; the macOS installation still needs local verification.

## Why this is useful

These checks validate the installed engineering *infrastructure*, deterministic state transitions, protected command classification and the demonstration repair loop. They do not measure model decision quality, comprehensive app security or deployment readiness.
