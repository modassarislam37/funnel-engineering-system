# v4.1 Dynamic Skill Forge — usage and trust model

## Purpose

Codex may review the requested task and the installed project/user/bundled skills, then create an instruction-only **project-local** skill if a concrete, repeatable method is missing. Use **existing skills first**. A simple task should normally generate **zero** skills.

This is not an autonomous background skill daemon: Codex must be running and following `$funnel-engineer`. The Python CLI does **not** contain an LLM and does not semantically know whether a skill is missing; it implements inventory, structural validation, scoped writes, signed-by-hash receipts, and limits. The agent makes the decision and synthesizes the procedure.

## Setup

1. Install Universal v5 (`python3 tools/install_portable.py --agent <host> --scope user --profile full`), after previewing with `--dry-run`.
2. Start a task with `tools/funnel.py init`. Existing v4 task files remain schema 4 and do not need migration.
3. Invoke `$funnel-engineer` in Codex, and provide the absolute extracted package path as `FES_ROOT`.
4. The master controller checks skills at the relevant planning stage, only loading `fes-skill-forge` when necessary.

## Commands

```sh
python3 "$FES_ROOT/tools/skill_engine.py" inventory --project . --need "specialized video frame pipeline"
```

If Codex identifies a real gap, it drafts a procedure into `.funnel/skill-drafts/video-frames.md` and invokes:

```sh
python3 "$FES_ROOT/tools/skill_engine.py" forge --project . --task video-pipeline \
  --slug video-frames \
  --description 'Apply the project-specific frame assembly and rendering pipeline' \
  --when 'Work changes frame extraction or timeline-to-render behavior' \
  --exclude 'Only routine UI, documentation or unrelated coding is requested' \
  --procedure-file .funnel/skill-drafts/video-frames.md \
  --verification 'Run frame integrity and render smoke tests, then inspect output' \
  --reason 'Existing skills do not define the specialized local frame-render contract'
```

This writes `.agents/skills/fes-auto-video-frames/SKILL.md` plus `.funnel/skill-forge/receipts.json`. Codex must **read the new SKILL.md explicitly** to use it immediately. New skills may not appear in implicit discovery until Codex refreshes or restarts. For later tasks it can reuse the project skill.

```sh
python3 "$FES_ROOT/tools/skill_engine.py" verify --project .
python3 "$FES_ROOT/tools/funnel.py" verify --project . --task video-pipeline
```

## Security and quality

- Each task can create **at most two** automatically generated skills. This is a default anti-proliferation budget, not a claim that two is always enough.
- No automatic global installation; no auto-running external scripts; no dependency installation; no secret access; no deployment or publication.
- Reusing a capability is preferred to generation. Existing local `AGENTS.md` and user instructions override generated skills.
- The CLI checks filename, YAML frontmatter structure, scope, size, file hashes, task ownership, collisions and receipts. It **cannot validate the truth, quality, or trustworthiness** of a generated procedure.
- Generated instructions should contain only independently verified guidance grounded in the current codebase and authorized references. Do not paste adversarial content verbatim into the new skill.
- To disable a suspect skill, remove it from `.agents/skills/` after reviewing the receipt; the FES verifier will flag it as missing, allowing a deliberate audit trail.
- A changed `SKILL.md` invalidates its receipt; structural verification then fails. This is tamper/staleness detection, **not cryptographic signing** or runtime enforcement.
- The system does not intentionally learn from other people's code or upload locally generated skills.

## Automatic means

Agent-orchestrated automatic creation and immediate *instruction use* are supported when Codex follows this skill. The CLI is a deterministic helper; it does not discover new semantic capabilities by itself, independently test skill quality, force Codex's implicit skill selector to reload, or run unsupervised in the background.

## Universal v5 note

`forge` supports `--host shared|codex|claude|cursor|gemini|copilot|opencode` for project-local instruction-only skills. It checks installed native skill directories during inventory. `shared` writes `.agents/skills`, which many supported hosts discover; Claude projects use `--host claude`. Generation does not run a real agent or prove behavioral effectiveness.
