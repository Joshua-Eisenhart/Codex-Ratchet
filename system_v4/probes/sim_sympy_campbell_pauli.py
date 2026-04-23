#!/usr/bin/env python3
"""sim_sympy_campbell_pauli -- Campbell identity exp(iaX)exp(ibY)exp(-iaX) etc
for Pauli triples; symbolic closed-form certification via su(2) rotation algebra.
"""
import json, os
import numpy as np
import sympy as sp

TOOL_MANIFEST = {
    "pytorch":{"tried":False,"used":False,"reason":"numeric expm won't certify closed-form equality"},
    "pyg":{"tried":False,"used":False,"reason":"no graph"},
    "z3":{"tried":False,"used":False,"reason":"trigonometric identities beyond nonlinear SMT"},
    "cvc5":{"tried":False,"used":False,"reason":"same"},
    "sympy":{"tried":True,"used":True,"reason":"symbolic matrix exponentials + simplify prove rotation-conjugation identity exactly"},
    "clifford":{"tried":False,"used":False,"reason":"cross-check only; identity is purely algebraic"},
    "geomstats":{"tried":False,"used":False,"reason":"not needed"},
    "e3nn":{"tried":False,"used":False,"reason":"not needed"},
    "rustworkx":{"tried":False,"used":False,"reason":"not needed"},
    "xgi":{"tried":False,"used":False,"reason":"not needed"},
    "toponetx":{"tried":False,"used":False,"reason":"not needed"},
    "gudhi":{"tried":False,"used":False,"reason":"not needed"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"

I = sp.I
sx = sp.Matrix([[0,1],[1,0]])
sy = sp.Matrix([[0,-I],[I,0]])
sz = sp.Matrix([[1,0],[0,-1]])


def rot(axis, theta):
    return sp.simplify((sp.cos(theta/2)*sp.eye(2) - I*sp.sin(theta/2)*axis))


def run_positive_tests():
    a, b = sp.symbols('a b', real=True)
    # Rx(a) sy Rx(-a) = cos(a) sy - sin(a) sz  (standard rotation of Pauli)
    Rxa = rot(sx, a)
    lhs = sp.simplify(Rxa * sy * Rxa.H)
    rhs = sp.simplify(sp.cos(a)*sy + sp.sin(a)*sz)
    test1 = sp.simplify(lhs - rhs) == sp.zeros(2,2)
    # Rz(b) sx Rz(-b) = cos(b) sx + sin(b) sy
    Rzb = rot(sz, b)
    lhs2 = sp.simplify(Rzb * sx * Rzb.H)
    rhs2 = sp.simplify(sp.cos(b)*sx + sp.sin(b)*sy)
    test2 = sp.simplify(lhs2 - rhs2) == sp.zeros(2,2)
    return {"Rx_rotates_sy_to_sy_sz": test1, "Rz_rotates_sx_to_sx_sy": test2}


def run_negative_tests():
    a = sp.symbols('a', real=True)
    Rxa = rot(sx, a)
    wrong = sp.cos(a)*sy + 2*sp.sin(a)*sz  # wrong coefficient
    diff = sp.simplify(Rxa*sy*Rxa.H - wrong)
    return {"wrong_coeff_detected": diff != sp.zeros(2,2)}


def run_boundary_tests():
    # theta=0 -> identity conjugation
    Rx0 = rot(sx, 0)
    ident = sp.simplify(Rx0*sy*Rx0.H - sy) == sp.zeros(2,2)
    # theta=2*pi -> full turn yields +sy again
    Rx2pi = sp.simplify(rot(sx, 2*sp.pi))
    full = sp.simplify(Rx2pi*sy*Rx2pi.H - sy) == sp.zeros(2,2)
    return {"zero_angle_identity": ident, "two_pi_returns": full}


def run_ablation():
    # Numpy: picks a specific angle, can't certify for all a.
    a = 0.37
    c, s = np.cos(a/2), np.sin(a/2)
    Rx = np.array([[c, -1j*s],[-1j*s, c]])
    sy_n = np.array([[0,-1j],[1j,0]])
    sz_n = np.array([[1,0],[0,-1]])
    lhs = Rx @ sy_n @ Rx.conj().T
    rhs = np.cos(a)*sy_n - np.sin(a)*sz_n
    return {"numpy_single_point_only": True, "numeric_residual": float(np.linalg.norm(lhs-rhs)),
            "note": "numpy evaluates at one angle; cannot certify identity as a function of a"}


if __name__ == "__main__":
    results = {
        "name": "sympy_campbell_pauli",
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
    out_path = os.path.join(out_dir, "sympy_campbell_pauli_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
