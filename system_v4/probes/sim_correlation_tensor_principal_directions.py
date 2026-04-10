#!/usr/bin/env python3
"""
PURE LEGO: Correlation-Tensor Principal Directions
==================================================
Direct local bipartite lego for principal directions of two-qubit correlation tensors.
"""

import json
import pathlib

import numpy as np


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for principal directions of bounded two-qubit correlation tensors, "
    "kept separate from graph proxies and later coupling surfaces."
)

LEGO_IDS = [
    "correlation_tensor_principal_directions",
]

PRIMARY_LEGO_IDS = [
    "correlation_tensor_principal_directions",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed -- direct tensor object, no graph proxy"},
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

SX = np.array([[0, 1], [1, 0]], dtype=complex)
SY = np.array([[0, -1j], [1j, 0]], dtype=complex)
SZ = np.array([[1, 0], [0, -1]], dtype=complex)
PAULIS = [SX, SY, SZ]


def ket(v):
    return np.array(v, dtype=complex).reshape(-1, 1)


def dm(v):
    k = ket(v).flatten()
    return np.outer(k, k.conj())


def werner_state(r):
    bell = (np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2.0))
    return (1.0 - r) * np.eye(4, dtype=complex) / 4.0 + r * np.outer(bell, bell.conj())


def correlation_tensor(rho):
    tensor = np.zeros((3, 3), dtype=float)
    for i, a in enumerate(PAULIS):
        for j, b in enumerate(PAULIS):
            tensor[i, j] = float(np.real(np.trace(rho @ np.kron(a, b))))
    return tensor


def principal_data(tensor):
    u, s, vh = np.linalg.svd(tensor)
    return {
        "singular_values": [float(x) for x in s],
        "left_principal_axis": [float(x) for x in u[:, 0]],
        "right_principal_axis": [float(x) for x in vh[0, :]],
        "rank": int(np.sum(s > 1e-8)),
    }


def main():
    k0 = [1, 0]
    k1 = [0, 1]

    rho_prod = dm(np.kron(k0, k0))
    rho_bell = dm((np.kron(k0, k0) + np.kron(k1, k1)) / np.sqrt(2.0))
    rho_classical = 0.5 * dm(np.kron(k0, k0)) + 0.5 * dm(np.kron(k1, k1))
    rho_werner = werner_state(0.6)

    t_prod = correlation_tensor(rho_prod)
    t_bell = correlation_tensor(rho_bell)
    t_classical = correlation_tensor(rho_classical)
    t_werner = correlation_tensor(rho_werner)

    p_prod = principal_data(t_prod)
    p_bell = principal_data(t_bell)
    p_classical = principal_data(t_classical)
    p_werner = principal_data(t_werner)

    positive = {
        "product_and_classical_rows_have_single_dominant_principal_direction": {
            "product_rank": p_prod["rank"],
            "classical_rank": p_classical["rank"],
            "pass": p_prod["rank"] == 1 and p_classical["rank"] == 1,
        },
        "bell_state_has_three_nonzero_principal_directions": {
            "bell_rank": p_bell["rank"],
            "bell_singular_values": p_bell["singular_values"],
            "pass": p_bell["rank"] == 3,
        },
        "werner_state_retains_isotropic_principal_structure": {
            "werner_singular_values": p_werner["singular_values"],
            "pass": max(p_werner["singular_values"]) - min(p_werner["singular_values"]) < 1e-8,
        },
    }

    negative = {
        "bell_and_classical_principal_spectra_are_not_same": {
            "pass": not np.allclose(p_bell["singular_values"], p_classical["singular_values"], atol=EPS),
        },
        "product_and_werner_do_not_share_same_rank": {
            "pass": p_prod["rank"] != p_werner["rank"],
        },
    }

    boundary = {
        "product_and_classical_align_with_z_axis": {
            "product_axis": p_prod["left_principal_axis"],
            "classical_axis": p_classical["left_principal_axis"],
            "pass": abs(abs(p_prod["left_principal_axis"][2]) - 1.0) < 1e-8
            and abs(abs(p_classical["left_principal_axis"][2]) - 1.0) < 1e-8,
        },
        "singular_values_stay_in_physical_range": {
            "pass": all(
                max(data["singular_values"]) <= 1.0 + EPS
                for data in [p_prod, p_bell, p_classical, p_werner]
            ),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "correlation_tensor_principal_directions",
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
            "scope_note": "Direct local principal-direction lego on bounded two-qubit correlation tensors.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "correlation_tensor_principal_directions_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
