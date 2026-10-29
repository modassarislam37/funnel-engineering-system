#!/usr/bin/env python3
"""Conservatively migrate a v3 task to v4, resetting all gate passes for fresh verification.

Original v3 JSON is preserved as .v3-backup.json. No historical PASS is trusted.
"""
from pathlib import Path
import argparse
import json
import shutil
import sys
import funnel


def migrate(project: Path, task: str) -> None:
    p = funnel.task_path(project, task)
    if not p.is_file():
        raise ValueError("v3 task not found")
    old = json.loads(p.read_text())
    if old.get("schema_version") != 2 or old.get("track") not in funnel.TRACKS:
        raise ValueError("Expected v3 schema 2 and known track")
    backup = p.with_suffix(".v3-backup.json")
    if backup.exists():
        raise ValueError("Refusing to replace existing backup")
    shutil.copy2(p, backup)
    new = {
        "schema_version": 4, "task": task, "track": old["track"], "risk": "normal",
        "created_at": old.get("created_at", funnel.utc()), "revision": 0,
        "max_retries": 3, "retries": 0, "required_checks": list(funnel.REQUIRED[old["track"]]),
        "gates": {}, "checks": [], "handoffs": [],
        "events": [{"type": "migration", "at": funnel.utc(), "message": "v3 checkpoints reset; prior evidence must be rerun", "backup": backup.name}],
    }
    for g in funnel.GATES:
        saved = old.get("gates", {}).get(g, {})
        new["gates"][g] = {
            "status": "PENDING" if g in funnel.TRACKS[new["track"]] else "SKIP",
            "evidence": [], "notes": saved.get("notes", []), "reason": None,
            "source_sha": None, "pass_seq": None,
        }
    funnel.store(p, new)
    print("Migrated", p, "(old passes reset; backup:", backup, ")")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--task", required=True)
    args = ap.parse_args()
    try:
        project = funnel.project_dir(args.project)
        with funnel.locked(project, args.task):
            migrate(project, args.task)
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as e:
        print("ERROR:", e, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
