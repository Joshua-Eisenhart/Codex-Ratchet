#!/usr/bin/env python3
"""sim_sympy_det_product_4x4 -- det(AB) = det(A) det(B) symbolic for 4x4 matrices
with fully symbolic entries. Certifies the identity by simplify-to-zero.
"""
import json, os
import numpy as np
import sympy as sp

TOOL_MANIFEST = {
    "pytorch":{"tried":False,"used":False,"reason":"numeric determinants float; cannot certify polynomial identity"},
    "pyg":{"tried":False,"used":False,"reason":"n/a"},
    "z3":{"tried":False,"used":False,"reason":"polynomial identity of 32 free vars; sympy handles exactly"},
    "cvc5":{"tried":False,"used":False,"reason":"same"},
    "sympy":{"tried":True,"used":True,"reason":"symbolic determinant expansion; expand(det(AB)-det(A)det(B)) simplifies to 0"},
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


def sym_matrix(name, n=4):
    return sp.Matrix(n, n, lambda i, j: sp.symbols(f'{name}_{i}{j}'))


def run_positive_tests():
    A = sym_matrix('a')
    B = sym_matrix('b')
    lhs = (A*B).det()
    rhs = A.det() * B.det()
    diff = sp.expand(lhs - rhs)
    return {"det_product_identity_4x4": diff == 0}


def run_negative_tests():
    # det(A+B) != det(A)+det(B) in general
    A = sym_matrix('a')
    B = sym_matrix('b')
    diff = sp.expand((A+B).det() - A.det() - B.det())
    return {"det_sum_identity_false": diff != 0}


def run_boundary_tests():
    # B = identity -> det(AB) = det(A)
    A = sym_matrix('a')
    I4 = sp.eye(4)
    lhs = (A*I4).det()
    rhs = A.det() * I4.det()
    # B = zero -> both sides zero
    Z = sp.zeros(4,4)
    lhs0 = (A*Z).det()
    rhs0 = A.det() * Z.det()
    return {"identity_case": sp.expand(lhs-rhs) == 0,
            "zero_case": sp.expand(lhs0 - rhs0) == 0}


def run_ablation():
    rng = np.random.default_rng(3)
    A = rng.standard_normal((4,4)); B = rng.standard_normal((4,4))
    lhs = np.linalg.det(A@B); rhs = np.linalg.det(A)*np.linalg.det(B)
    return {"numpy_single_draw": True, "abs_residual": float(abs(lhs-rhs)),
            "note": "numeric agreement per-draw; cannot certify polynomial identity over all entries"}


if __name__ == "__main__":
    results = {
        "name": "sympy_det_product_4x4",
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
    out_path = os.path.join(out_dir, "sympy_det_product_4x4_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
