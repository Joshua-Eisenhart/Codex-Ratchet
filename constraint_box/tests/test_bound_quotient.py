from __future__ import annotations

import json
import unittest
from pathlib import Path

from constraintbox.bound_quotient import decide_bound_packet
from constraintbox.distinguishability import decide_packet


BOX = Path(__file__).resolve().parents[1]
BOUND = BOX / "fixtures" / "bound_observation"
DIST = BOX / "fixtures" / "distinguishability"


def _load(directory: Path, name: str) -> dict:
    return json.loads((directory / name).read_text(encoding="utf-8"))


class BoundQuotientTests(unittest.TestCase):
    def test_split_rows_make_three_static_basins(self) -> None:
        receipt = decide_bound_packet(_load(BOUND, "bound_split.json"))
        self.assertEqual(receipt["status"], "PASS")
        self.assertTrue(receipt["quotient_admitted"])
        self.assertEqual(receipt["operation"], "bound_observation_quotient.v1")
        self.assertEqual(len(receipt["basins"]), 3)
        self.assertEqual(receipt["geometry"], "indistinguishability_relation")
        self.assertIn("attractor", receipt["not"])
        pairs = {(item["left"], item["right"]) for item in receipt["split"]}
        self.assertIn(("a", "b"), pairs)
        self.assertEqual(receipt["capacities"]["fibre"]["status"], "unearned")
        self.assertEqual(receipt["capacities"]["record"]["distinct_observation_tuples"], 3)

    def test_identical_rows_remain_fuzz(self) -> None:
        receipt = decide_bound_packet(_load(BOUND, "bound_fuzz.json"))
        self.assertEqual(receipt["status"], "PASS")
        self.assertEqual(receipt["fuzz"], [{"left": "a", "right": "b"}])
        self.assertEqual(receipt["split"], [])
        self.assertEqual(len(receipt["basins"]), 1)
        self.assertEqual(receipt["basins"][0]["members"], ["a", "b"])

    def test_missing_row_holds_without_a_quotient(self) -> None:
        receipt = decide_bound_packet(_load(BOUND, "bound_unbound.json"))
        self.assertEqual(receipt["status"], "HOLD")
        self.assertFalse(receipt["quotient_admitted"])
        self.assertEqual(receipt["reason"], "REFUSE_UNBOUND_OBSERVATION")
        self.assertIn("b/shape", receipt["missing_rows"])
        self.assertNotIn("basins", receipt)

    def test_solver_feasibility_does_not_admit_a_quotient(self) -> None:
        receipt = decide_packet(_load(DIST, "positive_distinguish.json"))
        self.assertEqual(receipt["status"], "BOUNDED_SAT")
        self.assertEqual(receipt["witness_kind"], "solver_chosen")
        self.assertFalse(receipt["quotient_admitted"])


if __name__ == "__main__":
    unittest.main()
