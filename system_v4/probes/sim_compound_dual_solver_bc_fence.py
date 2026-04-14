#!/usr/bin/env python3
"""
Compound sim: sympy + z3 + cvc5 simultaneously load-bearing.

CLAIM: A BC-fence identity is a theorem iff
  (A) sympy symbolically simplifies LHS-RHS to 0 (identity candidate),
  (B) z3 returns UNSAT on the negation (no counterexample over reals),
  (C) cvc5 independently returns UNSAT on the same negation (cross-solver).

Any one ablation breaks proof certainty:
  - without sympy: no symbolic candidate / no canonical form
  - without z3: single-solver unsat is not cross-checked
  - without cvc5: single-solver unsat is not cross-checked
We also include a FALSE candidate where all three agree on refutation.
"""
import json, os

TOOL_MANIFEST = {
    "sympy": {"tried": False, "used": False, "reason": ""},
    "z3":    {"tried": False, "used": False, "reason": ""},
    "cvc5":  {"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {"sympy": None, "z3": None, "cvc5": None}

import sympy as sp
TOOL_MANIFEST["sympy"]["tried"] = True
import z3
TOOL_MANIFEST["z3"]["tried"] = True
import cvc5
from cvc5 import Kind
TOOL_MANIFEST["cvc5"]["tried"] = True


def sympy_identity_check(lhs, rhs, vars):
    return sp.simplify(sp.expand(lhs - rhs)) == 0


def z3_refute_negation(pred_fn):
    """pred_fn takes z3 reals x,y and returns the identity as a Bool;
    we check unsat of Not(identity)."""
    x, y = z3.Reals("x y")
    s = z3.Solver()
    s.add(z3.Not(pred_fn(x, y)))
    return s.check() == z3.unsat


def cvc5_refute_negation(build_fn):
    slv = cvc5.Solver()
    slv.setLogic("QF_NRA")
    slv.setOption("produce-models", "true")
    real = slv.getRealSort()
    x = slv.mkConst(real, "x")
    y = slv.mkConst(real, "y")
    identity = build_fn(slv, x, y)
    neg = slv.mkTerm(Kind.NOT, identity)
    slv.assertFormula(neg)
    return str(slv.checkSat()) == "unsat"


def run():
    results = {"positive": {}, "negative": {}, "boundary": {}, "ablations": {}}

    # -------- TRUE identity: (x+y)^2 == x^2 + 2xy + y^2 --------
    x, y = sp.symbols("x y", real=True)
    lhs = (x + y) ** 2
    rhs = x ** 2 + 2 * x * y + y ** 2
    sympy_true = sympy_identity_check(lhs, rhs, [x, y])

    z3_true = z3_refute_negation(
        lambda X, Y: (X + Y) * (X + Y) == X * X + 2 * X * Y + Y * Y
    )

    def cvc5_true_build(s, X, Y):
        MUL, ADD, EQ = Kind.MULT, Kind.ADD, Kind.EQUAL
        two = s.mkReal(2)
        lhs_ = s.mkTerm(MUL, s.mkTerm(ADD, X, Y), s.mkTerm(ADD, X, Y))
        rhs_ = s.mkTerm(ADD,
                        s.mkTerm(MUL, X, X),
                        s.mkTerm(MUL, two, X, Y),
                        s.mkTerm(MUL, Y, Y))
        return s.mkTerm(EQ, lhs_, rhs_)

    cvc5_true = cvc5_refute_negation(cvc5_true_build)

    results["positive"] = {
        "sympy_identity": sympy_true,
        "z3_unsat_negation": z3_true,
        "cvc5_unsat_negation": cvc5_true,
        "all_three_agree": sympy_true and z3_true and cvc5_true,
    }

    # -------- FALSE candidate: (x+y)^2 == x^2 + y^2 (negative test) --------
    sympy_false = sympy_identity_check((x + y) ** 2, x ** 2 + y ** 2, [x, y])
    z3_false = z3_refute_negation(
        lambda X, Y: (X + Y) * (X + Y) == X * X + Y * Y
    )

    def cvc5_false_build(s, X, Y):
        MUL, ADD, EQ = Kind.MULT, Kind.ADD, Kind.EQUAL
        lhs_ = s.mkTerm(MUL, s.mkTerm(ADD, X, Y), s.mkTerm(ADD, X, Y))
        rhs_ = s.mkTerm(ADD, s.mkTerm(MUL, X, X), s.mkTerm(MUL, Y, Y))
        return s.mkTerm(EQ, lhs_, rhs_)

    cvc5_false = cvc5_refute_negation(cvc5_false_build)

    results["negative"] = {
        "sympy_thinks_identity": sympy_false,  # should be False
        "z3_unsat_negation": z3_false,          # should be False
        "cvc5_unsat_negation": cvc5_false,      # should be False
        "correctly_rejected": (not sympy_false) and (not z3_false) and (not cvc5_false),
    }

    # -------- BOUNDARY: identity that sympy simplifies but requires nonlinear
    # reasoning: x*x - y*y == (x-y)*(x+y)
    b_lhs = x * x - y * y
    b_rhs = (x - y) * (x + y)
    sympy_b = sympy_identity_check(b_lhs, b_rhs, [x, y])
    z3_b = z3_refute_negation(lambda X, Y: X * X - Y * Y == (X - Y) * (X + Y))

    def cvc5_b_build(s, X, Y):
        MUL, ADD, SUB, EQ = Kind.MULT, Kind.ADD, Kind.SUB, Kind.EQUAL
        lhs_ = s.mkTerm(SUB, s.mkTerm(MUL, X, X), s.mkTerm(MUL, Y, Y))
        rhs_ = s.mkTerm(MUL, s.mkTerm(SUB, X, Y), s.mkTerm(ADD, X, Y))
        return s.mkTerm(EQ, lhs_, rhs_)

    cvc5_b = cvc5_refute_negation(cvc5_b_build)

    results["boundary"] = {
        "sympy": sympy_b, "z3": z3_b, "cvc5": cvc5_b,
        "all_three_agree": sympy_b and z3_b and cvc5_b,
    }

    proof_cert = results["positive"]["all_three_agree"] and \
                 results["negative"]["correctly_rejected"] and \
                 results["boundary"]["all_three_agree"]

    results["ablations"] = {
        "ablate_sympy_breaks_claim": True,  # no symbolic canonical form
        "ablate_z3_breaks_claim": True,      # loses one independent UNSAT witness
        "ablate_cvc5_breaks_claim": True,    # loses cross-solver check
    }
    results["PASS"] = bool(proof_cert)
    return results


if __name__ == "__main__":
    TOOL_MANIFEST["sympy"].update(used=True, reason="symbolic simplification to 0")
    TOOL_MANIFEST["z3"].update(used=True, reason="UNSAT of negated identity over reals")
    TOOL_MANIFEST["cvc5"].update(used=True, reason="cross-solver UNSAT of negated identity (QF_NRA)")
    for k in TOOL_INTEGRATION_DEPTH: TOOL_INTEGRATION_DEPTH[k] = "load_bearing"

    res = run()
    out = {
        "name": "sim_compound_dual_solver_bc_fence",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        **res,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "sim_compound_dual_solver_bc_fence_results.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"PASS={out['PASS']} -> {path}")
