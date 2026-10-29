"""FES v4 state-engine unit and integration tests: no network calls."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import json

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("funnel", ROOT / "tools" / "funnel.py")
funnel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(funnel)


class V4Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = Path(self.tmp.name)
        (self.project / "src.py").write_text("VALUE = 1\n")
        (self.project / "evidence.md").write_text("Measured result\n")
        self.slug = "test-task"
        funnel.new_task(self.project, self.slug, "build")

    def load(self):
        return funnel.read_task(self.project, self.slug)[1]

    def save(self, doc):
        funnel.store(funnel.task_path(self.project, self.slug), doc)

    def pass_to_g4(self):
        doc = self.load()
        for g in funnel.GATES[:5]:
            funnel.advance(self.project, doc, g, "evidence.md")
        self.save(doc)
        return doc

    def test_fresh_state_valid(self):
        self.assertEqual(funnel.validate(self.project, self.load()), [])

    def test_slug_validation(self):
        for slug in ("../escape", "", "x" * 65, "white space"):
            with self.assertRaises(ValueError):
                funnel.task_path(self.project, slug)

    def test_prevent_skipped_gate(self):
        with self.assertRaises(ValueError):
            funnel.advance(self.project, self.load(), "G1", "evidence.md")

    def test_reject_missing_evidence(self):
        with self.assertRaises(ValueError):
            funnel.advance(self.project, self.load(), "G0", "absent.md")

    def test_reject_path_escape(self):
        with self.assertRaises(ValueError):
            funnel.advance(self.project, self.load(), "G0", "../anywhere")

    def test_evidence_tamper_detected(self):
        doc = self.load()
        funnel.advance(self.project, doc, "G0", "evidence.md")
        (self.project / "evidence.md").write_text("Changed after pass")
        self.assertTrue(any("stale evidence" in e for e in funnel.validate(self.project, doc)))

    def test_source_tamper_detected(self):
        doc = self.pass_to_g4()
        (self.project / "src.py").write_text("VALUE = 2\n")
        self.assertTrue(any("source changed" in e for e in funnel.validate(self.project, doc)))

    def test_build_requires_post_g4_test(self):
        doc = self.pass_to_g4()
        with self.assertRaisesRegex(ValueError, "requires successful"):
            funnel.advance(self.project, doc, "G5", "evidence.md")

    def test_valid_check_unlocks_g5(self):
        doc = self.pass_to_g4()
        self.assertEqual(funnel.run_check(self.project, doc, [sys.executable, "-c", "assert True"], "test", 5), 0)
        funnel.advance(self.project, doc, "G5", "evidence.md")
        self.assertEqual(funnel.validate(self.project, doc), [])

    def test_no_zero_exit_after_failed_latest_check(self):
        doc = self.pass_to_g4()
        funnel.run_check(self.project, doc, [sys.executable, "-c", "assert True"], "test", 5)
        funnel.run_check(self.project, doc, [sys.executable, "-c", "raise Exception('bad')"], "test", 5)
        with self.assertRaisesRegex(ValueError, "requires successful"):
            funnel.advance(self.project, doc, "G5", "evidence.md")

    def test_rerun_after_recovery(self):
        doc = self.pass_to_g4()
        funnel.run_check(self.project, doc, [sys.executable, "-c", "exit(2)"], "test", 5)
        funnel.recover(doc, "failed regression")
        self.assertEqual(doc["gates"]["G4"]["status"], "PENDING")
        funnel.advance(self.project, doc, "G4", "evidence.md")
        with self.assertRaisesRegex(ValueError, "requires successful"):
            funnel.advance(self.project, doc, "G5", "evidence.md")
        self.assertEqual(funnel.run_check(self.project, doc, [sys.executable, "-c", "assert True"], "test", 5), 0)
        funnel.advance(self.project, doc, "G5", "evidence.md")
        self.assertEqual(funnel.validate(self.project, doc), [])

    def test_recovery_budget_exhausts(self):
        doc = self.pass_to_g4()
        doc["max_retries"] = 1
        for _ in range(2):
            funnel.run_check(self.project, doc, [sys.executable, "-c", "exit(2)"], "test", 5)
            funnel.recover(doc, "still failing")
            if doc["gates"]["G4"]["status"] != "BLOCKED":
                funnel.advance(self.project, doc, "G4", "evidence.md")
        self.assertEqual(doc["gates"]["G4"]["status"], "BLOCKED")
        self.assertEqual(doc["retries"], 2)

    def test_high_risk_needs_security(self):
        funnel.new_task(self.project, "sensitive", "build", risk="high")
        _, doc = funnel.read_task(self.project, "sensitive")
        for g in funnel.GATES[:5]:
            funnel.advance(self.project, doc, g, "evidence.md")
        funnel.run_check(self.project, doc, [sys.executable, "-c", "assert True"], "test", 5)
        with self.assertRaisesRegex(ValueError, "security"):
            funnel.advance(self.project, doc, "G5", "evidence.md")
        import importlib.util
        spec=importlib.util.spec_from_file_location("hardening", ROOT / "tools" / "hardening.py")
        # hardening.py imports funnel, so make tools visible to Python imports.
        sys.path.insert(0,str(ROOT / "tools"))
        import hardening
        hardening.write_report(self.project,'.funnel/audits/scan.json',hardening.scan(self.project))
        funnel.run_check(self.project, doc, [sys.executable, str(ROOT / "tools" / "hardening.py"), "gate", "--project", str(self.project), "--report", ".funnel/audits/scan.json"], "security", 5)
        funnel.run_check(self.project, doc, [sys.executable,str(ROOT / "tools" / "hardening.py"), "gate", "--project",str(self.project),"--report",'.funnel/audits/scan.json'], "hardening", 5)
        funnel.advance(self.project, doc, "G5", "evidence.md")
        self.assertEqual(funnel.validate(self.project, doc), [])

    def test_review_track_skips_implementation(self):
        funnel.new_task(self.project, "audit", "review")
        _, doc = funnel.read_task(self.project, "audit")
        self.assertEqual(doc["gates"]["G4"]["status"], "SKIP")
        self.assertEqual(doc["required_checks"], [])

    def test_reopen_invalidates_downstream(self):
        doc = self.pass_to_g4()
        funnel.reset_from(doc, "G2")
        self.assertEqual(doc["gates"]["G3"]["status"], "PENDING")
        self.assertEqual(doc["gates"]["G4"]["source_sha"], None)

    def test_source_generation_ignored(self):
        first = funnel.fingerprint(self.project)
        out = self.project / ".funnel" / "logs"
        out.mkdir(parents=True, exist_ok=True)
        (out / "log.txt").write_text("temporary")
        self.assertEqual(first, funnel.fingerprint(self.project))

    def test_source_check_mutation_invalid(self):
        doc = self.pass_to_g4()
        command = [sys.executable, "-c", "open('src.py','w').write('VALUE = 9\\n')"]
        self.assertNotEqual(funnel.run_check(self.project, doc, command, "test", 5), 0)
        self.assertEqual(doc["checks"][-1]["exit_code"], 125)

    def test_log_tamper_detection(self):
        doc = self.pass_to_g4()
        funnel.run_check(self.project, doc, [sys.executable, "-c", "print('ok')"], "test", 5)
        (self.project / doc["checks"][-1]["log"]).write_text("faked")
        self.assertTrue(any("tampered" in e for e in funnel.validate(self.project, doc)))

    def test_report_produced(self):
        path = funnel.report(self.project, self.load())
        self.assertTrue(path.is_file())
        self.assertIn("Checkpoint validation", path.read_text())

    def test_prepared_handoff_not_spawning_agent(self):
        self.assertFalse((self.project / ".codex").exists())
        self.assertEqual(self.load()["handoffs"], [])

    def test_cli_end_to_end(self):
        cli = ROOT / "tools" / "funnel.py"
        cmd = [sys.executable, str(cli), "status", "--project", str(self.project), "--task", self.slug]
        self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 0)

    def test_no_log_secrets_simple_redaction(self):
        rec = funnel.write_log(self.project, self.slug, 1, ["echo"], 0, "api_key=abcdefg password: xyz123")
        txt = (self.project / rec["path"]).read_text()
        self.assertNotIn("abcdefg", txt)
        self.assertNotIn("xyz123", txt)

    def test_atomic_permissions(self):
        path = funnel.task_path(self.project, self.slug)
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
