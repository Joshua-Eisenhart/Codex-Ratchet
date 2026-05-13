#!/usr/bin/env python3
"""cvc5 negative control for bare Pauli labels without carrier metrics."""

from __future__ import annotations

import json
from pathlib import Path

import cvc5
from cvc5 import Kind
from receipt_boundary import apply_default_receipt_boundary


NAME = "cvc5_bare_pauli_no_carrier_fiber_base_metric_unsat"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "checks SAT/UNSAT controls for whether bare Pauli labels can satisfy declared carrier/projection metric predicates",
    }
}
TOOL_INTEGRATION_DEPTH = {"cvc5": "load_bearing"}


def solver() -> cvc5.Solver:
    s = cvc5.Solver()
    s.setLogic("QF_UF")
    s.setOption("produce-models", "true")
    return s


def conjunction(s: cvc5.Solver, terms: list[cvc5.Term]) -> cvc5.Term:
    if not terms:
        return s.mkBoolean(True)
    if len(terms) == 1:
        return terms[0]
    return s.mkTerm(Kind.AND, *terms)


def neg(s: cvc5.Solver, term: cvc5.Term) -> cvc5.Term:
    return s.mkTerm(Kind.NOT, term)


def implies(s: cvc5.Solver, left: cvc5.Term, right: cvc5.Term) -> cvc5.Term:
    return s.mkTerm(Kind.IMPLIES, left, right)


def bool_terms(s: cvc5.Solver) -> dict[str, cvc5.Term]:
    boolean = s.getBooleanSort()
    names = [
        "has_carrier",
        "has_projection",
        "has_only_pauli_label",
        "fiber_s3_visible",
        "fiber_s2_hidden",
        "base_s3_visible",
        "base_s2_visible",
        "pole_base_s2_collapsed",
    ]
    return {name: s.mkConst(boolean, name) for name in names}


def carrier_metric_axioms(s: cvc5.Solver, t: dict[str, cvc5.Term]) -> cvc5.Term:
    return conjunction(
        s,
        [
            implies(
                s,
                t["has_only_pauli_label"],
                conjunction(s, [neg(s, t["has_carrier"]), neg(s, t["has_projection"])]),
            ),
            implies(
                s,
                neg(s, t["has_carrier"]),
                conjunction(s, [neg(s, t["fiber_s3_visible"]), neg(s, t["base_s3_visible"])]),
            ),
            implies(
                s,
                neg(s, t["has_projection"]),
                conjunction(s, [neg(s, t["base_s2_visible"]), t["fiber_s2_hidden"]]),
            ),
            implies(
                s,
                conjunction(s, [t["has_carrier"], t["has_projection"]]),
                t["pole_base_s2_collapsed"],
            ),
        ],
    )


def assert_required(s: cvc5.Solver, t: dict[str, cvc5.Term], required_terms: list[str]) -> None:
    for name in required_terms:
        s.assertFormula(t[name])


def assert_full_pattern(s: cvc5.Solver, t: dict[str, cvc5.Term]) -> None:
    s.assertFormula(
        conjunction(
            s,
            [
                t["fiber_s3_visible"],
                t["fiber_s2_hidden"],
                t["base_s3_visible"],
                t["base_s2_visible"],
                t["pole_base_s2_collapsed"],
            ],
        )
    )


def solver_result(required_terms: list[str], *, require_full_pattern: bool = False) -> str:
    s = solver()
    t = bool_terms(s)
    s.assertFormula(carrier_metric_axioms(s, t))
    assert_required(s, t, required_terms)
    if require_full_pattern:
        assert_full_pattern(s, t)
    return str(s.checkSat())


def explicit_denial_result(*, deny_carrier: bool = False, deny_projection: bool = False, required_terms: list[str]) -> str:
    s = solver()
    t = bool_terms(s)
    s.assertFormula(carrier_metric_axioms(s, t))
    if deny_carrier:
        s.assertFormula(neg(s, t["has_carrier"]))
    if deny_projection:
        s.assertFormula(neg(s, t["has_projection"]))
    assert_required(s, t, required_terms)
    return str(s.checkSat())


def run_checks() -> tuple[dict[str, object], dict[str, object]]:
    positive = {
        "carrier_and_projection_can_satisfy_metric_pattern": {
            "cvc5_result": solver_result(["has_carrier", "has_projection"], require_full_pattern=True),
            "expected": "sat",
        },
        "bare_pauli_label_without_metric_claim_is_consistent": {
            "cvc5_result": solver_result(["has_only_pauli_label"]),
            "expected": "sat",
        },
    }
    graveyards = {
        "bare_pauli_label_cannot_supply_s3_carrier_motion": {
            "cvc5_result": solver_result(["has_only_pauli_label", "fiber_s3_visible"]),
            "expected": "unsat",
        },
        "bare_pauli_label_cannot_supply_base_projection_motion": {
            "cvc5_result": solver_result(["has_only_pauli_label", "base_s2_visible"]),
            "expected": "unsat",
        },
        "bare_pauli_label_cannot_satisfy_full_fiber_base_metric_pattern": {
            "cvc5_result": solver_result(["has_only_pauli_label"], require_full_pattern=True),
            "expected": "unsat",
        },
        "not_carrier_with_projection_cannot_supply_s3_motion": {
            "cvc5_result": explicit_denial_result(
                deny_carrier=True,
                required_terms=["has_projection", "base_s3_visible"],
            ),
            "expected": "unsat",
        },
        "carrier_with_not_projection_cannot_supply_base_s2_motion": {
            "cvc5_result": explicit_denial_result(
                deny_projection=True,
                required_terms=["has_carrier", "base_s2_visible"],
            ),
            "expected": "unsat",
        },
    }
    for row in positive.values():
        row["passed"] = row["cvc5_result"] == row["expected"]
    for row in graveyards.values():
        row["passed"] = row["cvc5_result"] == row["expected"]
    return positive, graveyards


def main() -> int:
    positive, graveyards = run_checks()
    all_pass = bool(all(row["passed"] for row in positive.values()) and all(row["passed"] for row in graveyards.values()))
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "cvc5 bare-Pauli/no-carrier negative-control baseline only; this formalizes that label-only Pauli "
            "predicates cannot supply declared Hopf/Weyl S3-carrier and S2-projection metric facts; no physical "
            "geometry, no flux, no QIT, GStack, axis, bridge, nonclassical, target-system, or full "
            "geometric-constraint-manifold admission"
        ),
        "next_lego_target": "bare_pauli_no_carrier_negative_control",
        "promotion_condition": "No promotion from this receipt; use only as a negative control beside carrier-geometry receipts.",
        "demotion_condition": (
            "Demote if bare Pauli labels become SAT for S3 carrier motion, base S2 projection motion, or the full "
            "fiber/base metric pattern without explicit carrier and projection predicates."
        ),
        "blocked_until": "blocked from all topology, carrier, flux, and target-system claims until separate carrier receipts exist",
        "out_of_scope": [
            "No Hopf/Weyl carrier is constructed.",
            "No S3 or S2 metric is computed.",
            "No flux representation or Pauli-boundary shortcut.",
            "No QIT, GStack, axis, bridge, nonclassical, or target-system admission.",
        ],
        "divergence_log": (
            "This cvc5 negative control is intentionally label-only and cross-checks the z3 version. It supports the "
            "boundary that Pauli labels do not replace carrier/projection geometry."
        ),
        "operation_sequence": [
            "declare Boolean predicates for carrier, projection, and bare Pauli label availability",
            "declare Boolean predicates for S3 carrier motion and S2 projection motion readouts",
            "assert that bare Pauli labels imply no carrier and no projection",
            "assert that absent carrier prevents S3 motion readouts",
            "assert that absent projection prevents base S2 motion readouts",
            "check that the full carrier/projection metric pattern is SAT only when carrier and projection are present",
            "check that bare Pauli label controls are UNSAT for the metric pattern",
        ],
        "carrier_topology": "none; finite Boolean predicate model separating bare label availability from carrier/projection availability",
        "observable": "cvc5 SAT/UNSAT outcomes for carrier/projection metric predicates under bare Pauli label controls",
        "pass_fail_predicate": (
            "carrier plus projection can satisfy the metric pattern, bare Pauli label alone is consistent only without "
            "metric claims, and bare Pauli label plus any carrier/projection metric claim is UNSAT"
        ),
        "graveyards": [
            "bare Pauli label cannot supply S3 carrier motion",
            "bare Pauli label cannot supply base S2 projection motion",
            "bare Pauli label cannot satisfy full fiber-base metric pattern",
            "projection with explicitly absent carrier cannot supply S3 motion",
            "carrier with explicitly absent projection cannot supply base S2 motion",
        ],
        "baselines": [
            "Z3 bare-Pauli/no-carrier fiber-base metric negative control",
            "Pauli orientation integer predicate baseline",
            "SymPy Hopf/Weyl S3/S2 exact identity baseline",
            "Geomstats Hopf/Weyl S3/S2 distance baseline",
        ],
        "alternative_formulations": [
            "z3 Boolean negative control for the same predicates",
            "SymPy carrier-free Pauli label gap identity",
            "Clifford bare-generator control without carrier coordinates",
        ],
        "exact_tool_function_needs": {
            "cvc5": ["Solver", "getBooleanSort", "mkConst", "mkTerm", "assertFormula", "checkSat"],
        },
        "lego_or_coupling_target": "bare_pauli_no_carrier_negative_control",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyards_detail": graveyards,
        "promotion_allowed": False,
        "pass": all_pass,
    }
    results = apply_default_receipt_boundary(results, source_name=f"sim_{NAME}")
    out_path = RESULTS_DIR / f"{NAME}_results.json"
    out_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"name": NAME, "all_pass": all_pass, "result": str(out_path)}, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
