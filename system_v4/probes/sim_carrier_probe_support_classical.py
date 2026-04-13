#!/usr/bin/env python3
"""Classical baseline sim: carrier_probe_support lego.

Lane B classical baseline (numpy-only). NOT canonical.
Captures: the support of a probe POVM element E on a carrier state rho is
nonzero iff tr(E rho) > 0; support-compatibility means every rho in the
carrier has at least one outcome with positive probability.
Innately missing: nonclassical carrier-geometry, constraint-admissibility of
the support set. Classical support analysis ignores whether the carrier shell
can host the probe at all — useful failure data.
"""
import json, os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "trace/support arithmetic"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}

def outcome_prob(E, rho):
    return float(np.real(np.trace(E @ rho)))

def has_support(povm, rho, tol=1e-9):
    return any(outcome_prob(E, rho) > tol for E in povm)

def run_positive_tests():
    rho = np.diag([0.6, 0.4])
    povm = [np.diag([1, 0]).astype(float), np.diag([0, 1]).astype(float)]
    return {
        "both_outcomes_positive": all(outcome_prob(E, rho) > 0 for E in povm),
        "support_exists": has_support(povm, rho),
        "probs_sum_to_one": abs(sum(outcome_prob(E, rho) for E in povm) - 1.0) < 1e-9,
    }

def run_negative_tests():
    # carrier fully in |0> but probe only measures |1>
    rho = np.diag([1.0, 0.0])
    povm_bad = [np.diag([0, 1]).astype(float)]  # not complete, degenerate
    return {
        "no_support_detected": not has_support(povm_bad, rho),
    }

def run_boundary_tests():
    # maximally mixed state has support under any PSD probe element with trace>0
    rho = np.eye(2) / 2
    E_tiny = np.diag([1e-10, 1e-10])
    return {
        "mixed_has_support_under_tiny": has_support([E_tiny], rho, tol=1e-15),
        "mixed_no_support_under_zero": not has_support([np.zeros((2, 2))], rho),
    }

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "carrier_probe_support_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "summary": {"all_pass": all_pass},
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "carrier_probe_support_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
