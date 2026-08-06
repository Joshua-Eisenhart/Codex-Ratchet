#!/usr/bin/env python3
"""Finite SMT checker for the controller-built attractor-basin observations.

This worker accepts exactly one compact, typed controller bundle through
``--input``.  It never discovers, opens, or parses a Julia/JAX/PyTorch receipt
path.  ``--selftest`` constructs that same controller-shaped bundle in memory
solely to exercise the checker before the controller bundle is available.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable, Iterable

import cvc5
import z3


BUNDLE_SCHEMA = "cb_attractor_basin_observations_v1"
MAP_FORMULA = "F_h(x,y)=(x-h*(x^3-x),0.5*y)"
ENGINE_NAMES = ("jax", "julia", "pytorch")
RADIUS_ORDER = ("negative_one", "origin", "positive_one")
WORK_ID = "cb_attractor_basin_three_engine_20260801"
SOURCE_PATH = Path(__file__).resolve()
SOURCE_LOGICAL_PATH = "workers/attractor_basin_v1/smt_basin.py"


class BundleError(ValueError):
    """Raised when --input is not the controller's declared typed bundle."""


@dataclass(frozen=True)
class EngineObservation:
    name: str
    negative_count: int
    boundary_count: int
    positive_count: int
    nominal_radii_tenths: tuple[int, int, int]
    wrong_radii_tenths: tuple[int, int, int]
    all_controls_passed: bool
    source_sha256: str
    receipt_sha256: str


@dataclass(frozen=True)
class ObservationBundle:
    h: Fraction
    steps: int
    grid_shape: tuple[int, int]
    engines: dict[str, EngineObservation]
    controller_validated_receipts: bool
    controller_roles_separated: bool


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def require_exact_keys(value: Any, expected: set[str], path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise BundleError(f"{path} must be an object")
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise BundleError(f"{path} keys mismatch; missing={missing}, extra={extra}")
    return value


def require_int(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise BundleError(f"{path} must be an integer")
    return value


def require_bool(value: Any, path: str) -> bool:
    if not isinstance(value, bool):
        raise BundleError(f"{path} must be a boolean")
    return value


def require_sha256(value: Any, path: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise BundleError(f"{path} must be a 64-character SHA-256 string")
    try:
        int(value, 16)
    except ValueError as exc:
        raise BundleError(f"{path} must be hexadecimal") from exc
    return value.lower()


def require_radius_vector(value: Any, path: str) -> tuple[int, int, int]:
    if not isinstance(value, list) or len(value) != 3:
        raise BundleError(f"{path} must be a three-element integer array")
    result = tuple(require_int(item, f"{path}[{index}]") for index, item in enumerate(value))
    if any(item < 0 for item in result):
        raise BundleError(f"{path} must contain non-negative tenths")
    return result


def controller_shaped_selftest_bundle() -> dict[str, Any]:
    """Return an in-memory fixture that has the exact public --input shape."""

    def hashes(engine_name: str) -> tuple[str, str]:
        return (
            sha256_bytes(f"{engine_name}:selftest:source".encode("utf-8")),
            sha256_bytes(f"{engine_name}:selftest:receipt".encode("utf-8")),
        )

    engines: dict[str, Any] = {}
    for name in ENGINE_NAMES:
        source_sha256, receipt_sha256 = hashes(name)
        engines[name] = {
            "partition_counts": {"negative": 165, "boundary": 11, "positive": 165},
            "fixed_point_spectral_radii_tenths": [6, 12, 6],
            "wrong_fixed_point_spectral_radii_tenths": [14, 8, 14],
            "all_controls_passed": True,
            "source_sha256": source_sha256,
            "receipt_sha256": receipt_sha256,
        }
    return {
        "schema": BUNDLE_SCHEMA,
        "map": {
            "formula": MAP_FORMULA,
            "h_numerator": 1,
            "h_denominator": 5,
            "steps": 80,
            "grid_shape": [31, 11],
        },
        "engines": engines,
        "controller": {"validated_receipts": True, "roles_separated": True},
    }


def parse_controller_bundle(raw: Any) -> ObservationBundle:
    top = require_exact_keys(raw, {"schema", "map", "engines", "controller"}, "bundle")
    if top["schema"] != BUNDLE_SCHEMA:
        raise BundleError(f"bundle.schema must equal {BUNDLE_SCHEMA!r}")

    map_data = require_exact_keys(
        top["map"],
        {"formula", "h_numerator", "h_denominator", "steps", "grid_shape"},
        "bundle.map",
    )
    if map_data["formula"] != MAP_FORMULA:
        raise BundleError("bundle.map.formula does not name the fixed F_h challenge")
    h_numerator = require_int(map_data["h_numerator"], "bundle.map.h_numerator")
    h_denominator = require_int(map_data["h_denominator"], "bundle.map.h_denominator")
    if h_denominator <= 0:
        raise BundleError("bundle.map.h_denominator must be positive")
    if not isinstance(map_data["grid_shape"], list) or len(map_data["grid_shape"]) != 2:
        raise BundleError("bundle.map.grid_shape must be a two-element array")
    grid_shape = tuple(
        require_int(item, f"bundle.map.grid_shape[{index}]")
        for index, item in enumerate(map_data["grid_shape"])
    )
    if any(item <= 0 for item in grid_shape):
        raise BundleError("bundle.map.grid_shape entries must be positive")

    engines_data = require_exact_keys(top["engines"], set(ENGINE_NAMES), "bundle.engines")
    engines: dict[str, EngineObservation] = {}
    for name in ENGINE_NAMES:
        record = require_exact_keys(
            engines_data[name],
            {
                "partition_counts",
                "fixed_point_spectral_radii_tenths",
                "wrong_fixed_point_spectral_radii_tenths",
                "all_controls_passed",
                "source_sha256",
                "receipt_sha256",
            },
            f"bundle.engines.{name}",
        )
        counts = require_exact_keys(
            record["partition_counts"],
            {"negative", "boundary", "positive"},
            f"bundle.engines.{name}.partition_counts",
        )
        negative_count = require_int(counts["negative"], f"bundle.engines.{name}.partition_counts.negative")
        boundary_count = require_int(counts["boundary"], f"bundle.engines.{name}.partition_counts.boundary")
        positive_count = require_int(counts["positive"], f"bundle.engines.{name}.partition_counts.positive")
        if min(negative_count, boundary_count, positive_count) < 0:
            raise BundleError(f"bundle.engines.{name}.partition_counts cannot be negative")
        engines[name] = EngineObservation(
            name=name,
            negative_count=negative_count,
            boundary_count=boundary_count,
            positive_count=positive_count,
            nominal_radii_tenths=require_radius_vector(
                record["fixed_point_spectral_radii_tenths"],
                f"bundle.engines.{name}.fixed_point_spectral_radii_tenths",
            ),
            wrong_radii_tenths=require_radius_vector(
                record["wrong_fixed_point_spectral_radii_tenths"],
                f"bundle.engines.{name}.wrong_fixed_point_spectral_radii_tenths",
            ),
            all_controls_passed=require_bool(
                record["all_controls_passed"], f"bundle.engines.{name}.all_controls_passed"
            ),
            source_sha256=require_sha256(record["source_sha256"], f"bundle.engines.{name}.source_sha256"),
            receipt_sha256=require_sha256(record["receipt_sha256"], f"bundle.engines.{name}.receipt_sha256"),
        )

    controller = require_exact_keys(
        top["controller"], {"validated_receipts", "roles_separated"}, "bundle.controller"
    )
    return ObservationBundle(
        h=Fraction(h_numerator, h_denominator),
        steps=require_int(map_data["steps"], "bundle.map.steps"),
        grid_shape=grid_shape,
        engines=engines,
        controller_validated_receipts=require_bool(
            controller["validated_receipts"], "bundle.controller.validated_receipts"
        ),
        controller_roles_separated=require_bool(
            controller["roles_separated"], "bundle.controller.roles_separated"
        ),
    )


def fraction_tenths(value: Fraction) -> int:
    scaled = 10 * value
    if scaled.denominator != 1:
        raise BundleError(f"expected radius {value} is not integral in tenths")
    return scaled.numerator


def enumerate_finite_obligations(bundle: ObservationBundle) -> dict[str, Any]:
    """Independent CPython-stdlib finite grid enumeration and exact arithmetic."""

    x_values = [Fraction(-15 + index, 10) for index in range(31)]
    y_values = [Fraction(-5 + index, 10) for index in range(11)]
    labels: Counter[str] = Counter()
    for x_value in x_values:
        for _y_value in y_values:
            if x_value < 0:
                labels["negative"] += 1
            elif x_value > 0:
                labels["positive"] += 1
            else:
                labels["boundary"] += 1

    nominal_x_fixed = abs(1 - 2 * bundle.h)
    nominal_origin = abs(1 + bundle.h)
    wrong_h = -bundle.h
    wrong_x_fixed = abs(1 - 2 * wrong_h)
    wrong_origin = abs(1 + wrong_h)
    expected_nominal_radii = (
        fraction_tenths(nominal_x_fixed),
        fraction_tenths(nominal_origin),
        fraction_tenths(nominal_x_fixed),
    )
    expected_wrong_radii = (
        fraction_tenths(wrong_x_fixed),
        fraction_tenths(wrong_origin),
        fraction_tenths(wrong_x_fixed),
    )
    expected_counts = {
        "negative": labels["negative"],
        "boundary": labels["boundary"],
        "positive": labels["positive"],
    }
    exact_challenge = (
        bundle.h == Fraction(1, 5)
        and bundle.steps == 80
        and bundle.grid_shape == (31, 11)
        and expected_counts == {"negative": 165, "boundary": 11, "positive": 165}
        and expected_nominal_radii == (6, 12, 6)
        and expected_wrong_radii == (14, 8, 14)
    )
    engine_matches: dict[str, bool] = {}
    for name, engine in bundle.engines.items():
        engine_matches[name] = (
            engine.negative_count == expected_counts["negative"]
            and engine.boundary_count == expected_counts["boundary"]
            and engine.positive_count == expected_counts["positive"]
            and engine.nominal_radii_tenths == expected_nominal_radii
            and engine.wrong_radii_tenths == expected_wrong_radii
            and engine.all_controls_passed
        )

    return {
        "method": "CPython stdlib fractions + explicit 31x11 finite enumeration",
        "enumerated_grid_shape": [len(x_values), len(y_values)],
        "enumerated_grid_point_count": len(x_values) * len(y_values),
        "expected_partition_counts": expected_counts,
        "expected_fixed_point_spectral_radii_tenths": list(expected_nominal_radii),
        "expected_wrong_fixed_point_spectral_radii_tenths": list(expected_wrong_radii),
        "fixed_point_radius_order": list(RADIUS_ORDER),
        "engine_measurements_match": engine_matches,
        "controller_flags_observed": (
            bundle.controller_validated_receipts and bundle.controller_roles_separated
        ),
        "positive_observed": exact_challenge
        and all(engine_matches.values())
        and bundle.controller_validated_receipts
        and bundle.controller_roles_separated,
        "contradictory_label_rejected": all(
            engine.positive_count != expected_counts["positive"] + 1
            for engine in bundle.engines.values()
        ),
        "erased_label_rejected": all(engine.positive_count != 0 for engine in bundle.engines.values()),
        "wrong_sign_stability_rejected": all(
            engine.wrong_radii_tenths[0] >= 10 and engine.wrong_radii_tenths[2] >= 10
            for engine in bundle.engines.values()
        ),
    }


def z3_fraction(value: Fraction) -> z3.RatNumRef:
    return z3.Q(value.numerator, value.denominator)


def build_z3_solver(bundle: ObservationBundle, enumeration: dict[str, Any]) -> tuple[z3.Solver, dict[str, Any], dict[str, z3.BoolRef]]:
    solver = z3.Solver()
    solver.set(unsat_core=True)
    assumptions: dict[str, z3.BoolRef] = {}
    terms: dict[str, Any] = {}

    def guarded(name: str, formulas: Iterable[z3.BoolRef]) -> None:
        literal = z3.Bool(f"z3_assume_{name}")
        assumptions[name] = literal
        for formula in formulas:
            solver.add(z3.Implies(literal, formula))

    h = z3.Real("z3_h")
    terms["h"] = h
    guarded("map", [h == z3_fraction(bundle.h), h == z3_fraction(Fraction(1, 5))])
    guarded(
        "controller",
        [z3.BoolVal(bundle.controller_validated_receipts and bundle.controller_roles_separated)],
    )
    expected_counts = enumeration["expected_partition_counts"]
    expected_nominal_radii = enumeration["expected_fixed_point_spectral_radii_tenths"]
    expected_wrong_radii = enumeration["expected_wrong_fixed_point_spectral_radii_tenths"]

    for name in ENGINE_NAMES:
        engine = bundle.engines[name]
        negative = z3.Int(f"z3_{name}_negative_count")
        boundary = z3.Int(f"z3_{name}_boundary_count")
        positive = z3.Int(f"z3_{name}_positive_count")
        terms[f"{name}_positive_count"] = positive
        guarded(
            f"{name}_partition",
            [
                negative == engine.negative_count,
                boundary == engine.boundary_count,
                positive == engine.positive_count,
                negative == expected_counts["negative"],
                boundary == expected_counts["boundary"],
                positive == expected_counts["positive"],
                negative + boundary + positive == bundle.grid_shape[0] * bundle.grid_shape[1],
            ],
        )

        nominal_radii = [z3.Real(f"z3_{name}_nominal_radius_{index}") for index in range(3)]
        wrong_radii = [z3.Real(f"z3_{name}_wrong_radius_{index}") for index in range(3)]
        terms[f"{name}_wrong_fixed_radius"] = wrong_radii[0]
        one = z3.Q(1, 1)
        two = z3.Q(2, 1)
        ten = z3.Q(10, 1)
        nominal_fixed_formula = ten * (one - two * h)
        nominal_origin_formula = ten * (one + h)
        wrong_fixed_formula = ten * (one + two * h)
        wrong_origin_formula = ten * (one - h)
        guarded(
            f"{name}_nominal_radii",
            [
                nominal_radii[0] == engine.nominal_radii_tenths[0],
                nominal_radii[1] == engine.nominal_radii_tenths[1],
                nominal_radii[2] == engine.nominal_radii_tenths[2],
                nominal_radii[0] == expected_nominal_radii[0],
                nominal_radii[1] == expected_nominal_radii[1],
                nominal_radii[2] == expected_nominal_radii[2],
                nominal_radii[0] == nominal_fixed_formula,
                nominal_radii[1] == nominal_origin_formula,
                nominal_radii[2] == nominal_fixed_formula,
            ],
        )
        guarded(
            f"{name}_wrong_radii",
            [
                wrong_radii[0] == engine.wrong_radii_tenths[0],
                wrong_radii[1] == engine.wrong_radii_tenths[1],
                wrong_radii[2] == engine.wrong_radii_tenths[2],
                wrong_radii[0] == expected_wrong_radii[0],
                wrong_radii[1] == expected_wrong_radii[1],
                wrong_radii[2] == expected_wrong_radii[2],
                wrong_radii[0] == wrong_fixed_formula,
                wrong_radii[1] == wrong_origin_formula,
                wrong_radii[2] == wrong_fixed_formula,
            ],
        )
        guarded(f"{name}_controls", [z3.BoolVal(engine.all_controls_passed)])
    return solver, terms, assumptions


def z3_status(result: z3.CheckSatResult) -> str:
    if result == z3.sat:
        return "sat"
    if result == z3.unsat:
        return "unsat"
    return "unknown"


def run_z3(bundle: ObservationBundle, enumeration: dict[str, Any]) -> dict[str, Any]:
    positive_solver, _positive_terms, positive_assumptions = build_z3_solver(bundle, enumeration)
    positive_result = positive_solver.check(*positive_assumptions.values())
    controls: dict[str, Any] = {}
    control_builders: dict[str, Callable[[dict[str, Any]], z3.BoolRef]] = {
        "contradictory_label": lambda terms: terms["julia_positive_count"]
        == bundle.engines["julia"].positive_count + 1,
        "erased_label": lambda terms: terms["julia_positive_count"] == 0,
        "wrong_sign_stability": lambda terms: terms["julia_wrong_fixed_radius"] < z3.Q(10, 1),
    }
    for control_name, condition_builder in control_builders.items():
        solver, terms, assumptions = build_z3_solver(bundle, enumeration)
        literal = z3.Bool(f"z3_assume_control_{control_name}")
        solver.add(z3.Implies(literal, condition_builder(terms)))
        result = solver.check(*assumptions.values(), literal)
        core = [str(item) for item in solver.unsat_core()] if result == z3.unsat else []
        controls[control_name] = {
            "verdict": z3_status(result),
            "assumption_literal": str(literal),
            "unsat_core": core,
            "core_contains_control_assumption": str(literal) in core,
        }
    return {
        "package_version": z3.get_version_string(),
        "positive": {
            "verdict": z3_status(positive_result),
            "assumption_literals": [str(item) for item in positive_assumptions.values()],
        },
        "controls": controls,
    }


def cvc5_real(solver: cvc5.Solver, value: Fraction | int) -> cvc5.Term:
    fraction = value if isinstance(value, Fraction) else Fraction(value, 1)
    return solver.mkReal(fraction.numerator, fraction.denominator)


def build_cvc5_solver(
    bundle: ObservationBundle, enumeration: dict[str, Any]
) -> tuple[cvc5.Solver, dict[str, cvc5.Term], dict[str, cvc5.Term]]:
    solver = cvc5.Solver()
    solver.setOption("produce-unsat-cores", "true")
    solver.setOption("produce-unsat-assumptions", "true")
    solver.setOption("incremental", "true")
    solver.setLogic("QF_LIRA")
    boolean = solver.getBooleanSort()
    integer = solver.getIntegerSort()
    real = solver.getRealSort()
    assumptions: dict[str, cvc5.Term] = {}
    terms: dict[str, cvc5.Term] = {}

    def make(kind: cvc5.Kind, *children: cvc5.Term) -> cvc5.Term:
        return solver.mkTerm(kind, *children)

    def equals(left: cvc5.Term, right: cvc5.Term) -> cvc5.Term:
        return make(cvc5.Kind.EQUAL, left, right)

    def guarded(name: str, formulas: Iterable[cvc5.Term]) -> None:
        literal = solver.mkConst(boolean, f"cvc5_assume_{name}")
        assumptions[name] = literal
        for formula in formulas:
            solver.assertFormula(make(cvc5.Kind.IMPLIES, literal, formula))

    h = solver.mkConst(real, "cvc5_h")
    terms["h"] = h
    guarded("map", [equals(h, cvc5_real(solver, bundle.h)), equals(h, cvc5_real(solver, Fraction(1, 5)))])
    guarded(
        "controller",
        [solver.mkBoolean(bundle.controller_validated_receipts and bundle.controller_roles_separated)],
    )
    expected_counts = enumeration["expected_partition_counts"]
    expected_nominal_radii = enumeration["expected_fixed_point_spectral_radii_tenths"]
    expected_wrong_radii = enumeration["expected_wrong_fixed_point_spectral_radii_tenths"]
    one = cvc5_real(solver, 1)
    two = cvc5_real(solver, 2)
    ten = cvc5_real(solver, 10)
    nominal_fixed_formula = make(cvc5.Kind.MULT, ten, make(cvc5.Kind.SUB, one, make(cvc5.Kind.MULT, two, h)))
    nominal_origin_formula = make(cvc5.Kind.MULT, ten, make(cvc5.Kind.ADD, one, h))
    wrong_fixed_formula = make(cvc5.Kind.MULT, ten, make(cvc5.Kind.ADD, one, make(cvc5.Kind.MULT, two, h)))
    wrong_origin_formula = make(cvc5.Kind.MULT, ten, make(cvc5.Kind.SUB, one, h))

    for name in ENGINE_NAMES:
        engine = bundle.engines[name]
        negative = solver.mkConst(integer, f"cvc5_{name}_negative_count")
        boundary = solver.mkConst(integer, f"cvc5_{name}_boundary_count")
        positive = solver.mkConst(integer, f"cvc5_{name}_positive_count")
        terms[f"{name}_positive_count"] = positive
        guarded(
            f"{name}_partition",
            [
                equals(negative, solver.mkInteger(engine.negative_count)),
                equals(boundary, solver.mkInteger(engine.boundary_count)),
                equals(positive, solver.mkInteger(engine.positive_count)),
                equals(negative, solver.mkInteger(expected_counts["negative"])),
                equals(boundary, solver.mkInteger(expected_counts["boundary"])),
                equals(positive, solver.mkInteger(expected_counts["positive"])),
                equals(
                    make(cvc5.Kind.ADD, negative, boundary, positive),
                    solver.mkInteger(bundle.grid_shape[0] * bundle.grid_shape[1]),
                ),
            ],
        )
        nominal_radii = [solver.mkConst(real, f"cvc5_{name}_nominal_radius_{index}") for index in range(3)]
        wrong_radii = [solver.mkConst(real, f"cvc5_{name}_wrong_radius_{index}") for index in range(3)]
        terms[f"{name}_wrong_fixed_radius"] = wrong_radii[0]
        guarded(
            f"{name}_nominal_radii",
            [
                equals(nominal_radii[0], cvc5_real(solver, engine.nominal_radii_tenths[0])),
                equals(nominal_radii[1], cvc5_real(solver, engine.nominal_radii_tenths[1])),
                equals(nominal_radii[2], cvc5_real(solver, engine.nominal_radii_tenths[2])),
                equals(nominal_radii[0], cvc5_real(solver, expected_nominal_radii[0])),
                equals(nominal_radii[1], cvc5_real(solver, expected_nominal_radii[1])),
                equals(nominal_radii[2], cvc5_real(solver, expected_nominal_radii[2])),
                equals(nominal_radii[0], nominal_fixed_formula),
                equals(nominal_radii[1], nominal_origin_formula),
                equals(nominal_radii[2], nominal_fixed_formula),
            ],
        )
        guarded(
            f"{name}_wrong_radii",
            [
                equals(wrong_radii[0], cvc5_real(solver, engine.wrong_radii_tenths[0])),
                equals(wrong_radii[1], cvc5_real(solver, engine.wrong_radii_tenths[1])),
                equals(wrong_radii[2], cvc5_real(solver, engine.wrong_radii_tenths[2])),
                equals(wrong_radii[0], cvc5_real(solver, expected_wrong_radii[0])),
                equals(wrong_radii[1], cvc5_real(solver, expected_wrong_radii[1])),
                equals(wrong_radii[2], cvc5_real(solver, expected_wrong_radii[2])),
                equals(wrong_radii[0], wrong_fixed_formula),
                equals(wrong_radii[1], wrong_origin_formula),
                equals(wrong_radii[2], wrong_fixed_formula),
            ],
        )
        guarded(f"{name}_controls", [solver.mkBoolean(engine.all_controls_passed)])
    return solver, terms, assumptions


def cvc5_status(result: cvc5.Result) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return "unknown"


def run_cvc5(bundle: ObservationBundle, enumeration: dict[str, Any]) -> dict[str, Any]:
    positive_solver, _positive_terms, positive_assumptions = build_cvc5_solver(bundle, enumeration)
    positive_result = positive_solver.checkSatAssuming(*positive_assumptions.values())
    controls: dict[str, Any] = {}

    def contradictory_label(solver: cvc5.Solver, terms: dict[str, cvc5.Term]) -> cvc5.Term:
        return solver.mkTerm(
            cvc5.Kind.EQUAL,
            terms["julia_positive_count"],
            solver.mkInteger(bundle.engines["julia"].positive_count + 1),
        )

    def erased_label(solver: cvc5.Solver, terms: dict[str, cvc5.Term]) -> cvc5.Term:
        return solver.mkTerm(cvc5.Kind.EQUAL, terms["julia_positive_count"], solver.mkInteger(0))

    def wrong_sign_stability(solver: cvc5.Solver, terms: dict[str, cvc5.Term]) -> cvc5.Term:
        return solver.mkTerm(cvc5.Kind.LT, terms["julia_wrong_fixed_radius"], solver.mkReal(10))

    control_builders: dict[str, Callable[[cvc5.Solver, dict[str, cvc5.Term]], cvc5.Term]] = {
        "contradictory_label": contradictory_label,
        "erased_label": erased_label,
        "wrong_sign_stability": wrong_sign_stability,
    }
    for control_name, condition_builder in control_builders.items():
        solver, terms, assumptions = build_cvc5_solver(bundle, enumeration)
        literal = solver.mkConst(solver.getBooleanSort(), f"cvc5_assume_control_{control_name}")
        solver.assertFormula(
            solver.mkTerm(cvc5.Kind.IMPLIES, literal, condition_builder(solver, terms))
        )
        result = solver.checkSatAssuming(*assumptions.values(), literal)
        full_core = [str(item) for item in solver.getUnsatCore()] if result.isUnsat() else []
        assumption_core = [str(item) for item in solver.getUnsatAssumptions()] if result.isUnsat() else []
        controls[control_name] = {
            "verdict": cvc5_status(result),
            "assumption_literal": str(literal),
            "unsat_assumption_core": assumption_core,
            "unsat_core": full_core,
            "core_contains_control_assumption": str(literal) in assumption_core,
        }
    return {
        "package_version": cvc5.__version__,
        "positive": {
            "verdict": cvc5_status(positive_result),
            "assumption_literals": [str(item) for item in positive_assumptions.values()],
        },
        "controls": controls,
    }


def solver_controls_observed(result: dict[str, Any]) -> bool:
    return result["positive"]["verdict"] == "sat" and all(
        control["verdict"] == "unsat" and control["core_contains_control_assumption"]
        for control in result["controls"].values()
    )


def finite_operation_gate(
    enumeration: dict[str, Any], z3_result: dict[str, Any] | None, cvc5_result: dict[str, Any] | None
) -> bool:
    return bool(
        enumeration["positive_observed"]
        and z3_result is not None
        and cvc5_result is not None
        and solver_controls_observed(z3_result)
        and solver_controls_observed(cvc5_result)
    )


def bundle_summary(bundle: ObservationBundle) -> dict[str, Any]:
    return {
        "schema": BUNDLE_SCHEMA,
        "map": {
            "formula": MAP_FORMULA,
            "h_numerator": bundle.h.numerator,
            "h_denominator": bundle.h.denominator,
            "steps": bundle.steps,
            "grid_shape": list(bundle.grid_shape),
        },
        "engines": {
            name: {
                "partition_counts": {
                    "negative": engine.negative_count,
                    "boundary": engine.boundary_count,
                    "positive": engine.positive_count,
                },
                "fixed_point_spectral_radii_tenths": list(engine.nominal_radii_tenths),
                "wrong_fixed_point_spectral_radii_tenths": list(engine.wrong_radii_tenths),
                "all_controls_passed": engine.all_controls_passed,
                "source_sha256": engine.source_sha256,
                "receipt_sha256": engine.receipt_sha256,
            }
            for name, engine in bundle.engines.items()
        },
        "controller": {
            "validated_receipts": bundle.controller_validated_receipts,
            "roles_separated": bundle.controller_roles_separated,
        },
    }


def output_path_for(args: argparse.Namespace) -> Path:
    default_name = "smt_basin_selftest_receipt.json" if args.selftest else "smt_basin_receipt.json"
    return args.output_dir.resolve() / default_name


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    input_mode = parser.add_mutually_exclusive_group(required=True)
    input_mode.add_argument("--input", type=Path, help="controller-built typed observation bundle")
    input_mode.add_argument("--selftest", action="store_true", help="use only the internal controller-shaped fixture")
    parser.add_argument("--output-dir", type=Path, required=True, help="directory for this run's SMT receipt")
    args = parser.parse_args()

    if args.selftest:
        raw_bundle = controller_shaped_selftest_bundle()
        input_descriptor = {"mode": "selftest_internal_fixture"}
        input_path_metadata: str | None = None
        input_bytes_sha256 = sha256_bytes(canonical_json_bytes(raw_bundle))
    else:
        input_path = args.input.resolve()
        raw_bytes = input_path.read_bytes()
        raw_bundle = json.loads(raw_bytes.decode("utf-8"))
        input_descriptor = {"mode": "controller_bundle"}
        input_path_metadata = str(input_path)
        input_bytes_sha256 = sha256_bytes(raw_bytes)

    bundle = parse_controller_bundle(raw_bundle)
    canonical_bundle_sha256 = sha256_bytes(canonical_json_bytes(raw_bundle))
    enumeration = enumerate_finite_obligations(bundle)
    # Compatibility is earned by the actual assumption, SAT, UNSAT-core, and
    # model APIs below. Exact observed versions belong in the external profile
    # receipt/requirements file, not in a host-pinned runtime abort.
    z3_result = run_z3(bundle, enumeration)
    cvc5_result = run_cvc5(bundle, enumeration)
    finite_gate_observed = finite_operation_gate(enumeration, z3_result, cvc5_result)
    operation_severance = {
        "z3_removed_gate_observed_false": not finite_operation_gate(enumeration, None, cvc5_result),
        "cvc5_removed_gate_observed_false": not finite_operation_gate(enumeration, z3_result, None),
        "both_solvers_removed_gate_observed_false": not finite_operation_gate(enumeration, None, None),
    }

    output_path = output_path_for(args)
    receipt = {
        "schema_version": "cb_attractor_basin_smt_receipt.v1",
        "role_id": "smt_crossover_proof_engineer",
        "worker_status": "raw_execution_complete",
        "classification": "scratch_diagnostic",
        "claim_ceiling": "finite 31x11 partition and fixed-point-radius obligations only; continuous-basin proof is false",
        "continuous_basin_proof": False,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "scientific_admission_allowed": False,
        "builder_statement": "This worker retained raw finite checks and solver cores; it did not audit, admit, certify, or promote any engine result.",
        "source": {"logical_path": SOURCE_LOGICAL_PATH, "sha256": sha256_bytes(SOURCE_PATH.read_bytes())},
        "input": {
            **input_descriptor,
            "input_bytes_sha256": input_bytes_sha256,
            "canonical_bundle_sha256": canonical_bundle_sha256,
            "reads_raw_peer_receipt_paths": False,
            "accepted_input_only": "--input controller-built typed observation bundle",
        },
        "observation_bundle": bundle_summary(bundle),
        "runtime": {
            "python_executable": sys.executable,
            "python_version": sys.version,
            "z3_version": z3.get_version_string(),
            "cvc5_version": cvc5.__version__,
            "compatibility_basis": (
                "required SAT, assumption-literal, model, and UNSAT-core "
                "operations completed in this run"
            ),
        },
        "actual_apis": {
            "z3": ["z3.Solver", "z3.Solver.check(*assumptions)", "z3.Solver.unsat_core"],
            "cvc5": [
                "cvc5.Solver",
                "cvc5.Solver.checkSatAssuming(*assumptions)",
                "cvc5.Solver.getUnsatAssumptions",
                "cvc5.Solver.getUnsatCore",
            ],
            "cpython_stdlib": ["fractions.Fraction", "collections.Counter", "explicit finite grid loops"],
        },
        "tool_calls": [
            {
                "tool": "Z3 4.16",
                "qualified_api": "z3.Solver.check(*assumption_literals)",
                "input_object": "controller typed counts and tenths radii for all three engines",
                "output_object": "positive SAT and retained UNSAT cores for contradictory, erased, and wrong-stability controls",
                "positive_case": "all engine finite observations bind to F_h constraints",
                "negative_or_erased_control": "contradictory label and erased positive label are UNSAT",
                "boundary_case": "11 exact x=0 cells bind the boundary count",
                "demotion_condition": "missing Z3 result makes the finite operation gate false",
                "gates": ["finite_operation_gate", "operation_severance"],
            },
            {
                "tool": "CVC5 1.3.3",
                "qualified_api": "cvc5.Solver.checkSatAssuming(*assumption_literals)",
                "input_object": "independently encoded controller typed counts and tenths radii",
                "output_object": "positive SAT plus assumption and full UNSAT cores",
                "positive_case": "all engine finite observations bind to F_h constraints",
                "negative_or_erased_control": "contradictory label and erased positive label are UNSAT",
                "boundary_case": "11 exact x=0 cells bind the boundary count",
                "demotion_condition": "missing CVC5 result makes the finite operation gate false",
                "gates": ["finite_operation_gate", "operation_severance"],
            },
            {
                "tool": "CPython stdlib enumeration",
                "qualified_api": "fractions.Fraction + explicit 31x11 loops",
                "input_object": "map h, grid shape, and typed engine observations",
                "output_object": "independent counts and stability-radius expectations",
                "positive_case": "165/11/165 and 6/12/6 observations match",
                "negative_or_erased_control": "166 positive cells and zero positive cells do not match enumeration",
                "boundary_case": "x=0 contributes exactly 11 cells",
                "demotion_condition": "missing enumeration makes the finite operation gate false",
                "gates": ["finite_operation_gate"],
            },
        ],
        "independent_enumeration": enumeration,
        "solvers": {"z3": z3_result, "cvc5": cvc5_result},
        "controls": {
            "positive": {
                "observed": finite_gate_observed,
                "z3_verdict": z3_result["positive"]["verdict"],
                "cvc5_verdict": cvc5_result["positive"]["verdict"],
                "enumeration_observed": enumeration["positive_observed"],
            },
            "contradictory_label": {
                "observed": (
                    enumeration["contradictory_label_rejected"]
                    and z3_result["controls"]["contradictory_label"]["verdict"] == "unsat"
                    and cvc5_result["controls"]["contradictory_label"]["verdict"] == "unsat"
                ),
            },
            "erased_label": {
                "observed": (
                    enumeration["erased_label_rejected"]
                    and z3_result["controls"]["erased_label"]["verdict"] == "unsat"
                    and cvc5_result["controls"]["erased_label"]["verdict"] == "unsat"
                ),
            },
            "wrong_sign_stability": {
                "observed": (
                    enumeration["wrong_sign_stability_rejected"]
                    and z3_result["controls"]["wrong_sign_stability"]["verdict"] == "unsat"
                    and cvc5_result["controls"]["wrong_sign_stability"]["verdict"] == "unsat"
                ),
            },
            "operation_severance": {"observed": all(operation_severance.values()), **operation_severance},
        },
        "receipt_types": {
            "partition_counts": "JSON integers",
            "stability_radii": "integer tenths derived from exact rational h",
            "control_observations": "JSON booleans",
            "unsat_cores": "solver term strings",
        },
        "execution": {
            "recommended_input_command": "<python> workers/attractor_basin_v1/smt_basin.py --input <controller-observations.json> --output-dir <directory>",
            "recommended_selftest_command": "<python> workers/attractor_basin_v1/smt_basin.py --selftest --output-dir <directory>",
            "output_filename": output_path.name,
            "output_dir_required": True,
        },
        "path_metadata": {
            "non_semantic": True,
            "source_path": str(SOURCE_PATH),
            "input_path": input_path_metadata,
            "output_dir": str(output_path.parent),
            "output_file": str(output_path),
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    raw_controls = {name: value["observed"] for name, value in receipt["controls"].items()}
    print(f"SMT_BASIN_RECEIPT={output_path}")
    print("SMT_BASIN_RAW_CONTROLS=" + json.dumps(raw_controls, sort_keys=True))
    return 0 if all(raw_controls.values()) else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BundleError as exc:
        print(f"SMT_BASIN_INPUT_ERROR={exc}", file=sys.stderr)
        raise SystemExit(2)
