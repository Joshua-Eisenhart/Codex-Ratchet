from __future__ import annotations

import unittest

from claimgate_plugin.ratchet_floor_smt import (
    RatchetVerdict,
    UndeclaredSymbolError,
    UnsupportedConstraintOpError,
    VariableDomainMismatchError,
    classify_transition,
    cross_check_cases,
    floor_claims_to_spec,
    format_cross_check,
    run_cross_check,
    verdict_examples,
)


def _spec(
    constraints: list[dict[str, object]],
    *,
    variables: dict[str, list[object]] | None = None,
) -> dict[str, object]:
    return {
        "variables": variables or {"x": [0, 1, 2, 3]},
        "constraints": constraints,
    }


def _eq(name: str, value: object) -> dict[str, object]:
    return {
        "op": "eq",
        "left": {"var": name},
        "right": {"const": value},
    }


class RatchetFloorSMTVerdictTests(unittest.TestCase):
    def test_all_five_verdicts_are_reachable(self) -> None:
        expected = {
            "tightened_floor_1_to_2": RatchetVerdict.TIGHTENED,
            "equivalent_same_floor": RatchetVerdict.EQUIVALENT,
            "weakened_floor_2_to_1": RatchetVerdict.WEAKENED,
            "broken_unsat_next": RatchetVerdict.BROKEN,
            "incomparable_disjoint_singletons": RatchetVerdict.INCOMPARABLE,
        }
        observed = {
            name: classify_transition(current_spec, next_spec)
            for name, current_spec, next_spec in verdict_examples()
        }
        self.assertEqual(observed, expected)

    def test_incomparable_is_first_class_not_weakened_or_error(self) -> None:
        current = _spec([_eq("x", 0)])
        next_spec = _spec([_eq("x", 1)])
        self.assertIs(
            classify_transition(current, next_spec),
            RatchetVerdict.INCOMPARABLE,
        )

    def test_broken_precedes_vacuous_implication(self) -> None:
        current = _spec([_eq("x", 0)])
        next_spec = _spec(
            [
                {
                    "op": "and",
                    "constraints": [_eq("x", 1), _eq("x", 2)],
                }
            ]
        )
        self.assertIs(
            classify_transition(current, next_spec),
            RatchetVerdict.BROKEN,
        )


class RatchetFloorSMTIntakeTests(unittest.TestCase):
    def test_rejects_variable_name_mismatch(self) -> None:
        current = _spec([], variables={"x": [0, 1]})
        next_spec = _spec([], variables={"y": [0, 1]})
        with self.assertRaisesRegex(
            VariableDomainMismatchError, "variable names differ"
        ):
            classify_transition(current, next_spec)

    def test_rejects_domain_value_mismatch_by_name(self) -> None:
        current = _spec([], variables={"x": [0, 1]})
        next_spec = _spec([], variables={"x": [0, 2]})
        with self.assertRaisesRegex(
            VariableDomainMismatchError, "domain for 'x' differs at index 1"
        ):
            classify_transition(current, next_spec)

    def test_int_domain_and_bool_domain_match_under_eq(self) -> None:
        current = _spec([], variables={"x": [0, 1]})
        next_spec = _spec([], variables={"x": [False, True]})
        self.assertIs(
            classify_transition(current, next_spec),
            RatchetVerdict.EQUIVALENT,
        )

    def test_equal_unhashable_domain_values_are_supported(self) -> None:
        variables = {"x": [["a"], ["b"]]}
        current = _spec([_eq("x", ["a"])], variables=variables)
        next_spec = _spec([_eq("x", ["a"])], variables=variables)
        self.assertIs(
            classify_transition(current, next_spec),
            RatchetVerdict.EQUIVALENT,
        )

    def test_domain_declaration_order_is_irrelevant(self) -> None:
        current = _spec(
            [_eq("x", 0)],
            variables={"x": [0, 1], "y": ["a", "b"]},
        )
        next_spec = _spec(
            [_eq("x", 0)],
            variables={"y": ["a", "b"], "x": [0, 1]},
        )
        self.assertIs(
            classify_transition(current, next_spec),
            RatchetVerdict.EQUIVALENT,
        )

    def test_domain_value_order_is_significant(self) -> None:
        current = _spec([], variables={"x": [0, 1]})
        next_spec = _spec([], variables={"x": [1, 0]})
        with self.assertRaises(VariableDomainMismatchError):
            classify_transition(current, next_spec)

    def test_rejects_undeclared_symbols_in_every_reference_shape(self) -> None:
        cases = {
            "left": [
                {
                    "op": "eq",
                    "left": {"var": "ghost_left"},
                    "right": {"const": 0},
                }
            ],
            "right": [
                {
                    "op": "eq",
                    "left": {"const": 0},
                    "right": {"var": "ghost_right"},
                }
            ],
            "value": [
                {
                    "op": "in",
                    "value": {"var": "ghost_value"},
                    "values": [0],
                }
            ],
            "vars": [
                {
                    "op": "all_different",
                    "vars": ["x", "ghost_vars"],
                }
            ],
            "nested_and_or_not": [
                {
                    "op": "and",
                    "constraints": [
                        {
                            "op": "or",
                            "constraints": [
                                {
                                    "op": "not",
                                    "constraint": _eq("ghost_nested", 0),
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        valid = _spec([])
        for label, constraints in cases.items():
            with self.subTest(label=label):
                with self.assertRaisesRegex(
                    UndeclaredSymbolError, "ghost_"
                ):
                    classify_transition(_spec(constraints), valid)

    def test_const_payload_var_key_is_not_a_symbol_reference(self) -> None:
        variables = {"x": [{"var": "literal"}, {"var": "other"}]}
        current = _spec(
            [_eq("x", {"var": "literal"})], variables=variables
        )
        next_spec = _spec(
            [_eq("x", {"var": "literal"})], variables=variables
        )
        self.assertIs(
            classify_transition(current, next_spec),
            RatchetVerdict.EQUIVALENT,
        )

    def test_unused_operand_field_cannot_project_out_unknown_symbol(self) -> None:
        constraint = _eq("x", 0)
        constraint["value"] = {"var": "ghost_unused"}
        with self.assertRaisesRegex(
            UndeclaredSymbolError, "ghost_unused"
        ):
            classify_transition(_spec([constraint]), _spec([]))

    def test_unsupported_operation_raises_named_error(self) -> None:
        invalid = _spec(
            [
                {
                    "op": "xor",
                    "left": {"var": "x"},
                    "right": {"const": 0},
                }
            ]
        )
        with self.assertRaisesRegex(
            UnsupportedConstraintOpError, "unsupported op 'xor'"
        ):
            classify_transition(invalid, _spec([]))


class RatchetFloorSMTOperatorTests(unittest.TestCase):
    def test_relational_ops_compare_values_not_domain_addresses(self) -> None:
        variables = {"x": [10, 0, 5]}
        relational = _spec(
            [
                {
                    "op": "ge",
                    "left": {"var": "x"},
                    "right": {"const": 5},
                }
            ],
            variables=variables,
        )
        extensional = _spec(
            [
                {
                    "op": "in",
                    "value": {"var": "x"},
                    "values": [10, 5],
                }
            ],
            variables=variables,
        )
        self.assertIs(
            classify_transition(relational, extensional),
            RatchetVerdict.EQUIVALENT,
        )

    def test_full_constraint_language_compiles(self) -> None:
        variables = {"x": [0, 1, 2], "y": [0, 1, 2]}
        constraints = [
            {
                "op": "and",
                "constraints": [
                    {
                        "op": "neq",
                        "left": {"var": "x"},
                        "right": {"var": "y"},
                    },
                    {
                        "op": "lt",
                        "left": {"var": "x"},
                        "right": {"const": 2},
                    },
                    {
                        "op": "le",
                        "left": {"var": "x"},
                        "right": {"var": "y"},
                    },
                    {
                        "op": "gt",
                        "left": {"var": "y"},
                        "right": {"const": 0},
                    },
                    {
                        "op": "ge",
                        "left": {"var": "y"},
                        "right": {"var": "x"},
                    },
                    {
                        "op": "in",
                        "value": {"var": "x"},
                        "values": [0, 1],
                    },
                    {
                        "op": "not_in",
                        "value": {"var": "y"},
                        "values": [0],
                    },
                    {"op": "all_different", "vars": ["x", "y"]},
                    {
                        "op": "table",
                        "vars": ["x", "y"],
                        "allowed": [[0, 1], [1, 2]],
                    },
                    {
                        "op": "or",
                        "constraints": [
                            _eq("x", 0),
                            {"op": "not", "constraint": _eq("x", 0)},
                        ],
                    },
                ],
            }
        ]
        spec = _spec(constraints, variables=variables)
        self.assertIs(
            classify_transition(spec, spec),
            RatchetVerdict.EQUIVALENT,
        )

    def test_scalar_floor_encoding_uses_ge_and_le_regions(self) -> None:
        domains = {"high": [0, 1, 2], "low": [0, 1, 2]}
        current = floor_claims_to_spec(
            domains,
            [
                {
                    "key": "high",
                    "value": 1,
                    "direction": "higher_is_better",
                },
                {
                    "key": "low",
                    "value": 1,
                    "direction": "lower_is_better",
                },
            ],
        )
        next_spec = floor_claims_to_spec(
            domains,
            [
                {
                    "key": "high",
                    "value": 2,
                    "direction": "higher_is_better",
                },
                {
                    "key": "low",
                    "value": 0,
                    "direction": "lower_is_better",
                },
            ],
        )
        self.assertIs(
            classify_transition(current, next_spec),
            RatchetVerdict.TIGHTENED,
        )


class RatchetFloorSMTCrossCheckTests(unittest.TestCase):
    def test_cross_check_runs_scalar_subprocess_and_preserves_findings(
        self,
    ) -> None:
        rows = run_cross_check()
        self.assertEqual(len(rows), len(cross_check_cases()))
        by_name = {row.name: row for row in rows}
        self.assertEqual(
            (
                by_name["higher_tightened"].scalar_verdict,
                by_name["higher_tightened"].scalar_exit_code,
                by_name["higher_tightened"].smt_verdict,
                by_name["higher_tightened"].agreement,
            ),
            ("ADMITTED", 0, "TIGHTENED", "AGREE"),
        )
        self.assertEqual(
            (
                by_name["higher_weakened"].scalar_verdict,
                by_name["higher_weakened"].scalar_exit_code,
                by_name["higher_weakened"].smt_verdict,
                by_name["higher_weakened"].agreement,
            ),
            ("REJECTED", 1, "WEAKENED", "AGREE"),
        )
        expected_disagreements = {
            "epsilon_tolerance_gap",
            "empty_admitted_region",
            "direction_flip",
            "multi_metric_tradeoff",
            "unknown_new_key",
        }
        self.assertEqual(
            {
                row.name
                for row in rows
                if row.agreement == "DISAGREE"
            },
            expected_disagreements,
        )
        rendered = format_cross_check(rows)
        for name in expected_disagreements:
            self.assertIn(name, rendered)
        self.assertIn('"exact_input"', rendered)


if __name__ == "__main__":
    unittest.main()
