#!/usr/bin/env python3
"""geomstats SPD affine-invariant distance symmetry micro probe.

Tool-stage scope:
  - one tool: geomstats
  - one API surface: SPDMatrices(n=2).metric.dist
  - one tiny claim: geomstats returns a symmetric affine-invariant SPD
    distance for bounded 2x2 SPD matrix fixtures.

This is a tool-lego fit probe. It does not promote a lego, coupling, bridge,
axis, stack, or nonclassical admission claim.
"""

import json
import os

import numpy as np
from geomstats.geometry.spd_matrices import SPDMatrices

from receipt_boundary import apply_default_receipt_boundary

classification = "tool_lego_fit_probe"
NAME = "sim_geomstats_spd_affine_symmetry_micro"
PROBE_FAMILY = "geomstats_spd_affine_distance_symmetry_micro"
CONSTRAINT_SET = "bounded_spd2_affine_distance_symmetry_fixtures"

_NOT_USED_REASON = (
    "not used: this micro probe isolates geomstats SPDMatrices.metric.dist "
    "distance symmetry only; cross-tool coupling and promotion are out of scope."
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
            "geomstats is load-bearing: SPDMatrices(n=2).metric.dist decides "
            "the forward/reverse SPD affine-distance symmetry verdicts."
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

SPD2 = SPDMatrices(n=2)
TOL = 1e-8

SPD_A = np.array([[2.0, 0.35], [0.35, 1.25]])
SPD_B = np.array([[1.6, -0.20], [-0.20, 2.1]])
SPD_IDENTITY = np.eye(2)
SPD_NEAR_BOUNDARY = np.diag([1e-5, 1.0])
NON_SPD_SYMMETRIC = np.array([[1.0, 2.0], [2.0, 1.0]])


def _dist(left, right):
    return float(SPD2.metric.dist(left, right))


def _close(left, right, tol=TOL):
    return bool(abs(left - right) <= tol)


def run_positive_tests():
    forward = _dist(SPD_A, SPD_B)
    reverse = _dist(SPD_B, SPD_A)

    return {
        "spd_affine_distance_is_symmetric_on_fixture_pair": {
            "passed": _close(forward, reverse) and forward > 0.0,
            "forward_distance": forward,
            "reverse_distance": reverse,
            "symmetry_gap": abs(forward - reverse),
            "carrier": "finite ordered pair of 2x2 SPD matrices in SPDMatrices(n=2)",
        },
        "identity_pair_admitted_with_zero_distance": {
            "passed": _close(_dist(SPD_IDENTITY, SPD_IDENTITY), 0.0),
            "distance": _dist(SPD_IDENTITY, SPD_IDENTITY),
            "expected": 0.0,
            "carrier": "2x2 identity SPD matrix",
        },
    }


def run_negative_tests():
    forward = _dist(SPD_A, SPD_B)
    reverse = _dist(SPD_B, SPD_A)
    asymmetric_baseline_gap = abs(forward - (reverse + 1e-3))
    non_spd_admitted = bool(SPD2.belongs(NON_SPD_SYMMETRIC, atol=1e-9))

    return {
        "asymmetric_readout_is_excluded_for_this_surface": {
            "passed": asymmetric_baseline_gap > 1e-4,
            "geomstats_forward_distance": forward,
            "shifted_reverse_control": reverse + 1e-3,
            "control_gap": asymmetric_baseline_gap,
            "exclusion_note": (
                "The shifted reverse control is not admitted as the symmetric "
                "SPDMatrices.metric.dist readout."
            ),
        },
        "indefinite_symmetric_matrix_is_excluded_from_carrier": {
            "passed": not non_spd_admitted,
            "belongs_to_spd2": non_spd_admitted,
            "exclusion_note": "A symmetric matrix with a negative eigenvalue is excluded from SPD(2).",
        },
    }


def run_boundary_tests():
    near_forward = _dist(SPD_IDENTITY, SPD_NEAR_BOUNDARY)
    near_reverse = _dist(SPD_NEAR_BOUNDARY, SPD_IDENTITY)
    tiny_gap = abs(near_forward - near_reverse)

    return {
        "near_boundary_spd_distance_remains_finite_and_symmetric": {
            "passed": np.isfinite(near_forward) and _close(near_forward, near_reverse, tol=1e-7),
            "forward_distance": near_forward,
            "reverse_distance": near_reverse,
            "symmetry_gap": tiny_gap,
            "boundary_note": (
                "The fixture stays inside SPD(2) but near the positive-definite "
                "boundary; singular matrices remain out of scope."
            ),
        }
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
        "finite_map": (
            "ordered SPD(2) matrix pair (A, B) -> pair of geomstats affine distances "
            "(dist(A, B), dist(B, A)) and their absolute symmetry gap"
        ),
        "domain": "finite set of pinned 2x2 SPD matrix fixtures plus one indefinite control",
        "codomain_or_output": "finite distance scalars, symmetry gaps, and carrier exclusion booleans",
        "carrier": "SPDMatrices(n=2) over explicit 2x2 positive-definite matrix fixtures",
        "one_variable": (
            "only SPDMatrices(n=2).metric.dist behavior is uncertain; fixtures, "
            "thresholds, controls, and claim ceiling are pinned"
        ),
        "surviving_alternatives": [
            "Other geomstats SPD surfaces such as log, exp, geodesic, and Frechet mean require separate micro receipts."
        ],
        "demotion_condition": (
            "Demote geomstats for this function surface if SPDMatrices.metric.dist "
            "returns asymmetric forward/reverse distances on bounded SPD(2) fixtures, "
            "admits the indefinite control carrier, or loses finite symmetric behavior "
            "near the positive-definite boundary."
        ),
        "out_of_scope": [
            "no lego promotion",
            "no tool-tool coupling",
            "no bridge claim",
            "no axis claim",
            "no stack claim",
            "no proof of the whole geomstats library",
            "no result JSON is written unless the runner executes this file later",
        ],
        "criteria_checked": [
            "geomstats SPDMatrices.metric.dist forward/reverse symmetry",
            "identity SPD zero-distance boundary",
            "asymmetric shifted-control exclusion",
            "indefinite symmetric matrix carrier exclusion",
            "near-boundary SPD finite symmetric behavior",
        ],
        "summary": {
            "passed": sum(1 for test in flat_tests if test.get("passed")),
            "total": len(flat_tests),
            "classification": "tool_lego_fit_probe",
            "promotion_allowed": False,
            "ledger_loopback": (
                "geomstats tool-depth row: SPDMatrices(n=2).metric.dist affine-invariant "
                "distance symmetry; shallow-tool checker threshold >=10 load-bearing receipts"
            ),
        },
        "claim_ceiling": "tool_lego_fit_probe_only",
        "next_lego_target": "bounded SPD(2) geometry fixture only; no lego promotion from this receipt",
        "promotion_condition": (
            "requires a later downstream row that names this exact function receipt, "
            "declares a promotion-eligible lego target, and passes strict runner admission"
        ),
        "blocked_until": (
            "blocked from lego, coupling, bridge, axis, GStack, and nonclassical promotion "
            "until an admitted downstream packet consumes this exact receipt"
        ),
        "all_pass": all_pass,
    }
    results = apply_default_receipt_boundary(
        results,
        source_name=NAME,
        target=(
            "Use as bounded geomstats SPDMatrices.metric.dist symmetry evidence "
            "before SPD geometry lego-fit or integration packets."
        ),
    )

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Summary: {results['summary']['passed']}/{results['summary']['total']} admitted")

    if not all_pass:
        raise SystemExit(1)
