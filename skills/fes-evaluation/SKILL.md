---
name: fes-evaluation
description: Evaluate Funnel against standard agent with paired, held-out engineering tasks, reproducible quality evidence and explicit pass/fail metrics; use when assessing reliability or promoting a generated skill.
---

# Funnel Evaluation Laboratory

Build a small balanced evaluation corpus: ordinary feature, bugfix, refactor, auth regression, injection issue, dependency vulnerability, browser UI flow, rollback and a misleading static pattern.
Run **the same starting commit, permissions, test infrastructure and time budget** for baseline agent and Funnel candidate. Keep a held-out set not used in skill construction. Measure executed test success, security issues still open, scope violations and manual interventions. For security tests, use non-production local fixtures and no active exploitation of third-party systems.

Write each paired result in the JSON format under `docs/evaluation.md`. Evaluate with:
`python3 <FES_ROOT>/tools/evaluation.py --input paired-results.json --output comparison.json`

The scorer does **not** call the host agent or verify observations. A pass on the local Python fixture suite is not an agent-performance benchmark. No claim of improvement without actual paired experiments. Use measured outcomes to decide whether a generated skill is worth reusing.
