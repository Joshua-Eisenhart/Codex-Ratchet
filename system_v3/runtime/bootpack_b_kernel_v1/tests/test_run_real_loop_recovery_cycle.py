from __future__ import annotations

import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BASE / "tools"))

from run_real_loop_recovery_cycle import (  # noqa: E402
    _inject_recovery_flag,
    _inject_recovery_invocation_source,
)


class TestRunRealLoopRecoveryCycle(unittest.TestCase):
    def test_injects_recovery_flag_when_missing(self) -> None:
        argv = ["run_real_loop_recovery_cycle.py", "--run-id", "RUN_X"]
        self.assertEqual(
            ["run_real_loop_recovery_cycle.py", "--run-id", "RUN_X", "--allow-reconstructed-artifacts"],
            _inject_recovery_flag(argv),
        )

    def test_does_not_duplicate_recovery_flag(self) -> None:
        argv = [
            "run_real_loop_recovery_cycle.py",
            "--run-id",
            "RUN_X",
            "--allow-reconstructed-artifacts",
        ]
        self.assertEqual(argv, _inject_recovery_flag(argv))

    def test_injects_dedicated_recovery_invocation_source_when_missing(self) -> None:
        argv = [
            "run_real_loop_recovery_cycle.py",
            "--run-id",
            "RUN_X",
            "--allow-reconstructed-artifacts",
        ]
        self.assertEqual(
            [
                "run_real_loop_recovery_cycle.py",
                "--run-id",
                "RUN_X",
                "--allow-reconstructed-artifacts",
                "--recovery-invocation-source",
                "dedicated_recovery_entrypoint",
            ],
            _inject_recovery_invocation_source(argv),
        )

    def test_does_not_duplicate_recovery_invocation_source(self) -> None:
        argv = [
            "run_real_loop_recovery_cycle.py",
            "--run-id",
            "RUN_X",
            "--allow-reconstructed-artifacts",
            "--recovery-invocation-source",
            "dedicated_recovery_entrypoint",
        ]
        self.assertEqual(argv, _inject_recovery_invocation_source(argv))


if __name__ == "__main__":
    unittest.main()
