#!/usr/bin/env python3
"""
Leviathan atom 2 of 7: STRUCTURE.

Claim: given a carrier, a civilizational shell requires a connected
relational structure over carrier-bearing agents. Disconnected structures
cannot support a single shell; they are at best two candidate shells.

Load-bearing tool: rustworkx (connectedness, components). PyG/xgi not used
at this atom -- structure here is graph-level, not hypergraph or message-
passing.
"""

import json, os

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "no learned structure yet"},
    "pyg":       {"tried": False, "used": False, "reason": "message passing is reduction atom 3"},
    "z3":        {"tried": False, "used": False, "reason": "connectedness solved combinatorially"},
    "cvc5":      {"tried": False, "used": False, "reason": "redundant"},
    "sympy":     {"tried": False, "used": False, "reason": "no symbolic claim here"},
    "clifford":  {"tried": False, "used": False, "reason": "no multivector structure"},
    "geomstats": {"tried": False, "used": False, "reason": "no metric structure yet"},
    "e3nn":      {"tried": False, "used": False, "reason": "no equivariance"},
    "rustworkx": {"tried": False, "used": False, "reason": "connected-components test"},
    "xgi":       {"tried": False, "used": False, "reason": "structure here is 2-uniform"},
    "toponetx":  {"tried": False, "used": False, "reason": "no cell complex yet"},
    "gudhi":     {"tried": False, "used": False, "reason": "persistence not probed here"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import rustworkx as rx
    TOOL_MANIFEST["rustworkx"]["tried"] = True
except ImportError:
    rx = None
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"


def _build(edges, n):
    g = rx.PyGraph()
    g.add_nodes_from(list(range(n)))
    for u, v in edges:
        g.add_edge(u, v, None)
    return g


def run_positive_tests():
    if rx is None: return {"skipped": "rustworkx missing"}
    g = _build([(0,1),(1,2),(2,3),(3,0)], 4)
    k = rx.number_connected_components(g)
    TOOL_MANIFEST["rustworkx"]["used"] = True
    TOOL_MANIFEST["rustworkx"]["reason"] = "connected-components decides shell admissibility"
    TOOL_INTEGRATION_DEPTH["rustworkx"] = "load_bearing"
    return {"connected_ring": {"components": k, "pass": k == 1}}


def run_negative_tests():
    if rx is None: return {"skipped": "rustworkx missing"}
    g = _build([(0,1),(2,3)], 4)  # two disjoint edges
    k = rx.number_connected_components(g)
    return {"disconnected_rejected": {"components": k, "pass": k > 1}}


def run_boundary_tests():
    if rx is None: return {"skipped": "rustworkx missing"}
    g = _build([], 1)  # single isolated node: degenerate but trivially connected
    k = rx.number_connected_components(g)
    return {"singleton_degenerate": {"components": k, "pass": k == 1}}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = (pos.get("connected_ring",{}).get("pass",False)
                and neg.get("disconnected_rejected",{}).get("pass",False)
                and bnd.get("singleton_degenerate",{}).get("pass",False))
    out = {"name":"leviathan_atom_2_structure","classification":"canonical",
           "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,
           "positive":pos,"negative":neg,"boundary":bnd,
           "status":"PASS" if all_pass else "FAIL"}
    d = os.path.join(os.path.dirname(__file__),"a2_state","sim_results")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "leviathan_atom_2_structure_results.json")
    with open(p,"w") as f: json.dump(out,f,indent=2,default=str)
    print(f"[{out['status']}] {p}")
