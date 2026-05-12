#!/usr/bin/env python3
"""sim_sympy_campbell_pauli -- Campbell identity exp(iaX)exp(ibY)exp(-iaX) etc
for Pauli triples; symbolic closed-form certification via su(2) rotation algebra.
"""
import json, os
import numpy as np
import sympy as sp

from receipt_boundary import apply_default_receipt_boundary

NAME = "sim_sympy_campbell_pauli"
classification = "canonical"
divergence_log = (
    "SymPy is load-bearing for exact Pauli rotation-conjugation identities; "
    "the numpy ablation is a classical single-angle numeric check and cannot "
    "certify the symbolic trigonometric identity."
)

TOOL_MANIFEST = {
    "pytorch":{"tried":False,"used":False,"reason":"numeric expm won't certify closed-form equality"},
    "pyg":{"tried":False,"used":False,"reason":"PyG is not used because the Pauli conjugation identity is not a graph learning or message-passing problem"},
    "z3":{"tried":False,"used":False,"reason":"trigonometric identities beyond nonlinear SMT"},
    "cvc5":{"tried":False,"used":False,"reason":"cvc5 is not used because nonlinear symbolic trigonometric simplification is handled directly by SymPy here"},
    "sympy":{"tried":True,"used":True,"reason":"symbolic matrix exponentials + simplify prove rotation-conjugation identity exactly"},
    "clifford":{"tried":False,"used":False,"reason":"cross-check only; identity is purely algebraic"},
    "geomstats":{"tried":False,"used":False,"reason":"Geomstats is not used because the packet checks exact symbolic matrices, not manifold distances or geodesics"},
    "e3nn":{"tried":False,"used":False,"reason":"e3nn is not used because no equivariant neural representation or spherical tensor feature is involved"},
    "rustworkx":{"tried":False,"used":False,"reason":"rustworkx is not used because no graph traversal, DAG, or graph invariant is part of the identity"},
    "xgi":{"tried":False,"used":False,"reason":"XGI is not used because the packet has no hypergraph incidence, hyperedge, or higher-order network structure"},
    "toponetx":{"tried":False,"used":False,"reason":"TopoNetX is not used because no cell complex, cochain, or boundary operator is evaluated"},
    "gudhi":{"tried":False,"used":False,"reason":"GUDHI is not used because no simplex tree, filtration, or persistent homology calculation is present"},
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
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    all_pass = all(positive.values()) and all(negative.values()) and all(boundary.values())
    results = {
        "name": NAME,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "ablation": run_ablation(),
        "classification": classification,
        "divergence_log": divergence_log,
        "summary": {"all_pass": bool(all_pass)},
        "all_pass": bool(all_pass),
    }
    results = apply_default_receipt_boundary(
        results,
        source_name=NAME,
        target="Use as bounded SymPy exact Pauli conjugation evidence before operator/algebra lego-fit packets.",
    )
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
