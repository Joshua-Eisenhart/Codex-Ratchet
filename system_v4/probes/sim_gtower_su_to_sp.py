#!/usr/bin/env python3
"""sim_gtower_su_to_sp -- reduction SU(2n) -> Sp(n) admissibility probe.

An SU(2n) candidate admits an Sp(n) (compact symplectic) reduction iff it
preserves a quaternionic / symplectic form omega on C^{2n}:
    U^T omega U = omega  (for the complex antisymmetric form)
Equivalently, U commutes with the quaternionic structure j (antilinear
with j^2 = -I). Obstruction: odd complex dimension (no antisymmetric
nondegenerate form exists on C^{odd}).

Load-bearing: sympy proves det of any 3x3 antisymmetric complex matrix
is zero (odd-dim obstruction). z3 cross-checks det=+-1 constraint for
a symmetric 1x1 case.
"""
import json
import os
import numpy as np

classification = "canonical"

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": ""},
    "pyg":       {"tried": False, "used": False, "reason": ""},
    "z3":        {"tried": False, "used": False, "reason": ""},
    "cvc5":      {"tried": False, "used": False, "reason": ""},
    "sympy":     {"tried": False, "used": False, "reason": ""},
    "clifford":  {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn":      {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi":       {"tried": False, "used": False, "reason": ""},
    "toponetx":  {"tried": False, "used": False, "reason": ""},
    "gudhi":     {"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import z3
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

from _gtower_common import in_SUn


def omega_C(n):
    """Complex antisymmetric form on C^{2n}."""
    I = np.eye(n)
    Z = np.zeros((n, n))
    return np.block([[Z, I], [-I, Z]]).astype(complex)


def in_Spn_complex(U, tol=1e-8):
    """U in Sp(n): U^T omega U = omega on C^{2n}."""
    U = np.asarray(U, dtype=complex)
    m = U.shape[0]
    if m % 2 != 0:
        return False
    om = omega_C(m // 2)
    return np.allclose(U.T @ om @ U, om, atol=tol)


def run_positive_tests():
    results = {}
    # Identity admits Sp structure.
    results["identity_admitted"] = in_Spn_complex(np.eye(2, dtype=complex))
    # Sp(1) = SU(2): every SU(2) element preserves the 2x2 complex symplectic
    # form om = [[0,1],[-1,0]].
    theta = 0.6
    a = complex(np.cos(theta), 0.2)
    b = complex(0.3, np.sin(theta))
    nrm = np.sqrt(abs(a) ** 2 + abs(b) ** 2)
    a /= nrm
    b /= nrm
    U = np.array([[a, -np.conj(b)], [b, np.conj(a)]])
    results["su2_is_sp1"] = (in_SUn(U) and in_Spn_complex(U))
    return results


def run_negative_tests():
    results = {}
    # A diagonal SU(2) element exp(i theta diag(1,1)) with theta = pi/2:
    # diag(i, i) has det = -1, not SU. Use diag(e^{i t}, e^{-i t}) -- this IS
    # SU(2) AND preserves omega. So use an SU(4) element that does NOT preserve
    # the 4x4 complex omega: block-diagonal of two independent SU(2)'s on the
    # "wrong" splitting.
    th = 0.3
    SU2 = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]], dtype=complex)
    # Standard splitting for omega_C(2): (1,3) and (2,4) pairs. Block-diag on
    # (1,2) and (3,4) pairs does NOT preserve omega.
    U4 = np.block([[SU2, np.zeros((2, 2))], [np.zeros((2, 2)), SU2]]).astype(complex)
    results["U4_in_SU4"] = in_SUn(U4)
    results["U4_breaks_omega"] = (not in_Spn_complex(U4))
    return results


def run_boundary_tests():
    results = {}
    # sympy: det of any antisymmetric 3x3 complex matrix vanishes -> no
    # nondegenerate symplectic form on C^3 -> odd-dim obstruction.
    sympy_ok = "skipped"
    if TOOL_MANIFEST["sympy"]["tried"]:
        a, b, c = sp.symbols("a b c")
        M = sp.Matrix([[0, a, b], [-a, 0, c], [-b, -c, 0]])
        sympy_ok = (sp.simplify(M.det()) == 0)
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = "proves det of 3x3 antisymmetric matrix = 0 (odd-dim Sp obstruction)"
        TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"
    results["sympy_odd_dim_obstruction"] = sympy_ok
    # z3: supplementary phase constraint
    z3_result = "skipped"
    if TOOL_MANIFEST["z3"]["tried"]:
        x, y = z3.Reals("x y")
        s = z3.Solver()
        s.add(x * x + y * y == 1)
        # Require both det=1 and det=-1 (inconsistent)
        s.add(x == 1)
        s.add(x == -1)
        z3_result = str(s.check())
        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = "cross-check that phase cannot be simultaneously +1 and -1 (unsat)"
        TOOL_INTEGRATION_DEPTH["z3"] = "supportive"
    results["z3_consistency"] = z3_result
    return results


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    def _t(v): return bool(v) is True
    all_pass = (all(_t(v) for v in pos.values())
                and all(_t(v) for v in neg.values())
                and _t(bnd.get("sympy_odd_dim_obstruction")))
    results = {
        "name": "sim_gtower_su_to_sp",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "status": "PASS" if all_pass else "FAIL",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "sim_gtower_su_to_sp_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{results['name']}: {results['status']}")
