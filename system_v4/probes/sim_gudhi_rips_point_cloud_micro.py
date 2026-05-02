#!/usr/bin/env python3
"""GUDHI RipsComplex point-cloud persistence micro probe.

Tool-stage scope:
  - one tool: GUDHI
  - one API surface: RipsComplex(points=...).create_simplex_tree(...).persistence()
  - one tiny claim: a four-point square in a Vietoris-Rips filtration exposes
    a finite H1 bar that dies when diagonals/triangles enter.

This is pre-lego evidence. It does not promote a lego, coupling, bridge, or
whole-topology claim.
"""

import json
import math
import os
import sys

import gudhi

classification = "canonical"
NAME = "sim_gudhi_rips_point_cloud_micro"
PROBE_FAMILY = "gudhi_rips_point_cloud_persistence_micro"
CONSTRAINT_SET = "rips_complex_square_h1_birth_death_boundary"

_NOT_USED_REASON = (
    "not used: this micro probe isolates GUDHI RipsComplex point-cloud "
    "persistence only; cross-tool coupling and lego promotion are out of scope."
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
            "GUDHI is load-bearing: RipsComplex builds the point-cloud "
            "filtration, create_simplex_tree materializes simplices, and "
            "persistence reports the H1 birth/death verdicts."
        ),
    },
}

TOOL_INTEGRATION_DEPTH = {tool: None for tool in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["gudhi"] = "load_bearing"

SQUARE_POINTS = [
    [0.0, 0.0],
    [1.0, 0.0],
    [1.0, 1.0],
    [0.0, 1.0],
]
TRIANGLE_POINTS = [
    [0.0, 0.0],
    [1.0, 0.0],
    [0.5, math.sqrt(3.0) / 2.0],
]
SINGLETON_POINT = [[0.0, 0.0]]


def _rips_tree(points, max_edge_length, max_dimension=2):
    rips = gudhi.RipsComplex(points=points, max_edge_length=max_edge_length)
    st = rips.create_simplex_tree(max_dimension=max_dimension)
    st.persistence(homology_coeff_field=2, min_persistence=0.0)
    return st


def _finite_lifetimes(intervals):
    return [
        float(death - birth)
        for birth, death in intervals
        if math.isfinite(float(death))
    ]


def _intervals_as_lists(intervals):
    return [[float(birth), float(death)] for birth, death in intervals]


def _filtration_rows(st):
    return [
        {"simplex": list(simplex), "filtration": float(filtration)}
        for simplex, filtration in st.get_filtration()
    ]


def _simplex_counts_by_dimension(st):
    counts = {}
    for simplex, _filtration in st.get_filtration():
        dim = len(simplex) - 1
        counts[dim] = counts.get(dim, 0) + 1
    return counts


def run_positive_tests():
    st = _rips_tree(SQUARE_POINTS, max_edge_length=1.5, max_dimension=2)
    h1_intervals = st.persistence_intervals_in_dimension(1)
    lifetimes = _finite_lifetimes(h1_intervals)
    birth, death = h1_intervals[0] if len(h1_intervals) == 1 else (None, None)
    expected_death = math.sqrt(2.0)

    return {
        "square_rips_has_one_finite_h1_bar": {
            "passed": (
                len(h1_intervals) == 1
                and abs(float(birth) - 1.0) <= 1e-12
                and abs(float(death) - expected_death) <= 1e-12
            ),
            "expected": "one H1 interval born at side length 1 and killed at diagonal length sqrt(2)",
            "h1_intervals": _intervals_as_lists(h1_intervals),
            "expected_birth": 1.0,
            "expected_death": expected_death,
            "longest_h1_lifetime": max(lifetimes) if lifetimes else 0.0,
            "admission_note": (
                "The square's side edges create a 1-cycle at filtration 1.0; "
                "diagonals enter at sqrt(2), creating triangles that kill it."
            ),
        },
        "square_rips_contains_triangles_at_killing_threshold": {
            "passed": _simplex_counts_by_dimension(st).get(2, 0) > 0,
            "expected": "2-simplices exist once diagonals enter the Rips filtration",
            "simplex_counts_by_dimension": _simplex_counts_by_dimension(st),
        },
    }


def run_negative_tests():
    st = _rips_tree(TRIANGLE_POINTS, max_edge_length=1.1, max_dimension=2)
    h1_intervals = st.persistence_intervals_in_dimension(1)
    lifetimes = _finite_lifetimes(h1_intervals)

    return {
        "equilateral_triangle_filled_at_threshold_excludes_h1": {
            "passed": len(h1_intervals) == 0 or max(lifetimes, default=0.0) == 0.0,
            "expected": "no positive-length H1 interval for a filled three-point Rips triangle",
            "h1_intervals": _intervals_as_lists(h1_intervals),
            "longest_h1_lifetime": max(lifetimes) if lifetimes else 0.0,
            "exclusion_note": (
                "All three edges and the 2-simplex are born at the same side "
                "length, so the would-be loop is filled at birth."
            ),
        },
        "triangle_rips_materializes_one_filled_face": {
            "passed": _simplex_counts_by_dimension(st).get(2, 0) == 1,
            "expected": "the three-point triangle has exactly one 2-simplex",
            "simplex_counts_by_dimension": _simplex_counts_by_dimension(st),
        },
    }


def run_boundary_tests():
    side_only = _rips_tree(SQUARE_POINTS, max_edge_length=1.0, max_dimension=2)
    side_only_h1 = side_only.persistence_intervals_in_dimension(1)
    side_only_filtration = _filtration_rows(side_only)

    singleton = _rips_tree(SINGLETON_POINT, max_edge_length=0.01, max_dimension=2)
    singleton_h1 = singleton.persistence_intervals_in_dimension(1)
    singleton_filtration = _filtration_rows(singleton)

    finite_filtration_values = all(
        math.isfinite(row["filtration"]) for row in side_only_filtration + singleton_filtration
    )

    return {
        "side_threshold_square_has_only_edges_before_diagonals": {
            "passed": (
                finite_filtration_values
                and _simplex_counts_by_dimension(side_only).get(1, 0) == 4
                and _simplex_counts_by_dimension(side_only).get(2, 0) == 0
                and max(row["filtration"] for row in side_only_filtration) == 1.0
            ),
            "expected": "at side-length cutoff only finite vertices and side edges have entered",
            "h1_intervals": _intervals_as_lists(side_only_h1),
            "simplex_counts_by_dimension": _simplex_counts_by_dimension(side_only),
            "boundary_note": (
                "This truncated side-only fixture checks the entry boundary for "
                "edges and absence of triangles; finite H1 death is checked in "
                "the positive square fixture with diagonals admitted."
            ),
        },
        "finite_simplices_and_singleton_no_h1": {
            "passed": (
                finite_filtration_values
                and len(singleton_h1) == 0
                and _simplex_counts_by_dimension(singleton) == {0: 1}
            ),
            "expected": "finite filtration values and no H1 for a singleton at tiny threshold",
            "singleton_h1_intervals": _intervals_as_lists(singleton_h1),
            "singleton_filtration": singleton_filtration,
            "side_only_filtration_count": len(side_only_filtration),
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
            "Other point-cloud filtrations may survive; this micro receipt only covers the named RipsComplex persistence surface.",
            "Manual SimplexTree persistence remains a separate GUDHI surface and is not retested here.",
        ],
        "demotion_condition": (
            "Demote GUDHI for this RipsComplex surface if it cannot build the "
            "tiny point-cloud simplex tree, if square H1 is not born at side "
            "length 1.0 and killed at diagonal length sqrt(2), if the filled "
            "three-point triangle reports a positive-length H1 bar, or if "
            "finite singleton/boundary filtrations cannot be reported."
        ),
        "out_of_scope": [
            "no manually inserted SimplexTree claim",
            "no AlphaComplex or CubicalComplex coverage",
            "no persistent cohomology claim",
            "no TopoNetX cross-check",
            "no lego promotion",
            "no tool-tool coupling",
            "no Hopf, bridge, or axis-level topology claim",
            "no proof of the whole GUDHI library",
        ],
        "criteria_checked": [
            "GUDHI RipsComplex square H1 birth at side length",
            "GUDHI RipsComplex square H1 death at diagonal/triangle threshold",
            "GUDHI RipsComplex filled triangle H1 exclusion",
            "GUDHI RipsComplex boundary finite simplices and singleton no-H1 check",
        ],
        "summary": {
            "passed": sum(1 for test in flat_tests if test.get("passed")),
            "total": len(flat_tests),
        },
        "all_pass": all_pass,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Summary: {results['summary']['passed']}/{results['summary']['total']} passed")
    sys.exit(0 if all_pass else 1)
