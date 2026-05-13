#!/usr/bin/env python3
"""
sim_rustworkx_transitive_reduction_collapse_fit.py

Bounded tool-lego fit probe for one rustworkx function surface:
PyDiGraph admissibility DAG construction, topological_sort, and
transitive_reduction.

This is local tool-lego fit evidence only. It checks whether a tiny
deterministic constraint-DAG can collapse redundant shortcut edges while
preserving reachability and topological admissibility. It does not promote a
lego, coupling, bridge, axis, GStack, QIT, or nonclassical claim.
"""

from __future__ import annotations

import json
import os
from collections import deque
from typing import Any

from receipt_boundary import apply_default_receipt_boundary


CLASSIFICATION = "tool_lego_fit_probe"
classification = CLASSIFICATION

TOOL_MANIFEST = {
    "pytorch": {
        "tried": False,
        "used": False,
        "reason": "not needed: this probe is finite DAG structure, not tensor dynamics",
    },
    "pyg": {
        "tried": False,
        "used": False,
        "reason": "not needed: no message-passing graph neural layer is tested",
    },
    "z3": {
        "tried": False,
        "used": False,
        "reason": "not needed: finite hand-enumerated reachability is the baseline",
    },
    "cvc5": {
        "tried": False,
        "used": False,
        "reason": "not needed: no SMT or SyGuS surface is exercised",
    },
    "sympy": {
        "tried": False,
        "used": False,
        "reason": "not needed: no symbolic algebra is part of the graph reduction check",
    },
    "clifford": {
        "tried": False,
        "used": False,
        "reason": "not needed: no Clifford, rotor, or geometric algebra object appears",
    },
    "geomstats": {
        "tried": False,
        "used": False,
        "reason": "not needed: no manifold metric or geodesic is tested",
    },
    "e3nn": {
        "tried": False,
        "used": False,
        "reason": "not needed: no equivariance or irreducible representation is tested",
    },
    "rustworkx": {
        "tried": False,
        "used": False,
        "reason": "under test: PyDiGraph, topological_sort, and transitive_reduction",
    },
    "xgi": {
        "tried": False,
        "used": False,
        "reason": "not needed: the fixture is a pairwise DAG, not a hypergraph",
    },
    "toponetx": {
        "tried": False,
        "used": False,
        "reason": "not needed: no cell-complex incidence or boundary operator is tested",
    },
    "gudhi": {
        "tried": False,
        "used": False,
        "reason": "not needed: no filtration or persistence computation is tested",
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
    RX_IMPORT_ERROR = None
    TOOL_MANIFEST["rustworkx"]["tried"] = True
except Exception as exc:  # pragma: no cover - dependency absence is a receipt state
    rx = None
    RX_AVAILABLE = False
    RX_VERSION = None
    RX_IMPORT_ERROR = f"{type(exc).__name__}: {exc}"
    TOOL_MANIFEST["rustworkx"]["reason"] = f"blocked: rustworkx unavailable ({RX_IMPORT_ERROR})"


NODES = [
    "raw_constraints",
    "admission_filter",
    "collapse_candidate",
    "collapsed_carrier",
    "observable_readout",
    "graveyard_reject",
]

EDGES = [
    ("raw_constraints", "admission_filter"),
    ("admission_filter", "collapse_candidate"),
    ("collapse_candidate", "collapsed_carrier"),
    ("collapsed_carrier", "observable_readout"),
    ("raw_constraints", "collapse_candidate"),
    ("admission_filter", "collapsed_carrier"),
    ("raw_constraints", "observable_readout"),
    ("graveyard_reject", "observable_readout"),
]

EXPECTED_REDUCED_EDGES = {
    ("raw_constraints", "admission_filter"),
    ("admission_filter", "collapse_candidate"),
    ("collapse_candidate", "collapsed_carrier"),
    ("collapsed_carrier", "observable_readout"),
    ("graveyard_reject", "observable_readout"),
}

REDUNDANT_EDGES = {
    ("raw_constraints", "collapse_candidate"),
    ("admission_filter", "collapsed_carrier"),
    ("raw_constraints", "observable_readout"),
}


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


def _manual_reachability(edges: list[tuple[str, str]], nodes: list[str]) -> dict[str, list[str]]:
    return {node: sorted(_manual_descendants(edges, node)) for node in nodes}


def _build_graph(edges: list[tuple[str, str]] = EDGES, nodes: list[str] = NODES):
    assert rx is not None, "rustworkx is required"
    graph = rx.PyDiGraph(check_cycle=True)
    node_ids = {name: graph.add_node(name) for name in nodes}
    for left, right in edges:
        graph.add_edge(node_ids[left], node_ids[right], {"edge": f"{left}->{right}"})
    return graph, node_ids


def _edge_names(graph: Any) -> set[tuple[str, str]]:
    return {(graph[left], graph[right]) for left, right in graph.edge_list()}


def _topological_names(graph: Any) -> list[str]:
    assert rx is not None, "rustworkx is required"
    return [graph[index] for index in rx.topological_sort(graph)]


def _has_transitive_reduction() -> bool:
    return bool(RX_AVAILABLE and hasattr(rx, "transitive_reduction"))


def _reduce_graph(graph: Any):
    assert rx is not None, "rustworkx is required"
    reduced = rx.transitive_reduction(graph)
    if isinstance(reduced, tuple):
        return reduced[0]
    return reduced


def run_positive_tests() -> dict[str, dict[str, Any]]:
    if not _has_transitive_reduction():
        return {
            "rustworkx_transitive_reduction_available": {
                "pass": False,
                "status": "blocked",
                "detail": "rustworkx or rustworkx.transitive_reduction is unavailable",
            }
        }

    graph, _node_ids = _build_graph()
    reduced = _reduce_graph(graph)
    topo = _topological_names(graph)
    reduced_edges = _edge_names(reduced)
    original_reachability = _manual_reachability(EDGES, NODES)
    reduced_reachability = _manual_reachability(sorted(reduced_edges), NODES)

    return {
        "topological_sort_respects_constraint_order": {
            "pass": topo.index("raw_constraints") < topo.index("admission_filter")
            < topo.index("collapse_candidate") < topo.index("collapsed_carrier")
            < topo.index("observable_readout"),
            "topological_order": topo,
        },
        "transitive_reduction_matches_expected_minimal_dag": {
            "pass": reduced_edges == EXPECTED_REDUCED_EDGES,
            "reduced_edges": sorted(reduced_edges),
            "expected_reduced_edges": sorted(EXPECTED_REDUCED_EDGES),
        },
        "collapse_preserves_reachability": {
            "pass": original_reachability == reduced_reachability,
            "original_reachability": original_reachability,
            "reduced_reachability": reduced_reachability,
        },
    }


def run_negative_tests() -> dict[str, dict[str, Any]]:
    if not _has_transitive_reduction():
        return {
            "rustworkx_transitive_reduction_available": {
                "pass": False,
                "status": "blocked",
                "detail": "rustworkx or rustworkx.transitive_reduction is unavailable",
            }
        }

    graph, _node_ids = _build_graph()
    reduced = _reduce_graph(graph)
    reduced_edges = _edge_names(reduced)

    cycle_blocked = False
    cycle_error = None
    try:
        cyclic, node_ids = _build_graph(
            edges=[("raw_constraints", "admission_filter"), ("admission_filter", "raw_constraints")],
            nodes=["raw_constraints", "admission_filter"],
        )
        _ = cyclic, node_ids
    except rx.DAGWouldCycle as exc:
        cycle_blocked = True
        cycle_error = f"{type(exc).__name__}: {exc}"

    return {
        "redundant_shortcut_edges_removed": {
            "pass": not (REDUNDANT_EDGES & reduced_edges),
            "removed_edges": sorted(REDUNDANT_EDGES - reduced_edges),
            "still_present": sorted(REDUNDANT_EDGES & reduced_edges),
        },
        "non_redundant_graveyard_edge_retained": {
            "pass": ("graveyard_reject", "observable_readout") in reduced_edges,
            "detail": "graveyard edge has no alternate path and must not be collapsed away",
        },
        "cyclic_admissibility_fixture_rejected": {
            "pass": cycle_blocked,
            "error_type": cycle_error,
            "detail": "checked PyDiGraph must reject a cycle before reduction is trusted",
        },
    }


def run_boundary_tests() -> dict[str, dict[str, Any]]:
    if not _has_transitive_reduction():
        return {
            "rustworkx_transitive_reduction_available": {
                "pass": False,
                "status": "blocked",
                "detail": "rustworkx or rustworkx.transitive_reduction is unavailable",
            }
        }

    diamond_edges = [
        ("root", "left"),
        ("root", "right"),
        ("left", "sink"),
        ("right", "sink"),
    ]
    diamond, _node_ids = _build_graph(
        edges=diamond_edges,
        nodes=["root", "left", "right", "sink"],
    )
    diamond_reduced = _reduce_graph(diamond)
    diamond_reduced_edges = _edge_names(diamond_reduced)

    singleton, _single_ids = _build_graph(edges=[], nodes=["only"])
    singleton_reduced = _reduce_graph(singleton)

    return {
        "diamond_parallel_paths_are_not_collapsed_into_one_parent": {
            "pass": diamond_reduced_edges == set(diamond_edges),
            "reduced_edges": sorted(diamond_reduced_edges),
            "detail": "parallel admissibility parents are both load-bearing; neither edge is transitive",
        },
        "singleton_boundary_survives_as_zero_edge_graph": {
            "pass": list(singleton_reduced.node_indices()) == [0] and list(singleton_reduced.edge_list()) == [],
            "node_count": len(list(singleton_reduced.node_indices())),
            "edge_count": len(list(singleton_reduced.edge_list())),
        },
    }


def _all_pass(section: dict[str, dict[str, Any]]) -> bool:
    return all(bool(item.get("pass", False)) for item in section.values())


def _base_receipt(status: str, positive: dict[str, Any], negative: dict[str, Any], boundary: dict[str, Any]):
    summary = {
        "status": status,
        "positive_all_pass": _all_pass(positive),
        "negative_all_pass": _all_pass(negative),
        "boundary_all_pass": _all_pass(boundary),
    }
    summary["all_pass"] = status == "ok" and all(
        [summary["positive_all_pass"], summary["negative_all_pass"], summary["boundary_all_pass"]]
    )
    summary["promotion_allowed"] = False
    summary["claim_ceiling"] = "local rustworkx constraint-DAG transitive-reduction tool-lego fit only"

    receipt = {
        "name": "sim_rustworkx_transitive_reduction_collapse_fit",
        "probe_family": "M_rustworkx_transitive_reduction_collapse_fit",
        "constraint_set": "C_tiny_admissibility_dag_redundant_edge_collapse",
        "classification": CLASSIFICATION,
        "status": status,
        "rustworkx_version": RX_VERSION,
        "rustworkx_import_error": RX_IMPORT_ERROR,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "operation_sequence": [
            "construct checked rustworkx.PyDiGraph from deterministic admissibility-DAG fixture",
            "run rustworkx.topological_sort to verify admissible dependency order",
            "run rustworkx.transitive_reduction to collapse redundant shortcut edges",
            "compare reduced DAG reachability against hand-enumerated finite baseline",
        ],
        "carrier_topology": {
            "carrier": "finite directed acyclic graph",
            "nodes": NODES,
            "edges": EDGES,
            "topology": "diamond-plus-chain admissibility DAG with one graveyard readout edge",
        },
        "observable": "minimal edge set after transitive reduction plus preserved reachability relation",
        "pass_fail_predicate": (
            "pass iff topological_sort respects the admissibility chain, transitive_reduction removes exactly "
            "the redundant shortcut edges, reachability is unchanged, graveyard/nonredundant edges remain, "
            "cycle input is rejected, and boundary fixtures behave as named"
        ),
        "graveyards": [
            {
                "name": "graveyard_reject",
                "role": "excluded/rejected state that still has a direct observable readout edge",
                "predicate": "edge must remain because no alternate path exists",
            }
        ],
        "baselines": [
            "hand-enumerated BFS reachability over the same finite edge list",
            "explicit expected reduced-edge set for the tiny fixture",
        ],
        "alternative_formulations": [
            "NetworkX transitive_reduction could provide a classical cross-check in a separate receipt",
            "TopoNetX Hasse/cell-complex carriers remain separate topology-lego formulations",
            "XGI hypergraph incidence is not represented by this pairwise DAG fixture",
        ],
        "exact_tool_function_needs": [
            "rustworkx.PyDiGraph(check_cycle=True)",
            "rustworkx.topological_sort",
            "rustworkx.transitive_reduction",
        ],
        "lego_coupling_target": (
            "dependency_dag_and_collapse / graph_shell_geometry fit target only; no coupling target is admitted"
        ),
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "surviving_alternatives": [
            "A downstream graph-cell lego could use this as a parent only after its own admitted receipt.",
            "NetworkX or TopoNetX formulations could disagree and would need separate receipts.",
        ],
        "criteria_checked": [
            "C1 topological order is compatible with the admissibility dependency chain",
            "C2 transitive reduction removes exactly redundant shortcut edges",
            "C3 reachability before and after reduction is identical under a finite baseline",
            "C4 nonredundant graveyard edge is retained",
            "C5 cycle and boundary fixtures are explicit",
        ],
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
        "claim_ceiling": "local rustworkx constraint-DAG transitive-reduction tool-lego fit only",
        "promotion_allowed": False,
        "next_lego_target": "none",
        "promotion_condition": (
            "promotion_allowed is false; requires a separate admitted downstream lego/coupling receipt "
            "with exact parent references before any promotion is considered"
        ),
        "blocked_until": (
            "blocked from lego, coupling, bridge, axis, GStack, QIT, and nonclassical admission until "
            "separate downstream stage-gate receipts exist"
        ),
        "demotion_condition": (
            "demote if rustworkx topological_sort or transitive_reduction output changes, if reachability "
            "is not preserved, if any redundant edge remains, or if any claim exceeds local tool-lego fit"
        ),
        "out_of_scope": [
            "no lego promotion",
            "no tool-tool coupling",
            "no QIT claim",
            "no GStack claim",
            "no axis claim",
            "no bridge claim",
            "no nonclassical admission",
            "no whole-rustworkx proof",
        ],
    }
    return apply_default_receipt_boundary(
        receipt,
        source_name="sim_rustworkx_transitive_reduction_collapse_fit",
        target="none",
    )


if __name__ == "__main__":
    if _has_transitive_reduction():
        TOOL_MANIFEST["rustworkx"]["used"] = True
        TOOL_MANIFEST["rustworkx"]["reason"] = (
            "load-bearing: PyDiGraph, topological_sort, and transitive_reduction determine "
            "the admissibility-DAG collapse predicate"
        )
        status = "ok"
    else:
        status = "blocked"

    positive_results = run_positive_tests()
    negative_results = run_negative_tests()
    boundary_results = run_boundary_tests()
    results = _base_receipt(status, positive_results, negative_results, boundary_results)

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_rustworkx_transitive_reduction_collapse_fit_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=str)

    print(f"Results written to {out_path}")
    print(f"summary.status = {results['summary']['status']}")
    print(f"summary.all_pass = {results['summary']['all_pass']}")
