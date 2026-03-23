from __future__ import annotations

import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BASE / "tools"))

from run_bridge_determinism_pair import (  # noqa: E402
    _manual_review_details,
    _manual_review_required,
    _pair_status,
)


class TestRunBridgeDeterminismPair(unittest.TestCase):
    def test_manual_review_required_detects_controller_signal(self) -> None:
        self.assertTrue(_manual_review_required({"controller_review_required": True}))
        self.assertFalse(_manual_review_required({"controller_review_required": False}))
        self.assertFalse(_manual_review_required({}))

    def test_manual_review_details_preserves_decision_and_reason(self) -> None:
        self.assertEqual(
            {
                "required": True,
                "decision": "MANUAL_REVIEW_REQUIRED",
                "reason": "compatibility_recovery_path_used",
            },
            _manual_review_details(
                {
                    "controller_review_required": True,
                    "controller_review_decision": "MANUAL_REVIEW_REQUIRED",
                    "controller_review_reason": "compatibility_recovery_path_used",
                }
            ),
        )
        self.assertEqual(
            {
                "required": False,
                "decision": None,
                "reason": None,
            },
            _manual_review_details({}),
        )

    def test_pair_status_fails_when_manual_review_is_required(self) -> None:
        self.assertEqual(
            "FAIL",
            _pair_status(
                rc_a=0,
                rc_b=0,
                same_state_hash=True,
                same_counts=True,
                same_event_hash_norm=True,
                manual_review_required=True,
            ),
        )

    def test_pair_status_passes_only_when_runs_match_and_no_review_is_required(self) -> None:
        self.assertEqual(
            "PASS",
            _pair_status(
                rc_a=0,
                rc_b=0,
                same_state_hash=True,
                same_counts=True,
                same_event_hash_norm=True,
                manual_review_required=False,
            ),
        )


if __name__ == "__main__":
    unittest.main()
