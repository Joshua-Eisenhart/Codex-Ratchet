#!/usr/bin/env python3
"""GUDHI AlphaComplex point-cloud persistence micro probe.

Tool-stage scope:
  - one tool: GUDHI
  - one API surface: AlphaComplex(points=...).create_simplex_tree(...).persistence()
  - one tiny claim: a four-point square AlphaComplex exposes a finite H1 bar
    that is born at side-edge alpha square 0.25 and killed at triangle alpha
    square 0.5.

This is pre-lego evidence. It does not promote a lego, coupling, bridge, axis,
or whole-topology claim.
"""

import json
import math
import os

import gudhi

classification = "canonical"
NAME = "sim_gudhi_alpha_complex_micro"
SCOPE = "tool_function_micro_only"
PROBE_FAMILY = "gudhi_alpha_complex_point_cloud_persistence_micro"
CONSTRAINT_SET = "alpha_complex_square_h1_birth_death_boundary"

_NOT_USED_REASON = (
    "not used: this micro probe isolates GUDHI AlphaComplex point-cloud "
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
            "GUDHI is load-bearing: AlphaComplex builds the point-cloud alpha "
            "filtration, create_simplex_tree materializes the alpha complex, "
            "and persistence reports the H1 birth/death verdicts."
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
CENTERED_SQUARE_POINTS = [
    [0.0, 0.0],
    [1.0, 0.0],
    [1.0, 1.0],
    [0.0, 1.0],
    [0.5, 0.5],
]
TWO_POINTS = [
    [0.0, 0.0],
    [1.0, 0.0],
]
SINGLETON_POINT = [[0.0, 0.0]]


def _alpha_tree(points, max_alpha_square=None):
    alpha = gudhi.AlphaComplex(points=points)
    if max_alpha_square is None:
        st = alpha.create_simplex_tree()
    else:
        st = alpha.create_simplex_tree(max_alpha_square=max_alpha_square)
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
    st = _alpha_tree(SQUARE_POINTS)
    h1_intervals = st.persistence_intervals_in_dimension(1)
    lifetimes = _finite_lifetimes(h1_intervals)
    birth, death = h1_intervals[0] if len(h1_intervals) == 1 else (None, None)

    return {
        "square_alpha_has_one_finite_h1_bar": {
            "passed": (
                len(h1_intervals) == 1
                and abs(float(birth) - 0.25) <= 1e-12
                and abs(float(death) - 0.5) <= 1e-12
            ),
            "expected": "one H1 interval born at side-edge alpha square 0.25 and killed at triangle alpha square 0.5",
            "h1_intervals": _intervals_as_lists(h1_intervals),
            "expected_birth": 0.25,
            "expected_death": 0.5,
            "longest_h1_lifetime": max(lifetimes) if lifetimes else 0.0,
            "admission_note": (
                "The square side edges create a 1-cycle at alpha square 0.25; "
                "a Delaunay diagonal and adjacent triangles enter at alpha "
                "square 0.5 and kill it."
            ),
        },
        "square_alpha_materializes_killing_triangles": {
            "passed": _simplex_counts_by_dimension(st).get(2, 0) == 2,
            "expected": "two 2-simplices exist at the H1 killing threshold",
            "simplex_counts_by_dimension": _simplex_counts_by_dimension(st),
            "filtration": _filtration_rows(st),
        },
    }


def run_negative_tests():
    st = _alpha_tree(CENTERED_SQUARE_POINTS)
    h1_intervals = st.persistence_intervals_in_dimension(1)
    lifetimes = _finite_lifetimes(h1_intervals)

    return {
        "center_point_fills_square_excludes_h1_bar": {
            "passed": len(h1_intervals) == 0 or max(lifetimes, default=0.0) == 0.0,
            "expected": "no positive-length H1 interval when the center point fills the square before the outer cycle survives",
            "h1_intervals": _intervals_as_lists(h1_intervals),
            "longest_h1_lifetime": max(lifetimes) if lifetimes else 0.0,
            "exclusion_note": (
                "The center point connects to all corners at alpha square "
                "0.125, so the square does not admit the same persistent "
                "outer H1 bar as the four-corner fixture."
            ),
        },
        "centered_square_uses_center_edges_before_outer_cycle": {
            "passed": (
                _simplex_counts_by_dimension(st).get(0, 0) == 5
                and any(
                    row["simplex"] in ([0, 4], [1, 4], [2, 4], [3, 4])
                    and abs(row["filtration"] - 0.125) <= 1e-12
                    for row in _filtration_rows(st)
                )
            ),
            "expected": "center-corner edges enter at alpha square 0.125",
            "simplex_counts_by_dimension": _simplex_counts_by_dimension(st),
            "filtration": _filtration_rows(st),
        },
    }


def run_boundary_tests():
    side_threshold = _alpha_tree(SQUARE_POINTS, max_alpha_square=0.25)
    side_filtration = _filtration_rows(side_threshold)

    pair = _alpha_tree(TWO_POINTS)
    pair_h0 = pair.persistence_intervals_in_dimension(0)

    singleton = _alpha_tree(SINGLETON_POINT)
    singleton_h1 = singleton.persistence_intervals_in_dimension(1)
    singleton_filtration = _filtration_rows(singleton)

    finite_filtration_values = all(
        math.isfinite(row["filtration"])
        for row in side_filtration + _filtration_rows(pair) + singleton_filtration
    )

    return {
        "side_alpha_boundary_has_edges_before_triangles": {
            "passed": (
                finite_filtration_values
                and _simplex_counts_by_dimension(side_threshold).get(1, 0) == 4
                and _simplex_counts_by_dimension(side_threshold).get(2, 0) == 0
                and max(row["filtration"] for row in side_filtration) == 0.25
            ),
            "expected": "at alpha square 0.25 the square has only vertices and side edges",
            "simplex_counts_by_dimension": _simplex_counts_by_dimension(side_threshold),
            "filtration": side_filtration,
            "boundary_note": (
                "This cutoff fixture checks the edge-entry boundary and absence "
                "of triangles; the full square fixture checks the finite H1 death."
            ),
        },
        "two_point_and_singleton_boundaries_report_minimal_persistence": {
            "passed": (
                finite_filtration_values
                and len(pair_h0) == 2
                and any(abs(float(death) - 0.25) <= 1e-12 for _birth, death in pair_h0)
                and len(singleton_h1) == 0
                and _simplex_counts_by_dimension(singleton) == {0: 1}
            ),
            "expected": "two points merge at alpha square 0.25 and a singleton exposes no H1",
            "pair_h0_intervals": _intervals_as_lists(pair_h0),
            "singleton_h1_intervals": _intervals_as_lists(singleton_h1),
            "singleton_filtration": singleton_filtration,
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
        "scope": SCOPE,
        "probe_family": PROBE_FAMILY,
        "constraint_set": CONSTRAINT_SET,
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "surviving_alternatives": [
            "Other alpha-complex point-cloud fixtures may survive; this micro receipt only covers the named AlphaComplex persistence surface.",
            "RipsComplex and manual SimplexTree persistence remain separate GUDHI surfaces and are not retested here.",
        ],
        "claim_ceiling": "tool_function_micro_only",
        "next_lego_target": (
            "minimal AlphaComplex point-cloud fixture before topology coupling "
            "or graph-cell promotion"
        ),
        "promotion_condition": (
            "requires a later admitted downstream row that names this exact "
            "function receipt and passes strict runner admission; this MICRO "
            "row does not promote any lego"
        ),
        "blocked_until": (
            "blocked until a downstream queue row declares the exact topology "
            "target, parent receipt use, and active stage gate for promotion"
        ),
        "demotion_condition": (
            "Demote GUDHI for this AlphaComplex surface if it cannot build the "
            "tiny point-cloud simplex tree, if square H1 is not born at alpha "
            "square 0.25 and killed at alpha square 0.5, if the centered square "
            "reports a positive-length H1 bar, or if finite singleton/boundary "
            "filtrations cannot be reported."
        ),
        "out_of_scope": [
            "no RipsComplex claim",
            "no manually inserted SimplexTree claim",
            "no CubicalComplex coverage",
            "no persistent cohomology claim",
            "no TopoNetX cross-check",
            "no lego promotion",
            "no tool-tool coupling",
            "no Hopf, bridge, or axis-level topology claim",
            "no proof of the whole GUDHI library",
        ],
        "criteria_checked": [
            "GUDHI AlphaComplex square H1 birth at side-edge alpha square",
            "GUDHI AlphaComplex square H1 death at triangle alpha square",
            "GUDHI AlphaComplex centered-square H1 exclusion",
            "GUDHI AlphaComplex finite boundary and singleton no-H1 check",
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

    if not all_pass:
        raise SystemExit(1)
