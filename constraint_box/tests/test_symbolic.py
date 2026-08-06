from __future__ import annotations

import builtins
import json
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from constraintbox.contracts import Disposition, TaskRequest
from constraintbox.controller import ConstraintBoxController
from constraintbox.symbolic import SympyRationalPolynomialProfile


def payload(
    coefficients: list[dict[str, object]],
    claimed: list[dict[str, object]],
    **extra: object,
) -> bytes:
    body: dict[str, object] = {
        "coefficients": coefficients,
        "claimed_canonical": claimed,
    }
    body.update(extra)
    return json.dumps(body, separators=(",", ":")).encode()


def term(degree: object, numerator: object, denominator: object) -> dict[str, object]:
    return {
        "degree": degree,
        "numerator": numerator,
        "denominator": denominator,
    }


GOOD_SOURCE = [term(2, 6, 8), term(1, 0, 7), term(0, 2, 4)]
GOOD_CLAIM = [term(0, 1, 2), term(2, 3, 4)]


def _correct_constant_poly_as_dict_fixture(
    _polynomial: object,
    native: bool = False,
    zero: bool = False,
):
    del native, zero
    return {
        (0,): sympy.Rational(1, 2),  # type: ignore[name-defined]
        (2,): sympy.Rational(3, 4),  # type: ignore[name-defined]
    }


class SympyRationalPolynomialProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = SympyRationalPolynomialProfile(
            variable_name="x",
            max_degree=4,
            max_coefficient_bits=16,
        )

    def evaluate(self, raw: bytes):
        return self.profile.evaluate(raw, Path("/unused"))

    def test_exact_poly_over_qq_is_eligible_with_canonical_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            controller = ConstraintBoxController(
                {"exact-polynomial": self.profile},
                Path(directory),
            )
            result = controller.run(
                TaskRequest(
                    "exact-polynomial",
                    payload(GOOD_SOURCE, GOOD_CLAIM),
                    "sympy-good",
                )
            )

        self.assertEqual(result.disposition, Disposition.ELIGIBLE)
        self.assertEqual(result.reason, "exact_polynomial_recomputed")
        self.assertEqual(
            result.evidence["exact_api"],
            "sympy.Poly(..., domain=sympy.QQ).as_dict()",
        )
        self.assertEqual(result.evidence["required_version"], "1.14.0")
        self.assertEqual(
            result.evidence["maximum_exclusive_version"],
            "1.15.0",
        )
        self.assertEqual(result.evidence["sympy_version"], "1.14.0")
        self.assertTrue(result.evidence["version_matches_policy"])
        self.assertEqual(
            result.evidence["runtime_identity"]["distribution"],
            "sympy",
        )
        self.assertEqual(
            result.evidence["runtime_identity"],
            result.evidence["runtime_identity_post_operation"],
        )
        callable_identity = result.evidence["runtime_identity"][
            "callable_bindings"
        ]["Poly.as_dict"]
        self.assertEqual(
            callable_identity["callable"],
            "sympy.polys.polytools.Poly.as_dict",
        )
        self.assertEqual(len(callable_identity["code_sha256"]), 64)
        self.assertEqual(len(callable_identity["code_origin_sha256"]), 64)
        self.assertEqual(
            set(
                result.evidence["runtime_identity"][
                    "callable_bindings"
                ]
            ),
            {
                "Symbol.__new__",
                "Add.__new__",
                "Rational.__new__",
                "Poly.__new__",
                "Poly.as_dict",
            },
        )
        self.assertEqual(
            result.evidence["runtime_identity"]["object_bindings"]["QQ"],
            {
                "module": "sympy.polys.domains.rationalfield",
                "type": "RationalField",
                "identity": "module_singleton",
            },
        )
        self.assertTrue(
            result.evidence["runtime_identity"]["trust_boundary"][
                "host_process_must_be_trusted"
            ]
        )
        self.assertIn(
            "complete transitive SymPy internal call graph",
            result.evidence["runtime_identity"]["trust_boundary"][
                "not_verified"
            ],
        )
        self.assertEqual(result.evidence["sympy_canonical"], GOOD_CLAIM)
        self.assertEqual(
            result.evidence["sympy_canonical"],
            result.evidence["stdlib_fraction_reference"],
        )
        self.assertTrue(result.evidence["stdlib_crosscheck_agrees"])
        operation_receipt = result.evidence["exact_operation_receipt"]
        self.assertEqual(
            operation_receipt["schema"],
            "constraintbox.symbolic.exact-operation.v1",
        )
        self.assertEqual(operation_receipt["operation"], "poly_qq_as_dict")
        self.assertEqual(
            operation_receipt["domain"],
            {
                "requested": "sympy.QQ",
                "observed_is_captured_qq": True,
                "observed_type": (
                    "sympy.polys.domains.rationalfield.RationalField"
                ),
            },
        )
        self.assertEqual(
            operation_receipt["generator"],
            {
                "count": 1,
                "name": "x",
                "observed_type": "sympy.core.symbol.Symbol",
                "matches_requested_symbol": True,
            },
        )
        self.assertEqual(
            operation_receipt["output"]["mapping_type"],
            "builtins.dict",
        )
        self.assertTrue(
            operation_receipt["output"]
            ["all_output_coefficients_are_supported_rationals"]
        )
        self.assertEqual(
            operation_receipt["output"]["observed_rational_types"],
            [
                "sympy.core.numbers.Half",
                "sympy.core.numbers.Rational",
            ],
        )
        self.assertEqual(
            len(result.evidence["exact_operation_receipt_sha256"]),
            64,
        )
        self.assertEqual(len(result.evidence["canonical_input_sha256"]), 64)
        self.assertEqual(len(result.evidence["canonical_output_sha256"]), 64)
        self.assertIn("bounded rational univariate", result.claim_ceiling)

    def test_wrong_but_well_formed_claim_is_blocked(self) -> None:
        outcome = self.evaluate(
            payload(GOOD_SOURCE, [term(0, 1, 2), term(2, 5, 4)])
        )
        self.assertEqual(outcome.disposition, Disposition.BLOCKED)
        self.assertEqual(outcome.reason, "canonical_coefficient_mismatch")
        self.assertTrue(outcome.evidence["stdlib_crosscheck_agrees"])

    def test_configured_degree_and_bit_boundaries_are_enforced(self) -> None:
        maximum = (1 << self.profile.max_coefficient_bits) - 1
        accepted = self.evaluate(
            payload([term(4, maximum, 1)], [term(4, maximum, 1)])
        )
        too_high_degree = self.evaluate(
            payload([term(5, 1, 1)], [term(5, 1, 1)])
        )
        too_many_bits = self.evaluate(
            payload([term(4, 1 << 16, 1)], [term(4, 1 << 16, 1)])
        )
        zero_polynomial = self.evaluate(payload([], []))

        self.assertEqual(accepted.disposition, Disposition.ELIGIBLE)
        self.assertEqual(zero_polynomial.disposition, Disposition.BLOCKED)
        self.assertEqual(zero_polynomial.reason, "symbolic_contract_invalid")
        self.assertEqual(
            zero_polynomial.evidence["error"],
            "coefficients must describe a nonzero polynomial",
        )
        self.assertEqual(too_high_degree.reason, "symbolic_contract_invalid")
        self.assertEqual(too_many_bits.reason, "symbolic_contract_invalid")

    def test_hostile_or_ambiguous_inputs_are_rejected_before_sympy(self) -> None:
        cases = {
            "boolean": payload([term(True, 1, 1)], GOOD_CLAIM),
            "boolean numerator": payload([term(0, True, 1)], GOOD_CLAIM),
            "float exponent": payload([term(0.0, 1, 1)], GOOD_CLAIM),
            "zero denominator": payload([term(0, 1, 0)], GOOD_CLAIM),
            "negative exponent": payload([term(-1, 1, 1)], GOOD_CLAIM),
            "duplicate exponent": payload(
                [term(0, 1, 2), term(0, 1, 3)],
                GOOD_CLAIM,
            ),
            "zero polynomial term": payload([term(0, 0, 1)], []),
            "oversized negative coefficient": payload(
                [term(0, -(1 << 16), 1)],
                GOOD_CLAIM,
            ),
            "free-form expression": payload(
                GOOD_SOURCE,
                GOOD_CLAIM,
                expression="x**2 + arbitrary_call()",
            ),
            "string coefficient": payload([term(0, "1", 2)], GOOD_CLAIM),
            "floating coefficient": payload([term(0, 0.5, 1)], GOOD_CLAIM),
            "extra term key": payload(
                [
                    {
                        "degree": 0,
                        "numerator": 1,
                        "denominator": 2,
                        "verdict": "pass",
                    }
                ],
                GOOD_CLAIM,
            ),
            "noncanonical claim": payload(
                GOOD_SOURCE,
                [term(0, 2, 4), term(2, 3, 4)],
            ),
            "unsorted claim": payload(
                GOOD_SOURCE,
                [term(2, 3, 4), term(0, 1, 2)],
            ),
        }
        for name, raw in cases.items():
            with self.subTest(name=name):
                outcome = self.evaluate(raw)
                self.assertEqual(outcome.disposition, Disposition.BLOCKED)
                self.assertIn(
                    outcome.reason,
                    {
                        "symbolic_contract_keys_mismatch",
                        "symbolic_contract_invalid",
                    },
                )

    def test_missing_sympy_parks_instead_of_false_green(self) -> None:
        real_import = builtins.__import__

        def block_sympy(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "sympy" or name.startswith("sympy."):
                raise ModuleNotFoundError(
                    "No module named 'sympy'",
                    name="sympy",
                )
            return real_import(name, globals, locals, fromlist, level)

        with patch("builtins.__import__", side_effect=block_sympy):
            outcome = self.evaluate(payload(GOOD_SOURCE, GOOD_CLAIM))

        self.assertEqual(outcome.disposition, Disposition.PARKED)
        self.assertEqual(outcome.reason, "sympy_unavailable")
        self.assertEqual(
            outcome.evidence["exact_api"],
            "sympy.Poly(..., domain=sympy.QQ).as_dict()",
        )
        self.assertEqual(
            outcome.evidence["exception_type"],
            "ModuleNotFoundError",
        )
        self.assertEqual(outcome.evidence["missing_module"], "sympy")

    def test_transitive_sympy_import_error_is_blocked(self) -> None:
        real_import = builtins.__import__

        def break_sympy(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "sympy":
                raise ImportError(
                    "cannot import name 'QQ' from 'sympy.polys'"
                )
            return real_import(name, globals, locals, fromlist, level)

        with patch("builtins.__import__", side_effect=break_sympy):
            outcome = self.evaluate(payload(GOOD_SOURCE, GOOD_CLAIM))

        self.assertEqual(outcome.disposition, Disposition.BLOCKED)
        self.assertEqual(outcome.reason, "sympy_import_error")
        self.assertEqual(outcome.evidence["exception_type"], "ImportError")
        self.assertEqual(outcome.evidence["phase"], "module_import")

    def test_transitive_sympy_module_absence_is_blocked(self) -> None:
        real_import = builtins.__import__

        def break_sympy(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "sympy":
                raise ModuleNotFoundError(
                    "No module named 'mpmath'",
                    name="mpmath",
                )
            return real_import(name, globals, locals, fromlist, level)

        with patch("builtins.__import__", side_effect=break_sympy):
            outcome = self.evaluate(payload(GOOD_SOURCE, GOOD_CLAIM))

        self.assertEqual(outcome.disposition, Disposition.BLOCKED)
        self.assertEqual(outcome.reason, "sympy_import_error")
        self.assertEqual(
            outcome.evidence["exception_type"],
            "ModuleNotFoundError",
        )
        self.assertEqual(outcome.evidence["missing_module"], "mpmath")

    def test_sympy_import_runtime_error_is_blocked(self) -> None:
        real_import = builtins.__import__

        def break_sympy(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "sympy":
                raise RuntimeError("sympy initialization failed")
            return real_import(name, globals, locals, fromlist, level)

        with patch("builtins.__import__", side_effect=break_sympy):
            outcome = self.evaluate(payload(GOOD_SOURCE, GOOD_CLAIM))

        self.assertEqual(outcome.disposition, Disposition.BLOCKED)
        self.assertEqual(outcome.reason, "sympy_import_error")
        self.assertEqual(outcome.evidence["exception_type"], "RuntimeError")
        self.assertEqual(
            outcome.evidence["error"],
            "sympy initialization failed",
        )

    def test_sympy_version_drift_is_blocked(self) -> None:
        import sympy

        with patch.object(sympy, "__version__", "1.15.0"):
            outcome = self.evaluate(payload(GOOD_SOURCE, GOOD_CLAIM))

        self.assertEqual(outcome.disposition, Disposition.BLOCKED)
        self.assertEqual(outcome.reason, "sympy_version_drift")
        self.assertEqual(outcome.evidence["required_version"], "1.14.0")
        self.assertEqual(
            outcome.evidence["maximum_exclusive_version"],
            "1.15.0",
        )
        self.assertEqual(outcome.evidence["observed_version"], "1.15.0")
        self.assertFalse(outcome.evidence["version_matches_policy"])

    def test_missing_sympy_version_is_blocked_without_escaping(self) -> None:
        class MissingVersionSympy:
            pass

        real_import = builtins.__import__

        def replace_sympy(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "sympy":
                return MissingVersionSympy()
            return real_import(name, globals, locals, fromlist, level)

        with patch("builtins.__import__", side_effect=replace_sympy):
            outcome = self.evaluate(payload(GOOD_SOURCE, GOOD_CLAIM))

        self.assertEqual(outcome.disposition, Disposition.BLOCKED)
        self.assertEqual(outcome.reason, "sympy_version_inspection_error")
        self.assertEqual(outcome.evidence["exception_type"], "AttributeError")
        self.assertEqual(outcome.evidence["phase"], "version_inspection")

    def test_raising_sympy_version_is_blocked_without_escaping(self) -> None:
        class RaisingVersionSympy:
            @property
            def __version__(self):
                raise RuntimeError("sympy version inspection failed")

        real_import = builtins.__import__

        def replace_sympy(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "sympy":
                return RaisingVersionSympy()
            return real_import(name, globals, locals, fromlist, level)

        with patch("builtins.__import__", side_effect=replace_sympy):
            outcome = self.evaluate(payload(GOOD_SOURCE, GOOD_CLAIM))

        self.assertEqual(outcome.disposition, Disposition.BLOCKED)
        self.assertEqual(outcome.reason, "sympy_version_inspection_error")
        self.assertEqual(outcome.evidence["exception_type"], "RuntimeError")
        self.assertEqual(
            outcome.evidence["error"],
            "sympy version inspection failed",
        )

    def test_fixed_policy_semantic_replay_is_identical(self) -> None:
        raw = payload(GOOD_SOURCE, GOOD_CLAIM)
        first = self.profile.evaluate(raw, Path("/unused-first"))
        replay = self.profile.evaluate(raw, Path("/unused-replay"))

        self.assertEqual(first.disposition, replay.disposition)
        self.assertEqual(first.reason, replay.reason)
        self.assertEqual(
            first.evidence["canonical_input_sha256"],
            replay.evidence["canonical_input_sha256"],
        )
        self.assertEqual(
            first.evidence["canonical_output_sha256"],
            replay.evidence["canonical_output_sha256"],
        )
        self.assertEqual(
            first.evidence["sympy_canonical"],
            replay.evidence["sympy_canonical"],
        )
        self.assertEqual(
            first.evidence["stdlib_fraction_reference"],
            replay.evidence["stdlib_fraction_reference"],
        )
        self.assertEqual(first.evidence, replay.evidence)

    def test_poly_as_dict_mutation_is_caught_by_fraction_crosscheck(self) -> None:
        import sympy

        with patch.object(
            sympy.Poly,
            "as_dict",
            autospec=True,
            return_value={},
        ), patch(
            "constraintbox.symbolic._verify_sympy_runtime",
            return_value={"test_identity": "fixed"},
        ):
            outcome = self.evaluate(payload(GOOD_SOURCE, GOOD_CLAIM))

        self.assertEqual(outcome.disposition, Disposition.BLOCKED)
        self.assertEqual(outcome.reason, "symbolic_crosscheck_disagreement")
        self.assertFalse(outcome.evidence["stdlib_crosscheck_agrees"])
        self.assertEqual(outcome.evidence["sympy_canonical"], [])

    def test_poly_construction_severance_blocks_before_any_result_exists(
        self,
    ) -> None:
        import sympy

        class ExactOperationSevered(RuntimeError):
            pass

        class SeveredPoly:
            @staticmethod
            def __new__(
                _class: object,
                *_args: object,
                **_kwargs: object,
            ) -> object:
                raise ExactOperationSevered(
                    "Poly construction deliberately severed"
                )

            def as_dict(self) -> dict[object, object]:
                raise AssertionError("Poly.as_dict must not be reached")

        with patch.object(
            sympy,
            "Poly",
            new=SeveredPoly,
        ), patch(
            "constraintbox.symbolic._verify_sympy_runtime",
            return_value={"test_identity": "fixed"},
        ):
            outcome = self.evaluate(payload(GOOD_SOURCE, GOOD_CLAIM))

        self.assertEqual(outcome.disposition, Disposition.BLOCKED)
        self.assertEqual(outcome.reason, "sympy_operation_error")
        self.assertEqual(
            outcome.evidence["exception_type"],
            "ExactOperationSevered",
        )
        self.assertEqual(
            outcome.evidence["error"],
            "Poly construction deliberately severed",
        )
        self.assertNotIn("sympy_canonical", outcome.evidence)

    def test_non_sympy_rational_result_type_is_blocked_before_receipt(
        self,
    ) -> None:
        import sympy
        from fractions import Fraction

        with patch.object(
            sympy.Poly,
            "as_dict",
            autospec=True,
            return_value={(0,): Fraction(1, 2)},
        ), patch(
            "constraintbox.symbolic._verify_sympy_runtime",
            return_value={"test_identity": "fixed"},
        ):
            outcome = self.evaluate(payload(GOOD_SOURCE, GOOD_CLAIM))

        self.assertEqual(outcome.disposition, Disposition.BLOCKED)
        self.assertEqual(outcome.reason, "sympy_operation_error")
        self.assertEqual(
            outcome.evidence["error"],
            "Poly.as_dict returned a coefficient outside the expected "
            "SymPy rational domain",
        )
        self.assertNotIn("exact_operation_receipt", outcome.evidence)

    def test_sympy_receives_raw_unreduced_and_negative_denominator_pairs(
        self,
    ) -> None:
        import sympy

        real_rational_new = sympy.Rational.__new__
        cases = (
            (
                "unreduced",
                [term(0, 6, 8)],
                [term(0, 3, 4)],
                (6, 8),
            ),
            (
                "negative denominator",
                [term(0, 1, -2)],
                [term(0, -1, 2)],
                (1, -2),
            ),
        )
        for name, source, claim, poisoned_pair in cases:
            with self.subTest(name=name):
                observed_pairs: list[tuple[int, int]] = []

                def poisoned_rational_new(
                    rational_class: object,
                    numerator: int,
                    denominator: int,
                    gcd: int | None = None,
                ):
                    observed_pairs.append((numerator, denominator))
                    if (numerator, denominator) == poisoned_pair:
                        return real_rational_new(rational_class, 7, 8)
                    return real_rational_new(
                        rational_class,
                        numerator,
                        denominator,
                        gcd,
                    )

                with patch.object(
                    sympy.Rational,
                    "__new__",
                    new=staticmethod(poisoned_rational_new),
                ), patch(
                    "constraintbox.symbolic._verify_sympy_runtime",
                    return_value={"test_identity": "fixed"},
                ):
                    outcome = self.evaluate(payload(source, claim))
                self.assertIn(poisoned_pair, observed_pairs)
                self.assertEqual(outcome.disposition, Disposition.BLOCKED)
                self.assertEqual(
                    outcome.reason,
                    "symbolic_crosscheck_disagreement",
                )
                self.assertFalse(outcome.evidence["stdlib_crosscheck_agrees"])

    def test_same_version_substitute_is_blocked_by_runtime_identity(self) -> None:
        substitute = types.ModuleType("sympy")
        substitute.__version__ = "1.14.0"
        real_import = builtins.__import__

        def replace_sympy(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "sympy":
                return substitute
            return real_import(name, globals, locals, fromlist, level)

        with patch("builtins.__import__", side_effect=replace_sympy):
            outcome = self.evaluate(payload(GOOD_SOURCE, GOOD_CLAIM))

        self.assertEqual(outcome.disposition, Disposition.BLOCKED)
        self.assertEqual(outcome.reason, "sympy_runtime_identity_error")
        self.assertEqual(
            outcome.evidence["phase"],
            "runtime_identity_pre_operation",
        )

    def test_correct_constant_poly_as_dict_is_blocked_by_semantic_witness(
        self,
    ) -> None:
        import sympy
        import sympy.polys.polytools

        poisoned_code = _correct_constant_poly_as_dict_fixture.__code__.replace(
            co_filename=str(Path(sympy.polys.polytools.__file__).resolve())
        )
        constant_callable = types.FunctionType(
            poisoned_code,
            {
                "__builtins__": __builtins__,
                "sympy": sympy,
            },
            "as_dict",
            (False, False),
        )
        constant_callable.__module__ = "sympy.polys.polytools"
        constant_callable.__qualname__ = "Poly.as_dict"
        self.assertEqual(
            constant_callable(None),
            {
                (0,): sympy.Rational(1, 2),
                (2,): sympy.Rational(3, 4),
            },
        )

        distinct_source = [term(1, 5, 7)]
        distinct_claim = [term(1, 5, 7)]
        cases = (
            ("fixture-matching input", GOOD_SOURCE, GOOD_CLAIM),
            ("distinct input", distinct_source, distinct_claim),
        )
        with patch.object(
            sympy.Poly,
            "as_dict",
            new=constant_callable,
        ):
            for name, source, claim in cases:
                with self.subTest(name=name):
                    outcome = self.evaluate(payload(source, claim))
                    self.assertEqual(
                        outcome.disposition,
                        Disposition.BLOCKED,
                    )
                    self.assertEqual(
                        outcome.reason,
                        "sympy_runtime_identity_error",
                    )
                    self.assertEqual(
                        outcome.evidence["phase"],
                        "runtime_identity_pre_operation",
                    )
                    self.assertIn(
                        "semantic witness failed",
                        outcome.evidence["error"],
                    )
                    self.assertNotIn(
                        "raw_validated_input",
                        outcome.evidence,
                    )

    def test_correct_constant_add_substitution_is_blocked_pre_operation(
        self,
    ) -> None:
        import sympy
        import sympy.core.add

        variable = sympy.Symbol("x")
        correct_fixture_expression = (
            sympy.Rational(1, 2)
            + sympy.Rational(3, 4) * variable**2
        )

        def constant_add(*_args: object):
            return correct_fixture_expression

        self.assertEqual(
            sympy.Poly(
                constant_add(),
                variable,
                domain=sympy.QQ,
            ).as_dict(),
            {
                (0,): sympy.Rational(1, 2),
                (2,): sympy.Rational(3, 4),
            },
        )
        with patch.object(
            sympy,
            "Add",
            new=constant_add,
        ), patch.object(
            sympy.core.add,
            "Add",
            new=constant_add,
        ):
            outcome = self.evaluate(payload(GOOD_SOURCE, GOOD_CLAIM))

        self.assertEqual(outcome.disposition, Disposition.BLOCKED)
        self.assertEqual(outcome.reason, "sympy_runtime_identity_error")
        self.assertEqual(
            outcome.evidence["phase"],
            "runtime_identity_pre_operation",
        )
        self.assertIn(
            "public constructor type drift: Add",
            outcome.evidence["error"],
        )
        self.assertNotIn("raw_validated_input", outcome.evidence)

    def test_qq_substitution_is_blocked_pre_operation(self) -> None:
        import sympy
        import sympy.polys.domains.rationalfield

        with patch.object(
            sympy,
            "QQ",
            new=sympy.ZZ,
        ), patch.object(
            sympy.polys.domains.rationalfield,
            "QQ",
            new=sympy.ZZ,
        ):
            outcome = self.evaluate(payload(GOOD_SOURCE, GOOD_CLAIM))

        self.assertEqual(outcome.disposition, Disposition.BLOCKED)
        self.assertEqual(outcome.reason, "sympy_runtime_identity_error")
        self.assertEqual(
            outcome.evidence["phase"],
            "runtime_identity_pre_operation",
        )
        self.assertIn(
            "QQ singleton/type identity drift",
            outcome.evidence["error"],
        )
        self.assertNotIn("raw_validated_input", outcome.evidence)

    def test_constructor_live_binding_mutations_are_blocked(self) -> None:
        import sympy

        def poisoned_new(
            _class: object,
            *_args: object,
            **_kwargs: object,
        ) -> object:
            return object()

        for name, constructor in (
            ("Symbol", sympy.Symbol),
            ("Add", sympy.Add),
            ("Rational", sympy.Rational),
            ("Poly", sympy.Poly),
        ):
            with self.subTest(name=name), patch.object(
                constructor,
                "__new__",
                new=staticmethod(poisoned_new),
            ):
                outcome = self.evaluate(payload(GOOD_SOURCE, GOOD_CLAIM))
                self.assertEqual(
                    outcome.disposition,
                    Disposition.BLOCKED,
                )
                self.assertEqual(
                    outcome.reason,
                    "sympy_runtime_identity_error",
                )
                self.assertEqual(
                    outcome.evidence["phase"],
                    "runtime_identity_pre_operation",
                )
                self.assertIn(name, outcome.evidence["error"])
                self.assertNotIn(
                    "raw_validated_input",
                    outcome.evidence,
                )

    def test_transitive_fake_rational_and_int_subclasses_cannot_spoof_equality(
        self,
    ) -> None:
        from sympy.polys.polyclasses import DMP

        class EvilInt(int):
            def __eq__(self, other: object) -> bool:
                if type(other) is int and other == 0:
                    return False
                return True

        class FakeRational:
            is_Rational = True

            def __init__(self, numerator: int, denominator: int) -> None:
                self.p = EvilInt(numerator)
                self.q = EvilInt(denominator)

        forged = {
            (0,): FakeRational(7, 8),
            (2,): FakeRational(5, 6),
        }
        with patch.object(
            DMP,
            "to_sympy_dict",
            autospec=True,
            return_value=forged,
        ) as poisoned:
            outcome = self.evaluate(payload(GOOD_SOURCE, GOOD_CLAIM))

        poisoned.assert_called_once()
        self.assertEqual(outcome.disposition, Disposition.BLOCKED)
        self.assertEqual(outcome.reason, "sympy_runtime_identity_error")
        self.assertIn(
            outcome.evidence["error"],
            {
                (
                    "SymPy semantic witness failed: constant-and-square "
                    "non-rational coefficient"
                ),
                "SymPy semantic witness failed: constant-and-square output shape",
            },
        )
        self.assertNotIn("sympy_canonical", outcome.evidence)
        self.assertNotIn("stdlib_crosscheck_agrees", outcome.evidence)

    def test_poly_as_dict_result_is_bounded_before_evidence_materialization(
        self,
    ) -> None:
        import sympy

        too_many = {
            (degree,): sympy.Rational(1, 1)
            for degree in range(self.profile.max_degree + 2)
        }
        mutations = {
            "term count": too_many,
            "degree": {
                (self.profile.max_degree + 1,): sympy.Rational(1, 1)
            },
            "coefficient bits": {
                (0,): sympy.Rational(
                    1 << self.profile.max_coefficient_bits,
                    1,
                )
            },
            "zero coefficient": {(0,): sympy.Rational(0, 1)},
        }
        for name, returned in mutations.items():
            with self.subTest(name=name):
                with patch.object(
                    sympy.Poly,
                    "as_dict",
                    autospec=True,
                    return_value=returned,
                ), patch(
                    "constraintbox.symbolic._verify_sympy_runtime",
                    return_value={"test_identity": "fixed"},
                ):
                    outcome = self.evaluate(payload(GOOD_SOURCE, GOOD_CLAIM))
                self.assertEqual(outcome.disposition, Disposition.BLOCKED)
                self.assertEqual(outcome.reason, "sympy_operation_error")
                self.assertNotIn("sympy_canonical", outcome.evidence)
                self.assertNotIn("canonical_output", outcome.evidence)

    def test_exact_poly_as_dict_operation_severance_blocks(self) -> None:
        import sympy

        class ExactOperationSevered(RuntimeError):
            pass

        with patch.object(
            sympy.Poly,
            "as_dict",
            autospec=True,
            side_effect=ExactOperationSevered("Poly.as_dict deliberately severed"),
        ) as severed, patch(
            "constraintbox.symbolic._verify_sympy_runtime",
            return_value={"test_identity": "fixed"},
        ):
            outcome = self.evaluate(payload(GOOD_SOURCE, GOOD_CLAIM))

        severed.assert_called_once()
        self.assertEqual(outcome.disposition, Disposition.BLOCKED)
        self.assertEqual(outcome.reason, "sympy_operation_error")
        self.assertEqual(
            outcome.evidence["exception_type"],
            "ExactOperationSevered",
        )
        self.assertEqual(
            outcome.evidence["error"],
            "Poly.as_dict deliberately severed",
        )
        self.assertEqual(
            outcome.evidence["exact_api"],
            "sympy.Poly(..., domain=sympy.QQ).as_dict()",
        )

    def test_profile_configuration_rejects_unbounded_or_other_operations(self) -> None:
        with self.assertRaises(ValueError):
            SympyRationalPolynomialProfile(expected_operation="sympify_text")
        with self.assertRaises(ValueError):
            SympyRationalPolynomialProfile(max_degree=True)
        with self.assertRaises(ValueError):
            SympyRationalPolynomialProfile(max_degree=65)
        with self.assertRaises(ValueError):
            SympyRationalPolynomialProfile(max_coefficient_bits=4097)
        with self.assertRaises(ValueError):
            SympyRationalPolynomialProfile(variable_name="x + y")
        with self.assertRaisesRegex(ValueError, "required_version"):
            SympyRationalPolynomialProfile(required_version="1.15.0")


if __name__ == "__main__":
    unittest.main()
