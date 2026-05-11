#!/usr/bin/env python3
"""
Tier A A0x tool-capability probe for networkx.

Thin capability scope only: networkx is the sole manifested tool, and every
positive, negative, and boundary section depends on native graph construction
or graph-algorithm APIs that stop being meaningful if the library is removed.
"""

import json
import os

classification = "canonical"
NAME = "tool_capability_networkx"
SCOPE_NOTE = "Tier A networkx capability probe: isolated graph construction and graph-algorithm behavior only."

TOOL_MANIFEST = {
    "networkx": {
        "tried": False,
        "used": False,
        "reason": "networkx is the sole graph library used to admit weighted shortest-path, max-flow, connectivity, and boundary graph-behavior checks in every test section.",
    }
}

TOOL_INTEGRATION_DEPTH = {"networkx": "load_bearing"}
CANONICAL_TOOL_NAMES = (
    "pytorch",
    "pyg",
    "z3",
    "cvc5",
    "sympy",
    "clifford",
    "geomstats",
    "e3nn",
    "rustworkx",
    "xgi",
    "toponetx",
    "gudhi",
)
for _tool_name in CANONICAL_TOOL_NAMES:
    TOOL_MANIFEST.setdefault(
        _tool_name,
        {
            "tried": False,
            "used": False,
            "reason": f"not used; {NAME} isolates networkx capability only",
        },
    )
    TOOL_INTEGRATION_DEPTH.setdefault(_tool_name, None)


def _row_passes(row):
    if row.get("status") == "skipped":
        return False
    if "pass" in row:
        return bool(row["pass"])
    if "claim_excluded" in row:
        return bool(row["claim_excluded"])
    return False


def _section_passes(section):
    return bool(section) and all(_row_passes(row) for row in section.values())

try:
    import networkx as nx

    TOOL_MANIFEST["networkx"]["tried"] = True
except ImportError:
    nx = None
    TOOL_MANIFEST["networkx"]["reason"] = "networkx import failed on this machine; queued runner execution will show whether the graph library is installed."


def _mark_networkx_used() -> None:
    TOOL_MANIFEST["networkx"]["used"] = True


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    if not TOOL_MANIFEST["networkx"]["tried"]:
        results["networkx_import_gate"] = {
            "status": "skipped",
            "reason": "networkx not importable",
        }
        return results

    weighted = nx.Graph()
    weighted.add_weighted_edges_from(
        [
            ("s", "a", 2),
            ("a", "t", 2),
            ("s", "b", 1),
            ("b", "c", 1),
            ("c", "t", 5),
            ("a", "b", 2),
        ]
    )
    path = nx.shortest_path(weighted, source="s", target="t", weight="weight")
    length = nx.shortest_path_length(weighted, source="s", target="t", weight="weight")
    _mark_networkx_used()
    results["weighted_shortest_path_survives"] = {
        "path": path,
        "length": length,
        "expected": {"path": ["s", "a", "t"], "length": 4},
        "pass": path == ["s", "a", "t"] and length == 4,
    }

    flow_graph = nx.DiGraph()
    flow_graph.add_edge("s", "a", capacity=3)
    flow_graph.add_edge("s", "b", capacity=2)
    flow_graph.add_edge("a", "t", capacity=2)
    flow_graph.add_edge("b", "t", capacity=3)
    flow_graph.add_edge("a", "b", capacity=1)
    flow_value, flow_dict = nx.maximum_flow(flow_graph, "s", "t")
    _mark_networkx_used()
    results["maximum_flow_survives"] = {
        "flow_value": flow_value,
        "flow_dict": flow_dict,
        "expected": 5,
        "pass": flow_value == 5,
    }

    cycle_a = nx.cycle_graph(5)
    cycle_b = nx.relabel_nodes(nx.cycle_graph(5), {i: (i + 2) % 5 for i in range(5)})
    isomorphic = nx.is_isomorphic(cycle_a, cycle_b)
    _mark_networkx_used()
    results["cycle_relabel_isomorphism_survives"] = {
        "isomorphic": isomorphic,
        "expected": True,
        "pass": isomorphic is True,
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    if not TOOL_MANIFEST["networkx"]["tried"]:
        results["networkx_import_gate"] = {
            "status": "skipped",
            "reason": "networkx not importable",
        }
        return results

    disconnected = nx.Graph()
    disconnected.add_nodes_from([0, 1])
    try:
        nx.shortest_path(disconnected, source=0, target=1)
        status = "unexpected_success"
        detail = "path admitted in disconnected graph"
        claim_excluded = False
    except nx.NetworkXNoPath as exc:
        _mark_networkx_used()
        status = "no_path"
        detail = str(exc)
        claim_excluded = True
    results["disconnected_shortest_path_excluded"] = {
        "status": status,
        "detail": detail,
        "incorrect_claim": "a disconnected graph still admits a path between isolated nodes",
        "claim_excluded": claim_excluded,
    }

    isomorphic = nx.is_isomorphic(nx.cycle_graph(5), nx.path_graph(5))
    _mark_networkx_used()
    results["nonisomorphic_pair_excluded"] = {
        "isomorphic": isomorphic,
        "incorrect_claim": "cycle_graph(5) and path_graph(5) are structurally indistinguishable",
        "claim_excluded": isomorphic is False,
    }

    cyclic_digraph = nx.DiGraph([(0, 1), (1, 2), (2, 0)])
    try:
        list(nx.topological_sort(cyclic_digraph))
        topo_status = "unexpected_success"
        topo_detail = "cyclic graph admitted as DAG"
        topo_excluded = False
    except nx.NetworkXUnfeasible as exc:
        _mark_networkx_used()
        topo_status = "cycle_detected"
        topo_detail = str(exc)
        topo_excluded = True
    results["cyclic_graph_topological_order_excluded"] = {
        "status": topo_status,
        "detail": topo_detail,
        "incorrect_claim": "a directed 3-cycle admits a topological ordering",
        "claim_excluded": topo_excluded,
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    if not TOOL_MANIFEST["networkx"]["tried"]:
        results["networkx_import_gate"] = {
            "status": "skipped",
            "reason": "networkx not importable",
        }
        return results

    singleton = nx.Graph()
    singleton.add_node("solo")
    path = nx.shortest_path(singleton, source="solo", target="solo")
    _mark_networkx_used()
    results["singleton_shortest_path_boundary"] = {
        "path": path,
        "pass": path == ["solo"],
    }

    empty = nx.Graph()
    components = list(nx.connected_components(empty))
    _mark_networkx_used()
    results["empty_graph_boundary"] = {
        "nodes": empty.number_of_nodes(),
        "edges": empty.number_of_edges(),
        "components": components,
        "pass": empty.number_of_nodes() == 0 and empty.number_of_edges() == 0 and components == [],
    }

    zero_cut = nx.DiGraph()
    zero_cut.add_edge("s", "a", capacity=5)
    zero_cut.add_edge("a", "t", capacity=0)
    flow_value, flow_dict = nx.maximum_flow(zero_cut, "s", "t")
    _mark_networkx_used()
    results["zero_capacity_cut_boundary"] = {
        "flow_value": flow_value,
        "flow_dict": flow_dict,
        "pass": flow_value == 0,
    }

    return results


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    summary = {
        "positive_all_pass": _section_passes(positive),
        "negative_all_pass": _section_passes(negative),
        "boundary_all_pass": _section_passes(boundary),
        "promotion_allowed": False,
        "claim_ceiling": "isolated_networkx_capability_only",
        "scope_note": SCOPE_NOTE,
    }
    summary["all_pass"] = bool(summary["positive_all_pass"] and summary["negative_all_pass"] and summary["boundary_all_pass"])
    results = {
        "name": NAME,
        "classification": classification,
        "classification_note": SCOPE_NOTE,
        "divergence_log": SCOPE_NOTE,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, sort_keys=True)
    print(f"Results written to {out_path}")
