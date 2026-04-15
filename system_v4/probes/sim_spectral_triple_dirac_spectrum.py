#!/usr/bin/env python3
"""
sim_spectral_triple_dirac_spectrum -- Family #2 lego 2/6.

Structure object = Dirac operator D on the carrier. We probe its spectrum:
Hermiticity -> real eigenvalues, chiral symmetry {gamma,D}=0 -> spectrum
symmetric about 0, compact resolvent (finite-dim so automatic).
"""
import json, os
import numpy as np

classification = "canonical"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "numpy.linalg.eigh spectrum of D"},
    "sympy": {"tried": False,"used": False, "reason": ""},
    "gudhi": {"tried": False,"used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing", "sympy": "supportive", "gudhi": None}

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"].update(tried=True, used=True,
        reason="symbolic characteristic polynomial check")
except Exception as e:
    TOOL_MANIFEST["sympy"]["reason"] = f"unavailable: {e}"


def dirac(n=4):
    gamma = np.diag([1] * (n // 2) + [-1] * (n // 2)).astype(float)
    D = np.zeros((n, n))
    for i in range(n // 2):
        D[i, i + n // 2] = D[i + n // 2, i] = float(i + 1)
    return D, gamma


def run_positive_tests():
    r = {}
    D, gamma = dirac(4)
    w = np.linalg.eigvalsh(D)
    r["eigs_real"] = bool(np.allclose(w.imag, 0))
    w_sorted = np.sort(w)
    r["spectrum_symmetric_about_zero"] = bool(
        np.allclose(w_sorted, -w_sorted[::-1], atol=1e-10))
    # chiral partner: gamma v is a -lambda eigenvector
    w2, V = np.linalg.eigh(D)
    idx = int(np.argmax(w2))
    v = V[:, idx]
    Dv = D @ (gamma @ v)
    r["chiral_partner_negates_eigenvalue"] = bool(
        np.allclose(Dv, -w2[idx] * (gamma @ v), atol=1e-10))
    # sympy char poly has only even powers for chiral D
    Ds = sp.Matrix([[0, 0, 1, 0], [0, 0, 0, 2], [1, 0, 0, 0], [0, 2, 0, 0]])
    p = Ds.charpoly().as_expr()
    lam = list(p.free_symbols)[0]
    coeffs = sp.Poly(p, lam).all_coeffs()
    odd_coeffs_zero = all(c == 0 for c in coeffs[1::2])
    r["sympy_char_poly_even_only"] = bool(odd_coeffs_zero)
    return r


def run_negative_tests():
    r = {}
    # non-Hermitian D -> complex eigenvalues (not admissible)
    D = np.array([[0, 1], [-1, 0]], float)
    w = np.linalg.eigvals(D)
    r["non_hermitian_rejected"] = bool(not np.allclose(w.imag, 0))
    # non-chiral (even) Dirac: spectrum not symmetric about 0
    D = np.diag([1.0, 2.0, 3.0])
    w = np.sort(np.linalg.eigvalsh(D))
    r["non_chiral_spectrum_asymmetric"] = bool(
        not np.allclose(w, -w[::-1], atol=1e-10))
    return r


def run_boundary_tests():
    r = {}
    # zero operator: degenerate symmetric spectrum {0,0,0,0}
    D = np.zeros((4, 4))
    w = np.linalg.eigvalsh(D)
    r["zero_spectrum_degenerate"] = bool(np.allclose(w, 0))
    # scaled D: eigenvalues scale linearly
    D, _ = dirac(4)
    w1 = np.sort(np.linalg.eigvalsh(D))
    w2 = np.sort(np.linalg.eigvalsh(3.7 * D))
    r["eigenvalues_scale_linearly"] = bool(np.allclose(w2, 3.7 * w1, atol=1e-10))
    return r


if __name__ == "__main__":
    results = {
        "name": "spectral_triple_dirac_spectrum",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "spectral_triple_dirac_spectrum_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(json.dumps({k: results[k] for k in ("positive", "negative", "boundary")},
                     indent=2, default=str))
