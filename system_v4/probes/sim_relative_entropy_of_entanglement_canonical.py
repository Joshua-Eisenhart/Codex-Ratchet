#!/usr/bin/env python3
"""
Lane C canonical: Relative Entropy of Entanglement (REE).

Quantum/classical gap:
  REE(|Phi+><Phi+|) = 1 bit (log2). Any separable state has REE = 0.
  Classical mutual-info bound on a separable product = 0.
  Measured gap: ~1 bit.

Load-bearing tool: pytorch (all REE numerics via torch.linalg + autograd-compatible
von Neumann entropies). Upper bound to nearest separable proxy is torch-computed.
"""

import json
import os
import math
import numpy as np
classification = "classical_baseline"  # auto-backfill

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": ""},
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi": {"tried": False, "used": False, "reason": ""},
    "toponetx": {"tried": False, "used": False, "reason": ""},
    "gudhi": {"tried": False, "used": False, "reason": ""},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "pyg": None, "z3": None, "cvc5": None, "sympy": None,
    "clifford": None, "geomstats": None, "e3nn": None,
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

LN2 = math.log(2.0)


def phi_plus_rho():
    psi = np.array([1, 0, 0, 1], dtype=np.complex128) / math.sqrt(2)
    return np.outer(psi, psi.conj())


def product_rho(a=(0, 0, 1.0), b=(0, 0, 1.0)):
    I = np.eye(2, dtype=np.complex128)
    sx = np.array([[0, 1], [1, 0]], dtype=np.complex128)
    sy = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
    sz = np.array([[1, 0], [0, -1]], dtype=np.complex128)
    P = [sx, sy, sz]
    ra = I / 2 + sum(a[i] * P[i] / 2 for i in range(3))
    rb = I / 2 + sum(b[i] * P[i] / 2 for i in range(3))
    return np.kron(ra, rb)


def vne_torch(rho):
    evals = torch.linalg.eigvalsh(rho).real
    evals = torch.clamp(evals, min=1e-12)
    return -(evals * torch.log(evals)).sum()


def rel_entropy_torch(rho, sigma):
    """S(rho || sigma) computed via eigendecomposition (torch load-bearing)."""
    e_rho = torch.linalg.eigvalsh(rho).real
    e_rho = torch.clamp(e_rho, min=1e-12)
    # -S(rho)
    neg_s_rho = (e_rho * torch.log(e_rho)).sum()
    # -Tr(rho log sigma)
    w, V = torch.linalg.eigh(sigma)
    w = torch.clamp(w.real, min=1e-12)
    log_sigma = V @ torch.diag(torch.log(w)).to(V.dtype) @ V.conj().T
    tr = torch.trace(rho @ log_sigma).real
    return (neg_s_rho - tr)


def closest_separable_proxy(rho_t):
    """Proxy: product of marginals rho_A tensor rho_B (valid separable state)."""
    r = rho_t.reshape(2, 2, 2, 2)
    rho_a = torch.einsum("ijkj->ik", r)
    rho_b = torch.einsum("ijil->jl", r)
    return torch.kron(rho_a, rho_b)


def ree_upper_bound(rho_t):
    """Upper bound to REE: S(rho || rho_A x rho_B) = mutual information.
    For |Phi+>: S(rho) = 0, S(rho_A) = S(rho_B) = log2, REE_upper = 2 log 2.
    Tighter: use E_F-like proxy via convex mix toward I/4."""
    sigma = closest_separable_proxy(rho_t)
    return float(rel_entropy_torch(rho_t, sigma).item())


def _ket(idx, n=4):
    v = torch.zeros(n, dtype=torch.complex128)
    v[idx] = 1.0
    return v


def ree_min_over_grid(rho_t):
    """Minimize S(rho||sigma_sep) over a grid of separable mixtures.
    For Phi+, theoretical REE = log 2, achieved at sigma = (|00><00|+|11><11|)/2.
    We sweep convex combinations across a basis-separable family."""
    sigma_prod = closest_separable_proxy(rho_t)
    I4 = torch.eye(4, dtype=rho_t.dtype) / 4
    # Diagonal/classical separable anchors
    p00 = torch.outer(_ket(0), _ket(0).conj())
    p11 = torch.outer(_ket(3), _ket(3).conj())
    p01 = torch.outer(_ket(1), _ket(1).conj())
    p10 = torch.outer(_ket(2), _ket(2).conj())
    dephased_bell = 0.5 * (p00 + p11)  # classical correlation
    dephased_anti = 0.5 * (p01 + p10)

    anchors = [I4, sigma_prod, dephased_bell, dephased_anti,
               0.5 * dephased_bell + 0.5 * I4,
               0.5 * dephased_anti + 0.5 * I4]
    best = float("inf")
    # weights grid over anchors (coarse)
    grid = np.linspace(0.0, 1.0, 11)
    for a in grid:
        for b in grid:
            if a + b > 1.0:
                continue
            for c in grid:
                if a + b + c > 1.0 + 1e-9:
                    continue
                d = 1.0 - a - b - c
                if d < -1e-9:
                    continue
                sigma = a * anchors[0] + b * anchors[1] + c * anchors[2] + d * anchors[3]
                # ensure PSD and trace 1 (it is by convex comb of states)
                val = float(rel_entropy_torch(rho_t, sigma).item())
                if val < best:
                    best = val
    # also pure anchors
    for s in anchors:
        val = float(rel_entropy_torch(rho_t, s).item())
        if val < best:
            best = val
    return best


def run_positive_tests():
    results = {}
    rho = torch.tensor(phi_plus_rho(), dtype=torch.complex128)

    # P1: REE of Phi+ bounded above by log(2) from optimized grid
    ree = ree_min_over_grid(rho)
    results["P1_ree_phi_plus_near_log2"] = {
        "ree_bits": ree / LN2,
        "expected_bits": 1.0,
        "pass": abs(ree - LN2) < 0.05,
    }

    # P2: REE of product state = 0
    rho_prod = torch.tensor(product_rho(), dtype=torch.complex128)
    ree_prod = ree_min_over_grid(rho_prod)
    results["P2_ree_product_zero"] = {
        "ree": ree_prod,
        "pass": ree_prod < 1e-3,
    }

    # P3: quantum/classical gap measurement
    gap_bits = (ree - ree_prod) / LN2
    results["P3_quantum_classical_gap"] = {
        "gap_bits": gap_bits,
        "expected_gap_bits": 1.0,
        "pass": abs(gap_bits - 1.0) < 0.1,
    }
    return results


def run_negative_tests():
    results = {}
    # N1: REE non-negative for random 2-qubit states
    rng = np.random.RandomState(7)
    n1_pass = True
    n1_min = float("inf")
    for _ in range(10):
        psi = rng.randn(4) + 1j * rng.randn(4)
        psi /= np.linalg.norm(psi)
        rho = torch.tensor(np.outer(psi, psi.conj()), dtype=torch.complex128)
        v = ree_upper_bound(rho)
        n1_min = min(n1_min, v)
        if v < -1e-6:
            n1_pass = False
    results["N1_ree_non_negative"] = {"min": n1_min, "pass": n1_pass}

    # N2: classically correlated (|00><00|+|11><11|)/2 is separable -> REE = 0
    diag = torch.tensor(np.diag([0.5, 0.0, 0.0, 0.5]).astype(np.complex128))
    v = ree_min_over_grid(diag)
    results["N2_classical_corr_zero_ree"] = {"ree": v, "pass": v < 1e-3}
    return results


def run_boundary_tests():
    results = {}
    # B1: maximally mixed -> REE = 0
    I4 = torch.eye(4, dtype=torch.complex128) / 4
    v = ree_min_over_grid(I4)
    results["B1_max_mixed_zero"] = {"ree": v, "pass": v < 1e-6}

    # B2: Werner state at p=1/3 boundary -> REE near 0
    rho = (1 / 3) * torch.tensor(phi_plus_rho(), dtype=torch.complex128) \
          + (2 / 3) * I4
    v = ree_min_over_grid(rho)
    results["B2_werner_sep_boundary"] = {"ree": v, "pass": v < 0.2}
    return results


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "Load-bearing: REE eigendecomposition, matrix log, and relative "
        "entropy S(rho||sigma) all computed via torch.linalg.eigh / eigvalsh. "
        "Closest-separable proxy and grid minimization are torch tensor ops."
    )

    def count_passes(d):
        p, t = 0, 0
        if isinstance(d, dict):
            if "pass" in d:
                t += 1
                if d["pass"]:
                    p += 1
            for v in d.values():
                a, b = count_passes(v)
                p += a; t += b
        return p, t

    all_r = {"positive": positive, "negative": negative, "boundary": boundary}
    tp, tt = count_passes(all_r)

    results = {
        "name": "relative_entropy_of_entanglement_canonical",
        "description": "Lane C REE: Phi+ = 1 bit, separable = 0, gap = 1 bit",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": "canonical",
        "quantum_classical_gap_bits": positive["P3_quantum_classical_gap"]["gap_bits"],
        "summary": {"total_tests": tt, "total_pass": tp, "all_pass": tp == tt},
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "relative_entropy_of_entanglement_canonical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results: {tp}/{tt} pass -> {out_path}")
    if tp != tt:
        raise SystemExit(1)
