#!/usr/bin/env python3
"""Validate the distributed Funnel Engineering System package structure."""
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]


def validate(root: Path = ROOT) -> list[str]:
    errors = []
    manifest = json.loads((root / "manifest.json").read_text())
    if manifest.get("version") != "5.0.0":
        errors.append("Manifest must declare v5.0.0")
    skill_root = root / "skills"
    discovered = []
    for d in sorted(skill_root.iterdir()):
        if not d.is_dir():
            continue
        entry = d / "SKILL.md"
        if not entry.is_file():
            errors.append(f"Skill missing SKILL.md: {d.name}")
            continue
        text = entry.read_text()
        found = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.S)
        if not found:
            errors.append(f"Invalid skill frontmatter: {d.name}")
            continue
        name = re.search(r"(?m)^name:\s*(\S+)\s*$", found.group(1))
        desc = re.search(r"(?m)^description:\s*(.+)$", found.group(1))
        if not name or name.group(1) != d.name:
            errors.append(f"Skill name mismatch: {d.name}")
        if not desc or not desc.group(1).strip():
            errors.append(f"Skill description missing: {d.name}")
        discovered.append(d.name)
    if sorted(manifest.get("skills", [])) != discovered:
        errors.append("Manifest skill list mismatch")
    if len(discovered) != 22:
        errors.append(f"Expected 22 skills, found {len(discovered)}")
    roles = sorted(p.stem for p in (root / "codex" / "agents").glob("*.toml"))
    if roles != sorted(manifest.get("agents", [])):
        errors.append("Role config list mismatch")
    try:
        import tomllib
    except ImportError:
        pass
    else:
        config = tomllib.loads((root / "codex" / "config.toml").read_text())
        for role in roles:
            role_doc = tomllib.loads((root / "codex" / "agents" / (role + ".toml")).read_text())
            for key in ("name", "description", "developer_instructions"):
                if not role_doc.get(key): errors.append(f"Role {role}: missing {key}")
            if role_doc.get("name") != role: errors.append(f"Role {role}: name mismatch")
            if any(k in role_doc for k in ("sandbox_mode", "approval_policy", "mcp_servers")):
                errors.append(f"Role {role}: unsupported parent permission override")
            if not config.get("agents", {}).get("max_concurrent_threads_per_session"):
                errors.append("Codex snippet missing concurrency setting")
    for path in ("tools/install_portable.py", "tools/funnel.py", "tools/install.py", "tools/migrate_v3.py", "tools/smoke_test.py", "tools/skill_engine.py", "tools/hardening.py", "tools/evaluation.py", "tools/inventory.py", "tools/hardening_smoke_test.py", "README.md", "docs/security.md"):
        if not (root / path).is_file():
            errors.append("Required package file missing: " + path)
    return errors


if __name__ == "__main__":
    problems = validate()
    if problems:
        print("\n".join("FAIL: " + p for p in problems))
        sys.exit(1)
    print("PASS: v5 package manifest, 22 skill entrypoints, 5 agent roles and required files")
