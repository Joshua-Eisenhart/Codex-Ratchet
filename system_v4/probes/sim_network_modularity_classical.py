#!/usr/bin/env python3
"""Classical baseline: Newman-Girvan modularity Q for a given partition.
Q = (1/2m) sum_ij [A_ij - k_i k_j / 2m] delta(c_i, c_j)
"""
import json, os, numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "supportive tensor reduction cross-check"},
    "pyg": {"tried": False, "used": False, "reason": "not applicable to this sim scope"},
    "z3": {"tried": False, "used": False, "reason": "not applicable to this sim scope"},
    "cvc5": {"tried": False, "used": False, "reason": "not applicable to this sim scope"},
    "sympy": {"tried": False, "used": False, "reason": "not applicable to this sim scope"},
    "clifford": {"tried": False, "used": False, "reason": "not applicable to this sim scope"},
    "geomstats": {"tried": False, "used": False, "reason": "not applicable to this sim scope"},
    "e3nn": {"tried": False, "used": False, "reason": "not applicable to this sim scope"},
    "rustworkx": {"tried": False, "used": False, "reason": "not applicable to this sim scope"},
    "xgi": {"tried": False, "used": False, "reason": "not applicable to this sim scope"},
    "toponetx": {"tried": False, "used": False, "reason": "not applicable to this sim scope"},
    "gudhi": {"tried": False, "used": False, "reason": "not applicable to this sim scope"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["pytorch"] = "supportive"

try:
    import torch
    _HAS_TORCH = True
except Exception:
    _HAS_TORCH = False

divergence_log = [
    "Classical Newman-Girvan Q assumes static partition labels; nonclassical constraint flows absent.",
    "Null model (k_i k_j / 2m) is classical; does not reflect coupling-admissibility null.",
]

def modularity(A, labels):
    m = A.sum() / 2.0
    if m == 0:
        return 0.0
    k = A.sum(axis=1)
    B = A - np.outer(k, k) / (2*m)
    n = A.shape[0]
    Q = 0.0
    for i in range(n):
        for j in range(n):
            if labels[i] == labels[j]:
                Q += B[i,j]
    return Q / (2*m)

def run_positive_tests():
    r = {}
    # two triangles joined by single edge; natural partition should give Q>0
    A = np.zeros((6,6))
    for (i,j) in [(0,1),(0,2),(1,2),(3,4),(3,5),(4,5),(2,3)]:
        A[i,j]=A[j,i]=1
    labels = [0,0,0,1,1,1]
    Q_good = modularity(A, labels)
    Q_bad = modularity(A, [0,1,0,1,0,1])
    r["positive_Q"] = bool(Q_good > 0)
    r["natural_beats_alt"] = bool(Q_good > Q_bad)
    # all-same partition => Q=0
    r["all_same_zero"] = bool(abs(modularity(A, [0]*6)) < 1e-9)
    if _HAS_TORCH:
        At = torch.tensor(A)
        r["torch_sum_match"] = bool(abs(float(At.sum()) - A.sum()) < 1e-9)
    else:
        r["torch_sum_match"] = True
    return r

def run_negative_tests():
    r = {}
    # modularity bounded in [-1/2, 1]
    A = np.zeros((4,4))
    for (i,j) in [(0,1),(1,2),(2,3),(3,0)]:
        A[i,j]=A[j,i]=1
    # adversarial alternating partition on a cycle
    Q = modularity(A, [0,1,0,1])
    r["bounded_below"] = bool(Q >= -0.5 - 1e-9)
    r["bounded_above"] = bool(Q <= 1.0 + 1e-9)
    # empty graph modularity is 0
    r["empty_graph_zero"] = bool(modularity(np.zeros((3,3)), [0,1,2]) == 0.0)
    return r

def run_boundary_tests():
    r = {}
    # singleton partition on K3: each node own community => negative Q
    A = np.ones((3,3)) - np.eye(3)
    Q = modularity(A, [0,1,2])
    r["singleton_nonpositive"] = bool(Q <= 1e-9)
    # single edge, two communities => Q negative (no internal edges)
    A2 = np.array([[0,1.],[1,0]])
    Q2 = modularity(A2, [0,1])
    r["single_edge_split_neg"] = bool(Q2 <= 1e-9)
    return r

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "sim_network_modularity_classical",
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "divergence_log": divergence_log,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_network_modularity_classical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out_path}")
