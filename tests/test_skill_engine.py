"""Regression tests for FES v4.1 project-local automatic skill forge."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("skill_engine", ROOT / "tools" / "skill_engine.py")
forge_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(forge_module)


class TestSkillForge(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = Path(self.tmp.name)
        task = self.project / ".funnel" / "tasks" / "my-task.json"
        task.parent.mkdir(parents=True)
        task.write_text(json.dumps({"task": "my-task", "schema_version": 4}))
        draft = self.project / ".funnel" / "skill-drafts" / "domain.md"
        draft.parent.mkdir(parents=True)
        draft.write_text("## Steps\n" + "1. Check a specific observable domain contract and maintain its owner.\n" * 3)

    def make(self, slug="domain-helper", task="my-task"):
        return forge_module.forge(
            self.project, task, slug,
            "Use only when a project needs domain-specific data verification tasks",
            "A domain contract change needs a specialized validation procedure",
            "Existing generic test skill already covers this problem fully",
            ".funnel/skill-drafts/domain.md",
            "Run exact domain checks, inspect logs, and record failed cases",
            "Existing generic engineering skills do not cover this domain contract",
        )

    def test_create_and_receipt_verify(self):
        record = self.make()
        self.assertEqual(record["name"], "fes-auto-domain-helper")
        self.assertTrue((self.project / record["path"]).is_file())
        self.assertTrue(forge_module.verify(self.project)["valid"])
        self.assertFalse(record["behavior_tested"])

    def test_inventory_lists_generated(self):
        self.make()
        inv = forge_module.inventory(self.project)
        names = [x["name"] for x in inv]
        self.assertIn("fes-auto-domain-helper", names)
        self.assertIn("funnel-engineer", names)

    def test_match_is_advisory(self):
        self.make()
        matches = forge_module.match_skills(forge_module.inventory(self.project), "domain data verification")
        self.assertTrue(matches)
        self.assertTrue(any(x["name"] == "fes-auto-domain-helper" for x in matches))

    def test_duplicate_rejected(self):
        self.make()
        with self.assertRaisesRegex(forge_module.SkillError, "Already generated"):
            self.make()

    def test_max_two_per_task(self):
        self.make("alpha")
        self.make("beta")
        with self.assertRaisesRegex(forge_module.SkillError, "Maximum"):
            self.make("gamma")

    def test_no_arbitrary_task(self):
        with self.assertRaisesRegex(forge_module.SkillError, "Initialize"):
            self.make(task="other")

    def test_path_escape_rejected(self):
        outside = self.project.parent / "not-project.md"
        with self.assertRaises(forge_module.SkillError):
            forge_module.within(self.project, "../not-project.md")

    def test_symlink_draft_outside_rejected(self):
        target = Path(self.tmp.name).parent / "not-project.md"
        target.write_text("don't read external file")
        self.addCleanup(target.unlink)
        (self.project / "outside.md").symlink_to(target)
        with self.assertRaises(forge_module.SkillError):
            forge_module.within(self.project, "outside.md")

    def test_invalid_slug_does_not_write(self):
        with self.assertRaises(forge_module.SkillError):
            self.make("../secrets")
        self.assertFalse((self.project / ".agents").exists())

    def test_funnel_gate_validation_checks_generated_skill_receipt(self):
        spec = importlib.util.spec_from_file_location("funnel_for_forge", ROOT / "tools" / "funnel.py")
        funnel = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(funnel)
        record = self.make()
        doc = json.loads((self.project / ".funnel" / "tasks" / "my-task.json").read_text())
        # Use a normal v4 checkpoint for cross-system validation, preserving the receipt.
        (self.project / ".funnel" / "tasks" / "my-task.json").unlink()
        doc = funnel.new_task(self.project, "my-task", "review")
        self.assertEqual(funnel.validate(self.project, doc), [])
        entry = self.project / record["path"]
        entry.write_text(entry.read_text() + "\nTampered")
        self.assertTrue(any("modified generated skill" in e for e in funnel.validate(self.project, doc)))

    def test_tamper_detection(self):
        record = self.make()
        p = self.project / record["path"]
        p.write_text(p.read_text() + "\n# changed\n")
        v = forge_module.verify(self.project)
        self.assertFalse(v["valid"])
        self.assertEqual(v["skills"][0]["status"], "MISSING_OR_MODIFIED")

    def test_missing_detected(self):
        record = self.make()
        (self.project / record["path"]).unlink()
        self.assertFalse(forge_module.verify(self.project)["valid"])

    def test_symlink_collision_rejected(self):
        skill_dir = self.project / ".agents" / "skills"
        skill_dir.mkdir(parents=True)
        (skill_dir / "fes-auto-domain-helper").symlink_to(self.project / ".funnel", target_is_directory=True)
        with self.assertRaisesRegex(forge_module.SkillError, "exists"):
            self.make()

    def test_oversize_procedure_rejected(self):
        (self.project / ".funnel" / "skill-drafts" / "domain.md").write_text("x" * 20000)
        with self.assertRaisesRegex(forge_module.SkillError, "100–12000"):
            self.make()

    def test_inventory_cli_json(self):
        p = subprocess.run([sys.executable, str(ROOT / "tools" / "skill_engine.py"),
                            "inventory", "--project", str(self.project), "--need", "API"],
                            text=True, capture_output=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads(p.stdout)
        self.assertFalse(data["coverage_is_semantic"])
        self.assertGreater(data["count"], 0)

    def test_cli_full_auto_apply_flow(self):
        cmd = [sys.executable, str(ROOT / "tools" / "skill_engine.py"), "forge",
               "--project", str(self.project), "--task", "my-task", "--slug", "domain-helper",
               "--description", "Use this workflow to validate a domain-specific contract",
               "--when", "A contract-specific check is required in this repository",
               "--exclude", "A matching pre-existing skill covers the current situation",
               "--procedure-file", ".funnel/skill-drafts/domain.md",
               "--verification", "Run local contract tests and inspect evidence and failures",
               "--reason", "Existing skills lack the domain-specific verification steps"]
        result = subprocess.run(cmd, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        parsed = json.loads(result.stdout)
        self.assertIn("SKILL.md", parsed["same_session_instruction"])
        v = subprocess.run([sys.executable, str(ROOT / "tools" / "skill_engine.py"), "verify",
                            "--project", str(self.project)], capture_output=True, text=True)
        self.assertEqual(v.returncode, 0, v.stderr)


if __name__ == "__main__":
    unittest.main()
