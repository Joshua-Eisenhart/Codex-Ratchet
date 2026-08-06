"""The enumeration and z3 backends must not disagree on a legal spec.

Both backends are offered as independent checks of the same finite encoding.
If they can disagree on an input that passes intake, one of them is wrong and
the independence is decorative.

Regression for the repr-vs-== divergence: domains were deduplicated by repr()
while the enumeration backend compared with ==, so JSON values such as 1 and
true, or 1 and 1.0, passed intake as distinct and were then read differently by
each backend.  The z3 backend could return a "bounded witness" that the
enumeration evaluator rejected.
"""

from __future__ import annotations

import itertools
import random
import unittest

from constraintbox.constraints import (
    ConstraintSpecError,
    FiniteConstraintProblem,
    SolverStatus,
    evaluate_constraint,
)


Z3_SUPPORTED_OPS = ("eq", "neq", "all_different", "and", "or", "not")


def _z3_available() -> bool:
    try:
        import z3  # noqa: F401
    except ImportError:
        return False
    return True


class DomainDistinctnessTest(unittest.TestCase):
    """Intake must reject domains whose values collide under ==."""

    def test_int_and_bool_collision_rejected(self) -> None:
        with self.assertRaises(ConstraintSpecError):
            FiniteConstraintProblem.from_spec(
                {"variables": {"a": [1, True]}, "constraints": []}
            )

    def test_int_and_float_collision_rejected(self) -> None:
        with self.assertRaises(ConstraintSpecError):
            FiniteConstraintProblem.from_spec(
                {"variables": {"x": [1, 1.0]}, "constraints": []}
            )

    def test_zero_and_false_collision_rejected(self) -> None:
        with self.assertRaises(ConstraintSpecError):
            FiniteConstraintProblem.from_spec(
                {"variables": {"z": [0, False]}, "constraints": []}
            )

    def test_exact_duplicate_still_rejected(self) -> None:
        with self.assertRaises(ConstraintSpecError):
            FiniteConstraintProblem.from_spec(
                {"variables": {"d": ["a", "a"]}, "constraints": []}
            )

    def test_genuinely_distinct_domain_accepted(self) -> None:
        problem = FiniteConstraintProblem.from_spec(
            {"variables": {"ok": [0, 1, "a", None]}, "constraints": []}
        )
        self.assertEqual(problem.state_count, 4)


class CrossTypeConstantTest(unittest.TestCase):
    """A float constant must address an int domain value the way == does."""

    SPEC = {
        "variables": {"v": [1, 2]},
        "constraints": [{"op": "eq", "left": {"var": "v"}, "right": {"const": 1.0}}],
    }

    def test_enumeration_finds_the_witness(self) -> None:
        problem = FiniteConstraintProblem.from_spec(self.SPEC)
        result = problem.solve_enumerated()
        self.assertIs(result.status, SolverStatus.BOUNDED_SAT)

    @unittest.skipUnless(_z3_available(), "z3 not installed")
    def test_z3_agrees_with_enumeration(self) -> None:
        problem = FiniteConstraintProblem.from_spec(self.SPEC)
        self.assertIs(
            problem.solve_z3().status, problem.solve_enumerated().status
        )


class UnhashableDomainTest(unittest.TestCase):
    """JSON arrays are legal domain values and must not crash a backend.

    `all_different` used set() to detect collisions, which is hash-based, so a
    list value raised a bare TypeError out of the enumeration backend while the
    z3 backend returned a witness. Same repr-vs-== split, one layer down.
    """

    SPEC = {
        "variables": {"x": ["a", [1]], "y": ["b", [2]]},
        "constraints": [
            {"op": "all_different", "vars": ["x", "y"]},
            {"op": "neq", "left": {"var": "x"}, "right": {"const": "a"}},
        ],
    }

    def test_enumeration_does_not_raise(self) -> None:
        problem = FiniteConstraintProblem.from_spec(self.SPEC)
        result = problem.solve_enumerated()
        self.assertIn(
            result.status,
            (SolverStatus.BOUNDED_SAT, SolverStatus.BOUNDED_UNSAT),
        )

    def test_unhashable_domain_accepted_at_intake(self) -> None:
        problem = FiniteConstraintProblem.from_spec(
            {"variables": {"v": [[1], [2]]}, "constraints": []}
        )
        self.assertEqual(problem.state_count, 2)

    def test_equal_lists_still_rejected(self) -> None:
        with self.assertRaises(ConstraintSpecError):
            FiniteConstraintProblem.from_spec(
                {"variables": {"v": [[1], [1]]}, "constraints": []}
            )

    @unittest.skipUnless(_z3_available(), "z3 not installed")
    def test_backends_agree_on_unhashable_domain(self) -> None:
        problem = FiniteConstraintProblem.from_spec(self.SPEC)
        self.assertIs(
            problem.solve_z3().status, problem.solve_enumerated().status
        )


def _random_spec(rng: random.Random) -> dict:
    """Build a small finite problem using only the z3-supported op subset."""
    # The pool deliberately carries an unhashable JSON array. A pool of only
    # hashable scalars cannot reach the set()-based paths, which is exactly how
    # the all_different defect survived the first pass of this fix.
    pool = [0, 1, 2, "a", "b", [7], [8]]
    names = ["p", "q", "r"][: rng.randint(2, 3)]
    variables = {
        name: rng.sample(pool, rng.randint(2, 3)) for name in names
    }

    def leaf() -> dict:
        op = rng.choice(("eq", "neq"))
        left = {"var": rng.choice(names)}
        if rng.random() < 0.5:
            right: dict = {"var": rng.choice(names)}
        else:
            right = {"const": rng.choice(pool)}
        return {"op": op, "left": left, "right": right}

    def node(depth: int) -> dict:
        if depth == 0 or rng.random() < 0.45:
            if rng.random() < 0.15 and len(names) >= 2:
                return {"op": "all_different", "vars": list(names)}
            return leaf()
        op = rng.choice(("and", "or", "not"))
        if op == "not":
            return {"op": "not", "constraint": node(depth - 1)}
        return {
            "op": op,
            "constraints": [node(depth - 1) for _ in range(rng.randint(2, 3))],
        }

    return {
        "variables": variables,
        "constraints": [node(2) for _ in range(rng.randint(1, 3))],
    }


class DifferentialBackendTest(unittest.TestCase):
    """Randomised differential check across the shared op subset."""

    CASES = 400
    SEED = 20260726

    @unittest.skipUnless(_z3_available(), "z3 not installed")
    def test_backends_agree_on_status(self) -> None:
        rng = random.Random(self.SEED)
        compared = 0
        for case in range(self.CASES):
            spec = _random_spec(rng)
            try:
                problem = FiniteConstraintProblem.from_spec(spec)
            except ConstraintSpecError:
                continue
            enumerated = problem.solve_enumerated()
            z3_result = problem.solve_z3()
            if z3_result.status is SolverStatus.UNKNOWN:
                continue
            compared += 1
            self.assertIs(
                z3_result.status,
                enumerated.status,
                msg=f"case {case} backends disagree on {spec}",
            )
        self.assertGreater(compared, 50, "differential test compared too few cases")

    @unittest.skipUnless(_z3_available(), "z3 not installed")
    def test_z3_witness_satisfies_the_enumeration_evaluator(self) -> None:
        """A z3 model must be a real witness under the system's own evaluator."""
        rng = random.Random(self.SEED + 1)
        checked = 0
        for case in range(self.CASES):
            spec = _random_spec(rng)
            try:
                problem = FiniteConstraintProblem.from_spec(spec)
            except ConstraintSpecError:
                continue
            result = problem.solve_z3()
            if result.status is not SolverStatus.BOUNDED_SAT:
                continue
            checked += 1
            self.assertTrue(
                all(
                    evaluate_constraint(c, result.witness)
                    for c in problem.constraints
                ),
                msg=f"case {case} z3 returned a non-witness for {spec}",
            )
        self.assertGreater(checked, 20, "no SAT models were available to check")

    @unittest.skipUnless(_z3_available(), "z3 not installed")
    def test_unsat_is_confirmed_by_exhaustion(self) -> None:
        """A z3 UNSAT must survive full enumeration of the finite domain."""
        rng = random.Random(self.SEED + 2)
        checked = 0
        for _ in range(self.CASES):
            spec = _random_spec(rng)
            try:
                problem = FiniteConstraintProblem.from_spec(spec)
            except ConstraintSpecError:
                continue
            if problem.solve_z3().status is not SolverStatus.BOUNDED_UNSAT:
                continue
            checked += 1
            names = [name for name, _ in problem.variables]
            values = [domain for _, domain in problem.variables]
            for combination in itertools.product(*values):
                assignment = dict(zip(names, combination, strict=True))
                self.assertFalse(
                    all(
                        evaluate_constraint(c, assignment)
                        for c in problem.constraints
                    ),
                    msg=f"z3 said UNSAT but {assignment} satisfies {spec}",
                )
        self.assertGreater(checked, 5, "no UNSAT results were available to check")


if __name__ == "__main__":
    unittest.main()
