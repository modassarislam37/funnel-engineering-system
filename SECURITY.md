# Security policy

FES is a developer tool. It is **not a security certification**, and its offline pattern scanner is **not a substitute** for threat modeling, dependency advisories, SAST/DAST, access-control tests, or a professional review.

## Supported releases

We currently support the latest published release on the `main` branch. Fixes are best-effort while the project is in early development.

## Reporting a vulnerability

Do **not** open a public issue with a working exploit, secret, or information that could harm users. Prefer GitHub's **Report a vulnerability** feature in the repository's Security tab, if enabled. Otherwise contact the repository owner privately via GitHub. Include affected version, a minimal non-sensitive reproducer, impact, and suggested remediation. Do not test against third-party systems without permission.

## Security boundaries

- `tools/hardening.py` performs offline heuristic source inspection, not live penetration testing.
- `tools/funnel.py run` executes commands from the target repository. Review untrusted code, scripts, and build hooks before using it.
- Do not run unknown projects with production credentials or elevated permissions; use an isolated development environment.
- Generated skills must not override project permissions or be used to install untrusted code without review.
- Installation and agent configuration capabilities differ across hosts; read `docs/compatibility.md`.

See [docs/security.md](docs/security.md) for technical limits and [docs/hardening.md](docs/hardening.md) for the rescue workflow.
