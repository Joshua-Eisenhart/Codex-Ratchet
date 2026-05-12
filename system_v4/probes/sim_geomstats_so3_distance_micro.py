#!/usr/bin/env python3
"""geomstats SO(3) distance micro probe.

Tool-stage scope:
  - one tool: geomstats
  - one API surface: SpecialOrthogonal(n=3, point_type="matrix").metric.dist
  - one tiny claim: geomstats returns intrinsic SO(3) geodesic distances for
    bounded rotation-matrix fixtures, separating them from ambient Frobenius
    distance.

This is pre-lego evidence. It does not promote a lego, coupling, bridge, or
stack claim.
"""

import json
import os

import numpy as np
from geomstats.geometry.special_orthogonal import SpecialOrthogonal

from receipt_boundary import apply_default_receipt_boundary

classification = "canonical"
NAME = "sim_geomstats_so3_distance_micro"
PROBE_FAMILY = "geomstats_so3_distance_micro"
CONSTRAINT_SET = "bounded_so3_intrinsic_distance_fixtures"

_NOT_USED_REASON = (
    "not used: this micro probe isolates geomstats SO(3) metric distance only; "
    "cross-tool coupling and lego promotion are out of scope."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "pyg": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "z3": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "cvc5": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "sympy": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "clifford": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "geomstats": {
        "tried": True,
        "used": True,
        "reason": (
            "geomstats is load-bearing: SpecialOrthogonal(3).metric.dist "
            "produces the SO(3) geodesic distance verdicts."
        ),
    },
    "e3nn": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "xgi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "toponetx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "gudhi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": "load_bearing",
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

SO3 = SpecialOrthogonal(n=3, point_type="matrix")
IDENTITY = np.eye(3)
TOL = 1e-6


def _rotation(axis, angle):
    unit_axis = np.asarray(axis, dtype=float)
    unit_axis = unit_axis / np.linalg.norm(unit_axis)
    x, y, z = unit_axis
    skew = np.array([[0.0, -z, y], [z, 0.0, -x], [-y, x, 0.0]])
    return IDENTITY + np.sin(angle) * skew + (1.0 - np.cos(angle)) * (skew @ skew)


def _dist(left, right):
    return float(SO3.metric.dist(left, right))


def _passed(value, expected, tol=TOL):
    return abs(value - expected) <= tol


def run_positive_tests():
    quarter_turn = _rotation([1.0, 0.0, 0.0], np.pi / 2.0)
    third_turn = _rotation([0.0, 0.0, 1.0], np.pi / 3.0)
    frame_shift = _rotation([0.0, 0.0, 1.0], np.pi / 4.0)
    shifted_identity = frame_shift @ IDENTITY
    shifted_quarter = frame_shift @ quarter_turn

    quarter_distance = _dist(IDENTITY, quarter_turn)
    third_distance = _dist(IDENTITY, third_turn)
    shifted_distance = _dist(shifted_identity, shifted_quarter)

    return {
        "identity_to_quarter_turn": {
            "passed": _passed(quarter_distance, np.pi / 2.0),
            "geomstats_distance": quarter_distance,
            "expected": float(np.pi / 2.0),
            "fixture": "R_x(pi/2)",
        },
        "identity_to_third_turn": {
            "passed": _passed(third_distance, np.pi / 3.0),
            "geomstats_distance": third_distance,
            "expected": float(np.pi / 3.0),
            "fixture": "R_z(pi/3)",
        },
        "left_frame_invariance": {
            "passed": _passed(shifted_distance, quarter_distance),
            "geomstats_distance": shifted_distance,
            "reference_distance": quarter_distance,
            "fixture": "dist(Q @ I, Q @ R_x(pi/2)) == dist(I, R_x(pi/2))",
        },
    }


def run_negative_tests():
    non_antipodal_turn = _rotation([0.0, 1.0, 0.0], 2.0 * np.pi / 3.0)
    geomstats_distance = _dist(IDENTITY, non_antipodal_turn)
    frobenius_distance = float(np.linalg.norm(IDENTITY - non_antipodal_turn))
    separated = abs(geomstats_distance - frobenius_distance) > 0.1
    range_admissible = 0.0 <= geomstats_distance <= np.pi + TOL

    return {
        "ambient_frobenius_is_excluded_as_so3_metric": {
            "passed": separated and range_admissible,
            "geomstats_distance": geomstats_distance,
            "ambient_frobenius_distance": frobenius_distance,
            "analytic_angle_note": "non-antipodal 2*pi/3 fixture; exact-pi branch behavior is out of scope",
            "approx_expected_geomstats_distance": float(2.0 * np.pi / 3.0),
            "so3_range_admissible": bool(range_admissible),
            "exclusion_note": (
                "Ambient matrix distance is not admitted as the SO(3) "
                "geodesic distance for this fixture."
            ),
        }
    }


def run_boundary_tests():
    same_point = _dist(IDENTITY, IDENTITY)
    tiny_turn = _rotation([0.0, 0.0, 1.0], 1e-4)
    tiny_distance = _dist(IDENTITY, tiny_turn)
    near_cut = _rotation([0.0, 0.0, 1.0], np.pi - 1e-4)
    near_cut_distance = _dist(IDENTITY, near_cut)

    return {
        "identity_boundary_zero": {
            "passed": _passed(same_point, 0.0),
            "geomstats_distance": same_point,
            "expected": 0.0,
        },
        "near_identity_small_angle": {
            "passed": _passed(tiny_distance, 1e-4, tol=1e-6),
            "geomstats_distance": tiny_distance,
            "expected": 1e-4,
            "boundary_note": (
                "This detects small-angle collapse in the SO(3) distance "
                "observable before coupling programs use near-identity steps."
            ),
        },
        "near_pi_cut_locus_distance": {
            "passed": _passed(near_cut_distance, np.pi - 1e-4, tol=1e-5),
            "geomstats_distance": near_cut_distance,
            "expected": float(np.pi - 1e-4),
            "boundary_note": (
                "This stays below the SO(3) pi cut locus; exact-pi log/exp "
                "branch behavior remains out of scope for this distance micro."
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
            "Other SO(3) operations may remain useful; this micro receipt only "
            "covers the named geomstats metric.dist surface."
        ],
        "demotion_condition": (
            "Demote geomstats for this function surface if metric.dist diverges "
            "from analytic SO(3) rotation-angle distances, collapses to ambient "
            "Frobenius distance, violates left frame invariance, or mishandles "
            "the zero, near-identity, and near-pi boundary fixtures."
        ),
        "out_of_scope": [
            "no lego promotion",
            "no tool-tool coupling",
            "no bridge claim",
            "no proof of the whole geomstats library",
            "no SO(3) log/exp branch-selection receipt",
        ],
        "criteria_checked": [
            "geomstats SO(3) metric.dist analytic angle agreement",
            "left frame invariance of SO(3) metric.dist",
            "ambient Frobenius distance exclusion",
            "zero-distance, small-angle, and near-cut-locus boundary behavior",
        ],
        "summary": {
            "passed": sum(1 for test in flat_tests if test.get("passed")),
            "total": len(flat_tests),
        },
        "all_pass": all_pass,
    }
    results = apply_default_receipt_boundary(
        results,
        source_name="sim_geomstats_so3_distance_micro",
        target="Use as bounded geomstats SO(3) metric-distance function evidence before geometry lego fit packets.",
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
