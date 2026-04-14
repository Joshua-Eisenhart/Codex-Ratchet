#!/usr/bin/env python3
"""sim_sympy_jacobi_su2 -- Jacobi identity [X,[Y,Z]]+[Y,[Z,X]]+[Z,[X,Y]] = 0 for su(2).
Symbolic over arbitrary linear combinations of generators with symbolic coefficients.
"""
import json, os
import numpy as np
import sympy as sp

TOOL_MANIFEST = {
    "pytorch":{"tried":False,"used":False,"reason":"random numeric matrices cannot prove identity for all coefficients"},
    "pyg":{"tried":False,"used":False,"reason":"not graph"},
    "z3":{"tried":False,"used":False,"reason":"entries complex rationals; sympy simpler"},
    "cvc5":{"tried":False,"used":False,"reason":"same"},
    "sympy":{"tried":True,"used":True,"reason":"simplify of symbolic commutator sum returns exact zero matrix"},
    "clifford":{"tried":False,"used":False,"reason":"not needed"},
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
Jx, Jy, Jz = sx/2, sy/2, sz/2


def comm(A,B): return A*B - B*A


def run_positive_tests():
    a1,a2,a3,b1,b2,b3,c1,c2,c3 = sp.symbols('a1:4 b1:4 c1:4', real=True)
    X = a1*Jx + a2*Jy + a3*Jz
    Y = b1*Jx + b2*Jy + b3*Jz
    Z = c1*Jx + c2*Jy + c3*Jz
    s = sp.simplify(comm(X, comm(Y,Z)) + comm(Y, comm(Z,X)) + comm(Z, comm(X,Y)))
    return {"jacobi_zero": s == sp.zeros(2,2)}


def run_negative_tests():
    # q-deformed bracket [A,B]_q = A*B - 2*B*A violates Jacobi generically
    def qbr(A,B): return A*B - 2*B*A
    X, Y, Z = Jx, Jy, Jz
    s = sp.simplify(qbr(X, qbr(Y,Z)) + qbr(Y, qbr(Z,X)) + qbr(Z, qbr(X,Y)))
    return {"qdeformed_bracket_violates_jacobi": s != sp.zeros(2,2), "value": str(s)}


def run_boundary_tests():
    # X=Y case: [X,[X,Z]] + [X,[Z,X]] + [Z,[X,X]] = [X,[X,Z]] - [X,[X,Z]] + 0 = 0
    X, Z = Jx, Jz
    s = sp.simplify(comm(X,comm(X,Z)) + comm(X,comm(Z,X)) + comm(Z,comm(X,X)))
    # Zero generator
    s0 = sp.simplify(comm(sp.zeros(2,2), comm(Jy,Jz)) + comm(Jy,comm(Jz,sp.zeros(2,2))) + comm(Jz,comm(sp.zeros(2,2),Jy)))
    return {"repeat_generator_zero": s == sp.zeros(2,2), "zero_operand": s0 == sp.zeros(2,2)}


def run_ablation():
    # numpy: random numeric triple satisfies ~0 within fp error; cannot distinguish
    # from a perturbed "nearly-Lie" bracket at scale ~1e-12.
    rng = np.random.default_rng(1)
    a,b,c = [rng.standard_normal(3) for _ in range(3)]
    Jxn = np.array([[0,1],[1,0]])/2
    Jyn = np.array([[0,-1j],[1j,0]])/2
    Jzn = np.array([[1,0],[0,-1]])/2
    def mk(v): return v[0]*Jxn + v[1]*Jyn + v[2]*Jzn
    def cm(A,B): return A@B - B@A
    X,Y,Z = mk(a),mk(b),mk(c)
    s = cm(X,cm(Y,Z)) + cm(Y,cm(Z,X)) + cm(Z,cm(X,Y))
    return {"numpy_cannot_certify_all_coeffs": True, "residual_norm_single_draw": float(np.linalg.norm(s))}


if __name__ == "__main__":
    results = {
        "name": "sympy_jacobi_su2",
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
    out_path = os.path.join(out_dir, "sympy_jacobi_su2_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
