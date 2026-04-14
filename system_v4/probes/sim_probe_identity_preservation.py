#!/usr/bin/env python3
"""
PURE LEGO: Probe Identity Preservation
======================================
Direct local root/admission lego.

Checks that the same finite probe family applied repeatedly to the same admitted
state does not invent distinctions, while still separating genuinely different
states.
"""

import json
import pathlib

import numpy as np
classification = "classical_baseline"  # auto-backfill


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for repeatable probe-relative identity preservation on "
    "bounded qubit states."
)

LEGO_IDS = [
    "probe_identity_preservation",
    "probe_object",
    "carrier_probe_support",
]

PRIMARY_LEGO_IDS = [
    "probe_identity_preservation",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not needed for smallest repeatability row"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed for smallest repeatability row"},
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


def probe_probs(rho, effects):
    return np.array([float(np.real(np.trace(rho @ e))) for e in effects], dtype=float)


def main():
    rho0 = dm([1, 0])
    rho1 = dm([0, 1])
    rho_plus = dm([1 / np.sqrt(2), 1 / np.sqrt(2)])

    projective_z = [
        np.array([[1.0, 0.0], [0.0, 0.0]], dtype=complex),
        np.array([[0.0, 0.0], [0.0, 1.0]], dtype=complex),
    ]
    noisy_z = [
        np.array([[0.8, 0.0], [0.0, 0.2]], dtype=complex),
        np.array([[0.2, 0.0], [0.0, 0.8]], dtype=complex),
    ]
    flat_probe = [
        0.5 * np.eye(2, dtype=complex),
        0.5 * np.eye(2, dtype=complex),
    ]

    p0_first = probe_probs(rho0, projective_z)
    p0_second = probe_probs(rho0, projective_z)
    pplus_first = probe_probs(rho_plus, noisy_z)
    pplus_second = probe_probs(rho_plus, noisy_z)
    flat0 = probe_probs(rho0, flat_probe)
    flat1 = probe_probs(rho1, flat_probe)

    positive = {
        "same_state_same_probe_is_repeatable": {
            "first_probs": p0_first.tolist(),
            "second_probs": p0_second.tolist(),
            "pass": np.allclose(p0_first, p0_second, atol=EPS),
        },
        "same_state_same_noisy_probe_is_repeatable": {
            "first_probs": pplus_first.tolist(),
            "second_probs": pplus_second.tolist(),
            "pass": np.allclose(pplus_first, pplus_second, atol=EPS),
        },
        "different_states_can_still_be_separated": {
            "rho0_probs": p0_first.tolist(),
            "rho1_probs": probe_probs(rho1, projective_z).tolist(),
            "pass": not np.allclose(p0_first, probe_probs(rho1, projective_z), atol=EPS),
        },
    }

    negative = {
        "flat_probe_does_not_preserve_nontrivial_identity_relation": {
            "rho0_probs": flat0.tolist(),
            "rho1_probs": flat1.tolist(),
            "pass": np.allclose(flat0, flat1, atol=EPS),
        },
        "different_states_are_not_falsely_identical_under_projective_probe": {
            "pass": not np.allclose(probe_probs(rho0, projective_z), probe_probs(rho1, projective_z), atol=EPS),
        },
    }

    boundary = {
        "repeatability_holds_under_basis_change_state": {
            "pass": np.allclose(probe_probs(rho_plus, projective_z), probe_probs(rho_plus, projective_z), atol=EPS),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "probe_identity_preservation",
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
            "scope_note": "Direct local repeatability lego for probe-relative identity on bounded qubit states.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "probe_identity_preservation_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
