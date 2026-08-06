"""Contained-core checks for the failure-repair admission boundary.

These tests deliberately require no external simulation estate.  The broader
fault-injected controller-flow test remains in ``test_failure_repair.py`` and
runs only where that separate estate is actually present.
"""

from __future__ import annotations

import unittest

from constraintbox.failure_repair import (
    FailureRepairError,
    _selected_action,
    build_repair_plan_from_capability_result,
)


def _synthetic_nonpass_result() -> dict[str, object]:
    return {
        "schema": "constraintbox.external-capability-flow-result.v1",
        "capability_id": "synthetic-not-controller-issued-v1",
        "request_id": "contained-synthetic-1",
        "request_sha256": "1" * 64,
        "run_id": "contained-synthetic-run-1",
        "flow_policy_sha256": "2" * 64,
        "disposition": "BLOCKED",
        "reason": "exact_operation_controls_failed",
        "capability_receipt_sha256": "3" * 64,
        "flow_receipt_sha256": "4" * 64,
        "artifacts": {
            "capability_receipt": "/tmp/not-used-capability-receipt.json",
            "flow_receipt": "/tmp/not-used-flow-receipt.json",
            "flow_ledger": "/tmp/not-used-flow-ledger.jsonl",
            "flow_ledger_head": "/tmp/not-used-flow-ledger.jsonl.head",
        },
        "external_system": True,
        "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
        "release_allowed": False,
        "engine_readiness_claim": False,
        "cr_truth_claim": False,
        "promotion_allowed": False,
        "claim_ceiling": "synthetic contained-core refusal fixture only",
    }


class ContainedFailureRepairTests(unittest.TestCase):
    def test_synthetic_result_cannot_select_a_repair_action(self) -> None:
        with self.assertRaisesRegex(
            FailureRepairError, "capability id is not controller-registered"
        ):
            build_repair_plan_from_capability_result(_synthetic_nonpass_result())

    def test_unknown_reason_has_only_the_park_default(self) -> None:
        self.assertEqual(
            _selected_action("PARKED", "future_unmapped_failure"),
            ("park", "controller_mapping_unmatched_default_park"),
        )


if __name__ == "__main__":
    unittest.main()
