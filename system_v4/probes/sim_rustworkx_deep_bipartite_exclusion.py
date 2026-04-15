#!/usr/bin/env python3
"""sim_rustworkx_deep_bipartite_exclusion -- rustworkx load_bearing.

Uses rustworkx.two_color to decide bipartiteness of probe graphs. Graphs
admitting a valid 2-coloring survive the parity admissibility probe;
graphs with odd cycles are EXCLUDED.
"""
import json, os
import rustworkx as rx
classification = "classical_baseline"  # auto-added by adaptive_controller

SCOPE_NOTE = (
    "Parity admissibility (probe-relative to 2-coloring): "
    "rustworkx.two_color is load-bearing. Odd-cycle graphs are EXCLUDED; "
    "no manual DFS fallback."
)

TOOL_MANIFEST = {
    "rustworkx": {"tried": True, "used": True,
                  "reason": "two_color decides bipartite admissibility (load-bearing)"},
    "pytorch": {"tried": False, "used": False, "reason": "purely combinatorial, no tensor compute"},
}
TOOL_INTEGRATION_DEPTH = {"rustworkx": "load_bearing"}


def _is_bipartite(n, edges):
    g = rx.PyGraph()
    [g.add_node(i) for i in range(n)]
    for u, v in edges:
        g.add_edge(u, v, None)
    coloring = rx.two_color(g)
    return coloring is not None


def run_positive_tests():
    # 4-cycle is bipartite
    ok = _is_bipartite(4, [(0, 1), (1, 2), (2, 3), (3, 0)])
    return {"C4_admitted": {"pass": ok is True,
            "result": "admitted" if ok else "excluded"}}


def run_negative_tests():
    # Triangle: odd cycle -> excluded
    ok = _is_bipartite(3, [(0, 1), (1, 2), (2, 0)])
    return {"triangle_excluded": {"pass": ok is False,
            "result": "excluded" if not ok else "admitted"}}


def run_boundary_tests():
    # Tree (no cycles) trivially bipartite
    ok = _is_bipartite(5, [(0, 1), (0, 2), (1, 3), (1, 4)])
    return {"tree_admitted": {"pass": ok is True,
            "result": "admitted" if ok else "excluded"}}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    results = {
        "name": "sim_rustworkx_deep_bipartite_exclusion",
        "classification": "canonical",
        "scope_note": SCOPE_NOTE,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all(t["pass"] for t in list(pos.values()) + list(neg.values()) + list(bnd.values())),
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "sim_rustworkx_deep_bipartite_exclusion_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(results, open(out, "w"), indent=2, default=str)
    print(f"PASS={results['all_pass']} -> {out}")
