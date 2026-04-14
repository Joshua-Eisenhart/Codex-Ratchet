#!/usr/bin/env python3
"""
sim_networkx_capability.py -- Tool-capability sim for networkx.

Covers: shortest_path, normalized Laplacian spectrum, isomorphism check, max-flow.
Classification: canonical (tool-capability sim; networkx is load-bearing).
"""

import json
import os
import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "networkx": {"tried": False, "used": False, "reason": ""},
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": ""},
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi": {"tried": False, "used": False, "reason": ""},
    "toponetx": {"tried": False, "used": False, "reason": ""},
    "gudhi": {"tried": False, "used": False, "reason": ""},
}

TOOL_INTEGRATION_DEPTH = {
    "networkx": None,
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

try:
    import networkx as nx
    TOOL_MANIFEST["networkx"]["tried"] = True
except ImportError:
    nx = None
    TOOL_MANIFEST["networkx"]["reason"] = "not installed"

# Optional import tries (kept minimal; not used here)
for name, mod in [("sympy", "sympy")]:
    try:
        __import__(mod)
        TOOL_MANIFEST[name]["tried"] = True
    except ImportError:
        TOOL_MANIFEST[name]["reason"] = "not installed"


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    r = {}
    # shortest_path on a path graph 0-1-2-3-4
    G = nx.path_graph(5)
    sp = nx.shortest_path(G, source=0, target=4)
    r["shortest_path_path5"] = {"path": sp, "len": len(sp) - 1, "pass": sp == [0, 1, 2, 3, 4]}

    # normalized Laplacian spectrum of K4 -- known eigenvalues {0, 4/3, 4/3, 4/3}
    K4 = nx.complete_graph(4)
    L = nx.normalized_laplacian_matrix(K4).toarray()
    eig = sorted(np.linalg.eigvalsh(L).tolist())
    expected = [0.0, 4/3, 4/3, 4/3]
    ok = all(abs(a - b) < 1e-9 for a, b in zip(eig, expected))
    r["spectral_K4"] = {"eig": eig, "expected": expected, "pass": ok}

    # isomorphism: two relabelings of C5 are isomorphic
    C5a = nx.cycle_graph(5)
    C5b = nx.relabel_nodes(nx.cycle_graph(5), {i: (i + 2) % 5 for i in range(5)})
    iso = nx.is_isomorphic(C5a, C5b)
    r["iso_C5_relabel"] = {"iso": iso, "pass": iso is True}

    # max-flow on a small DAG with known capacity
    D = nx.DiGraph()
    D.add_edge("s", "a", capacity=3)
    D.add_edge("s", "b", capacity=2)
    D.add_edge("a", "t", capacity=2)
    D.add_edge("b", "t", capacity=3)
    D.add_edge("a", "b", capacity=1)
    flow_val, _ = nx.maximum_flow(D, "s", "t")
    r["max_flow_small"] = {"flow": flow_val, "expected": 5, "pass": flow_val == 5}
    return r


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    r = {}
    # shortest_path: disconnected graph must raise
    G = nx.Graph()
    G.add_nodes_from([0, 1])
    try:
        nx.shortest_path(G, source=0, target=1)
        raised = False
    except nx.NetworkXNoPath:
        raised = True
    r["shortest_path_disconnected_raises"] = {"raised": raised, "pass": raised}

    # spectral: non-isomorphic graphs with same node count should have different spectra
    P4 = nx.path_graph(4)
    K4 = nx.complete_graph(4)
    e1 = sorted(np.linalg.eigvalsh(nx.normalized_laplacian_matrix(P4).toarray()).tolist())
    e2 = sorted(np.linalg.eigvalsh(nx.normalized_laplacian_matrix(K4).toarray()).tolist())
    differ = any(abs(a - b) > 1e-9 for a, b in zip(e1, e2))
    r["spectral_P4_vs_K4_differ"] = {"differ": differ, "pass": differ}

    # iso: C5 vs P5 not isomorphic
    iso = nx.is_isomorphic(nx.cycle_graph(5), nx.path_graph(5))
    r["iso_C5_vs_P5_false"] = {"iso": iso, "pass": iso is False}

    # max-flow: zero-capacity cut yields flow 0
    D = nx.DiGraph()
    D.add_edge("s", "a", capacity=5)
    D.add_edge("a", "t", capacity=0)
    flow_val, _ = nx.maximum_flow(D, "s", "t")
    r["max_flow_zero_cut"] = {"flow": flow_val, "pass": flow_val == 0}
    return r


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    r = {}
    # Single-node shortest path
    G = nx.Graph()
    G.add_node(0)
    sp = nx.shortest_path(G, source=0, target=0)
    r["shortest_path_single_node"] = {"path": sp, "pass": sp == [0]}

    # Empty graph spectrum size 0
    E = nx.Graph()
    E.add_nodes_from(range(3))  # isolated nodes -> normalized Laplacian is identity on non-isolated only
    # With isolated nodes, normalized Laplacian is 0 matrix (by nx convention)
    L = nx.normalized_laplacian_matrix(E).toarray()
    eig = sorted(np.linalg.eigvalsh(L).tolist())
    r["spectral_isolated_nodes_all_zero"] = {"eig": eig, "pass": all(abs(v) < 1e-12 for v in eig)}

    # Iso: two empty graphs of equal order
    iso = nx.is_isomorphic(nx.empty_graph(4), nx.empty_graph(4))
    r["iso_empty_equal_order"] = {"iso": iso, "pass": iso is True}

    # Max-flow: source==sink should be 0 or raise; networkx returns inf for self; treat either as pass
    D = nx.DiGraph()
    D.add_edge("s", "t", capacity=1)
    try:
        flow_val, _ = nx.maximum_flow(D, "s", "s")
        pass_case = (flow_val == 0) or (flow_val == float("inf"))
    except nx.NetworkXError:
        flow_val = "raised"
        pass_case = True
    r["max_flow_source_equals_sink"] = {"flow": flow_val, "pass": pass_case}
    return r


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    # Mark networkx as load-bearing (it decides every test result).
    TOOL_MANIFEST["networkx"]["used"] = True
    TOOL_MANIFEST["networkx"]["reason"] = (
        "networkx provides shortest_path, normalized_laplacian_matrix, is_isomorphic, "
        "and maximum_flow -- each test's pass/fail is determined by networkx output; "
        "no substitute implementation is used."
    )
    TOOL_INTEGRATION_DEPTH["networkx"] = "load_bearing"

    all_sections = [positive, negative, boundary]
    all_pass = all(t.get("pass", False) for sec in all_sections for t in sec.values())

    results = {
        "name": "sim_networkx_capability",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": "canonical",
        "all_pass": all_pass,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_networkx_capability_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"ALL_PASS={all_pass}")
