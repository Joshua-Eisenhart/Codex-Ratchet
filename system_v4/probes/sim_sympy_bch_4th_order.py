#!/usr/bin/env python3
"""sim_sympy_bch_4th_order -- canonical sympy-deep BCH expansion certification.
Symbolically certifies exp(X)exp(Y) = exp(Z) through 4th order where
Z = X+Y + 1/2[X,Y] + 1/12([X,[X,Y]]+[Y,[Y,X]]) - 1/24[Y,[X,[X,Y]]] + O(5).
"""
import json, os
import numpy as np
import sympy as sp

from receipt_boundary import apply_default_receipt_boundary

NAME = "sim_sympy_bch_4th_order"
classification = "canonical"
divergence_log = (
    "SymPy is load-bearing for exact noncommutative BCH coefficient checks; "
    "the numpy/scipy ablation is a classical numeric approximation and cannot "
    "certify the symbolic identity."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "numeric-only; BCH identity requires symbolic noncommutative expansion"},
    "pyg":     {"tried": False, "used": False, "reason": "BCH coefficient certification has no graph or message-passing structure for PyG to evaluate"},
    "z3":      {"tried": False, "used": False, "reason": "Z3 is not used because this check needs noncommutative series algebra rather than SMT satisfiability"},
    "cvc5":    {"tried": False, "used": False, "reason": "cvc5 is not used because the packet certifies symbolic noncommutative expansion coefficients"},
    "sympy":   {"tried": True,  "used": True,  "reason": "noncommutative Symbol + series expansion proves identity coefficient-by-coefficient"},
    "clifford":{"tried": False, "used": False, "reason": "BCH holds for arbitrary associative algebra; Clifford is a special case"},
    "geomstats":{"tried": False,"used": False, "reason": "no Riemannian structure needed"},
    "e3nn":    {"tried": False, "used": False, "reason": "The BCH identity is algebraic and does not require equivariant tensor representation checks"},
    "rustworkx":{"tried": False,"used": False, "reason": "No graph traversal, reachability, or combinatorial graph invariant is part of this packet"},
    "xgi":     {"tried": False, "used": False, "reason": "No hyperedge incidence or hypergraph motif calculation is needed for BCH coefficients"},
    "toponetx":{"tried": False, "used": False, "reason": "No cell-complex boundary or topological incidence operator is involved in this packet"},
    "gudhi":   {"tried": False, "used": False, "reason": "No filtration, simplex tree, or persistent-homology computation is part of this packet"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"


def comm(A, B):
    return A*B - B*A


def _exp_series(A, order):
    s = sp.Integer(1)
    term = sp.Integer(1)
    for k in range(1, order+1):
        term = term * A / k
        s = s + term
    return s


def _low_order_residual(expr, t, max_deg):
    expr = sp.expand(expr)
    if expr == 0:
        return sp.Integer(0)
    terms = expr.args if expr.func is sp.Add else [expr]
    low = sp.Integer(0)
    for term in terms:
        deg = 0
        factors = term.args if term.func is sp.Mul else [term]
        for fac in factors:
            if fac == t:
                deg += 1
            elif fac.is_Pow and fac.base == t:
                deg += int(fac.exp)
        if deg <= max_deg:
            low = low + term
    return sp.expand(low)


def bch_residual_order(n):
    t = sp.symbols('t')
    X, Y = sp.symbols('X Y', commutative=False)
    Zt = (t*X + t*Y
          + sp.Rational(1, 2)*comm(t*X, t*Y)
          + sp.Rational(1, 12)*(comm(t*X, comm(t*X, t*Y)) + comm(t*Y, comm(t*Y, t*X)))
          - sp.Rational(1, 24)*comm(t*Y, comm(t*X, comm(t*X, t*Y))))
    lhs = sp.expand(_exp_series(t*X, n) * _exp_series(t*Y, n))
    rhs = sp.expand(_exp_series(Zt, n))
    diff = sp.expand(lhs - rhs)
    return diff, t


def run_positive_tests():
    out = {}
    diff, t = bch_residual_order(4)
    low_order = _low_order_residual(diff, t, 4)
    out["bch_up_to_order_4_vanishes"] = {
        "residual_low_order_is_zero": sp.expand(low_order) == 0,
        "expression": str(low_order),
    }
    return out


def run_negative_tests():
    out = {}
    # Corrupt the 1/12 coefficient -> identity must break.
    t = sp.symbols('t')
    X, Y = sp.symbols('X Y', commutative=False)
    lhs = sp.expand(_exp_series(t*X, 4) * _exp_series(t*Y, 4))
    Zt_bad = (t*X + t*Y + sp.Rational(1,2)*comm(t*X,t*Y)
              + sp.Rational(1,7)*(comm(t*X,comm(t*X,t*Y)) + comm(t*Y,comm(t*Y,t*X))))
    rhs = sp.expand(_exp_series(Zt_bad, 4))
    diff = sp.expand(lhs - rhs)
    low = _low_order_residual(diff, t, 3)
    out["corrupted_coefficient_detected"] = {
        "residual_nonzero": sp.expand(low) != 0
    }
    return out


def run_boundary_tests():
    out = {}
    t = sp.symbols('t')
    X, Y = sp.symbols('X Y', commutative=True)
    lhs = sp.expand(_exp_series(t*X, 4) * _exp_series(t*Y, 4))
    rhs = sp.expand(_exp_series(t*(X+Y), 4))
    low = _low_order_residual(sp.expand(lhs-rhs), t, 4)
    out["commuting_case_collapses"] = {"residual_zero": sp.expand(low) == 0}
    return out


def run_ablation():
    # numpy cannot symbolically certify: with random numeric matrices, equality
    # only holds approximately and cannot distinguish true identity from a
    # numerically-close wrong coefficient.
    rng = np.random.default_rng(0)
    X = rng.standard_normal((3,3))*0.1
    Y = rng.standard_normal((3,3))*0.1
    from scipy.linalg import expm
    def cm(A,B): return A@B - B@A
    Z = (X+Y + 0.5*cm(X,Y)
         + (1/12)*(cm(X,cm(X,Y)) + cm(Y,cm(Y,X)))
         - (1/24)*cm(Y,cm(X,cm(X,Y))))
    err_true = np.linalg.norm(expm(X)@expm(Y) - expm(Z))
    Z_bad = (X+Y + 0.5*cm(X,Y) + (1/13)*(cm(X,cm(X,Y)) + cm(Y,cm(Y,X))))
    err_bad = np.linalg.norm(expm(X)@expm(Y) - expm(Z_bad))
    return {
        "numpy_cannot_certify_symbolically": True,
        "true_residual_numeric": float(err_true),
        "wrong_residual_numeric": float(err_bad),
        "note": "numeric residual is small in both cases for small matrices; only symbolic vanishing certifies the identity",
    }


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    all_pass = (
        positive["bch_up_to_order_4_vanishes"]["residual_low_order_is_zero"]
        and negative["corrupted_coefficient_detected"]["residual_nonzero"]
        and boundary["commuting_case_collapses"]["residual_zero"]
    )
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
        target="Use as bounded SymPy exact BCH coefficient evidence before operator/algebra lego-fit packets.",
    )
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
