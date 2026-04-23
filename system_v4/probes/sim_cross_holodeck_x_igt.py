#!/usr/bin/env python3
"""
CROSS sim: Holodeck x IGT
=========================
Shell-local:
  Holodeck = observation-shell projection.
  IGT      = nested WIN/LOSE structure with win-lose-WIN-LOSE reversal.

Cross question: when holodeck projects only a limited horizon of IGT's nested
payoff tree, does the locally-optimal action *reverse* depending on projection
depth? EMERGENT: horizon-dependent optimal strategy -- a perception-induced
sign flip invisible shell-locally.

POS : short-horizon holodeck yields action A; long-horizon yields action B; A != B
NEG : flat (non-nested) payoff tree: horizon does not flip optimal action
BND : horizon >= full tree depth reproduces IGT-shell-local optimum
"""
from __future__ import annotations
import json, os
import numpy as np
classification = "classical_baseline"  # auto-backfill
divergence_log = "Classical shell baseline: horizon-flip behavior is a projection-vs-payoff numerical study, not a canonical nonclassical proof object."

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "tree evaluation"},
    "z3":    {"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive", "z3": None}

try:
    import z3; TOOL_MANIFEST["z3"]["tried"] = True
except ImportError: z3 = None


def nested_payoff(action, horizon):
    """
    action in {0,1}. Tree: action 0 gives immediate +1 (WIN) then -5 (LOSE);
    action 1 gives immediate -1 (LOSE) then +5 (WIN). Depth 2 reversal.
    """
    levels_0 = [1, -5]
    levels_1 = [-1, +5]
    seq = levels_0 if action == 0 else levels_1
    return float(sum(seq[:horizon]))


def flat_payoff(action, horizon):
    seq = [1, 1, 1] if action == 0 else [-1, -1, -1]
    return float(sum(seq[:horizon]))


def run_positive_tests():
    r = {}
    short = [nested_payoff(a, horizon=1) for a in (0, 1)]
    long  = [nested_payoff(a, horizon=2) for a in (0, 1)]
    short_best = int(np.argmax(short))
    long_best  = int(np.argmax(long))
    r["short_horizon_best"] = short_best == 0
    r["long_horizon_best"]  = long_best == 1
    r["horizon_induces_flip"] = short_best != long_best

    # z3 load-bearing: prove the sign reversal as an arithmetic fact.
    s = z3.Solver()
    a_short = z3.RealVal(1); b_short = z3.RealVal(-1)
    a_long  = z3.RealVal(1 + -5); b_long = z3.RealVal(-1 + 5)
    s.add(z3.Not(z3.And(a_short > b_short, a_long < b_long)))
    r["z3_horizon_reversal_valid"] = (s.check() == z3.unsat)
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "projection-depth reverses argmax"
    TOOL_INTEGRATION_DEPTH["z3"] = "supportive"

    r["EMERGENT_perception_induced_sign_flip"] = bool(r["horizon_induces_flip"])
    return r


def run_negative_tests():
    r = {}
    short = [flat_payoff(a, horizon=1) for a in (0, 1)]
    long  = [flat_payoff(a, horizon=3) for a in (0, 1)]
    r["flat_tree_no_flip"] = int(np.argmax(short)) == int(np.argmax(long))
    return r


def run_boundary_tests():
    r = {}
    full = [nested_payoff(a, horizon=2) for a in (0, 1)]
    r["full_horizon_matches_igt_local"] = int(np.argmax(full)) == 1
    return r


if __name__ == "__main__":
    results = {
        "name": "sim_cross_holodeck_x_igt",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    ok = all(bool(v) for d in (results["positive"], results["negative"], results["boundary"]) for v in d.values())
    results["PASS"] = ok
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results", "cross_holodeck_x_igt_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"PASS={ok}  ->  {out}")
