# Rescue mode for unfamiliar AI-generated (“vibe-coded”) applications

**This is defensive local engineering, not an active penetration-testing toolkit.** Before using npm/pip scripts or installing dependencies, review manifests; project scripts can be hostile. Use a disposable local branch/worktree, protect user data and avoid production secrets. Always inspect current git status.

## Fast safe preflight

```bash
python3 /path/to/fes/tools/hardening.py scan --project /path/to/app --output .funnel/audits/before.json
```

The scan is **non-executing and offline**. It reports source-pattern leads and Git-tracked `.env` filenames; it never reads the `.env` contents or prints source lines. Flags include Python shell=True, eval/exec, SQL interpolation, JavaScript innerHTML/React raw HTML, Node exec, insecure TLS, wildcard CORS, unsigned JWT and apparent hardcoded secrets. Some are false positives; absence of flags is not proof of security. Scans intentionally skip tests, docs, generated/dependency folders and files over 1MB (oversized files block the gate).

## Structured manual review

Use OWASP ASVS 5.0, supplemented with CWE and language-specific references. Verify reachable paths, authentication, access control/IDOR, privilege escalation, injection, XSS, SSRF, secrets, session handling, tenant isolation, unsafe upload/storage, dependency advisories, build pipeline, default credentials and error handling. Risk ranking depends on exploitability and asset sensitivity. Mark testing gaps and unresolved uncertain findings. Never test against real user accounts or third-party services without explicit authorization.

## Repair loop

1. Record actual failing behavior and create minimal regression tests.
2. Fix one issue and re-run targeted checks.
3. Run a fresh scan into `.funnel/audits/after.json`.
4. Compare: `python3 tools/hardening.py compare --project . --before .funnel/audits/before.json --after .funnel/audits/after.json`.
5. Confirm results with actual tests and review. A disappearing pattern is NOT a verified fix.
6. High-risk hardening gate: `python3 tools/hardening.py gate --project . --report .funnel/audits/after.json`.
7. When tracked `.env` or hardcoded credentials are found, treat rotation and history cleanup as a separately authorized operational task. Do not print the value.

The gate fails when the scan is stale, incomplete for oversized scanned source, or reports remaining high/critical heuristic findings. It doesn't validate dependencies, runtime auth, business logic or all application vulnerabilities.

## Permission model

Local source edits are allowed when explicitly requested. No silent package installs, network CVE calls, external recon/probing, production changes, deletions, data migrations or deployment. Local tests may be run once scripts have been reviewed. If unavailable, report blocked/not run.
