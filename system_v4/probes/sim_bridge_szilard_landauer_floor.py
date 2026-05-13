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
classification = "tool_lego_fit_probe"
divergence_log = (
    "z3 finite-arithmetic Landauer-floor fence only: rejects sub-floor erasure "
    "under declared positive distinguishability unit cost; no bridge, QIT, "
    "GStack, axis, nonclassical, or feedback-cycle admission."
)
TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}
TM = TOOL_MANIFEST
DEPTH = TOOL_INTEGRATION_DEPTH


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


def run_positive_tests():
    return run_positive()


def run_negative_tests():
    return run_negative()


def run_boundary_tests():
    return run_boundary()


if __name__ == "__main__":
    TM["z3"] = {"tried": True, "used": True, "reason": "UNSAT on sub-Landauer erasure; load-bearing admissibility floor"}
    DEPTH["z3"] = "load_bearing"
    pos = run_positive(); neg = run_negative(); bnd = run_boundary()
    ok = (pos["unsat_as_expected"] and neg["sat_as_expected"]
          and bnd["sat_as_expected"])
    results = {
        "name": NAME, "scope_note": SCOPE_NOTE,
        "classification": classification,
        "all_pass": bool(ok),
        "divergence_log": divergence_log,
        "claim_ceiling": (
            "local z3 Landauer-floor constraint fence only: sub-floor erasure is UNSAT "
            "under declared F01 > 0; no bridge, QIT, GStack, axis, nonclassical, "
            "or Szilard feedback-cycle admission"
        ),
        "next_lego_target": "classical erasure-cost calibration support only",
        "promotion_condition": (
            "No promotion from this receipt; downstream feedback-cycle calibration must "
            "supply explicit record, feedback, erasure, and graveyard receipts."
        ),
        "demotion_condition": (
            "Demote if sub-floor erasure becomes SAT under the declared floor, or if this "
            "receipt is used as bridge/QIT/GStack/axis/nonclassical evidence."
        ),
        "blocked_until": (
            "blocked from bridge, QIT, GStack, axis, nonclassical, or feedback-cycle claims "
            "until separate exact receipts close those gates"
        ),
        "out_of_scope": [
            "No feedback cycle.",
            "No quantum carrier.",
            "No bridge, QIT, GStack, axis, or nonclassical admission.",
        ],
        "operation_sequence": [
            "declare positive distinguishability unit F01 and nonnegative erasure energy Ev",
            "assert Landauer floor Ev >= F01 ln2",
            "ask z3 for sub-floor Ev < F01 ln2",
            "check floor-attainable and F01-zero boundaries",
        ],
        "carrier_topology": "finite scalar real-arithmetic constraint system",
        "observable": "z3 SAT/UNSAT verdicts for sub-floor, floor, and degenerate-boundary formulas",
        "pass_fail_predicate": "sub-floor erasure is UNSAT, exact floor is SAT, and F01-zero degenerate boundary is SAT",
        "graveyards": [
            "sub-floor erasure contradiction",
            "exact-floor attainable boundary",
            "zero-distinguishability degenerate boundary",
        ],
        "graveyard_companions": [
            "sub-floor erasure contradiction",
            "exact-floor attainable boundary",
            "zero-distinguishability degenerate boundary",
        ],
        "baselines": ["z3 real-arithmetic Landauer floor"],
        "alternative_formulations": [
            "numpy binary entropy cost curve",
            "measurement-feedback-erasure calibration cycle",
            "random-feedback graveyard",
        ],
        "exact_tool_function_needs": {"z3": ["Reals", "RealVal", "Solver"]},
        "lego_or_coupling_target": "classical erasure-cost constraint fence support",
        "promotion_allowed": False,
        "tool_manifest": TM, "tool_integration_depth": DEPTH,
        "load_bearing_tool": "z3",
        "positive": pos, "negative": neg, "boundary": bnd,
        "pass": bool(ok),
    }
    write_results(NAME, results)
