#!/usr/bin/env python3
"""
tool_capability_toponetx.py

Tier A A0.5 tool-capability probe for TopoNetX.

Thin capability scope only: TopoNetX is the sole scientific tool in scope, and
all three test sections depend on its native cell-complex and simplicial-complex
APIs rather than on fallback graph helpers.
"""

import json
import os

classification = "canonical"
NAME = "tool_capability_toponetx"

TOOL_MANIFEST = {
    "toponetx": {
        "tried": False,
        "used": False,
        "reason": "TopoNetX is the sole topology library used to build complexes, inspect incidence structure, and exclude malformed cells in this isolated capability probe.",
    }
}

TOOL_INTEGRATION_DEPTH = {"toponetx": "load_bearing"}

try:
    from toponetx.classes import CellComplex, SimplicialComplex

    TOOL_MANIFEST["toponetx"]["tried"] = True
except ImportError:
    CellComplex = SimplicialComplex = None
    TOOL_MANIFEST["toponetx"]["reason"] = "TopoNetX import failed on this machine; queued runner execution will show whether the topology library is installed."


def _mark_toponetx_used() -> None:
    TOOL_MANIFEST["toponetx"]["used"] = True


def _dense_to_list(matrix):
    return matrix.astype(int).todense().tolist()


def _normalize_simplicial_nodes(nodes):
    normalized = []
    for node in nodes:
        if isinstance(node, frozenset) and len(node) == 1:
            normalized.append(next(iter(node)))
        else:
            normalized.append(sorted(node) if isinstance(node, frozenset) else node)
    return sorted(normalized)


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    if not TOOL_MANIFEST["toponetx"]["tried"]:
        results["toponetx_import_gate"] = {
            "status": "skipped",
            "reason": "TopoNetX not importable",
        }
        return results

    triangle = CellComplex()
    triangle.add_cell([1, 2, 3], rank=2)
    _mark_toponetx_used()
    results["triangle_cell_complex_survives"] = {
        "shape": list(triangle.shape),
        "dim": triangle.dim,
        "nodes": sorted(triangle.nodes),
        "edges": [list(edge) for edge in sorted(tuple(edge) for edge in triangle.edges)],
        "cells": [list(cell.elements) for cell in triangle.cells],
        "incidence_rank_2": _dense_to_list(triangle.incidence_matrix(2)),
        "expected_shape": [3, 3, 1],
        "shape_matches": list(triangle.shape) == [3, 3, 1],
    }

    simplicial = SimplicialComplex([[1, 2, 3], [2, 3, 4]])
    _mark_toponetx_used()
    results["two_triangles_share_edge"] = {
        "shape": list(simplicial.shape),
        "dim": simplicial.dim,
        "nodes": _normalize_simplicial_nodes(simplicial.nodes),
        "incidence_rank_2": _dense_to_list(simplicial.incidence_matrix(2)),
        "expected_shape": [4, 5, 2],
        "shape_matches": list(simplicial.shape) == [4, 5, 2],
        "shared_edge_present": [2, 3] in [list(simplex.elements) for simplex in simplicial.skeleton(1)],
    }

    hasse_graph = simplicial.to_hasse_graph()
    _mark_toponetx_used()
    results["hasse_graph_conversion_survives"] = {
        "node_count": hasse_graph.number_of_nodes(),
        "edge_count": hasse_graph.number_of_edges(),
        "expected_nodes": 11,
        "node_count_matches": hasse_graph.number_of_nodes() == 11,
        "edge_count_positive": hasse_graph.number_of_edges() > 0,
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    if not TOOL_MANIFEST["toponetx"]["tried"]:
        results["toponetx_import_gate"] = {
            "status": "skipped",
            "reason": "TopoNetX not importable",
        }
        return results

    irregular = CellComplex()
    try:
        irregular.add_cell([1, 2, 2], rank=2)
        status = "unexpected_success"
        detail = "irregular 2-cell was admitted"
    except ValueError as exc:
        _mark_toponetx_used()
        status = "value_error"
        detail = str(exc)
    results["duplicate_vertex_cell_excluded"] = {
        "status": status,
        "expected": "value_error",
        "detail": detail,
    }

    try:
        SimplicialComplex([[1, 1, 2]])
        status = "unexpected_success"
        detail = "simplex with duplicate nodes was admitted"
    except ValueError as exc:
        _mark_toponetx_used()
        status = "value_error"
        detail = str(exc)
    results["duplicate_node_simplex_excluded"] = {
        "status": status,
        "expected": "value_error",
        "detail": detail,
    }

    triangle = CellComplex()
    triangle.add_cell([1, 2, 3], rank=2)
    try:
        triangle.remove_cell([4, 5, 6])
        status = "unexpected_success"
        detail = "missing cell removal did not raise"
    except KeyError as exc:
        _mark_toponetx_used()
        status = "key_error"
        detail = str(exc)
    results["missing_cell_removal_excluded"] = {
        "status": status,
        "expected": "key_error",
        "detail": detail,
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    if not TOOL_MANIFEST["toponetx"]["tried"]:
        results["toponetx_import_gate"] = {
            "status": "skipped",
            "reason": "TopoNetX not importable",
        }
        return results

    empty = SimplicialComplex()
    _mark_toponetx_used()
    results["empty_complex_boundary"] = {
        "shape": list(empty.shape),
        "dim": empty.dim,
        "simplices": len(list(empty.simplices)),
        "expected_shape": [],
        "shape_matches": list(empty.shape) == [],
    }

    singleton = SimplicialComplex([[7]])
    _mark_toponetx_used()
    results["singleton_vertex_boundary"] = {
        "shape": list(singleton.shape),
        "dim": singleton.dim,
        "nodes": _normalize_simplicial_nodes(singleton.nodes),
        "expected_shape": [1],
        "shape_matches": list(singleton.shape) == [1],
    }

    degenerate_interval = CellComplex()
    degenerate_interval.add_cell([10, 11], rank=1)
    _mark_toponetx_used()
    results["single_edge_cell_boundary"] = {
        "shape": list(degenerate_interval.shape),
        "dim": degenerate_interval.dim,
        "edges": [list(edge) for edge in sorted(tuple(edge) for edge in degenerate_interval.edges)],
        "expected_shape": [2, 1, 0],
        "shape_matches": list(degenerate_interval.shape) == [2, 1, 0],
    }

    return results


if __name__ == "__main__":
    results = {
        "name": NAME,
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, sort_keys=True)
    print(f"Results written to {out_path}")
