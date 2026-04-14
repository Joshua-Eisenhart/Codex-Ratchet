#!/usr/bin/env python3
"""sim_bridge_maxwell_demon_distinguishability_cost

scope_note: Bridge -- a zero-distinguishability-cost Maxwell demon is
  inadmissible. Illuminates CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md.
  z3 load-bearing: UNSAT under W>0, I_bits>=0, erase_cost = F01*I_bits*ln2,
  net = erase_cost - W, F01=0 AND W>0 => inconsistent with non-negative net.
"""
from _doc_illum_common import build_manifest, write_results
import z3

NAME = "bridge_maxwell_demon_distinguishability_cost"
SCOPE_NOTE = ("Bridge: z3 UNSAT that a demon extracts W>0 at F01=0 (no "
              "distinguishability cost) while maintaining non-negative "
              "net dissipation. Illuminates CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md.")
CLASSIFICATION = "canonical"
TM, DEPTH = build_manifest()

LN2 = z3.RealVal("0.6931471805599453")


def run_positive():
    F01, I_bits, W, net = z3.Reals("F01 I_bits W net")
    s = z3.Solver()
    s.add(F01 == 0, I_bits >= 0, W > 0)
    s.add(net == F01 * I_bits * LN2 - W)
    s.add(net >= 0)
    res = s.check()
    return {"zero_cost_demon": str(res),
            "unsat_as_expected": bool(res == z3.unsat)}


def run_negative():
    # With F01 > 0 and W <= F01*I*ln2, a consistent demon is SAT.
    F01, I_bits, W, net = z3.Reals("F01 I_bits W net")
    s = z3.Solver()
    s.add(F01 == 1, I_bits == 1, W == 0.5)
    s.add(net == F01 * I_bits * LN2 - W)
    s.add(net >= 0)
    res = s.check()
    return {"honest_demon": str(res),
            "sat_as_expected": bool(res == z3.sat)}


def run_boundary():
    # W == F01 * I * ln2 saturates the fence: SAT with net == 0.
    F01, I_bits, W, net = z3.Reals("F01 I_bits W net")
    s = z3.Solver()
    s.add(F01 == 1, I_bits == 2)
    s.add(W == F01 * I_bits * LN2)
    s.add(net == F01 * I_bits * LN2 - W)
    s.add(net == 0)
    res = s.check()
    return {"saturated_fence": str(res),
            "sat_as_expected": bool(res == z3.sat)}


if __name__ == "__main__":
    TM["z3"]["used"] = True
    TM["z3"]["reason"] = "UNSAT for zero-cost demon; load-bearing distinguishability fence"
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
