from __future__ import annotations

import importlib
import unittest
from typing import Any
from unittest.mock import patch

import cvc5
import z3

from constraintbox.clause_feedback import (
    ClauseFeedbackError,
    ClauseFeedbackUnavailable,
    build_clause_feedback,
)


def questions(names: tuple[str, ...]) -> dict[str, str]:
    return {name: f"What explicit value satisfies {name}?" for name in names}


def run_feedback(values: dict[str, bool]) -> dict[str, Any]:
    order = tuple(values)
    failed = tuple(name for name in order if not values[name])
    return build_clause_feedback(
        values,
        clause_order=order,
        retry_questions=questions(order),
        reference_failed=failed,
    )


class ClauseFeedbackTests(unittest.TestCase):
    def test_all_true_has_no_failed_core_and_is_deterministic(self) -> None:
        values = {"goal_explicit": True, "scope_explicit": True}

        first = run_feedback(values)
        second = run_feedback(values)

        self.assertEqual(first, second)
        self.assertTrue(first["agree"])
        self.assertEqual(first["reference_failed_clauses"], [])
        self.assertEqual(first["retry_feedback"], [])
        self.assertEqual(len(first["result_sha256"]), 64)
        self.assertEqual(
            first["tool_versions"],
            {
                "expected": {
                    "z3": [4, 16, 0, 0],
                    "cvc5": "1.3.3",
                },
                "observed": {
                    "z3": [4, 16, 0, 0],
                    "cvc5": "1.3.3",
                },
            },
        )
        self.assertEqual(
            first["per_solver"]["z3"]["summary_status"],
            "ALL_CLAUSES_SATISFIED",
        )
        self.assertEqual(
            first["per_solver"]["cvc5"]["summary_status"],
            "ALL_CLAUSES_SATISFIED",
        )
        self.assertTrue(
            all(
                check["status"] == "SAT"
                and check["unsat_core"] == []
                for solver in first["per_solver"].values()
                for check in solver["checks"]
            )
        )

    def test_one_failed_clause_has_matching_singleton_cores(self) -> None:
        result = run_feedback(
            {
                "goal_explicit": True,
                "scope_explicit": False,
                "evidence_explicit": True,
            }
        )

        self.assertEqual(
            result["reference_failed_clauses"], ["scope_explicit"]
        )
        for backend in ("z3", "cvc5"):
            solver = result["per_solver"][backend]
            self.assertEqual(solver["failed_clauses"], ["scope_explicit"])
            failed_check = next(
                check
                for check in solver["checks"]
                if check["clause"] == "scope_explicit"
            )
            self.assertEqual(failed_check["status"], "UNSAT")
            self.assertEqual(
                failed_check["unsat_core"],
                [failed_check["assumption_literal"]],
            )
        self.assertEqual(
            result["retry_feedback"],
            [
                {
                    "clause": "scope_explicit",
                    "question": (
                        "What explicit value satisfies scope_explicit?"
                    ),
                    "minimal_failed_assumption": (
                        "cb_requirement_1_scope_explicit"
                    ),
                }
            ],
        )

    def test_multiple_failed_clauses_are_all_reported_in_input_order(self) -> None:
        result = run_feedback(
            {
                "goal_explicit": False,
                "scope_explicit": True,
                "evidence_explicit": False,
                "actions_explicit": False,
            }
        )

        expected = [
            "goal_explicit",
            "evidence_explicit",
            "actions_explicit",
        ]
        self.assertEqual(result["reference_failed_clauses"], expected)
        self.assertEqual(
            result["per_solver"]["z3"]["failed_clauses"], expected
        )
        self.assertEqual(
            result["per_solver"]["cvc5"]["failed_clauses"], expected
        )
        self.assertEqual(
            [row["clause"] for row in result["retry_feedback"]],
            expected,
        )

    def test_all_false_at_hard_clause_boundary(self) -> None:
        values = {
            f"clause_{index:02d}": False
            for index in range(64)
        }

        result = run_feedback(values)

        expected = list(values)
        self.assertEqual(result["reference_failed_clauses"], expected)
        self.assertEqual(
            result["per_solver"]["z3"]["failed_clauses"], expected
        )
        self.assertEqual(
            result["per_solver"]["cvc5"]["failed_clauses"], expected
        )
        self.assertEqual(len(result["retry_feedback"]), 64)

    def test_clause_count_above_hard_boundary_is_rejected_before_tools(self) -> None:
        values = {
            f"clause_{index:02d}": True
            for index in range(65)
        }
        order = tuple(values)

        with patch(
            "constraintbox.clause_feedback.importlib.import_module"
        ) as import_module:
            with self.assertRaisesRegex(
                ClauseFeedbackError,
                "clause_feedback_controller_contract_invalid",
            ):
                build_clause_feedback(
                    values,
                    clause_order=order,
                    retry_questions=questions(order),
                    reference_failed=(),
                )

        import_module.assert_not_called()

    def test_missing_required_solver_propagates_import_error(self) -> None:
        values = {"goal_explicit": True}
        original_import = importlib.import_module

        def missing_z3(name: str) -> Any:
            if name == "z3":
                raise ModuleNotFoundError(
                    "forced missing z3",
                    name="z3",
                )
            return original_import(name)

        with patch(
            "constraintbox.clause_feedback.importlib.import_module",
            side_effect=missing_z3,
        ):
            with self.assertRaisesRegex(
                ClauseFeedbackUnavailable,
                "forced missing z3",
            ):
                run_feedback(values)

    def test_broken_solver_import_is_evaluation_error_not_unavailable(
        self,
    ) -> None:
        with patch(
            "constraintbox.clause_feedback.importlib.import_module",
            side_effect=ImportError("forced broken installed module"),
        ):
            with self.assertRaises(ClauseFeedbackError) as caught:
                run_feedback({"goal_explicit": True})

        self.assertEqual(caught.exception.reason, "z3_import_failed")
        self.assertEqual(caught.exception.evidence["backend"], "z3")

    def test_z3_version_drift_is_evaluation_error_before_operations(
        self,
    ) -> None:
        with (
            patch.object(z3, "get_version", return_value=(4, 16, 1, 0)),
            patch(
                "constraintbox.clause_feedback._run_z3_feedback"
            ) as run_z3,
        ):
            with self.assertRaises(ClauseFeedbackError) as caught:
                run_feedback({"goal_explicit": True})

        self.assertEqual(
            caught.exception.reason,
            "clause_feedback_version_drift",
        )
        self.assertEqual(
            caught.exception.evidence["tool_versions"],
            {
                "expected": {
                    "z3": [4, 16, 0, 0],
                    "cvc5": "1.3.3",
                },
                "observed": {
                    "z3": [4, 16, 1, 0],
                    "cvc5": "1.3.3",
                },
            },
        )
        self.assertEqual(
            caught.exception.evidence["drifted_backends"],
            ["z3"],
        )
        run_z3.assert_not_called()

    def test_cvc5_version_drift_is_evaluation_error_before_operations(
        self,
    ) -> None:
        with (
            patch.object(cvc5, "__version__", "1.3.4"),
            patch(
                "constraintbox.clause_feedback._run_z3_feedback"
            ) as run_z3,
        ):
            with self.assertRaises(ClauseFeedbackError) as caught:
                run_feedback({"goal_explicit": True})

        self.assertEqual(
            caught.exception.reason,
            "clause_feedback_version_drift",
        )
        self.assertEqual(
            caught.exception.evidence["tool_versions"]["observed"]["cvc5"],
            "1.3.4",
        )
        self.assertEqual(
            caught.exception.evidence["drifted_backends"],
            ["cvc5"],
        )
        run_z3.assert_not_called()

    def test_version_probe_failure_is_evaluation_error(self) -> None:
        with patch.object(
            z3,
            "get_version",
            side_effect=RuntimeError("forced version probe failure"),
        ):
            with self.assertRaises(ClauseFeedbackError) as caught:
                run_feedback({"goal_explicit": True})

        self.assertEqual(
            caught.exception.reason,
            "clause_feedback_version_probe_failed",
        )
        self.assertEqual(
            caught.exception.evidence["tool_versions"]["expected"]["z3"],
            [4, 16, 0, 0],
        )
        self.assertIsNone(
            caught.exception.evidence["tool_versions"]["observed"]["z3"]
        )
        self.assertIn(
            "forced version probe failure",
            caught.exception.evidence["error"],
        )

    def test_z3_unsat_core_api_severance_is_evaluation_error(self) -> None:
        with patch.object(
            z3.Solver,
            "unsat_core",
            side_effect=RuntimeError("forced unsat_core severance"),
        ):
            with self.assertRaises(ClauseFeedbackError) as caught:
                run_feedback({"goal_explicit": False})

        self.assertEqual(
            caught.exception.reason,
            "z3_clause_feedback_execution_failed",
        )
        self.assertEqual(caught.exception.evidence["backend"], "z3")
        self.assertIn(
            "forced unsat_core severance",
            caught.exception.evidence["error"],
        )

    def test_cvc5_unsat_assumption_api_severance_is_evaluation_error(
        self,
    ) -> None:
        class SeveredSolver:
            def __init__(self) -> None:
                self._solver = cvc5.Solver()

            def __getattr__(self, name: str) -> Any:
                return getattr(self._solver, name)

            def getUnsatAssumptions(self) -> Any:
                raise RuntimeError("forced getUnsatAssumptions severance")

        with patch(
            "constraintbox.clause_feedback._new_cvc5_solver",
            side_effect=lambda module: SeveredSolver(),
        ):
            with self.assertRaises(ClauseFeedbackError) as caught:
                run_feedback({"goal_explicit": False})

        self.assertEqual(
            caught.exception.reason,
            "cvc5_clause_feedback_execution_failed",
        )
        self.assertEqual(caught.exception.evidence["backend"], "cvc5")
        self.assertIn(
            "forced getUnsatAssumptions severance",
            caught.exception.evidence["error"],
        )

    def test_mutated_solver_failed_set_is_crosscheck_disagreement(self) -> None:
        mutated = {
            "api": "mutated",
            "summary_status": "ALL_CLAUSES_SATISFIED",
            "failed_clauses": [],
            "checks": [],
        }
        with patch(
            "constraintbox.clause_feedback._run_z3_feedback",
            return_value=mutated,
        ):
            with self.assertRaises(ClauseFeedbackError) as caught:
                run_feedback({"goal_explicit": False})

        self.assertEqual(
            caught.exception.reason,
            "clause_feedback_crosscheck_disagreement",
        )
        self.assertEqual(
            caught.exception.evidence["mismatch"],
            {
                "reference": ["goal_explicit"],
                "z3": [],
                "cvc5": ["goal_explicit"],
            },
        )


if __name__ == "__main__":
    unittest.main()
