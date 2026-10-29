import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

funnel = load("v4funnel", ROOT / "tools" / "funnel.py")
installer = load("v4install", ROOT / "tools" / "install.py")


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dest = Path(self.tmp.name)

    def test_dry_run_no_mutations(self):
        installer.install(self.dest, upgrade=False, agents=True, dry_run=True)
        self.assertFalse((self.dest / ".agents").exists())
        self.assertFalse((self.dest / ".codex").exists())

    def test_install_skills_agents_without_config_overwrite(self):
        config = self.dest / ".codex" / "config.toml"
        config.parent.mkdir()
        config.write_text("model = 'untouched'\n")
        count, _ = installer.install(self.dest, upgrade=False, agents=True, dry_run=False)
        self.assertEqual(count, 21)
        self.assertEqual(config.read_text(), "model = 'untouched'\n")
        self.assertTrue((self.dest / ".codex" / "agents" / "fes_architect.toml").is_file())
        self.assertTrue((self.dest / ".agents" / "skills" / "funnel-engineer" / "SKILL.md").is_file())

    def test_upgrade_backups(self):
        original = self.dest / ".agents" / "skills" / "fes-test"
        original.mkdir(parents=True)
        (original / "SKILL.md").write_text("user modified\n")
        installer.install(self.dest, upgrade=True, agents=False, dry_run=False)
        self.assertEqual((self.dest / ".agents" / "skills" / "fes-test.fes-v4-2-backup" / "SKILL.md").read_text(), "user modified\n")
        self.assertIn("name: fes-test", (original / "SKILL.md").read_text())


class CliIntegrations(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.p = Path(self.tmp.name)
        (self.p / "evidence.md").write_text("actual evidence")
        (self.p / "example.py").write_text("x=1\n")
        funnel.new_task(self.p, "mytask", "review")

    def cli(self, action, *params):
        command = [sys.executable, str(ROOT / "tools" / "funnel.py"), action,
                   "--project", str(self.p), "--task", "mytask", *params]
        return subprocess.run(command, capture_output=True, text=True, check=False)

    def test_handoff_prepared_then_reported(self):
        a = self.cli("handoff", "--role", "reviewer", "--scope", "Inspect auth boundaries")
        self.assertEqual(a.returncode, 0, a.stderr)
        self.assertIn("PREPARED only", a.stdout)
        b = self.cli("handoff-result", "--handoff-id", "H001", "--status", "REPORTED",
                     "--observed-by", "fes_reviewer", "--evidence", "evidence.md")
        self.assertEqual(b.returncode, 0, b.stderr)
        self.assertEqual(self.cli("verify").returncode, 0)
        (self.p / "evidence.md").write_text("tampered")
        self.assertIn("Stale handoff result", self.cli("verify").stdout)

    def test_refuse_reviewer_write(self):
        x = self.cli("handoff", "--role", "reviewer", "--scope", "Auth code", "--mode", "write")
        self.assertEqual(x.returncode, 2)

    def test_failure_recovery_cli(self):
        # Review track has no implementation recovery.
        x = self.cli("recover", "--reason", "not supported")
        self.assertEqual(x.returncode, 2)
        self.assertIn("review track", x.stderr)

    def test_v3_migration_resets_false_passes(self):
        path = funnel.task_path(self.p, "mytask")
        doc = json.loads(path.read_text())
        doc["schema_version"] = 2
        doc["gates"]["G0"]["status"] = "PASS"
        path.write_text(json.dumps(doc))
        script = ROOT / "tools" / "migrate_v3.py"
        r = subprocess.run([sys.executable, str(script), "--project", str(self.p), "--task", "mytask"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        converted = json.loads(path.read_text())
        self.assertEqual(converted["schema_version"], 4)
        self.assertEqual(converted["gates"]["G0"]["status"], "PENDING")
        self.assertTrue(path.with_suffix(".v3-backup.json").exists())

    def test_role_toml_valid(self):
        try:
            import tomllib
        except ImportError:
            self.skipTest("tomllib requires Python 3.11")
        config = tomllib.loads((ROOT / "codex" / "config.toml").read_text())
        self.assertGreaterEqual(config["agents"]["max_concurrent_threads_per_session"], 2)
        for file in (ROOT / "codex" / "agents").glob("*.toml"):
            self.assertIn("developer_instructions", tomllib.loads(file.read_text()))


if __name__ == "__main__":
    unittest.main()
