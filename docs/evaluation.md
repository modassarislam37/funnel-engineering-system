# Paired agent evaluation protocol

The evaluator scores *recorded* paired trials; it does not run Codex or authenticate reported metrics.

Each trial must contain `id`, `baseline`, and `candidate`. Each run requires exactly six nonnegative integer fields:
`tests_passed`, `tests_total`, `high_findings`, `critical_findings`, `scope_violations`, `human_interventions`.
A trial passes only if all selected tests pass, no high/critical vulnerabilities are left in the specified review scope, and no scope violations are recorded. **Zero tests is invalid.** An accurate evaluation requires relevant test coverage and an independent security review; a `high_findings: 0` assertion alone proves nothing.

```json
[
  {
    "id": "example-local-fixture-not-a-real-agent-benchmark",
    "baseline": {"tests_passed": 2,"tests_total": 3,"high_findings": 1,"critical_findings": 0,"scope_violations": 0,"human_interventions": 1},
    "candidate": {"tests_passed": 3,"tests_total": 3,"high_findings": 0,"critical_findings": 0,"scope_violations": 0,"human_interventions": 0}
  }
]
```

Run at least 10 balanced paired trials for a useful first comparison. Repeat high-variance cases, record actual logs and commits, use withheld fixtures, and separate workflow/tool validation from agent decision quality. Never populate a report with synthetic demo numbers and present it as a measured performance gain.
