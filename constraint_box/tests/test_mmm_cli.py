from __future__ import annotations

import os
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from constraintbox import core_tools


ROOT = Path(__file__).resolve().parents[1]
class MmmCliTests(unittest.TestCase):
    def run_cli(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(ROOT / "src")
        return subprocess.run(
            [sys.executable, "-m", "constraintbox", *arguments],
            cwd=ROOT,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_cli_matches_v9_doctor_output(self):
        cli_result = self.run_cli("doctor", "--json")
        self.assertEqual(cli_result.returncode, 0)
        self.assertEqual(json.loads(cli_result.stdout), core_tools.doctor())

    def test_unknown_v9_command_exits_two_with_empty_stdout(self):
        result = self.run_cli("nosuchpack")
        self.assertEqual(result.returncode, 2)
        self.assertIn("nosuchpack", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_json_preserves_order(self):
        result = self.run_cli("doctor", "--json")
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual([row["id"] for row in payload["rows"]], list(core_tools.CORE_TOOL_IDS))

    def test_exercise_from_different_cwd_matches_cli(self):
        cli_result = self.run_cli("exercise", "--json")
        with tempfile.TemporaryDirectory() as directory:
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(ROOT / "src")
            prime_result = subprocess.run(
                [sys.executable, "-m", "constraintbox", "exercise", "--json"],
                cwd=directory,
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(prime_result.returncode, 0)
        self.assertEqual(prime_result.stdout, cli_result.stdout)
        self.assertEqual(prime_result.stderr, "")


if __name__ == "__main__":
    unittest.main()
