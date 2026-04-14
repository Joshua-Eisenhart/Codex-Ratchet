#!/usr/bin/env python3
"""sim_gtower_deep_sp_symplectic_form_preservation -- Deep G-tower lego.

Claim (admissibility):
  Sp(2n,R) candidates satisfy M^T J M = J for the standard symplectic J.
  Non-preserving candidates are EXCLUDED. Diagonal scalings (non-symplectic)
  and non-even dimensions are outside Sp.

scope_note: LADDERS_FENCES_ADMISSION_REFERENCE.md -- Sp symplectic fence.
"""
import json, os

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": ""} for k in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"


def J(n):
    I = sp.eye(n); Z = sp.zeros(n,n)
    return sp.Matrix.vstack(sp.Matrix.hstack(Z, I), sp.Matrix.hstack(-I, Z))


def is_symplectic(M, n):
    Jm = J(n)
    return sp.simplify(M.T * Jm * M - Jm) == sp.zeros(2*n, 2*n)


def run_positive_tests():
    r = {}
    # Identity is symplectic
    r["id_symplectic"] = {"pass": is_symplectic(sp.eye(2), 1)}
    # Sp(2): [[a,b],[c,d]] with ad-bc=1 == SL(2) == Sp(2)
    a,b,c,d = sp.symbols('a b c d')
    M = sp.Matrix([[a,b],[c,d]])
    cond = sp.simplify(M.T*J(1)*M - J(1))
    # the only nontrivial entry is (a*d - b*c) * J
    r["Sp2_eq_SL2"] = {"val": str(cond), "pass": sp.simplify(cond[0,1] - (a*d - b*c - 1)) == 0}
    # Explicit SL(2) element
    M2 = sp.Matrix([[2,1],[1,1]])
    r["sl2_is_sp2"] = {"pass": is_symplectic(M2, 1)}
    # Sp(4): block-diag of two Sp(2) is Sp(4)? Not generally -- but identity in Sp(4)
    r["id4_symplectic"] = {"pass": is_symplectic(sp.eye(4), 2)}
    return r


def run_negative_tests():
    r = {}
    # det != 1: [[2,0],[0,1]] -- not symplectic in Sp(2)
    M = sp.Matrix([[2,0],[0,1]])
    r["det2_excluded"] = {"pass": not is_symplectic(M, 1)}
    # Symmetric matrix in 2D -- excluded
    S = sp.Matrix([[1,2],[2,3]])
    r["symmetric_excluded"] = {"pass": not is_symplectic(S, 1)}
    return r


def run_boundary_tests():
    r = {}
    # -I is symplectic (det = +1 when n=1)
    r["minus_id_symplectic"] = {"pass": is_symplectic(-sp.eye(2), 1)}
    # Shear [[1,t],[0,1]] is symplectic for any t
    t = sp.symbols('t')
    Sh = sp.Matrix([[1,t],[0,1]])
    cond = sp.simplify(Sh.T*J(1)*Sh - J(1))
    r["shear_symplectic"] = {"pass": cond == sp.zeros(2,2)}
    return r


if __name__ == "__main__":
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "symbolic M^T J M = J decides Sp admissibility"
    TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"
    results = {
        "name": "sim_gtower_deep_sp_symplectic_form_preservation",
        "scope_note": "LADDERS_FENCES_ADMISSION_REFERENCE.md: Sp symplectic fence",
        "language": "M^T J M = J -> admissible; else excluded from Sp",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "sim_gtower_deep_sp_symplectic_form_preservation_results.json")
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out}")
