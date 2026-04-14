#!/usr/bin/env python3
"""sim_gtower_deep_gl_invariant_volume_form -- Deep G-tower lego.

Claim (admissibility, not construction):
  Under GL(n,R), the standard volume form omega = dx1 ^ ... ^ dxn
  transforms by det(A). Candidates with det=0 are EXCLUDED from GL.
  SL(n) candidates (det=+-1) survive as volume-preserving.

scope_note: See system_v5/new docs/LADDERS_FENCES_ADMISSION_REFERENCE.md
  for the GL -> SL reduction fence (volume-preservation admissibility).
"""
import json, os
import numpy as np

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": ""} for k in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"


def run_positive_tests():
    r = {}
    # 2x2 and 3x3 symbolic determinants as volume-form coefficients
    a,b,c,d = sp.symbols('a b c d')
    M2 = sp.Matrix([[a,b],[c,d]])
    det2 = M2.det()
    # positive: det of identity is 1 (volume preserved)
    r["id2_det"] = {"val": int(sp.eye(2).det()), "expected": 1,
                    "pass": int(sp.eye(2).det()) == 1}
    # 3x3 rotation-like (orthogonal -> det +-1 -> survives SL-admissibility up to sign)
    R = sp.Matrix([[0,-1,0],[1,0,0],[0,0,1]])
    r["rot3_det"] = {"val": int(R.det()), "expected": 1, "pass": int(R.det()) == 1}
    # symbolic volume scaling: scaling matrix diag(k,k,k) -> k^3
    k = sp.symbols('k')
    S = sp.diag(k,k,k)
    r["scale3_det"] = {"val": str(sp.simplify(S.det())), "expected": "k**3",
                       "pass": sp.simplify(S.det() - k**3) == 0}
    return r


def run_negative_tests():
    r = {}
    # Singular matrix: excluded from GL (det=0)
    Z = sp.Matrix([[1,2],[2,4]])
    r["singular_excluded"] = {"val": int(Z.det()), "expected": 0,
                              "pass": int(Z.det()) == 0}
    # Non-volume-preserving: diag(2,1) has det 2 -> excluded from SL
    D = sp.Matrix([[2,0],[0,1]])
    r["not_sl_excluded"] = {"val": int(D.det()), "pass": int(D.det()) != 1 and int(D.det()) != -1}
    return r


def run_boundary_tests():
    r = {}
    # det = -1 (orientation-reversing) still GL-admissible
    F = sp.Matrix([[-1,0],[0,1]])
    r["orient_reverse_admissible"] = {"val": int(F.det()), "pass": int(F.det()) == -1}
    # infinitesimal: det(I + eps*A) = 1 + eps*tr(A) + O(eps^2)
    eps = sp.symbols('eps')
    A = sp.Matrix([[1,2],[3,4]])
    detI = sp.series((sp.eye(2)+eps*A).det(), eps, 0, 2).removeO()
    r["infinitesimal_trace"] = {"val": str(detI), "pass": sp.simplify(detI - (1 + eps*A.trace())) == 0}
    return r


if __name__ == "__main__":
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "symbolic determinants decide GL/SL admissibility"
    TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"
    results = {
        "name": "sim_gtower_deep_gl_invariant_volume_form",
        "scope_note": "LADDERS_FENCES_ADMISSION_REFERENCE.md: GL->SL volume-form fence",
        "language": "excluded/admissible (not constructed)",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "sim_gtower_deep_gl_invariant_volume_form_results.json")
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out}")
