#!/usr/bin/env python3
"""Publish the complete Funnel Engineering System source to its empty GitHub repository.

Runs locally with the user's existing Git credentials. Never force-pushes,
changes an existing remote repository, or uploads private files.
"""
import argparse
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path

DEFAULT_REMOTE = "https://github.com/modassarislam37/funnel-engineering-system.git"
REQUIRED = (
    "README.md", "LICENSE", "CONTRIBUTING.md", "SECURITY.md", "manifest.json",
    ".github/workflows/ci.yml", "tools/funnel.py", "tools/install_portable.py",
    "tests/test_funnel.py", "skills/funnel-engineer/SKILL.md",
)
SKIP_DIRS = {".git", ".funnel", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
SKIP_SUFFIXES = {".pyc", ".pyo"}


def git(args, cwd=None, capture=False):
    proc = subprocess.run(["git", *args], cwd=cwd, text=True,
                          stdout=subprocess.PIPE if capture else None,
                          stderr=subprocess.PIPE if capture else None,
                          check=False)
    if proc.returncode:
        detail = (proc.stderr or "").strip()
        raise RuntimeError("git " + " ".join(args) + " failed" + (": " + detail if detail else ""))
    return (proc.stdout or "").strip()


def publish(source, remote, dry_run=False):
    source = Path(source).resolve()
    missing = [name for name in REQUIRED if not (source / name).is_file()]
    if missing:
        raise RuntimeError("Missing required release files: " + ", ".join(missing))
    skills = list((source / "skills").glob("*/SKILL.md"))
    if len(skills) != 22:
        raise RuntimeError(f"Expected 22 skills; found {len(skills)}")
    files = sorted(p for p in source.rglob("*") if p.is_file()
                   and not SKIP_DIRS.intersection(p.relative_to(source).parts)
                   and p.suffix not in SKIP_SUFFIXES)
    if not files:
        raise RuntimeError("No release files detected")
    print(f"Release source: {source}; {len(files)} files, {len(skills)} skills")
    print(f"Destination: {remote}")
    if dry_run:
        for p in files: print(p.relative_to(source).as_posix())
        return None

    # Explicitly reject a nonempty remote to avoid overwriting someone else's work.
    if git(["ls-remote", "--heads", remote], capture=True).strip():
        raise RuntimeError("Remote has an existing branch. Publication refused to prevent overwrites.")
    with tempfile.TemporaryDirectory(prefix="fes-github-publication-") as tmp:
        checkout = Path(tmp) / "repo"
        git(["clone", "--quiet", remote, str(checkout)])
        # Verify empty after cloning too (guards races). Never force-push.
        if git(["rev-list", "--all"], cwd=checkout, capture=True).strip():
            raise RuntimeError("Remote repository is not empty; no files were changed.")
        git(["checkout", "--quiet", "-b", "main"], cwd=checkout)
        for p in files:
            target = checkout / p.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, target)
        git(["add", "--all"], cwd=checkout)
        git(["diff", "--cached", "--check"], cwd=checkout)
        git(["commit", "-m", "chore: publish Funnel Engineering System Universal v5.0"],cwd=checkout)
        git(["push", "-u", "origin", "main"],cwd=checkout)
        commit = git(["rev-parse", "HEAD"],cwd=checkout,capture=True)
        print(f"Published {len(files)} files at commit {commit}")
        return commit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--remote", default=DEFAULT_REMOTE, help="Destination empty repository")
    parser.add_argument("--dry-run", action="store_true", help="Check source and list files without Git changes")
    args = parser.parse_args()
    try:
        publish(Path(__file__).resolve().parents[1], args.remote, args.dry_run)
    except (RuntimeError, OSError) as exc:
        print(f"Publication stopped: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
