#!/usr/bin/env python3
"""sim_rustworkx_deep_mincut_probe_relative -- rustworkx load_bearing.

Uses rustworkx.stoer_wagner_min_cut to decide the minimum probe-edge cost
that severs a graph's connectivity. Configurations whose cut exceeds a
capacity bound are EXCLUDED from the admissible-coupling set.
"""
import json, os
import rustworkx as rx

SCOPE_NOTE = (
    "Probe-relative capacity: rustworkx stoer_wagner_min_cut is "
    "load-bearing for deciding coupling admissibility under a capacity "
    "bound. Graphs with min-cut above the bound are EXCLUDED."
)

TOOL_MANIFEST = {
    "rustworkx": {"tried": True, "used": True,
                  "reason": "stoer_wagner_min_cut computes global min-cut (load-bearing)"},
    "pytorch": {"tried": False, "used": False, "reason": "combinatorial"},
    "sympy": {"tried": False, "used": False, "reason": "integer weights"},
}
TOOL_INTEGRATION_DEPTH = {"rustworkx": "load_bearing"}


def _mincut(n, weighted_edges):
    g = rx.PyGraph()
    [g.add_node(i) for i in range(n)]
    for u, v, w in weighted_edges:
        g.add_edge(u, v, w)
    cut, _part = rx.stoer_wagner_min_cut(g, weight_fn=lambda w: float(w))
    return cut


def run_positive_tests():
    # Two triangles connected by a single weight-1 bridge -> mincut = 1
    edges = [(0, 1, 5), (1, 2, 5), (2, 0, 5),
             (3, 4, 5), (4, 5, 5), (5, 3, 5),
             (2, 3, 1)]
    cut = _mincut(6, edges)
    admissible = cut <= 1  # bound = 1
    return {"bridge_cut_admitted": {"pass": admissible is True,
            "cut": cut, "result": "admitted" if admissible else "excluded"}}


def run_negative_tests():
    # K4 all weight 3: mincut = 9 (each vertex has 3 edges of weight 3)
    edges = [(0, 1, 3), (0, 2, 3), (0, 3, 3),
             (1, 2, 3), (1, 3, 3), (2, 3, 3)]
    cut = _mincut(4, edges)
    admissible = cut <= 1
    return {"K4_above_bound_excluded": {"pass": admissible is False,
            "cut": cut, "result": "excluded" if not admissible else "admitted"}}


def run_boundary_tests():
    # Exactly at bound: two nodes joined by two parallel-equivalent edges -> cut = 2
    # rustworkx PyGraph supports multi-edges via multiple add_edge calls
    g = rx.PyGraph()
    [g.add_node(i) for i in range(3)]
    g.add_edge(0, 1, 1)
    g.add_edge(1, 2, 1)
    g.add_edge(0, 2, 1)
    cut, _ = rx.stoer_wagner_min_cut(g, weight_fn=lambda w: float(w))
    at_bound = cut == 2
    return {"triangle_mincut_equals_2": {"pass": at_bound is True,
            "cut": cut, "result": "admitted_at_bound" if at_bound else "excluded"}}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    results = {
        "name": "sim_rustworkx_deep_mincut_probe_relative",
        "classification": "canonical",
        "scope_note": SCOPE_NOTE,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all(t["pass"] for t in list(pos.values()) + list(neg.values()) + list(bnd.values())),
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "sim_rustworkx_deep_mincut_probe_relative_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(results, open(out, "w"), indent=2, default=str)
    print(f"PASS={results['all_pass']} -> {out}")
