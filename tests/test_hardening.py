import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import hardening
import evaluation
import funnel


class HardeningTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.p=Path(self.tmp.name)
        (self.p/'app.py').write_text('def safe(x):\n    return x + 1\n')

    def write_vuln(self):
        (self.p/'app.py').write_text('import subprocess\nsubprocess.run(user_input, shell=True)\n')

    def test_scan_detects_shell_true_without_running_project(self):
        self.write_vuln()
        doc=hardening.scan(self.p)
        self.assertIn('PY_SHELL_TRUE',{x['rule'] for x in doc['findings']})

    def test_scan_secret_does_not_disclose_value(self):
        marker='DO_NOT_PUBLISH_REAL_SECRET_VALUE_123'
        (self.p/'app.js').write_text('const JWT_SECRET = "'+marker+'";\n')
        doc=hardening.scan(self.p)
        self.assertIn('HARDCODED_SECRET',{x['rule'] for x in doc['findings']})
        self.assertNotIn(marker,json.dumps(doc))

    def test_gate_rejects_finding(self):
        self.write_vuln()
        hardening.write_report(self.p,'.funnel/audits/scan.json',hardening.scan(self.p))
        self.assertEqual(hardening.gate(self.p,'.funnel/audits/scan.json'),1)

    def test_gate_passes_clean_fixture_with_limitations(self):
        hardening.write_report(self.p,'.funnel/audits/scan.json',hardening.scan(self.p))
        self.assertEqual(hardening.gate(self.p,'.funnel/audits/scan.json'),0)

    def test_gate_rejects_stale_audit(self):
        hardening.write_report(self.p,'.funnel/audits/scan.json',hardening.scan(self.p))
        (self.p/'app.py').write_text('def safe(x): return x + 3\n')
        self.assertEqual(hardening.gate(self.p,'.funnel/audits/scan.json'),1)

    def test_gate_rejects_tampered_report(self):
        self.write_vuln()
        hardening.write_report(self.p,'.funnel/audits/scan.json',hardening.scan(self.p))
        file=self.p/'.funnel/audits/scan.json'
        doc=json.loads(file.read_text());doc['findings']=[];file.write_text(json.dumps(doc))
        self.assertEqual(hardening.gate(self.p,'.funnel/audits/scan.json'),1)

    def test_gate_rejects_empty_project(self):
        (self.p/'app.py').unlink()
        hardening.write_report(self.p,'.funnel/audits/scan.json',hardening.scan(self.p))
        self.assertEqual(hardening.gate(self.p,'.funnel/audits/scan.json'),1)

    def test_gate_rejects_oversized_source(self):
        (self.p/'huge.py').write_text('#'*(hardening.MAX_FILE_BYTES+1))
        hardening.write_report(self.p,'.funnel/audits/scan.json',hardening.scan(self.p))
        self.assertEqual(hardening.gate(self.p,'.funnel/audits/scan.json'),1)

    def test_compare_does_not_claim_verified_fix(self):
        self.write_vuln()
        hardening.write_report(self.p,'.funnel/audits/before.json',hardening.scan(self.p))
        (self.p/'app.py').write_text('def safe(x): return x\n')
        hardening.write_report(self.p,'.funnel/audits/after.json',hardening.scan(self.p))
        result=hardening.compare(self.p,'.funnel/audits/before.json','.funnel/audits/after.json')
        self.assertEqual(len(result['disappeared_patterns']),1)
        self.assertIn('NOT proof',result['note'])

    def test_scan_symlink_and_dependency_skip(self):
        folder=self.p/'node_modules';folder.mkdir();(folder/'bad.js').write_text('el.innerHTML = user;')
        (self.p/'skipped.js').symlink_to(folder/'bad.js')
        self.assertEqual(hardening.scan(self.p)['findings'],[])

    def test_project_path_escape_refused(self):
        with self.assertRaises(ValueError):
            hardening.write_report(self.p,'../outside.json',hardening.scan(self.p))

    def test_harden_track_requires_hardening_and_security(self):
        doc=funnel.new_task(self.p,'harden-app','harden')
        self.assertEqual(doc['risk'],'high')
        self.assertEqual(set(doc['required_checks']),{'test','security','hardening'})

    def test_hardening_kind_cannot_be_arbitrarily_labeled(self):
        doc=funnel.new_task(self.p,'guard','harden')
        with self.assertRaisesRegex(ValueError,'hardening'):
            funnel.run_check(self.p,doc,[sys.executable,'-c','pass'],'hardening',5)

    def test_hardening_gate_runs_in_funnel(self):
        doc=funnel.new_task(self.p,'verified','harden')
        for gate in funnel.GATES[:5]:funnel.advance(self.p,doc,gate,'app.py')
        path='.funnel/audits/scan.json'
        hardening.write_report(self.p,path,hardening.scan(self.p))
        self.assertEqual(funnel.run_check(self.p,doc,[sys.executable,str(ROOT/'tools/hardening.py'),'gate','--project',str(self.p),'--report',path],'hardening',10),0)
        self.assertEqual(funnel.run_check(self.p,doc,[sys.executable,'-c','assert True'],'test',5),0)
        self.assertEqual(funnel.run_check(self.p,doc,[sys.executable,str(ROOT/'tools/hardening.py'),'gate','--project',str(self.p),'--report',path],'security',5),0)
        funnel.advance(self.p,doc,'G5','app.py')
        self.assertEqual(funnel.validate(self.p,doc),[])


class EvaluationTests(unittest.TestCase):
    def test_score_rejects_zero_tests(self):
        with self.assertRaisesRegex(ValueError,'zero'):
            evaluation.score(dict(tests_passed=0,tests_total=0,high_findings=0,critical_findings=0,scope_violations=0,human_interventions=0))

    def test_score_requires_all_evidence_fields(self):
        with self.assertRaises(ValueError):evaluation.score({'tests_passed':1,'tests_total':2})

    def test_valid_pair(self):
        b={'tests_passed':1,'tests_total':2,'high_findings':0,'critical_findings':0,'scope_violations':0,'human_interventions':1}
        c={'tests_passed':2,'tests_total':2,'high_findings':0,'critical_findings':0,'scope_violations':0,'human_interventions':0}
        result=evaluation.evaluate([{'id':'sample','baseline':b,'candidate':c}])
        self.assertEqual(result['delta_percentage_points'],100.0)
        self.assertEqual(result['candidate_passed'],1)

    def test_repeat_ids_invalid(self):
        d={'tests_passed':1,'tests_total':1,'high_findings':0,'critical_findings':0,'scope_violations':0,'human_interventions':0}
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            evaluation.evaluate([{'id':'sample','baseline':d,'candidate':d}]*2)


if __name__=='__main__':unittest.main()

class RoleUpgradeTests(unittest.TestCase):
    def test_installer_upgrades_role_with_backup(self):
        from install import install
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);roles=p/'.codex/agents';roles.mkdir(parents=True)
            (roles/'fes_reviewer.toml').write_text('sandbox_mode = "read-only"\n')
            count, skipped=install(p,upgrade=True,agents=True,dry_run=False)
            self.assertEqual(count,21)
            self.assertIn('name = "fes_reviewer"',(roles/'fes_reviewer.toml').read_text())
            self.assertEqual((roles/'fes_reviewer.toml.fes-v4-2-backup').read_text(),'sandbox_mode = "read-only"\n')

    def test_role_schema_fully_formed(self):
        try:
            import tomllib
        except ModuleNotFoundError:  # Python 3.10 test-only fallback
            import tomli as tomllib
        from validate_package import validate
        self.assertEqual(validate(ROOT),[])
        for p in (ROOT/'codex/agents').glob('*.toml'):
            data=tomllib.loads(p.read_text())
            self.assertEqual(data['name'],p.stem)
            self.assertTrue(data['description'] and data['developer_instructions'])
            self.assertNotIn('sandbox_mode',data)

class SecurityCheckPolicyTests(unittest.TestCase):
    def test_noop_security_disallowed(self):
        self.assertFalse(funnel.security_command_allowed([sys.executable,'-c','assert True']))
        self.assertFalse(funnel.security_command_allowed(['true']))

    def test_known_auditor_allowed(self):
        self.assertTrue(funnel.security_command_allowed(['npm','audit','--offline']))
        self.assertTrue(funnel.security_command_allowed([sys.executable,'-m','bandit','-r','.']))
