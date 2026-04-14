#!/usr/bin/env python3
"""Classical triangle counting + local/global clustering coefficient."""
import json, os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True,
                "reason": "cross-check triangle count via torch.matrix_power(A,3).diagonal()/2"},
}
TOOL_INTEGRATION_DEPTH = {"pytorch": "supportive"}

try:
    import torch
except ImportError:
    TOOL_MANIFEST["pytorch"] = {"tried": False, "used": False, "reason": "not installed"}
    TOOL_INTEGRATION_DEPTH["pytorch"] = None

divergence_log = []


def triangles(A):
    A = A.astype(int)
    A3 = np.linalg.matrix_power(A, 3)
    return int(np.trace(A3) // 6)


def local_clustering(A):
    n = A.shape[0]
    A = A.astype(int)
    c = np.zeros(n)
    deg = A.sum(axis=1)
    A2 = A @ A
    for i in range(n):
        if deg[i] < 2:
            c[i] = 0.0
        else:
            tri_i = (A @ A @ A)[i, i] / 2
            c[i] = 2 * tri_i / (deg[i] * (deg[i] - 1))
    return c


def run_positive_tests():
    r = {}
    # K4 has C(4,3)=4 triangles
    A = np.ones((4, 4)) - np.eye(4)
    t = triangles(A)
    r["K4_4_triangles"] = {"count": t, "pass": t == 4}
    c = local_clustering(A)
    r["K4_clustering_1"] = {"c": c.tolist(), "pass": bool(np.allclose(c, 1.0))}
    # cycle C5 has 0 triangles
    A = np.zeros((5, 5))
    for i in range(5):
        A[i, (i+1) % 5] = A[(i+1) % 5, i] = 1
    t = triangles(A)
    r["C5_0_triangles"] = {"count": t, "pass": t == 0}
    # torch cross-check
    if TOOL_INTEGRATION_DEPTH["pytorch"] == "supportive":
        At = torch.tensor(A)
        tri_t = int(torch.linalg.matrix_power(At, 3).diagonal().sum().item() // 6)
        r["torch_cycle_agrees"] = {"torch": tri_t, "np": t, "pass": tri_t == t}
    return r


def run_negative_tests():
    r = {}
    # tree (path) has no triangles (negation of "graphs have triangles")
    A = np.zeros((4, 4))
    for i in range(3):
        A[i, i+1] = A[i+1, i] = 1
    t = triangles(A)
    r["path_has_triangle_fails"] = {"count": t, "pass": t == 0}
    # disconnected 2K2: no triangles
    A = np.array([[0,1,0,0],[1,0,0,0],[0,0,0,1],[0,0,1,0]], float)
    r["2K2_no_tri"] = {"count": triangles(A), "pass": triangles(A) == 0}
    divergence_log.append("negative-case: triangle-free graphs give 0 as expected")
    return r


def run_boundary_tests():
    r = {}
    # K3 -> 1 triangle
    A = np.ones((3, 3)) - np.eye(3)
    r["K3_one"] = {"count": triangles(A), "pass": triangles(A) == 1}
    # isolated node (n=1): clustering = 0
    A = np.zeros((1, 1))
    c = local_clustering(A)
    r["n1_zero_clust"] = {"c": c.tolist(), "pass": bool(c[0] == 0.0)}
    divergence_log.append("boundary: deg<2 yields c=0 by convention")
    return r


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(t.get("pass", False) for t in {**pos, **neg, **bnd}.values())
    results = {
        "name": "sim_triangle_count_classical",
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "divergence_log": divergence_log,
        "positive": pos, "negative": neg, "boundary": bnd,
        "summary": {"all_pass": bool(all_pass)}, "all_pass": bool(all_pass),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_triangle_count_classical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}  all_pass={all_pass}")
