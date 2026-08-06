from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOADER = ROOT / "mmm" / "load.py"
PRIME = ROOT / "mmm" / "prime.sh"


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

    def run_loader(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(LOADER), *arguments],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_cli_matches_loader_raw_output(self):
        cli_result = self.run_cli("mmm", "claimgate", "nominalist")
        loader_result = self.run_loader("claimgate", "nominalist")
        self.assertEqual(cli_result.returncode, 0)
        self.assertEqual(cli_result.stdout.encode(), loader_result.stdout.encode())
        self.assertFalse(cli_result.stdout.startswith("{"))

    def test_unknown_pack_exits_two_with_empty_stdout(self):
        result = self.run_cli("mmm", "nosuchpack")
        self.assertEqual(result.returncode, 2)
        self.assertIn("nosuchpack", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_json_preserves_order(self):
        result = self.run_cli("mmm", "claimgate", "--json")
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["packs"], ["claimgate"])
        self.assertEqual(len(payload["texts"]), 1)

    def test_prime_from_different_cwd_matches_cli(self):
        cli_result = self.run_cli("mmm", "claimgate", "nominalist")
        with tempfile.TemporaryDirectory() as directory:
            prime_result = subprocess.run(
                [str(PRIME), "claimgate", "nominalist"],
                cwd=directory,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(prime_result.returncode, 0)
        self.assertEqual(prime_result.stdout.encode(), cli_result.stdout.encode())
        self.assertEqual(prime_result.stderr, "")


if __name__ == "__main__":
    unittest.main()
