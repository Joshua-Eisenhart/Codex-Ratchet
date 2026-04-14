#!/usr/bin/env python3
"""sim_bridge_carnot_admissibility_fence

scope_note: Reframes classical Carnot as a constraint-admissibility fence.
  Illuminates system_v5/new docs/CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md
  (Landauer section). z3 load-bearing: UNSAT proves no admissible engine
  survives with eta > 1 - Tc/Th under positivity + second-law constraints.
"""
import numpy as np
from _doc_illum_common import build_manifest, write_results

NAME = "bridge_carnot_admissibility_fence"
SCOPE_NOTE = ("Bridge: Carnot as admissibility fence; z3 UNSAT that an engine "
              "with eta > 1 - Tc/Th is admissible under Tc<Th, Qh>0, Qc>=0, "
              "W=Qh-Qc, second law Qc/Tc >= Qh/Th. "
              "Illuminates CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md Landauer section.")
CLASSIFICATION = "canonical"
TM, DEPTH = build_manifest()

import z3


def run_positive():
    Tc, Th = z3.Reals("Tc Th")
    Qh, Qc, W = z3.Reals("Qh Qc W")
    eta = z3.Real("eta")
    s = z3.Solver()
    s.add(Tc > 0, Th > 0, Tc < Th)
    s.add(Qh > 0, Qc >= 0)
    s.add(W == Qh - Qc)
    s.add(Qc / Tc >= Qh / Th)   # Clausius: dS_total >= 0
    s.add(eta == W / Qh)
    s.add(eta > 1 - Tc / Th)    # claim to refute
    result = s.check()
    return {"super_carnot_check": str(result),
            "unsat_as_expected": bool(result == z3.unsat)}


def run_negative():
    # Sanity: eta == 1 - Tc/Th should be SAT (the bound is attainable).
    Tc, Th = z3.Reals("Tc Th")
    Qh, Qc, W, eta = z3.Reals("Qh Qc W eta")
    s = z3.Solver()
    s.add(Tc == 300, Th == 600)
    s.add(Qh == 2, Qc == 1, W == 1)
    s.add(eta == W / Qh)
    s.add(eta == 1 - Tc / Th)
    result = s.check()
    return {"attainable_bound_check": str(result),
            "sat_as_expected": bool(result == z3.sat)}


def run_boundary():
    # Tc -> Th (isothermal) forces eta <= 0: a strictly positive-W engine is UNSAT.
    Tc, Th = z3.Reals("Tc Th")
    Qh, Qc, W = z3.Reals("Qh Qc W")
    s = z3.Solver()
    s.add(Tc == Th, Tc > 0)
    s.add(Qh > 0, Qc >= 0, W == Qh - Qc, W > 0)
    s.add(Qc / Tc >= Qh / Th)
    result = s.check()
    return {"isothermal_positive_W": str(result),
            "unsat_as_expected": bool(result == z3.unsat)}


if __name__ == "__main__":
    TM["z3"]["used"] = True
    TM["z3"]["reason"] = "Proves UNSAT for super-Carnot; load-bearing admissibility fence"
    DEPTH["z3"] = "load_bearing"
    DEPTH["pytorch"] = None
    pos = run_positive(); neg = run_negative(); bnd = run_boundary()
    ok = (pos["unsat_as_expected"] and neg["sat_as_expected"]
          and bnd["unsat_as_expected"])
    results = {
        "name": NAME, "scope_note": SCOPE_NOTE,
        "classification": CLASSIFICATION,
        "tool_manifest": TM, "tool_integration_depth": DEPTH,
        "load_bearing_tool": "z3",
        "positive": pos, "negative": neg, "boundary": bnd,
        "pass": bool(ok),
    }
    write_results(NAME, results)
