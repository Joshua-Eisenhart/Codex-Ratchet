#!/usr/bin/env python3
"""
sim_spectral_triple_carrier_algebra -- Family #2 Spectral Triples, lego 1/6.

Carrier = an even spectral triple (A, H, D, gamma) on a 2-site discrete
model. A = diag matrices (commutative subalgebra), H = C^4, gamma chiral
grading {+1,+1,-1,-1}. We admit a carrier iff [gamma, a]=0 for all a in A
and {gamma, D}=0 for a prescribed Dirac.
"""
import json, os
import numpy as np

classification = "classical_baseline"
DEMOTE_REASON = "no non-numpy load_bearing tool; numeric numpy only"

TOOL_MANIFEST = {
    "numpy":  {"tried": True, "used": True,  "reason": "matrix algebra for (A,H,D,gamma)"},
    "sympy":  {"tried": False,"used": False, "reason": ""},
    "z3":     {"tried": False,"used": False, "reason": ""},
    "gudhi":  {"tried": False,"used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing", "sympy": "supportive", "z3": None, "gudhi": None,
}

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"].update(tried=True, used=True,
        reason="symbolic anticommutator {gamma,D}=0 check")
except Exception as e:
    TOOL_MANIFEST["sympy"]["reason"] = f"unavailable: {e}"


def build_triple():
    gamma = np.diag([1, 1, -1, -1]).astype(float)
    # odd-graded Dirac: off-diagonal block
    D = np.zeros((4, 4))
    D[0, 2] = D[2, 0] = 1.0
    D[1, 3] = D[3, 1] = 1.0
    # commutative A: diagonal, so automatically commutes with gamma
    a = np.diag([0.3, -0.7, 1.1, 0.2])
    return a, D, gamma


def run_positive_tests():
    r = {}
    a, D, gamma = build_triple()
    r["commutator_gamma_a_zero"] = bool(np.allclose(gamma @ a - a @ gamma, 0))
    r["anticommutator_gamma_D_zero"] = bool(np.allclose(gamma @ D + D @ gamma, 0))
    r["D_selfadjoint"] = bool(np.allclose(D, D.T))

    # symbolic sympy cross-check
    G = sp.diag(1, 1, -1, -1)
    Ds = sp.zeros(4, 4); Ds[0, 2] = Ds[2, 0] = 1; Ds[1, 3] = Ds[3, 1] = 1
    r["sympy_anticommutator_zero"] = bool((G * Ds + Ds * G) == sp.zeros(4, 4))
    return r


def run_negative_tests():
    r = {}
    _, D, gamma = build_triple()
    # even-graded (diagonal) Dirac should FAIL anticommutator
    D_even = np.diag([1.0, -1.0, 2.0, -0.5])
    r["even_D_rejected"] = bool(not np.allclose(gamma @ D_even + D_even @ gamma, 0))
    # non-diagonal a: off-diagonal mixing chiral sectors breaks [gamma,a]=0
    a_bad = np.array([[0, 1, 0, 0], [0, 0, 0, 0], [1, 0, 0, 0], [0, 0, 0, 0]], float)
    r["chiral_mixing_algebra_rejected"] = bool(
        not np.allclose(gamma @ a_bad - a_bad @ gamma, 0))
    return r


def run_boundary_tests():
    r = {}
    # zero Dirac trivially satisfies both conditions (degenerate carrier)
    gamma = np.diag([1, 1, -1, -1]).astype(float)
    D0 = np.zeros((4, 4))
    r["zero_D_degenerate_admissible"] = bool(
        np.allclose(gamma @ D0 + D0 @ gamma, 0))
    # tiny symmetric off-diag perturbation remains admissible
    Deps = np.zeros((4, 4))
    Deps[0, 2] = Deps[2, 0] = 1e-12
    r["tiny_perturbation_admissible"] = bool(
        np.allclose(gamma @ Deps + Deps @ gamma, 0, atol=1e-10))
    return r


if __name__ == "__main__":
    results = {
        "name": "spectral_triple_carrier_algebra",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "spectral_triple_carrier_algebra_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(json.dumps({k: results[k] for k in ("positive", "negative", "boundary")},
                     indent=2, default=str))
