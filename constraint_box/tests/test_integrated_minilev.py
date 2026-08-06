from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from constraintbox.integrated_minilev import run_integrated_receipt_lease


class IntegratedMiniLevLeaseTests(unittest.TestCase):
    def test_receipt_bound_lease_and_expiry_control_use_the_real_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = run_integrated_receipt_lease(
                run_root=Path(temporary).resolve() / "lease-stage",
                request_id="integrated-lease-test",
                suite_receipt_sha256="a" * 64,
                smt_crosscheck_sha256="b" * 64,
            )

        self.assertEqual(result["disposition"], "ELIGIBLE")
        self.assertEqual(
            result["reason"],
            "receipt_bound_lease_released_and_expiry_control_held",
        )
        self.assertEqual(result["positive"]["terminal"], "RELEASED")
        self.assertTrue(
            result["positive"]["execution_lease"]["all_protected_events_released"]
        )
        self.assertTrue(result["positive"]["audit"]["handler_completed"])
        self.assertEqual(result["expiry_control"]["terminal"], "HOLD")
        self.assertFalse(
            result["expiry_control"]["execution_lease"][
                "all_protected_events_released"
            ]
        )
        self.assertEqual(
            result["expiry_control"]["audit"]["failure_stage"],
            "post_hook_verify",
        )
        self.assertTrue(result["expiry_control"]["audit"]["handler_completed"])


if __name__ == "__main__":
    unittest.main()
