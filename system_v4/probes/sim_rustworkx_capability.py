#!/usr/bin/env python3
"""
sim_rustworkx_capability.py -- Tool-capability isolation sim for rustworkx.

Governing rule (durable, owner+Hermes 2026-04-13):
rustworkx is currently used as load_bearing in ~25 sims with no capability probe.
This sim is the bounded isolation probe that unblocks rustworkx for nonclassical use.

Contract (from new docs/plans/tool-capability-sim-program.md / ~/wiki/concepts/...):

- Job the tool is supposed to do here:
    Fast DAG construction, topological sort, transitive reduction,
    shortest path / Dijkstra, cycle detection on the shell-nesting /
    schedule-dependency / coupling-order graphs produced by other sims.

- Minimal bounded task it can actually do:
    Build a PyDiGraph / PyGraph, add nodes + weighted edges, run
    topological_sort, dag_longest_path_length, is_directed_acyclic_graph,
    transitive_reduction, dijkstra_shortest_paths on graphs of
    O(10^3) nodes with numeric-verified answers.

- Failure modes in this stack:
    * Silent: using rustworkx as a "decorative" import without exercising
      the ordering it supposedly provides (TOOL_INTEGRATION_DEPTH must be
      explicit).
    * API drift: rustworkx renames between versions
      (e.g. transitive_reduction lives in rustworkx.transitive_reduction
      in 0.13+, was different earlier); surface here.
    * Input: rustworkx raises on cyclic input to topological_sort
      (DAGHasCycle) -- downstream sims must handle or prove acyclicity first.

- Decorative vs load-bearing:
    Decorative = `import rustworkx` with no rx.* call materially affecting
    the result.
    Load-bearing = the ordering / path / reduction produced by rustworkx
    is the quantity the sim's claim rests on.

- Baseline vs canonical comparison:
    Baseline = NetworkX on the same graph (pure Python).
    Canonical-use = rustworkx on the same graph; both must agree on
    ordering / path length / cycle presence. Performance delta is
    reported, not load-bearing on its own.

- Actual-use witness:
    sim_foundation_shell_graph_topology.py
    uses rx.PyDiGraph, rx.topological_sort, rx.dag_longest_path_length,
    rx.is_directed_acyclic_graph as load-bearing. We replay a
    minimized version of that DAG here and confirm rustworkx produces
    the same ordering / depth that hand-verified ground truth gives.
"""

import json
import os
import time
import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "not needed -- pure graph capability probe"},
    "pyg":       {"tried": False, "used": False, "reason": "not needed -- pure graph capability probe"},
    "z3":        {"tried": False, "used": False, "reason": "not needed -- numeric ground truth is enough for capability probe"},
    "cvc5":      {"tried": False, "used": False, "reason": "not needed"},
    "sympy":     {"tried": False, "used": False, "reason": "not needed"},
    "clifford":  {"tried": False, "used": False, "reason": "not geometry-relevant"},
    "geomstats": {"tried": False, "used": False, "reason": "not geometry-relevant"},
    "e3nn":      {"tried": False, "used": False, "reason": "not geometry-relevant"},
    "rustworkx": {"tried": False, "used": False, "reason": "under test"},
    "xgi":       {"tried": False, "used": False, "reason": "baseline is networkx, not xgi"},
    "toponetx":  {"tried": False, "used": False, "reason": "not topology-relevant here"},
    "gudhi":     {"tried": False, "used": False, "reason": "not topology-relevant here"},
    "networkx":  {"tried": False, "used": False, "reason": "classical baseline for cross-check"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None, "pyg": None, "z3": None, "cvc5": None, "sympy": None,
    "clifford": None, "geomstats": None, "e3nn": None,
    "rustworkx": "load_bearing",   # the subject of the probe
    "xgi": None, "toponetx": None, "gudhi": None,
    "networkx": "supportive",       # cross-check baseline
}

try:
    import rustworkx as rx
    TOOL_MANIFEST["rustworkx"]["tried"] = True
    TOOL_MANIFEST["rustworkx"]["used"] = True
    TOOL_MANIFEST["rustworkx"]["reason"] = "capability under test -- DAG / toposort / transitive reduction / Dijkstra / cycle detection"
    RX_OK = True
    RX_VERSION = getattr(rx, "__version__", "unknown")
except Exception as exc:
    RX_OK = False
    RX_VERSION = None
    TOOL_MANIFEST["rustworkx"]["reason"] = f"not installed: {exc}"

try:
    import networkx as nx
    TOOL_MANIFEST["networkx"]["tried"] = True
    TOOL_MANIFEST["networkx"]["used"] = True
    NX_OK = True
except Exception as exc:
    NX_OK = False
    TOOL_MANIFEST["networkx"]["reason"] = f"not installed: {exc}"


# =====================================================================
# Helpers
# =====================================================================

def _build_rx_dag(edges, n_nodes):
    g = rx.PyDiGraph(check_cycle=False)
    idx = [g.add_node(i) for i in range(n_nodes)]
    for u, v, w in edges:
        g.add_edge(idx[u], idx[v], float(w))
    return g, idx


def _build_nx_dag(edges, n_nodes):
    g = nx.DiGraph()
    g.add_nodes_from(range(n_nodes))
    for u, v, w in edges:
        g.add_edge(u, v, weight=float(w))
    return g


def _is_topo_valid(order, edges):
    pos = {n: i for i, n in enumerate(order)}
    for u, v, _ in edges:
        if pos[u] >= pos[v]:
            return False
    return True


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}
    if not RX_OK:
        results["rustworkx_available"] = {"pass": False, "detail": "rustworkx missing"}
        return results
    results["rustworkx_available"] = {"pass": True, "version": RX_VERSION}

    # --- 1. DAG construction + topological sort correctness ---
    # Hand-verified diamond+tail:
    #   0 -> 1 -> 3 -> 4
    #   0 -> 2 -> 3
    edges = [(0, 1, 1.0), (0, 2, 1.0), (1, 3, 1.0), (2, 3, 1.0), (3, 4, 1.0)]
    n = 5
    g_rx, idx = _build_rx_dag(edges, n)
    topo_rx = [g_rx[n_]["_notused"] if False else n_ for n_ in rx.topological_sort(g_rx)]
    # rx.topological_sort returns node indices (ints).
    topo_valid = _is_topo_valid(topo_rx, edges)
    results["toposort_diamond"] = {
        "pass": bool(topo_valid),
        "order": list(topo_rx),
        "detail": "every edge (u,v) must have pos(u) < pos(v)",
    }

    if NX_OK:
        g_nx = _build_nx_dag(edges, n)
        topo_nx = list(nx.topological_sort(g_nx))
        results["toposort_vs_networkx"] = {
            "pass": _is_topo_valid(topo_nx, edges) and topo_valid,
            "rx_order": list(topo_rx),
            "nx_order": topo_nx,
            "detail": "both orderings must be topologically valid (not necessarily identical)",
        }

    # --- 2. Transitive reduction correctness ---
    # Graph: 0->1, 1->2, 0->2   reduction must drop 0->2
    tr_edges = [(0, 1, 1.0), (1, 2, 1.0), (0, 2, 1.0)]
    g_tr, _ = _build_rx_dag(tr_edges, 3)
    try:
        tr_fn = getattr(rx, "transitive_reduction", None)
        if tr_fn is None:
            results["transitive_reduction"] = {
                "pass": False,
                "detail": "rx.transitive_reduction not exposed in this rustworkx version -- API drift",
            }
        else:
            reduced = tr_fn(g_tr)
            # rustworkx may return a graph or (graph, mapping).
            red_graph = reduced[0] if isinstance(reduced, tuple) else reduced
            red_edges = set((u, v) for (u, v) in red_graph.edge_list())
            expected = {(0, 1), (1, 2)}
            results["transitive_reduction"] = {
                "pass": red_edges == expected,
                "got": sorted(red_edges),
                "expected": sorted(expected),
            }
    except Exception as exc:
        results["transitive_reduction"] = {"pass": False, "detail": f"raised: {exc}"}

    # --- 3. Dijkstra shortest path correctness ---
    # 0 --1--> 1 --1--> 3
    # 0 --4--> 3
    # 0 --2--> 2 --1--> 3
    sp_edges = [(0, 1, 1.0), (1, 3, 1.0), (0, 3, 4.0), (0, 2, 2.0), (2, 3, 1.0)]
    g_sp, _ = _build_rx_dag(sp_edges, 4)
    dists = rx.dijkstra_shortest_path_lengths(g_sp, 0, edge_cost_fn=lambda w: w)
    # dists is a mapping {node_index: length}
    dist_3 = dists[3] if 3 in dists else dists.get(3)
    results["dijkstra_01_3"] = {
        "pass": abs(dist_3 - 2.0) < 1e-9,
        "got": float(dist_3),
        "expected": 2.0,
        "detail": "shortest path 0->1->3 has length 2; 0->3 direct is 4",
    }

    # --- 4a. Cycle detection on known-acyclic graph ---
    results["acyclic_detection_positive"] = {
        "pass": bool(rx.is_directed_acyclic_graph(g_rx)),
        "detail": "diamond DAG must register as acyclic",
    }

    # --- 5. Actual-use witness: replay sim_foundation_shell_graph_topology DAG ---
    # Shell nesting chain L0 -> L1 -> L2 -> L3 -> L4 with branch L2 -> L3_alt
    shells = ["L0", "L1", "L2", "L3", "L4", "L3_alt"]
    shell_edges = [(0, 1, 1.0), (1, 2, 1.0), (2, 3, 1.0), (3, 4, 1.0), (2, 5, 1.0)]
    g_shell, _ = _build_rx_dag(shell_edges, len(shells))
    longest = int(rx.dag_longest_path_length(g_shell))
    shell_topo = list(rx.topological_sort(g_shell))
    results["witness_shell_nesting_dag"] = {
        "pass": (longest == 4)
                and _is_topo_valid(shell_topo, shell_edges)
                and bool(rx.is_directed_acyclic_graph(g_shell)),
        "longest_path_length": longest,
        "expected_longest": 4,
        "witness_file": "system_v4/probes/sim_foundation_shell_graph_topology.py",
        "detail": "Replays the shell-nesting DAG operations (PyDiGraph, topological_sort, "
                  "dag_longest_path_length, is_directed_acyclic_graph) used load-bearingly in the witness sim.",
    }
    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}
    if not RX_OK:
        results["rustworkx_available"] = {"pass": False, "detail": "rustworkx missing"}
        return results

    # --- 4b. Cycle detection on known-cyclic graph ---
    cyc_edges = [(0, 1, 1.0), (1, 2, 1.0), (2, 0, 1.0)]
    g_cyc = rx.PyDiGraph(check_cycle=False)
    for i in range(3):
        g_cyc.add_node(i)
    for u, v, w in cyc_edges:
        g_cyc.add_edge(u, v, float(w))
    results["cycle_detection_negative"] = {
        "pass": not rx.is_directed_acyclic_graph(g_cyc),
        "detail": "3-cycle must register as NOT acyclic",
    }

    # Topological sort on cyclic graph must raise.
    raised = False
    err_name = None
    try:
        rx.topological_sort(g_cyc)
    except Exception as exc:
        raised = True
        err_name = type(exc).__name__
    results["toposort_on_cycle_raises"] = {
        "pass": raised,
        "error_type": err_name,
        "detail": "rustworkx must refuse to linearize a cycle",
    }

    # Ill-formed input: adding an edge to a non-existent node index must raise.
    raised2 = False
    err2 = None
    try:
        g_bad = rx.PyDiGraph()
        g_bad.add_node(0)
        g_bad.add_edge(0, 999, 1.0)  # 999 does not exist
    except Exception as exc:
        raised2 = True
        err2 = type(exc).__name__
    results["ill_formed_edge_raises"] = {
        "pass": raised2,
        "error_type": err2,
        "detail": "edge to undefined node must raise",
    }
    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}
    if not RX_OK:
        results["rustworkx_available"] = {"pass": False, "detail": "rustworkx missing"}
        return results

    # Empty graph
    g_empty = rx.PyDiGraph()
    results["empty_graph_acyclic"] = {
        "pass": bool(rx.is_directed_acyclic_graph(g_empty)) and rx.topological_sort(g_empty) == [],
        "detail": "empty graph is vacuously acyclic with empty topo order",
    }

    # Singleton
    g_one = rx.PyDiGraph()
    g_one.add_node(0)
    results["singleton_graph"] = {
        "pass": list(rx.topological_sort(g_one)) == [0]
                and int(rx.dag_longest_path_length(g_one)) == 0,
        "detail": "single node: topo=[0], longest_path_length=0",
    }

    # Performance comparison vs NetworkX on a moderate random DAG (~1000 nodes).
    # Not load-bearing on its own -- reported for context.
    perf = {"pass": True}
    if NX_OK:
        rng = np.random.default_rng(0)
        N = 1000
        edges = []
        # Only forward edges (i<j) to guarantee acyclicity.
        for i in range(N):
            # ~3 outgoing edges per node on average
            targets = rng.integers(i + 1, N + 1, size=3)
            for j in targets:
                if j < N:
                    edges.append((int(i), int(j), 1.0))
        g_rx_big, _ = _build_rx_dag(edges, N)
        g_nx_big = _build_nx_dag(edges, N)

        t0 = time.perf_counter()
        order_rx = list(rx.topological_sort(g_rx_big))
        t1 = time.perf_counter()
        order_nx = list(nx.topological_sort(g_nx_big))
        t2 = time.perf_counter()

        rx_time = t1 - t0
        nx_time = t2 - t1
        # Both orderings must be topologically valid.
        rx_ok = _is_topo_valid(order_rx, edges)
        nx_ok = _is_topo_valid(order_nx, edges)
        perf = {
            "pass": rx_ok and nx_ok,
            "rx_time_s": rx_time,
            "nx_time_s": nx_time,
            "speedup_rx_over_nx": (nx_time / rx_time) if rx_time > 0 else None,
            "N_nodes": N,
            "M_edges": len(edges),
            "detail": "Both orderings must be valid; speedup reported for context, not load-bearing.",
        }
    else:
        perf = {"pass": True, "detail": "networkx missing; perf comparison skipped"}
    results["perf_vs_networkx_1k"] = perf

    return results


# =====================================================================
# MAIN
# =====================================================================

def _all_pass(section):
    return all(bool(v.get("pass", False)) for v in section.values())


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    summary = {
        "positive_all_pass": _all_pass(pos),
        "negative_all_pass": _all_pass(neg),
        "boundary_all_pass": _all_pass(bnd),
    }
    summary["all_pass"] = all(summary.values())

    results = {
        "name": "sim_rustworkx_capability",
        "purpose": "Tool-capability isolation probe for rustworkx -- unblocks its load-bearing use in ~25 sims.",
        "rustworkx_version": RX_VERSION,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
        "witness_file": "system_v4/probes/sim_foundation_shell_graph_topology.py",
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "rustworkx_capability_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"summary.all_pass = {summary['all_pass']}")
