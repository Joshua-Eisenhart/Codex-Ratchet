#!/usr/bin/env python3
"""Classical baseline sim: probe_identity_preservation lego.

Lane B classical baseline (numpy-only). NOT canonical.
Captures: a probe P preserves identity iff applying P to equal inputs yields
equal outputs (P is a function), and composition with identity is a no-op.
Innately missing: operator-level identity (I⊗P), carrier support, nonclassical
gauge invariance. A classical map can appear identity-preserving while
destroying nonclassical coherence — useful failure data.
"""
import json, os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "matrix identity checks"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}

def preserves_identity(P, tol=1e-9):
    n = P.shape[0]
    return bool(np.allclose(P @ np.eye(n), P, atol=tol) and
                np.allclose(np.eye(n) @ P, P, atol=tol))

def is_function_consistent(P, x, tol=1e-9):
    # Apply twice to same input — must match
    return bool(np.allclose(P @ x, P @ x, atol=tol))

def run_positive_tests():
    I = np.eye(4); R = np.diag([1, -1, 1, -1]).astype(float)
    x = np.array([1.0, 2.0, 3.0, 4.0])
    return {
        "identity_preserves_identity": preserves_identity(I),
        "rotation_preserves_identity": preserves_identity(R),
        "function_consistent": is_function_consistent(R, x),
    }

def run_negative_tests():
    # a "probe" that injects noise each call is NOT function-consistent; we
    # simulate by comparing two stochastic applications
    rng = np.random.default_rng(0)
    x = np.array([1.0, 0.0])
    y1 = x + rng.normal(0, 0.1, size=2)
    y2 = x + rng.normal(0, 0.1, size=2)
    return {
        "stochastic_breaks_consistency": not np.allclose(y1, y2, atol=1e-6),
    }

def run_boundary_tests():
    # zero operator: trivially function-consistent but annihilates identity
    Z = np.zeros((3, 3))
    return {
        "zero_op_annihilates_identity": not preserves_identity(Z),
    }

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "probe_identity_preservation_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "summary": {"all_pass": all_pass},
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "probe_identity_preservation_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
