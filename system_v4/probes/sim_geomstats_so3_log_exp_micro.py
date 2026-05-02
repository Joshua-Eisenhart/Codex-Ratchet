#!/usr/bin/env python3
"""geomstats SO(3) log/exp branch-selection micro probe.

Tool-stage scope:
  - one tool: geomstats
  - one API surface: SpecialOrthogonal(3).metric.exp and metric.log
  - one tiny claim: geomstats round-trips bounded SO(3) tangent fixtures and
    selects the principal log branch instead of a long ambient branch.

This is pre-lego evidence. It does not promote a lego, coupling, bridge, or
stack claim.
"""

import json
import os

import numpy as np
from geomstats.geometry.special_orthogonal import SpecialOrthogonal

classification = "canonical"
NAME = "sim_geomstats_so3_log_exp_micro"
PROBE_FAMILY = "geomstats_so3_log_exp_micro"
CONSTRAINT_SET = "bounded_so3_log_exp_branch_fixtures"

_NOT_USED_REASON = (
    "not used: this micro probe isolates geomstats SO(3) log/exp only; "
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
            "geomstats is load-bearing: SpecialOrthogonal(3).metric.exp and "
            "metric.log produce the SO(3) tangent/rotation round-trip verdicts."
        ),
    },
    "e3nn": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "xgi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "toponetx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "gudhi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
}

TOOL_INTEGRATION_DEPTH = {tool: None for tool in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["geomstats"] = "load_bearing"

SO3 = SpecialOrthogonal(n=3, point_type="matrix")
IDENTITY = np.eye(3)
TOL = 1e-7


def _skew_z(angle):
    return np.array([[0.0, -angle, 0.0], [angle, 0.0, 0.0], [0.0, 0.0, 0.0]])


def _angle_from_skew(skew):
    return float(np.linalg.norm(skew) / np.sqrt(2.0))


def _close(left, right, tol=TOL):
    return bool(np.allclose(left, right, atol=tol))


def run_positive_tests():
    tangent = _skew_z(0.5)
    rotation = SO3.metric.exp(tangent, IDENTITY)
    recovered = SO3.metric.log(rotation, IDENTITY)
    rerotated = SO3.metric.exp(recovered, IDENTITY)

    return {
        "log_exp_roundtrip_small_tangent": {
            "passed": _close(recovered, tangent) and _close(rerotated, rotation),
            "expected_angle": 0.5,
            "recovered_angle": _angle_from_skew(recovered),
            "rotation_belongs_to_so3": bool(SO3.belongs(rotation)),
        },
        "exp_log_roundtrip_rotation_matrix": {
            "passed": _close(rerotated, rotation) and bool(SO3.belongs(rerotated)),
            "expected": "exp(log(R)) returns the same SO(3) point",
            "frobenius_roundtrip_error": float(np.linalg.norm(rerotated - rotation)),
        },
    }


def run_negative_tests():
    long_tangent = _skew_z(2.0 * np.pi + 0.1)
    rotation = SO3.metric.exp(long_tangent, IDENTITY)
    recovered = SO3.metric.log(rotation, IDENTITY)
    recovered_angle = _angle_from_skew(recovered)
    ambient_step = IDENTITY + _skew_z(0.5)

    return {
        "principal_log_rejects_long_branch": {
            "passed": abs(recovered_angle - 0.1) < 1e-6 and abs(recovered_angle - (2.0 * np.pi + 0.1)) > 1.0,
            "expected": "principal log angle is 0.1, not 2*pi + 0.1",
            "recovered_angle": recovered_angle,
            "excluded_long_angle": float(2.0 * np.pi + 0.1),
        },
        "ambient_additive_step_is_not_so3_exp": {
            "passed": not bool(SO3.belongs(ambient_step)),
            "expected": "I + skew(angle) is not admitted as an SO(3) point",
            "belongs_to_so3": bool(SO3.belongs(ambient_step)),
            "exclusion_note": "The micro receipt uses metric.exp, not ambient matrix addition.",
        },
    }


def run_boundary_tests():
    tiny_tangent = _skew_z(1e-5)
    tiny_rotation = SO3.metric.exp(tiny_tangent, IDENTITY)
    tiny_recovered = SO3.metric.log(tiny_rotation, IDENTITY)

    near_cut_tangent = _skew_z(np.pi - 1e-4)
    near_cut_rotation = SO3.metric.exp(near_cut_tangent, IDENTITY)
    near_cut_recovered = SO3.metric.log(near_cut_rotation, IDENTITY)

    return {
        "tiny_angle_does_not_collapse": {
            "passed": abs(_angle_from_skew(tiny_recovered) - 1e-5) < 1e-7,
            "expected_angle": 1e-5,
            "recovered_angle": _angle_from_skew(tiny_recovered),
        },
        "near_pi_below_cut_locus_stays_on_principal_branch": {
            "passed": abs(_angle_from_skew(near_cut_recovered) - (np.pi - 1e-4)) < 1e-5,
            "expected_angle": float(np.pi - 1e-4),
            "recovered_angle": _angle_from_skew(near_cut_recovered),
            "boundary_note": "Exact pi branch ambiguity is intentionally out of scope.",
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
            "Other manifolds and exact-pi branch conventions remain separate future micro surfaces."
        ],
        "demotion_condition": (
            "Demote geomstats for this surface if SO(3) exp/log fail round-trip "
            "on bounded tangents, admit ambient additive updates as SO(3) points, "
            "or return the long branch instead of the principal log branch."
        ),
        "out_of_scope": [
            "no Hopf geometry claim",
            "no lego promotion",
            "no tool-tool coupling",
            "no bridge claim",
            "no proof of the whole geomstats library",
        ],
        "criteria_checked": [
            "geomstats SO(3) exp/log local roundtrip",
            "geomstats SO(3) principal branch selection",
            "ambient additive update exclusion",
            "tiny-angle and near-pi boundary behavior",
        ],
        "summary": {"passed": sum(1 for test in flat_tests if test.get("passed")), "total": len(flat_tests)},
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
