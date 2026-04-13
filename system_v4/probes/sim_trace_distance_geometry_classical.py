#!/usr/bin/env python3
"""Classical baseline: trace_distance_geometry.
Trace distance T(rho,sigma)=0.5*||rho-sigma||_1 on Hermitian matrices.
Tests: triangle inequality, unitary invariance, non-negativity, identity of indiscernibles."""
import json, os, numpy as np
from _classical_baseline_common import TOOL_MANIFEST, TOOL_INTEGRATION_DEPTH
classification = "classical_baseline"
NAME = "trace_distance_geometry"

def rand_density(n, rng):
    A = rng.standard_normal((n, n)) + 1j * rng.standard_normal((n, n))
    rho = A @ A.conj().T
    return rho / np.trace(rho).real

def rand_unitary(n, rng):
    A = rng.standard_normal((n, n)) + 1j * rng.standard_normal((n, n))
    Q, R = np.linalg.qr(A); d = np.diagonal(R); return Q * (d / np.abs(d))

def trace_distance(a, b):
    w = np.linalg.eigvalsh(a - b)
    return 0.5 * np.sum(np.abs(w))

def run_positive_tests():
    r = {}; rng = np.random.default_rng(0)
    for n in (2, 3, 4):
        trials = 20
        tri = True; uinv = True; nn = True; ident = True
        for _ in range(trials):
            a, b, c = (rand_density(n, rng) for _ in range(3))
            d_ab = trace_distance(a, b); d_bc = trace_distance(b, c); d_ac = trace_distance(a, c)
            if d_ac > d_ab + d_bc + 1e-8: tri = False
            if d_ab < -1e-12: nn = False
            if trace_distance(a, a) > 1e-10: ident = False
            U = rand_unitary(n, rng)
            d1 = trace_distance(U @ a @ U.conj().T, U @ b @ U.conj().T)
            if abs(d1 - d_ab) > 1e-8: uinv = False
        r[f"triangle_n{n}"] = tri
        r[f"unitary_invariance_n{n}"] = uinv
        r[f"nonneg_n{n}"] = nn
        r[f"identity_n{n}"] = ident
    return r

def run_negative_tests():
    r = {}; rng = np.random.default_rng(1)
    a = rand_density(3, rng); b = rand_density(3, rng)
    # non-unitary conjugation generically changes distance
    M = rng.standard_normal((3, 3)) + 1j * rng.standard_normal((3, 3))
    d0 = trace_distance(a, b)
    d1 = trace_distance(M @ a @ M.conj().T, M @ b @ M.conj().T)
    r["nonunitary_changes_distance"] = bool(abs(d0 - d1) > 1e-6)
    # distance between distinct states strictly positive
    r["distinct_positive"] = bool(d0 > 1e-8)
    return r

def run_boundary_tests():
    r = {}; rng = np.random.default_rng(2)
    a = rand_density(2, rng)
    r["zero_self_distance"] = bool(trace_distance(a, a) < 1e-12)
    # orthogonal pure states -> distance 1
    e0 = np.array([[1, 0], [0, 0]], dtype=complex); e1 = np.array([[0, 0], [0, 1]], dtype=complex)
    r["orthogonal_dist_one"] = bool(abs(trace_distance(e0, e1) - 1.0) < 1e-10)
    return r

if __name__ == "__main__":
    results = {"name": NAME, "classification": "classical_baseline",
               "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
               "positive": run_positive_tests(), "negative": run_negative_tests(),
               "boundary": run_boundary_tests(),
               "classical_captured": "triangle inequality, unitary invariance, non-negativity, 0/1 extremes",
               "innately_missing": "trace distance under nonclassical coupling / probe contextuality"}
    results["all_pass"] = all(v for s in ("positive","negative","boundary") for v in results[s].values())
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results", f"{NAME}_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out,"w") as f: json.dump(results,f,indent=2,default=str)
    print(f"all_pass={results['all_pass']} -> {out}")
