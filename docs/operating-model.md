# Operating manual

Stage outputs: G0 scope/authority; G1 examined source and git status; G2 acceptance contract; G3 architecture, risk and reversible tasks; G4 changed code and actual diff; G5 checks with logs; G6 review findings/mitigations; G7 delivery and true deployment status.

Tracks: `build` runs G0–G7; `fix` and `refactor` skip G2; `quick` skips G2/G3; `review` skips G2/G4 and does not require running tests. A review must not claim tests passed if none ran. Quick track is intended for low-risk, narrow changes; use build for major features.

### Exact CLI usage

```bash
python3 tools/funnel.py init --project PROJECT --task SLUG --track build --risk normal --max-retries 3
python3 tools/funnel.py note --project PROJECT --task SLUG --gate G1 --text "Inspected routes and schema"
python3 tools/funnel.py advance --project PROJECT --task SLUG --gate G0 --evidence docs/evidence/scope.md
python3 tools/funnel.py run --project PROJECT --task SLUG --kind test --timeout 120 -- python3 -m unittest
python3 tools/funnel.py fail --project PROJECT --task SLUG --gate G4 --reason "Failed acceptance"
python3 tools/funnel.py recover --project PROJECT --task SLUG --reason "Last test revealed a real bug"
python3 tools/funnel.py reopen --project PROJECT --task SLUG --gate G3
python3 tools/funnel.py block --project PROJECT --task SLUG --gate G5 --reason "Missing device"
python3 tools/funnel.py handoff --project PROJECT --task SLUG --role reviewer --scope "Review auth module" --mode read
python3 tools/funnel.py handoff-result --project PROJECT --task SLUG --handoff-id H001 --status REPORTED --observed-by fes_reviewer --evidence docs/evidence/review.md
python3 tools/funnel.py status --project PROJECT --task SLUG
python3 tools/funnel.py verify --project PROJECT --task SLUG
python3 tools/funnel.py report --project PROJECT --task SLUG
```

A successful `run` command must be after G4 PASS for it to unlock G5; if the latest check of a required kind fails, an earlier success is not sufficient. Source files modified by the command itself cause exit code 125 on otherwise successful checks. Review any tools invoked; `run` does not use shell evaluation or provide sandboxing. State and log files have mode 0600 where supported.

A `recover` call requires last check failed and G4 was previously marked PASS. It returns the task to G4 and resets all downstream statuses; it does not modify source. The fourth failure on the default retry budget blocks progress.

**Staleness and integrity:** `verify` reports changed evidence, logs or code after a later gate passed. It does not track excluded docs, untracked non-source assets, changes outside the local project, active services or infrastructure.
