#!/usr/bin/env python3
"""
PURE LEGO: Low-Rank PSD Approximation
=====================================
Direct local compression lego.

Construct low-rank trace-renormalized PSD approximations of bounded density operators
and verify PSD preservation, trace normalization, and monotone reconstruction quality.
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
    "Canonical local lego for low-rank PSD approximation with trace renormalization on bounded "
    "density operators."
)

LEGO_IDS = [
    "low_rank_psd_approximation",
    "spectral_truncation",
    "operator_low_rank_factorization",
]

PRIMARY_LEGO_IDS = [
    "low_rank_psd_approximation",
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


def random_density_matrix(d):
    G = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    rho = G @ G.conj().T
    return rho / np.trace(rho)


def fidelity(rho, sigma):
    sq_rho = sqrtm(rho)
    inner = sqrtm(sq_rho @ sigma @ sq_rho)
    f = np.real(np.trace(inner)) ** 2
    return float(np.clip(f, 0.0, 1.0))


def trace_distance(rho, sigma):
    diff = rho - sigma
    evals = np.linalg.eigvalsh(diff @ diff.conj().T)
    evals = np.maximum(evals, 0.0)
    return float(0.5 * np.sum(np.sqrt(evals)))


def is_valid_dm(rho, tol=1e-10):
    tr = np.real(np.trace(rho))
    herm = np.allclose(rho, rho.conj().T, atol=tol)
    evals = np.linalg.eigvalsh(rho)
    psd = bool(np.all(evals >= -tol))
    return {
        "trace_ok": bool(abs(tr - 1.0) < tol),
        "hermitian": bool(herm),
        "psd": psd,
        "rank": int(np.sum(evals > tol)),
    }


def low_rank_psd(rho, k):
    evals, evecs = np.linalg.eigh(rho)
    idx = np.argsort(evals)[::-1]
    evals = evals[idx]
    evecs = evecs[:, idx]
    top = np.maximum(evals[:k], 0.0)
    rho_k = evecs[:, :k] @ np.diag(top) @ evecs[:, :k].conj().T
    if np.trace(rho_k) > EPS:
        rho_k = rho_k / np.trace(rho_k)
    return rho_k, top


def main():
    states = {f"trial_{i}": random_density_matrix(4) for i in range(6)}
    positive = {}
    for name, rho in states.items():
        truncs = []
        prev_f = -1.0
        prev_t = 1e9
        mono_f = True
        mono_t = True
        for k in [1, 2, 3]:
            rho_k, top = low_rank_psd(rho, k)
            valid = is_valid_dm(rho_k)
            f = fidelity(rho, rho_k)
            t = trace_distance(rho, rho_k)
            truncs.append({
                "k": k,
                "retained_eigenvalues": [float(x) for x in top],
                "validity": valid,
                "fidelity": f,
                "trace_distance": t,
            })
            if f + 1e-10 < prev_f:
                mono_f = False
            if t - 1e-10 > prev_t:
                mono_t = False
            prev_f = f
            prev_t = t

        positive[name] = {
            "truncations": truncs,
            "psd_preserved": all(x["validity"]["psd"] for x in truncs),
            "trace_preserved": all(x["validity"]["trace_ok"] for x in truncs),
            "fidelity_monotone_in_k": mono_f,
            "trace_distance_nonincreasing_in_k": mono_t,
            "pass": (
                all(x["validity"]["psd"] for x in truncs)
                and all(x["validity"]["trace_ok"] for x in truncs)
                and mono_f
                and mono_t
            ),
        }

    negative = {
        "rank_one_not_exact_for_generic_mixed_states": {
            "pass": all(v["truncations"][0]["trace_distance"] > 1e-6 for v in positive.values()),
        }
    }

    boundary = {
        "rank_three_better_than_rank_one": {
            "pass": all(
                v["truncations"][2]["fidelity"] >= v["truncations"][0]["fidelity"] - 1e-10
                for v in positive.values()
            ),
        }
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "low_rank_psd_approximation",
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
            "scope_note": "Direct local low-rank PSD approximation lego with trace renormalization.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "low_rank_psd_approximation_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
