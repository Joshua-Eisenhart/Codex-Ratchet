from __future__ import annotations

import builtins
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import ANY, patch

from constraintbox.constraints import SolverResult, SolverStatus
from constraintbox.dualsolve import dual_solve, run_differential


BOX_ROOT = Path(__file__).resolve().parents[1]


class DualSolveAgreementTest(unittest.TestCase):
    @staticmethod
    def _import_fault(
        target: str,
        error: BaseException,
    ):
        original_import = builtins.__import__

        def import_with_fault(name, *args, **kwargs):
            if name == target:
                raise error
            return original_import(name, *args, **kwargs)

        return import_with_fault

    def test_all_three_agree_sat(self) -> None:
        spec = {
            "variables": {"x": [1, 2], "y": [2, 3]},
            "constraints": [
                {
                    "op": "eq",
                    "left": {"var": "x"},
                    "right": {"var": "y"},
                }
            ],
        }
        result = dual_solve(spec)
        self.assertEqual(result["z3"], "BOUNDED_SAT")
        self.assertEqual(result["cvc5"], "BOUNDED_SAT")
        self.assertEqual(result["enumeration"], "BOUNDED_SAT")
        self.assertTrue(result["all_definite"])
        self.assertTrue(result["agree"])
        self.assertEqual(
            result["backend_roles"]["enumeration"],
            "internal_bounded_reference_checker",
        )

    def test_cvc5_solver_process_exits_cleanly_after_a_real_solve(self) -> None:
        """Catch native-binding teardown faults hidden by an in-process result."""

        command = [sys.executable]
        if sys.flags.optimize:
            command.append("-O")
        command.extend(
            [
                "-c",
                (
                    "from constraintbox.dualsolve import dual_solve; "
                    "spec={'variables': {'x': [False, True]}, "
                    "'constraints': [{'op': 'eq', 'left': {'var': 'x'}, "
                    "'right': {'const': True}}]}; "
                    "print(dual_solve(spec, max_states=2)['cvc5'])"
                ),
            ]
        )
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(BOX_ROOT / "src")
        completed = subprocess.run(
            command,
            cwd=BOX_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        self.assertEqual(
            completed.returncode,
            0,
            msg=(
                "cvc5 solver process did not exit cleanly; "
                f"stdout={completed.stdout!r}; stderr={completed.stderr!r}"
            ),
        )
        self.assertEqual(completed.stdout.strip(), "BOUNDED_SAT")

    def test_all_three_agree_unsat(self) -> None:
        spec = {
            "variables": {"x": [1], "y": [2]},
            "constraints": [
                {
                    "op": "eq",
                    "left": {"var": "x"},
                    "right": {"var": "y"},
                }
            ],
        }
        result = dual_solve(spec)
        self.assertEqual(result["z3"], "BOUNDED_UNSAT")
        self.assertEqual(result["cvc5"], "BOUNDED_UNSAT")
        self.assertEqual(result["enumeration"], "BOUNDED_UNSAT")
        self.assertTrue(result["all_definite"])
        self.assertTrue(result["agree"])

    def test_one_unknown_prevents_agreement(self) -> None:
        spec = {
            "variables": {"x": [1, 2], "y": [2, 3]},
            "constraints": [
                {
                    "op": "lt",
                    "left": {"var": "x"},
                    "right": {"var": "y"},
                }
            ],
        }
        result = dual_solve(spec)
        self.assertEqual(result["z3"], "UNKNOWN")
        self.assertEqual(result["cvc5"], "BOUNDED_SAT")
        self.assertEqual(result["enumeration"], "BOUNDED_SAT")
        self.assertFalse(result["all_definite"])
        self.assertFalse(result["agree"])
        self.assertEqual(
            result["disagreement"]["reason"],
            "mandatory_decider_not_definite",
        )
        self.assertEqual(
            result["disagreement"]["nondefinite_deciders"], ["z3"]
        )
        self.assertEqual(
            result["abstentions"]["z3"],
            "constraint_not_supported_by_z3_profile",
        )

    def test_enumeration_abstains_above_max_states(self) -> None:
        spec = {
            "variables": {"x": list(range(11)), "y": list(range(11))},
            "constraints": [
                {
                    "op": "eq",
                    "left": {"var": "x"},
                    "right": {"var": "y"},
                }
            ],
        }
        result = dual_solve(spec, max_states=100)
        self.assertEqual(result["z3"], "BOUNDED_SAT")
        self.assertEqual(result["cvc5"], "BOUNDED_SAT")
        self.assertEqual(result["enumeration"], "UNKNOWN")
        self.assertFalse(result["all_definite"])
        self.assertFalse(result["agree"])
        self.assertEqual(
            result["disagreement"]["nondefinite_deciders"],
            ["enumeration"],
        )

    def test_cross_variable_equal_values_are_not_same_domain_addresses(self) -> None:
        spec = {
            "variables": {
                "x": [True, 2, [1]],
                "y": [1, 3, [1, 2]],
            },
            "constraints": [
                {
                    "op": "eq",
                    "left": {"var": "x"},
                    "right": {"var": "y"},
                }
            ],
        }
        result = dual_solve(spec)
        self.assertEqual(result["z3"], "BOUNDED_SAT")
        self.assertEqual(result["cvc5"], "BOUNDED_SAT")
        self.assertEqual(result["enumeration"], "BOUNDED_SAT")
        self.assertTrue(result["agree"])

    def test_unhashable_values_work_with_all_different(self) -> None:
        spec = {
            "variables": {"x": [[1]], "y": [[1], [1, 2]]},
            "constraints": [{"op": "all_different", "vars": ["x", "y"]}],
        }
        result = dual_solve(spec)
        self.assertEqual(result["z3"], "BOUNDED_SAT")
        self.assertEqual(result["cvc5"], "BOUNDED_SAT")
        self.assertEqual(result["enumeration"], "BOUNDED_SAT")
        self.assertTrue(result["agree"])

    @patch("constraintbox.dualsolve._solve_z3")
    @patch("constraintbox.dualsolve._solve_cvc5")
    @patch(
        "constraintbox.dualsolve.FiniteConstraintProblem.solve_enumerated"
    )
    def test_all_unknown_is_not_agreement(
        self, solve_enumerated, solve_cvc5, solve_z3
    ) -> None:
        solve_z3.return_value = SolverResult(
            SolverStatus.UNKNOWN, None, 0, "z3_unknown", "z3"
        )
        solve_cvc5.return_value = SolverResult(
            SolverStatus.UNKNOWN, None, 0, "cvc5_unknown", "cvc5"
        )
        solve_enumerated.return_value = SolverResult(
            SolverStatus.UNKNOWN,
            None,
            0,
            "enumeration_bound",
            "enumeration",
        )
        result = dual_solve(
            {
                "variables": {"x": [1]},
                "constraints": [],
            }
        )
        self.assertFalse(result["all_definite"])
        self.assertFalse(result["definite_status_conflict"])
        self.assertFalse(result["agree"])
        self.assertEqual(
            result["disagreement"]["reason"],
            "mandatory_decider_not_definite",
        )
        self.assertEqual(result["disagreement"]["definite_statuses"], {})
        self.assertEqual(
            result["disagreement"]["nondefinite_deciders"],
            ["z3", "cvc5", "enumeration"],
        )

    @patch("constraintbox.dualsolve._solve_z3")
    @patch("constraintbox.dualsolve._solve_cvc5")
    @patch(
        "constraintbox.dualsolve.FiniteConstraintProblem.solve_enumerated"
    )
    def test_definite_conflict_outranks_unknown_decider(
        self, solve_enumerated, solve_cvc5, solve_z3
    ) -> None:
        solve_z3.return_value = SolverResult(
            SolverStatus.BOUNDED_SAT,
            {"x": 1},
            0,
            "bounded_model_found",
            "z3",
        )
        solve_cvc5.return_value = SolverResult(
            SolverStatus.BOUNDED_UNSAT,
            None,
            1,
            "forced_definite_conflict",
            "cvc5",
        )
        solve_enumerated.return_value = SolverResult(
            SolverStatus.UNKNOWN,
            None,
            0,
            "forced_enumeration_unknown",
            "enumeration",
        )

        result = dual_solve(
            {
                "variables": {"x": [1]},
                "constraints": [],
            }
        )

        self.assertFalse(result["all_definite"])
        self.assertTrue(result["definite_status_conflict"])
        self.assertFalse(result["agree"])
        self.assertEqual(
            result["disagreement"]["reason"],
            "definite_status_disagreement",
        )
        self.assertTrue(
            result["disagreement"]["definite_status_conflict"]
        )
        self.assertEqual(
            result["disagreement"]["definite_statuses"],
            {
                "z3": "BOUNDED_SAT",
                "cvc5": "BOUNDED_UNSAT",
            },
        )
        self.assertEqual(
            result["disagreement"]["nondefinite_deciders"],
            ["enumeration"],
        )

    @patch(
        "constraintbox.dualsolve._solve_cvc5",
        side_effect=RuntimeError("backend exploded"),
    )
    def test_backend_exception_becomes_typed_unknown(self, solve_cvc5) -> None:
        result = dual_solve(
            {
                "variables": {"x": [1]},
                "constraints": [],
            }
        )
        self.assertEqual(result["cvc5"], "UNKNOWN")
        self.assertFalse(result["agree"])
        self.assertEqual(
            result["backend_results"]["cvc5"],
            {
                "status": "UNKNOWN",
                "reason": "backend_exception:RuntimeError",
                "explored": 0,
            },
        )
        self.assertEqual(
            result["abstentions"]["cvc5"],
            "backend_exception:RuntimeError",
        )
        self.assertTrue(result["has_execution_error"])
        self.assertEqual(
            result["execution_errors"],
            {"cvc5": "backend_exception:RuntimeError"},
        )
        self.assertEqual(
            result["backend_execution"]["cvc5"]["state"],
            "EXECUTION_ERROR",
        )
        self.assertEqual(
            result["disagreement"]["reason"],
            "backend_execution_error",
        )

    @patch("constraintbox.dualsolve._solve_z3")
    def test_backend_reported_dependency_unavailability_is_not_execution_error(
        self, solve_z3
    ) -> None:
        solve_z3.return_value = SolverResult(
            SolverStatus.UNKNOWN,
            None,
            0,
            "z3_unavailable",
            "z3",
        )
        result = dual_solve(
            {
                "variables": {"x": [1]},
                "constraints": [],
            }
        )

        self.assertEqual(result["z3"], "UNKNOWN")
        self.assertFalse(result["has_execution_error"])
        self.assertEqual(result["execution_errors"], {})
        self.assertEqual(
            result["backend_execution"]["z3"],
            {
                "state": "UNAVAILABLE",
                "reason": "z3_unavailable",
            },
        )
        self.assertEqual(
            result["disagreement"]["reason"],
            "mandatory_decider_not_definite",
        )

    def test_exact_missing_cvc5_module_is_unavailable(self) -> None:
        missing = ModuleNotFoundError(
            "forced missing cvc5",
            name="cvc5",
        )
        with patch(
            "builtins.__import__",
            side_effect=self._import_fault("cvc5", missing),
        ):
            result = dual_solve(
                {
                    "variables": {"x": [1]},
                    "constraints": [],
                }
            )

        self.assertEqual(result["cvc5"], "UNKNOWN")
        self.assertFalse(result["has_execution_error"])
        self.assertEqual(
            result["backend_execution"]["cvc5"]["state"],
            "UNAVAILABLE",
        )

    def test_broken_cvc5_import_is_execution_error(self) -> None:
        broken = ModuleNotFoundError(
            "forced missing cvc5 transitive dependency",
            name="cvc5_transitive_dependency",
        )
        with patch(
            "builtins.__import__",
            side_effect=self._import_fault("cvc5", broken),
        ):
            result = dual_solve(
                {
                    "variables": {"x": [1]},
                    "constraints": [],
                }
            )

        self.assertEqual(result["cvc5"], "UNKNOWN")
        self.assertTrue(result["has_execution_error"])
        self.assertEqual(
            result["execution_errors"],
            {"cvc5": "backend_exception:ModuleNotFoundError"},
        )

    def test_exact_missing_z3_module_is_unavailable_with_or_without_timeout(
        self,
    ) -> None:
        for timeout_ms in (5_000, None):
            with self.subTest(timeout_ms=timeout_ms):
                missing = ModuleNotFoundError(
                    "forced missing z3",
                    name="z3",
                )
                with patch(
                    "builtins.__import__",
                    side_effect=self._import_fault("z3", missing),
                ):
                    result = dual_solve(
                        {
                            "variables": {"x": [1]},
                            "constraints": [],
                        },
                        z3_timeout_ms=timeout_ms,
                    )

                self.assertEqual(result["z3"], "UNKNOWN")
                self.assertFalse(result["has_execution_error"])
                self.assertEqual(
                    result["backend_execution"]["z3"]["state"],
                    "UNAVAILABLE",
                )

    def test_transitive_z3_import_failure_is_execution_error_for_both_paths(
        self,
    ) -> None:
        for timeout_ms in (5_000, None):
            with self.subTest(timeout_ms=timeout_ms):
                broken = ModuleNotFoundError(
                    "forced missing z3 transitive dependency",
                    name="z3_transitive_dependency",
                )
                with patch(
                    "builtins.__import__",
                    side_effect=self._import_fault("z3", broken),
                ):
                    result = dual_solve(
                        {
                            "variables": {"x": [1]},
                            "constraints": [],
                        },
                        z3_timeout_ms=timeout_ms,
                    )

                self.assertEqual(result["z3"], "UNKNOWN")
                self.assertTrue(result["has_execution_error"])
                self.assertEqual(
                    result["execution_errors"],
                    {"z3": "backend_exception:ModuleNotFoundError"},
                )

    @patch(
        "constraintbox.dualsolve._solve_cvc5",
        side_effect=ImportError("forced import error after invocation"),
    )
    def test_import_error_after_backend_invocation_is_execution_error(
        self, solve_cvc5
    ) -> None:
        result = dual_solve(
            {
                "variables": {"x": [1]},
                "constraints": [],
            }
        )

        self.assertEqual(result["cvc5"], "UNKNOWN")
        self.assertTrue(result["has_execution_error"])
        self.assertEqual(
            result["execution_errors"],
            {"cvc5": "backend_exception:ImportError"},
        )

    @patch(
        "constraintbox.dualsolve._solve_cvc5",
        return_value={"status": "BOUNDED_SAT"},
    )
    def test_malformed_backend_return_is_execution_error(
        self, solve_cvc5
    ) -> None:
        result = dual_solve(
            {
                "variables": {"x": [1]},
                "constraints": [],
            }
        )

        self.assertEqual(result["cvc5"], "UNKNOWN")
        self.assertTrue(result["has_execution_error"])
        self.assertEqual(
            result["execution_errors"],
            {"cvc5": "backend_contract_error:dict"},
        )
        self.assertEqual(
            result["backend_execution"]["cvc5"]["state"],
            "EXECUTION_ERROR",
        )

    @patch(
        "constraintbox.dualsolve._solve_cvc5",
        return_value=SolverResult(
            SolverStatus.UNKNOWN,
            None,
            -1,
            "forced_invalid_execution_record",
            "cvc5",
        ),
    )
    def test_invalid_backend_execution_record_is_execution_error(
        self, solve_cvc5
    ) -> None:
        result = dual_solve(
            {
                "variables": {"x": [1]},
                "constraints": [],
            }
        )

        self.assertEqual(result["cvc5"], "UNKNOWN")
        self.assertTrue(result["has_execution_error"])
        self.assertEqual(
            result["execution_errors"],
            {"cvc5": "backend_contract_error:invalid_explored"},
        )

    @patch("constraintbox.dualsolve._solve_z3")
    @patch("constraintbox.dualsolve._solve_cvc5")
    def test_timeout_configuration_is_passed_and_bound_to_output(
        self, solve_cvc5, solve_z3
    ) -> None:
        solve_z3.return_value = SolverResult(
            SolverStatus.BOUNDED_SAT,
            {"x": 1},
            0,
            "bounded_model_found",
            "z3",
        )
        solve_cvc5.return_value = SolverResult(
            SolverStatus.BOUNDED_SAT,
            {"x": 1},
            0,
            "bounded_one_hot_model_found",
            "cvc5",
        )
        result = dual_solve(
            {
                "variables": {"x": [1]},
                "constraints": [],
            },
            max_states=17,
            z3_timeout_ms=101,
            cvc5_timeout_ms=202,
        )
        solve_z3.assert_called_once_with(ANY, timeout_ms=101)
        solve_cvc5.assert_called_once_with(ANY, timeout_ms=202)
        self.assertEqual(
            result["backend_settings"],
            {
                "z3": {"timeout_ms": 101, "max_states": 1},
                "cvc5": {"timeout_ms": 202, "state_count": 1},
                "enumeration": {"timeout_ms": None, "max_states": 17},
            },
        )
        self.assertTrue(result["agree"])


class DualSolveDisagreementTest(unittest.TestCase):
    SPEC = {
        "variables": {"x": [1, 2]},
        "constraints": [
            {
                "op": "eq",
                "left": {"var": "x"},
                "right": {"const": 1},
            }
        ],
    }

    @patch("constraintbox.dualsolve._solve_cvc5")
    def test_injected_wrong_verdict_reaches_disagreement(
        self, solve_cvc5
    ) -> None:
        solve_cvc5.return_value = SolverResult(
            SolverStatus.BOUNDED_UNSAT,
            None,
            2,
            "injected_wrong_verdict",
            "cvc5",
        )
        result = dual_solve(self.SPEC)
        self.assertFalse(result["agree"])
        self.assertEqual(
            result["disagreement"]["definite_statuses"],
            {
                "z3": "BOUNDED_SAT",
                "cvc5": "BOUNDED_UNSAT",
                "enumeration": "BOUNDED_SAT",
            },
        )
        self.assertEqual(
            result["disagreement"]["invalid_witnesses"], {}
        )

    @patch("constraintbox.dualsolve._solve_cvc5")
    def test_injected_bad_witness_is_disagreement(self, solve_cvc5) -> None:
        solve_cvc5.return_value = SolverResult(
            SolverStatus.BOUNDED_SAT,
            {"x": 2},
            0,
            "injected_bad_witness",
            "cvc5",
        )
        result = dual_solve(self.SPEC)
        self.assertFalse(result["agree"])
        self.assertEqual(
            result["disagreement"]["invalid_witnesses"],
            {"cvc5": "constraint_0_failed"},
        )

    @patch("constraintbox.dualsolve._solve_cvc5")
    def test_sat_witness_must_have_exact_variable_keys(
        self, solve_cvc5
    ) -> None:
        solve_cvc5.return_value = SolverResult(
            SolverStatus.BOUNDED_SAT,
            {"x": 1, "attacker_extra": True},
            0,
            "injected_extra_witness_key",
            "cvc5",
        )

        result = dual_solve(self.SPEC)

        self.assertTrue(result["has_execution_error"])
        self.assertEqual(
            result["disagreement"]["invalid_witnesses"],
            {"cvc5": "witness_variable_keys_mismatch"},
        )
        self.assertEqual(
            result["execution_errors"],
            {
                "cvc5": (
                    "invalid_sat_witness:"
                    "witness_variable_keys_mismatch"
                )
            },
        )

    @patch("constraintbox.dualsolve._solve_cvc5")
    def test_sat_witness_value_must_belong_to_declared_domain(
        self, solve_cvc5
    ) -> None:
        solve_cvc5.return_value = SolverResult(
            SolverStatus.BOUNDED_SAT,
            {"x": 999},
            0,
            "injected_out_of_domain_witness",
            "cvc5",
        )

        result = dual_solve(self.SPEC)

        self.assertTrue(result["has_execution_error"])
        self.assertEqual(
            result["disagreement"]["invalid_witnesses"],
            {"cvc5": "witness_value_outside_domain:x"},
        )

    @patch("constraintbox.dualsolve._solve_cvc5")
    def test_witness_domain_membership_supports_unhashable_values(
        self, solve_cvc5
    ) -> None:
        solve_cvc5.return_value = SolverResult(
            SolverStatus.BOUNDED_SAT,
            {"x": [1]},
            0,
            "injected_valid_unhashable_witness",
            "cvc5",
        )

        result = dual_solve(
            {
                "variables": {"x": [[1], [2]]},
                "constraints": [],
            }
        )

        self.assertTrue(result["agree"])
        self.assertFalse(result["has_execution_error"])


class DifferentialGeneratorTest(unittest.TestCase):
    def test_generator_emits_every_required_collision_family(self) -> None:
        report = run_differential(cases=15, seed=20260727)
        self.assertEqual(report["specs_run"], 15)
        self.assertEqual(report["disagreements"], [])
        self.assertTrue(
            all(
                count > 0
                for count in report["collision_family_counts"].values()
            )
        )
        self.assertGreater(report["cross_variable_collision_specs"], 0)
        self.assertGreater(report["unhashable_value_specs"], 0)


if __name__ == "__main__":
    unittest.main()
