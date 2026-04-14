#!/usr/bin/env python3
"""sim_sympy_charpoly_eigvals -- Characteristic polynomial roots exactly equal
eigenvalues for a rational 3x3 matrix. Certified via radical/RootOf equality.
"""
import json, os
import numpy as np
import sympy as sp

TOOL_MANIFEST = {
    "pytorch":{"tried":False,"used":False,"reason":"numeric eigvals float only; cannot equate to exact radicals"},
    "pyg":{"tried":False,"used":False,"reason":"n/a"},
    "z3":{"tried":False,"used":False,"reason":"algebraic-number equality native to sympy"},
    "cvc5":{"tried":False,"used":False,"reason":"same"},
    "sympy":{"tried":True,"used":True,"reason":"charpoly.roots and Matrix.eigenvals produce identical exact algebraic multisets"},
    "clifford":{"tried":False,"used":False,"reason":"n/a"},
    "geomstats":{"tried":False,"used":False,"reason":"n/a"},
    "e3nn":{"tried":False,"used":False,"reason":"n/a"},
    "rustworkx":{"tried":False,"used":False,"reason":"n/a"},
    "xgi":{"tried":False,"used":False,"reason":"n/a"},
    "toponetx":{"tried":False,"used":False,"reason":"n/a"},
    "gudhi":{"tried":False,"used":False,"reason":"n/a"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"


def fixed_matrix():
    return sp.Matrix([
        [sp.Rational(2,1), sp.Rational(-1,3), sp.Rational(1,2)],
        [sp.Rational(0,1), sp.Rational(3,1), sp.Rational(-1,4)],
        [sp.Rational(1,5), sp.Rational(1,1), sp.Rational(-2,1)],
    ])


def run_positive_tests():
    A = fixed_matrix()
    x = sp.symbols('x')
    p = A.charpoly(x).as_expr()
    roots_poly = sp.roots(p, x, multiple=True)  # with multiplicities
    eig = A.eigenvals()  # dict eigenvalue -> multiplicity
    eig_multiset = []
    for k, m in eig.items():
        eig_multiset.extend([sp.simplify(k)]*int(m))
    # Multiset comparison: every root matches some eigenvalue via sp.simplify==0, and counts equal
    remaining = list(eig_multiset)
    matched = True
    for r in roots_poly:
        found = None
        for i, e in enumerate(remaining):
            if sp.simplify(r - e) == 0:
                found = i; break
        if found is None:
            matched = False; break
        remaining.pop(found)
    equal = matched and len(remaining) == 0 and len(roots_poly) == len(eig_multiset)
    # Also check each eigenvalue satisfies charpoly exactly
    vanish = all(sp.simplify(p.subs(x, e)) == 0 for e in eig_multiset)
    return {"charpoly_roots_equal_eigenvalues": bool(equal),
            "eigenvalues_satisfy_charpoly": bool(vanish),
            "n_roots": len(roots_poly)}


def run_negative_tests():
    A = fixed_matrix()
    x = sp.symbols('x')
    p = A.charpoly(x).as_expr()
    # Perturb matrix; its charpoly should no longer vanish on original eigenvalues generically
    B = A + sp.Rational(1,7)*sp.eye(3)
    pB = B.charpoly(x).as_expr()
    eigA = list(A.eigenvals().keys())
    detected = any(sp.simplify(pB.subs(x, e)) != 0 for e in eigA)
    return {"perturbed_charpoly_not_vanishing_on_original_eigs": bool(detected)}


def run_boundary_tests():
    # Diagonal matrix: eigenvalues = diagonal entries exactly
    D = sp.diag(sp.Rational(1,2), sp.Rational(-3,5), sp.Rational(7,1))
    eig = D.eigenvals()
    exp = {sp.Rational(1,2):1, sp.Rational(-3,5):1, sp.Rational(7,1):1}
    return {"diagonal_eigs_equal_diag": eig == exp}


def run_ablation():
    A = np.array([[2.0, -1/3, 0.5],[0.0, 3.0, -0.25],[0.2, 1.0, -2.0]])
    eig_n = np.linalg.eigvals(A)
    coeffs = np.poly(A)  # char poly coeffs (numeric)
    residuals = [abs(np.polyval(coeffs, e)) for e in eig_n]
    return {"numpy_charpoly_vs_eig_numeric_only": True,
            "max_residual": float(max(residuals)),
            "note": "numeric residuals nonzero at ~1e-13; only sympy proves exact equality"}


if __name__ == "__main__":
    results = {
        "name": "sympy_charpoly_eigvals",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "ablation": run_ablation(),
        "classification": "canonical",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sympy_charpoly_eigvals_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
