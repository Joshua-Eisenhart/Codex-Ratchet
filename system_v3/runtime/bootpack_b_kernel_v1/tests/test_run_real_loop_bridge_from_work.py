from __future__ import annotations

import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BASE / "tools"))

from run_real_loop_bridge_from_work import _compatibility_recovery_bridge_warning  # noqa: E402


class TestRunRealLoopBridgeFromWork(unittest.TestCase):
    def test_no_warning_for_strict_default_invocation(self) -> None:
        argv = ["run_real_loop_bridge_from_work.py", "--run-id", "RUN_X"]
        self.assertIsNone(_compatibility_recovery_bridge_warning(argv))

    def test_warning_for_compatibility_recovery_flag(self) -> None:
        argv = [
            "run_real_loop_bridge_from_work.py",
            "--run-id",
            "RUN_X",
            "--allow-reconstructed-artifacts",
        ]
        warning = _compatibility_recovery_bridge_warning(argv)
        self.assertIsNotNone(warning)
        self.assertIn("MANUAL_REVIEW_REQUIRED", str(warning))
        self.assertIn("prefer system_v3/tools/run_real_loop_recovery_bridge_from_work.py", str(warning))


if __name__ == "__main__":
    unittest.main()
