#!/usr/bin/env python3
"""
PURE LEGO: Operator Low-Rank Factorization
==========================================
Direct local compression lego.

Factorize bounded Hermitian PSD operators into low-rank forms, reconstruct them,
and compare induced action on a fixed small state family.
"""

import json
import pathlib

import numpy as np
classification = "classical_baseline"  # auto-backfill


np.random.seed(42)
EPS = 1e-14

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for low-rank factorization of bounded Hermitian PSD operators "
    "and comparison of their induced action on a fixed state family."
)

LEGO_IDS = [
    "operator_low_rank_factorization",
    "low_rank_psd_approximation",
    "principal_subspace",
]

PRIMARY_LEGO_IDS = [
    "operator_low_rank_factorization",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed -- pure numpy factorization lego"},
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


def random_psd_operator(d):
    G = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    O = G @ G.conj().T
    return (O + O.conj().T) / 2


def normalize_state(v):
    n = np.linalg.norm(v)
    return v / n if n > EPS else v


def rank_k_factorization(O, k):
    evals, evecs = np.linalg.eigh(O)
    idx = np.argsort(evals)[::-1]
    evals = np.maximum(evals[idx], 0.0)
    evecs = evecs[:, idx]
    top = evals[:k]
    U = evecs[:, :k] @ np.diag(np.sqrt(top))
    recon = U @ U.conj().T
    return recon, U, top


def state_output(O, psi):
    out = O @ psi
    return normalize_state(out)


def state_fidelity(psi, phi):
    return float(abs(np.vdot(psi, phi)) ** 2)


def main():
    operators = {f"op_{i}": random_psd_operator(4) for i in range(3)}
    states = {
        "basis_0": normalize_state(np.array([1, 0, 0, 0], dtype=complex)),
        "basis_1": normalize_state(np.array([0, 1, 0, 0], dtype=complex)),
        "superposition": normalize_state(np.array([1, 1, 1, 1], dtype=complex)),
    }

    positive = {}
    for name, O in operators.items():
        truncs = []
        prev_err = 1e9
        prev_out = -1.0
        mono_err = True
        mono_out = True
        for k in [1, 2, 3, 4]:
            O_k, U, top = rank_k_factorization(O, k)
            fro_err = float(np.linalg.norm(O - O_k, "fro"))
            if fro_err - 1e-10 > prev_err:
                mono_err = False
            prev_err = fro_err

            output_fids = {}
            min_fid = 1.0
            for sname, psi in states.items():
                full = state_output(O, psi)
                trunc = state_output(O_k, psi)
                fid = state_fidelity(full, trunc)
                output_fids[sname] = fid
                min_fid = min(min_fid, fid)
            if min_fid + 1e-10 < prev_out:
                mono_out = False
            prev_out = min_fid

            truncs.append({
                "k": k,
                "retained_eigenvalues": [float(x) for x in top],
                "factor_shape": list(U.shape),
                "frobenius_error": fro_err,
                "min_output_fidelity": min_fid,
            })

        positive[name] = {
            "truncations": truncs,
            "frobenius_error_nonincreasing": mono_err,
            "output_fidelity_nondecreasing": mono_out,
            "exact_recovery_at_full_rank": truncs[-1]["frobenius_error"] < 1e-10,
            "pass": mono_err and mono_out and truncs[-1]["frobenius_error"] < 1e-10,
        }

    negative = {
        "rank_one_not_exact_for_generic_operator": {
            "pass": all(v["truncations"][0]["frobenius_error"] > 1e-6 for v in positive.values()),
        }
    }

    boundary = {
        "full_rank_factorization_exact": {
            "pass": all(v["exact_recovery_at_full_rank"] for v in positive.values()),
        }
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "operator_low_rank_factorization",
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
            "operator_count": len(operators),
            "state_count": len(states),
            "scope_note": "Direct local operator factorization lego on bounded PSD operators.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "operator_low_rank_factorization_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
