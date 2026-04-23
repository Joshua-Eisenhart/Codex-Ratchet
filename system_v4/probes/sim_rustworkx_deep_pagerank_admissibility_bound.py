#!/usr/bin/env python3
"""sim_rustworkx_deep_pagerank_admissibility_bound -- rustworkx load_bearing.

Uses rustworkx.pagerank on the probe-weighted digraph. Nodes whose
stationary weight falls below a floor are EXCLUDED from the admissible
attention set (probe-relative to the restart vector).
"""
import json, os
import rustworkx as rx

SCOPE_NOTE = (
    "Probe-relative attention: rustworkx.pagerank supplies the "
    "load-bearing stationary distribution. Exclusion floor is defined on "
    "this distribution; no numpy eigenvector fallback."
)

TOOL_MANIFEST = {
    "rustworkx": {"tried": True, "used": True,
                  "reason": "pagerank stationary vector decides exclusion floor (load-bearing)"},
    "pytorch": {"tried": False, "used": False, "reason": "no autograd needed"},
}
TOOL_INTEGRATION_DEPTH = {"rustworkx": "load_bearing"}


def _pr(n, edges):
    g = rx.PyDiGraph()
    [g.add_node(i) for i in range(n)]
    for u, v in edges:
        g.add_edge(u, v, 1.0)
    return rx.pagerank(g, alpha=0.85)


def run_positive_tests():
    # Star: hub 0 absorbs rank; leaves below floor -> excluded
    edges = [(1, 0), (2, 0), (3, 0), (4, 0)]
    pr = _pr(5, edges)
    floor = 0.15
    leaves_excluded = all(pr[i] < floor for i in (1, 2, 3, 4))
    return {"star_leaves_excluded": {"pass": leaves_excluded is True,
            "pr": {k: round(v, 4) for k, v in pr.items()},
            "result": "leaves_excluded" if leaves_excluded else "admitted"}}


def run_negative_tests():
    # Symmetric ring: all nodes ~equal, none excluded under floor=0.15
    edges = [(0, 1), (1, 2), (2, 3), (3, 0)]
    pr = _pr(4, edges)
    floor = 0.15
    all_admitted = all(pr[i] >= floor for i in range(4))
    return {"ring_all_admitted": {"pass": all_admitted is True,
            "pr": {k: round(v, 4) for k, v in pr.items()},
            "result": "admitted" if all_admitted else "excluded"}}


def run_boundary_tests():
    # Dangling node has no outgoing edges; pagerank still returns a value
    edges = [(0, 1), (1, 2)]
    pr = _pr(3, edges)
    # sum should be ~1
    s = sum(pr.values())
    normed = abs(s - 1.0) < 1e-6
    return {"pagerank_sum_normalized": {"pass": normed is True,
            "sum": round(s, 6),
            "result": "normalized" if normed else "excluded"}}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    results = {
        "name": "sim_rustworkx_deep_pagerank_admissibility_bound",
        "classification": "canonical",
        "scope_note": SCOPE_NOTE,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all(t["pass"] for t in list(pos.values()) + list(neg.values()) + list(bnd.values())),
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "sim_rustworkx_deep_pagerank_admissibility_bound_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(results, open(out, "w"), indent=2, default=str)
    print(f"PASS={results['all_pass']} -> {out}")
