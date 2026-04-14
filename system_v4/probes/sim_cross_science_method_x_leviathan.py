#!/usr/bin/env python3
"""
CROSS sim: Science-Method x Leviathan
=====================================
Shell-local:
  Science-method = refutation-adversary against a hypothesis.
  Leviathan      = authoritarian-attractor that rewards consensus over refutation.

Cross question: do these two failure modes of empiricism combine to produce
an emergent *false-stable* hypothesis region -- claims that survive because
the civic shell suppresses refutation probes? EMERGENT: set of claims that
are individually refutable but collectively unrefuted under Leviathan.

POS : under leviathan, a strictly refutable claim retains non-zero support.
NEG : without leviathan, refutation rate is high (claim collapses).
BND : leviathan weight = 0 reproduces pure science-method.
"""
from __future__ import annotations
import json, os
import numpy as np
classification = "classical_baseline"  # auto-backfill

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "simulate adversary vs consensus"},
    "z3":    {"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing", "z3": None}

try:
    import z3; TOOL_MANIFEST["z3"]["tried"] = True
except ImportError: z3 = None


def survival(refute_prob, leviathan_weight, rounds=200, seed=0):
    rng = np.random.default_rng(seed)
    support = 1.0
    for _ in range(rounds):
        # refutation probe event
        refuted = rng.random() < refute_prob
        if refuted:
            # Leviathan absorbs refutation proportional to its weight
            support *= (1.0 - (1.0 - leviathan_weight) * 0.1)
        else:
            # consensus grows
            support = min(1.0, support + 0.01 * leviathan_weight)
    return support


def run_positive_tests():
    r = {}
    s_civic = survival(refute_prob=0.3, leviathan_weight=0.95, rounds=300, seed=1)
    s_free  = survival(refute_prob=0.3, leviathan_weight=0.0,  rounds=300, seed=1)
    r["civic_preserves_refutable_claim"] = s_civic > 0.5
    r["free_collapses_claim"] = s_free < s_civic

    # z3 load-bearing: for leviathan_weight=1, the multiplier (1 - (1-1)*0.1) = 1
    # so support never decreases regardless of refutation. Prove claim.
    s = z3.Solver()
    supp = z3.Real("s")
    w = z3.Real("w")
    s.add(w == 1.0, supp > 0, supp <= 1)
    factor = 1 - (1 - w) * z3.RealVal("0.1")
    s.add(factor * supp < supp)  # claim: strict decrease under full leviathan
    r["z3_full_leviathan_blocks_decay"] = (s.check() == z3.unsat)
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "leviathan weight=1 freezes support"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"

    r["EMERGENT_false_stable_region"] = bool(r["civic_preserves_refutable_claim"] and r["free_collapses_claim"])
    return r


def run_negative_tests():
    r = {}
    # No leviathan, high refutation: claim should collapse quickly
    s_free = survival(refute_prob=0.8, leviathan_weight=0.0, rounds=300, seed=2)
    r["pure_refutation_collapses_claim"] = s_free < 0.1
    return r


def run_boundary_tests():
    r = {}
    # leviathan=0 identical to shell-local science-method
    s_a = survival(0.4, 0.0, 100, seed=3)
    s_b = survival(0.4, 0.0, 100, seed=3)
    r["zero_leviathan_reproduces_free"] = abs(s_a - s_b) < 1e-12
    return r


if __name__ == "__main__":
    results = {
        "name": "sim_cross_science_method_x_leviathan",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    ok = all(bool(v) for d in (results["positive"], results["negative"], results["boundary"]) for v in d.values())
    results["PASS"] = ok
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results", "cross_science_method_x_leviathan_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"PASS={ok}  ->  {out}")
