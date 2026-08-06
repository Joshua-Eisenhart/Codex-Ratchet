"""Regression and demonstration tests for the solver-backed can-fail decider."""

from __future__ import annotations

import unittest

import z3

from claimgate_plugin.canfail_smt import (
    CAN_FAIL,
    CONTRADICTION,
    TAUTOLOGY,
    UNKNOWN,
    analyze_canfail,
)


class CanFailSmtTests(unittest.TestCase):
    def test_disguised_tautologies_and_real_check(self) -> None:
        x = z3.Int("x")
        p = z3.Bool("p")
        unused = z3.Int("declared_but_unused")
        demo_cases = [
            ("1. x == x", x == x, (x,)),
            ("2. x >= x", x >= x, (x,)),
            ("3. Or(p, Not(p))", z3.Or(p, z3.Not(p)), (p,)),
            ("4. Implies(p, p)", z3.Implies(p, p), (p,)),
            ("5. x + 0 == x", x + 0 == x, (x,)),
            ("6. 2*x == x + x", 2 * x == x + x, (x,)),
            ("7. Or(x < 5, x >= 5)", z3.Or(x < 5, x >= 5), (x,)),
            (
                "8. declared-but-unused variable",
                x == x,
                (x, unused),
            ),
        ]

        total_seconds = 0.0
        for name, check, variables in demo_cases:
            with self.subTest(name=name):
                result = analyze_canfail(check, variables)
                total_seconds += result.elapsed_seconds
                print(
                    f"{name}: verdict={result.verdict} "
                    f"cost_seconds={result.elapsed_seconds:.9f}"
                )
                self.assertEqual(TAUTOLOGY, result.verdict)
                self.assertIsNone(result.model)
                self.assertIsNone(result.witness)

        real_check = z3.And(x >= 0, x <= 10)
        real_result = analyze_canfail(real_check, (x,))
        total_seconds += real_result.elapsed_seconds
        print(
            "REAL. 0 <= x <= 10: "
            f"verdict={real_result.verdict} "
            f"witness={real_result.witness} "
            f"cost_seconds={real_result.elapsed_seconds:.9f}"
        )
        print(f"DEMO TOTAL: cost_seconds={total_seconds:.9f}")

        self.assertEqual(CAN_FAIL, real_result.verdict)
        self.assertIsNotNone(real_result.model)
        self.assertIsNotNone(real_result.witness)
        self.assertIn("x", real_result.witness)
        self.assertTrue(
            z3.is_false(
                real_result.model.eval(real_check, model_completion=True)
            )
        )

    def test_contradiction_is_separate_from_can_fail(self) -> None:
        x = z3.Int("contradiction_x")
        result = analyze_canfail(z3.And(x < 0, x >= 0), (x,))
        self.assertEqual(CONTRADICTION, result.verdict)
        self.assertIsNone(result.model)
        self.assertIsNone(result.witness)

    def test_unknown_is_not_folded_into_a_proof_verdict(self) -> None:
        x = z3.Real("unknown_x")
        result = analyze_canfail(x**x == 2, (x,))
        self.assertEqual(UNKNOWN, result.verdict)
        self.assertIsNone(result.model)
        self.assertIsNone(result.witness)
        self.assertIsNotNone(result.unknown_reason)

    def test_undeclared_free_variable_is_rejected(self) -> None:
        x = z3.Int("declared_x")
        y = z3.Int("undeclared_y")
        with self.assertRaisesRegex(ValueError, "undeclared variables"):
            analyze_canfail(x < y, (x,))

    def test_ambiguous_witness_names_are_rejected(self) -> None:
        integer = z3.Int("same_name")
        boolean = z3.Bool("same_name")
        check = z3.And(integer >= 0, boolean)
        with self.assertRaisesRegex(ValueError, "distinct rendered names"):
            analyze_canfail(check, (integer, boolean))


if __name__ == "__main__":
    unittest.main()
