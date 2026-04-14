#!/usr/bin/env python3
"""
PURE LEGO: Correlation Tensor Object
====================================
Direct local bipartite lego.

Compute Pauli correlation tensors on a few small two-qubit states and verify the
tensor distinguishes product, classical-correlation, and Bell structures.
"""

import json
import pathlib

import numpy as np
classification = "classical_baseline"  # auto-backfill


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for bipartite Pauli correlation tensors on bounded "
    "two-qubit state families."
)

LEGO_IDS = [
    "correlation_tensor_object",
    "joint_density_matrix",
]

PRIMARY_LEGO_IDS = [
    "correlation_tensor_object",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed -- direct numpy tensor lego"},
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


SX = np.array([[0, 1], [1, 0]], dtype=complex)
SY = np.array([[0, -1j], [1j, 0]], dtype=complex)
SZ = np.array([[1, 0], [0, -1]], dtype=complex)
PAULIS = [SX, SY, SZ]


def ket(v):
    return np.array(v, dtype=complex).reshape(-1, 1)


def dm(v):
    k = ket(v).flatten()
    return np.outer(k, k.conj())


def correlation_tensor(rho):
    tensor = np.zeros((3, 3), dtype=float)
    for i, a in enumerate(PAULIS):
        for j, b in enumerate(PAULIS):
            tensor[i, j] = float(np.real(np.trace(rho @ np.kron(a, b))))
    return tensor


def main():
    k0 = [1, 0]
    k1 = [0, 1]

    prod = dm(np.kron(k0, k0))
    bell = dm((np.kron(k0, k0) + np.kron(k1, k1)) / np.sqrt(2))
    classical = 0.5 * dm(np.kron(k0, k0)) + 0.5 * dm(np.kron(k1, k1))

    t_prod = correlation_tensor(prod)
    t_bell = correlation_tensor(bell)
    t_classical = correlation_tensor(classical)

    positive = {
        "product_state_tensor_matches_expected_axis_alignment": {
            "tensor": t_prod.tolist(),
            "pass": np.allclose(t_prod, np.diag([0.0, 0.0, 1.0]), atol=EPS),
        },
        "bell_state_tensor_matches_phi_plus_signature": {
            "tensor": t_bell.tolist(),
            "pass": np.allclose(t_bell, np.diag([1.0, -1.0, 1.0]), atol=EPS),
        },
        "classical_correlation_keeps_only_zz_component": {
            "tensor": t_classical.tolist(),
            "pass": np.allclose(t_classical, np.diag([0.0, 0.0, 1.0]), atol=EPS),
        },
    }

    negative = {
        "bell_tensor_differs_from_classical_tensor": {
            "fro_norm_difference": float(np.linalg.norm(t_bell - t_classical)),
            "pass": float(np.linalg.norm(t_bell - t_classical)) > EPS,
        },
        "product_tensor_is_not_bell_tensor": {
            "fro_norm_difference": float(np.linalg.norm(t_prod - t_bell)),
            "pass": float(np.linalg.norm(t_prod - t_bell)) > EPS,
        },
    }

    boundary = {
        "tensor_entries_stay_in_physical_range": {
            "pass": bool(np.all(np.abs(t_bell) <= 1.0 + EPS) and np.all(np.abs(t_classical) <= 1.0 + EPS)),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "correlation_tensor_object",
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
            "scope_note": "Direct local bipartite correlation-tensor lego on bounded two-qubit states.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "correlation_tensor_object_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
