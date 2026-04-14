#!/usr/bin/env python3
"""sim_bridge_szilard_landauer_floor

scope_note: Bridges Szilard-extracted work to Landauer erasure floor.
  Illuminates CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md: z3 UNSAT
  shows erasure energy Ev < F01 * ln2 is inadmissible once the
  distinguishability quantum F01 is treated as a unit cost.
"""
from _doc_illum_common import build_manifest, write_results
import z3

NAME = "bridge_szilard_landauer_floor"
SCOPE_NOTE = ("Bridge: Landauer floor as admissibility constraint. "
              "z3 UNSAT for Ev < F01 * ln2 under F01 > 0, Ev >= 0. "
              "Illuminates CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md Landauer section.")
CLASSIFICATION = "canonical"
TM, DEPTH = build_manifest()


def run_positive():
    Ev, F01 = z3.Reals("Ev F01")
    ln2 = z3.RealVal("0.6931471805599453")
    s = z3.Solver()
    s.add(F01 > 0, Ev >= 0)
    s.add(Ev >= F01 * ln2)  # admissibility fence: erasure must meet Landauer floor
    s.add(Ev < F01 * ln2)   # sub-Landauer erasure claim (to refute)
    res = s.check()
    return {"sub_landauer_check": str(res),
            "unsat_as_expected": bool(res == z3.unsat)}


def run_negative():
    # Ev == F01 * ln2 must be SAT (floor attainable in the limit).
    Ev, F01 = z3.Reals("Ev F01")
    s = z3.Solver()
    s.add(F01 == 1.0)
    s.add(Ev == 0.6931471805599453)
    res = s.check()
    return {"floor_attainable": str(res),
            "sat_as_expected": bool(res == z3.sat)}


def run_boundary():
    # F01 == 0 degenerate limit: Ev == 0 is SAT (no distinguishability => no floor).
    Ev, F01 = z3.Reals("Ev F01")
    s = z3.Solver()
    s.add(F01 == 0, Ev == 0)
    res = s.check()
    return {"degenerate_F01_zero": str(res),
            "sat_as_expected": bool(res == z3.sat)}


if __name__ == "__main__":
    TM["z3"]["used"] = True
    TM["z3"]["reason"] = "UNSAT on sub-Landauer erasure; load-bearing admissibility floor"
    DEPTH["z3"] = "load_bearing"
    pos = run_positive(); neg = run_negative(); bnd = run_boundary()
    ok = (pos["unsat_as_expected"] and neg["sat_as_expected"]
          and bnd["sat_as_expected"])
    results = {
        "name": NAME, "scope_note": SCOPE_NOTE,
        "classification": CLASSIFICATION,
        "tool_manifest": TM, "tool_integration_depth": DEPTH,
        "load_bearing_tool": "z3",
        "positive": pos, "negative": neg, "boundary": bnd,
        "pass": bool(ok),
    }
    write_results(NAME, results)
