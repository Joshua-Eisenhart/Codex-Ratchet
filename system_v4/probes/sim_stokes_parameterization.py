#!/usr/bin/env python3
"""
PURE LEGO: Stokes Parameterization
=================================
Direct local Stokes-parameterization lego on a tiny admitted qubit state set.
"""

import json
import pathlib

import numpy as np


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for Stokes parameterization on one-qubit admitted states, "
    "kept separate from density-matrix admission, characteristic-function rows, "
    "operator-coordinate rows, and Mueller/channel-action rows."
)

LEGO_IDS = [
    "stokes_parameterization",
]

PRIMARY_LEGO_IDS = [
    "stokes_parameterization",
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

I2 = np.eye(2, dtype=complex)
SX = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
SY = np.array([[0.0, -1j], [1j, 0.0]], dtype=complex)
SZ = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
PAULIS = [I2, SX, SY, SZ]


def dm(v):
    vec = np.array(v, dtype=complex).reshape(-1, 1)
    return vec @ vec.conj().T


def density_to_stokes(rho):
    return np.array([float(np.real(np.trace(rho @ p))) for p in PAULIS])


def stokes_to_density(s):
    return 0.5 * sum(s[i] * PAULIS[i] for i in range(4))


def bloch_vector(rho):
    s = density_to_stokes(rho)
    return s[1:]


def valid_stokes(s):
    return bool(s[0] >= -EPS and np.linalg.norm(s[1:]) <= s[0] + EPS)


def main():
    ket0 = dm([1.0, 0.0])
    ket_plus = dm([1.0 / np.sqrt(2.0), 1.0 / np.sqrt(2.0)])
    maximally_mixed = I2 / 2.0
    interior_mixed = np.array([[0.7, 0.1 - 0.05j], [0.1 + 0.05j, 0.3]], dtype=complex)

    states = {
        "ket0": ket0,
        "ket_plus": ket_plus,
        "maximally_mixed": maximally_mixed,
        "interior_mixed": interior_mixed,
    }

    roundtrip_pass = True
    trace_pass = True
    bloch_pass = True
    pure_norm_pass = True
    for rho in states.values():
        s = density_to_stokes(rho)
        recon = stokes_to_density(s)
        roundtrip_pass = roundtrip_pass and np.allclose(recon, rho, atol=EPS)
        trace_pass = trace_pass and abs(s[0] - np.trace(rho).real) < EPS and abs(s[0] - 1.0) < EPS
        bloch_pass = bloch_pass and np.allclose(s[1:], bloch_vector(rho), atol=EPS)
        if abs(np.trace(rho @ rho).real - 1.0) < 1e-8:
            pure_norm_pass = pure_norm_pass and abs(np.linalg.norm(s[1:]) - s[0]) < 1e-8

    phase_sensitive_pair_a = dm([1.0 / np.sqrt(2.0), 1.0 / np.sqrt(2.0)])
    phase_sensitive_pair_b = dm([1.0 / np.sqrt(2.0), 1j / np.sqrt(2.0)])
    same_spectrum = np.allclose(
        np.linalg.eigvalsh(phase_sensitive_pair_a),
        np.linalg.eigvalsh(phase_sensitive_pair_b),
        atol=EPS,
    )
    different_stokes = not np.allclose(
        density_to_stokes(phase_sensitive_pair_a),
        density_to_stokes(phase_sensitive_pair_b),
        atol=EPS,
    )

    positive = {
        "density_to_stokes_and_back_is_exact_on_tiny_state_set": {
            "pass": roundtrip_pass,
        },
        "stokes_s0_matches_trace_for_normalized_states": {
            "pass": trace_pass,
        },
        "stokes_spatial_part_matches_bloch_vector": {
            "pass": bloch_pass,
        },
    }

    negative = {
        "same_spectrum_can_still_give_different_stokes_vectors": {
            "pass": same_spectrum and different_stokes,
        },
        "invalid_stokes_vector_is_rejected_by_physicality_test": {
            "pass": not valid_stokes(np.array([1.0, 1.1, 0.0, 0.0])),
        },
    }

    boundary = {
        "maximally_mixed_state_maps_to_1000": {
            "pass": np.allclose(density_to_stokes(maximally_mixed), np.array([1.0, 0.0, 0.0, 0.0]), atol=EPS),
        },
        "pure_states_saturate_spatial_norm_equals_s0": {
            "pass": pure_norm_pass,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "stokes_parameterization",
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
            "scope_note": "Direct local Stokes-parameterization lego on a tiny admitted qubit state set.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "stokes_parameterization_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
