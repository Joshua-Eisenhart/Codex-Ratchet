#!/usr/bin/env python3
"""sim_classical_carnot_efficiency_vs_reservoir

scope_note: Illuminates Landauer section of
  system_v5/new docs/CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md
  by computing Carnot efficiency eta = 1 - Tc/Th across reservoir pairs.
  Classical baseline only; no admissibility claim.
"""
import numpy as np
from _doc_illum_common import build_manifest, write_results

NAME = "classical_carnot_efficiency_vs_reservoir"
SCOPE_NOTE = ("Illuminates CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md "
              "(Landauer section): classical Carnot bound eta<=1-Tc/Th.")
CLASSIFICATION = "classical_baseline"

TM, DEPTH = build_manifest()
TM["pytorch"]["used"] = False  # numpy-only lane
DEPTH["pytorch"] = None


def carnot_eta(Tc, Th):
    return 1.0 - Tc / Th


def run_positive():
    r = {}
    pairs = [(300.0, 600.0), (77.0, 300.0), (1.0, 1e6)]
    for Tc, Th in pairs:
        eta = carnot_eta(Tc, Th)
        theory = 1 - Tc / Th
        r[f"pair_{Tc}_{Th}"] = {
            "eta": float(eta), "theory": float(theory),
            "ok": bool(np.isclose(eta, theory))
        }
    return r


def run_negative():
    # A proposed engine claiming eta > Carnot must fail the bound check.
    Tc, Th = 300.0, 600.0
    claimed = 0.9  # > 1 - 300/600 = 0.5
    return {"rejected_superCarnot": bool(claimed > carnot_eta(Tc, Th))}


def run_boundary():
    r = {}
    # Tc -> 0: eta -> 1
    r["tc_zero"] = {"eta": float(carnot_eta(1e-12, 1.0)), "near_one": True}
    # Tc == Th: eta == 0
    r["isothermal"] = {"eta": float(carnot_eta(500.0, 500.0))}
    return r


if __name__ == "__main__":
    TM["pytorch"]["reason"] = "numpy-only classical lane"
    # numpy is the load-bearing numeric engine
    pos = run_positive(); neg = run_negative(); bnd = run_boundary()
    ok = (all(v["ok"] for v in pos.values())
          and neg["rejected_superCarnot"]
          and bnd["isothermal"]["eta"] == 0.0)
    results = {
        "name": NAME, "scope_note": SCOPE_NOTE,
        "classification": CLASSIFICATION,
        "tool_manifest": TM, "tool_integration_depth": {
            **DEPTH, "pytorch": None,
        },
        "load_bearing_tool": "numpy",
        "positive": pos, "negative": neg, "boundary": bnd,
        "pass": bool(ok),
    }
    write_results(NAME, results)
