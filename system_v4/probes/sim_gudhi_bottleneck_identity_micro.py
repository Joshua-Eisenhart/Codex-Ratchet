#!/usr/bin/env python3
"""GUDHI bottleneck-distance identity micro probe.

Tool-stage scope:
  - one tool: GUDHI
  - one API surface: gudhi.bottleneck_distance(diagram_a, diagram_b)
  - one tiny claim: a finite persistence diagram has bottleneck distance 0
    from itself, while a pinned shifted diagram is excluded from identity.

This is a tool-lego fit probe. It does not promote a lego, coupling, bridge,
axis, engine, or whole-topology claim.
"""

import json
import math
import os

from gudhi import bottleneck_distance


classification = "tool_lego_fit_probe"
NAME = "sim_gudhi_bottleneck_identity_micro"
PROBE_FAMILY = "gudhi_bottleneck_distance_identity_micro"
CONSTRAINT_SET = "finite_persistence_diagram_identity_zero"

_NOT_USED_REASON = (
    "not used: this micro probe isolates GUDHI bottleneck_distance on pinned "
    "finite persistence diagrams; cross-tool coupling and promotion are out of scope."
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
            "GUDHI is load-bearing: bottleneck_distance is the only operator "
            "that decides whether the pinned finite persistence diagram is at "
            "identity distance 0 from itself and nonzero from the shifted control."
        ),
    },
}

TOOL_INTEGRATION_DEPTH = {tool: None for tool in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["gudhi"] = "load_bearing"

IDENTITY_DIAGRAM = [(0.0, 1.0), (0.25, 0.75)]
SHIFTED_DIAGRAM = [(0.0, 1.2), (0.25, 0.75)]
EMPTY_DIAGRAM = []
EPSILON = 1e-12


def _distance(diagram_a, diagram_b):
    return float(bottleneck_distance(diagram_a, diagram_b))


def run_positive_tests():
    distance = _distance(IDENTITY_DIAGRAM, IDENTITY_DIAGRAM)
    return {
        "identical_finite_diagram_admitted_at_zero_distance": {
            "passed": abs(distance) <= EPSILON,
            "expected": "bottleneck distance from a finite diagram to itself is exactly 0 within numeric tolerance",
            "carrier": "finite persistence diagram with two H1-style birth/death intervals",
            "diagram_a": IDENTITY_DIAGRAM,
            "diagram_b": IDENTITY_DIAGRAM,
            "bottleneck_distance": distance,
            "admission_note": (
                "The identical diagram pair is admitted only for the identity-zero "
                "readout of the named GUDHI API surface."
            ),
        }
    }


def run_negative_tests():
    distance = _distance(IDENTITY_DIAGRAM, SHIFTED_DIAGRAM)
    return {
        "shifted_death_diagram_excluded_from_identity": {
            "passed": distance > EPSILON,
            "expected": "changing one death coordinate excludes identity distance 0",
            "carrier": "same finite two-interval diagram with one pinned shifted death coordinate",
            "diagram_a": IDENTITY_DIAGRAM,
            "diagram_b": SHIFTED_DIAGRAM,
            "bottleneck_distance": distance,
            "exclusion_note": (
                "The shifted control is excluded from the identity-zero claim; "
                "the only unpinned behavior is GUDHI's bottleneck_distance readout."
            ),
        }
    }


def run_boundary_tests():
    empty_distance = _distance(EMPTY_DIAGRAM, EMPTY_DIAGRAM)
    single_point_diagram = [(0.5, 0.5)]
    diagonal_distance = _distance(single_point_diagram, EMPTY_DIAGRAM)
    return {
        "empty_diagram_identity_boundary": {
            "passed": abs(empty_distance) <= EPSILON,
            "expected": "empty diagram against itself remains at identity distance 0",
            "diagram_a": EMPTY_DIAGRAM,
            "diagram_b": EMPTY_DIAGRAM,
            "bottleneck_distance": empty_distance,
            "boundary_note": "The empty finite carrier is the degenerate identity boundary.",
        },
        "diagonal_point_boundary": {
            "passed": abs(diagonal_distance) <= EPSILON,
            "expected": "a zero-lifetime interval lies on the diagonal boundary against the empty diagram",
            "diagram_a": single_point_diagram,
            "diagram_b": EMPTY_DIAGRAM,
            "bottleneck_distance": diagonal_distance,
            "boundary_note": "The diagonal interval checks the zero-persistence matching boundary.",
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
            "Other GUDHI bottleneck-distance inputs may be admissible; this micro receipt covers only pinned finite diagram identity and the named shifted control."
        ],
        "demotion_condition": (
            "Demote GUDHI for this surface if bottleneck_distance is nonzero on "
            "the identical finite diagram, zero on the shifted-death control, "
            "or nonzero on the empty/diagonal boundary fixtures."
        ),
        "out_of_scope": [
            "no persistence computation backend claim",
            "no RipsComplex, AlphaComplex, CubicalComplex, or SimplexTree coverage",
            "no Wasserstein distance claim",
            "no topology lego promotion",
            "no tool-tool coupling",
            "no bridge, axis, GStack, QIT engine, or nonclassical claim",
            "no proof of the whole GUDHI library",
        ],
        "criteria_checked": [
            "GUDHI bottleneck_distance identical finite diagram returns 0",
            "GUDHI bottleneck_distance shifted death coordinate is excluded from identity 0",
            "GUDHI bottleneck_distance empty-diagram identity boundary returns 0",
            "GUDHI bottleneck_distance diagonal point boundary returns 0 against empty diagram",
        ],
        "operation_sequence": [
            "pin a finite two-interval persistence diagram",
            "call gudhi.bottleneck_distance on the diagram against itself",
            "call gudhi.bottleneck_distance on the diagram against a one-coordinate shifted control",
            "call gudhi.bottleneck_distance on empty and diagonal-boundary fixtures",
        ],
        "carrier_topology": {
            "carrier": "finite persistence-diagram multiset with explicit birth/death coordinate pairs",
            "positive_fixture": "two finite intervals [(0.0, 1.0), (0.25, 0.75)] compared to itself",
            "graveyard_fixtures": [
                "same diagram with one death coordinate shifted from 1.0 to 1.2",
                "empty diagram",
                "zero-lifetime diagonal interval",
            ],
            "topological_dimension_checked": "diagram metric surface only; no persistence backend is checked",
        },
        "observable": {
            "primary": "bottleneck distance identity value",
            "negative_readout": "strictly positive distance for the shifted control",
            "boundary_readout": "zero distance for empty identity and diagonal-boundary fixtures",
        },
        "pass_fail_predicate": {
            "admit": [
                "identical finite diagram has bottleneck distance 0 within tolerance",
                "empty diagram has bottleneck distance 0 from itself",
                "zero-lifetime diagonal point has bottleneck distance 0 against the empty diagram",
            ],
            "exclude": [
                "shifted death coordinate reports identity distance 0",
                "identical finite diagram reports nonzero distance",
                "boundary fixtures report nonzero distance",
            ],
        },
        "summary": {
            "passed": sum(1 for test in flat_tests if test.get("passed")),
            "total": len(flat_tests),
            "promotion_allowed": False,
            "claim": (
                "GUDHI bottleneck_distance is isolated on pinned finite persistence "
                "diagrams for identity-zero tool-lego fit only."
            ),
        },
        "claim_ceiling": "tool_lego_fit_probe_only",
        "next_lego_target": "minimal finite persistence-diagram metric fixture before topology metric coupling or stability probes",
        "ledger_loopback": {
            "tool_depth_row": "gudhi.bottleneck_distance finite persistence-diagram metric identity",
            "threshold_note": "feeds the shallow-tool checker threshold of >=10 load-bearing receipts for gudhi",
        },
        "promotion_condition": (
            "requires a later admitted downstream row that names this exact GUDHI "
            "bottleneck-distance receipt and passes strict runner admission; this "
            "MICRO row does not promote any lego, topology program, bridge, axis, "
            "GStack, QIT engine, or nonclassical claim"
        ),
        "blocked_until": (
            "blocked from topology, bridge, axis, GStack, QIT engine, and "
            "nonclassical promotion until a downstream queue row declares the "
            "exact parent receipt use and active stage gate for promotion"
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
