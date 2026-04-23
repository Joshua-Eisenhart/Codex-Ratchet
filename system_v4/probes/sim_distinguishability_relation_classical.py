#!/usr/bin/env python3
"""Classical baseline sim: distinguishability_relation lego.

Lane B classical baseline (numpy-only). NOT canonical.
Captures: probe-relative distinguishability d(x,y)=0 iff p(k|x)=p(k|y) for all k,
and the equivalence-relation axioms (reflexive/symmetric/transitive) of
"indistinguishable under probe P".
Innately missing: nonclassical constraint-admissibility; POVM-level Helstrom
bounds; coupling-dependence. Failures where two classically equal dists come
from structurally distinct carriers are useful boundary data.
"""
import json, os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "probability arithmetic"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
    "z3": {"tried": False, "used": False, "reason": "classical baseline"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}

def indistinguishable(px, py, tol=1e-9):
    return bool(np.allclose(px, py, atol=tol))

def run_positive_tests():
    a = np.array([0.3, 0.7]); b = np.array([0.3, 0.7]); c = np.array([0.3, 0.7])
    return {
        "reflexive": indistinguishable(a, a),
        "symmetric": indistinguishable(a, b) == indistinguishable(b, a),
        "transitive": (indistinguishable(a, b) and indistinguishable(b, c)) == indistinguishable(a, c),
    }

def run_negative_tests():
    a = np.array([0.3, 0.7]); d = np.array([0.5, 0.5])
    return {
        "distinct_detected": not indistinguishable(a, d),
        "asymmetry_violation_absent": indistinguishable(a, d) == indistinguishable(d, a),
    }

def run_boundary_tests():
    a = np.array([0.5, 0.5]); b = np.array([0.5 + 1e-12, 0.5 - 1e-12])
    return {
        "within_tol_indistinguishable": indistinguishable(a, b),
        "just_outside_tol_distinguished": not indistinguishable(a, a + np.array([1e-6, -1e-6])),
    }

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "distinguishability_relation_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "summary": {"all_pass": all_pass},
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "distinguishability_relation_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
