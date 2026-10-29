#!/usr/bin/env python3
"""Funnel Engineering System v4: ordered, evidence-backed local engineering checkpoints.

This program never talks to Codex or deploys software. It only runs commands when
explicitly invoked with `run -- <argv>` and does not use shell evaluation.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile
from typing import Any

try:
    import fcntl                 # POSIX: macOS / Linux
except ImportError:
    fcntl = None

SCHEMA = 4
GATES = tuple(f"G{i}" for i in range(8))
TRACKS = {
    "build": set(GATES),
    "fix": {"G0", "G1", "G3", "G4", "G5", "G6", "G7"},
    "refactor": {"G0", "G1", "G3", "G4", "G5", "G6", "G7"},
    "harden": set(GATES),
    "review": {"G0", "G1", "G3", "G5", "G6", "G7"},
    "quick": {"G0", "G1", "G4", "G5", "G6", "G7"},
}
STATES = {"PENDING", "PASS", "FAIL", "BLOCKED", "SKIP"}
CHECK_KINDS = {"test", "lint", "typecheck", "build", "security", "hardening", "visual", "other"}
REQUIRED = {
    "build": ["test"], "fix": ["test"], "refactor": ["test"],
    "quick": ["test"], "review": [], "harden": ["test"],
}
# Directory names omitted from fingerprints; this must exclude transient dependency/build outputs.
SKIP_DIRS = {".git", ".funnel", "node_modules", ".venv", "venv", "__pycache__", ".next", ".cache", "dist", "build", "coverage", ".pytest_cache", ".tox", "target"}
SOURCE_EXTS = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".go", ".rs", ".java", ".kt", ".swift", ".c", ".h", ".cpp", ".cs", ".php", ".rb", ".sh", ".sql", ".css", ".scss", ".html", ".vue", ".svelte", ".json", ".toml", ".yml", ".yaml", ".xml"}
SOURCE_NAMES = {"Dockerfile", "Makefile", "Justfile", "AGENTS.md", "requirements.txt", "Pipfile", "Gemfile", "go.mod", "Cargo.lock", "package-lock.json", "pnpm-lock.yaml", "yarn.lock"}
MAX_FILES = 30000
MAX_LOG_BYTES = 60000
TASK_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z")


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def project_dir(raw: str | Path) -> Path:
    project = Path(raw).expanduser().resolve()
    if not project.is_dir():
        raise ValueError(f"Project directory not found: {project}")
    return project


def task_path(project: Path, task: str) -> Path:
    if not TASK_RE.fullmatch(task):
        raise ValueError("Task slug must be 1–64 letters, digits, hyphens or underscores")
    return project / ".funnel" / "tasks" / (task + ".json")


def relative_file(project: Path, raw: str) -> tuple[str, Path]:
    supplied = Path(raw)
    if supplied.is_absolute() or not raw.strip():
        raise ValueError("Evidence paths must be nonempty project-relative file paths")
    candidate = (project / supplied).resolve()
    if not candidate.is_relative_to(project):
        raise ValueError("Evidence path escapes project root")
    if not candidate.is_file():
        raise ValueError(f"Evidence file missing: {raw}")
    return candidate.relative_to(project).as_posix(), candidate


def digest_file(file: Path) -> str:
    h = hashlib.sha256()
    with file.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fingerprint(project: Path) -> str:
    """Source/config snapshot. Excludes docs and generated output, not a universal build graph."""
    h = hashlib.sha256()
    count = 0
    for base, dirs, files in os.walk(project, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not (Path(base) / d).is_symlink())
        for name in sorted(files):
            path = Path(base) / name
            if path.suffix.lower() not in SOURCE_EXTS and name not in SOURCE_NAMES:
                continue
            count += 1
            if count > MAX_FILES:
                raise ValueError("More than 30000 source files: use smaller repository or configure exclusions")
            rel = path.relative_to(project).as_posix().encode()
            h.update(len(rel).to_bytes(4, "big") + rel)
            if path.is_symlink():
                h.update(b"symlink:" + os.readlink(path).encode())
            else:
                h.update(digest_file(path).encode())
    return h.hexdigest()


def git_head(project: Path) -> str | None:
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=project, capture_output=True,
                             text=True, timeout=4, check=False)
        return res.stdout.strip() if res.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


@contextmanager
def locked(project: Path, task: str):
    """Serialize local task writers using an advisory file lock; macOS/Linux only."""
    if fcntl is None:
        raise ValueError("This CLI currently requires POSIX fcntl for safe task writes")
    lockpath = task_path(project, task).with_suffix(".lock")
    lockpath.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(lockpath, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        with os.fdopen(fd, "r+") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            yield
            fcntl.flock(handle, fcntl.LOCK_UN)
    finally:
        pass


def store(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(doc, indent=2, ensure_ascii=False) + "\n").encode()
    fd, temp = tempfile.mkstemp(prefix=".checkpoint-", suffix=".tmp", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def new_task(project: Path, task: str, track: str, risk: str = "normal", max_retries: int = 3) -> dict:
    if track not in TRACKS:
        raise ValueError("Invalid track")
    if track == "harden":
        risk = "high"
    if risk not in ("normal", "high"):
        raise ValueError("Risk must be normal or high")
    if not 1 <= max_retries <= 10:
        raise ValueError("Retry budget must be 1..10")
    path = task_path(project, task)
    if path.exists():
        raise ValueError("Task exists; use status or create another slug")
    doc = {
        "schema_version": SCHEMA, "task": task, "track": track, "risk": risk,
        "created_at": utc(), "revision": 0, "max_retries": max_retries, "retries": 0,
        "required_checks": REQUIRED[track] + (["security", "hardening"] if risk == "high" and track != "review" else []),
        "gates": {g: {"status": "PENDING" if g in TRACKS[track] else "SKIP", "evidence": [],
                      "notes": [], "reason": None, "source_sha": None, "pass_seq": None} for g in GATES},
        "checks": [], "handoffs": [], "events": [],
    }
    store(path, doc)
    return doc


def read_task(project: Path, task: str) -> tuple[Path, dict]:
    path = task_path(project, task)
    if not path.is_file():
        raise ValueError("Unknown task. Run init first")
    doc = json.loads(path.read_text("utf-8"))
    if doc.get("schema_version") != SCHEMA:
        raise ValueError("This CLI requires v4 task schema. Use tools/migrate_v3.py for a v3 checkpoint")
    return path, doc


def log_event(doc: dict, kind: str, **fields: Any) -> None:
    doc.setdefault("events", []).append({"at": utc(), "type": kind, **fields})
    doc["revision"] += 1


def reset_from(doc: dict, gate: str) -> None:
    """Clear gate and all dependent assertions; historical checks remain for audit."""
    for g in GATES[GATES.index(gate):]:
        rec = doc["gates"][g]
        if rec["status"] != "SKIP":
            rec.update(status="PENDING", evidence=[], reason=None, source_sha=None, pass_seq=None)


def evidence_record(project: Path, raw: str) -> dict:
    rel, path = relative_file(project, raw)
    return {"path": rel, "sha256": digest_file(path)}


def validate(project: Path, doc: dict) -> list[str]:
    errors: list[str] = []
    if doc.get("schema_version") != SCHEMA:
        return ["Unsupported schema"]
    track = doc.get("track")
    if track not in TRACKS:
        return ["Unknown track"]
    if set(doc.get("gates", {})) != set(GATES):
        return ["Incomplete gate set"]
    if doc.get("risk") not in ("normal", "high"):
        errors.append("Invalid risk")
    if not isinstance(doc.get("checks"), list):
        return ["Invalid checks"]
    checks = doc["checks"]
    current = fingerprint(project)
    seen_unpassed = False
    for g in GATES:
        rec = doc["gates"][g]
        status = rec.get("status")
        if status not in STATES:
            errors.append(f"{g}: unknown state")
            continue
        if g not in TRACKS[track]:
            if status != "SKIP": errors.append(f"{g}: skipped in this track")
            continue
        if seen_unpassed and status == "PASS":
            errors.append(f"{g}: passed after incomplete predecessor")
        if status != "PASS": seen_unpassed = True
        if status in {"FAIL", "BLOCKED"} and not rec.get("reason"):
            errors.append(f"{g}: failure reason missing")
        if status == "PASS":
            if not rec.get("evidence"):
                errors.append(f"{g}: PASS without evidence")
            for item in rec.get("evidence", []):
                try:
                    rel, path = relative_file(project, item["path"])
                    if digest_file(path) != item["sha256"]:
                        errors.append(f"{g}: stale evidence: {rel}")
                except (KeyError, TypeError, ValueError, OSError) as e:
                    errors.append(f"{g}: invalid evidence: {e}")
            if g in ("G4", "G5", "G6", "G7") and rec.get("source_sha") != current:
                errors.append(f"{g}: source changed after pass; reopen affected gate")
            if g == "G5":
                for k in doc.get("required_checks", []):
                    relevant = [c for c in checks if c.get("kind") == k and
                                c.get("source_sha") == current and
                                c.get("seq", -1) > doc["gates"]["G4"].get("pass_seq", -1)]
                    if not relevant or relevant[-1].get("exit_code") != 0 or not check_log_valid(project, relevant[-1]):
                        errors.append(f"G5: missing successful post-G4 current-source {k} check")
    for c in checks:
        if not isinstance(c, dict) or not all(k in c for k in ("command", "kind", "exit_code", "source_sha", "log", "log_sha256")):
            errors.append("Invalid check record")
        elif not check_log_valid(project, c):
            errors.append("Check log missing or tampered: " + str(c.get("log")))
    for handoff in doc.get("handoffs", []):
        if handoff.get("status") in {"REPORTED", "BLOCKED"}:
            result = handoff.get("result")
            if not isinstance(result, dict):
                errors.append("Handoff result missing: " + str(handoff.get("id")))
                continue
            try:
                rel, result_path = relative_file(project, result["path"])
                if digest_file(result_path) != result["sha256"]:
                    errors.append("Stale handoff result: " + rel)
            except (ValueError, OSError, KeyError, TypeError) as e:
                errors.append("Invalid handoff result: " + str(e))
    # Validate dynamically created project skill receipts belonging to this task.
    # Hash integrity is structural evidence, not behavioral assurance.
    forge_ledger = project / ".funnel" / "skill-forge" / "receipts.json"
    if forge_ledger.exists():
        try:
            records = json.loads(forge_ledger.read_text(encoding="utf-8"))
            if not isinstance(records, list):
                raise ValueError("Invalid skill forge ledger type")
            for item in records:
                if item.get("task") != doc.get("task"):
                    continue
                name = item["name"]
                expected = (Path(".agents") / "skills" / name / "SKILL.md")
                if not name.startswith("fes-auto-") or item.get("path") != expected.as_posix():
                    errors.append("Invalid generated skill receipt path: " + str(name))
                    continue
                candidate = project / expected
                if (not candidate.is_file() or candidate.is_symlink() or
                        not candidate.resolve().is_relative_to(project) or
                        digest_file(candidate) != item.get("sha256")):
                    errors.append("Missing or modified generated skill: " + str(name))
        except (ValueError, TypeError, KeyError, OSError, json.JSONDecodeError) as e:
            errors.append("Invalid skill forge ledger: " + str(e))
    return errors


def check_log_valid(project: Path, item: dict) -> bool:
    try:
        _, path = relative_file(project, item["log"])
        return digest_file(path) == item["log_sha256"]
    except (ValueError, KeyError, TypeError, OSError):
        return False


def write_log(project: Path, task: str, number: int, command: list[str], code: int, output: str) -> dict:
    base = project / ".funnel" / "logs"
    base.mkdir(parents=True, exist_ok=True)
    path = base / f"{task}-{number:04d}.txt"
    # Never show or write input environment variables. Stdout/stderr can still contain secrets.
    output = re.sub(r"(?i)((?:api[_-]?key|access[_-]?token|password|secret)\s*[:=]\s*)\S+", r"\1[REDACTED]", output)
    data = f"EXIT: {code}\nOUTPUT (at most {MAX_LOG_BYTES} bytes):\n" + output[:MAX_LOG_BYTES]
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(data)
    return {"path": path.relative_to(project).as_posix(), "sha256": digest_file(path)}


def security_command_allowed(argv: list[str]) -> bool:
    """Reject obvious no-op/mislabeled security checks. Not a command trust guarantee."""
    if not argv:
        return False
    prog = Path(argv[0]).name.lower()
    first = argv[1].lower() if len(argv) > 1 else ""
    if prog in {"npm", "pnpm", "yarn", "composer", "cargo"} and first == "audit":
        return True
    if prog in {"pip-audit", "bandit", "semgrep", "gosec", "govulncheck", "trivy", "safety", "checkov"}:
        return True
    if prog in {"python", "python3", "python3.10", "python3.11", "python3.12", "python3.13"}:
        if first == "-m" and len(argv) >= 3 and argv[2] in {"bandit", "pip_audit", "semgrep", "safety"}:
            return True
        if len(argv) >= 3 and Path(argv[1]).resolve() == Path(__file__).with_name("hardening.py").resolve() and argv[2] == "gate":
            return True
    return False


def run_check(project: Path, doc: dict, argv: list[str], kind: str, timeout: int) -> int:
    if kind not in CHECK_KINDS:
        raise ValueError("Invalid check kind")
    if argv and argv[0] == "--": argv = argv[1:]
    if not argv:
        raise ValueError("Supply executable after --")
    if kind == "security" and not security_command_allowed(argv):
        raise ValueError("security kind requires a recognized security tool or packaged hardening gate; ordinary checks belong under test/other")
    if kind == "hardening":
        # Named security checks alone can be mislabeled. This dedicated gate verifies
        # that the trusted local FES hardening report was checked for this project.
        from pathlib import Path as _Path
        if len(argv) < 5 or _Path(argv[0]).name not in {"python", "python3", "python3.10", "python3.11", "python3.12", "python3.13"}:
            raise ValueError("hardening kind requires python3 <FES_ROOT>/tools/hardening.py gate --project ...")
        if _Path(argv[1]).resolve() != _Path(__file__).with_name("hardening.py").resolve() or argv[2] != "gate":
            raise ValueError("hardening check must invoke this package's hardening.py gate")
        try:
            specified = _Path(argv[argv.index("--project") + 1]).resolve()
        except (ValueError, IndexError):
            raise ValueError("hardening check requires --project")
        if specified != project:
            raise ValueError("hardening check must target the current project")
    if timeout < 1 or timeout > 1800:
        raise ValueError("timeout must be 1..1800 seconds")
    source = fingerprint(project)
    try:
        res = subprocess.run(argv, cwd=project, capture_output=True, text=True, timeout=timeout, check=False,
                             errors="replace")
        code, output = res.returncode, res.stdout + "\n" + res.stderr
    except subprocess.TimeoutExpired:
        code, output = 124, f"Timed out after {timeout}s"
    except OSError as e:
        code, output = 127, f"Execution failed: {e}"
    after = fingerprint(project)
    if source != after:
        # Tests that change actual source are not proof of the pre/post code snapshot.
        code = 125 if code == 0 else code
        output += "\nWARNING: Source changed during check; result not valid for a stable code snapshot."
    record = write_log(project, doc["task"], len(doc["checks"]) + 1, argv, code, output)
    doc["checks"].append({"kind": kind, "command": argv, "exit_code": code, "at": utc(),
                          "source_sha": source, "git_head": git_head(project), "log": record["path"],
                          "log_sha256": record["sha256"], "seq": doc["revision"] + 1})
    log_event(doc, "check", check_kind=kind, exit_code=code, log=record["path"])
    print(f"{kind} check: exit {code}; private log {record['path']}")
    return 0 if code == 0 else 1


def advance(project: Path, doc: dict, gate: str, evidence: str) -> None:
    rec = doc["gates"][gate]
    if rec["status"] == "SKIP": raise ValueError("Gate skipped for track")
    if rec["status"] == "PASS": raise ValueError("Gate already passed; reopen before changing it")
    if any(doc["gates"][g]["status"] != "PASS" for g in GATES[:GATES.index(gate)] if g in TRACKS[doc["track"]]):
        raise ValueError("Earlier gates must PASS first")
    ev = evidence_record(project, evidence)
    current = fingerprint(project)
    if gate == "G5":
        successful = set()
        for kind in doc["required_checks"]:
            matches = [c for c in doc["checks"] if c["kind"] == kind and c["source_sha"] == current and
                       c.get("seq", -1) > doc["gates"]["G4"].get("pass_seq", -1)]
            if matches and matches[-1]["exit_code"] == 0 and check_log_valid(project, matches[-1]):
                successful.add(kind)
        missing = set(doc["required_checks"]) - successful
        if missing:
            raise ValueError("G5 requires successful current-source checks: " + ", ".join(sorted(missing)))
    rec.update(status="PASS", evidence=[ev], reason=None,
               source_sha=current if gate in ("G4", "G5", "G6", "G7") else None,
               pass_seq=doc["revision"] + 1)
    log_event(doc, "gate-pass", gate=gate, evidence=ev["path"])


def recover(doc: dict, reason: str) -> None:
    if doc["track"] == "review":
        raise ValueError("Read-only review track has no implementation recovery")
    if not doc["checks"] or doc["checks"][-1]["exit_code"] == 0:
        raise ValueError("Recovery requires the last recorded check to have failed")
    if doc["gates"]["G4"]["status"] != "PASS":
        raise ValueError("Recovery expects G4 PASS: investigate the work before retrying")
    doc["retries"] += 1
    if doc["retries"] > doc["max_retries"]:
        reset_from(doc, "G4")
        doc["gates"]["G4"].update(status="BLOCKED", reason="Recovery budget exhausted: " + reason)
        log_event(doc, "recovery-exhausted", reason=reason, retries=doc["retries"])
        return
    reset_from(doc, "G4")
    doc["gates"]["G4"]["notes"].append({"at": utc(), "text": "Recovery attempt " + str(doc["retries"]) + ": " + reason})
    log_event(doc, "recover", reason=reason, retry=doc["retries"])


def report(project: Path, doc: dict) -> Path:
    errors = validate(project, doc)
    path = project / ".funnel" / "reports" / (doc["task"] + ".md")
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# Funnel v4.2 task: {doc['task']}", "", f"Track: `{doc['track']}` · Risk: `{doc['risk']}` · Retries: {doc['retries']}/{doc['max_retries']}",
             "", "| Gate | State | Evidence |", "|---|---|---|"]
    for g in GATES:
        rec = doc["gates"][g]
        lines.append(f"| {g} | {rec['status']} | {', '.join(x['path'] for x in rec['evidence']) or '—'} |")
    lines += ["", "## Recorded checks (not independent proof)"]
    for c in doc["checks"]:
        lines.append(f"- `{c['kind']}` exit {c['exit_code']}, source `{c['source_sha'][:12]}`, log `{c['log']}`")
    lines += ["", "## Delegation handoffs"]
    for h in doc["handoffs"]:
        lines.append(f"- {h['id']}: {h['role']} — {h['status']} ({h['scope']})")
    lines += ["", "## Checkpoint validation", "PASS" if not errors else "FAIL: " + "; ".join(errors),
              "", "State validation verifies consistency and file hashes, not correctness, true agent independence, or deployment.", ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    path.chmod(0o600)
    return path


def act(args: argparse.Namespace) -> int:
    project = project_dir(args.project)
    task = args.task
    with locked(project, task):
        if args.action == "init":
            doc = new_task(project, task, args.track, args.risk, args.max_retries)
            print(f"Created {task} ({doc['track']}, {doc['risk']} risk)")
            return 0
        path, doc = read_task(project, task)
        if args.action == "status":
            print(f"{task} [{doc['track']}; risk={doc['risk']}; retry={doc['retries']}/{doc['max_retries']}]")
            for g in GATES:
                r = doc["gates"][g]
                print(f"{g}: {r['status']}" + (f" — {r['reason']}" if r.get("reason") else ""))
            print(f"Checks: {len(doc['checks'])} · Handoffs: {len(doc['handoffs'])}")
            return 0
        if args.action == "verify":
            errors = validate(project, doc)
            if errors:
                print("\n".join("FAIL: " + e for e in errors))
                return 1
            print("PASS: checkpoint consistency and evidence integrity; not software correctness")
            return 0
        if args.action == "report":
            target = report(project, doc)
            print(target)
            return 0 if not validate(project, doc) else 1
        if args.action == "run":
            code = run_check(project, doc, args.command, args.kind, args.timeout)
            store(path, doc)
            return code
        if args.action == "recover":
            recover(doc, args.reason)
        elif args.action == "handoff":
            if args.role not in {"architect", "developer", "tester", "reviewer", "security_auditor"}:
                raise ValueError("Unknown role")
            if not args.scope.strip():
                raise ValueError("Handoff requires a bounded scope")
            if args.role in {"reviewer", "security_auditor"} and args.mode == "write":
                raise ValueError("Independent reviewer role should be read-only")
            identifier = f"H{len(doc['handoffs']) + 1:03d}"
            handoff = {"id": identifier, "role": args.role, "mode": args.mode,
                       "scope": args.scope, "status": "PREPARED", "at": utc(), "result": None}
            doc["handoffs"].append(handoff)
            log_event(doc, "handoff-prepared", id=identifier)
            print(json.dumps(handoff, indent=2))
            print("PREPARED only. Actual subagent spawning must happen in Codex; this CLI does not spawn one.")
        elif args.action == "handoff-result":
            h = next((h for h in doc["handoffs"] if h["id"] == args.handoff_id), None)
            if h is None: raise ValueError("Unknown handoff ID")
            if h["status"] != "PREPARED": raise ValueError("Handoff already has a result")
            ev = evidence_record(project, args.evidence)
            h.update(status=args.status, result=ev, observed_by=args.observed_by, completed_at=utc())
            log_event(doc, "handoff-result", id=h["id"], status=args.status)
        else:
            gate = args.gate
            rec = doc["gates"][gate]
            if args.action == "note":
                rec["notes"].append({"text": args.text, "at": utc()})
                log_event(doc, "note", gate=gate)
            elif args.action == "advance":
                advance(project, doc, gate, args.evidence)
            elif args.action in {"fail", "block", "reopen"}:
                if rec["status"] == "SKIP": raise ValueError("Gate skipped for track")
                reset_from(doc, gate)
                if args.action != "reopen":
                    rec.update(status="FAIL" if args.action == "fail" else "BLOCKED", reason=args.reason)
                log_event(doc, args.action, gate=gate, reason=getattr(args, "reason", None))
        errors = validate(project, doc)
        if errors:
            raise ValueError("State change rejected: " + "; ".join(errors))
        store(path, doc)
        print(f"Saved task {task} revision {doc['revision']}")
        return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    for action in ("init", "status", "verify", "report", "run", "advance", "note", "fail", "block", "reopen", "recover", "handoff", "handoff-result"):
        p = sub.add_parser(action)
        p.add_argument("--project", required=True)
        p.add_argument("--task", required=True)
        if action == "init":
            p.add_argument("--track", choices=sorted(TRACKS), required=True)
            p.add_argument("--risk", choices=["normal", "high"], default="normal")
            p.add_argument("--max-retries", type=int, default=3)
        if action in {"advance", "note", "fail", "block", "reopen"}:
            p.add_argument("--gate", choices=GATES, required=True)
        if action in {"advance", "handoff-result"}:
            p.add_argument("--evidence", required=True)
        if action == "note": p.add_argument("--text", required=True)
        if action in {"fail", "block", "recover"}: p.add_argument("--reason", required=True)
        if action == "run":
            p.add_argument("--kind", choices=sorted(CHECK_KINDS), required=True)
            p.add_argument("--timeout", type=int, default=120)
            p.add_argument("command", nargs=argparse.REMAINDER)
        if action == "handoff":
            p.add_argument("--role", choices=["architect", "developer", "tester", "reviewer", "security_auditor"], required=True)
            p.add_argument("--scope", required=True)
            p.add_argument("--mode", choices=["read", "write"], default="read")
        if action == "handoff-result":
            p.add_argument("--handoff-id", required=True)
            p.add_argument("--status", choices=["REPORTED", "BLOCKED"], required=True)
            p.add_argument("--observed-by", required=True, help="Actual Codex role or operator who reported the result")
    args = parser.parse_args(argv)
    try:
        return act(args)
    except (ValueError, OSError, json.JSONDecodeError) as e:
        print("ERROR:", e, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
