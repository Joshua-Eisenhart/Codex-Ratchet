#!/usr/bin/env python3
"""GUDHI SimplexTree persistence micro probe.

Tool-stage scope:
  - one tool: GUDHI
  - one API surface: SimplexTree manual insertion plus persistence queries
  - one tiny claim: GUDHI can distinguish a delayed-filled 1-cycle from a
    trivially filled triangle and report the boundary filtration transition.

This is pre-lego evidence. It does not promote a lego, coupling, bridge, or
stack claim.
"""

import json
import math
import os

import gudhi

from receipt_boundary import apply_default_receipt_boundary

classification = "canonical"
NAME = "sim_gudhi_simplex_persistence_micro"
PROBE_FAMILY = "gudhi_simplex_tree_persistence_micro"
CONSTRAINT_SET = "manual_simplex_tree_h1_birth_death_boundary"

_NOT_USED_REASON = (
    "not used: this micro probe isolates GUDHI SimplexTree persistence only; "
    "cross-tool coupling and lego promotion are out of scope."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "pyg": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "z3": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "cvc5": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "sympy": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "clifford": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "e3nn": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "xgi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "toponetx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": (
            "GUDHI is load-bearing: SimplexTree.insert, persistence, "
            "persistence_intervals_in_dimension, and persistent_betti_numbers "
            "produce the H1 birth/death and boundary verdicts."
        ),
    }
}

TOOL_INTEGRATION_DEPTH = {tool: None for tool in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["gudhi"] = "load_bearing"


def _delayed_filled_triangle():
    """Hollow triangle at t=0, filled by a 2-simplex at t=1."""
    st = gudhi.SimplexTree()
    for vertex in ([0], [1], [2]):
        st.insert(vertex, filtration=0.0)
    for edge in ([0, 1], [1, 2], [0, 2]):
        st.insert(edge, filtration=0.0)
    st.insert([0, 1, 2], filtration=1.0)
    st.make_filtration_non_decreasing()
    st.persistence(homology_coeff_field=2, min_persistence=0.0)
    return st


def _immediately_filled_triangle():
    """Triangle whose face exists at the same filtration as its boundary."""
    st = gudhi.SimplexTree()
    st.insert([0, 1, 2], filtration=0.0)
    st.make_filtration_non_decreasing()
    st.persistence(homology_coeff_field=2, min_persistence=0.0)
    return st


def _single_vertex():
    st = gudhi.SimplexTree()
    st.insert([0], filtration=0.0)
    st.persistence(homology_coeff_field=2, min_persistence=0.0)
    return st


def _finite_lifetimes(intervals):
    return [
        float(death - birth)
        for birth, death in intervals
        if math.isfinite(float(death))
    ]


def _persistent_betti(st, value):
    return list(st.persistent_betti_numbers(from_value=value, to_value=value))


def run_positive_tests():
    st = _delayed_filled_triangle()
    h1_intervals = st.persistence_intervals_in_dimension(1)
    lifetimes = _finite_lifetimes(h1_intervals)
    longest = max(lifetimes) if lifetimes else 0.0
    betti_mid = _persistent_betti(st, 0.5)

    return {
        "delayed_filled_triangle_has_one_h1_bar": {
            "passed": len(h1_intervals) == 1 and abs(longest - 1.0) <= 1e-12,
            "expected": "one finite H1 interval with lifetime 1.0",
            "h1_intervals": h1_intervals.tolist(),
            "longest_h1_lifetime": longest,
            "admission_note": (
                "The edge cycle survives between its boundary completion at "
                "filtration 0 and face filling at filtration 1."
            ),
        },
        "mid_filtration_admits_h1": {
            "passed": len(betti_mid) >= 2 and betti_mid[0] == 1 and betti_mid[1] == 1,
            "expected": "persistent Betti at t=0.5 is beta0=1, beta1=1",
            "persistent_betti_at_0_5": betti_mid,
        },
    }


def run_negative_tests():
    st = _immediately_filled_triangle()
    h1_intervals = st.persistence_intervals_in_dimension(1)
    lifetimes = _finite_lifetimes(h1_intervals)
    longest = max(lifetimes) if lifetimes else 0.0
    betti_mid = _persistent_betti(st, 0.5)

    return {
        "immediately_filled_triangle_excludes_h1_bar": {
            "passed": len(h1_intervals) == 0 or longest == 0.0,
            "expected": "no positive-length H1 interval",
            "h1_intervals": h1_intervals.tolist(),
            "longest_h1_lifetime": longest,
            "exclusion_note": (
                "A face born with its boundary kills the would-be cycle at "
                "birth, so no persistent H1 class survives."
            ),
        },
        "filled_triangle_mid_filtration_has_no_h1": {
            "passed": len(betti_mid) < 2 or betti_mid[1] == 0,
            "expected": "persistent Betti at t=0.5 has beta1=0",
            "persistent_betti_at_0_5": betti_mid,
        },
    }


def run_boundary_tests():
    delayed = _delayed_filled_triangle()
    before_fill = _persistent_betti(delayed, 0.999)
    after_fill = _persistent_betti(delayed, 1.001)

    singleton = _single_vertex()
    singleton_h1 = singleton.persistence_intervals_in_dimension(1)

    return {
        "boundary_transition_at_face_filtration": {
            "passed": (
                len(before_fill) >= 2
                and before_fill[1] == 1
                and (len(after_fill) < 2 or after_fill[1] == 0)
            ),
            "expected": "H1 exists just before t=1 and is gone just after t=1",
            "persistent_betti_before_1": before_fill,
            "persistent_betti_after_1": after_fill,
            "boundary_note": "The face filtration value is the exact H1 death boundary.",
        },
        "single_vertex_has_no_h1_surface": {
            "passed": len(singleton_h1) == 0,
            "expected": "single 0-simplex exposes no H1 intervals",
            "h1_intervals": singleton_h1.tolist(),
        },
    }


def _flatten_sections(*sections):
    flat = []
    for section in sections:
        for value in section.values():
            if isinstance(value, dict) and "passed" in value:
                flat.append(value)
    return flat


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    flat_tests = _flatten_sections(positive, negative, boundary)
    all_pass = all(test.get("passed") for test in flat_tests)

    results = {
        "name": NAME,
        "probe_family": PROBE_FAMILY,
        "constraint_set": CONSTRAINT_SET,
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "surviving_alternatives": [
            "Other manually filtered simplex fixtures may survive; this micro receipt only covers the named SimplexTree persistence surface."
        ],
        "demotion_condition": (
            "Demote GUDHI for this surface if SimplexTree persistence cannot "
            "report the delayed H1 interval, if persistent_betti_numbers misses "
            "the face-filtration transition, or if the immediately filled "
            "triangle reports a positive-length H1 bar."
        ),
        "out_of_scope": [
            "no point-cloud sampling claim",
            "no RipsComplex or AlphaComplex coverage",
            "no TopoNetX cross-check",
            "no lego promotion",
            "no tool-tool coupling",
            "no bridge claim",
            "no proof of the whole GUDHI library",
        ],
        "criteria_checked": [
            "GUDHI SimplexTree delayed H1 birth/death interval",
            "GUDHI SimplexTree immediate-fill H1 exclusion",
            "GUDHI persistent Betti boundary before and after face filtration",
        ],
        "operation_sequence": [
            "construct a filtered SimplexTree with three vertices and three boundary edges at filtration 0",
            "insert the filling 2-simplex at filtration 1",
            "make the filtration non-decreasing",
            "compute persistence over field 2",
            "read H1 intervals and persistent Betti values before, during, and after the face-filtration boundary",
        ],
        "carrier_topology": {
            "carrier": "finite filtered 2-dimensional simplicial complex",
            "positive_fixture": "one delayed-filled triangle with boundary at filtration 0 and face at filtration 1",
            "graveyard_fixtures": [
                "immediately filled triangle",
                "single 0-simplex",
            ],
            "topological_dimension_checked": "H1 only",
        },
        "observable": {
            "primary": "positive-length H1 interval lifetime",
            "secondary": "persistent Betti number beta1 at selected filtration values",
            "boundary_readout": "beta1 exists immediately before face filtration and is absent after it",
        },
        "pass_fail_predicate": {
            "pass": [
                "delayed-filled triangle has exactly one finite H1 interval with lifetime 1.0",
                "persistent Betti at filtration 0.5 reports beta0=1 and beta1=1",
                "beta1 is present before filtration 1.0 and absent after filtration 1.0",
                "single vertex has no H1 interval",
            ],
            "fail": [
                "GUDHI fails to report the delayed H1 interval",
                "immediately filled triangle reports a positive-length H1 interval",
                "persistent Betti readout misses the face-filtration boundary transition",
            ],
        },
        "graveyards": [
            {
                "name": "immediately_filled_triangle",
                "change": "move the filling 2-simplex to the same filtration as its boundary",
                "expected_death": "no positive-length H1 interval survives",
            },
            {
                "name": "single_vertex",
                "change": "remove all edges and faces",
                "expected_death": "no H1 surface exists",
            },
        ],
        "baselines": [
            {
                "name": "manual_interval_expectation",
                "role": "classical baseline for the tiny fixture",
                "expected": "H1 lifetime equals face_filtration minus boundary_filtration",
            }
        ],
        "alternative_formulations": [
            "RipsComplex construction on points chosen to induce the same delayed 1-cycle",
            "TopoNetX or NetworkX representation of the same boundary/fill incidence before GUDHI persistence",
            "manual boundary-matrix reduction for the same filtered triangle",
        ],
        "tool_function_needs": [
            {
                "tool": "gudhi",
                "functions": [
                    "SimplexTree.insert",
                    "SimplexTree.make_filtration_non_decreasing",
                    "SimplexTree.persistence",
                    "SimplexTree.persistence_intervals_in_dimension",
                    "SimplexTree.persistent_betti_numbers",
                ],
                "depth": "load_bearing",
            }
        ],
        "lego_coupling_target": [
            "persistence_geometry",
            "cell_complex_geometry",
        ],
        "summary": {
            "passed": sum(1 for test in flat_tests if test.get("passed")),
            "total": len(flat_tests),
        },
        "all_pass": all_pass,
    }
    results = apply_default_receipt_boundary(
        results,
        source_name="sim_gudhi_simplex_persistence_micro",
        target="Use as bounded GUDHI SimplexTree persistence function evidence before topology lego fit or coupling packets.",
    )

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Summary: {results['summary']['passed']}/{results['summary']['total']} passed")

    if not all_pass:
        raise SystemExit(1)
