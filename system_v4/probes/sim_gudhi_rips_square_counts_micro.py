#!/usr/bin/env python3
"""GUDHI RipsComplex square simplex-count micro probe.

Tool-stage scope:
  - one tool: GUDHI
  - one API surface: RipsComplex(points=...).create_simplex_tree(max_dimension=2)
  - one tiny claim: a pinned four-point unit square has the expected
    Vietoris-Rips simplex counts at side, diagonal, and below-side thresholds.

This is a tool-lego fit probe over one finite fixture. It does not promote a
lego, coupling, bridge, axis, GStack, QIT, or nonclassical claim.
"""

import json
import math
import os

import gudhi


classification = "tool_lego_fit_probe"
NAME = "sim_gudhi_rips_square_counts_micro"
PROBE_FAMILY = "gudhi_rips_square_simplex_counts_micro"
CONSTRAINT_SET = "finite_four_point_square_rips_simplex_count_thresholds"

SQUARE_POINTS = [
    [0.0, 0.0],
    [1.0, 0.0],
    [1.0, 1.0],
    [0.0, 1.0],
]

_NOT_USED_REASON = (
    "not used: this micro probe isolates GUDHI RipsComplex simplex-count "
    "readout on a pinned four-point square; cross-tool coupling and downstream "
    "promotion are out of scope."
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
            "GUDHI is load-bearing: RipsComplex and create_simplex_tree "
            "materialize the finite square filtration whose per-dimension "
            "simplex counts decide this bounded receipt."
        ),
    },
}

TOOL_INTEGRATION_DEPTH = {tool: None for tool in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["gudhi"] = "load_bearing"


def _rips_tree(max_edge_length):
    rips = gudhi.RipsComplex(points=SQUARE_POINTS, max_edge_length=max_edge_length)
    return rips.create_simplex_tree(max_dimension=2)


def _simplex_counts_by_dimension(st):
    counts = {}
    for simplex, _filtration in st.get_filtration():
        dim = len(simplex) - 1
        counts[dim] = counts.get(dim, 0) + 1
    return counts


def _filtration_rows(st):
    return [
        {"simplex": list(simplex), "filtration": float(filtration)}
        for simplex, filtration in st.get_filtration()
    ]


def _count_readout(max_edge_length):
    st = _rips_tree(max_edge_length)
    counts = _simplex_counts_by_dimension(st)
    return {
        "max_edge_length": float(max_edge_length),
        "counts_by_dimension": counts,
        "total_simplices": int(st.num_simplices()),
        "filtration_rows": _filtration_rows(st),
    }


def run_positive_tests():
    readout = _count_readout(max_edge_length=1.5)
    expected = {0: 4, 1: 6, 2: 4}

    return {
        "square_diagonal_threshold_admits_complete_2_skeleton": {
            "passed": (
                readout["counts_by_dimension"] == expected
                and readout["total_simplices"] == 14
            ),
            "expected": (
                "four vertices, six edges, and four 2-simplices for the "
                "unit square once side and diagonal distances are admitted"
            ),
            "carrier": "finite 4-point unit square in R2",
            "readout": readout,
            "admission_note": (
                "The pinned square fixture is admitted for this surface only "
                "when GUDHI materializes the expected finite Rips 2-skeleton."
            ),
        }
    }


def run_negative_tests():
    readout = _count_readout(max_edge_length=0.99)
    excluded_expected = {0: 4, 1: 6, 2: 4}

    return {
        "below_side_threshold_excludes_square_edge_skeleton": {
            "passed": (
                readout["counts_by_dimension"] != excluded_expected
                and readout["counts_by_dimension"] == {0: 4}
                and readout["total_simplices"] == 4
            ),
            "expected": (
                "below the unit side length, only the four vertices are "
                "admitted and the square edge skeleton is excluded"
            ),
            "carrier": "same finite 4-point unit square with threshold below side length",
            "readout": readout,
            "exclusion_note": (
                "This control excludes a hardcoded complete-graph count by "
                "holding the carrier fixed and moving only the Rips threshold."
            ),
        }
    }


def run_boundary_tests():
    side_readout = _count_readout(max_edge_length=1.0)
    diagonal_readout = _count_readout(max_edge_length=math.sqrt(2.0))

    return {
        "side_threshold_admits_cycle_without_2_simplices": {
            "passed": (
                side_readout["counts_by_dimension"] == {0: 4, 1: 4}
                and side_readout["total_simplices"] == 8
            ),
            "expected": "at side length, the square has four vertices and four side edges only",
            "carrier": "finite 4-point unit square at the side-length boundary",
            "readout": side_readout,
            "boundary_note": (
                "The side threshold is the entry boundary for the square edge "
                "cycle before diagonal edges and triangles are admitted."
            ),
        },
        "diagonal_threshold_admits_all_triangles": {
            "passed": (
                diagonal_readout["counts_by_dimension"] == {0: 4, 1: 6, 2: 4}
                and diagonal_readout["total_simplices"] == 14
            ),
            "expected": (
                "at diagonal length sqrt(2), all six edges and four "
                "2-simplices are admitted in the max-dimension-2 Rips complex"
            ),
            "carrier": "finite 4-point unit square at the diagonal boundary",
            "readout": diagonal_readout,
            "boundary_note": (
                "The diagonal threshold is the boundary where the finite "
                "Rips 2-skeleton reaches the complete square count."
            ),
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
            "Other RipsComplex point-cloud fixtures may survive; this micro receipt only covers the named four-point square simplex-count surface."
        ],
        "demotion_condition": (
            "Demote GUDHI for this surface if RipsComplex cannot materialize "
            "the pinned square counts {0:4, 1:6, 2:4} at diagonal threshold, "
            "if the below-side control admits edges, or if the side-threshold "
            "boundary does not report exactly four edges and no 2-simplices."
        ),
        "out_of_scope": [
            "no persistence-bar claim",
            "no AlphaComplex or CubicalComplex coverage",
            "no manually inserted SimplexTree claim",
            "no TopoNetX cross-check",
            "no tool-tool coupling",
            "no lego promotion",
            "no bridge, axis, GStack, QIT, or nonclassical claim",
            "no proof of the whole GUDHI library",
        ],
        "criteria_checked": [
            "GUDHI RipsComplex four-point square diagonal-threshold simplex counts",
            "GUDHI RipsComplex below-side threshold exclusion of edge skeleton",
            "GUDHI RipsComplex side-threshold boundary simplex counts",
            "GUDHI RipsComplex diagonal-threshold boundary simplex counts",
        ],
        "operation_sequence": [
            "pin the finite carrier as four unit-square points in R2",
            "call gudhi.RipsComplex on the pinned carrier at one threshold",
            "call create_simplex_tree with max_dimension=2",
            "read get_filtration rows and num_simplices",
            "compare per-dimension counts against pinned expectations",
        ],
        "carrier_topology": {
            "carrier": "finite 4-point unit square point cloud in R2",
            "positive_fixture": "same square at max_edge_length 1.5",
            "graveyard_fixtures": [
                "same square below side threshold at max_edge_length 0.99",
            ],
            "boundary_fixtures": [
                "same square at side threshold max_edge_length 1.0",
                "same square at diagonal threshold max_edge_length sqrt(2)",
            ],
            "topological_dimension_checked": "simplex dimensions 0, 1, and 2 only",
        },
        "observable": {
            "primary": "per-dimension simplex counts returned by GUDHI SimplexTree filtration",
            "secondary": "total SimplexTree simplex count",
            "boundary_readout": "side threshold has no 2-simplices; diagonal threshold has four 2-simplices",
        },
        "pass_fail_predicate": {
            "pass": [
                "diagonal-threshold square count is {0:4, 1:6, 2:4} with total 14",
                "below-side control count is {0:4} with total 4",
                "side-threshold boundary count is {0:4, 1:4} with total 8",
            ],
            "fail": [
                "GUDHI RipsComplex returns a different square count at diagonal threshold",
                "below-side control admits any edge or 2-simplex",
                "side-threshold boundary admits any 2-simplex",
            ],
        },
        "graveyards": [
            {
                "name": "below_side_threshold_square",
                "change": "move only max_edge_length below the unit side length",
                "expected_exclusion": "the square edge skeleton is excluded",
            }
        ],
        "baselines": [
            {
                "name": "manual_unit_square_distance_expectation",
                "role": "pinned finite-count baseline for the tiny fixture",
                "expected": "four side distances equal 1 and two diagonal distances equal sqrt(2)",
            }
        ],
        "tool_function_needs": [
            {
                "tool": "gudhi",
                "functions": [
                    "RipsComplex",
                    "RipsComplex.create_simplex_tree",
                    "SimplexTree.get_filtration",
                    "SimplexTree.num_simplices",
                ],
                "depth": "load_bearing",
            }
        ],
        "ledger_loopback": {
            "tool_depth_row": "gudhi:RipsComplex.create_simplex_tree:square_simplex_counts",
            "threshold_context": "shallow-tool checker threshold is >=10 load_bearing receipts for gudhi",
            "ledger_action_if_runner_receipt_later_exists": "count only as one bounded load_bearing GUDHI RipsComplex square-count receipt after runner result reconciliation",
        },
        "summary": {
            "passed": sum(1 for test in flat_tests if test.get("passed")),
            "total": len(flat_tests),
            "classification": "tool_lego_fit_probe",
            "promotion_allowed": False,
            "claim": (
                "GUDHI RipsComplex materializes the expected finite simplex "
                "counts for one pinned four-point square fixture."
            ),
            "one_variable": "only the GUDHI RipsComplex simplex-tree count behavior is under test",
        },
        "claim_ceiling": "tool_lego_fit_probe_only",
        "next_lego_target": "minimal finite topology fixture for GUDHI RipsComplex simplex-count readout",
        "promotion_condition": (
            "promotion_allowed is false; any downstream use requires a later "
            "runner-written result JSON, queue reconciliation, and stage-gate "
            "admission naming this exact surface"
        ),
        "blocked_until": (
            "blocked from topology, bridge, axis, GStack, QIT, and nonclassical "
            "promotion until a downstream queue row declares the parent receipt "
            "use and satisfies strict runner admission"
        ),
        "all_pass": all_pass,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Summary: {results['summary']['passed']}/{results['summary']['total']} admitted")

    if not all_pass:
        raise SystemExit(1)
