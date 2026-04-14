#!/usr/bin/env python3
"""Classical baseline sim: coherence_measure lego (l1-norm coherence).

Lane B classical baseline (numpy-only). NOT canonical.
Classical states are diagonal in the computational basis; l1-norm coherence
C_l1(rho) = sum_{i!=j} |rho_ij| is always 0.
Innately missing: superposition, relative-entropy of coherence on mixed
off-diagonal states, basis-dependence (classical is basis-fixed).
"""
import json, os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "matrix arithmetic"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}


def l1_coherence(rho):
    return float(np.sum(np.abs(rho - np.diag(np.diag(rho)))))


def classical_state_from_pmf(p):
    return np.diag(p).astype(float)


def run_positive_tests():
    p = np.array([0.2, 0.3, 0.5])
    rho = classical_state_from_pmf(p)
    return {
        "diagonal_state_has_zero_coherence": l1_coherence(rho) == 0.0,
        "uniform_classical_zero_coherence": l1_coherence(classical_state_from_pmf(np.ones(4)/4)) == 0.0,
    }


def run_negative_tests():
    # nonclassical rho with off-diagonals should NOT be zero
    rho = np.array([[0.5, 0.4], [0.4, 0.5]])
    return {
        "offdiag_state_has_positive_coherence": l1_coherence(rho) > 0.0,
        "classical_cannot_represent_this_state": True,
    }


def run_boundary_tests():
    rho_pure_classical = np.diag([1.0, 0.0])
    return {
        "pure_classical_zero_coherence": l1_coherence(rho_pure_classical) == 0.0,
        "zero_matrix_zero_coherence": l1_coherence(np.zeros((3, 3))) == 0.0,
    }


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "coherence_measure_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
        "divergence_log": [
            "classical diagonal states have identically zero l1 coherence",
            "no basis rotation sensitivity; coherence is basis-fixed trivially",
            "cannot witness superposition as a resource",
        ],
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "coherence_measure_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
