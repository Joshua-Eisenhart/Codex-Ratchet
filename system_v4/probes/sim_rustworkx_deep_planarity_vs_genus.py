#!/usr/bin/env python3
"""sim_rustworkx_deep_planarity_vs_genus -- rustworkx load_bearing.

Uses rustworkx.is_planar (Left-Right planarity test) to separate genus-0
admissible probe graphs from genus>=1 excluded ones. K_5 and K_{3,3}
are the canonical excluded witnesses (Kuratowski).
"""
import json, os
import rustworkx as rx

SCOPE_NOTE = (
    "Topological admissibility (probe-relative to sphere embedding): "
    "rustworkx.is_planar is load-bearing. Non-planar graphs are EXCLUDED "
    "from genus-0 admissible class; the Kuratowski witnesses K_5, K_{3,3} "
    "are the canonical exclusion cases."
)

TOOL_MANIFEST = {
    "rustworkx": {"tried": True, "used": True,
                  "reason": "is_planar Left-Right test decides genus-0 admissibility (load-bearing)"},
    "toponetx": {"tried": False, "used": False,
                 "reason": "planarity sufficient; no cell-complex needed here"},
}
TOOL_INTEGRATION_DEPTH = {"rustworkx": "load_bearing"}


def _planar(n, edges):
    g = rx.PyGraph()
    [g.add_node(i) for i in range(n)]
    for u, v in edges:
        g.add_edge(u, v, None)
    return rx.is_planar(g)


def run_positive_tests():
    # K4 is planar
    edges = [(i, j) for i in range(4) for j in range(i + 1, 4)]
    ok = _planar(4, edges)
    return {"K4_admitted": {"pass": ok is True,
            "result": "admitted" if ok else "excluded"}}


def run_negative_tests():
    # K5 is non-planar -> excluded
    edges = [(i, j) for i in range(5) for j in range(i + 1, 5)]
    ok = _planar(5, edges)
    return {"K5_excluded": {"pass": ok is False,
            "result": "excluded" if not ok else "admitted"}}


def run_boundary_tests():
    # K_{3,3} non-planar -> excluded (Kuratowski second witness)
    left, right = [0, 1, 2], [3, 4, 5]
    edges = [(l, r) for l in left for r in right]
    ok = _planar(6, edges)
    return {"K33_excluded": {"pass": ok is False,
            "result": "excluded" if not ok else "admitted"}}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    results = {
        "name": "sim_rustworkx_deep_planarity_vs_genus",
        "classification": "canonical",
        "scope_note": SCOPE_NOTE,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all(t["pass"] for t in list(pos.values()) + list(neg.values()) + list(bnd.values())),
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "sim_rustworkx_deep_planarity_vs_genus_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(results, open(out, "w"), indent=2, default=str)
    print(f"PASS={results['all_pass']} -> {out}")
