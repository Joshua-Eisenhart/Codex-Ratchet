#!/usr/bin/env python3
"""
sim_lego_entropy_relative_js.py
===============================

Pure-math lego for entropy/divergence families on quantum states.

Verifies:
  - Quantum relative entropy D(rho || sigma)
  - Relative entropy to maximally mixed state
  - Quantum Jensen-Shannon divergence
  - Classical reduction on commuting (diagonal) states

Non-metric caveats:
  - Relative entropy is not symmetric and is not a metric.
  - It can be infinite when supports do not match.
  - Jensen-Shannon divergence is bounded and symmetric here, but we do
    not claim metric structure from the raw divergence value.

Outputs JSON to:
  system_v4/probes/a2_state/sim_results/sim_lego_entropy_relative_js_results.json
"""

import json
import os
from datetime import datetime, timezone

import numpy as np
classification = "classical_baseline"  # auto-backfill

EPS = 1e-12

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed; pure numpy lego"},
    "pyg": {"tried": False, "used": False, "reason": "not needed; no graph computation"},
    "z3": {"tried": False, "used": False, "reason": "not needed; numeric divergence check"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed; numeric divergence check"},
    "sympy": {"tried": False, "used": False, "reason": "not needed; analytic identities are numeric here"},
    "clifford": {"tried": False, "used": False, "reason": "not needed; no geometric algebra"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed; no manifold geometry"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed; no equivariant computation"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed; no dependency DAG"},
    "xgi": {"tried": False, "used": False, "reason": "not needed; no hypergraph structure"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed; no cell-complex structure"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed; no persistent homology"},
}


def _hermitian(M):
    return 0.5 * (M + M.conj().T)


def _eigvals_psd(M):
    evals = np.linalg.eigvalsh(_hermitian(M))
    return np.maximum(evals, 0.0)


def _matrix_log2_psd(M):
    evals, evecs = np.linalg.eigh(_hermitian(M))
    evals = np.maximum(evals, EPS)
    return (evecs * np.log2(evals)) @ evecs.conj().T


def entropy_vn_bits(rho):
    evals = _eigvals_psd(rho)
    evals = evals[evals > EPS]
    if evals.size == 0:
        return 0.0
    return float(-np.sum(evals * np.log2(evals)))


def support_outside_sigma(rho, sigma):
    evals_sigma, evecs_sigma = np.linalg.eigh(_hermitian(sigma))
    null_mask = evals_sigma < 1e-12
    if not np.any(null_mask):
        return False
    null_basis = evecs_sigma[:, null_mask]
    leak = np.real(np.trace(null_basis.conj().T @ rho @ null_basis))
    return leak > 1e-10


def relative_entropy_bits(rho, sigma):
    if support_outside_sigma(rho, sigma):
        return float("inf")
    log_rho = _matrix_log2_psd(rho)
    log_sigma = _matrix_log2_psd(sigma)
    val = np.trace(_hermitian(rho) @ (log_rho - log_sigma))
    val = float(np.real(val))
    if val < -1e-9:
        return float("inf")
    return max(0.0, val)


def quantum_js_divergence_bits(rho, sigma):
    mid = 0.5 * (_hermitian(rho) + _hermitian(sigma))
    return 0.5 * relative_entropy_bits(rho, mid) + 0.5 * relative_entropy_bits(sigma, mid)


def classical_kl_bits(p, q):
    p = np.asarray(p, dtype=float)
    q = np.asarray(q, dtype=float)
    mask = p > EPS
    if np.any((q <= EPS) & mask):
        return float("inf")
    return float(np.sum(p[mask] * np.log2(p[mask] / q[mask])))


def classical_js_bits(p, q):
    m = 0.5 * (np.asarray(p, dtype=float) + np.asarray(q, dtype=float))
    return 0.5 * classical_kl_bits(p, m) + 0.5 * classical_kl_bits(q, m)


def dm_from_bloch(x, y, z):
    return 0.5 * np.array([[1 + z, x - 1j * y], [x + 1j * y, 1 - z]], dtype=np.complex128)


def state(name, rho):
    return {"name": name, "rho": rho, "entropy_bits": entropy_vn_bits(rho)}


def positive_tests():
    results = {}

    rho_diag = np.diag([0.7, 0.3]).astype(np.complex128)
    sigma_diag = np.diag([0.4, 0.6]).astype(np.complex128)
    rho_noncomm = dm_from_bloch(0.6, 0.0, 0.0)   # full-rank, off-diagonal
    sigma_noncomm = dm_from_bloch(0.0, 0.0, -0.2)  # full-rank, diagonal
    maximally_mixed = np.eye(2, dtype=np.complex128) / 2.0

    d_rho_sigma = relative_entropy_bits(rho_noncomm, sigma_noncomm)
    d_sigma_rho = relative_entropy_bits(sigma_noncomm, rho_noncomm)
    d_self = relative_entropy_bits(rho_diag, rho_diag)

    results["P1_relative_entropy_axioms"] = {
        "test": "relative entropy is nonnegative, zero on identical states, asymmetric on generic pairs",
        "D_rho_sigma_bits": d_rho_sigma,
        "D_sigma_rho_bits": d_sigma_rho,
        "D_self_bits": d_self,
        "nonnegative": d_rho_sigma >= -1e-10 and d_sigma_rho >= -1e-10,
        "identity_of_indiscernibles": abs(d_self) < 1e-12,
        "asymmetry_detected": abs(d_rho_sigma - d_sigma_rho) > 1e-4,
        "pass": d_rho_sigma >= -1e-10 and d_sigma_rho >= -1e-10 and abs(d_self) < 1e-12 and abs(d_rho_sigma - d_sigma_rho) > 1e-4,
    }

    d_mm = relative_entropy_bits(rho_noncomm, maximally_mixed)
    entropy_rho = entropy_vn_bits(rho_noncomm)
    expected_mm = 1.0 - entropy_rho

    results["P2_relative_entropy_to_maximally_mixed"] = {
        "test": "D(rho || I/2) = 1 - S(rho) in bits for qubits",
        "D_rho_mm_bits": d_mm,
        "entropy_rho_bits": entropy_rho,
        "expected_bits": expected_mm,
        "abs_error": abs(d_mm - expected_mm),
        "pass": abs(d_mm - expected_mm) < 1e-10,
    }

    js_rho_sigma = quantum_js_divergence_bits(rho_noncomm, sigma_noncomm)
    js_sigma_rho = quantum_js_divergence_bits(sigma_noncomm, rho_noncomm)
    js_self = quantum_js_divergence_bits(rho_diag, rho_diag)

    results["P3_jensen_shannon_divergence"] = {
        "test": "quantum Jensen-Shannon divergence is symmetric and bounded on qubits",
        "JS_rho_sigma_bits": js_rho_sigma,
        "JS_sigma_rho_bits": js_sigma_rho,
        "JS_self_bits": js_self,
        "symmetric": abs(js_rho_sigma - js_sigma_rho) < 1e-12,
        "bounded": 0.0 <= js_rho_sigma <= 1.0 + 1e-10 and 0.0 <= js_sigma_rho <= 1.0 + 1e-10,
        "zero_on_identity": abs(js_self) < 1e-12,
        "pass": abs(js_rho_sigma - js_sigma_rho) < 1e-12 and 0.0 <= js_rho_sigma <= 1.0 + 1e-10 and abs(js_self) < 1e-12,
    }

    p = np.array([0.7, 0.3], dtype=float)
    q = np.array([0.4, 0.6], dtype=float)
    classical_kl = classical_kl_bits(p, q)
    classical_js = classical_js_bits(p, q)

    results["P4_commuting_reduction"] = {
        "test": "diagonal states reduce exactly to classical KL and JS divergences",
        "quantum_relative_entropy_bits": relative_entropy_bits(rho_diag, sigma_diag),
        "classical_kl_bits": classical_kl,
        "relative_entropy_error": abs(relative_entropy_bits(rho_diag, sigma_diag) - classical_kl),
        "quantum_js_bits": quantum_js_divergence_bits(rho_diag, sigma_diag),
        "classical_js_bits": classical_js,
        "js_error": abs(quantum_js_divergence_bits(rho_diag, sigma_diag) - classical_js),
        "pass": (
            abs(relative_entropy_bits(rho_diag, sigma_diag) - classical_kl) < 1e-12
            and abs(quantum_js_divergence_bits(rho_diag, sigma_diag) - classical_js) < 1e-12
        ),
    }

    return results


def negative_tests():
    results = {}

    rho = dm_from_bloch(0.6, 0.0, 0.0)
    sigma = np.diag([0.85, 0.15]).astype(np.complex128)

    d_rho_sigma = relative_entropy_bits(rho, sigma)
    d_sigma_rho = relative_entropy_bits(sigma, rho)

    results["N1_relative_entropy_not_symmetric"] = {
        "test": "relative entropy should fail symmetry for a generic noncommuting pair",
        "D_rho_sigma_bits": d_rho_sigma,
        "D_sigma_rho_bits": d_sigma_rho,
        "symmetry_gap": abs(d_rho_sigma - d_sigma_rho),
        "pass": abs(d_rho_sigma - d_sigma_rho) > 1e-4,
    }

    pure_0 = np.array([[1, 0], [0, 0]], dtype=np.complex128)
    pure_1 = np.array([[0, 0], [0, 1]], dtype=np.complex128)
    d01 = relative_entropy_bits(pure_0, pure_1)
    d10 = relative_entropy_bits(pure_1, pure_0)

    results["N2_support_mismatch_produces_infinite_divergence"] = {
        "test": "support mismatch should trigger infinite relative entropy",
        "D_0_to_1": d01,
        "D_1_to_0": d10,
        "support_mismatch_detected": np.isinf(d01) and np.isinf(d10),
        "pass": np.isinf(d01) and np.isinf(d10),
    }

    return results


def boundary_tests():
    results = {}

    pure_0 = np.array([[1, 0], [0, 0]], dtype=np.complex128)
    pure_1 = np.array([[0, 0], [0, 1]], dtype=np.complex128)
    maximally_mixed = np.eye(2, dtype=np.complex128) / 2.0

    js_orthogonal = quantum_js_divergence_bits(pure_0, pure_1)
    d_0_1 = relative_entropy_bits(pure_0, pure_1)
    d_1_0 = relative_entropy_bits(pure_1, pure_0)
    d_0_mm = relative_entropy_bits(pure_0, maximally_mixed)

    results["B1_orthogonal_pure_states"] = {
        "test": "orthogonal pure states give infinite relative entropy and maximal JS on qubits",
        "D_0_to_1": d_0_1,
        "D_1_to_0": d_1_0,
        "JS_0_1_bits": js_orthogonal,
        "D_0_to_mm_bits": d_0_mm,
        "relative_entropy_infinite": np.isinf(d_0_1) and np.isinf(d_1_0),
        "js_maximal": abs(js_orthogonal - 1.0) < 1e-12,
        "mm_identity": abs(d_0_mm - 1.0) < 1e-12,
        "pass": np.isinf(d_0_1) and np.isinf(d_1_0) and abs(js_orthogonal - 1.0) < 1e-12 and abs(d_0_mm - 1.0) < 1e-12,
    }

    d_mm_mm = relative_entropy_bits(maximally_mixed, maximally_mixed)
    js_mm_mm = quantum_js_divergence_bits(maximally_mixed, maximally_mixed)

    results["B2_maximally_mixed_fixed_point"] = {
        "test": "maximally mixed state is a zero point for both divergences against itself",
        "D_mm_mm_bits": d_mm_mm,
        "JS_mm_mm_bits": js_mm_mm,
        "pass": abs(d_mm_mm) < 1e-12 and abs(js_mm_mm) < 1e-12,
    }

    return results


def main():
    positive = positive_tests()
    negative = negative_tests()
    boundary = boundary_tests()

    all_tests = {}
    for section in (positive, negative, boundary):
        for name, test in section.items():
            all_tests[name] = bool(test.get("pass", False))

    n_pass = sum(1 for ok in all_tests.values() if ok)
    n_total = len(all_tests)

    results = {
        "name": "sim_lego_entropy_relative_js",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "classification": "canonical",
        "schema": {
            "version": 1,
            "surface": "pure_lego_entropy",
            "sections": ["positive", "negative", "boundary", "tool_manifest", "summary"],
            "non_metric_caveats": [
                "Relative entropy is asymmetric and can be infinite on support mismatch.",
                "Raw quantum Jensen-Shannon divergence is treated as a bounded divergence here; triangle inequality is not claimed.",
            ],
        },
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "total_tests": n_total,
            "passed": n_pass,
            "failed": n_total - n_pass,
            "all_pass": n_pass == n_total,
            "all_divergence_family_checks_pass": n_pass == n_total,
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_lego_entropy_relative_js_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"Results written to {out_path}")
    print(f"Tests: {n_pass}/{n_total} passed")
    print("ALL PASS" if n_pass == n_total else "FAILED")


if __name__ == "__main__":
    main()
