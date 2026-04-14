#!/usr/bin/env python3
"""
FEP atom 2 of 7: STRUCTURE.

Claim: an FEP shell requires a Markov-blanket-shaped relational
structure -- internal states I, external states E, and blanket B (sensory
S + active A) -- such that removing B disconnects I from E. If removal
of the blanket leaves I and E in the same component, there is no FEP
shell (the blanket failed its structural duty).

Load-bearing tool: rustworkx (component count after blanket-node
removal).
"""

import json, os

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "no learning here"},
    "pyg":       {"tried": False, "used": False, "reason": "message passing is reduction atom"},
    "z3":        {"tried": False, "used": False, "reason": "conditional-indep proof is atom 4"},
    "cvc5":      {"tried": False, "used": False, "reason": "redundant"},
    "sympy":     {"tried": False, "used": False, "reason": "symbolic done in atom 1"},
    "clifford":  {"tried": False, "used": False, "reason": "not used"},
    "geomstats": {"tried": False, "used": False, "reason": "no metric yet"},
    "e3nn":      {"tried": False, "used": False, "reason": "not used"},
    "rustworkx": {"tried": False, "used": False, "reason": "component count after blanket removal"},
    "xgi":       {"tried": False, "used": False, "reason": "2-uniform suffices"},
    "toponetx":  {"tried": False, "used": False, "reason": "not used"},
    "gudhi":     {"tried": False, "used": False, "reason": "not used"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import rustworkx as rx
    TOOL_MANIFEST["rustworkx"]["tried"] = True
except ImportError:
    rx = None
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"


def _components_without(nodes, edges, remove):
    g = rx.PyGraph()
    idx = {n: g.add_node(n) for n in nodes if n not in remove}
    for u, v in edges:
        if u in idx and v in idx:
            g.add_edge(idx[u], idx[v], None)
    return rx.number_connected_components(g)


def run_positive_tests():
    if rx is None: return {"skipped":"rustworkx missing"}
    # I = {i1,i2}, B = {s, a}, E = {e1,e2}. Edges: I<->B<->E only.
    nodes = ["i1","i2","s","a","e1","e2"]
    edges = [("i1","i2"),("i1","s"),("i2","a"),
             ("s","e1"),("a","e2"),("e1","e2")]
    k_full = _components_without(nodes, edges, set())
    k_noB  = _components_without(nodes, edges, {"s","a"})
    TOOL_MANIFEST["rustworkx"]["used"] = True
    TOOL_MANIFEST["rustworkx"]["reason"] = "blanket removal splits I from E"
    TOOL_INTEGRATION_DEPTH["rustworkx"] = "load_bearing"
    return {"blanket_separates": {
        "full_components": k_full, "no_blanket_components": k_noB,
        "pass": k_full == 1 and k_noB == 2
    }}


def run_negative_tests():
    if rx is None: return {"skipped":"rustworkx missing"}
    # Direct I<->E edge bypasses blanket -- structure invalid
    nodes = ["i1","s","a","e1","leak_i","leak_e"]
    edges = [("i1","s"),("s","e1"),("i1","a"),("a","e1"),
             ("leak_i","leak_e")]  # direct internal->external leak
    # Place leak between internal and external: redo
    nodes = ["i1","s","a","e1"]
    edges = [("i1","s"),("s","e1"),("i1","a"),("a","e1"),
             ("i1","e1")]  # leak edge
    k_noB = _components_without(nodes, edges, {"s","a"})
    # blanket removal still leaves i1-e1 connected -> not separated
    return {"leaky_blanket_rejected": {"no_blanket_components": k_noB,
                                       "pass": k_noB == 1}}


def run_boundary_tests():
    if rx is None: return {"skipped":"rustworkx missing"}
    # Trivial: no internal, no external; only blanket. Degenerate SAT.
    nodes = ["s","a"]; edges = [("s","a")]
    k = _components_without(nodes, edges, set())
    return {"blanket_only_degenerate": {"components": k, "pass": k == 1}}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = (pos.get("blanket_separates",{}).get("pass",False)
                and neg.get("leaky_blanket_rejected",{}).get("pass",False)
                and bnd.get("blanket_only_degenerate",{}).get("pass",False))
    out = {"name":"fep_atom_2_structure","classification":"canonical",
           "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,
           "positive":pos,"negative":neg,"boundary":bnd,
           "status":"PASS" if all_pass else "FAIL"}
    d = os.path.join(os.path.dirname(__file__),"a2_state","sim_results")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d,"fep_atom_2_structure_results.json")
    with open(p,"w") as f: json.dump(out,f,indent=2,default=str)
    print(f"[{out['status']}] {p}")
