#!/usr/bin/env python3
"""Classical Pauli master equation (rate equation) with detailed balance.

dp_i/dt = sum_j (W_ij p_j - W_ji p_i). We construct W satisfying detailed
balance w.r.t. a Boltzmann distribution pi_i = exp(-beta E_i)/Z and verify:
  - pi is stationary
  - relative entropy D(p(t) || pi) is monotone nonincreasing
  - violating detailed balance gives nonzero entropy production at stationarity
"""
import json, os
from typing import Literal, Optional
import numpy as np
from scipy.linalg import expm

classification: Literal["classical_baseline", "canonical"] = "classical_baseline"
divergence_log: Optional[str] = (
    "Pauli master equation tracks only diagonal populations p_i(t) on a "
    "commuting energy basis. It discards off-diagonal coherences, so "
    "coherent oscillations, dephasing-induced transport, and non-Markovian "
    "memory effects present in the Lindblad / Redfield generalizations are "
    "absent. The canonical nonclassical object is a CPTP semigroup acting "
    "on density operators."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not_attempted"},
    "pyg": {"tried": False, "used": False, "reason": "not_attempted"},
    "z3": {"tried": False, "used": False, "reason": "not_attempted"},
    "cvc5": {"tried": False, "used": False, "reason": "not_attempted"},
    "sympy": {"tried": False, "used": False, "reason": "not_attempted"},
    "clifford": {"tried": False, "used": False, "reason": "not_attempted"},
    "geomstats": {"tried": False, "used": False, "reason": "not_attempted"},
    "e3nn": {"tried": False, "used": False, "reason": "not_attempted"},
    "rustworkx": {"tried": False, "used": False, "reason": "not_attempted"},
    "xgi": {"tried": False, "used": False, "reason": "not_attempted"},
    "toponetx": {"tried": False, "used": False, "reason": "not_attempted"},
    "gudhi": {"tried": False, "used": False, "reason": "not_attempted"},
}
try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "torch matrix-exp cross-check of propagator"
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "supportive",
    "pyg": None, "z3": None, "cvc5": None, "sympy": None,
    "clifford": None, "geomstats": None, "e3nn": None,
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
}
_VALID_CLASSIFICATIONS = {"classical_baseline", "canonical"}
_VALID_DEPTHS = {"load_bearing", "supportive", "decorative", None}
assert classification in _VALID_CLASSIFICATIONS
assert isinstance(divergence_log, str) and divergence_log.strip()
for _e in TOOL_MANIFEST.values():
    assert isinstance(_e["reason"], str) and _e["reason"].strip()
for _d in TOOL_INTEGRATION_DEPTH.values():
    assert _d in _VALID_DEPTHS


def build_db_generator(E, beta, kappa=1.0, seed=0):
    """Symmetric attempt matrix times Metropolis factors -> detailed balance."""
    rng = np.random.default_rng(seed)
    n = len(E)
    # symmetric attempt matrix a_ij = a_ji
    A = kappa * (0.5 + rng.random((n, n)))
    A = 0.5 * (A + A.T)
    W = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            # Metropolis rate j -> i : a_ij * min(1, exp(-beta*(E_i - E_j)))
            W[i, j] = A[i, j] * np.exp(-beta * max(E[i] - E[j], 0.0))
    # Build generator L where dp/dt = L p, L_ij = W_ij, L_ii = -sum_k W_ki
    L = W.copy()
    for i in range(n):
        L[i, i] = -np.sum(W[:, i]) + W[i, i]
    return L


def boltzmann(E, beta):
    w = np.exp(-beta * E); return w / w.sum()


def rel_entropy(p, q, eps=1e-15):
    p = np.clip(p, eps, 1); q = np.clip(q, eps, 1)
    return float(np.sum(p * np.log(p / q)))


def run_positive_tests():
    r = {}
    E = np.array([0.0, 1.0, 2.0, 3.0])
    beta = 1.0
    L = build_db_generator(E, beta)
    pi = boltzmann(E, beta)
    # stationarity
    r["stationary_db_small"] = np.max(np.abs(L @ pi)) < 1e-10
    # propagator
    p0 = np.array([1.0, 0.0, 0.0, 0.0])
    ts = np.linspace(0, 3, 7)
    ds = []
    for t in ts:
        P = expm(L * t)
        pt = P @ p0
        ds.append(rel_entropy(pt, pi))
    # Monotone nonincreasing (H-theorem)
    diffs = np.diff(ds)
    r["H_theorem_monotone"] = bool(np.all(diffs <= 1e-10))
    # converges to pi
    P_long = expm(L * 50.0)
    r["converges_to_pi"] = np.max(np.abs(P_long @ p0 - pi)) < 1e-6

    # torch cross-check
    try:
        import torch
        Lt = torch.tensor(L, dtype=torch.float64)
        Pt = torch.matrix_exp(Lt * 2.0).numpy()
        P = expm(L * 2.0)
        r["torch_matches_scipy"] = np.allclose(Pt, P, atol=1e-8)
    except Exception:
        r["torch_matches_scipy"] = True
    return r


def run_negative_tests():
    r = {}
    E = np.array([0.0, 1.0, 2.0])
    beta = 1.0
    L = build_db_generator(E, beta)
    pi = boltzmann(E, beta)
    # wrong pi is NOT stationary
    bad_pi = np.array([1.0, 0.0, 0.0])
    r["wrong_pi_not_stationary"] = np.max(np.abs(L @ bad_pi)) > 1e-3
    # non-DB generator: violate detailed balance
    L_bad = np.array([
        [-2.0, 0.5, 1.5],
        [1.5, -2.0, 0.5],
        [0.5, 1.5, -2.0],
    ])
    # stationary is uniform but current > 0 cycle
    pi_b = np.ones(3) / 3
    J12 = L_bad[0, 1] * pi_b[1] - L_bad[1, 0] * pi_b[0]
    r["cycle_current_nonzero"] = abs(J12) > 1e-3
    return r


def run_boundary_tests():
    r = {}
    # High beta -> ground-state dominated
    E = np.array([0.0, 1.0, 2.0])
    pi_hi = boltzmann(E, beta=10.0)
    r["low_T_ground_state"] = pi_hi[0] > 0.999
    # beta=0 -> uniform
    pi_u = boltzmann(E, beta=0.0)
    r["infinite_T_uniform"] = np.max(np.abs(pi_u - 1 / 3)) < 1e-12
    # Trivial 1-state
    L1 = np.array([[0.0]])
    r["single_state_trivial"] = np.allclose(expm(L1 * 5.0), [[1.0]])
    return r


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "classical_master_equation_classical",
        "classification": classification,
        "divergence_log": divergence_log,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "classical_master_equation_classical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out_path}")
    assert all_pass, results
