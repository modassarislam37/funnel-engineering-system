---
name: fes-recovery
description: Recover engineering funnel stages from failed tests, mismatched contracts, stale evidence, and bounded repeated attempts without declaring false success.
---
# Failure recovery

- Distinguish code failure, test harness failure, permission failure, transient dependency, and unmet acceptance criterion.
- Inspect exit code/log and reproduce failure before editing. Never treat a zero-test selection as passing.
- If implementation is at fault, use `funnel.py recover --reason '<root cause>'`. The local state returns to G4 and downstream passes are invalidated. Apply the smallest targeted fix; pass G4 with new evidence; execute a fresh test after G4.
- If the requirement or architecture is wrong, `reopen` G2/G3 rather than patching code repeatedly.
- Retry budget is finite; exhausted attempt sets G4 BLOCKED. Escalate actionable specifics, never continue pretending success.
- If source changes after a pass, run `verify` to detect stale G4+ fingerprint, reopen G4, recheck and re-review.
- The CLI validates a recorded failure and stage order. It does not autonomously diagnose or modify source. The agent is responsible for real correction.
