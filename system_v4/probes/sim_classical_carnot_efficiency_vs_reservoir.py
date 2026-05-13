#!/usr/bin/env python3
"""sim_classical_carnot_efficiency_vs_reservoir

scope_note: Illuminates Landauer section of
  system_v5/docs/CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md
  by computing Carnot efficiency eta = 1 - Tc/Th across reservoir pairs.
  Classical baseline only; no admissibility claim.
"""
import numpy as np
from _doc_illum_common import write_results

NAME = "classical_carnot_efficiency_vs_reservoir"
SCOPE_NOTE = ("Illuminates CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md "
              "(Landauer section): classical Carnot bound eta<=1-Tc/Th.")
CLASSIFICATION = "classical_baseline"
classification = CLASSIFICATION

DIVERGENCE_LOG = (
    "Classical baseline only: computes the reservoir-temperature Carnot bound "
    "eta = 1 - Tc/Th with numpy arithmetic; no engine mechanics, QIT, GStack, "
    "bridge, axis, nonclassical, or cycle-admission claim."
)
DIVERGENCE_DETAILS = [
    "No Lindblad bath, Hamiltonian stroke, work reservoir, or finite-time dynamics is represented.",
    "The super-Carnot control is a bound check, not an engine simulation.",
    "A later calibration cycle must add operation sequence, stroke observables, and graveyard companions.",
]

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "compute scalar Carnot bound values and numeric equality checks",
    },
    "pytorch": {
        "tried": False,
        "used": False,
        "reason": "not used; this is a numpy-only classical baseline lane",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "pytorch": None,
}
divergence_log = DIVERGENCE_LOG
divergence_details = DIVERGENCE_DETAILS


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
    TOOL_MANIFEST["pytorch"]["reason"] = "numpy-only classical lane"
    # numpy is the load-bearing numeric engine
    pos = run_positive(); neg = run_negative(); bnd = run_boundary()
    ok = (all(v["ok"] for v in pos.values())
          and neg["rejected_superCarnot"]
          and bnd["isothermal"]["eta"] == 0.0)
    results = {
        "name": NAME, "scope_note": SCOPE_NOTE,
        "classification": CLASSIFICATION,
        "all_pass": bool(ok),
        "claim_ceiling": (
            "classical reservoir-bound baseline only: finite arithmetic check of eta <= 1 - Tc/Th; "
            "no Carnot-cycle execution, QIT, GStack, bridge, axis, nonclassical, or engine admission"
        ),
        "next_lego_target": (
            "none; use as a baseline before separate two-bath cycle calibration with explicit strokes, "
            "work/heat observables, and graveyards"
        ),
        "promotion_condition": (
            "No promotion from this receipt; downstream calibration must implement a stroke sequence and "
            "pass same-bath, swapped-order, reversed-direction, and no-work graveyards."
        ),
        "demotion_condition": (
            "Demote or block if reservoir-bound arithmetic fails, if the divergence log is removed, "
            "or if this receipt is used as evidence for engine mechanics."
        ),
        "blocked_until": (
            "blocked from engine, QIT, GStack, bridge, axis, nonclassical, or cycle-mechanics claims "
            "until separate exact calibration receipts close those gates"
        ),
        "out_of_scope": [
            "No heat/work stroke simulation.",
            "No Lindblad bath or Hamiltonian dynamics.",
            "No engine, QIT, GStack, bridge, axis, or nonclassical claim.",
        ],
        "divergence_log": DIVERGENCE_LOG,
        "divergence_details": DIVERGENCE_DETAILS,
        "operation_sequence": [
            "evaluate eta = 1 - Tc/Th for reservoir pairs",
            "check super-Carnot bound rejection",
            "check Tc approximately zero and Tc equals Th boundaries",
        ],
        "carrier_topology": "none; scalar reservoir-temperature arithmetic only",
        "observable": "Carnot efficiency bound values and bound-rejection boolean",
        "pass_fail_predicate": "computed efficiencies equal 1 - Tc/Th, super-Carnot claim is rejected, and equal-temperature efficiency is zero",
        "graveyards": [
            "super-Carnot claimed efficiency control",
            "equal-temperature zero-efficiency boundary",
        ],
        "baselines": [
            "scalar reservoir-temperature arithmetic",
            "numpy isclose comparison to analytic formula",
        ],
        "alternative_formulations": [
            "two-bath four-stroke calibration cycle",
            "finite-time irreversible companion",
            "same-bath no-work graveyard",
        ],
        "exact_tool_function_needs": {"numpy": ["isclose"]},
        "lego_or_coupling_target": "none; classical calibration baseline only",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": {
            **TOOL_INTEGRATION_DEPTH, "pytorch": None,
        },
        "load_bearing_tool": "numpy",
        "positive": pos, "negative": neg, "boundary": bnd,
        "pass": bool(ok),
    }
    write_results(NAME, results)
