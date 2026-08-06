from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_external_validation.py"
SPEC = importlib.util.spec_from_file_location("external_validation_runner", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ExternalValidationRunnerTests(unittest.TestCase):
    def test_terminal_priority_is_fail_closed(self) -> None:
        self.assertEqual(MODULE._terminal_from_components("ELIGIBLE"), "ELIGIBLE")
        self.assertEqual(
            MODULE._terminal_from_components("ELIGIBLE", "PARKED"), "PARKED"
        )
        self.assertEqual(
            MODULE._terminal_from_components("PARKED", "BLOCKED"), "BLOCKED"
        )
        self.assertEqual(
            MODULE._terminal_from_components("BLOCKED", "HOLD"), "HOLD"
        )

    def test_invalid_lev_timeout_is_rejected_before_creating_run_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_root = Path(directory) / "new-run"
            with self.assertRaises(MODULE.ExternalValidationError):
                MODULE.run_external_validation(
                    request_id="external-validation-test",
                    run_root=run_root,
                    formal_runtime_dir=Path("/not-used-because-timeout-is-invalid"),
                    java_executable=Path("/not-used-because-timeout-is-invalid/java"),
                    lev_root=None,
                    subject_root=Path("/not-used-because-timeout-is-invalid"),
                    timeout_seconds=61,
                )
            self.assertFalse(run_root.exists())


if __name__ == "__main__":
    unittest.main()
