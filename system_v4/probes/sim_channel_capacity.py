#!/usr/bin/env python3
"""
PURE LEGO: Channel Capacity
===========================
Direct local one-shot channel-capacity proxy lego on a tiny fixed ensemble.
"""

import json
import pathlib

import numpy as np


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for a bounded one-shot channel-capacity proxy on a tiny fixed "
    "qubit ensemble, kept separate from coherent information, degradability, and broad channel theory."
)

LEGO_IDS = [
    "channel_capacity",
]

PRIMARY_LEGO_IDS = [
    "channel_capacity",
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
X = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
Y = np.array([[0.0, -1j], [1j, 0.0]], dtype=complex)
Z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)


def dm(v):
    vec = np.array(v, dtype=complex).reshape(-1, 1)
    return vec @ vec.conj().T


def apply_channel(kraus_ops, rho):
    out = np.zeros_like(rho, dtype=complex)
    for k in kraus_ops:
        out += k @ rho @ k.conj().T
    return out


def entropy(rho):
    evals = np.linalg.eigvalsh((rho + rho.conj().T) / 2)
    evals = evals[evals > EPS]
    return float(-np.sum(evals * np.log2(evals))) if len(evals) else 0.0


def holevo_binary(kraus_ops, rho0, rho1, p=0.5):
    e0 = apply_channel(kraus_ops, rho0)
    e1 = apply_channel(kraus_ops, rho1)
    avg = p * e0 + (1 - p) * e1
    return entropy(avg) - p * entropy(e0) - (1 - p) * entropy(e1)


def depolarizing_kraus(p):
    return [
        np.sqrt(1 - p) * I2,
        np.sqrt(p / 3) * X,
        np.sqrt(p / 3) * Y,
        np.sqrt(p / 3) * Z,
    ]


def dephasing_kraus(p):
    return [
        np.sqrt(1 - p) * I2,
        np.sqrt(p) * Z,
    ]


def amplitude_damping_kraus(gamma):
    return [
        np.array([[1.0, 0.0], [0.0, np.sqrt(1 - gamma)]], dtype=complex),
        np.array([[0.0, np.sqrt(gamma)], [0.0, 0.0]], dtype=complex),
    ]


def main():
    rho0 = dm([1.0, 0.0])
    rho1 = dm([0.0, 1.0])
    rho_plus = dm([1.0 / np.sqrt(2.0), 1.0 / np.sqrt(2.0)])
    rho_minus = dm([1.0 / np.sqrt(2.0), -1.0 / np.sqrt(2.0)])

    identity = [I2]
    dephase = dephasing_kraus(0.4)
    depol = depolarizing_kraus(0.3)
    amp = amplitude_damping_kraus(0.4)

    chi_identity_z = holevo_binary(identity, rho0, rho1)
    chi_dephase_z = holevo_binary(dephase, rho0, rho1)
    chi_identity_x = holevo_binary(identity, rho_plus, rho_minus)
    chi_dephase_x = holevo_binary(dephase, rho_plus, rho_minus)
    chi_depol_z = holevo_binary(depol, rho0, rho1)
    chi_amp_z = holevo_binary(amp, rho0, rho1)

    positive = {
        "identity_preserves_full_binary_distinguishability": {
            "chi_identity_z": chi_identity_z,
            "chi_identity_x": chi_identity_x,
            "pass": abs(chi_identity_z - 1.0) < 1e-8 and abs(chi_identity_x - 1.0) < 1e-8,
        },
        "z_dephasing_preserves_z_basis_but_not_x_basis_capacity_proxy": {
            "chi_dephase_z": chi_dephase_z,
            "chi_dephase_x": chi_dephase_x,
            "pass": abs(chi_dephase_z - 1.0) < 1e-8 and chi_dephase_x < chi_identity_x - 1e-3,
        },
        "depolarizing_and_amplitude_damping_reduce_binary_capacity_proxy": {
            "chi_depol_z": chi_depol_z,
            "chi_amp_z": chi_amp_z,
            "pass": chi_depol_z < chi_identity_z - 1e-3 and chi_amp_z < chi_identity_z - 1e-3,
        },
    }

    negative = {
        "different_channels_do_not_collapse_to_same_proxy_value": {
            "pass": len({round(chi_identity_z, 6), round(chi_dephase_x, 6), round(chi_depol_z, 6), round(chi_amp_z, 6)}) > 2,
        },
        "no_asymptotic_theorem_claim_is_needed": {
            "pass": all(np.isfinite(v) for v in [chi_identity_z, chi_dephase_z, chi_dephase_x, chi_depol_z, chi_amp_z]),
        },
    }

    boundary = {
        "holevo_proxy_stays_between_zero_and_one_bit_on_bounded_binary_ensemble": {
            "pass": all(-EPS <= v <= 1.0 + EPS for v in [chi_identity_z, chi_identity_x, chi_dephase_z, chi_dephase_x, chi_depol_z, chi_amp_z]),
        },
        "same_channel_can_score_differently_on_different_input_bases": {
            "pass": abs(chi_dephase_z - chi_dephase_x) > 1e-3,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "channel_capacity",
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
            "scope_note": "Direct local one-shot channel-capacity proxy lego on a tiny fixed binary ensemble.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "channel_capacity_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
