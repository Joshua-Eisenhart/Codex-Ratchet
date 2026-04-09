#!/usr/bin/env python3
"""
PURE LEGO: Carrier Probe Support
================================
Direct local root/admission lego.

Check that a finite carrier supports a finite probe family with the right shape,
bounded probabilities, and nontrivial separation behavior.
"""

import json
import pathlib

import numpy as np


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for carrier/probe compatibility on bounded qubit carriers."
)

LEGO_IDS = [
    "carrier_probe_support",
    "probe_object",
    "positivity_constraint",
]

PRIMARY_LEGO_IDS = [
    "carrier_probe_support",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not needed for smallest honest carrier/probe support row"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed for smallest honest carrier/probe support row"},
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


def born_probs(rho, effects):
    return [float(np.real(np.trace(rho @ e))) for e in effects]


def family_supports_carrier(carrier_dim, effects):
    shapes_ok = all(e.shape == (carrier_dim, carrier_dim) for e in effects)
    psd_ok = True
    for e in effects:
        if e.shape != (carrier_dim, carrier_dim):
            psd_ok = False
            continue
        evals = np.linalg.eigvalsh((e + e.conj().T) / 2)
        if not np.all(evals >= -EPS):
            psd_ok = False
    resolves_identity = shapes_ok and np.allclose(sum(effects), np.eye(carrier_dim), atol=EPS)
    return {
        "shapes_ok": bool(shapes_ok),
        "psd_ok": bool(psd_ok),
        "resolves_identity": bool(resolves_identity),
    }


def main():
    rho0 = dm([1, 0])
    rho1 = dm([0, 1])
    rho_plus = dm([1 / np.sqrt(2), 1 / np.sqrt(2)])

    supported_probe = [
        np.array([[1.0, 0.0], [0.0, 0.0]], dtype=complex),
        np.array([[0.0, 0.0], [0.0, 1.0]], dtype=complex),
    ]
    noisy_supported_probe = [
        np.array([[0.75, 0.0], [0.0, 0.25]], dtype=complex),
        np.array([[0.25, 0.0], [0.0, 0.75]], dtype=complex),
    ]
    wrong_dim_probe = [
        np.eye(3, dtype=complex) / 2,
        np.eye(3, dtype=complex) / 2,
    ]
    nonresolving_probe = [
        np.array([[0.5, 0.0], [0.0, 0.1]], dtype=complex),
        np.array([[0.1, 0.0], [0.0, 0.1]], dtype=complex),
    ]

    good = family_supports_carrier(2, supported_probe)
    noisy = family_supports_carrier(2, noisy_supported_probe)
    bad_dim = family_supports_carrier(2, wrong_dim_probe)
    bad_sum = family_supports_carrier(2, nonresolving_probe)

    positive = {
        "qubit_carrier_supports_projective_probe_family": {
            **good,
            "rho0_probs": born_probs(rho0, supported_probe),
            "rho1_probs": born_probs(rho1, supported_probe),
            "pass": (
                good["shapes_ok"]
                and good["psd_ok"]
                and good["resolves_identity"]
                and born_probs(rho0, supported_probe)[0] > born_probs(rho1, supported_probe)[0]
            ),
        },
        "qubit_carrier_supports_noisy_probe_family": {
            **noisy,
            "rho_plus_probs": born_probs(rho_plus, noisy_supported_probe),
            "pass": (
                noisy["shapes_ok"]
                and noisy["psd_ok"]
                and noisy["resolves_identity"]
                and all(0.0 - EPS <= p <= 1.0 + EPS for p in born_probs(rho_plus, noisy_supported_probe))
            ),
        },
    }

    negative = {
        "wrong_dimension_probe_family_is_rejected": {
            **bad_dim,
            "pass": not bad_dim["shapes_ok"],
        },
        "nonresolving_probe_family_is_rejected": {
            **bad_sum,
            "pass": not bad_sum["resolves_identity"],
        },
    }

    boundary = {
        "all_supported_probe_probabilities_are_bounded": {
            "pass": all(
                0.0 - EPS <= p <= 1.0 + EPS
                for probs in [
                    born_probs(rho0, supported_probe),
                    born_probs(rho1, supported_probe),
                    born_probs(rho_plus, noisy_supported_probe),
                ]
                for p in probs
            ),
        },
        "same_supported_family_separates_a_state_pair": {
            "pass": not np.allclose(born_probs(rho0, supported_probe), born_probs(rho1, supported_probe), atol=EPS),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "carrier_probe_support",
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
            "scope_note": "Direct local carrier/probe compatibility lego on bounded qubit carriers.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "carrier_probe_support_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
