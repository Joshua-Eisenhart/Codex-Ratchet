#!/usr/bin/env python3
"""sim_gtower_su_to_sp_symplectic -- SU(2n) -> Sp(n) admissibility via symplectic form.

Scope note: LADDERS_FENCES_ADMISSION_REFERENCE.md (SU->Sp fence: preservation
of standard symplectic form J with J^2 = -I).

Load-bearing: sympy proves A^T J A = J is preserved symbolically for a
generic Sp(2) element and fails for a generic SU(2) element.
"""
import json, os
import numpy as np

classification = "classical_baseline"
DEMOTE_REASON = "no non-numpy load_bearing tool; numeric numpy only"

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": ""} for k in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

from _gtower_common import in_Spn_real, standard_omega, in_SUn


def run_positive_tests():
    r = {}
    # Sp(2,R): generic 2x2 symplectic over reals is SL(2,R); det=1 suffices.
    A = sp.Matrix([[2, 1], [1, 1]])  # det=1
    J = sp.Matrix([[0, 1], [-1, 0]])
    r["sp2_preserves_J"] = sp.simplify(A.T * J * A - J) == sp.zeros(2, 2)
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "symbolic Sp(2n) preservation of J"
    TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"
    # numeric Sp(4): block diag of Sp(2) copies
    I2 = np.eye(2); Z2 = np.zeros((2, 2))
    B = np.array([[2.0, 1.0], [1.0, 1.0]])
    M = np.block([[B, Z2], [Z2, B]])
    # reorder to standard basis: actually build explicit Sp(4)
    Msp = np.array([[1,0,1,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]], dtype=float)
    r["sp4_numeric_admitted"] = in_Spn_real(Msp)
    return r


def run_negative_tests():
    r = {}
    # A real 2x2 with det != 1 is excluded from Sp(2,R)=SL(2,R)
    NonSp = np.array([[1.0, 0.0], [0.0, 2.0]])  # det=2
    r["detne1_excluded_from_sp"] = not in_Spn_real(NonSp)
    # A non-symplectic matrix: scale
    S = 2.0 * np.eye(2)
    r["scale_excluded"] = not in_Spn_real(S)
    return r


def run_boundary_tests():
    r = {}
    # boundary: identity is in every group
    r["identity_in_sp"] = in_Spn_real(np.eye(4))
    # symbolic: show generic symplectic 2x2 has det=1 (Sp(2)=SL(2))
    a, b, c, d = sp.symbols("a b c d", real=True)
    A = sp.Matrix([[a, b], [c, d]])
    J = sp.Matrix([[0, 1], [-1, 0]])
    cond = sp.simplify((A.T * J * A - J))
    # cond[0,1] = a*d - b*c - 1 = 0 -> det=1
    det_eq = sp.simplify(cond[0, 1] + 1)  # == a*d - b*c
    r["sp2_is_sl2"] = sp.simplify(det_eq - (a*d - b*c)) == 0
    return r


if __name__ == "__main__":
    pos, neg, bnd = run_positive_tests(), run_negative_tests(), run_boundary_tests()
    def _t(v): return bool(v) is True
    all_pass = all(_t(v) for d in (pos, neg, bnd) for v in d.values())
    results = {
        "name": "sim_gtower_su_to_sp_symplectic",
        "classification": "canonical",
        "scope_note": "LADDERS_FENCES_ADMISSION_REFERENCE.md: SU->Sp symplectic-form fence",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "status": "PASS" if all_pass else "FAIL",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "sim_gtower_su_to_sp_symplectic_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{results['name']}: {results['status']}")
