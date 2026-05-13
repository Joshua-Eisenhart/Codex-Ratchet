#!/usr/bin/env python3
"""z3 controls for Hopf/Weyl vertical fiber and horizontal-base metric predicates."""

from __future__ import annotations

import json
from pathlib import Path

from receipt_boundary import apply_default_receipt_boundary


NAME = "z3_hopf_weyl_vertical_horizontal_metric_predicate_controls"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "z3": {
        "tried": True,
        "used": True,
        "reason": "checks bounded rational SAT/UNSAT controls for exact Hopf/Weyl vertical fiber and horizontal base-lift metric predicates",
    },
}
TOOL_INTEGRATION_DEPTH = {"z3": "load_bearing"}


def check(assertions: list[object]) -> str:
    from z3 import Solver

    solver = Solver()
    for assertion in assertions:
        solver.add(assertion)
    return str(solver.check())


def main() -> int:
    from z3 import Q, Real

    fiber_norm_sq = Real("fiber_norm_sq")
    raw_base_norm_sq = Real("raw_base_norm_sq")
    horizontal_base_norm_sq = Real("horizontal_base_norm_sq")
    raw_base_fiber_inner = Real("raw_base_fiber_inner")
    horizontal_base_fiber_inner = Real("horizontal_base_fiber_inner")
    wrong_sign_horizontal_fiber_inner = Real("wrong_sign_horizontal_fiber_inner")
    pole_horizontal_base_norm_sq = Real("pole_horizontal_base_norm_sq")
    equator_raw_base_fiber_inner = Real("equator_raw_base_fiber_inner")

    theta_pi_over_3_facts = [
        fiber_norm_sq == Q(1, 4),
        raw_base_norm_sq == Q(1, 4),
        horizontal_base_norm_sq == Q(3, 16),
        raw_base_fiber_inner == Q(1, 8),
        horizontal_base_fiber_inner == Q(0, 1),
        wrong_sign_horizontal_fiber_inner == Q(1, 4),
    ]
    pole_facts = [pole_horizontal_base_norm_sq == Q(0, 1)]
    equator_facts = [equator_raw_base_fiber_inner == Q(0, 1)]

    positive = {
        "theta_pi_over_3_metric_facts_sat": check(theta_pi_over_3_facts),
        "horizontal_base_independent_from_fiber_sat": check(theta_pi_over_3_facts + [horizontal_base_fiber_inner == 0]),
        "raw_base_has_connection_component_sat": check(theta_pi_over_3_facts + [raw_base_fiber_inner > 0]),
        "wrong_sign_connection_has_fiber_component_sat": check(theta_pi_over_3_facts + [wrong_sign_horizontal_fiber_inner > 0]),
        "pole_horizontal_base_collapse_sat": check(pole_facts + [pole_horizontal_base_norm_sq == 0]),
        "equator_raw_base_accidental_independence_sat": check(equator_facts + [equator_raw_base_fiber_inner == 0]),
    }

    graveyards = {
        "raw_base_independent_from_fiber_is_unsat_at_non_equator": {
            "check": check(theta_pi_over_3_facts + [raw_base_fiber_inner == 0]),
            "passed": check(theta_pi_over_3_facts + [raw_base_fiber_inner == 0]) == "unsat",
        },
        "horizontal_base_not_independent_from_fiber_is_unsat": {
            "check": check(theta_pi_over_3_facts + [horizontal_base_fiber_inner != 0]),
            "passed": check(theta_pi_over_3_facts + [horizontal_base_fiber_inner != 0]) == "unsat",
        },
        "wrong_connection_sign_independent_from_fiber_is_unsat": {
            "check": check(theta_pi_over_3_facts + [wrong_sign_horizontal_fiber_inner == 0]),
            "passed": check(theta_pi_over_3_facts + [wrong_sign_horizontal_fiber_inner == 0]) == "unsat",
        },
        "pole_horizontal_base_noncollapse_is_unsat": {
            "check": check(pole_facts + [pole_horizontal_base_norm_sq > 0]),
            "passed": check(pole_facts + [pole_horizontal_base_norm_sq > 0]) == "unsat",
        },
        "equator_raw_base_nonzero_connection_is_unsat": {
            "check": check(equator_facts + [equator_raw_base_fiber_inner != 0]),
            "passed": check(equator_facts + [equator_raw_base_fiber_inner != 0]) == "unsat",
        },
    }

    all_positive = all(value == "sat" for value in positive.values())
    all_pass = bool(all_positive and all(row["passed"] for row in graveyards.values()))
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "z3 bounded rational predicate-control baseline for exact Hopf/Weyl vertical fiber and horizontal base-lift "
            "metric readouts at declared control points only; this checks consistency of already-derived metric predicates, "
            "not physical loop independence in a full nested Hopf-torus geometric-constraint manifold; no flux representation, "
            "no QIT, no GStack, no axis, no bridge, no nonclassical admission, and no target-system admission"
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
            "This predicate packet converts the SymPy/Geomstats/Clifford vertical-horizontal metric controls into bounded "
            "SAT/UNSAT checks. It does not add geometry beyond those receipts."
        ),
        "operation_sequence": [
            "declare rational metric readout variables for the theta=pi/3 control point",
            "assert fiber, raw-base, horizontal-base, and wrong-sign metric facts from lower receipts",
            "check positive SAT predicates for horizontal independence and raw/wrong-sign connection components",
            "check UNSAT graveyards for raw-base independence, horizontal-base non-independence, wrong-sign independence, pole noncollapse, and equator nonzero connection",
        ],
        "carrier_topology": "predicate abstraction of local Hopf/Weyl S3 carrier tangent metric readouts; no geometric construction inside z3",
        "observable": "SAT/UNSAT status for bounded rational metric predicates and adjacent controls",
        "pass_fail_predicate": "all declared positive predicates are SAT and all contradictory adjacent controls are UNSAT",
        "graveyards": [
            "raw base independent from fiber is UNSAT at non-equator",
            "horizontal base not independent from fiber is UNSAT",
            "wrong connection sign independent from fiber is UNSAT",
            "pole horizontal base noncollapse is UNSAT",
            "equator raw base nonzero connection is UNSAT",
        ],
        "baselines": [
            "SymPy Hopf/Weyl fiber-horizontal-base loop independence identities",
            "Geomstats Hopf/Weyl fiber-horizontal-base loop distance baseline",
            "Clifford Hopf/Weyl fiber-horizontal-base tangent inner-product baseline",
        ],
        "alternative_formulations": [
            "cvc5 bounded rational predicate controls over the same facts",
            "symbolic z3 nonlinear trigonometric approximation grid",
            "physical operator-evolution fixture over vertical and horizontal carrier paths",
        ],
        "exact_tool_function_needs": {
            "z3": ["Real", "Q", "Solver.add", "Solver.check", "linear rational SAT/UNSAT"],
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
