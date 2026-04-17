#!/usr/bin/env python3
"""
Tier A A0x tool-capability probe for gudhi.

Thin capability scope only: gudhi is the only manifested tool, and every test
section depends on native simplicial-complex, persistence, or Rips-complex APIs
that stop being meaningful if the library is removed.
"""

import json
import math
import os

classification = "canonical"
NAME = "tool_capability_gudhi"

TOOL_MANIFEST = {
    "gudhi": {
        "tried": False,
        "used": False,
        "reason": "gudhi is the sole topology library used to build simplex trees, compute persistence, and exclude malformed insertions in every test section.",
    }
}

TOOL_INTEGRATION_DEPTH = {"gudhi": "load_bearing"}

try:
    import gudhi

    TOOL_MANIFEST["gudhi"]["tried"] = True
except ImportError:
    gudhi = None
    TOOL_MANIFEST["gudhi"]["reason"] = "gudhi import failed on this machine; queued runner execution will show whether the topology library is installed."


def _mark_gudhi_used() -> None:
    TOOL_MANIFEST["gudhi"]["used"] = True


def _clean_number(value):
    if isinstance(value, float):
        if math.isinf(value):
            return "inf" if value > 0 else "-inf"
        if value.is_integer():
            return int(value)
    return value


def _serialize_intervals(intervals):
    return [[_clean_number(float(start)), _clean_number(float(end))] for start, end in intervals]


def _serialize_filtration(simplex_tree):
    return [{"simplex": list(simplex), "filtration": _clean_number(float(filtration))} for simplex, filtration in simplex_tree.get_filtration()]


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    if not TOOL_MANIFEST["gudhi"]["tried"]:
        results["gudhi_import_gate"] = {
            "status": "skipped",
            "reason": "gudhi not importable",
        }
        return results

    interval = gudhi.SimplexTree()
    interval.insert([0], filtration=0.0)
    interval.insert([1], filtration=0.0)
    interval.insert([0, 1], filtration=1.0)
    interval.compute_persistence()
    _mark_gudhi_used()
    results["interval_persistence_survives"] = {
        "num_vertices": interval.num_vertices(),
        "num_simplices": interval.num_simplices(),
        "dimension": interval.dimension(),
        "betti_numbers": interval.betti_numbers(),
        "intervals_dim_0": _serialize_intervals(interval.persistence_intervals_in_dimension(0)),
        "filtration": _serialize_filtration(interval),
        "expected": {
            "num_vertices": 2,
            "num_simplices": 3,
            "dimension": 1,
            "betti_numbers": [1],
        },
        "pass": interval.num_vertices() == 2 and interval.num_simplices() == 3 and interval.dimension() == 1 and interval.betti_numbers() == [1],
    }

    filled_triangle = gudhi.SimplexTree()
    filled_triangle.insert([0, 1, 2], filtration=2.0)
    filled_triangle.compute_persistence()
    _mark_gudhi_used()
    results["filled_triangle_survives_as_contractible_complex"] = {
        "num_vertices": filled_triangle.num_vertices(),
        "num_simplices": filled_triangle.num_simplices(),
        "dimension": filled_triangle.dimension(),
        "betti_numbers": filled_triangle.betti_numbers(),
        "filtration": _serialize_filtration(filled_triangle),
        "expected": {
            "num_vertices": 3,
            "num_simplices": 7,
            "dimension": 2,
            "betti_numbers": [1, 0],
        },
        "pass": filled_triangle.num_vertices() == 3 and filled_triangle.num_simplices() == 7 and filled_triangle.dimension() == 2 and filled_triangle.betti_numbers() == [1, 0],
    }

    rips = gudhi.RipsComplex(points=[[0.0], [1.0], [3.0]], max_edge_length=1.1)
    threshold_complex = rips.create_simplex_tree(max_dimension=2)
    threshold_complex.compute_persistence()
    _mark_gudhi_used()
    results["rips_threshold_admits_only_close_pair"] = {
        "num_vertices": threshold_complex.num_vertices(),
        "num_simplices": threshold_complex.num_simplices(),
        "dimension": threshold_complex.dimension(),
        "betti_numbers": threshold_complex.betti_numbers(),
        "intervals_dim_0": _serialize_intervals(threshold_complex.persistence_intervals_in_dimension(0)),
        "filtration": _serialize_filtration(threshold_complex),
        "expected": {
            "num_vertices": 3,
            "num_simplices": 4,
            "dimension": 1,
            "betti_numbers": [2],
        },
        "pass": threshold_complex.num_vertices() == 3 and threshold_complex.num_simplices() == 4 and threshold_complex.dimension() == 1 and threshold_complex.betti_numbers() == [2],
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    if not TOOL_MANIFEST["gudhi"]["tried"]:
        results["gudhi_import_gate"] = {
            "status": "skipped",
            "reason": "gudhi not importable",
        }
        return results

    simplex_tree = gudhi.SimplexTree()
    simplex_tree.insert([0, 1], filtration=1.0)
    second_insert = simplex_tree.insert([0, 1], filtration=2.0)
    _mark_gudhi_used()
    results["duplicate_simplex_reinsertion_excluded"] = {
        "first_filtration": _clean_number(float(simplex_tree.filtration([0, 1]))),
        "second_insert_returned": second_insert,
        "incorrect_claim": "reinserting an existing simplex at a higher filtration admits a new simplex",
        "claim_excluded": second_insert is False and simplex_tree.filtration([0, 1]) == 1.0,
    }

    bad_labels = gudhi.SimplexTree()
    try:
        bad_labels.insert(["a"], filtration=0.0)
        status = "unexpected_success"
        detail = "string vertex label was admitted"
    except TypeError as exc:
        _mark_gudhi_used()
        status = "type_error"
        detail = str(exc)
    results["non_integer_vertex_label_excluded"] = {
        "status": status,
        "expected": "type_error",
        "detail": detail,
    }

    disconnected = gudhi.RipsComplex(points=[[0.0], [1.0], [3.0]], max_edge_length=0.9)
    disconnected_tree = disconnected.create_simplex_tree(max_dimension=2)
    disconnected_tree.compute_persistence()
    _mark_gudhi_used()
    results["tight_threshold_excludes_long_edge"] = {
        "num_simplices": disconnected_tree.num_simplices(),
        "dimension": disconnected_tree.dimension(),
        "betti_numbers": disconnected_tree.betti_numbers(),
        "filtration": _serialize_filtration(disconnected_tree),
        "incorrect_claim": "the 0.9 threshold still admits a 1-simplex between points at distance 1.0",
        "claim_excluded": disconnected_tree.num_simplices() == 3 and disconnected_tree.dimension() == 0 and disconnected_tree.betti_numbers() == [],
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    if not TOOL_MANIFEST["gudhi"]["tried"]:
        results["gudhi_import_gate"] = {
            "status": "skipped",
            "reason": "gudhi not importable",
        }
        return results

    empty = gudhi.SimplexTree()
    empty.compute_persistence()
    _mark_gudhi_used()
    results["empty_simplex_tree_boundary"] = {
        "num_vertices": empty.num_vertices(),
        "num_simplices": empty.num_simplices(),
        "dimension": empty.dimension(),
        "betti_numbers": empty.betti_numbers(),
        "filtration": _serialize_filtration(empty),
        "pass": empty.num_vertices() == 0 and empty.num_simplices() == 0 and empty.dimension() == -1 and empty.betti_numbers() == [],
    }

    singleton = gudhi.SimplexTree()
    singleton.insert([42], filtration=0.0)
    singleton.compute_persistence()
    _mark_gudhi_used()
    results["singleton_vertex_boundary"] = {
        "num_vertices": singleton.num_vertices(),
        "num_simplices": singleton.num_simplices(),
        "dimension": singleton.dimension(),
        "betti_numbers": singleton.betti_numbers(),
        "filtration": _serialize_filtration(singleton),
        "pass": singleton.num_vertices() == 1 and singleton.num_simplices() == 1 and singleton.dimension() == 0 and singleton.betti_numbers() == [],
    }

    edge = gudhi.SimplexTree()
    edge.insert([0, 1], filtration=1.0)
    _mark_gudhi_used()
    results["simplex_order_is_boundary_invariant"] = {
        "find_01": edge.find([0, 1]),
        "find_10": edge.find([1, 0]),
        "filtration_10": _clean_number(float(edge.filtration([1, 0]))),
        "pass": edge.find([0, 1]) and edge.find([1, 0]) and edge.filtration([1, 0]) == 1.0,
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
