#!/usr/bin/env python3
"""Install FES SKILL.md folders into documented AI coding agent locations.
No network, execution of target scripts, config overwrite, or privilege escalation.
"""
from __future__ import annotations
import argparse
import filecmp
import json
from pathlib import Path
import shutil
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ('codex', 'claude', 'cursor', 'gemini', 'copilot', 'opencode', 'all')
PROFILES = {
    'core': {'funnel-engineer', 'fes-investigate', 'fes-product', 'fes-architect',
             'fes-implement', 'fes-test', 'fes-review', 'fes-deliver', 'fes-recovery'},
    'rescue': {'funnel-engineer', 'fes-investigate', 'fes-vibe-hardening', 'fes-security',
               'fes-test', 'fes-review', 'fes-recovery', 'fes-implement', 'fes-deliver',
               'fes-skill-forge', 'fes-agent-portability'},
}

class InstallError(ValueError):
    pass


def destinations(agent: str, scope: str, root: Path) -> list[Path]:
    if scope == 'project':
        mapped = {'codex': '.agents/skills', 'claude': '.claude/skills',
                  'cursor': '.cursor/skills', 'gemini': '.gemini/skills',
                  'copilot': '.github/skills', 'opencode': '.opencode/skills'}
    else:
        mapped = {'codex': '.agents/skills', 'claude': '.claude/skills',
                  'cursor': '.cursor/skills', 'gemini': '.gemini/skills',
                  'copilot': '.copilot/skills', 'opencode': '.config/opencode/skills'}
    choices = ['codex', 'claude'] if agent == 'all' else [agent]
    return [root / mapped[x] for x in choices]


def no_symlink_ancestors(path: Path, base: Path) -> None:
    check = path
    while check != base:
        if check.is_symlink():
            raise InstallError(f'Symlink in destination: {check}')
        if check.parent == check:
            raise InstallError(f'Destination escaped install root: {path}')
        check = check.parent
    if base.is_symlink():
        raise InstallError('Install root is a symlink')


def same_tree(a: Path, b: Path) -> bool:
    if not a.is_dir() or not b.is_dir():
        return False
    ax = {p.relative_to(a) for p in a.rglob('*') if p.is_file()}
    bx = {p.relative_to(b) for p in b.rglob('*') if p.is_file()}
    return ax == bx and all(filecmp.cmp(a / x, b / x, shallow=False) for x in ax)


def replace_tree(src: Path, dst: Path, *, upgrade: bool, dry_run: bool, base: Path) -> str:
    no_symlink_ancestors(dst, base)
    if not src.is_dir() or not (src / 'SKILL.md').is_file():
        raise InstallError(f'Invalid source skill: {src}')
    if any(p.is_symlink() for p in src.rglob('*')):
        raise InstallError(f'Source contains symlink: {src}')
    if dst.is_symlink():
        raise InstallError(f'Symlink skill target: {dst}')
    if dst.exists() and not dst.is_dir():
        raise InstallError(f'Not a skill directory: {dst}')
    if dst.exists() and same_tree(src, dst):
        return 'unchanged'
    if dst.exists() and not upgrade:
        return 'skipped_conflict'
    if dry_run:
        return 'upgrade_planned' if dst.exists() else 'install_planned'
    dst.parent.mkdir(parents=True, exist_ok=True)
    stage = dst.with_name('.fes-tmp-' + uuid.uuid4().hex)
    backup = dst.with_name(dst.name + '.fes-v5-backup-' + uuid.uuid4().hex[:8])
    try:
        shutil.copytree(src, stage)
        if dst.exists():
            dst.rename(backup)
            try:
                stage.rename(dst)
            except BaseException:
                backup.rename(dst)
                raise
            return 'upgraded_backup=' + str(backup)
        stage.rename(dst)
        return 'installed'
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def replace_file(src: Path, dst: Path, *, upgrade: bool, dry_run: bool, base: Path) -> str:
    no_symlink_ancestors(dst, base)
    if dst.is_symlink():
        raise InstallError(f'Symlink file target: {dst}')
    if dst.exists() and not dst.is_file():
        raise InstallError(f'Non-file agent role: {dst}')
    if dst.exists() and dst.read_bytes() == src.read_bytes():
        return 'unchanged'
    if dst.exists() and not upgrade:
        return 'skipped_conflict'
    if dry_run:
        return 'upgrade_planned' if dst.exists() else 'install_planned'
    dst.parent.mkdir(parents=True, exist_ok=True)
    stage = dst.with_name('.fes-tmp-' + uuid.uuid4().hex)
    backup = dst.with_name(dst.name + '.fes-v5-backup-' + uuid.uuid4().hex[:8])
    try:
        shutil.copy2(src, stage)
        if dst.exists():
            dst.rename(backup)
            try:
                stage.rename(dst)
            except BaseException:
                backup.rename(dst)
                raise
            return 'upgraded_backup=' + str(backup)
        stage.rename(dst)
        return 'installed'
    finally:
        if stage.exists(): stage.unlink()


def install(agent: str, scope: str, destination: Path, profile: str = 'full',
            upgrade: bool = False, dry_run: bool = False, codex_roles: bool = False,
            source: Path = ROOT) -> list[dict]:
    if agent not in AGENTS:
        raise InstallError(f'Unknown agent: {agent}')
    if profile not in ('full', 'core', 'rescue'):
        raise InstallError(f'Unknown profile: {profile}')
    destination = destination.expanduser().absolute()
    if not destination.is_dir() or destination.is_symlink():
        raise InstallError(f'Destination root unavailable or linked: {destination}')
    if codex_roles and agent not in ('codex', 'all'):
        raise InstallError('Codex role configs only available with --agent codex or --agent all')
    selected = [p for p in sorted((source / 'skills').iterdir())
                if p.is_dir() and (p / 'SKILL.md').is_file()
                and (profile == 'full' or p.name in PROFILES[profile])]
    actions = []
    for folder in destinations(agent, scope, destination):
        for src in selected:
            dst = folder / src.name
            status = replace_tree(src, dst, upgrade=upgrade, dry_run=dry_run, base=destination)
            actions.append({'skill': src.name, 'target': str(dst), 'result': status})
    if codex_roles:
        for src in sorted((source / 'codex/agents').glob('*.toml')):
            dst = destination / '.codex/agents' / src.name
            status = replace_file(src, dst, upgrade=upgrade, dry_run=dry_run, base=destination)
            actions.append({'role': src.name, 'target': str(dst), 'result': status})
        snippet = destination / '.codex/fes-v5-config-snippet.toml'
        status = replace_file(source / 'codex/config.toml', snippet,
                              upgrade=False, dry_run=dry_run, base=destination)
        actions.append({'snippet': 'manual_merge_only', 'target': str(snippet), 'result': status})
    return actions


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--agent', choices=AGENTS, required=True)
    parser.add_argument('--scope', choices=['user', 'project'], default='user')
    parser.add_argument('--project', help='Required with --scope project')
    parser.add_argument('--profile', choices=['full', 'core', 'rescue'], default='full')
    parser.add_argument('--upgrade', action='store_true', help='Back up existing skill before overwriting')
    parser.add_argument('--dry-run', action='store_true', help='Show planned actions without writes')
    parser.add_argument('--with-codex-roles', action='store_true')
    parser.add_argument('--json', action='store_true', help='Emit machine-readable install result')
    args = parser.parse_args(argv)
    if args.scope == 'project' and not args.project:
        parser.error('--project is required for project scope')
    dest = Path(args.project).expanduser() if args.scope == 'project' else Path.home()
    try:
        results = install(args.agent, args.scope, dest, args.profile, args.upgrade,
                          args.dry_run, args.with_codex_roles)
        if args.json:
            print(json.dumps({'agent': args.agent, 'scope': args.scope,
                              'profile': args.profile, 'dry_run': args.dry_run,
                              'actions': results}, indent=2))
        else:
            for x in results:
                print(x['result'], x['target'])
            print(f'{len(results)} actions; existing unrelated files were not changed.')
        if any(x['result'] == 'skipped_conflict' for x in results):
            print('Some existing skills differ. Inspect and rerun with --upgrade to back up and replace.', file=sys.stderr)
        return 0
    except (InstallError, OSError, ValueError) as e:
        print('ERROR:', e, file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
