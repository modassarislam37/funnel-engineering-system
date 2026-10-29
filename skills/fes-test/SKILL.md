---
name: fes-test
description: Test-driven regression and verifiable test evidence specialist for Funnel v4, including source-scoped checks and negative paths.
---
# Verification

Identify relevant project test runner and current expectations. For defects reproduce failure first when feasible; validate exact boundary rather than matching error strings alone. Do not disable tests to achieve PASS. Run targeted unit/integration tests, then broader tests if the change risk justifies it. Run typecheck/build/visual checks when relevant.

Use `python3 <FES_ROOT>/tools/funnel.py run --project . --task <slug> --kind test -- <test command>` after G4 is passed. A successful current-source test log is mandatory for G5 on implementation tracks. High-risk work also requires `--kind security` evidence; choose a defensible tool and explain its scope. G5 cannot pass based on prior G4 runs or stale checked code. Test output is private local metadata, but could contain secrets; avoid commands that print them.

Report checks actually executed, counts observed, failure reasons, accepted gaps and expected runtime environments. Do not claim CLI source fingerprints capture external provider state or deployment health.

## Hardening tasks
For an unfamiliar app, run existing tests first (after reviewing scripts), add failing regression tests for actual bugs, and verify the fixed behavior. Add API authorization tests for cross-user access, negative input tests for injection, UI smoke tests for main flows where available, and build/typecheck/lint checks. Disclose anything untestable; no zero-test passes.
