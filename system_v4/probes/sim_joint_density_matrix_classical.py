#!/usr/bin/env python3
"""Classical baseline sim: joint_density_matrix lego.

Lane B classical baseline (numpy-only). NOT canonical.
Captures: joint pmf p_AB(a,b) on a product sample space — the classical
surrogate of a joint density matrix.
Innately missing: off-diagonal coherences, non-separable entangled joint
states, and the PPT / negativity witnesses that only exist on true density
matrices. Classical joints are ALWAYS separable mixtures of products.
"""
import json, os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "pmf arithmetic"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}

def valid_joint(pab, atol=1e-10):
    return np.all(pab >= -atol) and abs(pab.sum() - 1.0) < atol

def is_separable_classical(pab, rtol=1e-8):
    # classically any normalized nonneg joint is a mixture of product states
    # (delta_a x delta_b), trivially separable
    return valid_joint(pab) and np.all(pab >= -rtol)

def run_positive_tests():
    p = np.array([[0.1,0.2],[0.3,0.4]])
    prod = np.outer([0.5,0.5],[0.4,0.6])
    return {
        "valid_joint": valid_joint(p),
        "product_joint_valid": valid_joint(prod),
        "all_classical_joints_separable": is_separable_classical(p),
    }

def run_negative_tests():
    bad_neg = np.array([[-0.1, 0.6],[0.3, 0.2]])
    bad_norm = np.array([[0.3, 0.3],[0.3, 0.3]])
    return {
        "negative_rejected": not valid_joint(bad_neg),
        "unnormalized_rejected": not valid_joint(bad_norm),
    }

def run_boundary_tests():
    # boundary normalization
    p = np.array([[1.0, 0.0],[0.0, 0.0]])
    return {
        "corner_delta_valid": valid_joint(p),
        "uniform_valid": valid_joint(np.ones((3,3))/9),
    }

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "joint_density_matrix_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
        "divergence_log": [
            "no off-diagonal coherences; only diagonal joint pmf",
            "every classical joint is separable; cannot represent entangled joint states",
            "no PPT / negativity witness structure; partial-transpose map undefined",
        ],
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "joint_density_matrix_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
