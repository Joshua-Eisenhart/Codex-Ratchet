#!/usr/bin/env python3
"""
PURE LEGO: Trace-Distance Geometry
==================================
Direct local metric-geometry lego on bounded qubit states.
"""

import json
import pathlib

import numpy as np
classification = "classical_baseline"  # auto-backfill


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for trace-distance geometry on bounded qubit state pairs."
)

LEGO_IDS = [
    "trace_distance_geometry",
]

PRIMARY_LEGO_IDS = [
    "trace_distance_geometry",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}


def dm(v):
    v = np.array(v, dtype=complex).reshape(-1, 1)
    return v @ v.conj().T


def trace_distance(rho, sigma):
    diff = (rho - sigma + (rho - sigma).conj().T) / 2
    evals = np.linalg.eigvalsh(diff)
    return float(0.5 * np.sum(np.abs(evals)))


def unitary_rotate(rho):
    h = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
    return h @ rho @ h.conj().T


def main():
    rho0 = dm([1, 0])
    rho1 = dm([0, 1])
    rho_plus = dm([1 / np.sqrt(2), 1 / np.sqrt(2)])
    rho_mix = np.eye(2, dtype=complex) / 2
    rho_mid = 0.7 * rho0 + 0.3 * rho_mix

    positive = {
        "identity_pair_zero_distance": {
            "pass": trace_distance(rho0, rho0) < EPS and trace_distance(rho_plus, rho_plus) < EPS,
        },
        "symmetry_of_distance": {
            "pass": abs(trace_distance(rho0, rho_plus) - trace_distance(rho_plus, rho0)) < EPS,
        },
        "basis_pair_max_separation": {
            "value": trace_distance(rho0, rho1),
            "pass": abs(trace_distance(rho0, rho1) - 1.0) < EPS,
        },
        "unitary_invariance": {
            "pass": abs(
                trace_distance(rho0, rho_plus)
                - trace_distance(unitary_rotate(rho0), unitary_rotate(rho_plus))
            ) < EPS,
        },
    }

    negative = {
        "mixed_state_contraction_relative_to_pure": {
            "pure_distance": trace_distance(rho0, rho1),
            "mixed_distance": trace_distance(rho_mid, rho1),
            "pass": trace_distance(rho_mid, rho1) < trace_distance(rho0, rho1),
        },
        "nonorthogonal_pair_not_maximal": {
            "value": trace_distance(rho0, rho_plus),
            "pass": trace_distance(rho0, rho_plus) < 1.0 - EPS,
        },
    }

    boundary = {
        "triangle_inequality_spot_check": {
            "lhs": trace_distance(rho0, rho_mix),
            "rhs": trace_distance(rho0, rho_plus) + trace_distance(rho_plus, rho_mix),
            "pass": trace_distance(rho0, rho_mix) <= trace_distance(rho0, rho_plus) + trace_distance(rho_plus, rho_mix) + EPS,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "trace_distance_geometry",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "scope_note": "Direct local trace-distance lego on bounded qubit states.",
        },
    }

    out_path = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results" / "trace_distance_geometry_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
