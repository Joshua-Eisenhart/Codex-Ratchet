from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from constraintbox import (
    ConstraintBoxController,
    Disposition,
    FiniteConstraintProblem,
    FiniteConstraintProfile,
    NumpyAggregateProfile,
    SolverStatus,
    TaskRequest,
)


def problem_bytes(spec: dict[str, object]) -> bytes:
    return json.dumps(spec, sort_keys=True, separators=(",", ":")).encode()


class FiniteConstraintTests(unittest.TestCase):
    def test_bounded_sat_returns_witness(self) -> None:
        problem = FiniteConstraintProblem.from_spec(
            {
                "variables": {"x": [0, 1], "y": [0, 1]},
                "constraints": [
                    {
                        "op": "neq",
                        "left": {"var": "x"},
                        "right": {"var": "y"},
                    }
                ],
            }
        )
        result = problem.solve_enumerated()
        self.assertEqual(result.status, SolverStatus.BOUNDED_SAT)
        self.assertNotEqual(result.witness["x"], result.witness["y"])  # type: ignore[index]

    def test_bounded_unsat_exhausts_domain(self) -> None:
        problem = FiniteConstraintProblem.from_spec(
            {
                "variables": {"x": [0, 1]},
                "constraints": [
                    {
                        "op": "eq",
                        "left": {"var": "x"},
                        "right": {"const": 0},
                    },
                    {
                        "op": "eq",
                        "left": {"var": "x"},
                        "right": {"const": 1},
                    },
                ],
            }
        )
        result = problem.solve_enumerated()
        self.assertEqual(result.status, SolverStatus.BOUNDED_UNSAT)
        self.assertEqual(result.explored, 2)

    def test_bound_exceeded_is_unknown(self) -> None:
        problem = FiniteConstraintProblem.from_spec(
            {"variables": {"x": list(range(11)), "y": list(range(11))}, "constraints": []}
        )
        result = problem.solve_enumerated(max_states=100)
        self.assertEqual(result.status, SolverStatus.UNKNOWN)

    def test_controller_parks_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            controller = ConstraintBoxController(
                {"finite": FiniteConstraintProfile(max_states=4)},
                Path(directory),
            )
            result = controller.run(
                TaskRequest(
                    "finite",
                    problem_bytes(
                        {
                            "variables": {
                                "x": [0, 1, 2],
                                "y": [0, 1, 2],
                            },
                            "constraints": [],
                        }
                    ),
                    "too-large",
                )
            )
            self.assertEqual(result.disposition, Disposition.PARKED)

    def test_profile_requires_controller_owned_sat_polarity(self) -> None:
        contradictory = problem_bytes(
            {
                "variables": {"x": [0, 1]},
                "constraints": [
                    {
                        "op": "eq",
                        "left": {"var": "x"},
                        "right": {"const": 0},
                    },
                    {
                        "op": "eq",
                        "left": {"var": "x"},
                        "right": {"const": 1},
                    },
                ],
            }
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            expects_sat = ConstraintBoxController(
                {"finite": FiniteConstraintProfile()},
                root / "sat",
            )
            expects_unsat = ConstraintBoxController(
                {
                    "finite": FiniteConstraintProfile(
                        expected_status=SolverStatus.BOUNDED_UNSAT
                    )
                },
                root / "unsat",
            )
            mismatch = expects_sat.run(
                TaskRequest("finite", contradictory, "expected-sat")
            )
            matched = expects_unsat.run(
                TaskRequest("finite", contradictory, "expected-unsat")
            )

        self.assertEqual(mismatch.disposition, Disposition.BLOCKED)
        self.assertEqual(mismatch.reason, "bounded_solver_polarity_mismatch")
        self.assertEqual(matched.disposition, Disposition.ELIGIBLE)
        self.assertEqual(
            matched.evidence["expected_status"],
            SolverStatus.BOUNDED_UNSAT.value,
        )

    def test_mixed_order_domain_blocks_instead_of_escaping(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            controller = ConstraintBoxController(
                {"finite": FiniteConstraintProfile()},
                Path(directory),
            )
            result = controller.run(
                TaskRequest(
                    "finite",
                    problem_bytes(
                        {
                            "variables": {"x": ["not-orderable", 1]},
                            "constraints": [
                                {
                                    "op": "lt",
                                    "left": {"var": "x"},
                                    "right": {"const": 2},
                                }
                            ],
                        }
                    ),
                    "mixed-domain",
                )
            )
        self.assertEqual(result.disposition, Disposition.BLOCKED)
        self.assertEqual(result.reason, "finite_problem_invalid")
        self.assertIn("not supported", result.evidence["error"])

    def test_effective_policy_digest_binds_backend_bound_and_polarity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policies = {
                ConstraintBoxController(
                    {"finite": FiniteConstraintProfile()},
                    root / "default",
                ).policy_sha256,
                ConstraintBoxController(
                    {"finite": FiniteConstraintProfile(max_states=99)},
                    root / "bound",
                ).policy_sha256,
                ConstraintBoxController(
                    {"finite": FiniteConstraintProfile(backend="z3")},
                    root / "backend",
                ).policy_sha256,
                ConstraintBoxController(
                    {
                        "finite": FiniteConstraintProfile(
                            expected_status=SolverStatus.BOUNDED_UNSAT
                        )
                    },
                    root / "polarity",
                ).policy_sha256,
            }
        self.assertEqual(len(policies), 4)

    def test_optional_z3_never_false_greens_when_absent(self) -> None:
        problem = FiniteConstraintProblem.from_spec(
            {"variables": {"x": [0, 1]}, "constraints": []}
        )
        result = problem.solve_z3()
        self.assertIn(
            result.status,
            {SolverStatus.UNKNOWN, SolverStatus.BOUNDED_SAT},
        )
        if result.status is SolverStatus.UNKNOWN:
            self.assertEqual(result.reason, "z3_unavailable")

    def test_numpy_correct_and_wrong(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            controller = ConstraintBoxController(
                {"mean": NumpyAggregateProfile("mean")},
                Path(directory),
            )
            good = controller.run(
                TaskRequest(
                    "mean",
                    problem_bytes({"values": [1, 2, 3], "claimed_value": 2}),
                    "mean-good",
                )
            )
            bad = controller.run(
                TaskRequest(
                    "mean",
                    problem_bytes({"values": [1, 2, 3], "claimed_value": 9}),
                    "mean-bad",
                )
            )
            self.assertEqual(good.disposition, Disposition.ELIGIBLE)
            self.assertEqual(bad.disposition, Disposition.BLOCKED)

    def test_numpy_order_sensitive_sum_parks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            controller = ConstraintBoxController(
                {"sum": NumpyAggregateProfile("sum")},
                Path(directory),
            )
            result = controller.run(
                TaskRequest(
                    "sum",
                    problem_bytes(
                        {"values": [1e16, 1.0, -1e16], "claimed_value": 1.0}
                    ),
                    "sum-order",
                )
            )
            self.assertEqual(result.disposition, Disposition.PARKED)


if __name__ == "__main__":
    unittest.main()
