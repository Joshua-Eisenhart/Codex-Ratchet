#!/usr/bin/env python3
"""
PURE LEGO: Spectral Truncation
==============================
Direct local compression lego.

Truncate bounded density operators to their top-k spectral modes and verify the
expected monotone reconstruction behavior.
"""

import json
import pathlib

import numpy as np
from scipy.linalg import sqrtm


np.random.seed(42)
EPS = 1e-14

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for spectral truncation on bounded density operators with "
    "explicit fidelity and trace-distance improvement as k increases."
)

LEGO_IDS = [
    "spectral_truncation",
    "qpca_spectral_extraction",
    "low_rank_psd_approximation",
    "principal_subspace",
]

PRIMARY_LEGO_IDS = [
    "spectral_truncation",
    "qpca_spectral_extraction",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed -- pure numpy/scipy spectral lego"},
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


def von_neumann_entropy(rho):
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > EPS]
    return float(-np.sum(evals * np.log2(evals)))


def fidelity(rho, sigma):
    sq_rho = sqrtm(rho)
    product = sq_rho @ sigma @ sq_rho
    evals = np.linalg.eigvalsh(product)
    evals = np.maximum(evals, 0.0)
    return float(np.sum(np.sqrt(evals))) ** 2


def trace_distance(rho, sigma):
    diff = rho - sigma
    evals = np.linalg.eigvalsh(diff @ diff.conj().T)
    evals = np.maximum(evals, 0.0)
    return float(0.5 * np.sum(np.sqrt(evals)))


def random_density_matrix(d):
    G = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    rho = G @ G.conj().T
    return rho / np.trace(rho)


def quantum_pca(rho, k):
    evals, evecs = np.linalg.eigh(rho)
    idx = np.argsort(evals)[::-1]
    evals = evals[idx]
    evecs = evecs[:, idx]
    top_evals = evals[:k]
    top_evecs = evecs[:, :k]
    rho_k = top_evecs @ np.diag(top_evals) @ top_evecs.conj().T
    if np.trace(rho_k) > EPS:
        rho_k = rho_k / np.trace(rho_k)
    return rho_k, top_evals


def main():
    states = {
        "rank_2_mixed": random_density_matrix(4),
        "rank_3_mixed": random_density_matrix(4),
        "rank_4_mixed": random_density_matrix(4),
    }

    positive = {}
    for name, rho in states.items():
        s_full = von_neumann_entropy(rho)
        truncs = []
        prev_f = -1.0
        prev_t = 1e9
        monotone_f = True
        monotone_t = True
        for k in range(1, 5):
            rho_k, top_evals = quantum_pca(rho, k)
            f = fidelity(rho, rho_k)
            t = trace_distance(rho, rho_k)
            truncs.append({
                "k": k,
                "top_eigenvalues": [float(x) for x in top_evals],
                "fidelity": float(f),
                "trace_distance": float(t),
                "entropy_ratio": float(von_neumann_entropy(rho_k) / s_full) if s_full > EPS else 1.0,
            })
            if f + 1e-10 < prev_f:
                monotone_f = False
            if t - 1e-10 > prev_t:
                monotone_t = False
            prev_f = f
            prev_t = t

        positive[name] = {
            "truncations": truncs,
            "fidelity_monotone_in_k": monotone_f,
            "trace_distance_nonincreasing_in_k": monotone_t,
            "exact_recovery_at_full_rank": bool(truncs[-1]["trace_distance"] < 1e-10),
            "pass": monotone_f and monotone_t and bool(truncs[-1]["trace_distance"] < 1e-10),
        }

    negative = {
        "rank_1_truncation_not_exact_for_mixed_states": {
            "pass": all(v["truncations"][0]["trace_distance"] > 1e-6 for v in positive.values()),
        }
    }

    boundary = {
        "full_rank_truncation_is_exact": {
            "pass": all(v["exact_recovery_at_full_rank"] for v in positive.values()),
        }
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "spectral_truncation",
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
            "state_count": len(states),
            "scope_note": "Direct local spectral truncation lego on bounded density operators.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "spectral_truncation_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
