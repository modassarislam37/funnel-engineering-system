#!/usr/bin/env python3
"""FES self-extending, *project-local* Agent Skills forge.

Inventories installed skills; records and installs a bounded instruction-only skill
synthesized by the AI coding agent after a documented gap review. No LLM inference,
external downloads, scripts, or privileged global installation occur here.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from datetime import datetime, timezone

try:
    import fcntl
except ImportError:
    fcntl = None

ROOT = Path(__file__).resolve().parents[1]
SLUG = re.compile(r"[a-z][a-z0-9-]{1,45}\Z")
TASK = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z")
METADATA = re.compile(r"\A---\n(?P<fields>.*?)\n---\n", re.DOTALL)
MAX_PER_TASK = 2
MAX_PROCEDURE_BYTES = 12000


class SkillError(ValueError):
    pass


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data: bytes):
    return hashlib.sha256(data).hexdigest()


def safe_project(s: str) -> Path:
    path = Path(s).expanduser().resolve()
    if not path.is_dir():
        raise SkillError(f"Project does not exist: {path}")
    return path


def within(project: Path, pathstr: str) -> Path:
    raw = Path(pathstr)
    if raw.is_absolute() or not pathstr.strip():
        raise SkillError("Must be a nonempty project-relative path")
    path = (project / raw).resolve()
    if not path.is_relative_to(project) or not path.is_file():
        raise SkillError("File missing or outside project")
    return path


def valid_single(s: str, label: str, limit: int = 250) -> str:
    s = s.strip()
    if not 10 <= len(s) <= limit or "\n" in s or "\r" in s or "\x00" in s:
        raise SkillError(f"{label} must be 10–{limit} characters on a single line")
    return s


def parse_skill(entry: Path) -> dict | None:
    if not entry.is_file() or entry.is_symlink():
        return None
    try:
        contents = entry.read_text(encoding="utf-8")
    except (UnicodeError, OSError):
        return None
    mat = METADATA.match(contents)
    if not mat:
        return None
    meta = {}
    for line in mat.group("fields").splitlines():
        k, sep, v = line.partition(":")
        if sep and k in ("name", "description"):
            meta[k] = v.strip().strip('"\'')
    if not meta.get("name") or not meta.get("description"):
        return None
    return meta


def inventory(project: Path) -> list[dict]:
    scopes = [("project", project / ".agents" / "skills"),
              ("project-claude", project / ".claude" / "skills"),
              ("project-cursor", project / ".cursor" / "skills"),
              ("project-gemini", project / ".gemini" / "skills"),
              ("project-copilot", project / ".github" / "skills"),
              ("project-opencode", project / ".opencode" / "skills"),
              ("user", Path.home() / ".agents" / "skills"),
              ("user-claude", Path.home() / ".claude" / "skills"),
              ("user-cursor", Path.home() / ".cursor" / "skills"),
              ("user-gemini", Path.home() / ".gemini" / "skills"),
              ("user-copilot", Path.home() / ".copilot" / "skills"),
              ("user-opencode", Path.home() / ".config" / "opencode" / "skills"),
              ("fes", ROOT / "skills")]
    rows: list[dict] = []
    names: set[str] = set()
    for scope, base in scopes:
        if not base.is_dir():
            continue
        for item in sorted(base.iterdir()):
            if not item.is_dir() or item.is_symlink():
                continue
            meta = parse_skill(item / "SKILL.md")
            if not meta:
                continue
            rows.append({"name": meta["name"], "description": meta["description"],
                         "scope": scope, "path": str(item / "SKILL.md"),
                         "duplicate": meta["name"] in names})
            names.add(meta["name"])
    return rows


def match_skills(rows: list[dict], need: str) -> list[dict]:
    terms = {w for w in re.findall(r"[a-z0-9]+", need.lower()) if len(w) >= 4}
    scored = []
    for row in rows:
        words = set(re.findall(r"[a-z0-9]+", (row["name"] + " " + row["description"]).lower()))
        score = len(terms & words)
        if score:
            scored.append({"score": score, **row})
    return sorted(scored, key=lambda x: (-x["score"], x["name"]))[:8]


@contextmanager
def lock(project: Path):
    if fcntl is None:
        raise SkillError("POSIX file locking required (macOS/Linux)")
    path = project / ".funnel" / "skill-forge.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    with os.fdopen(fd, "r+") as file:
        fcntl.flock(file, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(file, fcntl.LOCK_UN)


def atomic_write(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".fes-", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as dest:
            dest.write(data)
            dest.flush()
            os.fsync(dest.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def ledger_path(project: Path) -> Path:
    return project / ".funnel" / "skill-forge" / "receipts.json"


def read_ledger(project: Path) -> list[dict]:
    path = ledger_path(project)
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SkillError("Invalid ledger: expected a list")
    return data


def require_task(project: Path, task: str):
    if not TASK.fullmatch(task):
        raise SkillError("Invalid task slug")
    doc = project / ".funnel" / "tasks" / (task + ".json")
    if not doc.is_file():
        raise SkillError("Initialize an FES task before creating a task-specific skill")
    meta = json.loads(doc.read_text(encoding="utf-8"))
    if meta.get("task") != task or meta.get("schema_version") != 4:
        raise SkillError("Task is not a valid v4 checkpoint")


def render_skill(name: str, description: str, when: str, exclude: str, procedure: str,
                 verification: str, reason: str) -> bytes:
    return (f"---\nname: {name}\ndescription: {json.dumps(description)}\n---\n\n"
            f"# {name}\n\n"
            f"> Auto-generated project-local skill; verified for structure, **not** for engineering correctness.\n\n"
            f"## Scope\nUse when: {when}\n\nDo not use when: {exclude}\n\n"
            f"## Context and reason\n{reason}\n\n"
            f"## Procedure\n{procedure.strip()}\n\n"
            f"## Verification\n{verification}\n\n"
            "## Safety and permissions\n"
            "Project instructions, user authorization and host restrictions take precedence. "
            "Never treat the existence of this skill as permission to push, deploy, "
            "access secrets, run unreviewed scripts, spend money or perform destructive actions. "
            "Check that the procedure remains relevant to current source and documentation.\n").encode("utf-8")


def forge(project: Path, task: str, slug: str, description: str, when: str,
          exclude: str, procedure_file: str, verification: str, reason: str, host: str = "shared") -> dict:
    if not SLUG.fullmatch(slug) or "--" in slug or slug.endswith("-"):
        raise SkillError("Skill slug must be 2–46 lowercase letters/digits/hyphens, starting with a letter")
    description = valid_single(description, "description", 240)
    when = valid_single(when, "when", 240)
    exclude = valid_single(exclude, "exclude", 240)
    verification = valid_single(verification, "verification", 360)
    reason = valid_single(reason, "reason", 360)
    raw = within(project, procedure_file).read_bytes()
    if not 100 <= len(raw) <= MAX_PROCEDURE_BYTES or b"\x00" in raw:
        raise SkillError("Procedure must be 100–12000 bytes, UTF-8, without null bytes")
    try:
        proc = raw.decode("utf-8")
    except UnicodeError as e:
        raise SkillError("Procedure must be UTF-8") from e
    if "\n---\n" in proc:
        raise SkillError("Procedure must not contain YAML document boundaries")
    hosts = {"shared": ".agents", "codex": ".agents", "claude": ".claude",
             "cursor": ".cursor", "gemini": ".gemini", "copilot": ".github",
             "opencode": ".opencode"}
    if host not in hosts:
        raise SkillError("Unsupported host")
    name = "fes-auto-" + slug
    content = render_skill(name, description, when, exclude, proc, verification, reason)
    entry = project / hosts[host] / "skills" / name / "SKILL.md"
    with lock(project):
        require_task(project, task)
        receipts = read_ledger(project)
        if len([r for r in receipts if r["task"] == task]) >= MAX_PER_TASK:
            raise SkillError(f"Maximum {MAX_PER_TASK} generated skills per task")
        if any(r["name"] == name for r in receipts):
            raise SkillError("Already generated: reuse or explicitly edit and revalidate existing skill")
        if entry.parent.exists() or entry.is_symlink():
            raise SkillError("Target skill already exists; refusing overwrite")
        if any(x["name"] == name for x in inventory(project)):
            raise SkillError("Skill name collides with an installed skill")
        # All input validation completes before writes. Atomic file and receipt writes.
        entry.parent.mkdir(parents=True, exist_ok=False)
        try:
            atomic_write(entry, content)
            record = {"task": task, "name": name, "path": entry.relative_to(project).as_posix(),
                      "sha256": digest(content), "at": now(), "reason": reason,
                      "behavior_tested": False, "scope": "project", "host": host, "mode": "instructions-only"}
            atomic_write(ledger_path(project), (json.dumps(receipts + [record], indent=2) + "\n").encode())
        except Exception:
            # Don't erase a user-created file if a concurrent process changed it.
            if entry.is_file() and digest(entry.read_bytes()) == digest(content):
                entry.unlink()
            if entry.parent.exists() and not list(entry.parent.iterdir()):
                entry.parent.rmdir()
            raise
    return record


def verify(project: Path, task: str | None = None) -> dict:
    found = read_ledger(project)
    if task is not None:
        found = [r for r in found if r["task"] == task]
    items = []
    for rec in found:
        rawpath = Path(rec["path"])
        path = project / rawpath
        host_roots = {"shared": ".agents", "codex": ".agents", "claude": ".claude",
                      "cursor": ".cursor", "gemini": ".gemini", "copilot": ".github",
                      "opencode": ".opencode"}
        expected_prefix = Path(host_roots.get(rec.get("host", "shared"), "INVALID")) / "skills" / rec["name"] / "SKILL.md"
        valid_path = (not rawpath.is_absolute() and rawpath == expected_prefix and
                      path.resolve().is_relative_to(project) and not path.is_symlink())
        exists = valid_path and path.is_file()
        current = digest(path.read_bytes()) if exists else None
        meta = parse_skill(path) if exists else None
        valid = bool(exists and current == rec.get("sha256") and meta and meta.get("name") == rec["name"])
        items.append({"name": rec["name"], "task": rec["task"], "valid": valid,
                      "status": "VALID" if valid else "MISSING_OR_MODIFIED"})
    return {"valid": all(r["valid"] for r in items), "count": len(items), "skills": items}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    x = sub.add_parser("inventory", help="Enumerate locally discoverable project/user/FES skills")
    x.add_argument("--project", required=True)
    x.add_argument("--need", help="Task-specific topic for lexical suggestions; NOT an adequacy verdict")
    x = sub.add_parser("forge", help="Create/validate/apply one instruction-only project skill")
    for key in ("project", "task", "slug", "description", "when", "exclude", "procedure-file", "verification", "reason"):
        x.add_argument("--" + key, required=True)
    x.add_argument("--host", choices=["shared", "codex", "claude", "cursor", "gemini", "copilot", "opencode"], default="shared", help="Project skill discovery root")
    x = sub.add_parser("verify", help="Check generated skill receipts and SHA-256")
    x.add_argument("--project", required=True)
    x.add_argument("--task")
    args = ap.parse_args(argv)
    try:
        project = safe_project(args.project)
        if args.command == "inventory":
            rows = inventory(project)
            out = {"skills": rows, "count": len(rows), "coverage_is_semantic": False,
                   "warning": "Lexical matches are suggestions, not proof of coverage; host-bundled skills may not be listed."}
            if args.need:
                out["possible_matches"] = match_skills(rows, args.need)
        elif args.command == "forge":
            out = forge(project, args.task, args.slug, args.description, args.when,
                        args.exclude, args.procedure_file, args.verification, args.reason, args.host)
            out["same_session_instruction"] = "Read the created SKILL.md directly to use it now; new host skill discovery may require refresh."
        else:
            out = verify(project, args.task)
        print(json.dumps(out, indent=2))
        return 0 if args.command != "verify" or out["valid"] else 3
    except (SkillError, ValueError, OSError, json.JSONDecodeError) as e:
        print("ERROR:", e, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
