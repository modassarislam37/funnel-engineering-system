#!/usr/bin/env python3
"""Conservative, local, non-executing security heuristics for unfamiliar projects.

Not a vulnerability scanner or a proof of security. Never executes target code,
reads .env contents, or sends source to a network endpoint.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

# Import source fingerprint to bind audit to the same source snapshot as quality gates.
from funnel import fingerprint, project_dir

VERSION = '4.2.0'
MAX_FILES = 15000
MAX_FILE_BYTES = 1_000_000
ALLOWED_EXT = {'.py', '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs', '.php', '.go', '.rb', '.java', '.cs', '.html', '.vue', '.svelte'}
SKIP = {'.git','.funnel','.agents','node_modules','dist','build','coverage','venv','.venv','__pycache__','.next','vendor','.cache','target','out','tests','test','fixtures','docs','examples'}
RULES = (
    ('PY_SHELL_TRUE', 'HIGH', 'MEDIUM', 'Python subprocess shell=True can introduce shell injection', {'.py'}, r'\b(?:(?:subprocess\.)?(?:run|call|check_output|check_call|Popen))\s*\([^\n]*\bshell\s*=\s*True\b'),
    ('PY_EVAL_EXEC', 'MEDIUM', 'LOW', 'Python dynamic code execution needs taint/source review', {'.py'}, r'(?<![\w.])(?:eval|exec)\s*\('),
    ('PY_SQL_INTERPOLATION', 'HIGH', 'MEDIUM', 'SQL execution with interpolated query warrants injection review', {'.py'}, r'\b(?:execute|executemany)\s*\(\s*(?:f[\'\"]|[^\n]*\.format\s*\()'),
    ('JS_INNER_HTML', 'MEDIUM', 'LOW', 'Dynamic innerHTML can create XSS if fed untrusted content', {'.js','.jsx','.ts','.tsx','.vue','.svelte','.mjs','.cjs'}, r'\.innerHTML\s*='),
    ('REACT_UNSAFE_HTML', 'MEDIUM', 'LOW', 'dangerouslySetInnerHTML requires trusted or sanitized content', {'.jsx','.tsx','.js','.ts'}, r'\bdangerouslySetInnerHTML\s*='),
    ('NODE_EXEC', 'HIGH', 'LOW', 'Node child_process.exec requires review for command injection', {'.js','.mjs','.cjs','.ts'}, r'\b(?:child_process\.)?exec\s*\('),
    ('TLS_VERIFY_OFF', 'HIGH', 'MEDIUM', 'TLS verification explicitly disabled', {'.py','.js','.ts','.tsx'}, r'\bverify\s*=\s*False\b|rejectUnauthorized\s*:\s*false\b'),
    ('CORS_WILDCARD', 'MEDIUM', 'LOW', 'Wildcard CORS must be checked against auth and credential policy', {'.py','.js','.ts','.tsx'}, r'Access-Control-Allow-Origin[\'\"]?\s*[,=:]\s*[\'\"]\*[\'\"]|\borigin\s*:\s*[\'\"]\*[\'\"]'),
    ('JWT_NO_VERIFY', 'HIGH', 'MEDIUM', 'Signature verification disabled or unsigned JWT accepted', {'.py','.js','.ts'}, r'verify_signature[\'\"]?\s*:\s*False|algorithms\s*[:=]\s*\[\s*[\'\"]none[\'\"]'),
)
COMPILED = [(name,severity,confidence,description,exts,re.compile(pattern, re.IGNORECASE)) for name,severity,confidence,description,exts,pattern in RULES]
SECRET_ASSIGN = re.compile(r'\b(?:const|let|var|export\s+const|[A-Za-z_][\w]*\s*=\s*)\s*(?:JWT_SECRET|PRIVATE_KEY|SECRET_KEY|API_SECRET|STRIPE_SECRET_KEY)\s*[:=]\s*[\'\"]([^\'\"]+)[\'\"]',re.IGNORECASE)


def _source_files(project: Path):
    num=0
    for base, dirs, files in os.walk(project, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in SKIP and not (Path(base)/d).is_symlink())
        for name in sorted(files):
            p = Path(base)/name
            if p.suffix.lower() not in ALLOWED_EXT or p.is_symlink():
                continue
            num += 1
            if num > MAX_FILES: raise ValueError('Source file limit exceeded; scan incomplete')
            yield p


def _id(rule: str, rel: str, line: int) -> str:
    return hashlib.sha256(f'{rule}:{rel}:{line}'.encode()).hexdigest()[:16]


def _git_tracked_env(project: Path):
    # Only filenames; DO NOT read environment file contents or include secret values.
    try:
        p=subprocess.run(['git','ls-files','--cached','--','*.env','.env','.env.*','**/.env','**/.env.*'], cwd=project, capture_output=True, text=True, timeout=3, check=False)
        if p.returncode == 0:
            for line in p.stdout.splitlines():
                path=Path(line)
                if path.name in {'.env.example','.env.sample','.env.template','.env.test.example'}: continue
                if path.name == '.env' or path.name.startswith('.env.') or path.suffix == '.env':
                    yield path.as_posix()
    except (OSError,subprocess.TimeoutExpired):
        return


def scan(project: Path) -> dict:
    project=project_dir(project)
    findings=[]
    scanned=0
    truncated=[]
    for p in _source_files(project):
        if p.stat().st_size > MAX_FILE_BYTES:
            truncated.append(p.relative_to(project).as_posix())
            continue
        scanned += 1
        rel=p.relative_to(project).as_posix()
        lines=p.read_text(encoding='utf-8',errors='replace').splitlines()
        for line_no, line in enumerate(lines, 1):
            for rule, severity, confidence, description, exts, regex in COMPILED:
                if p.suffix.lower() not in exts or not regex.search(line): continue
                findings.append({'id':_id(rule,rel,line_no),'rule':rule,'severity':severity,'confidence':confidence,
                                 'path':rel,'line':line_no,'description':description,
                                 'verification':'Manual data-flow review and targeted regression test required'})
            match=SECRET_ASSIGN.search(line)
            if match and match.group(1).lower() not in {'changeme','replace_me','your-secret-here','example','test','placeholder'}:
                findings.append({'id':_id('HARDCODED_SECRET',rel,line_no),'rule':'HARDCODED_SECRET','severity':'HIGH',
                                 'confidence':'MEDIUM','path':rel,'line':line_no,
                                 'description':'Potential embedded credential; rotate if exposed and move to secret storage',
                                 'verification':'Confirm whether value is live; never print secret value'})
    for rel in _git_tracked_env(project):
        findings.append({'id':_id('TRACKED_ENV',rel,0),'rule':'TRACKED_ENV','severity':'HIGH','confidence':'HIGH',
                         'path':rel,'line':0,'description':'Environment file is tracked by Git; inspect exposure and rotate any leaked credentials',
                         'verification':'Review git history and secret storage without printing values'})
    findings.sort(key=lambda x:(x['path'],x['line'],x['rule']))
    return {'schema':1,'tool':'FES conservative static heuristics','version':VERSION,
            'created_at':datetime.now(timezone.utc).isoformat(), 'project_sha':fingerprint(project),
            'scanned_files':scanned,'skipped_oversize':truncated,
            'scope':'Local static source patterns and tracked env filenames only; no dependency CVE or runtime coverage',
            'findings':findings}


def _safe_file(project:Path, raw:str) -> Path:
    dest=(project/Path(raw)).resolve()
    if not dest.is_relative_to(project): raise ValueError('Output/report must be project-local')
    if dest.is_symlink(): raise ValueError('Symlink output not allowed')
    return dest


def write_report(project:Path,raw:str,report:dict):
    dest=_safe_file(project,raw)
    dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.is_dir(): raise ValueError('Report path is directory')
    tmp=dest.with_name(dest.name+'.tmp')
    tmp.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    os.chmod(tmp,0o600)
    os.replace(tmp,dest)
    print(f'Wrote {dest} (findings: {len(report["findings"])}, files: {report["scanned_files"]})')


def load_report(project:Path,raw:str):
    p=_safe_file(project,raw)
    doc=json.loads(p.read_text(encoding='utf-8'))
    if doc.get('schema')!=1 or not isinstance(doc.get('findings'),list): raise ValueError('Invalid audit report')
    return doc


def gate(project:Path,raw:str) -> int:
    report=load_report(project,raw)
    if report.get('project_sha') != fingerprint(project):
        print('FAIL: report source fingerprint stale',file=sys.stderr);return 1
    # Recompute conservative signals at gate time, so editing a JSON report alone
    # cannot transform an unresolved finding into a success.
    now = scan(project)
    expected = {(f['id'], f['rule'], f['severity']) for f in now['findings']}
    saved = {(f['id'], f['rule'], f['severity']) for f in report['findings']}
    if expected != saved or now['scanned_files'] != report.get('scanned_files') or now['skipped_oversize'] != report.get('skipped_oversize'):
        print('FAIL: saved report does not match a fresh read-only scan',file=sys.stderr);return 1
    if report.get('scanned_files', 0) == 0:
        print('BLOCKED: no source files were scanned',file=sys.stderr);return 1
    if report.get('skipped_oversize'):
        print('BLOCKED: unscanned oversized source files',file=sys.stderr);return 1
    blocking=[f for f in report['findings'] if f['severity'] in {'HIGH','CRITICAL'}]
    if blocking:
        print(f'FAIL: {len(blocking)} high/critical heuristic findings require triage or remediation',file=sys.stderr)
        for f in blocking: print(f"{f['id']} {f['rule']} {f['path']}:{f['line']}",file=sys.stderr)
        return 1
    print(f'PASS: no high/critical findings from limited static heuristics ({report["scanned_files"]} files). NOT a security certification.')
    return 0


def compare(project:Path, before:str, after:str) -> dict:
    b=load_report(project,before);a=load_report(project,after)
    bmap={f['id']:f for f in b['findings']};amap={f['id']:f for f in a['findings']}
    return {'disappeared_patterns':[bmap[x] for x in sorted(bmap.keys()-amap.keys())],
            'remaining_patterns':[amap[x] for x in sorted(bmap.keys() & amap.keys())],
            'new_patterns':[amap[x] for x in sorted(amap.keys()-bmap.keys())],
            'note':'Disappearance of a static pattern is NOT proof a vulnerability is fixed.'}


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    sub=ap.add_subparsers(dest='action',required=True)
    for action in ('scan','gate','compare'):
        p=sub.add_parser(action)
        p.add_argument('--project',required=True)
        if action=='scan':p.add_argument('--output',default='.funnel/audits/latest.json')
        if action=='gate':p.add_argument('--report',default='.funnel/audits/latest.json')
        if action=='compare':p.add_argument('--before',required=True);p.add_argument('--after',required=True)
    args=ap.parse_args(argv)
    try:
        project=project_dir(args.project)
        if args.action=='scan':
            write_report(project,args.output,scan(project));return 0
        if args.action=='gate':return gate(project,args.report)
        print(json.dumps(compare(project,args.before,args.after),indent=2));return 0
    except (ValueError,OSError,json.JSONDecodeError,KeyError) as e:
        print('ERROR:',e,file=sys.stderr);return 2

if __name__=='__main__':sys.exit(main())
