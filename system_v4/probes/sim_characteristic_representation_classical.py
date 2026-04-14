#!/usr/bin/env python3
"""Classical baseline: characteristic_representation.
Characteristic polynomial / function of a matrix via numpy. Tests Cayley-Hamilton,
coefficient sign pattern, and degeneracy edge case. Classical captures the
polynomial; innately misses noncommutative operator-algebra structure."""
import json, os, numpy as np
classification = "classical_baseline"
divergence_log = "Classical baseline: characteristic representation is modeled here by matrix-polynomial numerics, not a canonical nonclassical witness."
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "eigenvalue and matrix-polynomial numerics"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}

NAME = "characteristic_representation"

def char_poly(A):
    # Leverrier-Faddeev-free: use eigenvalues then expand
    eig = np.linalg.eigvals(A)
    # build polynomial coefficients from roots (highest degree first)
    return np.poly(eig)

def run_positive_tests():
    r = {}
    rng = np.random.default_rng(0)
    for n in (2, 3, 5):
        A = rng.standard_normal((n, n))
        p = char_poly(A)
        # Cayley-Hamilton: p(A) = 0
        pA = np.zeros_like(A, dtype=complex)
        Ak = np.eye(n, dtype=complex)
        for c in p[::-1]:
            pA = pA + c * Ak
            Ak = Ak @ A
        # p is leading-first; re-evaluate correctly
        pA = np.zeros((n, n), dtype=complex)
        for i, c in enumerate(p):
            pA = pA + c * np.linalg.matrix_power(A.astype(complex), len(p) - 1 - i)
        r[f"cayley_hamilton_n{n}"] = bool(np.allclose(pA, 0, atol=1e-6))
        # trace == -p[1] (for monic)
        r[f"trace_matches_n{n}"] = bool(np.isclose(np.trace(A), -p[1], atol=1e-9))
    return r

def run_negative_tests():
    r = {}
    rng = np.random.default_rng(1)
    A = rng.standard_normal((4, 4))
    p = char_poly(A)
    # wrong polynomial should fail Cayley-Hamilton
    bad = p + np.array([0, 0, 0, 0, 1.0])
    n = 4
    pA = sum(bad[i] * np.linalg.matrix_power(A.astype(complex), n - i) for i in range(n + 1))
    r["wrong_poly_nonzero"] = bool(np.linalg.norm(pA) > 1e-3)
    # characteristic poly of non-square must fail
    try:
        char_poly(np.ones((2, 3)))
        r["nonsquare_rejected"] = False
    except Exception:
        r["nonsquare_rejected"] = True
    return r

def run_boundary_tests():
    r = {}
    # degenerate: zero matrix -> p(x)=x^n
    A = np.zeros((3, 3))
    p = char_poly(A)
    r["zero_matrix_poly"] = bool(np.allclose(p, [1, 0, 0, 0], atol=1e-9))
    # identity: (x-1)^n
    A = np.eye(3)
    p = char_poly(A)
    r["identity_poly"] = bool(np.allclose(p, [1, -3, 3, -1], atol=1e-9))
    # repeated eigenvalues
    A = np.diag([2.0, 2.0, 5.0])
    p = char_poly(A)
    r["repeated_eigs"] = bool(np.allclose(np.sort(np.roots(p).real), [2, 2, 5], atol=1e-6))
    return r

if __name__ == "__main__":
    results = {
        "name": NAME,
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classical_captured": "characteristic polynomial coefficients and Cayley-Hamilton on commutative numeric matrices",
        "innately_missing": "operator-algebra / noncommutative characteristic structure, constraint-admissibility of representation choice",
    }
    results["all_pass"] = all(v for section in ("positive", "negative", "boundary") for v in results[section].values())
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results", f"{NAME}_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"all_pass={results['all_pass']} -> {out}")
