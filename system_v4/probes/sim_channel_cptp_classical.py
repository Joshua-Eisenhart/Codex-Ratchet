#!/usr/bin/env python3
"""Classical baseline: CPTP channel = column-stochastic matrix.
CP reduces to entrywise nonneg; TP reduces to columns sum to 1.
"""
import json, os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "stochastic matrix checks"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
    "z3": {"tried": False, "used": False, "reason": "no proof claim"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}

def is_cptp_classical(T, atol=1e-10):
    T = np.asarray(T, float)
    cp = bool(np.all(T >= -atol))
    tp = bool(np.allclose(T.sum(axis=0), 1.0, atol=atol))
    return cp, tp

def run_positive_tests():
    rng = np.random.default_rng(0)
    T = rng.dirichlet(np.ones(4), size=4).T
    cp, tp = is_cptp_classical(T)
    I = np.eye(5)
    perm = np.eye(4)[:, [2,0,3,1]]
    return {
        "random_stochastic_cp": cp,
        "random_stochastic_tp": tp,
        "identity_cptp": all(is_cptp_classical(I)),
        "permutation_cptp": all(is_cptp_classical(perm)),
    }

def run_negative_tests():
    T = np.array([[0.5, 0.2],[0.6, 0.9]])  # cols sum != 1
    cp, tp = is_cptp_classical(T)
    T_neg = np.array([[1.2, 0.0],[-0.2, 1.0]])
    cp2, tp2 = is_cptp_classical(T_neg)
    return {
        "non_tp_detected": not tp,
        "non_cp_detected": not cp2,
    }

def run_boundary_tests():
    # composition of stochastic is stochastic
    rng = np.random.default_rng(1)
    A = rng.dirichlet(np.ones(3), size=3).T
    B = rng.dirichlet(np.ones(3), size=3).T
    C = A @ B
    return {
        "composition_preserves_cptp": all(is_cptp_classical(C)),
        "dephasing_trivial_in_diag_basis": all(is_cptp_classical(np.diag([1.0]*3))),
    }

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "channel_cptp_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump({
            "name": "channel_cptp_classical",
            "classification": "classical_baseline",
            "tool_manifest": TOOL_MANIFEST,
            "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
            "positive": pos, "negative": neg, "boundary": bnd,
            "all_pass": all_pass, "summary": {"all_pass": all_pass},
            "divergence_log": [
                "CP classically reduces to entrywise positivity; misses complete-positivity on entangled extensions (tensor with ancilla)",
                "no Choi-positivity witnessing for noncommuting channels",
                "unitary channels absent; only permutations are reversible classically",
                "cannot model non-Markovian / non-CP-divisible quantum dynamics",
            ],
        }, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
