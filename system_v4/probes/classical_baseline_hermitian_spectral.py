#!/usr/bin/env python3
"""classical baseline hermitian spectral

classical_baseline, numpy-only. Non-canon. Lane_B-eligible.
"""
import json, os
import numpy as np

TOOL_MANIFEST = {
    "numpy":    {"tried": True,  "used": True,  "reason": "load-bearing linear algebra / rng for classical baseline"},
    "pytorch":  {"tried": False, "used": False, "reason": "classical_baseline sim; torch not required"},
    "pyg":      {"tried": False, "used": False, "reason": "no graph-NN step in this baseline"},
    "z3":       {"tried": False, "used": False, "reason": "equality-based checks; no UNSAT proof in baseline"},
    "cvc5":     {"tried": False, "used": False, "reason": "equality-based checks; no UNSAT proof in baseline"},
    "sympy":    {"tried": False, "used": False, "reason": "numerical identity sufficient; symbolic not needed here"},
    "clifford": {"tried": False, "used": False, "reason": "matrix rep baseline; Cl(n) algebra deferred to canonical lane"},
    "geomstats":{"tried": False, "used": False, "reason": "flat/discrete baseline; manifold tooling out of scope"},
    "e3nn":     {"tried": False, "used": False, "reason": "no equivariant NN in baseline"},
    "rustworkx":{"tried": False, "used": False, "reason": "small adjacency handled by numpy"},
    "xgi":      {"tried": False, "used": False, "reason": "no hypergraph structure in this sim"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell complex in this sim"},
    "gudhi":    {"tried": False, "used": False, "reason": "no persistent homology in this sim"},
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "pytorch": None, "pyg": None, "z3": None, "cvc5": None, "sympy": None,
    "clifford": None, "geomstats": None, "e3nn": None, "rustworkx": None,
    "xgi": None, "toponetx": None, "gudhi": None,
}

NAME = "classical_baseline_hermitian_spectral"

def _rand_herm(n, rng):
    A = rng.standard_normal((n, n)) + 1j * rng.standard_normal((n, n))
    return (A + A.conj().T) / 2

def run_positive_tests():
    rng = np.random.default_rng(0)
    out = {}
    for k in range(5):
        H = _rand_herm(4, rng)
        w, V = np.linalg.eigh(H)
        recon = V @ np.diag(w) @ V.conj().T
        ok = np.allclose(recon, H, atol=1e-10) and np.allclose(V.conj().T @ V, np.eye(4), atol=1e-10)
        out[f"herm_{k}"] = {"pass": bool(ok), "max_err": float(np.max(np.abs(recon - H)))}
    return out

def run_negative_tests():
    # Non-Hermitian matrix should NOT satisfy eigh reconstruction as Hermitian
    rng = np.random.default_rng(1)
    A = rng.standard_normal((4,4)) + 1j*rng.standard_normal((4,4))  # not Hermitian
    is_herm = np.allclose(A, A.conj().T)
    return {"non_hermitian_detected": {"pass": (not is_herm)}}

def run_boundary_tests():
    # Degenerate: identity has all eigenvalues 1
    w, V = np.linalg.eigh(np.eye(5))
    ok = np.allclose(w, np.ones(5))
    # 1x1 trivial
    w2, _ = np.linalg.eigh(np.array([[3.0]]))
    return {"identity_spectrum": {"pass": bool(ok)}, "scalar": {"pass": bool(np.isclose(w2[0], 3.0))}}


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = (
        all(v.get("pass") for v in pos.values()) and
        all(v.get("pass") for v in neg.values()) and
        all(v.get("pass") for v in bnd.values())
    )
    results = {
        "name": NAME,
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, NAME + "_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{NAME}: all_pass={all_pass} -> {out_path}")
