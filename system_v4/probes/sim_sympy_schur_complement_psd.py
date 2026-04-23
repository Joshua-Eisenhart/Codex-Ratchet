#!/usr/bin/env python3
"""sim_sympy_schur_complement_psd -- Symbolic Schur-complement PSD equivalence.
For symmetric M = [[A,B],[B.T,C]] with A>0: M >= 0 iff C - B.T A^{-1} B >= 0.
We symbolically verify the block factorization M = L D L.T exactly.
"""
import json, os
import numpy as np
import sympy as sp

TOOL_MANIFEST = {
    "pytorch":{"tried":False,"used":False,"reason":"numeric eigenvalues can't certify symbolic identity"},
    "pyg":{"tried":False,"used":False,"reason":"not graph"},
    "z3":{"tried":False,"used":False,"reason":"rational-matrix identity simpler in sympy"},
    "cvc5":{"tried":False,"used":False,"reason":"same"},
    "sympy":{"tried":True,"used":True,"reason":"block LDL factorization simplify-to-zero certifies identity exactly"},
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


def run_positive_tests():
    a,b,c,d,e,f = sp.symbols('a b c d e f', real=True)
    A = sp.Matrix([[a, b],[b, c]])
    B = sp.Matrix([[d],[e]])
    C = sp.Matrix([[f]])
    M = sp.Matrix.vstack(sp.Matrix.hstack(A, B), sp.Matrix.hstack(B.T, C))
    # Schur complement
    S = C - B.T * A.inv() * B
    # LDL block factorization
    I2 = sp.eye(2)
    L = sp.Matrix.vstack(sp.Matrix.hstack(I2, sp.zeros(2,1)),
                         sp.Matrix.hstack((A.inv()*B).T, sp.eye(1)))
    D = sp.Matrix.vstack(sp.Matrix.hstack(A, sp.zeros(2,1)),
                         sp.Matrix.hstack(sp.zeros(1,2), S))
    recon = sp.simplify(L * D * L.T)
    diff = sp.simplify(recon - M)
    return {"block_LDL_factorization_exact": diff == sp.zeros(3,3)}


def run_negative_tests():
    # Use wrong Schur complement (sign flip) -> factorization fails
    a,b,c,d,e,f = sp.symbols('a b c d e f', real=True)
    A = sp.Matrix([[a, b],[b, c]])
    B = sp.Matrix([[d],[e]])
    C = sp.Matrix([[f]])
    M = sp.Matrix.vstack(sp.Matrix.hstack(A, B), sp.Matrix.hstack(B.T, C))
    S_wrong = C + B.T * A.inv() * B
    I2 = sp.eye(2)
    L = sp.Matrix.vstack(sp.Matrix.hstack(I2, sp.zeros(2,1)),
                         sp.Matrix.hstack((A.inv()*B).T, sp.eye(1)))
    D = sp.Matrix.vstack(sp.Matrix.hstack(A, sp.zeros(2,1)),
                         sp.Matrix.hstack(sp.zeros(1,2), S_wrong))
    recon = sp.simplify(L*D*L.T)
    return {"wrong_sign_breaks_factorization": sp.simplify(recon - M) != sp.zeros(3,3)}


def run_boundary_tests():
    # B = 0 case: Schur complement = C exactly
    a,b,c,f = sp.symbols('a b c f', real=True)
    A = sp.Matrix([[a,b],[b,c]])
    B = sp.zeros(2,1)
    C = sp.Matrix([[f]])
    S = sp.simplify(C - B.T*A.inv()*B)
    return {"B_zero_schur_equals_C": S == C}


def run_ablation():
    # numpy numeric: pick specific PSD A,B,C; verifying Schur condition requires eigvals>=0
    rng = np.random.default_rng(2)
    A = np.array([[2.0, 0.3],[0.3, 1.5]])
    B = rng.standard_normal((2,1))
    C = np.array([[3.0]])
    S = C - B.T @ np.linalg.inv(A) @ B
    M = np.block([[A, B],[B.T, C]])
    return {"numpy_only_verifies_this_instance": True,
            "min_eig_M": float(np.linalg.eigvalsh(M).min()),
            "schur_scalar": float(S[0,0]),
            "note": "numeric can confirm one instance; cannot certify symbolic LDL identity"}


if __name__ == "__main__":
    results = {
        "name": "sympy_schur_complement_psd",
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
    out_path = os.path.join(out_dir, "sympy_schur_complement_psd_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
