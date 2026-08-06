from __future__ import annotations

import unittest

from constraintbox.discharge import (
    EVALUATION_ERROR,
    FAIL,
    ILL_TYPED_VARIABLE,
    INCOMPLETE_EVALUATION,
    MISSING_REQUIRED_VARIABLE,
    PASS,
    STALE_VARIABLE,
    UNDATED_VARIABLE,
    Check,
    Observation,
    Policy,
    Requirement,
    discharge,
    unevaluated_variables,
)


NOW = 1_000_000.0


def fresh(value: object, age: float = 1.0) -> Observation:
    return Observation(value=value, observed_at=NOW - age, source="test")


class PolicyDeclarationTests(unittest.TestCase):
    """1. A policy declares required variables, a comparator, a freshness bound."""

    def setUp(self) -> None:
        self.policy = Policy(
            policy_id="gate:seal",
            requirements=(
                Requirement("residual", "lte", 1e-9),
                Requirement("engine_count", "gte", 3),
                Requirement("solver", "in", ("z3", "cvc5")),
                Requirement("notes", "eq", "clean", optional=True),
            ),
            max_age_seconds=600.0,
        )

    def test_policy_names_its_parts(self) -> None:
        self.assertEqual(
            self.policy.required_variables,
            ("residual", "engine_count", "solver"),
        )
        self.assertEqual(self.policy.optional_variables, ("notes",))
        self.assertEqual(self.policy.max_age_seconds, 600.0)
        self.assertEqual(self.policy.requirements[0].comparator, "lte")

    def test_requirements_coerced_to_tuple(self) -> None:
        policy = Policy(
            policy_id="p",
            requirements=[Requirement("a", "gt", 0)],
            max_age_seconds=1.0,
        )
        self.assertIsInstance(policy.requirements, tuple)

    def test_unknown_comparator_rejected_at_declaration(self) -> None:
        with self.assertRaises(ValueError) as caught:
            Requirement("residual", "approximately", 1e-9)
        self.assertIn("unknown comparator", str(caught.exception))

    def test_ordering_comparator_needs_numeric_threshold(self) -> None:
        with self.assertRaises(ValueError):
            Requirement("residual", "lte", "1e-9")

    def test_membership_comparator_needs_collection_threshold(self) -> None:
        with self.assertRaises(ValueError):
            Requirement("solver", "in", "z3")

    def test_duplicate_variable_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Policy(
                policy_id="p",
                requirements=(
                    Requirement("a", "gt", 0),
                    Requirement("a", "lt", 9),
                ),
                max_age_seconds=1.0,
            )

    def test_all_optional_policy_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Policy(
                policy_id="p",
                requirements=(Requirement("a", "gt", 0, optional=True),),
                max_age_seconds=1.0,
            )

    def test_freshness_bound_must_be_positive_and_finite(self) -> None:
        for bound in (0.0, -1.0, float("inf"), float("nan")):
            with self.subTest(bound=bound), self.assertRaises(ValueError):
                Policy(
                    policy_id="p",
                    requirements=(Requirement("a", "gt", 0),),
                    max_age_seconds=bound,
                )


class GatePolicyFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = Policy(
            policy_id="gate:seal",
            requirements=(
                Requirement("residual", "lte", 1e-9),
                Requirement("engine_count", "gte", 3),
                Requirement("solver", "in", ("z3", "cvc5")),
            ),
            max_age_seconds=600.0,
        )
        self.good = {
            "residual": fresh(1e-12),
            "engine_count": fresh(3),
            "solver": fresh("z3"),
        }


class VerdictTests(GatePolicyFixture):
    """2. All variables present and fresh -> a real verdict."""

    def test_all_present_and_fresh_passes(self) -> None:
        result = discharge(self.policy, self.good, now=NOW)
        self.assertEqual(result.status, PASS)
        self.assertTrue(result.is_verdict)
        self.assertFalse(result.blocking)
        self.assertEqual(result.reason_code, "policy_satisfied")
        self.assertEqual(len(result.checks), 3)
        self.assertEqual(result.unusable, ())

    def test_a_real_fail_is_a_verdict_not_an_error(self) -> None:
        observations = dict(self.good, residual=fresh(1e-3))
        result = discharge(self.policy, observations, now=NOW)
        self.assertEqual(result.status, FAIL)
        self.assertTrue(result.is_verdict)
        self.assertFalse(result.blocking)
        self.assertEqual(result.reason_code, "policy_unsatisfied")
        failed = [c.variable for c in result.checks if c.outcome == FAIL]
        self.assertEqual(failed, ["residual"])

    def test_receipt_records_the_evidence_each_check_ran_on(self) -> None:
        result = discharge(self.policy, self.good, now=NOW)
        by_name = {check.variable: check for check in result.checks}
        self.assertEqual(by_name["residual"].observed, 1e-12)
        self.assertEqual(by_name["residual"].threshold, 1e-9)
        self.assertEqual(by_name["residual"].comparator, "lte")
        self.assertEqual(by_name["residual"].age_seconds, 1.0)
        self.assertEqual(result.decided_at, NOW)

    def test_boundary_values_compare_exactly(self) -> None:
        observations = dict(self.good, residual=fresh(1e-9), engine_count=fresh(3))
        self.assertEqual(discharge(self.policy, observations, now=NOW).status, PASS)
        observations["engine_count"] = fresh(2)
        self.assertEqual(discharge(self.policy, observations, now=NOW).status, FAIL)


class MissingVariableTests(GatePolicyFixture):
    """3. A missing required variable -> EVALUATION_ERROR, blocking, named."""

    def test_missing_required_variable_blocks(self) -> None:
        observations = {k: v for k, v in self.good.items() if k != "residual"}
        result = discharge(self.policy, observations, now=NOW)
        self.assertEqual(result.status, EVALUATION_ERROR)
        self.assertTrue(result.blocking)
        self.assertFalse(result.is_verdict)
        self.assertNotEqual(result.status, PASS)
        self.assertNotEqual(result.status, FAIL)
        self.assertEqual(result.reason_code, MISSING_REQUIRED_VARIABLE)
        self.assertIn("residual", result.missing)

    def test_error_carries_no_comparisons(self) -> None:
        observations = {k: v for k, v in self.good.items() if k != "residual"}
        result = discharge(self.policy, observations, now=NOW)
        self.assertEqual(result.checks, ())

    def test_every_missing_variable_is_named(self) -> None:
        result = discharge(self.policy, {}, now=NOW)
        self.assertEqual(set(result.missing), {"residual", "engine_count", "solver"})

    def test_no_observations_at_all_is_not_a_pass(self) -> None:
        # A bare `value > threshold` over an empty mapping would raise or
        # coerce.  Here it must be a blocking non-verdict.
        result = discharge(self.policy, {}, now=NOW)
        self.assertEqual(result.status, EVALUATION_ERROR)


class StaleVariableTests(GatePolicyFixture):
    """4. A stale variable -> the same treatment as missing."""

    def test_variable_older_than_the_bound_blocks(self) -> None:
        observations = dict(self.good, residual=fresh(1e-12, age=601.0))
        result = discharge(self.policy, observations, now=NOW)
        self.assertEqual(result.status, EVALUATION_ERROR)
        self.assertTrue(result.blocking)
        self.assertEqual(result.reason_code, STALE_VARIABLE)
        self.assertIn("residual", result.stale)
        self.assertEqual(result.checks, ())

    def test_stale_value_that_would_have_passed_still_blocks(self) -> None:
        observations = dict(self.good, residual=fresh(0.0, age=10_000.0))
        result = discharge(self.policy, observations, now=NOW)
        self.assertEqual(result.status, EVALUATION_ERROR)

    def test_exactly_at_the_bound_is_fresh(self) -> None:
        observations = dict(self.good, residual=fresh(1e-12, age=600.0))
        self.assertEqual(discharge(self.policy, observations, now=NOW).status, PASS)

    def test_undated_observation_blocks(self) -> None:
        observations = dict(self.good, residual=Observation(value=1e-12))
        result = discharge(self.policy, observations, now=NOW)
        self.assertEqual(result.status, EVALUATION_ERROR)
        self.assertEqual(result.reason_code, UNDATED_VARIABLE)
        self.assertIn("residual", result.undated)

    def test_future_dated_observation_blocks(self) -> None:
        observations = dict(self.good, residual=fresh(1e-12, age=-5.0))
        result = discharge(self.policy, observations, now=NOW)
        self.assertEqual(result.status, EVALUATION_ERROR)
        self.assertIn("residual", result.stale)


class OptionalVariableTests(unittest.TestCase):
    """5. An optional variable missing -> the verdict still issues."""

    def setUp(self) -> None:
        self.policy = Policy(
            policy_id="gate:seal",
            requirements=(
                Requirement("residual", "lte", 1e-9),
                Requirement("reviewer_ok", "eq", True, optional=True),
            ),
            max_age_seconds=600.0,
        )

    def test_absent_optional_still_yields_a_verdict(self) -> None:
        result = discharge(self.policy, {"residual": fresh(1e-12)}, now=NOW)
        self.assertEqual(result.status, PASS)
        self.assertTrue(result.is_verdict)
        self.assertFalse(result.blocking)

    def test_receipt_records_which_optionals_were_absent(self) -> None:
        result = discharge(self.policy, {"residual": fresh(1e-12)}, now=NOW)
        self.assertEqual(result.absent_optional, ("reviewer_ok",))
        self.assertEqual([c.variable for c in result.checks], ["residual"])

    def test_present_optional_participates_in_the_verdict(self) -> None:
        observations = {"residual": fresh(1e-12), "reviewer_ok": fresh(False)}
        result = discharge(self.policy, observations, now=NOW)
        self.assertEqual(result.status, FAIL)
        self.assertEqual(result.absent_optional, ())

    def test_present_but_stale_optional_blocks(self) -> None:
        # Optional means "may be absent", not "may be unusable".
        observations = {
            "residual": fresh(1e-12),
            "reviewer_ok": fresh(True, age=9_999.0),
        }
        result = discharge(self.policy, observations, now=NOW)
        self.assertEqual(result.status, EVALUATION_ERROR)
        self.assertIn("reviewer_ok", result.stale)


class WrongTypeTests(GatePolicyFixture):
    """6. A variable of the wrong type -> EVALUATION_ERROR, not a coercion."""

    def test_string_where_a_number_is_required_blocks(self) -> None:
        observations = dict(self.good, residual=fresh("1e-12"))
        result = discharge(self.policy, observations, now=NOW)
        self.assertEqual(result.status, EVALUATION_ERROR)
        self.assertEqual(result.reason_code, ILL_TYPED_VARIABLE)
        self.assertIn("residual", result.ill_typed)
        self.assertEqual(result.checks, ())

    def test_none_where_a_number_is_required_blocks(self) -> None:
        observations = dict(self.good, engine_count=fresh(None))
        result = discharge(self.policy, observations, now=NOW)
        self.assertEqual(result.status, EVALUATION_ERROR)
        self.assertIn("engine_count", result.ill_typed)

    def test_bool_is_not_coerced_to_a_number(self) -> None:
        # Naive Python: True >= 3 is False, and True >= 1 is True.  Either way
        # a verdict would be issued on a flag standing in for a count.
        observations = dict(self.good, engine_count=fresh(True))
        result = discharge(self.policy, observations, now=NOW)
        self.assertEqual(result.status, EVALUATION_ERROR)
        self.assertIn("engine_count", result.ill_typed)

    def test_nan_blocks_rather_than_silently_failing(self) -> None:
        # Naive Python: nan <= 1e-9 is False, which reads as an honest fail.
        observations = dict(self.good, residual=fresh(float("nan")))
        result = discharge(self.policy, observations, now=NOW)
        self.assertEqual(result.status, EVALUATION_ERROR)
        self.assertNotEqual(result.status, FAIL)
        self.assertIn("residual", result.ill_typed)

    def test_infinity_blocks(self) -> None:
        observations = dict(self.good, residual=fresh(float("inf")))
        result = discharge(self.policy, observations, now=NOW)
        self.assertEqual(result.status, EVALUATION_ERROR)

    def test_membership_over_a_wrong_type_blocks(self) -> None:
        observations = dict(self.good, solver=fresh(["z3"]))
        result = discharge(self.policy, observations, now=NOW)
        self.assertEqual(result.status, EVALUATION_ERROR)
        self.assertIn("solver", result.ill_typed)

    def test_equality_across_type_classes_blocks(self) -> None:
        policy = Policy(
            policy_id="gate:flag",
            requirements=(Requirement("sealed", "eq", True),),
            max_age_seconds=60.0,
        )
        # Naive Python: 1 == True is True.
        result = discharge(policy, {"sealed": fresh(1)}, now=NOW)
        self.assertEqual(result.status, EVALUATION_ERROR)
        self.assertIn("sealed", result.ill_typed)
        self.assertEqual(discharge(policy, {"sealed": fresh(True)}, now=NOW).status, PASS)

    def test_int_and_float_are_the_same_type_class(self) -> None:
        policy = Policy(
            policy_id="gate:count",
            requirements=(Requirement("n", "eq", 3),),
            max_age_seconds=60.0,
        )
        self.assertEqual(discharge(policy, {"n": fresh(3.0)}, now=NOW).status, PASS)


class PrecedenceAndGuardTests(GatePolicyFixture):
    def test_missing_is_reported_before_the_other_faults(self) -> None:
        observations = {
            "engine_count": fresh("three"),
            "solver": fresh("z3", age=9_999.0),
        }
        result = discharge(self.policy, observations, now=NOW)
        self.assertEqual(result.reason_code, MISSING_REQUIRED_VARIABLE)
        self.assertEqual(result.missing, ("residual",))
        self.assertEqual(result.stale, ("solver",))
        self.assertEqual(result.ill_typed, ("engine_count",))
        self.assertEqual(
            set(result.unusable), {"residual", "solver", "engine_count"}
        )

    def test_coverage_guard_names_uncompared_variables(self) -> None:
        # The guard recomputes coverage from the receipt, so a comparison that
        # never ran cannot pass for one that did.
        ran = (
            Check("residual", "lte", 1e-9, 1e-12, 1.0, PASS),
            Check("engine_count", "gte", 3, 3, 1.0, PASS),
        )
        self.assertEqual(
            unevaluated_variables(self.policy, ran), ("solver",)
        )

    def test_coverage_guard_is_satisfied_by_a_full_receipt(self) -> None:
        result = discharge(self.policy, self.good, now=NOW)
        self.assertEqual(unevaluated_variables(self.policy, result.checks), ())

    def test_coverage_guard_counts_absent_optionals_as_accounted(self) -> None:
        policy = Policy(
            policy_id="p",
            requirements=(
                Requirement("a", "gt", 0),
                Requirement("b", "gt", 0, optional=True),
            ),
            max_age_seconds=60.0,
        )
        ran = (Check("a", "gt", 0, 1, 1.0, PASS),)
        self.assertEqual(unevaluated_variables(policy, ran, ("b",)), ())
        self.assertEqual(unevaluated_variables(policy, ran), ("b",))

    def test_incomplete_evaluation_reason_code_exists_for_the_guard(self) -> None:
        self.assertEqual(INCOMPLETE_EVALUATION, "incomplete_evaluation")

    def test_now_must_be_a_finite_clock(self) -> None:
        for clock in (float("nan"), float("inf"), "1000000", None):
            with self.subTest(clock=clock), self.assertRaises(ValueError):
                discharge(self.policy, self.good, now=clock)


class ThreeWayDistinctionTests(GatePolicyFixture):
    """One policy, three input sets, three outcomes that stay distinct."""

    def test_pass_fail_and_evaluation_error_are_three_outcomes(self) -> None:
        passing = discharge(self.policy, self.good, now=NOW)
        failing = discharge(
            self.policy, dict(self.good, residual=fresh(1e-3)), now=NOW
        )
        blocked = discharge(
            self.policy,
            {k: v for k, v in self.good.items() if k != "residual"},
            now=NOW,
        )
        self.assertEqual(
            [passing.status, failing.status, blocked.status],
            [PASS, FAIL, EVALUATION_ERROR],
        )
        self.assertEqual([r.blocking for r in (passing, failing, blocked)],
                         [False, False, True])
        self.assertEqual([r.is_verdict for r in (passing, failing, blocked)],
                         [True, True, False])
        self.assertEqual(len({passing.status, failing.status, blocked.status}), 3)

    def test_the_blocked_case_is_not_reported_as_the_failing_case(self) -> None:
        failing = discharge(
            self.policy, dict(self.good, residual=fresh(1e-3)), now=NOW
        )
        blocked = discharge(
            self.policy,
            {k: v for k, v in self.good.items() if k != "residual"},
            now=NOW,
        )
        self.assertNotEqual(failing.status, blocked.status)
        self.assertNotEqual(failing.reason_code, blocked.reason_code)
        self.assertTrue(failing.checks)
        self.assertFalse(blocked.checks)


if __name__ == "__main__":
    unittest.main()
