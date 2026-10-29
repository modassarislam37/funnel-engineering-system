---
name: fes-agent-portability
description: Install, invoke, diagnose and distribute Funnel Engineering System skills across Codex, Claude Code, Cursor, Gemini CLI, GitHub Copilot and OpenCode, while preserving host-specific permission boundaries.
---
# Agent portability specialist

Use this skill when the requested outcome is to install, transfer, troubleshoot, package or adapt FES to a different AI coding host. Do not assume that discovering an instruction skill enables shell execution, true subagents, browser access or privileged operations.

1. Detect the actual host and consult its current skill discovery rules. Do not infer capability from a folder name alone.
2. Prefer `python3 <FES_ROOT>/tools/install_portable.py --agent <host> --scope project --project <path> --dry-run` before installing; use `--upgrade` only when backup/replacement is approved.
3. For broad local compatibility choose `--agent all`, which installs a shared `.agents/skills` copy and a `.claude/skills` copy. This may produce duplicate discovery in hosts that search multiple roots; verify which copy wins and do not edit both independently.
4. Do not install optional Codex role TOMLs on another host. Use bounded sequential specialist instructions if subagents are unavailable; record observed real delegation only.
5. For generated project skills, shared hosts usually discover `.agents/skills`; host-specific discovery uses the corresponding native skills directory. Have the running agent read a new skill directly in the same session.
6. Run package validation and relevant application tests; do not describe metadata checks as behavioral benchmarks.
7. Respect project policies, no silent deployments/pushes, and a human-approved dependency/runtime install.
