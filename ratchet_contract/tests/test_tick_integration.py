import json
import subprocess
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent.parent
INTERPRETER = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"


class TickIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.completed = subprocess.run(
            [INTERPRETER, str(HERE / "run_ratchet_tick.py")],
            text=True,
            capture_output=True,
            check=False,
            timeout=120,
        )
        cls.result = json.loads(
            (HERE / "results" / "ratchet_tick.json").read_text(encoding="utf-8")
        )

    def test_tick_reports_nonempty_stdout(self):
        self.assertEqual(self.completed.returncode, 0, self.completed.stderr)
        self.assertTrue(self.completed.stdout.strip())

    def test_help_reports_usage_and_exits_zero(self):
        completed = subprocess.run(
            [INTERPRETER, str(HERE / "run_ratchet_tick.py"), "--help"],
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("usage:", completed.stdout)
        self.assertEqual(completed.stderr, "")

    def test_tick_contains_all_supplemental_gate_verdicts_per_package(self):
        expected = {
            "order_honesty_gate",
            "distinction_adequacy_gate",
            "operational_reidentification_gate",
            "gauge_rejection_gate",
        }
        for tick_name in ("tick0", "tick1", "junk_run"):
            packages = self.result[tick_name]["supplemental_gate_verdicts"]
            self.assertTrue(packages)
            for gate_results in packages.values():
                self.assertEqual(set(gate_results), expected)


if __name__ == "__main__":
    unittest.main()
