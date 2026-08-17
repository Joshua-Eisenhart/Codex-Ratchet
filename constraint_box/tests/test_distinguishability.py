from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from constraintbox.distinguishability import (
    PACKET_SCHEMA,
    compile_packet,
    decide_packet,
    obs_var,
)


BOX_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = BOX_ROOT / "fixtures" / "distinguishability"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class DistinguishabilityStage1Test(unittest.TestCase):
    def test_positive_distinguish_is_sat_with_a_witness(self) -> None:
        receipt = decide_packet(_load("positive_distinguish.json"))
        self.assertEqual(receipt["status"], "BOUNDED_SAT")
        self.assertTrue(receipt["dual_solve"]["agree"])
        witnesses = receipt["dual_solve"]["witnesses"]
        self.assertIn("enumeration", witnesses)
        witness = witnesses["enumeration"]
        differs = any(
            witness[obs_var(probe, "a")] != witness[obs_var(probe, "b")]
            for probe in ("color", "shape")
        )
        self.assertTrue(differs)
        self.assertTrue(all(item["holds"] for item in receipt["witness_checks"]))
        self.assertEqual(receipt["cores"], {})

    def test_negative_control_indistinguishable_is_sat(self) -> None:
        receipt = decide_packet(_load("negative_control_indistinguishable.json"))
        self.assertEqual(receipt["status"], "BOUNDED_SAT")
        self.assertTrue(receipt["dual_solve"]["agree"])
        witness = receipt["dual_solve"]["witnesses"]["enumeration"]
        self.assertEqual(witness[obs_var("color", "a")], witness[obs_var("color", "b")])
        self.assertEqual(witness[obs_var("shape", "a")], witness[obs_var("shape", "b")])

    def test_collapsed_demand_is_unsat_and_cores_name_demand(self) -> None:
        receipt = decide_packet(_load("collapsed_demand.json"))
        self.assertEqual(receipt["status"], "BOUNDED_UNSAT")
        self.assertTrue(receipt["dual_solve"]["agree"])
        deletion = receipt["cores"]["deletion"]
        self.assertIn("demand:a_b", deletion)
        self.assertTrue(any(name.startswith("C:eq_") for name in deletion))
        z3_core = receipt["cores"]["z3"]
        self.assertEqual(z3_core["status"], "BOUNDED_UNSAT")
        self.assertIn("demand:a_b", z3_core["core"])
        cvc5_core = receipt["cores"]["cvc5"]
        self.assertEqual(cvc5_core["status"], "BOUNDED_UNSAT")
        self.assertIn("demand:a_b", cvc5_core["core"])

    def test_nonfinite_theory_holds_without_a_solver_verdict(self) -> None:
        receipt = decide_packet(_load("nonfinite_hold.json"))
        self.assertEqual(receipt["status"], "HOLD")
        self.assertEqual(receipt["reason"], "theory_not_finite")
        self.assertNotIn("dual_solve", receipt)

    def test_compile_assigns_assumption_literals(self) -> None:
        _packet, spec, named = compile_packet(_load("collapsed_demand.json"))
        ids = [name for name, _constraint in named]
        self.assertEqual(
            ids,
            ["demand:a_b", "C:eq_color", "C:eq_shape"],
        )
        self.assertEqual(set(spec["variables"]), {
            "obs__color__a",
            "obs__color__b",
            "obs__shape__a",
            "obs__shape__b",
        })

    def test_packet_schema_is_the_stage1_contract(self) -> None:
        packet = _load("positive_distinguish.json")
        self.assertEqual(packet["schema"], PACKET_SCHEMA)
        self.assertEqual(packet["authority"], "none")

    def test_receipt_records_the_process_that_ran(self) -> None:
        receipt = decide_packet(_load("positive_distinguish.json"))
        self.assertEqual(receipt["interpreter"], sys.executable)
        self.assertEqual(
            receipt["operation"], "finite_probe_assignment_feasibility.v1"
        )
        self.assertEqual(receipt["claim_ceiling"], "exists")
        self.assertIn("z3", receipt["solver_versions"])
        self.assertIn("cvc5", receipt["solver_versions"])
        self.assertTrue(receipt["receipt_sha256"])


if __name__ == "__main__":
    unittest.main()
