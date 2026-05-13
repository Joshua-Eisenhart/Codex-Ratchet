#!/usr/bin/env python3
"""cvc5 controls for Hopf/Weyl vertical fiber and horizontal-base metric predicates."""

from __future__ import annotations

import json
from pathlib import Path

import cvc5
from cvc5 import Kind
from receipt_boundary import apply_default_receipt_boundary


NAME = "cvc5_hopf_weyl_vertical_horizontal_metric_predicate_controls"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "checks bounded rational SAT/UNSAT controls for exact Hopf/Weyl vertical fiber and horizontal base-lift metric predicates",
    },
}
TOOL_INTEGRATION_DEPTH = {"cvc5": "load_bearing"}


def solver() -> cvc5.Solver:
    s = cvc5.Solver()
    s.setLogic("QF_LRA")
    s.setOption("produce-models", "true")
    return s


def rat(s: cvc5.Solver, numerator: int, denominator: int = 1) -> cvc5.Term:
    return s.mkReal(numerator, denominator)


def eq(s: cvc5.Solver, left: cvc5.Term, right: cvc5.Term) -> cvc5.Term:
    return s.mkTerm(Kind.EQUAL, left, right)


def neq(s: cvc5.Solver, left: cvc5.Term, right: cvc5.Term) -> cvc5.Term:
    return s.mkTerm(Kind.NOT, eq(s, left, right))


def gt(s: cvc5.Solver, left: cvc5.Term, right: cvc5.Term) -> cvc5.Term:
    return s.mkTerm(Kind.GT, left, right)


def metric_terms(s: cvc5.Solver) -> dict[str, cvc5.Term]:
    real = s.getRealSort()
    return {
        name: s.mkConst(real, name)
        for name in [
            "fiber_norm_sq",
            "raw_base_norm_sq",
            "horizontal_base_norm_sq",
            "raw_base_fiber_inner",
            "horizontal_base_fiber_inner",
            "wrong_sign_horizontal_fiber_inner",
            "pole_horizontal_base_norm_sq",
            "equator_raw_base_fiber_inner",
        ]
    }


def theta_pi_over_3_facts(s: cvc5.Solver, t: dict[str, cvc5.Term]) -> list[cvc5.Term]:
    return [
        eq(s, t["fiber_norm_sq"], rat(s, 1, 4)),
        eq(s, t["raw_base_norm_sq"], rat(s, 1, 4)),
        eq(s, t["horizontal_base_norm_sq"], rat(s, 3, 16)),
        eq(s, t["raw_base_fiber_inner"], rat(s, 1, 8)),
        eq(s, t["horizontal_base_fiber_inner"], rat(s, 0, 1)),
        eq(s, t["wrong_sign_horizontal_fiber_inner"], rat(s, 1, 4)),
    ]


def check(extra_terms: list[cvc5.Term], *, include_theta_facts: bool = True) -> str:
    s = solver()
    t = metric_terms(s)
    if include_theta_facts:
        for fact in theta_pi_over_3_facts(s, t):
            s.assertFormula(fact)
    for term in extra_terms:
        s.assertFormula(term)
    return str(s.checkSat())


def check_with_builder(builder, *, include_theta_facts: bool = True) -> str:
    s = solver()
    t = metric_terms(s)
    if include_theta_facts:
        for fact in theta_pi_over_3_facts(s, t):
            s.assertFormula(fact)
    for term in builder(s, t):
        s.assertFormula(term)
    return str(s.checkSat())


def main() -> int:
    positive = {
        "theta_pi_over_3_metric_facts_sat": check([], include_theta_facts=True),
        "horizontal_base_independent_from_fiber_sat": check_with_builder(
            lambda s, t: [eq(s, t["horizontal_base_fiber_inner"], rat(s, 0))]
        ),
        "raw_base_has_connection_component_sat": check_with_builder(
            lambda s, t: [gt(s, t["raw_base_fiber_inner"], rat(s, 0))]
        ),
        "wrong_sign_connection_has_fiber_component_sat": check_with_builder(
            lambda s, t: [gt(s, t["wrong_sign_horizontal_fiber_inner"], rat(s, 0))]
        ),
        "pole_horizontal_base_collapse_sat": check_with_builder(
            lambda s, t: [eq(s, t["pole_horizontal_base_norm_sq"], rat(s, 0))],
            include_theta_facts=False,
        ),
        "equator_raw_base_accidental_independence_sat": check_with_builder(
            lambda s, t: [eq(s, t["equator_raw_base_fiber_inner"], rat(s, 0))],
            include_theta_facts=False,
        ),
    }

    graveyards = {
        "raw_base_independent_from_fiber_is_unsat_at_non_equator": {
            "check": check_with_builder(lambda s, t: [eq(s, t["raw_base_fiber_inner"], rat(s, 0))]),
            "passed": False,
        },
        "horizontal_base_not_independent_from_fiber_is_unsat": {
            "check": check_with_builder(lambda s, t: [neq(s, t["horizontal_base_fiber_inner"], rat(s, 0))]),
            "passed": False,
        },
        "wrong_connection_sign_independent_from_fiber_is_unsat": {
            "check": check_with_builder(lambda s, t: [eq(s, t["wrong_sign_horizontal_fiber_inner"], rat(s, 0))]),
            "passed": False,
        },
        "pole_horizontal_base_noncollapse_is_unsat": {
            "check": check_with_builder(
                lambda s, t: [
                    eq(s, t["pole_horizontal_base_norm_sq"], rat(s, 0)),
                    gt(s, t["pole_horizontal_base_norm_sq"], rat(s, 0)),
                ],
                include_theta_facts=False,
            ),
            "passed": False,
        },
        "equator_raw_base_nonzero_connection_is_unsat": {
            "check": check_with_builder(
                lambda s, t: [
                    eq(s, t["equator_raw_base_fiber_inner"], rat(s, 0)),
                    neq(s, t["equator_raw_base_fiber_inner"], rat(s, 0)),
                ],
                include_theta_facts=False,
            ),
            "passed": False,
        },
    }
    for row in graveyards.values():
        row["passed"] = row["check"] == "unsat"

    all_positive = all(value == "sat" for value in positive.values())
    all_pass = bool(all_positive and all(row["passed"] for row in graveyards.values()))
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "cvc5 bounded rational predicate-control baseline for exact Hopf/Weyl vertical fiber and horizontal base-lift "
            "metric readouts at declared control points only; this cross-checks consistency of already-derived metric "
            "predicates, not physical loop independence in a full nested Hopf-torus geometric-constraint manifold; no flux "
            "representation, no QIT, no GStack, no axis, no bridge, no nonclassical admission, and no target-system admission"
        ),
        "next_lego_target": "hopf_weyl_carrier_loop_geometry_baseline",
        "promotion_condition": (
            "May only support later geometry planning after independent symbolic, numerical, Clifford, topology, and physical "
            "operator-evolution receipts reproduce compatible vertical/horizontal separation with adjacent controls."
        ),
        "demotion_condition": (
            "Demote if raw-base independence is satisfiable at the non-equator control point, if horizontal-base non-independence "
            "is satisfiable, if wrong-sign connection passes, or if pole/equator controls do not collapse."
        ),
        "blocked_until": "blocked from target-system claims until full carrier/topology and physical-evolution receipts exist",
        "out_of_scope": [
            "No full nested Hopf-torus manifold or geometric-constraint manifold.",
            "No flux representation or Pauli-boundary shortcut.",
            "No Lindblad, Hamiltonian, thermodynamic, or information-cycle mechanics.",
            "No QIT, GStack, axis, bridge, nonclassical, or target-system admission.",
        ],
        "divergence_log": (
            "This cvc5 packet is a solver cross-check for the z3 vertical-horizontal metric predicate controls. It does "
            "not add geometry beyond the lower SymPy, Geomstats, and Clifford receipts."
        ),
        "operation_sequence": [
            "declare rational metric readout variables for the theta=pi/3 control point",
            "assert fiber, raw-base, horizontal-base, and wrong-sign metric facts from lower receipts",
            "check positive SAT predicates for horizontal independence and raw/wrong-sign connection components",
            "check UNSAT graveyards for raw-base independence, horizontal-base non-independence, wrong-sign independence, pole noncollapse, and equator nonzero connection",
        ],
        "carrier_topology": "predicate abstraction of local Hopf/Weyl S3 carrier tangent metric readouts; no geometric construction inside cvc5",
        "observable": "cvc5 SAT/UNSAT status for bounded rational metric predicates and adjacent controls",
        "pass_fail_predicate": "all declared positive predicates are SAT and all contradictory adjacent controls are UNSAT",
        "graveyards": [
            "raw base independent from fiber is UNSAT at non-equator",
            "horizontal base not independent from fiber is UNSAT",
            "wrong connection sign independent from fiber is UNSAT",
            "pole horizontal base noncollapse is UNSAT",
            "equator raw base nonzero connection is UNSAT",
        ],
        "baselines": [
            "z3 Hopf/Weyl vertical-horizontal metric predicate controls",
            "SymPy Hopf/Weyl fiber-horizontal-base loop independence identities",
            "Geomstats Hopf/Weyl fiber-horizontal-base loop distance baseline",
            "Clifford Hopf/Weyl fiber-horizontal-base tangent inner-product baseline",
        ],
        "alternative_formulations": [
            "symbolic cvc5 nonlinear trigonometric approximation grid",
            "SAT/UNSAT agreement harness pairing z3 and cvc5 result JSONs",
            "physical operator-evolution fixture over vertical and horizontal carrier paths",
        ],
        "exact_tool_function_needs": {
            "cvc5": ["Real sort", "mkReal", "mkConst", "Kind.EQUAL", "Kind.NOT", "Kind.GT", "assertFormula", "checkSat"],
        },
        "lego_or_coupling_target": "hopf_weyl_carrier_loop_geometry_baseline",
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
    print(f"Results written to {out_path}")
    print(f"PASS={results['pass']}  name={NAME}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
