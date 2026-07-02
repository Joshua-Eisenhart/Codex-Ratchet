#!/usr/bin/env python3
"""geomstats S2 tangent-projection micro probe.

Tool-stage scope:
  - one tool: geomstats
  - one API surface: Hypersphere(2).to_tangent
  - one tiny claim: geomstats projects finite ambient R3 vectors to the
    tangent plane at one fixed S2 base point, excluding radial components.

Inventory note:
  Hypersphere(2) exp/log round-trip is already covered by
  system_v4/probes/a2_state/sim_results/sim_geomstats_capability_results.json.
  This file uses the nearest uncovered neighbor surface, to_tangent.

This is pre-lego tool-lego-fit evidence. It does not promote a lego, coupling,
bridge, axis, engine, or nonclassical admission claim.
"""

import json
import os

import numpy as np
from geomstats.geometry.hypersphere import Hypersphere

classification = "tool_lego_fit_probe"
NAME = "sim_geomstats_s2_to_tangent_micro"
PROBE_FAMILY = "geomstats_s2_to_tangent_micro"
CONSTRAINT_SET = "bounded_s2_tangent_projection_fixture"

_NOT_USED_REASON = (
    "not used: this micro probe isolates geomstats Hypersphere(2).to_tangent "
    "only; cross-tool coupling and lego promotion are out of scope."
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
            "geomstats is load-bearing: Hypersphere(2).to_tangent decides "
            "whether finite ambient R3 vectors are admitted as S2 tangent "
            "vectors at the fixed carrier point."
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

S2 = Hypersphere(dim=2)
BASE_POINT = np.array([0.0, 0.0, 1.0])
TOL = 1e-10


def _as_array(value):
    return np.asarray(value, dtype=float)


def _project(ambient_vec):
    return _as_array(S2.to_tangent(vector=ambient_vec, base_point=BASE_POINT))


def _orthogonality_residual(tangent_vec):
    return float(abs(np.dot(BASE_POINT, tangent_vec)))


def _close(left, right, tol=TOL):
    return bool(np.allclose(left, right, atol=tol, rtol=0.0))


def run_positive_tests():
    ambient_tangent = np.array([0.125, -0.25, 0.0])
    projected = _project(ambient_tangent)

    return {
        "ambient_tangent_vector_admitted": {
            "passed": _close(projected, ambient_tangent)
            and _orthogonality_residual(projected) < TOL,
            "carrier": "finite fixture: base point (0,0,1) on S2 with one ambient R3 vector",
            "expected_projection": ambient_tangent.tolist(),
            "geomstats_projection": projected.tolist(),
            "orthogonality_residual": _orthogonality_residual(projected),
            "admissibility_note": (
                "The input vector is already tangent to S2 at the carrier point; "
                "the projected vector remains admitted by the tangent-plane constraint."
            ),
        }
    }


def run_negative_tests():
    radial_vector = np.array([0.0, 0.0, 0.5])
    projected = _project(radial_vector)
    zero = np.zeros(3)

    return {
        "pure_radial_component_excluded": {
            "passed": _close(projected, zero)
            and _orthogonality_residual(projected) < TOL,
            "carrier": "finite fixture: base point (0,0,1) on S2 with one radial R3 vector",
            "excluded_input": radial_vector.tolist(),
            "geomstats_projection": projected.tolist(),
            "exclusion_note": (
                "The radial component is excluded under the tangent-plane constraint; "
                "only the zero tangent vector remains at this carrier point."
            ),
        }
    }


def run_boundary_tests():
    epsilon = 1e-9
    near_radial = np.array([epsilon, -epsilon, 0.5])
    projected = _project(near_radial)
    expected = np.array([epsilon, -epsilon, 0.0])

    return {
        "near_radial_epsilon_tangent_component": {
            "passed": _close(projected, expected, tol=1e-14)
            and _orthogonality_residual(projected) < 1e-14,
            "carrier": (
                "finite fixture: base point (0,0,1) on S2 with one radial-dominant "
                "ambient R3 vector carrying epsilon tangent displacement"
            ),
            "expected_projection": expected.tolist(),
            "geomstats_projection": projected.tolist(),
            "orthogonality_residual": _orthogonality_residual(projected),
            "boundary_note": (
                "The probe distinguishes an epsilon tangent component while excluding "
                "the radial component; smaller numerical tolerances remain out of scope."
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
        "carrier": (
            "finite S2 carrier fixture: one fixed base point (0,0,1) and three "
            "finite ambient R3 vectors probing tangent, radial, and boundary cases"
        ),
        "finite_map": (
            "Hypersphere(2).to_tangent maps each finite ambient R3 vector at the "
            "fixed S2 base point to its tangent-plane output vector"
        ),
        "one_variable": "only geomstats Hypersphere(2).to_tangent behavior is under test",
        "surviving_alternatives": [
            "Other Hypersphere(2) APIs and other base points remain separate micro surfaces."
        ],
        "summary": {
            "promotion_allowed": False,
            "claim": (
                "Hypersphere(2).to_tangent is a bounded tool-lego-fit probe for "
                "finite tangent-plane projection only."
            ),
            "promotion_note": (
                "classification is tool_lego_fit_probe; promotion_allowed is false; "
                "this does not promote a lego, coupling, bridge, axis, engine, "
                "or nonclassical admission claim."
            ),
            "covered_check": (
                "switched: Hypersphere(2) exp/log round-trip already has a "
                "geomstats load-bearing receipt in sim_geomstats_capability_results.json"
            ),
            "ledger_loopback": (
                "geomstats shallow-tool checker row: Hypersphere(2).to_tangent; "
                "threshold target remains >=10 load-bearing geomstats receipts"
            ),
            "passed": sum(1 for test in flat_tests if test.get("passed")),
            "total": len(flat_tests),
        },
        "demotion_condition": (
            "Demote geomstats for this surface if to_tangent does not preserve an "
            "already tangent vector, does not exclude radial components, or loses "
            "the stated epsilon tangent boundary component."
        ),
        "out_of_scope": [
            "no sim execution by this authoring packet",
            "no result JSON from this authoring packet",
            "no registry or doc edit",
            "no tool-tool coupling",
            "no lego promotion",
            "no bridge claim",
            "no axis claim",
            "no engine claim",
            "no nonclassical admission claim",
        ],
        "criteria_checked": [
            "geomstats Hypersphere(2).to_tangent preserves an already tangent ambient vector",
            "geomstats Hypersphere(2).to_tangent excludes a pure radial component",
            "geomstats Hypersphere(2).to_tangent preserves an epsilon tangent boundary component",
        ],
        "claim_ceiling": "tool_lego_fit_probe_only",
        "next_lego_target": "bounded S2 tangent-plane finite fixture for later geomstats geometry rows",
        "promotion_condition": (
            "requires a later admitted downstream row that names this exact geomstats "
            "function receipt and passes the relevant runner and stage gates"
        ),
        "blocked_until": (
            "blocked from manifold, bridge, axis, GStack, QIT engine, and nonclassical "
            "promotion until a downstream queue row cites this exact parent receipt "
            "and satisfies the active stage gate"
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
