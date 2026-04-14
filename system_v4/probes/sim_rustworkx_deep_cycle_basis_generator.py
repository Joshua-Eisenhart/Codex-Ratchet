#!/usr/bin/env python3
"""sim_rustworkx_deep_cycle_basis_generator -- rustworkx load_bearing.

Uses rustworkx.cycle_basis to enumerate the cycle space generators of
an undirected probe graph. Configurations whose forbidden edge lies in
NO basis cycle are EXCLUDED from the homologically-nontrivial admissible
set.
"""
import json, os
import rustworkx as rx

SCOPE_NOTE = (
    "Cycle basis from rustworkx spans H_1(graph; Z). Membership of a "
    "probe edge in any basis cycle is load-bearing for the admissibility "
    "decision; no linear-algebra fallback is used."
)

TOOL_MANIFEST = {
    "rustworkx": {"tried": True, "used": True,
                  "reason": "cycle_basis enumerates Z-basis of H_1 (load-bearing)"},
    "pytorch": {"tried": False, "used": False, "reason": "no tensor op needed"},
    "sympy": {"tried": False, "used": False, "reason": "integer cycle membership only"},
}
TOOL_INTEGRATION_DEPTH = {"rustworkx": "load_bearing"}


def _edge_in_any_cycle(n, edges, probe_edge):
    g = rx.PyGraph()
    idx = [g.add_node(i) for i in range(n)]
    for u, v in edges:
        g.add_edge(idx[u], idx[v], None)
    cycles = rx.cycle_basis(g)
    a, b = probe_edge
    for cyc in cycles:
        for i in range(len(cyc)):
            u, v = cyc[i], cyc[(i + 1) % len(cyc)]
            if {u, v} == {a, b}:
                return True
    return False


def run_positive_tests():
    # Triangle: every edge participates in the basis cycle
    edges = [(0, 1), (1, 2), (2, 0)]
    hit = _edge_in_any_cycle(3, edges, (0, 1))
    return {"triangle_edge_in_basis": {"pass": hit is True,
            "result": "admitted" if hit else "excluded"}}


def run_negative_tests():
    # Tree: no cycles, edge (0,1) excluded from admissible set
    edges = [(0, 1), (1, 2), (2, 3)]
    hit = _edge_in_any_cycle(4, edges, (0, 1))
    return {"tree_edge_excluded": {"pass": hit is False,
            "result": "excluded" if not hit else "admitted"}}


def run_boundary_tests():
    # Two disjoint triangles: basis has 2 cycles; probe edge in second component
    edges = [(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3)]
    hit = _edge_in_any_cycle(6, edges, (3, 4))
    return {"disjoint_triangles_second_component": {"pass": hit is True,
            "result": "admitted" if hit else "excluded"}}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    results = {
        "name": "sim_rustworkx_deep_cycle_basis_generator",
        "classification": "canonical",
        "scope_note": SCOPE_NOTE,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all(t["pass"] for t in list(pos.values()) + list(neg.values()) + list(bnd.values())),
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "sim_rustworkx_deep_cycle_basis_generator_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(results, open(out, "w"), indent=2, default=str)
    print(f"PASS={results['all_pass']} -> {out}")
