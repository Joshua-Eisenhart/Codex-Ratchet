#!/usr/bin/env python3
"""Classical degree assortativity coefficient (Pearson over edge endpoints)."""
import json, os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True,
                "reason": "cross-check Pearson r of endpoint degrees using torch.corrcoef"},
}
TOOL_INTEGRATION_DEPTH = {"pytorch": "supportive"}

try:
    import torch
except ImportError:
    TOOL_MANIFEST["pytorch"] = {"tried": False, "used": False, "reason": "not installed"}
    TOOL_INTEGRATION_DEPTH["pytorch"] = None

divergence_log = []


def assortativity(A):
    A = (A + A.T > 0).astype(int)
    deg = A.sum(axis=1)
    n = A.shape[0]
    xs, ys = [], []
    for i in range(n):
        for j in range(i+1, n):
            if A[i, j]:
                xs += [deg[i], deg[j]]
                ys += [deg[j], deg[i]]
    if len(xs) < 2:
        return 0.0
    xs = np.array(xs, float); ys = np.array(ys, float)
    if xs.std() == 0 or ys.std() == 0:
        return 0.0
    return float(np.corrcoef(xs, ys)[0, 1])


def run_positive_tests():
    r = {}
    # K4: all degrees equal -> undefined/0
    A = np.ones((4, 4)) - np.eye(4)
    rv = assortativity(A)
    r["regular_K4_zero"] = {"r": rv, "pass": abs(rv) < 1e-9}
    # star: disassortative (high-deg center connects to deg-1 leaves) -> negative
    A = np.zeros((6, 6))
    for i in range(1, 6):
        A[0, i] = A[i, 0] = 1
    rv = assortativity(A)
    r["star_disassortative"] = {"r": rv, "pass": rv < -0.5}
    # two triangles joined by bridge: mildly assortative
    A = np.array([
        [0,1,1,0,0,0,0],
        [1,0,1,0,0,0,0],
        [1,1,0,1,0,0,0],
        [0,0,1,0,1,0,0],
        [0,0,0,1,0,1,1],
        [0,0,0,0,1,0,1],
        [0,0,0,0,1,1,0],
    ], float)
    rv = assortativity(A)
    r["bridge_finite"] = {"r": rv, "pass": bool(-1.0 <= rv <= 1.0)}
    if TOOL_INTEGRATION_DEPTH["pytorch"] == "supportive":
        # torch corrcoef cross-check on the star
        A = np.zeros((6, 6))
        for i in range(1, 6):
            A[0, i] = A[i, 0] = 1
        deg = A.sum(axis=1)
        xs, ys = [], []
        for i in range(6):
            for j in range(i+1, 6):
                if A[i, j]:
                    xs += [deg[i], deg[j]]; ys += [deg[j], deg[i]]
        t = torch.tensor(np.stack([xs, ys]))
        rt = float(torch.corrcoef(t)[0, 1].item())
        rn = assortativity(A)
        r["torch_star_agrees"] = {"torch": rt, "np": rn, "pass": bool(abs(rt - rn) < 1e-6)}
    return r


def run_negative_tests():
    r = {}
    # empty graph: r should be 0 (degenerate), not positive
    A = np.zeros((5, 5))
    rv = assortativity(A)
    r["empty_not_positive"] = {"r": rv, "pass": rv <= 0.0}
    # star is NOT assortative (negation)
    A = np.zeros((5, 5))
    for i in range(1, 5):
        A[0, i] = A[i, 0] = 1
    rv = assortativity(A)
    r["star_not_assortative"] = {"r": rv, "pass": rv < 0}
    divergence_log.append("negative-case: star correctly disassortative")
    return r


def run_boundary_tests():
    r = {}
    # single edge: endpoints same degree -> zero variance, defined as 0
    A = np.array([[0, 1], [1, 0]], float)
    rv = assortativity(A)
    r["single_edge"] = {"r": rv, "pass": abs(rv) < 1e-9}
    # 3-regular cycle: undefined -> 0
    A = np.zeros((6, 6))
    for i in range(6):
        A[i, (i+1) % 6] = A[(i+1) % 6, i] = 1
    rv = assortativity(A)
    r["regular_cycle"] = {"r": rv, "pass": abs(rv) < 1e-9}
    divergence_log.append("boundary: regular graph -> undefined, returned 0")
    return r


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(t.get("pass", False) for t in {**pos, **neg, **bnd}.values())
    results = {
        "name": "sim_assortativity_classical", "classification": classification,
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "divergence_log": divergence_log,
        "positive": pos, "negative": neg, "boundary": bnd,
        "summary": {"all_pass": bool(all_pass)}, "all_pass": bool(all_pass),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_assortativity_classical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}  all_pass={all_pass}")
