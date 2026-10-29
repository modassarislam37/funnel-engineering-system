#!/usr/bin/env python3
"""Safely install FES skills and optional Codex roles without replacing existing files."""
from __future__ import annotations
import argparse
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]


def install(destination: Path, upgrade: bool, agents: bool, dry_run: bool) -> tuple[int, int]:
    skills_path = destination / ".agents" / "skills"
    count, skipped = 0, 0
    for skill in sorted((ROOT / "skills").iterdir()):
        if skill.name == "fes-agent-portability":
            continue  # legacy v4 installer: preserve its tested 21-skill contract
        if not skill.is_dir() or not (skill / "SKILL.md").is_file():
            continue
        target = skills_path / skill.name
        if target.exists():
            if not upgrade:
                print("SKIP existing", target)
                skipped += 1
                continue
            # Never overwrite non-FES skills or links. Overwriting user edits requires manual intervention.
            if target.is_symlink():
                raise ValueError(f"Refusing symlink target {target}")
            if skill.name != "funnel-engineer" and not skill.name.startswith("fes-"):
                raise ValueError(f"Refusing unrelated skill {target}")
            # Unconditionally overwriting a modified target is risky: make .bak backup.
            backup = target.with_name(target.name + ".fes-v4-2-backup")
            if backup.exists():
                raise ValueError(f"Backup already exists; reconcile manually: {backup}")
            print("UPGRADE", target, "(backup", backup, ")")
            if not dry_run:
                target.rename(backup)
        else:
            print("INSTALL", target)
        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(skill, target)
        count += 1
    if agents:
        cfgdir = destination / ".codex"
        for role in sorted((ROOT / "codex" / "agents").glob("*.toml")):
            target = cfgdir / "agents" / role.name
            if target.exists():
                if not upgrade:
                    print("SKIP existing role", target)
                    continue
                if target.is_symlink() or not target.is_file():
                    raise ValueError(f"Unsafe role target: {target}")
                backup = target.with_name(target.name + ".fes-v4-2-backup")
                if backup.exists():
                    raise ValueError(f"Role backup exists; reconcile manually: {backup}")
                print("UPGRADE role", target, "(backup", backup, ")")
                if not dry_run: target.rename(backup)
            else:
                print("INSTALL role", target)
            if not dry_run:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(role, target)
        snippet = cfgdir / "fes-v4-2-config-snippet.toml"
        if not snippet.exists():
            print("WRITE config snippet", snippet)
            if not dry_run:
                cfgdir.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / "codex" / "config.toml", snippet)
        print("Manually merge the snippet into the existing config.toml (no automatic edits).")
    return count, skipped


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scope", choices=["user", "project"], default="user")
    ap.add_argument("--project", help="Project dir when --scope project")
    ap.add_argument("--upgrade", action="store_true", help="Back up existing FES skills before replacing them")
    ap.add_argument("--with-agents", action="store_true", help="Install role TOMLs and provide a manual config snippet")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    if args.scope == "project" and not args.project:
        ap.error("--project required for project scope")
    dest = Path.home() if args.scope == "user" else Path(args.project).expanduser().resolve()
    if not dest.is_dir():
        ap.error("Destination directory does not exist")
    try:
        installed, skipped = install(dest, args.upgrade, args.with_agents, args.dry_run)
        print(f"Installed or planned: {installed}; skipped: {skipped}")
        return 0
    except (OSError, ValueError) as e:
        print("ERROR:", e, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
