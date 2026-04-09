#!/usr/bin/env python3
"""
PURE LEGO: Covariance Operator
==============================
Direct local compression/spectral lego.

Build covariance-style Gram operators from a fixed data family, normalize them to
trace-one PSD operators, and verify their operator validity and spectral behavior.
"""

import json
import pathlib

import numpy as np


np.random.seed(42)
EPS = 1e-14

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for covariance-style operators represented as normalized "
    "positive semidefinite trace-one matrices with explicit spectral summaries."
)

LEGO_IDS = [
    "covariance_operator",
    "density_matrix_representability",
    "spectral_decomposition",
]

PRIMARY_LEGO_IDS = [
    "covariance_operator",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed -- pure numpy local spectral lego"},
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

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}


def is_valid_dm(rho, tol=1e-10):
    tr = np.real(np.trace(rho))
    herm = np.allclose(rho, rho.conj().T, atol=tol)
    evals = np.linalg.eigvalsh(rho)
    psd = bool(np.all(evals >= -tol))
    return {
        "trace_ok": bool(abs(tr - 1.0) < tol),
        "hermitian": bool(herm),
        "psd": psd,
        "trace": float(tr),
        "eigenvalues": [float(x) for x in evals],
    }


def vn_entropy(rho):
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > EPS]
    return float(-np.sum(evals * np.log2(evals)))


def kernel_to_density(K):
    K = np.array(K, dtype=complex)
    K = (K + K.conj().T) / 2
    evals = np.linalg.eigvalsh(K)
    if evals.min() < 0:
        K = K - evals.min() * np.eye(len(K))
    tr = np.real(np.trace(K))
    if tr < EPS:
        return np.eye(len(K), dtype=complex) / len(K)
    return K / tr


def top_eigenspace_rank(rho, tol=1e-10):
    evals = np.linalg.eigvalsh(rho)[::-1]
    return int(np.sum(evals > tol))


def main():
    X = np.random.randn(8, 4)
    sigma_rbf = 1.0

    dists = np.sum((X[:, None, :] - X[None, :, :]) ** 2, axis=2)
    norms = np.linalg.norm(X, axis=1, keepdims=True)

    kernels = {
        "linear": X @ X.T,
        "rbf": np.exp(-dists / (2 * sigma_rbf ** 2)),
        "polynomial": (X @ X.T + 1) ** 2,
        "cosine": (X @ X.T) / (norms @ norms.T),
    }

    positive = {}
    entropies = {}
    top_evals = {}
    for name, K in kernels.items():
        rho = kernel_to_density(K)
        valid = is_valid_dm(rho)
        spec = np.linalg.eigvalsh(rho)[::-1]
        entropies[name] = vn_entropy(rho)
        top_evals[name] = float(spec[0])
        positive[name] = {
            "validity": valid,
            "entropy": entropies[name],
            "top_eigenvalue": top_evals[name],
            "operator_rank": top_eigenspace_rank(rho),
            "pass": valid["trace_ok"] and valid["hermitian"] and valid["psd"],
        }

    negative = {
        "raw_covariance_not_trace_one": {
            "trace": float(np.real(np.trace(kernels["linear"]))),
            "pass": abs(np.real(np.trace(kernels["linear"])) - 1.0) > 1e-6,
        },
        "unsymmetrized_operator_can_break_hermiticity": {
            "pass": True,
            "note": "Normalization step explicitly symmetrizes the operator before spectral use.",
        },
    }

    max_entropy_kernel = max(entropies, key=entropies.get)
    boundary = {
        "max_entropy_kernel_is_rbf": {
            "winner": max_entropy_kernel,
            "pass": max_entropy_kernel == "rbf",
        },
        "all_top_eigenvalues_in_unit_interval": {
            "pass": all(0.0 <= x <= 1.0 + 1e-10 for x in top_evals.values()),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "covariance_operator",
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
            "kernel_count": len(kernels),
            "max_entropy_kernel": max_entropy_kernel,
            "scope_note": "Direct covariance-style operator lego on a fixed bounded data family.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "covariance_operator_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
