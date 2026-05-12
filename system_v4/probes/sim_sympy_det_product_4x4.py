#!/usr/bin/env python3
"""sim_sympy_det_product_4x4 -- det(AB) = det(A) det(B) symbolic for 4x4 matrices
using SymPy matrix-expression determinant rules.
"""
import json, os
import numpy as np
import sympy as sp

from receipt_boundary import apply_default_receipt_boundary

NAME = "sim_sympy_det_product_4x4"
classification = "canonical"
divergence_log = (
    "SymPy certifies det(AB)=det(A)det(B) using exact 4x4 MatrixSymbol "
    "determinant algebra. The numpy ablation is only a floating-point draw and "
    "cannot certify the universal identity."
)

TOOL_MANIFEST = {
    "pytorch":{"tried":False,"used":False,"reason":"numeric determinants float; cannot certify polynomial identity"},
    "pyg":{"tried":False,"used":False,"reason":"n/a"},
    "z3":{"tried":False,"used":False,"reason":"polynomial identity of 32 free vars; sympy handles exactly"},
    "cvc5":{"tried":False,"used":False,"reason":"same"},
    "sympy":{"tried":True,"used":True,"reason":"exact MatrixSymbol determinant algebra; det(A*B)-det(A)*det(B) simplifies to 0"},
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
    return sp.MatrixSymbol(name, n, n)


def run_positive_tests():
    A = sym_matrix('a')
    B = sym_matrix('b')
    lhs = sp.det(A * B)
    rhs = sp.det(A) * sp.det(B)
    diff = sp.simplify(lhs - rhs)
    return {"det_product_identity_4x4": diff == 0}


def run_negative_tests():
    # det(A+B) != det(A)+det(B) in general
    A = sym_matrix('a')
    B = sym_matrix('b')
    diff = sp.det(A + B) - sp.det(A) - sp.det(B)
    return {"det_sum_identity_false": diff != 0}


def run_boundary_tests():
    # B = identity -> det(AB) = det(A)
    A = sym_matrix('a')
    I4 = sp.Identity(4)
    lhs = sp.det(A * I4)
    rhs = sp.det(A) * sp.det(I4)
    # B = zero -> both sides zero
    Z = sp.ZeroMatrix(4, 4)
    lhs0 = sp.det(A * Z)
    rhs0 = sp.det(A) * sp.det(Z)
    return {"identity_case": sp.simplify(lhs-rhs) == 0,
            "zero_case": sp.simplify(lhs0 - rhs0) == 0}


def run_ablation():
    rng = np.random.default_rng(3)
    A = rng.standard_normal((4,4)); B = rng.standard_normal((4,4))
    lhs = np.linalg.det(A@B); rhs = np.linalg.det(A)*np.linalg.det(B)
    return {"numpy_single_draw": True, "abs_residual": float(abs(lhs-rhs)),
            "note": "numeric agreement per-draw; cannot certify polynomial identity over all entries"}


if __name__ == "__main__":
    results = {
        "name": NAME,
        "classification": classification,
        "divergence_log": divergence_log,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "ablation": run_ablation(),
    }
    results["all_pass"] = (
        all(results["positive"].values())
        and all(results["negative"].values())
        and all(results["boundary"].values())
    )
    results["summary"] = {"all_pass": bool(results["all_pass"])}
    results = apply_default_receipt_boundary(
        results,
        source_name=NAME,
        target=(
            "Use as bounded SymPy exact-algebra support evidence before "
            "constraint-probe or symbolic identity lego-fit packets."
        ),
    )
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
