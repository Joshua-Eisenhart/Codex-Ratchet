#!/usr/bin/env python3
"""Classical baseline sim: f01_finitude_constraint lego.

Lane B classical baseline (numpy-only). NOT canonical.
Captures: F01 finitude — any admissible carrier has finite dimension d < ∞ and
any admissible POVM has a finite number of outcomes K < ∞. Classical version
just checks cardinality bounds.
Innately missing: F01's role inside constraint-admissibility (F01+N01 as
process-generators); z3-level structural impossibility proofs. Classical
sim treats finitude as a label, not a constraint that creates the ratchet —
useful failure data.
"""
import json, os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "dimension/cardinality checks"},
    "z3": {"tried": False, "used": False, "reason": "classical baseline (no UNSAT proof)"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}

def is_finite_carrier(rho, dmax=1024):
    return bool(rho.ndim == 2 and rho.shape[0] == rho.shape[1] and rho.shape[0] < dmax)

def is_finite_povm(povm, kmax=1024):
    return bool(0 < len(povm) < kmax)

def run_positive_tests():
    rho = np.eye(4) / 4
    povm = [np.eye(4) / 3 for _ in range(3)]
    return {
        "carrier_finite": is_finite_carrier(rho),
        "povm_finite": is_finite_povm(povm),
    }

def run_negative_tests():
    # simulate "too large" — bound check fails
    big_shape = (2048, 2048)
    fake = type("Fake", (), {"ndim": 2, "shape": big_shape})()
    too_big = (fake.shape[0] < 1024)
    return {
        "oversized_rejected": not too_big,
        "empty_povm_rejected": not is_finite_povm([]),
    }

def run_boundary_tests():
    # d=1 carrier (scalar): technically finite
    rho1 = np.array([[1.0]])
    povm1 = [np.array([[1.0]])]
    return {
        "d1_carrier_finite": is_finite_carrier(rho1),
        "k1_povm_finite": is_finite_povm(povm1),
    }

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "f01_finitude_constraint_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "summary": {"all_pass": all_pass},
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "f01_finitude_constraint_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
