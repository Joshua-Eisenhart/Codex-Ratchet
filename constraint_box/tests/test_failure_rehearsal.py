from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from constraintbox.failure_rehearsal import (
    FailureRehearsalError,
    REHEARSAL_RECEIPT_NAME,
    run_scipy_replay_severance_rehearsal,
    verify_scipy_replay_severance_rehearsal,
)
from constraintbox.intake import parse_json_object
from constraintbox.external_bounded_numerics_flow_core import (
    ExternalBoundedNumericsFlowError,
)
from constraintbox.external_scipy_capability_flow import (
    controller_replay_severance_rehearsal_scope,
)


class FailureRehearsalTests(unittest.TestCase):
    """The retained failure route uses real workers, never a test patch."""

    def test_fixed_scipy_replay_severance_is_retained_and_fresh_rerun_is_clean(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as directory:
            root = Path(directory).resolve() / "fixed-scipy-rehearsal"
            receipt = run_scipy_replay_severance_rehearsal(run_root=root)

            self.assertTrue((root / REHEARSAL_RECEIPT_NAME).is_file())
            persisted = parse_json_object((root / REHEARSAL_RECEIPT_NAME).read_bytes())
            self.assertEqual(persisted, receipt)
            verified = verify_scipy_replay_severance_rehearsal(
                receipt,
                expected_run_root=root,
            )
            self.assertEqual(verified["receipt"], receipt)
            self.assertEqual(receipt["failure"]["disposition"], "BLOCKED")
            self.assertEqual(
                receipt["failure"]["reason"],
                "controller_recomputed_check_failed",
            )
            self.assertEqual(receipt["failure"]["normal_worker_returncode"], 0)
            self.assertEqual(receipt["failure"]["replay_worker_returncode"], 86)
            self.assertEqual(receipt["failure"]["severance_worker_returncode"], 86)
            self.assertFalse(receipt["failure"]["replay_control_passed"])
            self.assertTrue(receipt["failure"]["severance_control_passed"])
            self.assertEqual(receipt["fresh_rerun"]["rerun_disposition"], "ELIGIBLE")
            self.assertEqual(receipt["fresh_rerun"]["outcome_disposition"], "PARKED")
            self.assertTrue(receipt["fresh_rerun"]["independent_fresh_python_replay"])
            self.assertFalse(receipt["promotion_allowed"])
            self.assertFalse(receipt["controller_injection"]["llm_decision_authority"])

            with self.assertRaises(FailureRehearsalError):
                run_scipy_replay_severance_rehearsal(run_root=root)

    def test_nested_rehearsal_scope_is_refused_before_a_run_root_exists(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as directory:
            root = Path(directory).resolve() / "nested-scipy-rehearsal"
            with controller_replay_severance_rehearsal_scope():
                with self.assertRaisesRegex(
                    ExternalBoundedNumericsFlowError,
                    "cannot be nested",
                ):
                    run_scipy_replay_severance_rehearsal(run_root=root)
            self.assertFalse(root.exists())
