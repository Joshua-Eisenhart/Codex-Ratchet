#!/usr/bin/env python3
"""GUDHI SimplexTree dimension and filtration invariant micro probe.

Tool-stage scope:
  - one tool: GUDHI
  - one API surface: SimplexTree insertion, dimension, and filtration readouts
  - one tiny claim: a finite filtered simplex carrier is admissible only when
    GUDHI reports the expected top dimension and face-before-coface filtration
    invariants after manual insertion.

This is a tool-lego fit probe. It does not promote a lego, coupling, bridge,
axis, nonclassical, or whole-topology claim.
"""

import json
import math
import os

import gudhi

from receipt_boundary import apply_default_receipt_boundary


classification = "tool_lego_fit_probe"
NAME = "sim_gudhi_simplex_dimension_filtration_micro"
PROBE_FAMILY = "gudhi_simplex_tree_dimension_filtration_micro"
CONSTRAINT_SET = "manual_simplex_tree_dimension_and_filtration_invariants"
SURFACE = "gudhi.SimplexTree insertion/dimension/filtration invariants"
CARRIER = "finite filtered 2-simplex carrier on vertices {0,1,2}"
LEDGER_LOOPBACK = (
    "tool_depth:gudhi:SimplexTree insertion/dimension/filtration invariants; "
    "feeds the shallow-tool checker threshold >=10 load-bearing receipts for gudhi"
)

_NOT_USED_REASON = (
    "not used: this micro probe isolates one GUDHI SimplexTree "
    "insertion/dimension/filtration surface; cross-tool coupling, runner "
    "execution, and promotion are out of scope."
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
            "GUDHI is load-bearing: SimplexTree.insert, dimension, "
            "filtration, get_filtration, and make_filtration_non_decreasing "
            "supply the bounded invariant verdicts."
        ),
    },
}

TOOL_INTEGRATION_DEPTH = {tool: None for tool in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["gudhi"] = "load_bearing"


def _sorted_rows(simplex_tree):
    return [
        {"simplex": list(simplex), "filtration": float(filtration)}
        for simplex, filtration in simplex_tree.get_filtration()
    ]


def _count_by_dimension(simplex_tree):
    counts = {}
    for simplex, _filtration in simplex_tree.get_filtration():
        dim = len(simplex) - 1
        counts[dim] = counts.get(dim, 0) + 1
    return counts


def _faces(simplex):
    if len(simplex) <= 1:
        return []
    return [list(simplex[:index] + simplex[index + 1:]) for index in range(len(simplex))]


def _face_filtration_invariants(simplex_tree):
    rows = _sorted_rows(simplex_tree)
    filtration_by_simplex = {
        tuple(row["simplex"]): row["filtration"]
        for row in rows
    }
    checks = []
    for simplex, filtration in filtration_by_simplex.items():
        for face in _faces(list(simplex)):
            face_filtration = filtration_by_simplex[tuple(face)]
            checks.append(
                {
                    "simplex": list(simplex),
                    "face": face,
                    "simplex_filtration": filtration,
                    "face_filtration": face_filtration,
                    "admitted": face_filtration <= filtration + 1e-12,
                }
            )
    return checks


def _full_2_simplex():
    simplex_tree = gudhi.SimplexTree()
    for vertex in ([0], [1], [2]):
        simplex_tree.insert(vertex, filtration=0.0)
    for edge in ([0, 1], [1, 2], [0, 2]):
        simplex_tree.insert(edge, filtration=0.5)
    simplex_tree.insert([0, 1, 2], filtration=1.0)
    simplex_tree.make_filtration_non_decreasing()
    return simplex_tree


def _edge_only_carrier():
    simplex_tree = gudhi.SimplexTree()
    simplex_tree.insert([0], filtration=0.0)
    simplex_tree.insert([1], filtration=0.0)
    simplex_tree.insert([0, 1], filtration=0.5)
    simplex_tree.make_filtration_non_decreasing()
    return simplex_tree


def _singleton_carrier():
    simplex_tree = gudhi.SimplexTree()
    simplex_tree.insert([0], filtration=0.0)
    simplex_tree.make_filtration_non_decreasing()
    return simplex_tree


def run_positive_tests():
    simplex_tree = _full_2_simplex()
    rows = _sorted_rows(simplex_tree)
    face_checks = _face_filtration_invariants(simplex_tree)
    counts = _count_by_dimension(simplex_tree)

    return {
        "filtered_2_simplex_reports_dimension_and_counts": {
            "passed": simplex_tree.dimension() == 2 and counts == {0: 3, 1: 3, 2: 1},
            "expected": "top dimension 2 with 3 vertices, 3 edges, and 1 face",
            "dimension": simplex_tree.dimension(),
            "simplex_counts_by_dimension": counts,
            "admission_note": (
                "The finite 2-simplex carrier survived the SimplexTree "
                "dimension readout under the pinned insertion schedule."
            ),
        },
        "filtered_2_simplex_reports_pinned_filtration_values": {
            "passed": (
                math.isclose(float(simplex_tree.filtration([0])), 0.0)
                and math.isclose(float(simplex_tree.filtration([0, 1])), 0.5)
                and math.isclose(float(simplex_tree.filtration([0, 1, 2])), 1.0)
                and all(item["admitted"] for item in face_checks)
            ),
            "expected": "vertices at 0.0, edges at 0.5, face at 1.0, with every face filtration no larger than its coface",
            "filtration_rows": rows,
            "face_filtration_checks": face_checks,
        },
    }


def run_negative_tests():
    simplex_tree = _edge_only_carrier()
    rows = _sorted_rows(simplex_tree)
    counts = _count_by_dimension(simplex_tree)

    return {
        "edge_only_carrier_excluded_from_2_simplex_surface": {
            "passed": simplex_tree.dimension() == 1 and counts.get(2, 0) == 0,
            "expected": "edge-only carrier is dimension 1 and has no 2-simplex",
            "dimension": simplex_tree.dimension(),
            "simplex_counts_by_dimension": counts,
            "filtration_rows": rows,
            "exclusion_note": (
                "The edge-only fixture is inadmissible for the 2-simplex "
                "dimension/filtration surface, while remaining a valid lower "
                "dimensional SimplexTree carrier."
            ),
        },
        "edge_only_carrier_has_no_face_filtration_readout": {
            "passed": math.isinf(float(simplex_tree.filtration([0, 1, 2]))),
            "expected": "absent 2-simplex returns infinite filtration",
            "absent_face_filtration": float(simplex_tree.filtration([0, 1, 2])),
        },
    }


def run_boundary_tests():
    simplex_tree = _singleton_carrier()
    rows = _sorted_rows(simplex_tree)
    counts = _count_by_dimension(simplex_tree)
    face_checks = _face_filtration_invariants(simplex_tree)

    return {
        "singleton_boundary_reports_zero_dimension": {
            "passed": simplex_tree.dimension() == 0 and counts == {0: 1},
            "expected": "singleton carrier has top dimension 0",
            "dimension": simplex_tree.dimension(),
            "simplex_counts_by_dimension": counts,
            "filtration_rows": rows,
            "boundary_note": (
                "The minimal non-empty boundary fixture checks the lowest "
                "dimension admitted by this SimplexTree surface."
            ),
        },
        "singleton_boundary_has_vacuous_face_filtration_invariants": {
            "passed": face_checks == [] and math.isclose(float(simplex_tree.filtration([0])), 0.0),
            "expected": "no face/coface checks exist for a singleton and its vertex filtration is pinned",
            "face_filtration_checks": face_checks,
            "vertex_filtration": float(simplex_tree.filtration([0])),
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
        "surface": SURFACE,
        "one_variable": (
            "Only the GUDHI SimplexTree insertion/dimension/filtration behavior "
            "is uncertain; carrier fixtures, expected dimensions, and expected "
            "filtration values are pinned."
        ),
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "surviving_alternatives": [
            "Other finite filtered simplex carriers may be admissible; this micro probe covers only the named 2-simplex, edge-only, and singleton fixtures."
        ],
        "demotion_condition": (
            "Demote GUDHI for this surface if SimplexTree dimension readouts, "
            "simplex counts, absent-simplex filtration, or face-before-coface "
            "filtration invariants do not match the pinned finite fixtures."
        ),
        "out_of_scope": [
            "no persistence interval claim",
            "no point-cloud AlphaComplex or RipsComplex claim",
            "no TopoNetX cross-check",
            "no tool-tool coupling",
            "no bridge claim",
            "no axis claim",
            "no nonclassical admission",
            "no lego promotion",
        ],
        "criteria_checked": [
            "GUDHI SimplexTree insertion of a finite filtered 2-simplex carrier",
            "GUDHI SimplexTree.dimension top-dimension readout for 2D, 1D, and 0D fixtures",
            "GUDHI SimplexTree.filtration and get_filtration pinned-value readouts",
            "face-before-coface filtration invariant after make_filtration_non_decreasing",
        ],
        "operation_sequence": [
            "insert three vertices at filtration 0.0",
            "insert three edges at filtration 0.5",
            "insert one 2-simplex at filtration 1.0",
            "apply make_filtration_non_decreasing",
            "read dimension, simplex counts, filtration values, and face/coface inequalities",
        ],
        "carrier_topology": {
            "carrier": CARRIER,
            "positive_fixture": "finite filtered 2-simplex with vertices at 0.0, edges at 0.5, and face at 1.0",
            "negative_fixture": "finite filtered edge-only carrier with no 2-simplex",
            "boundary_fixture": "finite singleton 0-simplex carrier",
        },
        "observable": {
            "primary": "SimplexTree.dimension() equals the fixture top dimension",
            "secondary": "SimplexTree.filtration(simplex) matches pinned filtration values",
            "boundary_readout": "singleton reports dimension 0 and no face/coface checks",
        },
        "pass_fail_predicate": {
            "pass": [
                "2-simplex fixture reports dimension 2 and counts {0:3, 1:3, 2:1}",
                "vertices, edges, and face keep pinned filtration values 0.0, 0.5, and 1.0",
                "edge-only fixture reports dimension 1 and absent 2-simplex filtration infinity",
                "singleton fixture reports dimension 0 with only one vertex row",
            ],
            "fail": [
                "GUDHI reports the wrong top dimension for any pinned fixture",
                "GUDHI reports an unexpected finite filtration for the absent 2-simplex",
                "GUDHI returns a face filtration greater than a coface filtration after normalization",
            ],
        },
        "graveyards": [
            {
                "name": "edge_only_carrier",
                "change": "remove the 2-simplex face from the positive carrier",
                "expected_exclusion": "inadmissible for the 2-simplex dimension surface",
            }
        ],
        "baselines": [
            {
                "name": "manual_fixture_expectation",
                "role": "pinned finite carrier expectation",
                "expected": "top dimension and filtration values are fixed by the fixture schedule",
            }
        ],
        "alternative_formulations": [
            "manual boundary incidence table for the same 2-simplex carrier",
            "TopoNetX cell-complex representation of the same face/coface relation",
            "GUDHI persistence query layered later on top of this lower SimplexTree invariant receipt",
        ],
        "tool_function_needs": [
            {
                "tool": "gudhi",
                "functions": [
                    "SimplexTree.insert",
                    "SimplexTree.dimension",
                    "SimplexTree.filtration",
                    "SimplexTree.get_filtration",
                    "SimplexTree.make_filtration_non_decreasing",
                ],
                "depth": "load_bearing",
            }
        ],
        "ledger_loopback": LEDGER_LOOPBACK,
        "lego_coupling_target": [
            "cell_complex_geometry",
            "persistence_geometry",
        ],
        "summary": {
            "passed": sum(1 for test in flat_tests if test.get("passed")),
            "total": len(flat_tests),
            "promotion_allowed": False,
            "classification": "tool_lego_fit_probe",
            "claim": (
                "A finite filtered 2-simplex carrier survived the GUDHI "
                "SimplexTree insertion/dimension/filtration invariant checks "
                "only as pre-lego tool-depth evidence."
            ),
        },
        "all_pass": all_pass,
    }
    results = apply_default_receipt_boundary(
        results,
        source_name=NAME,
        target=(
            "Use as bounded GUDHI SimplexTree dimension/filtration function "
            "evidence before topology lego fit or coupling packets."
        ),
    )
    results["classification"] = classification
    results["summary"]["promotion_allowed"] = False
    results["claim_ceiling"] = (
        "tool_lego_fit_probe only; promotion_allowed=false; no bridge, "
        "GStack, axis, QIT, nonclassical admission, or lego promotion"
    )

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Summary: {results['summary']['passed']}/{results['summary']['total']} survived")

    if not all_pass:
        raise SystemExit(1)
