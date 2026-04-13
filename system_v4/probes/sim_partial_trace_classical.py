#!/usr/bin/env python3
"""Classical baseline sim: partial_trace_operator lego.

Lane B classical baseline (numpy-only). NOT canonical.
Captures: classical 'partial trace' as marginalization of a joint pmf:
  p_A(a) = sum_b p_AB(a,b).
Innately missing: quantum partial trace on density matrix (off-diagonal
coherences are averaged in; reduced state can be mixed even when joint is
pure — the entanglement signature). Classical marginal cannot represent
the purity-entropy inversion.
"""
import json, os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "sum over axis"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}

def marginal_A(pab): return np.asarray(pab).sum(axis=1)
def marginal_B(pab): return np.asarray(pab).sum(axis=0)

def run_positive_tests():
    pab = np.array([[0.1, 0.2],[0.3, 0.4]])
    return {
        "marginal_A_sum_1": abs(marginal_A(pab).sum() - 1.0) < 1e-12,
        "marginal_B_sum_1": abs(marginal_B(pab).sum() - 1.0) < 1e-12,
        "product_factorizes": np.allclose(np.outer(marginal_A(np.outer([0.5,0.5],[0.3,0.7])),
                                                     marginal_B(np.outer([0.5,0.5],[0.3,0.7]))),
                                           np.outer([0.5,0.5],[0.3,0.7]), atol=1e-10),
    }

def run_negative_tests():
    # Pure joint in classical sense (delta) has pure marginals (no entanglement signature)
    delta = np.zeros((2,2)); delta[0,0] = 1.0
    mA = marginal_A(delta)
    return {
        "classical_pure_joint_yields_pure_marginal": abs(np.max(mA) - 1.0) < 1e-12,
    }

def run_boundary_tests():
    # linearity
    p1 = np.array([[0.3,0.2],[0.1,0.4]]); p2 = np.array([[0.1,0.4],[0.4,0.1]])
    lam = 0.3
    mix = lam*p1 + (1-lam)*p2
    return {
        "linearity": np.allclose(marginal_A(mix), lam*marginal_A(p1) + (1-lam)*marginal_A(p2), atol=1e-12),
    }

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "partial_trace_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
        "divergence_log": [
            "cannot express pure-joint -> mixed-marginal (entanglement signature)",
            "no off-diagonal coherence tracing; only diagonal marginalization",
            "blind to subsystem purity inversion used in entanglement entropy",
        ],
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "partial_trace_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
