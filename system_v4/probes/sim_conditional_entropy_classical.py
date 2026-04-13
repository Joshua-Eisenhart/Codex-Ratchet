#!/usr/bin/env python3
"""Classical baseline sim: conditional_entropy lego.

Lane B classical baseline (numpy-only). NOT canonical.
Captures: H(X|Y) = H(X,Y) - H(Y). Always >= 0 classically.
Innately missing: quantum S(A|B) = S(AB)-S(B) can be NEGATIVE for
entangled joint states (coherent information). Classical baseline cannot
encode this sign and therefore cannot separate Axis-0 candidates where
signed conditional information is load-bearing.
"""
import json, os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "log/sum"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}

def H(p):
    p = np.asarray(p, dtype=float).ravel()
    p = p[p > 0]
    return float(-np.sum(p * np.log2(p)))

def H_cond(pxy):
    pxy = np.asarray(pxy, dtype=float)
    return H(pxy) - H(pxy.sum(axis=0))

def run_positive_tests():
    # independent: H(X|Y) = H(X)
    px = np.array([0.5, 0.5]); py = np.array([0.3, 0.7])
    ind = np.outer(px, py)
    return {
        "independent_equals_HX": abs(H_cond(ind) - H(px)) < 1e-10,
        "deterministic_Y_given_X_cond_X_zero": abs(H_cond(np.array([[0.5,0],[0,0.5]])) - 0.0) < 1e-10,
    }

def run_negative_tests():
    # classical conditional entropy nonneg on all random joints
    oks = []
    for _ in range(40):
        p = np.random.dirichlet(np.ones(9)).reshape(3,3)
        oks.append(H_cond(p) >= -1e-10)
    return {"always_nonneg_classical": all(oks)}

def run_boundary_tests():
    # chain rule: H(X,Y) = H(Y) + H(X|Y)
    pxy = np.array([[0.2, 0.3],[0.4, 0.1]])
    py = pxy.sum(axis=0)
    return {
        "chain_rule": abs(H(pxy) - (H(py) + H_cond(pxy))) < 1e-10,
        "bounded_by_HX": H_cond(pxy) <= H(pxy.sum(axis=1)) + 1e-10,
    }

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "conditional_entropy_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
        "divergence_log": [
            "classical H(X|Y) >= 0 always; quantum S(A|B) can be negative under entanglement",
            "no sign structure, so cannot carry coherent-information Axis-0 candidate",
            "no noncommuting conditioning",
        ],
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "conditional_entropy_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
