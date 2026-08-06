from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from hypothesis import example, given, note, seed, settings
from hypothesis import strategies as st

from constraintbox.constraints import SolverResult, SolverStatus
from constraintbox.intake import canonical_json
from constraintbox.user_request import (
    BLOCKED,
    EVALUATION_ERROR,
    assess_user_request,
)


ROOT = Path(__file__).resolve().parents[1]
REQUEST_FIXTURE = (
    ROOT / "fixtures" / "requests" / "assemble_constraintbox_v1.json"
)
BACKENDS = ("z3", "cvc5", "enumeration")
SAT_WITNESS = {
    "goal_explicit": True,
    "deliverable_explicit": True,
    "scope_explicit": True,
    "assumptions_explicit": True,
    "evidence_explicit": True,
    "actions_explicit": True,
    "external_tests_explicit": True,
    "claim_boundary_explicit": True,
}
EXPECTED_AUTHORITY_FIELDS = {
    "all_pass",
    "checker",
    "claim_ceiling",
    "command",
    "decision",
    "disposition",
    "effective_policy",
    "obligations",
    "pass",
    "policy",
    "profile_id",
    "promotion_allowed",
    "release",
    "retry_budget",
    "tolerance",
    "tool",
    "verdict",
}
AUTHORITY_KEY_VARIANTS = tuple(
    sorted(
        EXPECTED_AUTHORITY_FIELDS
        | {field.upper() for field in EXPECTED_AUTHORITY_FIELDS}
    )
)
REQUEST_ROOT_FIELDS = (
    "schema",
    "request_id",
    "goal",
    "deliverable",
    "in_scope",
    "out_of_scope",
    "assumption_state",
    "assumptions",
    "evidence_required",
    "allowed_actions",
    "requested_external_tests",
    "claim_boundary",
    "unknowns",
    "communication_needs",
)


def _solver_result(backend: str, status: SolverStatus) -> SolverResult:
    witness = SAT_WITNESS if status is SolverStatus.BOUNDED_SAT else None
    explored = 1 if status is SolverStatus.BOUNDED_SAT else 0
    return SolverResult(
        status,
        witness,
        explored,
        f"hypothesis_forced_{status.value.lower()}",
        backend,
    )


class HypothesisSolverPrecedenceTests(unittest.TestCase):
    @seed(20260728)
    @settings(
        max_examples=3,
        derandomize=True,
        database=None,
        deadline=None,
    )
    @example(unknown_backend="enumeration")
    @given(unknown_backend=st.sampled_from(BACKENDS))
    def test_definite_conflict_outranks_one_unknown_backend(
        self, unknown_backend: str
    ) -> None:
        """Replay the SAT/UNSAT/UNKNOWN precedence regression in every slot."""

        definite_backends = [
            backend for backend in BACKENDS if backend != unknown_backend
        ]
        statuses = {
            unknown_backend: SolverStatus.UNKNOWN,
            definite_backends[0]: SolverStatus.BOUNDED_SAT,
            definite_backends[1]: SolverStatus.BOUNDED_UNSAT,
        }
        forced = {
            backend: _solver_result(backend, statuses[backend])
            for backend in BACKENDS
        }
        note(f"forced_statuses={statuses}")

        with (
            patch(
                "constraintbox.dualsolve._solve_z3",
                return_value=forced["z3"],
            ),
            patch(
                "constraintbox.dualsolve._solve_cvc5",
                return_value=forced["cvc5"],
            ),
            patch(
                "constraintbox.dualsolve.FiniteConstraintProblem.solve_enumerated",
                return_value=forced["enumeration"],
            ),
        ):
            assessment = assess_user_request(REQUEST_FIXTURE.read_bytes())

        solver = assessment.solver
        context = (
            f"unknown_backend={unknown_backend}; "
            f"disposition={assessment.disposition}; reason={assessment.reason}; "
            f"solver={solver}"
        )
        self.assertEqual(
            assessment.disposition,
            EVALUATION_ERROR,
            msg=context,
        )
        self.assertEqual(
            assessment.reason,
            "request_solver_disagreement",
            msg=context,
        )
        self.assertIsNotNone(solver, msg=context)
        assert solver is not None
        self.assertFalse(solver["agree"], msg=context)
        self.assertTrue(solver["definite_status_conflict"], msg=context)
        self.assertEqual(solver[unknown_backend], "UNKNOWN", msg=context)
        self.assertEqual(
            {
                solver[backend]
                for backend in BACKENDS
                if backend != unknown_backend
            },
            {"BOUNDED_SAT", "BOUNDED_UNSAT"},
            msg=context,
        )
        self.assertEqual(
            solver["disagreement"]["reason"],
            "definite_status_disagreement",
            msg=context,
        )
        self.assertEqual(
            solver["disagreement"]["nondefinite_deciders"],
            [unknown_backend],
            msg=context,
        )


class HypothesisHostileIntakeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.request = json.loads(REQUEST_FIXTURE.read_bytes())

    @seed(20260728)
    @settings(
        max_examples=len(AUTHORITY_KEY_VARIANTS),
        derandomize=True,
        database=None,
        deadline=None,
    )
    @given(authority_key=st.sampled_from(AUTHORITY_KEY_VARIANTS))
    def test_nested_authority_fields_are_blocked_before_solver_selection(
        self, authority_key: str
    ) -> None:
        request = copy.deepcopy(self.request)
        assumptions = request["assumptions"]
        assert isinstance(assumptions, list)
        assert assumptions and isinstance(assumptions[0], dict)
        assumptions[0]["hostile_metadata"] = {authority_key: "PASS"}

        assessment = assess_user_request(canonical_json(request))
        expected_path = (
            f"$.assumptions[0].hostile_metadata.{authority_key}"
        )
        context = (
            f"authority_key={authority_key!r}; "
            f"disposition={assessment.disposition}; reason={assessment.reason}; "
            f"evidence={assessment.evidence}"
        )
        self.assertEqual(assessment.disposition, BLOCKED, msg=context)
        self.assertEqual(
            assessment.reason,
            "request_attempted_controller_authority",
            msg=context,
        )
        self.assertEqual(
            assessment.evidence["forbidden_paths"],
            [expected_path],
            msg=context,
        )
        self.assertIsNone(assessment.solver, msg=context)
        self.assertFalse(assessment.promotion_allowed, msg=context)

    @seed(20260728)
    @settings(
        max_examples=len(REQUEST_ROOT_FIELDS),
        derandomize=True,
        database=None,
        deadline=None,
    )
    @example(root_key="goal")
    @given(root_key=st.sampled_from(REQUEST_ROOT_FIELDS))
    def test_duplicate_root_keys_are_rejected_as_ambiguous_json(
        self, root_key: str
    ) -> None:
        raw = REQUEST_FIXTURE.read_bytes().rstrip()
        self.assertTrue(raw.endswith(b"}"))
        duplicate = (
            raw[:-1]
            + f', "{root_key}": null}}'.encode("utf-8")
        )

        assessment = assess_user_request(duplicate)
        context = (
            f"root_key={root_key!r}; "
            f"disposition={assessment.disposition}; reason={assessment.reason}; "
            f"evidence={assessment.evidence}"
        )
        self.assertEqual(assessment.disposition, BLOCKED, msg=context)
        self.assertEqual(
            assessment.reason,
            "strict_request_intake_failed",
            msg=context,
        )
        self.assertIn(
            f"duplicate JSON key: {root_key}",
            assessment.evidence["error"],
            msg=context,
        )
        self.assertIsNone(assessment.solver, msg=context)
        self.assertFalse(assessment.promotion_allowed, msg=context)


if __name__ == "__main__":
    unittest.main()
