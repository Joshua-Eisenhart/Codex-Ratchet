#!/usr/bin/env python3
"""Classical baseline: Blackwell garbling / channel sufficiency.

Channel A is 'more informative' than B iff exists stochastic M with B = M A.
Classical Blackwell theorem operates on stochastic matrices only.
"""
import json, os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "stochastic matrix / lstsq garbling check"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
    "scipy": {"tried": False, "used": False, "reason": "not required; used only if available"},
    "z3": {"tried": False, "used": False, "reason": "no proof claim"},
}
try:
    from scipy.optimize import nnls  # noqa: F401
    TOOL_MANIFEST["scipy"]["tried"] = True
    TOOL_MANIFEST["scipy"]["used"] = True
    TOOL_MANIFEST["scipy"]["reason"] = "nnls to solve garbling M >=0 columnwise"
    HAS_SCIPY = True
except Exception:
    HAS_SCIPY = False
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive", "scipy": "supportive" if HAS_SCIPY else None}

def garbles(A, B, atol=1e-6):
    """Find stochastic M with B ~= M A (A: K_A x X, B: K_B x X)."""
    A = np.asarray(A, float); B = np.asarray(B, float)
    KB, X = B.shape; KA = A.shape[0]
    # For each row of M (of length KA), solve NNLS: A^T m = B_row^T, m>=0, then renorm to sum=1.
    M = np.zeros((KB, KA))
    for k in range(KB):
        if HAS_SCIPY:
            m, _ = nnls(A.T, B[k])
        else:
            # lstsq fallback, clip negatives
            m, *_ = np.linalg.lstsq(A.T, B[k], rcond=None)
            m = np.clip(m, 0, None)
        M[k] = m
    # row sums of M should be 1 (since columns of A and B are pmfs over outcomes -> each x has A[:,x] sums to 1 and B[:,x] sums to 1)
    residual = np.linalg.norm(M @ A - B)
    row_sums = M.sum(axis=1)
    return residual < atol and np.allclose(row_sums, 1.0, atol=1e-4), residual, M

def run_positive_tests():
    rng = np.random.default_rng(0)
    A = rng.dirichlet(np.ones(3), size=4).T  # 3 outcomes x 4 states
    # Construct B = M0 A with random stochastic M0 (2 outcomes).
    M0 = rng.dirichlet(np.ones(3), size=2)
    B = M0 @ A
    ok, res, _ = garbles(A, B)
    # Identity: A garbles itself
    ok2, _, _ = garbles(A, A)
    return {
        "constructed_garbling_detected": ok,
        "self_garbling_trivial": ok2,
    }

def run_negative_tests():
    rng = np.random.default_rng(1)
    # make B strictly more informative than A: B = identity-like distinguishes more states.
    # Use A = uniform over states (no info), B distinguishes.
    X = 3
    A = np.ones((2, X)) / 2  # no information
    B = np.eye(X)  # perfect info
    ok, res, _ = garbles(A, B)  # cannot garble uninformative into informative
    return {
        "uninformative_cannot_yield_informative": not ok,
    }

def run_boundary_tests():
    X = 3
    I = np.eye(X)
    # permutation of I still sufficient: I garbles permutation and vice versa
    P = I[:, [1, 2, 0]]
    ok1, _, _ = garbles(I, P)
    ok2, _, _ = garbles(P, I)
    return {
        "permutation_equivalent_both_directions": ok1 and ok2,
    }

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "blackwell_comparison_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump({
            "name": "blackwell_comparison_classical",
            "classification": "classical_baseline",
            "tool_manifest": TOOL_MANIFEST,
            "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
            "positive": pos, "negative": neg, "boundary": bnd,
            "all_pass": all_pass, "summary": {"all_pass": all_pass},
            "divergence_log": [
                "Blackwell ordering on stochastic matrices is total up to sufficiency; quantum channel ordering (degradability) is strictly partial and basis-sensitive",
                "no quantum sufficiency / Petz recovery map; classical sufficiency has no coherent-frame analog",
                "misses entanglement-assisted information gaps where quantum B can exceed classical bound with side resource",
                "ignores incompatible-measurement hierarchy where no single classical M unifies two measurement channels",
            ],
        }, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
