---
name: fes-coordinator
description: Coordinate bounded host subagents and engineering handoffs while preventing overlapping edits and false claims of independent review.
---
# Multi-agent coordination

1. Classify tasks as independent read-only investigation, bounded implementation, verification or review.
2. Read the runtime's actual support before attempting to spawn. TOML configuration files provide **roles**, not an external running daemon.
3. Delegate only concrete scopes: assigned files, source revision, input artifacts, deliverable, allowed actions, excluded paths and stop condition.
4. Give architecture and security review read-only scope. Assign coding to ONE agent per ownership slice; coordinate shared interfaces with the controller.
5. If edits might overlap, serialize work or use approved separate Git worktrees. Agents working in a shared workspace must not race on files.
6. The orchestrator checks findings, reruns affected tests and resolves conflicts. A reviewer who worked on the patch cannot be labeled independent.
7. Use `funnel.py handoff` for a PREPARED record; only mark `handoff-result` after actual agent execution and a saved evidence report. Record the true runner (`observed-by`).
8. If role support unavailable, continue sequentially with specialists as instructions and disclose that no subagents ran.

Handoff response: inspected source/revision, changed paths, executed commands, findings, blockers, next owner.
