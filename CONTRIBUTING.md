# Contributing

Thank you for helping improve Funnel Engineering System (FES). This repository is an early-stage engineering toolkit and welcomes reproducible bug reports, documentation improvements, and focused pull requests.

## Before opening a PR

1. Check existing issues and explain the problem with a minimal reproducer.
2. Keep the proposed change small and consistent with existing project conventions.
3. Document any new CLI commands, skill contracts, supported host paths, or security implications.
4. Add regression tests for behavior changes and run:

   ```bash
   python3 tools/validate_package.py
   python3 -m unittest discover -s tests -v
   python3 tools/smoke_test.py
   python3 tools/hardening_smoke_test.py
   ```

5. Avoid submitting third-party copyrighted source without permission and license notices.

## Safety

Never submit credentials, customer projects, private chat transcripts, personal data, or exploit details affecting a live target. For confidential security reports, see [SECURITY.md](SECURITY.md).

## What makes a good skill contribution?

A new skill should solve a concrete capability gap rather than duplicate a current skill. Include a named `SKILL.md`, a narrow description, explicit input/output expectations, a trust-boundary note where relevant, a manifest entry, and a test or validation demonstration. Automated generation is not itself evidence of skill effectiveness.

Contributions are accepted under the project's MIT license.
