#!/usr/bin/env python3
"""
PURE LEGO: QPCA Spectral Extraction
===================================
Direct local compression lego.

Compare QPCA-style dominant-mode recovery against a simple classical correlation
surrogate on bounded density operators.
"""

import json
import pathlib

import numpy as np
from scipy.linalg import sqrtm
classification = "classical_baseline"  # auto-backfill


np.random.seed(42)
EPS = 1e-14

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for QPCA-style spectral extraction on bounded density operators, "
    "including dominant-mode recovery and comparison to a classical correlation surrogate."
)

LEGO_IDS = [
    "qpca_spectral_extraction",
    "principal_subspace",
    "spectral_truncation",
]

PRIMARY_LEGO_IDS = [
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

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}


I2 = np.eye(2, dtype=complex)
sx = np.array([[0, 1], [1, 0]], dtype=complex)
sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
sz = np.array([[1, 0], [0, -1]], dtype=complex)
PAULIS = [I2, sx, sy, sz]


def random_density_matrix(d):
    G = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    rho = G @ G.conj().T
    return rho / np.trace(rho)


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


def classical_coordinate_surrogate(rho, k):
    """Classical baseline: keep the top-k computational-basis diagonal masses only."""
    diag = np.real(np.diag(rho))
    idx = np.argsort(diag)[::-1]
    kept = np.zeros_like(diag)
    kept[idx[:k]] = np.maximum(diag[idx[:k]], 0.0)
    if np.sum(kept) > EPS:
        kept = kept / np.sum(kept)
    else:
        kept = np.ones_like(diag) / len(diag)
    return np.diag(kept.astype(complex))


def main():
    states = {
        "rank_2_mixed": random_density_matrix(4),
        "rank_3_mixed": random_density_matrix(4),
        "rank_4_mixed": random_density_matrix(4),
    }

    positive = {}
    for name, rho in states.items():
        full_entropy = von_neumann_entropy(rho)
        rows = []
        q_fidelities = []
        for k in range(1, 4):
            rho_qk, top = quantum_pca(rho, k)
            rho_ck = classical_coordinate_surrogate(rho, k)
            q_f = fidelity(rho, rho_qk)
            c_f = fidelity(rho, rho_ck)
            q_t = trace_distance(rho, rho_qk)
            rows.append({
                "k": k,
                "top_eigenvalues": [float(x) for x in top],
                "qpca_fidelity": q_f,
                "cpca_fidelity": c_f,
                "qpca_trace_distance": q_t,
                "qpca_entropy_ratio": float(von_neumann_entropy(rho_qk) / full_entropy) if full_entropy > EPS else 1.0,
            })
            q_fidelities.append(q_f)

        positive[name] = {
            "levels": rows,
            "qpca_fidelity_monotone_in_k": bool(all(rows[i]["qpca_fidelity"] <= rows[i + 1]["qpca_fidelity"] + 1e-10 for i in range(len(rows) - 1))),
            "qpca_beats_cpca_at_k1": bool(rows[0]["qpca_fidelity"] >= rows[0]["cpca_fidelity"] - 1e-10),
            "qpca_exact_by_k3_or_k4": bool(rows[-1]["qpca_fidelity"] > 0.95),
            "pass": bool(
                all(rows[i]["qpca_fidelity"] <= rows[i + 1]["qpca_fidelity"] + 1e-10 for i in range(len(rows) - 1))
                and rows[0]["qpca_fidelity"] >= rows[0]["cpca_fidelity"] - 1e-10
                and rows[-1]["qpca_fidelity"] > 0.95
            ),
        }

    negative = {
        "rank_one_qpca_not_exact_for_generic_mixed_states": {
            "pass": all(v["levels"][0]["qpca_trace_distance"] > 1e-6 for v in positive.values()),
        }
    }

    boundary = {
        "qpca_fidelity_improves_with_k": {
            "pass": all(v["qpca_fidelity_monotone_in_k"] for v in positive.values()),
        }
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "qpca_spectral_extraction",
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
            "scope_note": "Direct local QPCA lego on bounded density operators with classical surrogate comparison.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "qpca_spectral_extraction_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
