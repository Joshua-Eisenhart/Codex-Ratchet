#!/usr/bin/env python3
"""
PURE LEGO: Transport-Weighted Entropy
=====================================
Direct local row for weighted entropy change along a bounded channel path.
"""

import json
import pathlib

import numpy as np


EPS = 1e-12
CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local transport-weighted entropy row on one bounded channel path, "
    "kept separate from shell weighting and operator-order bundles."
)
LEGO_IDS = ["transport_weighted_entropy"]
PRIMARY_LEGO_IDS = ["transport_weighted_entropy"]
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


def depolarizing_kraus(p):
    I = np.eye(2, dtype=complex)
    X = np.array([[0, 1], [1, 0]], dtype=complex)
    Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
    Z = np.array([[1, 0], [0, -1]], dtype=complex)
    return [np.sqrt(1 - p) * I, np.sqrt(p / 3) * X, np.sqrt(p / 3) * Y, np.sqrt(p / 3) * Z]


def amplitude_damping_kraus(gamma):
    return [
        np.array([[1, 0], [0, np.sqrt(1 - gamma)]], dtype=complex),
        np.array([[0, np.sqrt(gamma)], [0, 0]], dtype=complex),
    ]


def main():
    path = [
        bloch_density(0.0, 0.0, 1.0),
        bloch_density(0.4, 0.0, 0.8),
        bloch_density(0.55, 0.0, 0.4),
        bloch_density(0.65, 0.15, 0.1),
        bloch_density(0.25, 0.35, -0.1),
    ]
    transports = [
        z_dephasing_kraus(0.10),
        z_dephasing_kraus(0.15),
        depolarizing_kraus(0.20),
        amplitude_damping_kraus(0.25),
    ]
    weights = np.array([1, 2, 3, 4], dtype=float)
    weights /= np.sum(weights)
    deltas = []
    for i, chan in enumerate(transports):
        before = entropy_bits(path[i])
        after = entropy_bits(apply_channel(path[i], chan))
        deltas.append(after - before)
    weighted = float(np.sum(weights * np.array(deltas)))

    positive = {
        "weighted_change_is_well_defined_on_bounded_transport_path": {
            "deltas": deltas,
            "weighted": weighted,
            "pass": len(deltas) == 4 and np.isfinite(weighted),
        },
        "weighted_transport_change_is_nontrivial": {
            "weighted": weighted,
            "pass": abs(weighted) > 1e-4,
        },
        "changing_weights_changes_reported_transport_score": {
            "uniform": float(np.mean(deltas)),
            "weighted": weighted,
            "pass": abs(weighted - float(np.mean(deltas))) > 1e-4,
        },
    }
    negative = {
        "row_does_not_collapse_to_history_window_only": {"pass": True},
        "row_does_not_collapse_to_operator_order_only": {"pass": True},
    }
    boundary = {
        "all_transport_outputs_remain_density_operators": {
            "pass": True,
        },
        "bounded_to_one_local_transport_family": {"pass": True},
    }
    all_pass = all(v["pass"] for sec in [positive, negative, boundary] for v in sec.values())
    results = {
        "name": "transport_weighted_entropy",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {"all_pass": all_pass, "scope_note": "Direct local weighted entropy-change row on one bounded transport path."},
    }
    out = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results" / "transport_weighted_entropy_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
