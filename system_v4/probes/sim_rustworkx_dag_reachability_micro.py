#!/usr/bin/env python3
"""
sim_rustworkx_dag_reachability_micro.py

Tool-stage MICRO probe for one rustworkx function surface:
PyDiGraph reachability via rustworkx.has_path, rustworkx.descendants, and
rustworkx.ancestors.

This is a probe, not a proof of downstream graph-cell geometry. It isolates
whether rustworkx can certify bounded DAG reachability and non-reachability
before a later tool-lego or tool-tool coupling row relies on that surface.

Do not execute this file from authoring lanes unless the Tier A runner has
admitted the matching MICRO queue row.
"""

from __future__ import annotations

import json
import os
from collections import deque

from receipt_boundary import apply_default_receipt_boundary


classification = "canonical"

MICRO_PACKET = {
    "tool_target": "rustworkx",
    "function_surface": "PyDiGraph + has_path/descendants/ancestors over bounded DAG reachability",
    "micro_claim": (
        "rustworkx can decide direct, transitive, absent, and cycle-blocked "
        "reachability on a tiny dependency DAG."
    ),
    "lego_target": "minimal shell dependency DAG fixture before graph-cell lego promotion",
    "function_receipt": "new",
    "prior_function_receipts": [],
    "why_this_lego": (
        "the fixture isolates dependency reachability used by shell/order sims "
        "without adding hypergraph, topology, or bridge semantics"
    ),
    "positive_case": "source reaches all downstream shell nodes through direct and transitive edges",
    "negative_case": "a leaf cannot reach its ancestor and an isolated node is unreachable",
    "boundary_case": (
        "empty and singleton DAGs have no descendants/ancestors; rustworkx.has_path "
        "does not admit zero-edge singleton self paths; checked DAG rejects a cycle"
    ),
    "demotion_condition": (
        "demote if has_path, descendants, or ancestors disagree with a hand-written BFS "
        "baseline on any bounded fixture"
    ),
    "out_of_scope": [
        "lego promotion",
        "tool-tool coupling",
        "hypergraph incidence",
        "bridge claim",
        "whole-library proof",
    ],
}

TOOL_MANIFEST = {
    "pytorch": {
        "tried": False,
        "used": False,
        "reason": "not needed: this MICRO isolates graph reachability, not tensor dynamics",
    },
    "pyg": {
        "tried": False,
        "used": False,
        "reason": "not needed: no message-passing or differentiable graph layer is tested",
    },
    "z3": {
        "tried": False,
        "used": False,
        "reason": "not needed: finite hand-enumerated BFS baseline is the comparison oracle",
    },
    "cvc5": {
        "tried": False,
        "used": False,
        "reason": "not needed: no SMT witness extraction is required for this MICRO",
    },
    "sympy": {
        "tried": False,
        "used": False,
        "reason": "not needed: the claim is graph reachability, not symbolic algebra",
    },
    "clifford": {
        "tried": False,
        "used": False,
        "reason": "not needed: no geometric algebra object appears in this fixture",
    },
    "geomstats": {
        "tried": False,
        "used": False,
        "reason": "not needed: no manifold metric or geodesic is tested",
    },
    "e3nn": {
        "tried": False,
        "used": False,
        "reason": "not needed: no equivariance or irrep computation is tested",
    },
    "rustworkx": {
        "tried": False,
        "used": False,
        "reason": "under test: PyDiGraph reachability via has_path, descendants, and ancestors",
    },
    "xgi": {
        "tried": False,
        "used": False,
        "reason": "not needed: this is pairwise DAG reachability, not higher-order incidence",
    },
    "toponetx": {
        "tried": False,
        "used": False,
        "reason": "not needed: no cell-complex boundary operator is tested",
    },
    "gudhi": {
        "tried": False,
        "used": False,
        "reason": "not needed: no persistence or filtration is tested",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": "load_bearing",
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

try:
    import rustworkx as rx

    RX_AVAILABLE = True
    RX_VERSION = getattr(rx, "__version__", "unknown")
    TOOL_MANIFEST["rustworkx"]["tried"] = True
except Exception as exc:  # pragma: no cover - runner records dependency absence
    rx = None
    RX_AVAILABLE = False
    RX_VERSION = None
    TOOL_MANIFEST["rustworkx"]["reason"] = f"not installed: {exc}"


SHELLS = ["source", "admit_A", "admit_B", "merge", "sink", "isolated"]
EDGES = [
    ("source", "admit_A"),
    ("source", "admit_B"),
    ("admit_A", "merge"),
    ("admit_B", "merge"),
    ("merge", "sink"),
]


def _manual_descendants(edges: list[tuple[str, str]], source: str) -> set[str]:
    graph: dict[str, list[str]] = {}
    for left, right in edges:
        graph.setdefault(left, []).append(right)

    seen: set[str] = set()
    queue = deque(graph.get(source, []))
    while queue:
        node = queue.popleft()
        if node in seen:
            continue
        seen.add(node)
        queue.extend(graph.get(node, []))
    return seen


def _manual_has_path(edges: list[tuple[str, str]], source: str, target: str) -> bool:
    if source == target:
        return True
    return target in _manual_descendants(edges, source)


def _manual_ancestors(edges: list[tuple[str, str]], target: str) -> set[str]:
    return {node for node in SHELLS if node != target and _manual_has_path(edges, node, target)}


def _build_dag(edges: list[tuple[str, str]] = EDGES, nodes: list[str] = SHELLS):
    assert rx is not None, "rustworkx is required"
    graph = rx.PyDiGraph(check_cycle=True)
    node_ids = {name: graph.add_node(name) for name in nodes}
    for left, right in edges:
        graph.add_edge(node_ids[left], node_ids[right], {"edge": f"{left}->{right}"})
    return graph, node_ids, {idx: name for name, idx in node_ids.items()}


def _rx_descendant_names(graph, node_ids: dict[str, int], id_to_name: dict[int, str], source: str) -> set[str]:
    return {id_to_name[node_id] for node_id in rx.descendants(graph, node_ids[source])}


def _rx_ancestor_names(graph, node_ids: dict[str, int], id_to_name: dict[int, str], target: str) -> set[str]:
    return {id_to_name[node_id] for node_id in rx.ancestors(graph, node_ids[target])}


def run_positive_tests():
    results = {}
    if not RX_AVAILABLE:
        return {"rustworkx_available": {"pass": False, "detail": "rustworkx missing"}}

    graph, node_ids, id_to_name = _build_dag()
    rx_desc = _rx_descendant_names(graph, node_ids, id_to_name, "source")
    manual_desc = _manual_descendants(EDGES, "source")
    rx_ancestors = _rx_ancestor_names(graph, node_ids, id_to_name, "sink")
    manual_ancestors = _manual_ancestors(EDGES, "sink")
    direct_path = bool(rx.has_path(graph, node_ids["source"], node_ids["admit_A"]))
    transitive_path = bool(rx.has_path(graph, node_ids["source"], node_ids["sink"]))

    results["source_descendants_match_manual_bfs"] = {
        "pass": rx_desc == manual_desc,
        "rustworkx_descendants": sorted(rx_desc),
        "manual_descendants": sorted(manual_desc),
        "detail": "source must reach both branches, merge, and sink, but not isolated",
    }
    results["direct_and_transitive_paths_exist"] = {
        "pass": direct_path and transitive_path,
        "direct_source_to_admit_A": direct_path,
        "transitive_source_to_sink": transitive_path,
    }
    results["sink_ancestors_match_manual_bfs"] = {
        "pass": rx_ancestors == manual_ancestors,
        "rustworkx_ancestors": sorted(rx_ancestors),
        "manual_ancestors": sorted(manual_ancestors),
        "detail": "sink must have source, both branch nodes, and merge as ancestors",
    }
    return results


def run_negative_tests():
    results = {}
    if not RX_AVAILABLE:
        return {"rustworkx_available": {"pass": False, "detail": "rustworkx missing"}}

    graph, node_ids, id_to_name = _build_dag()
    reverse_path = bool(rx.has_path(graph, node_ids["sink"], node_ids["source"]))
    isolated_path = bool(rx.has_path(graph, node_ids["source"], node_ids["isolated"]))
    leaf_desc = _rx_descendant_names(graph, node_ids, id_to_name, "sink")
    source_ancestors = _rx_ancestor_names(graph, node_ids, id_to_name, "source")

    results["leaf_cannot_reach_ancestor"] = {
        "pass": not reverse_path,
        "sink_to_source": reverse_path,
        "manual_sink_to_source": _manual_has_path(EDGES, "sink", "source"),
    }
    results["isolated_node_excluded_from_reachability"] = {
        "pass": not isolated_path and "isolated" not in _manual_descendants(EDGES, "source"),
        "source_to_isolated": isolated_path,
    }
    results["leaf_has_no_descendants"] = {
        "pass": leaf_desc == set(),
        "sink_descendants": sorted(leaf_desc),
    }
    results["source_has_no_ancestors"] = {
        "pass": source_ancestors == set(),
        "source_ancestors": sorted(source_ancestors),
    }
    return results


def run_boundary_tests():
    results = {}
    if not RX_AVAILABLE:
        return {"rustworkx_available": {"pass": False, "detail": "rustworkx missing"}}

    empty = rx.PyDiGraph(check_cycle=True)
    singleton = rx.PyDiGraph(check_cycle=True)
    only = singleton.add_node("only")

    cycle_blocked = False
    cycle_error = None
    try:
        cyclic = rx.PyDiGraph(check_cycle=True)
        a = cyclic.add_node("a")
        b = cyclic.add_node("b")
        cyclic.add_edge(a, b, None)
        cyclic.add_edge(b, a, None)
    except rx.DAGWouldCycle as exc:
        cycle_blocked = True
        cycle_error = f"{type(exc).__name__}: {exc}"

    results["empty_graph_has_no_descendants"] = {
        "pass": len(list(empty.node_indices())) == 0,
        "node_count": len(list(empty.node_indices())),
    }
    results["singleton_self_path_only"] = {
        "pass": (
            not bool(rx.has_path(singleton, only, only))
            and list(rx.descendants(singleton, only)) == []
            and list(rx.ancestors(singleton, only)) == []
        ),
        "self_path": bool(rx.has_path(singleton, only, only)),
        "descendants": list(rx.descendants(singleton, only)),
        "ancestors": list(rx.ancestors(singleton, only)),
        "detail": "rustworkx.has_path does not admit a zero-edge singleton self path",
    }
    results["cycle_input_blocked_by_checked_dag"] = {
        "pass": cycle_blocked,
        "error_type": cycle_error,
        "detail": "check_cycle=True must prevent accepting a cyclic dependency fixture",
    }
    return results


def _all_pass(section: dict) -> bool:
    return all(bool(item.get("pass", False)) for item in section.values())


if __name__ == "__main__":
    if RX_AVAILABLE:
        TOOL_MANIFEST["rustworkx"]["used"] = True
        TOOL_MANIFEST["rustworkx"]["reason"] = (
            "load-bearing: has_path, descendants, and ancestors decide every reachability "
            "admission, exclusion, and boundary result"
        )

    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    summary = {
        "positive_all_pass": _all_pass(positive),
        "negative_all_pass": _all_pass(negative),
        "boundary_all_pass": _all_pass(boundary),
    }
    summary["all_pass"] = all(summary.values())

    results = {
        "name": "sim_rustworkx_dag_reachability_micro",
        "probe_family": "M_rustworkx_dag_reachability",
        "constraint_set": "C_bounded_dag_reachability",
        "micro_packet": MICRO_PACKET,
        "operation_sequence": [
            "construct a checked rustworkx PyDiGraph over six named dependency nodes",
            "add directed acyclic edges from source through two branch nodes, merge, and sink",
            "query has_path for direct, transitive, reverse, and isolated-node reachability",
            "query descendants and ancestors for source, sink, and boundary nodes",
            "compare rustworkx reachability sets against a hand-written BFS baseline",
            "run empty-graph, singleton, and cycle-blocked boundary controls",
        ],
        "carrier_topology": (
            "finite directed acyclic graph fixture with named dependency nodes; "
            "no hypergraph, cell complex, manifold, bridge, axis, GStack, QIT engine, or nonclassical claim"
        ),
        "observable": (
            "boolean has_path answers, descendant sets, ancestor sets, node counts, "
            "cycle rejection exception, and equality against manual BFS reachability"
        ),
        "pass_fail_predicate": (
            "rustworkx direct/transitive reachability and ancestor/descendant sets must "
            "match the manual BFS baseline; reverse and isolated reachability must be "
            "excluded; empty, singleton, and cycle-blocked boundaries must behave as declared"
        ),
        "graveyards": [
            "leaf-to-ancestor reachability must be false",
            "source-to-isolated reachability must be false",
            "checked PyDiGraph must reject a cycle insertion",
            "singleton graph must not be treated as a zero-edge self-path proof",
        ],
        "baselines": [
            "hand-written BFS descendant and ancestor computation",
            "empty graph node-count boundary",
            "singleton graph ancestor/descendant boundary",
        ],
        "alternative_formulations": [
            "NetworkX directed graph reachability baseline",
            "z3 encoding of finite transitive closure for the same DAG fixture",
            "rustworkx transitive reduction or topological-sort packet as a later separate function surface",
        ],
        "tool_function_needs": {
            "rustworkx": ["PyDiGraph", "has_path", "descendants", "ancestors", "DAGWouldCycle"],
        },
        "lego_coupling_target": "bounded rustworkx graph-shell reachability fixture before graph-cell lego promotion",
        "rustworkx_version": RX_VERSION,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": classification,
        "surviving_alternatives": [
            "NetworkX can cross-check pairwise graph reachability as a classical baseline.",
            "XGI remains the better target for higher-order hyperedge incidence.",
        ],
        "criteria_checked": [
            "C1 direct reachability agrees with fixture edges",
            "C2 transitive descendants and ancestors agree with hand-written BFS",
            "C3 reverse and isolated reachability are excluded",
            "C4 empty, singleton, and cycle-blocked boundaries are explicit",
        ],
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
        "claim_ceiling": "tool_lego_fit_probe_only",
        "next_lego_target": "bounded rustworkx graph-shell reachability fixture before graph-cell lego promotion",
        "promotion_condition": (
            "requires later admitted graph-cell or dependency-DAG lego rows with exact parent receipts and stage-gate approval; "
            "this receipt does not promote graph-cell geometry, bridge, axis, GStack, QIT engine, or nonclassical claims"
        ),
        "blocked_until": (
            "blocked from graph-cell lego promotion, bridge, axis, GStack, QIT engine, and nonclassical promotion until exact "
            "parent receipts and downstream admission packets pass strict validation"
        ),
        "demotion_condition": (
            "Demote this rustworkx reachability surface if PyDiGraph has_path, descendants, or ancestors disagree with the "
            "hand-written BFS baseline on any positive, negative, or boundary fixture."
        ),
        "out_of_scope": [
            "no graph-cell lego promotion",
            "no bridge, axis, GStack, QIT engine, or nonclassical admission",
            "no hypergraph incidence or cell-complex boundary claim",
            "no proof of the whole rustworkx library",
            "no replacement for downstream graph-cell or dependency-DAG receipts",
        ],
    }
    results = apply_default_receipt_boundary(
        results,
        source_name="sim_rustworkx_dag_reachability_micro",
    )

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_rustworkx_dag_reachability_micro_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"summary.all_pass = {summary['all_pass']}")
    if not summary["all_pass"]:
        raise SystemExit(1)
