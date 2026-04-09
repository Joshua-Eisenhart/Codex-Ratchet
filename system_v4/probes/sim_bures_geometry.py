#!/usr/bin/env python3
"""
PURE LEGO: Bures Geometry
=========================
Direct local mixed-state metric lego on bounded qubit states.
"""

import json
import pathlib

import numpy as np


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for Bures geometry on bounded qubit states, kept separate "
    "from trace-distance and fidelity readout rows."
)

LEGO_IDS = [
    "bures_geometry",
]

PRIMARY_LEGO_IDS = [
    "bures_geometry",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed for the smallest direct local metric row"},
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


def matrix_sqrt(m):
    evals, evecs = np.linalg.eigh((m + m.conj().T) / 2)
    evals = np.maximum(evals, 0.0)
    return evecs @ np.diag(np.sqrt(evals)) @ evecs.conj().T


def fidelity(rho, sigma):
    sr = matrix_sqrt(rho)
    core = sr @ sigma @ sr
    return float(np.real(np.trace(matrix_sqrt(core))) ** 2)


def bures_distance(rho, sigma):
    f = fidelity(rho, sigma)
    return float(np.sqrt(max(0.0, 2.0 - 2.0 * np.sqrt(min(1.0, max(0.0, f))))))


def hadamard():
    return np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)


def main():
    rho0 = dm([1, 0])
    rho1 = dm([0, 1])
    rho_plus = dm([1 / np.sqrt(2), 1 / np.sqrt(2)])
    rho_mix = np.eye(2, dtype=complex) / 2.0
    rho_mid = np.array([[0.7, 0.0], [0.0, 0.3]], dtype=complex)

    d_same = bures_distance(rho0, rho0)
    d_orth = bures_distance(rho0, rho1)
    d_mix = bures_distance(rho0, rho_mix)
    d_mid = bures_distance(rho0, rho_mid)
    d_plus = bures_distance(rho0, rho_plus)

    h = hadamard()
    d_unitary = bures_distance(h @ rho0 @ h.conj().T, h @ rho_mix @ h.conj().T)

    positive = {
        "identity_pair_has_zero_bures_distance": {
            "value": d_same,
            "pass": abs(d_same) < EPS,
        },
        "symmetry_holds": {
            "lhs": d_plus,
            "rhs": bures_distance(rho_plus, rho0),
            "pass": abs(d_plus - bures_distance(rho_plus, rho0)) < EPS,
        },
        "unitary_invariance_holds": {
            "original": d_mix,
            "rotated": d_unitary,
            "pass": abs(d_mix - d_unitary) < EPS,
        },
    }

    negative = {
        "orthogonal_pure_pair_is_not_zero": {
            "value": d_orth,
            "pass": d_orth > 1.0 - EPS,
        },
        "pure_vs_mixed_is_not_maximal": {
            "mixed": d_mix,
            "orthogonal": d_orth,
            "pass": d_mix < d_orth - EPS,
        },
    }

    boundary = {
        "intermediate_ordering_is_stable": {
            "same": d_same,
            "mid": d_mid,
            "mix": d_mix,
            "orth": d_orth,
            "pass": d_same <= d_mid + EPS and d_mid <= d_mix + EPS and d_mix <= d_orth + EPS,
        },
        "near_boundary_state_is_finite": {
            "value": d_mid,
            "pass": np.isfinite(d_mid) and d_mid >= -EPS,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "bures_geometry",
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
            "scope_note": "Direct local Bures-distance lego on bounded qubit states.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "bures_geometry_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
