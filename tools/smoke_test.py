#!/usr/bin/env python3
"""Execute an entirely local end-to-end G0-G7 demo, including a real unit-test command."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

CLI = Path(__file__).resolve().parent / "funnel.py"


def call(project: Path, action: str, *args: str) -> None:
    cmd = [sys.executable, str(CLI), action, "--project", str(project), "--task", "smoke", *args]
    run = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if run.returncode != 0:
        raise RuntimeError(f"Failed: {' '.join(cmd)}\nOUT:{run.stdout}\nERR:{run.stderr}")
    print(run.stdout.strip())


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp)
        (project / "calculator.py").write_text("def double(x):\n    return x * 2\n")
        (project / "test_calculator.py").write_text(
            "import unittest\nfrom calculator import double\n"
            "class CalculatorTests(unittest.TestCase):\n"
            "    def test_double(self):\n        self.assertEqual(double(3), 6)\n"
            "    def test_negative(self):\n        self.assertEqual(double(-2), -4)\n")
        (project / "evidence.md").write_text("Smoke scope, source, architecture, implementation, verification, review and delivery documented. Self-review only.\n")
        call(project, "init", "--track", "build")
        for gate in ("G0", "G1", "G2", "G3", "G4"):
            call(project, "advance", "--gate", gate, "--evidence", "evidence.md")
        call(project, "run", "--kind", "test", "--", sys.executable, "-m", "unittest", "discover", "-p", "test_*.py", "-v")
        for gate in ("G5", "G6", "G7"):
            call(project, "advance", "--gate", gate, "--evidence", "evidence.md")
        call(project, "verify")
        call(project, "report")
        doc = json.loads((project / ".funnel" / "tasks" / "smoke.json").read_text())
        assert all(g["status"] == "PASS" for g in doc["gates"].values())
        assert doc["checks"][0]["exit_code"] == 0
        print("SMOKE PASS: eight gates and 2 real unit tests passed in local disposable project.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
