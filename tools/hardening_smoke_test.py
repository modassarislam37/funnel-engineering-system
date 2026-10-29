#!/usr/bin/env python3
"""Disposable simulated repair: deliberately flawed fixture -> failure -> correction -> re-verification.

This DOES NOT invoke Codex or repair arbitrary apps; it exercises deterministic CLI paths.
"""
from pathlib import Path
import json
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
CLI=ROOT/'tools/funnel.py'
HARDEN=ROOT/'tools/hardening.py'


def run_cmd(argv, expected=0):
    r=subprocess.run(argv,capture_output=True,text=True)
    if r.returncode != expected:
        raise AssertionError(f'Expected {expected}, got {r.returncode}: {argv}\n{r.stdout}\n{r.stderr}')
    return r


def main():
    with tempfile.TemporaryDirectory() as directory:
        project=Path(directory)
        source=project/'app.py'
        source.write_text('import subprocess\ndef add(a,b):\n    return a - b\nsubprocess.run("echo unsafe", shell=True)\n')
        (project/'test_app.py').write_text('import unittest\nfrom app import add\nclass T(unittest.TestCase):\n    def test_add(self): self.assertEqual(add(2,3),5)\n')
        (project/'evidence.md').write_text('Local test fixture baseline, plan, implementation, review and handoff; no external systems used.\n')
        c=lambda action,*args:[sys.executable,str(CLI),action,'--project',str(project),'--task','rescue',*args]
        run_cmd(c('init','--track','harden'))
        for g in ('G0','G1','G2','G3','G4'):
            run_cmd(c('advance','--gate',g,'--evidence','evidence.md'))
        run_cmd(c('run','--kind','test','--',sys.executable,'-m','unittest','discover','-p','test_*.py'),expected=1)
        run_cmd(c('recover','--reason','simulated bug reproduced; correct calculation and remove shell execution'))
        source.write_text('def add(a,b):\n    return a + b\n')
        run_cmd(c('advance','--gate','G4','--evidence','evidence.md'))
        run_cmd([sys.executable,str(HARDEN),'scan','--project',str(project),'--output','.funnel/audits/after.json'])
        run_cmd(c('run','--kind','test','--',sys.executable,'-m','unittest','discover','-p','test_*.py'))
        run_cmd(c('run','--kind','security','--',sys.executable,str(HARDEN),'gate','--project',str(project),'--report','.funnel/audits/after.json'))
        run_cmd(c('run','--kind','hardening','--',sys.executable,str(HARDEN),'gate','--project',str(project),'--report','.funnel/audits/after.json'))
        for g in ('G5','G6','G7'):
            run_cmd(c('advance','--gate',g,'--evidence','evidence.md'))
        run_cmd(c('verify'))
        doc=json.loads((project/'.funnel/tasks/rescue.json').read_text())
        assert doc['retries']==1 and all(rec['status']=='PASS' for rec in doc['gates'].values())
        assert [x['exit_code'] for x in doc['checks']]==[1,0,0,0]
        print('HARDENING SMOKE PASS: real failing fixture test, bounded recovery, correction, fresh read-only audit, and G0–G7 verified.')
        print('NOTE: demo security kind reuses the limited heuristic gate; not independent vulnerability review.')
if __name__=='__main__': main()
