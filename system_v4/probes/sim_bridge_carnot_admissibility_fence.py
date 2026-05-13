#!/usr/bin/env python3
"""sim_bridge_carnot_admissibility_fence

scope_note: Reframes classical Carnot as a constraint-admissibility fence.
  Illuminates system_v5/docs/CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md
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
classification = "tool_lego_fit_probe"
divergence_log = (
    "z3 finite-arithmetic Carnot-bound fence only: rejects super-Carnot "
    "efficiency under declared heat/work and second-law constraints; no bridge, "
    "QIT, GStack, axis, nonclassical, or runtime-engine admission."
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


def run_positive_tests():
    return run_positive()


def run_negative_tests():
    return run_negative()


def run_boundary_tests():
    return run_boundary()


if __name__ == "__main__":
    TM["z3"] = {"tried": True, "used": True, "reason": "Proves UNSAT for super-Carnot; load-bearing admissibility fence"}
    DEPTH["z3"] = "load_bearing"
    DEPTH["pytorch"] = None
    pos = run_positive(); neg = run_negative(); bnd = run_boundary()
    ok = (pos["unsat_as_expected"] and neg["sat_as_expected"]
          and bnd["unsat_as_expected"])
    results = {
        "name": NAME, "scope_note": SCOPE_NOTE,
        "classification": classification,
        "all_pass": bool(ok),
        "divergence_log": divergence_log,
        "claim_ceiling": (
            "local z3 Carnot-bound constraint fence only: super-Carnot efficiency is UNSAT "
            "under declared classical heat/work and second-law constraints; no bridge, QIT, "
            "GStack, axis, nonclassical, or runtime-engine admission"
        ),
        "next_lego_target": "classical two-bath cycle calibration support only",
        "promotion_condition": (
            "No promotion from this receipt; downstream cycle calibration must supply explicit "
            "strokes, heat/work observables, and same-bath/reversed/no-work graveyards."
        ),
        "demotion_condition": (
            "Demote if super-Carnot becomes SAT under the declared constraints, or if this "
            "receipt is used as bridge/QIT/GStack/axis/nonclassical evidence."
        ),
        "blocked_until": (
            "blocked from bridge, QIT, GStack, axis, nonclassical, runtime-engine, or cycle "
            "claims until separate exact receipts close those gates"
        ),
        "out_of_scope": [
            "No cycle dynamics.",
            "No quantum carrier.",
            "No bridge, QIT, GStack, axis, runtime-engine, or nonclassical admission.",
        ],
        "operation_sequence": [
            "declare positive hot/cold temperatures with Tc < Th",
            "declare heat/work variables and W = Qh - Qc",
            "assert Clausius second-law inequality",
            "ask z3 for eta > 1 - Tc/Th",
            "check attainable-bound and equal-temperature boundaries",
        ],
        "carrier_topology": "finite scalar real-arithmetic constraint system",
        "observable": "z3 SAT/UNSAT verdicts for super-Carnot, bound-attainment, and isothermal-positive-work formulas",
        "pass_fail_predicate": "super-Carnot and equal-temperature positive work are UNSAT while exact bound attainment is SAT",
        "graveyards": [
            "super-Carnot efficiency contradiction",
            "exact-bound attainable boundary",
            "equal-temperature positive-work contradiction",
        ],
        "graveyard_companions": [
            "super-Carnot efficiency contradiction",
            "exact-bound attainable boundary",
            "equal-temperature positive-work contradiction",
        ],
        "baselines": ["z3 real-arithmetic Carnot bound"],
        "alternative_formulations": [
            "numpy reservoir-bound arithmetic",
            "two-bath stroke calibration cycle",
            "same-bath no-work companion",
        ],
        "exact_tool_function_needs": {"z3": ["Reals", "Real", "Solver"]},
        "lego_or_coupling_target": "classical two-bath cycle constraint fence support",
        "promotion_allowed": False,
        "tool_manifest": TM, "tool_integration_depth": DEPTH,
        "load_bearing_tool": "z3",
        "positive": pos, "negative": neg, "boundary": bnd,
        "pass": bool(ok),
    }
    write_results(NAME, results)
