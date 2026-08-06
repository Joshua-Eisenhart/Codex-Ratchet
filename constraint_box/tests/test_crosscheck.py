from __future__ import annotations

import dataclasses
import unittest
from unittest import mock

import constraintbox.crosscheck as crosscheck_module
from constraintbox.crosscheck import cross_check


def _finite_sat_claim() -> dict[str, object]:
    return {
        "variables": {"x": [0, 1], "y": [0, 1]},
        "constraints": [
            {
                "op": "neq",
                "left": {"var": "x"},
                "right": {"var": "y"},
            }
        ],
    }


def _floor_spec(
    domain: list[object],
    *,
    value: object | None = None,
    op: str = "ge",
) -> dict[str, object]:
    constraints = []
    if value is not None:
        constraints.append(
            {
                "op": op,
                "left": {"var": "x"},
                "right": {"const": value},
            }
        )
    return {"variables": {"x": domain}, "constraints": constraints}


class CrossCheckTests(unittest.TestCase):
    def test_finite_constraint_deciders_all_decide_and_agree(self) -> None:
        result = cross_check(
            "finite_constraint_satisfiability", _finite_sat_claim()
        )

        self.assertEqual(result.agreement, "AGREE")
        self.assertEqual(result.reason, "")
        self.assertEqual(
            tuple(outcome.decider for outcome in result.outcomes),
            ("enumeration", "z3", "cvc5"),
        )
        self.assertTrue(
            all(outcome.status == "DECIDED" for outcome in result.outcomes)
        )
        self.assertEqual(
            {outcome.raw_verdict for outcome in result.outcomes},
            {"BOUNDED_SAT"},
        )
        self.assertEqual(
            {outcome.normal_verdict for outcome in result.outcomes},
            {"SAT"},
        )

    def test_ratchet_floor_disagreement_is_unresolved(self) -> None:
        result = cross_check(
            "ratchet_floor_transition",
            {
                "current": _floor_spec(
                    [0.9999999999995, 1.0, 1.5], value=1.0
                ),
                "next": _floor_spec(
                    [0.9999999999995, 1.0, 1.5],
                    value=0.9999999999995,
                ),
            },
        )

        self.assertEqual(result.agreement, "UNRESOLVED")
        self.assertEqual(len(result.outcomes), 2)
        self.assertEqual(
            {
                outcome.decider: (
                    outcome.status,
                    outcome.raw_verdict,
                    outcome.normal_verdict,
                )
                for outcome in result.outcomes
            },
            {
                "scalar": (
                    "DECIDED",
                    "ADMITTED",
                    "FLOOR_MOVES_OR_HOLDS",
                ),
                "smt": ("DECIDED", "WEAKENED", "FLOOR_BLOCKED"),
            },
        )

    def test_raising_decider_is_preserved_and_forces_unresolved(self) -> None:
        with mock.patch.object(
            crosscheck_module,
            "_run_z3",
            side_effect=RuntimeError("injected z3 failure"),
        ):
            result = cross_check(
                "finite_constraint_satisfiability", _finite_sat_claim()
            )

        z3_outcome = next(
            outcome for outcome in result.outcomes if outcome.decider == "z3"
        )
        self.assertEqual(result.agreement, "UNRESOLVED")
        self.assertEqual(len(result.outcomes), 3)
        self.assertEqual(z3_outcome.status, "ERRORED")
        self.assertIsNone(z3_outcome.raw_verdict)
        self.assertIsNone(z3_outcome.normal_verdict)
        self.assertEqual(z3_outcome.detail, "injected z3 failure")

    def test_parked_is_unmapped_and_keeps_raw_verdict(self) -> None:
        result = cross_check(
            "ratchet_floor_transition",
            {
                "current": _floor_spec([0, 1, 2]),
                "next": _floor_spec([0, 1, 2], value=1),
            },
        )

        scalar = next(
            outcome for outcome in result.outcomes if outcome.decider == "scalar"
        )
        self.assertEqual(result.agreement, "UNRESOLVED")
        self.assertEqual(scalar.status, "UNMAPPED")
        self.assertEqual(scalar.raw_verdict, "PARKED")
        self.assertIsNone(scalar.normal_verdict)
        self.assertEqual(scalar.detail, "exit_code=3")

    def test_result_has_no_winner_and_keeps_every_outcome(self) -> None:
        result = cross_check(
            "ratchet_floor_transition",
            {
                "current": _floor_spec([0, 1, 2], value=1),
                "next": _floor_spec([0, 1, 2], value=2),
            },
        )

        field_names = {field.name for field in dataclasses.fields(result)}
        self.assertTrue(
            field_names.isdisjoint({"winner", "preferred", "trusted"})
        )
        self.assertFalse(hasattr(result, "winner"))
        self.assertFalse(hasattr(result, "preferred"))
        self.assertFalse(hasattr(result, "trusted"))
        self.assertEqual(
            tuple(outcome.decider for outcome in result.outcomes),
            ("scalar", "smt"),
        )


if __name__ == "__main__":
    unittest.main()
