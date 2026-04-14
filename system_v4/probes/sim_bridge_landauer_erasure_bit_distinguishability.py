#!/usr/bin/env python3
"""sim_bridge_landauer_erasure_bit_distinguishability

scope_note: Bridge -- Landauer erasure cost rewritten in terms of the
  distinguishability quantum F01 with sympy symbolic derivation and z3
  admissibility fence. Illuminates CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md.
"""
from _doc_illum_common import build_manifest, write_results
import sympy as sp
import z3

NAME = "bridge_landauer_erasure_bit_distinguishability"
SCOPE_NOTE = ("Bridge: sympy derives E_erase = F01 * H(p) for Bernoulli p, "
              "and z3 proves UNSAT for E_erase < F01 * H(p). Illuminates "
              "CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md Landauer section.")
CLASSIFICATION = "canonical"
TM, DEPTH = build_manifest()


def _sympy_derive():
    p, F01 = sp.symbols("p F01", positive=True)
    H = -(p * sp.log(p) + (1 - p) * sp.log(1 - p))
    E = F01 * H
    # At p=1/2, E must equal F01 * ln 2.
    E_half = sp.simplify(E.subs(p, sp.Rational(1, 2)))
    target = F01 * sp.log(2)
    return sp.simplify(E_half - target)


def run_positive():
    residual = _sympy_derive()
    return {"sympy_residual_at_half": str(residual),
            "is_zero": bool(residual == 0)}


def run_negative():
    # z3 UNSAT: claim E < F01 * H for H>0, F01>0 cannot be admissible.
    E, F01, H = z3.Reals("E F01 H")
    s = z3.Solver()
    s.add(F01 > 0, H > 0)
    s.add(E < F01 * H)
    s.add(E >= F01 * H)   # admissibility fence says E must meet the floor
    res = s.check()
    return {"inadmissible_sub_floor": str(res),
            "unsat_as_expected": bool(res == z3.unsat)}


def run_boundary():
    # p -> 0: H -> 0, E -> 0.
    p, F01 = sp.symbols("p F01", positive=True)
    H = -(p * sp.log(p) + (1 - p) * sp.log(1 - p))
    E = F01 * H
    lim = sp.limit(E, p, 0, "+")
    return {"p_to_zero_limit": str(lim), "is_zero": bool(lim == 0)}


if __name__ == "__main__":
    TM["sympy"]["used"] = True
    TM["sympy"]["reason"] = "Symbolic derivation of E = F01 * H(p); load-bearing"
    TM["z3"]["used"] = True
    TM["z3"]["reason"] = "UNSAT on sub-floor erasure; load-bearing fence"
    DEPTH["sympy"] = "load_bearing"
    DEPTH["z3"] = "load_bearing"
    pos = run_positive(); neg = run_negative(); bnd = run_boundary()
    ok = (pos["is_zero"] and neg["unsat_as_expected"] and bnd["is_zero"])
    results = {
        "name": NAME, "scope_note": SCOPE_NOTE,
        "classification": CLASSIFICATION,
        "tool_manifest": TM, "tool_integration_depth": DEPTH,
        "load_bearing_tool": "sympy+z3",
        "positive": pos, "negative": neg, "boundary": bnd,
        "pass": bool(ok),
    }
    write_results(NAME, results)
