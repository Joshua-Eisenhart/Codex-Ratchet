#!/usr/bin/env python3
"""sim_rustworkx_deep_isomorphism_class_excludes -- rustworkx load_bearing.

Uses rustworkx.is_isomorphic (VF2) to decide structural indistinguishability
between candidate constraint graphs. Non-isomorphic candidates are EXCLUDED
from the same admissibility class.
"""
import json, os
import rustworkx as rx

SCOPE_NOTE = (
    "Probe-relative structural equivalence: rustworkx VF2 isomorphism is "
    "load-bearing. Two probe graphs are indistinguishable only if "
    "is_isomorphic returns True; otherwise one is EXCLUDED from the class."
)

TOOL_MANIFEST = {
    "rustworkx": {"tried": True, "used": True,
                  "reason": "VF2 is_isomorphic decides structural exclusion (load-bearing)"},
    "pytorch": {"tried": False, "used": False, "reason": "combinatorial"},
    "z3": {"tried": False, "used": False, "reason": "VF2 sufficient"},
}
TOOL_INTEGRATION_DEPTH = {"rustworkx": "load_bearing"}


def _build(n, edges):
    g = rx.PyGraph()
    [g.add_node(i) for i in range(n)]
    for u, v in edges:
        g.add_edge(u, v, None)
    return g


def run_positive_tests():
    g1 = _build(4, [(0, 1), (1, 2), (2, 3), (3, 0)])
    g2 = _build(4, [(0, 2), (2, 1), (1, 3), (3, 0)])  # relabeled 4-cycle
    iso = rx.is_isomorphic(g1, g2)
    return {"C4_relabeled_indistinguishable": {"pass": iso is True,
            "result": "indistinguishable" if iso else "excluded"}}


def run_negative_tests():
    g1 = _build(4, [(0, 1), (1, 2), (2, 3), (3, 0)])   # C4
    g2 = _build(4, [(0, 1), (0, 2), (0, 3)])           # K_{1,3}
    iso = rx.is_isomorphic(g1, g2)
    return {"C4_vs_star_excluded": {"pass": iso is False,
            "result": "excluded" if not iso else "indistinguishable"}}


def run_boundary_tests():
    # Two graphs with same degree sequence but non-isomorphic (6 nodes):
    # G1 = C6, G2 = two disjoint triangles. Both degree seq = [2]*6.
    g1 = _build(6, [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0)])
    g2 = _build(6, [(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3)])
    iso = rx.is_isomorphic(g1, g2)
    return {"same_degree_seq_but_excluded": {"pass": iso is False,
            "result": "excluded" if not iso else "indistinguishable"}}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    results = {
        "name": "sim_rustworkx_deep_isomorphism_class_excludes",
        "classification": "canonical",
        "scope_note": SCOPE_NOTE,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all(t["pass"] for t in list(pos.values()) + list(neg.values()) + list(bnd.values())),
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "sim_rustworkx_deep_isomorphism_class_excludes_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(results, open(out, "w"), indent=2, default=str)
    print(f"PASS={results['all_pass']} -> {out}")
