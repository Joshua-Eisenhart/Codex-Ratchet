from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from constraintbox.exploratory_sim import SOURCE_RELATIVE, run_ijk_prototype


class ExploratoryIJKTests(unittest.TestCase):
    def _source_tree(self, root: Path, *, falsify_finite_check: bool = False) -> None:
        source = Path(__file__).parents[2] / SOURCE_RELATIVE
        target = root / SOURCE_RELATIVE
        target.parent.mkdir(parents=True)
        text = source.read_text(encoding="utf-8")
        if falsify_finite_check:
            text = text.replace('"finite_carrier": N == 24,', '"finite_carrier": N == -1,')
        target.write_text(text, encoding="utf-8")

    def test_source_runs_and_captures_telemetry(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._source_tree(root)
            receipt, exit_code = run_ijk_prototype(
                run_root=root / "run",
                cr_root=root,
                timeout_seconds=30,
            )
            self.assertEqual(exit_code, 0)
            self.assertEqual(receipt["status"], "EXECUTED")
            self.assertTrue(receipt["execution"]["telemetry"]["checks_all_true"])
            self.assertAlmostEqual(
                receipt["execution"]["telemetry"]["math"]["noncommutator_frobenius"],
                1.7873395112465118,
            )
            self.assertFalse(receipt["promotion_allowed"])

    def test_false_check_does_not_suppress_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._source_tree(root, falsify_finite_check=True)
            receipt, exit_code = run_ijk_prototype(
                run_root=root / "run",
                cr_root=root,
                timeout_seconds=30,
            )
            self.assertEqual(exit_code, 0)
            self.assertEqual(receipt["status"], "EXECUTED")
            telemetry = receipt["execution"]["telemetry"]
            self.assertFalse(telemetry["checks"]["finite_carrier"])
            self.assertFalse(telemetry["checks_all_true"])
            self.assertTrue(receipt["checks_do_not_block_execution"])


if __name__ == "__main__":
    unittest.main()
