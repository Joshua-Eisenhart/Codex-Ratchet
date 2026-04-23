#!/usr/bin/env python3
"""
PURE LEGO: SVD Factorization
============================
Direct local compression lego.

Verify singular-value decomposition on bounded coefficient and operator matrices,
with exact reconstruction and rank-sensitive summaries.
"""

import json
import pathlib

import numpy as np
classification = "classical_baseline"  # auto-backfill


np.random.seed(42)
EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for singular-value factorization on bounded coefficient and "
    "operator matrices with exact reconstruction and rank-sensitive summaries."
)

LEGO_IDS = [
    "svd_factorization",
    "principal_subspace",
]

PRIMARY_LEGO_IDS = [
    "svd_factorization",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed -- pure numpy linear algebra lego"},
    "pyg": {"tried": False, "used": False, "reason": "not needed -- no graph-native computation"},
    "z3": {"tried": False, "used": False, "reason": "not needed -- no SMT proof layer here"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed -- no second-solver layer here"},
    "sympy": {"tried": False, "used": False, "reason": "not needed -- no symbolic derivation here"},
    "clifford": {"tried": False, "used": False, "reason": "not needed -- no geometric algebra"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed -- no manifold-statistics layer"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed -- no equivariant network layer"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed -- no dependency DAG"},
    "xgi": {"tried": False, "used": False, "reason": "not needed -- no hypergraph structure"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed -- no cell-complex topology"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed -- no persistent homology"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}


def ket(v):
    return np.array(v, dtype=complex).reshape(-1, 1)


def mps_decompose(psi_4, d=2):
    C = psi_4.reshape(d, d)
    U, S, Vh = np.linalg.svd(C)
    bond_dim = int(np.sum(S > EPS))
    A = U[:, :bond_dim] * S[:bond_dim]
    B = Vh[:bond_dim, :]
    psi_recon = (A @ B).flatten()
    recon_error = float(np.linalg.norm(psi_4 - psi_recon))
    return {
        "bond_dim": bond_dim,
        "singular_values": [float(x) for x in S],
        "reconstruction_error": recon_error,
        "pass": recon_error < 1e-10,
    }


def operator_svd(mat):
    U, S, Vh = np.linalg.svd(mat)
    recon = U @ np.diag(S) @ Vh
    recon_error = float(np.linalg.norm(mat - recon))
    return {
        "rank": int(np.sum(S > EPS)),
        "singular_values": [float(x) for x in S],
        "reconstruction_error": recon_error,
        "pass": recon_error < 1e-10,
    }


def main():
    k0 = ket([1, 0])
    k1 = ket([0, 1])
    product_psi = np.kron(k0, k0).flatten()
    bell_psi = (np.kron(k0, k0) + np.kron(k1, k1)).flatten() / np.sqrt(2)

    product = mps_decompose(product_psi)
    bell = mps_decompose(bell_psi)

    rho_product = np.outer(product_psi, product_psi.conj())
    rho_bell = np.outer(bell_psi, bell_psi.conj())
    op_prod = operator_svd(rho_product.reshape(4, 4))
    op_bell = operator_svd(rho_bell.reshape(4, 4))

    positive = {
        "product_state_factorization": {
            **product,
            "expected_bond_dim": 1,
            "pass": product["pass"] and product["bond_dim"] == 1,
        },
        "bell_state_factorization": {
            **bell,
            "expected_bond_dim": 2,
            "pass": bell["pass"] and bell["bond_dim"] == 2,
        },
        "product_operator_svd": op_prod,
        "bell_operator_svd": op_bell,
    }

    negative = {
        "product_not_rank_two": {
            "bond_dim": product["bond_dim"],
            "pass": product["bond_dim"] != 2,
        },
        "bell_not_rank_one": {
            "bond_dim": bell["bond_dim"],
            "pass": bell["bond_dim"] != 1,
        },
    }

    boundary = {
        "product_operator_rank_one": {
            "rank": op_prod["rank"],
            "pass": op_prod["rank"] == 1,
        },
        "bell_operator_rank_one_or_more": {
            "rank": op_bell["rank"],
            "pass": op_bell["rank"] >= 1,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "svd_factorization",
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
            "scope_note": "Direct local SVD lego on coefficient and operator matrices.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "svd_factorization_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
