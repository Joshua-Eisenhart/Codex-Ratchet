#!/usr/bin/env python3
"""Classical baseline: principal_subspace projection."""
import json, os, numpy as np
from _classical_baseline_common import TOOL_MANIFEST, TOOL_INTEGRATION_DEPTH
classification = "classical_baseline"

NAME = "principal_subspace"

def top_k_projector(A, k):
    w, V = np.linalg.eigh((A + A.T) / 2)
    idx = np.argsort(-w)[:k]
    U = V[:, idx]
    return U @ U.T, U

def run_positive_tests():
    r = {}
    rng = np.random.default_rng(0)
    U, _ = np.linalg.qr(rng.standard_normal((6, 6)))
    d = np.array([5.0, 4.0, 3.0, 0.1, 0.05, 0.01])
    A = U @ np.diag(d) @ U.T
    P, _ = top_k_projector(A, 3)
    # idempotent
    r["idempotent"] = {"err": float(np.max(np.abs(P @ P - P))), "pass": np.allclose(P @ P, P)}
    # symmetric
    r["symmetric"] = {"err": float(np.max(np.abs(P - P.T))), "pass": np.allclose(P, P.T)}
    # trace = rank = 3
    r["trace_is_rank"] = {"trace": float(np.trace(P)), "pass": abs(np.trace(P) - 3) < 1e-8}
    # captures top-3 eigenvectors: P A P ~ sum top 3
    captured = np.trace(P @ A)
    r["captures_top_variance"] = {"captured": float(captured), "expected": 12.0, "pass": abs(captured - 12.0) < 1e-8}
    return r

def run_negative_tests():
    r = {}
    rng = np.random.default_rng(1)
    U, _ = np.linalg.qr(rng.standard_normal((5, 5)))
    d = np.array([5.0, 4.0, 3.0, 2.0, 1.0])
    A = U @ np.diag(d) @ U.T
    # bottom-k projector should NOT be idempotent and equal top-k
    w, V = np.linalg.eigh(A)
    U_bot = V[:, :2]  # smallest two
    P_bot = U_bot @ U_bot.T
    captured_bot = np.trace(P_bot @ A)
    r["bottom_k_captures_less"] = {"captured": float(captured_bot), "pass": captured_bot < 4.0}
    # random non-orthogonal matrix is not a valid projector
    M = rng.standard_normal((4, 4))
    r["random_not_idempotent"] = {"err": float(np.max(np.abs(M @ M - M))), "pass": float(np.max(np.abs(M @ M - M))) > 0.1}
    return r

def run_boundary_tests():
    r = {}
    A = np.diag([3.0, 3.0, 1.0])  # degenerate top
    P, _ = top_k_projector(A, 2)
    r["degenerate_top_trace2"] = {"trace": float(np.trace(P)), "pass": abs(np.trace(P) - 2) < 1e-8}
    # k=0
    P0, _ = top_k_projector(A, 0)
    r["k0_zero_projector"] = {"norm": float(np.linalg.norm(P0)), "pass": float(np.linalg.norm(P0)) < 1e-10}
    # k=n full projector = identity
    Pn, _ = top_k_projector(A, 3)
    r["kn_identity"] = {"err": float(np.max(np.abs(Pn - np.eye(3)))), "pass": np.allclose(Pn, np.eye(3))}
    return r

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(v.get("pass", False) for v in list(pos.values()) + list(neg.values()) + list(bnd.values()))
    results = {"name": NAME, "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "all_pass": all_pass,
        "note": "classical captures: idempotent symmetric projector onto top-k eigenspace. Innately fails: non-orthogonal projections, subspaces of non-Hermitian operators, quantum subspace gauge freedom."}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results"); os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_classical_results.json")
    with open(out_path, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"{NAME} all_pass={all_pass} -> {out_path}")
