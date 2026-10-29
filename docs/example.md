# Example: build a CSV revenue dashboard

1. `G0` document constraints (local-only CSV, no user accounts), excluded features, real permissions.
2. `G1` inspect the actual project modules, current Git state, run commands and existing tests.
3. `G2` write acceptance cases: CSV upload, header/type errors, monthly chart, date filtering, growth KPI and empty state.
4. `G3` define CSV decoder → normalized rows → aggregation → UI; choose modules and integration tests.
5. `G4` implement a small working vertical slice; write `docs/evidence/implementation.md` with changed paths and observed behavior; advance G4.
6. `G5` run project tests with `funnel.py run --kind test -- <test-runner>`; optionally lint/build/visual, document coverage and failures. Advance with actual evidence.
7. `G6` read diff and check injection into export fields, excessive memory use, keyboard and mobile behavior; if Codex subagents are available, dispatch a separate reviewer. Save review notes.
8. `G7` provide local run steps, limitations, actual Git/PR/deploy state and checkpoints.

If a test fails, diagnose the error, run `recover` and fix G4. Re-run checks; do not reuse tests passed against prior code. Keep work local until authorized to publish or deploy.
