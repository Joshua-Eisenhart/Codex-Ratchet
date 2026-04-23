#!/usr/bin/env python3
"""sim_rustworkx_deep_scc_admissibility -- rustworkx load_bearing.

Uses rustworkx.strongly_connected_components on probe-reachability
digraphs to decide admissibility of cyclic constraint closures.
Exclusion language: configurations where an SCC contains a forbidden
probe pair are EXCLUDED from the admissible set.
"""
import json, os
import rustworkx as rx

SCOPE_NOTE = (
    "Probe-relative: admissibility is defined by whether the probe pair "
    "(forbidden_src, forbidden_dst) lies in a common SCC. rustworkx SCC "
    "is load-bearing; without Tarjan/Kosaraju on the full digraph the "
    "exclusion cannot be decided. No numpy fallback."
)

TOOL_MANIFEST = {
    "rustworkx": {"tried": True, "used": True,
                  "reason": "strongly_connected_components decides cyclic closure exclusion (load-bearing)"},
    "pytorch": {"tried": False, "used": False, "reason": "not needed: combinatorial admissibility"},
    "z3": {"tried": False, "used": False, "reason": "SCC is polynomial; SMT not required"},
    "sympy": {"tried": False, "used": False, "reason": "no symbolic closure needed"},
}
TOOL_INTEGRATION_DEPTH = {"rustworkx": "load_bearing"}


def _scc_contains_pair(edges, n, src, dst):
    g = rx.PyDiGraph()
    idx = [g.add_node(i) for i in range(n)]
    for u, v in edges:
        g.add_edge(idx[u], idx[v], None)
    sccs = rx.strongly_connected_components(g)
    for comp in sccs:
        s = set(comp)
        if src in s and dst in s:
            return True
    return False


def run_positive_tests():
    # 4-node cycle 0->1->2->3->0 has all nodes in one SCC; (0,2) excluded
    edges = [(0, 1), (1, 2), (2, 3), (3, 0)]
    excluded = _scc_contains_pair(edges, 4, 0, 2)
    return {"cycle4_pair_02_excluded": {"pass": excluded is True,
            "result": "excluded" if excluded else "admitted"}}


def run_negative_tests():
    # DAG 0->1->2->3 has no SCC with >1 node; pair (0,3) NOT excluded
    edges = [(0, 1), (1, 2), (2, 3)]
    excluded = _scc_contains_pair(edges, 4, 0, 3)
    return {"dag_pair_03_not_excluded": {"pass": excluded is False,
            "result": "admitted" if not excluded else "excluded"}}


def run_boundary_tests():
    # Self-loop only: node in trivial SCC with itself (size 1 but self-loop)
    g = rx.PyDiGraph()
    a = g.add_node(0); b = g.add_node(1)
    g.add_edge(a, a, None)
    sccs = rx.strongly_connected_components(g)
    # Self-loop node is in SCC of size 1; (0,0) counts as same component
    pair_in_same = any(0 in s and 1 in s for s in sccs)
    return {"self_loop_disjoint": {"pass": pair_in_same is False,
            "result": "admitted" if not pair_in_same else "excluded"}}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    results = {
        "name": "sim_rustworkx_deep_scc_admissibility",
        "classification": "canonical",
        "scope_note": SCOPE_NOTE,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all(t["pass"] for t in list(pos.values()) + list(neg.values()) + list(bnd.values())),
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "sim_rustworkx_deep_scc_admissibility_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(results, open(out, "w"), indent=2, default=str)
    print(f"PASS={results['all_pass']} -> {out}")
