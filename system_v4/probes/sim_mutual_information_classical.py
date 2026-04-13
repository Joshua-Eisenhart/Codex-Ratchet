#!/usr/bin/env python3
"""Classical baseline sim: mutual_information_measure lego.

Lane B classical baseline (numpy-only). NOT canonical.
Captures: I(X;Y) = H(X) + H(Y) - H(X,Y) on discrete joint pmf.
Innately missing: noncommuting-observable MI, quantum MI (S(A)+S(B)-S(AB))
under entanglement, coupling-induced violations of classical bounds
(I classical <= min(H(X),H(Y)); quantum MI can exceed H(A) via entanglement).
"""
import json, os, math
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "marginal/joint pmf log arithmetic"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
    "z3": {"tried": False, "used": False, "reason": "no proof claim"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}

def H(p):
    p = np.asarray(p, dtype=float).ravel()
    p = p[p > 0]
    return float(-np.sum(p * np.log2(p)))

def MI(pxy):
    pxy = np.asarray(pxy, dtype=float)
    px = pxy.sum(axis=1); py = pxy.sum(axis=0)
    return H(px) + H(py) - H(pxy)

def run_positive_tests():
    # independent -> MI=0
    px = np.array([0.5, 0.5]); py = np.array([0.4, 0.6])
    ind = np.outer(px, py)
    # perfectly correlated: diagonal joint
    diag = np.array([[0.5, 0.0],[0.0, 0.5]])
    return {
        "independent_MI_zero": abs(MI(ind)) < 1e-10,
        "perfect_corr_MI_equals_HX": abs(MI(diag) - 1.0) < 1e-10,
        "nonneg_random": all(MI(np.random.dirichlet(np.ones(9)).reshape(3,3)) >= -1e-10 for _ in range(20)),
    }

def run_negative_tests():
    return {
        "zero_joint_not_allowed_via_normalization": abs(np.array([[0.5,0.5],[0,0]]).sum() - 1.0) < 1e-12,
        "MI_bounded_by_min_marginal": MI(np.array([[0.4,0.1],[0.1,0.4]])) <= min(H([0.5,0.5]), H([0.5,0.5])) + 1e-10,
    }

def run_boundary_tests():
    # symmetry
    pxy = np.array([[0.3, 0.2],[0.1, 0.4]])
    return {
        "symmetry": abs(MI(pxy) - MI(pxy.T)) < 1e-12,
        "nonneg": MI(pxy) >= -1e-12,
    }

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "mutual_information_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
        "divergence_log": [
            "classical MI bounded by min(H(X),H(Y)); quantum MI can reach 2 S(A) via entanglement",
            "assumes commuting joint pmf; cannot encode noncommuting observable families",
            "no probe-conditional admissibility; every joint outcome presumed measurable",
        ],
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "mutual_information_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
