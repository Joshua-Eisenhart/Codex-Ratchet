from __future__ import annotations

import unittest

from constraintbox.crosscheck import cross_check
from constraintbox.integrated_workload import (
    _erased_obligation,
    _finite_obligation,
    _suite_facts,
)


def _suite_component(name: str, disposition: str) -> dict:
    return {
        "capability_id": name,
        "state": disposition,
        "result": {"disposition": disposition},
        "independent_replay": {"disposition": disposition},
        "result_sha256": "a" * 64,
        "independent_replay_sha256": "b" * 64,
    }


class IntegratedWorkloadSolverBindingTests(unittest.TestCase):
    def test_actual_component_state_drives_all_three_solver_outcomes(self) -> None:
        receipt = {
            "schema": "constraintbox.capability-suite-receipt.v1",
            "components": [
                _suite_component("alpha", "ELIGIBLE"),
                _suite_component("beta", "ELIGIBLE"),
            ],
        }
        variables, observations = _suite_facts(receipt)
        self.assertEqual(
            [row["eligible_from_receipt"] for row in observations],
            [True, True],
        )
        real = cross_check(
            "finite_constraint_satisfiability", _finite_obligation(variables)
        )
        erased = cross_check(
            "finite_constraint_satisfiability", _erased_obligation(variables)
        )
        self.assertEqual(real.agreement, "AGREE")
        self.assertEqual(
            [row.normal_verdict for row in real.outcomes],
            ["SAT", "SAT", "SAT"],
        )
        self.assertEqual(erased.agreement, "AGREE")
        self.assertEqual(
            [row.normal_verdict for row in erased.outcomes],
            ["UNSAT", "UNSAT", "UNSAT"],
        )

    def test_noneligible_component_cannot_be_laundered_into_a_sat_gate(self) -> None:
        receipt = {
            "schema": "constraintbox.capability-suite-receipt.v1",
            "components": [
                _suite_component("alpha", "ELIGIBLE"),
                _suite_component("beta", "BLOCKED"),
            ],
        }
        variables, observations = _suite_facts(receipt)
        self.assertEqual(
            [row["eligible_from_receipt"] for row in observations],
            [True, False],
        )
        result = cross_check(
            "finite_constraint_satisfiability", _finite_obligation(variables)
        )
        self.assertEqual(result.agreement, "AGREE")
        self.assertEqual(
            [row.normal_verdict for row in result.outcomes],
            ["UNSAT", "UNSAT", "UNSAT"],
        )


if __name__ == "__main__":
    unittest.main()
