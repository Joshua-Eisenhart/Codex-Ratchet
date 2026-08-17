from __future__ import annotations

import json
import unittest
from pathlib import Path

from constraintbox.manifold_foundation import (
    ManifoldFoundationError,
    validate_foundation,
    validate_foundation_file,
)


FIXTURE = Path(__file__).parents[1] / "fixtures" / "cr" / "manifold_time_first_seed_v1.json"


class ManifoldFoundationTests(unittest.TestCase):
    def test_time_first_seed_is_finite_and_ordered(self) -> None:
        receipt = validate_foundation_file(FIXTURE)
        self.assertEqual(receipt["status"], "PASS")
        self.assertTrue(receipt["checks"]["finite_first"])
        self.assertTrue(receipt["checks"]["positive_capacity_gradient"])
        self.assertTrue(receipt["checks"]["dual_order_gap"])
        self.assertEqual(receipt["checks"]["layer_ids"][0], "C0_finitude")
        self.assertEqual(receipt["operation"], "finite_time_first_seed_validation.v1")
        self.assertEqual(receipt["checks"]["capacity_bits_recomputed"], [1.0, 2.0, 3.0])
        self.assertEqual(receipt["surface"]["static_supports"][0]["W"], 2)
        capacities = receipt["surface"]["capacities"]
        self.assertEqual(capacities["support"]["K"], [1.0, 2.0, 3.0])
        self.assertEqual(capacities["fibre"]["status"], "unearned")
        self.assertEqual(capacities["record"]["status"], "unearned")
        self.assertIs(capacities["summed"], False)
        self.assertFalse(receipt["promotion_allowed"])

    def test_scalar_zero_is_not_admitted_as_typed_boundary(self) -> None:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["carrier"]["zero_object"]["scalar_zero"] = True
        with self.assertRaises(ManifoldFoundationError):
            validate_foundation(payload)

    def test_finitude_must_be_first(self) -> None:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["layers"][0]["id"] = "C1_time_opening_binding"
        with self.assertRaises(ManifoldFoundationError):
            validate_foundation(payload)

    def test_capacity_delta_mismatch_is_refused(self) -> None:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["time"]["delta_capacity_bits"][0] = 2.0
        with self.assertRaises(ManifoldFoundationError) as caught:
            validate_foundation(payload)
        self.assertIn("REFUSE_CAPACITY_MISMATCH", str(caught.exception))

    def test_collapsed_orders_are_refused(self) -> None:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["dual_engines"]["right_output"] = payload["dual_engines"]["left_output"]
        with self.assertRaises(ManifoldFoundationError) as caught:
            validate_foundation(payload)
        self.assertIn("REFUSE_ORDER_GAP_COLLAPSED", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
