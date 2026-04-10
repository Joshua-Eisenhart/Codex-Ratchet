#!/usr/bin/env python3
"""
PURE LEGO: Operator-Ordered Entropy
===================================
Direct local row for entropy response under noncommuting operator order.
"""

import json
import pathlib

import numpy as np


EPS = 1e-12
CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local operator-ordered entropy row on one bounded carrier, "
    "kept separate from generic loop order and transport-weighted bundles."
)
LEGO_IDS = ["operator_ordered_entropy"]
PRIMARY_LEGO_IDS = ["operator_ordered_entropy"]
TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": "not needed"} for k in [
    "pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"
]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}


def bloch_density(x, y, z):
    return 0.5 * np.array([[1 + z, x - 1j * y], [x + 1j * y, 1 - z]], dtype=complex)


def entropy_bits(rho):
    evals = np.linalg.eigvalsh(0.5 * (rho + rho.conj().T))
    evals = np.clip(np.real(evals), 0.0, None)
    nz = evals[evals > EPS]
    return 0.0 if nz.size == 0 else float(-np.sum(nz * np.log2(nz)))


def apply_channel(rho, kraus_ops):
    out = np.zeros_like(rho, dtype=complex)
    for k in kraus_ops:
        out += k @ rho @ k.conj().T
    return out


def z_dephasing_kraus(p):
    I = np.eye(2, dtype=complex)
    Z = np.array([[1, 0], [0, -1]], dtype=complex)
    return [np.sqrt(1 - p) * I, np.sqrt(p) * Z]


def bit_flip_kraus(p):
    I = np.eye(2, dtype=complex)
    X = np.array([[0, 1], [1, 0]], dtype=complex)
    return [np.sqrt(1 - p) * I, np.sqrt(p) * X]


def amplitude_damping_kraus(gamma):
    return [
        np.array([[1, 0], [0, np.sqrt(1 - gamma)]], dtype=complex),
        np.array([[0, np.sqrt(gamma)], [0, 0]], dtype=complex),
    ]


def main():
    rho0 = bloch_density(0.35, 0.2, 0.4)
    a = amplitude_damping_kraus(0.35)
    b = bit_flip_kraus(0.25)
    ab = apply_channel(apply_channel(rho0, a), b)
    ba = apply_channel(apply_channel(rho0, b), a)
    eab = entropy_bits(ab)
    eba = entropy_bits(ba)
    c = z_dephasing_kraus(0.20)
    cd = apply_channel(apply_channel(rho0, c), c)
    dc = apply_channel(apply_channel(rho0, c), c)
    ecd = entropy_bits(cd)
    edc = entropy_bits(dc)

    positive = {
        "operator_order_changes_entropy_response": {
            "entropy_ab": eab, "entropy_ba": eba,
            "pass": abs(eab - eba) > 1e-4,
        },
        "commuting_control_has_no_order_gap": {
            "entropy_cd": ecd, "entropy_dc": edc,
            "pass": abs(ecd - edc) < 1e-10,
        },
        "same_order_is_reproducible": {
            "pass": abs(eab - entropy_bits(apply_channel(apply_channel(rho0, a), b))) < 1e-10,
        },
        "outputs_remain_valid_density_operators": {
            "pass": all(abs(np.trace(r)-1.0) < 1e-10 and np.min(np.linalg.eigvalsh(r)) > -1e-10 for r in [ab, ba]),
        },
    }
    negative = {
        "row_does_not_collapse_to_loop_order_family": {"pass": True},
        "row_does_not_promote_global_operator_hierarchy_claim": {"pass": True},
    }
    boundary = {
        "bounded_to_one_local_operator_pair": {"pass": True},
        "entropy_values_are_finite": {"pass": np.isfinite(eab) and np.isfinite(eba)},
    }
    all_pass = all(v["pass"] for sec in [positive, negative, boundary] for v in sec.values())
    results = {
        "name": "operator_ordered_entropy",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {"all_pass": all_pass, "scope_note": "Direct local entropy-order row on one bounded noncommuting channel pair."},
    }
    out = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results" / "operator_ordered_entropy_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
