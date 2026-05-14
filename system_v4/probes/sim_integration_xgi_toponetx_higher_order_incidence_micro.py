#!/usr/bin/env python3
"""XGI x TopoNetX higher-order incidence integration micro probe.

Tool-stage scope:
  - two primary tools: XGI and TopoNetX
  - exact prior surfaces:
      * XGI Hypergraph edge/node incidence micro
      * TopoNetX CellComplex rank-2 cell incidence micro
  - one tiny claim: XGI size-3 hyperedge incidence and TopoNetX rank-2
    cell face incidence agree on a bounded two-triad fixture.

This is below lego stage. It does not promote a graph-cell lego, Hodge
spectral agreement, bridge, axis, higher-order dynamics, or whole-library
equivalence claim.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import numpy as np
import xgi
from toponetx.classes import CellComplex


classification = "canonical"
NAME = "sim_integration_xgi_toponetx_higher_order_incidence_micro"
PROBE_FAMILY = "xgi_toponetx_higher_order_incidence_micro"
CONSTRAINT_SET = "two_triad_hyperedge_cell_boundary_incidence_fixture"

PRIOR_RECEIPTS = {
    "xgi": "system_v4/probes/a2_state/sim_results/sim_xgi_hypergraph_incidence_micro_results.json",
    "toponetx": "system_v4/probes/a2_state/sim_results/sim_toponetx_cell_incidence_micro_results.json",
}

TRIADS = {
    "left": (0, 1, 2),
    "right": (1, 2, 3),
}

_NOT_USED_REASON = (
    "not used: this integration micro isolates XGI hyperedge incidence and "
    "TopoNetX rank-2 cell incidence on one tiny fixture; dynamics, Hodge "
    "spectra, persistence, lego promotion, and bridge claims are out of scope."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "pyg": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "z3": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "cvc5": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "sympy": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "clifford": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "e3nn": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "xgi": {
        "tried": True,
        "used": True,
        "reason": (
            "XGI is load-bearing: Hypergraph hyperedge members and shared "
            "incidence intersections supply one side of the higher-order "
            "fixture agreement."
        ),
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": (
            "TopoNetX is load-bearing: CellComplex rank-2 cells and "
            "incidence_matrix(2) supply the independent cell-boundary witness."
        ),
    },
    "gudhi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "numpy": {
        "tried": True,
        "used": True,
        "reason": (
            "NumPy is supportive: it densifies and inspects the TopoNetX "
            "incidence matrix without supplying the cell-complex structure."
        ),
    },
}

TOOL_INTEGRATION_DEPTH = {tool: None for tool in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["xgi"] = "load_bearing"
TOOL_INTEGRATION_DEPTH["toponetx"] = "load_bearing"
TOOL_INTEGRATION_DEPTH["numpy"] = "supportive"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_prior_receipts() -> dict[str, Any]:
    root = _repo_root()
    receipts = {}
    for tool, rel in PRIOR_RECEIPTS.items():
        path = root / rel
        data = json.loads(path.read_text(encoding="utf-8"))
        source_rel = f"system_v4/probes/{data.get('name')}.py"
        source_path = root / source_rel
        result_mtime = path.stat().st_mtime if path.exists() else 0.0
        source_mtime = source_path.stat().st_mtime if source_path.exists() else 0.0
        receipts[tool] = {
            "path": rel,
            "source_path": source_rel,
            "exists": path.exists(),
            "source_exists": source_path.exists(),
            "all_pass": data.get("all_pass") is True,
            "classification": data.get("classification"),
            "load_bearing": data.get("tool_integration_depth", {}).get(tool) == "load_bearing",
            "result_mtime": result_mtime,
            "source_mtime": source_mtime,
            "result_fresh_for_source": (
                path.exists() and source_path.exists() and result_mtime >= source_mtime
            ),
            "name": data.get("name"),
        }
    return receipts


def _prior_receipts_ok(receipts: dict[str, Any]) -> bool:
    return all(
        item["exists"]
        and item["source_exists"]
        and item["all_pass"]
        and item["classification"] == "canonical"
        and item["load_bearing"]
        and item["result_fresh_for_source"]
        for item in receipts.values()
    )


def _dense(matrix: Any) -> np.ndarray:
    if hasattr(matrix, "toarray"):
        return np.asarray(matrix.toarray(), dtype=float)
    return np.asarray(matrix, dtype=float)


def build_hypergraph() -> xgi.Hypergraph:
    hypergraph = xgi.Hypergraph()
    for edge_id, members in TRIADS.items():
        hypergraph.add_edge(members, idx=edge_id)
    return hypergraph


def build_cell_complex() -> CellComplex:
    complex_ = CellComplex()
    for members in TRIADS.values():
        complex_.add_cell(list(members), rank=2)
    return complex_


def _xgi_members(hypergraph: xgi.Hypergraph, edge_id: str) -> set[int]:
    return {int(item) for item in hypergraph.edges.members(edge_id)}


def _toponetx_cell_sets(complex_: CellComplex) -> set[frozenset[int]]:
    return {frozenset(int(item) for item in cell) for cell in complex_.cells}


def _toponetx_edge_sets(complex_: CellComplex) -> list[frozenset[int]]:
    return [frozenset(int(item) for item in edge) for edge in complex_.edges]


def _shared_edge_incidence(complex_: CellComplex, edge: frozenset[int]) -> int:
    edges = _toponetx_edge_sets(complex_)
    b2 = np.abs(_dense(complex_.incidence_matrix(2)))
    row = edges.index(edge)
    return int(np.sum(b2[row, :] > 0))


def run_positive_tests() -> dict[str, Any]:
    receipts = _load_prior_receipts()
    hypergraph = build_hypergraph()
    complex_ = build_cell_complex()

    xgi_sets = {edge_id: _xgi_members(hypergraph, edge_id) for edge_id in TRIADS}
    tnx_sets = _toponetx_cell_sets(complex_)
    shared_xgi = xgi_sets["left"] & xgi_sets["right"]
    shared_edge = frozenset(shared_xgi)
    shared_tnx_count = _shared_edge_incidence(complex_, shared_edge)

    return {
        "prior_function_receipts_are_admissible": {
            "passed": _prior_receipts_ok(receipts),
            "receipts": receipts,
        },
        "hyperedges_match_rank2_cell_vertices": {
            "passed": {frozenset(value) for value in xgi_sets.values()} == tnx_sets,
            "xgi_hyperedges": {
                edge_id: sorted(value) for edge_id, value in xgi_sets.items()
            },
            "toponetx_cells": sorted([sorted(value) for value in tnx_sets]),
        },
        "shared_pair_incidence_agrees": {
            "passed": shared_xgi == {1, 2} and shared_tnx_count == 2,
            "xgi_shared_intersection": sorted(shared_xgi),
            "toponetx_shared_edge": sorted(shared_edge),
            "toponetx_rank2_cells_incident_to_shared_edge": shared_tnx_count,
        },
    }


def run_negative_tests() -> dict[str, Any]:
    hypergraph = build_hypergraph()
    complex_ = build_cell_complex()
    xgi_sets = {edge_id: _xgi_members(hypergraph, edge_id) for edge_id in TRIADS}
    tnx_edges = set(_toponetx_edge_sets(complex_))

    fake_pair = {0, 3}
    omitted_vertex_cell = frozenset({0, 1})
    tnx_sets = _toponetx_cell_sets(complex_)

    return {
        "non_shared_pair_is_excluded": {
            "passed": fake_pair != (xgi_sets["left"] & xgi_sets["right"])
            and frozenset(fake_pair) not in tnx_edges,
            "fake_pair": sorted(fake_pair),
            "xgi_shared_intersection": sorted(xgi_sets["left"] & xgi_sets["right"]),
            "toponetx_edges": sorted([sorted(edge) for edge in tnx_edges]),
        },
        "omitted_vertex_cell_does_not_match_triad": {
            "passed": omitted_vertex_cell not in tnx_sets
            and omitted_vertex_cell != frozenset(xgi_sets["left"]),
            "omitted_vertex_cell": sorted(omitted_vertex_cell),
            "expected_left_triad": sorted(xgi_sets["left"]),
        },
    }


def run_boundary_tests() -> dict[str, Any]:
    single_hypergraph = xgi.Hypergraph()
    single_hypergraph.add_edge((0, 1, 2), idx="single")
    single_complex = CellComplex()
    single_complex.add_cell([0, 1, 2], rank=2)
    single_b2 = _dense(single_complex.incidence_matrix(2))

    empty_hypergraph = xgi.Hypergraph()
    empty_complex = CellComplex()

    return {
        "single_triad_maps_to_one_rank2_cell": {
            "passed": single_hypergraph.num_edges == 1
            and single_complex.shape[:3] == (3, 3, 1)
            and single_b2.shape == (3, 1),
            "xgi_num_edges": single_hypergraph.num_edges,
            "toponetx_shape": list(single_complex.shape),
            "toponetx_incidence_matrix_2_shape": list(single_b2.shape),
        },
        "empty_fixture_fabricates_no_incidence": {
            "passed": empty_hypergraph.num_edges == 0
            and (len(empty_complex.shape) == 0 or all(value == 0 for value in empty_complex.shape)),
            "xgi_num_edges": empty_hypergraph.num_edges,
            "toponetx_shape": list(empty_complex.shape),
        },
    }


def _flatten_sections(*sections: dict[str, Any]) -> list[dict[str, Any]]:
    flat = []
    for section in sections:
        for value in section.values():
            if isinstance(value, dict) and "passed" in value:
                flat.append(value)
    return flat


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    flat_tests = _flatten_sections(positive, negative, boundary)
    all_pass = all(test.get("passed") for test in flat_tests)

    results = {
        "name": NAME,
        "probe_family": PROBE_FAMILY,
        "constraint_set": CONSTRAINT_SET,
        "classification": classification,
        "operation_sequence": [
            "load exact prior XGI hypergraph-incidence and TopoNetX cell-incidence receipts",
            "construct an XGI Hypergraph with two overlapping three-node hyperedges",
            "construct a TopoNetX CellComplex with the same two rank-2 triad cells",
            "compare XGI hyperedge member sets against TopoNetX rank-2 cell vertex sets",
            "compare shared-pair incidence in XGI intersection and TopoNetX rank-2 boundary incidence",
            "run fake-pair, omitted-vertex, single-triad, and empty-fixture controls",
        ],
        "carrier_topology": (
            "finite two-triad higher-order incidence fixture represented once as "
            "an XGI hypergraph and once as a TopoNetX rank-2 cell complex; no "
            "Hodge spectrum, dynamics, graph-cell lego promotion, bridge, axis, "
            "GStack, QIT engine, or nonclassical claim"
        ),
        "observable": (
            "hyperedge member sets, rank-2 cell vertex sets, shared edge incidence "
            "count in the TopoNetX incidence matrix, fake-pair exclusion, and "
            "single/empty fixture boundary counts"
        ),
        "pass_fail_predicate": (
            "prior receipts must be canonical, load-bearing, all_pass, and fresh; "
            "XGI hyperedge sets must equal TopoNetX cell vertex sets; shared pair "
            "incidence must agree; fake pairs, omitted vertices, and empty fixtures "
            "must not fabricate agreement"
        ),
        "graveyards": [
            "non-shared pair {0,3} must not be treated as shared incidence",
            "omitted two-vertex cell {0,1} must not match the three-node triad",
            "empty XGI and TopoNetX fixtures must fabricate no incidence",
            "stale, missing, noncanonical, or non-load-bearing parent receipts block the integration claim",
        ],
        "baselines": [
            "prior XGI hypergraph incidence micro receipt",
            "prior TopoNetX cell incidence micro receipt",
            "single-triad one-cell boundary fixture",
            "empty fixture no-incidence boundary",
        ],
        "alternative_formulations": [
            "manual incidence matrix comparison from the same two triads",
            "NetworkX bipartite incidence graph projection as a lossy graph baseline",
            "GUDHI simplex-tree encoding as a separate topology comparison packet",
        ],
        "tool_function_needs": {
            "xgi": ["Hypergraph", "add_edge", "edges.members"],
            "toponetx": ["CellComplex", "add_cell", "cells", "edges", "incidence_matrix"],
            "numpy": ["asarray", "abs", "sum"],
        },
        "lego_coupling_target": "minimal two-triad higher-order incidence fixture below graph-cell lego promotion",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "prior_function_receipts": PRIOR_RECEIPTS,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "surviving_alternatives": [
            "Hodge spectral agreement, hypergraph Laplacians, dynamics, "
            "graph-cell lego promotion, and broader XGI/TopoNetX equivalence "
            "remain separate receipts."
        ],
        "claim_ceiling": "tool_integration_micro_only",
        "next_lego_target": "minimal two-triad higher-order incidence fixture below graph-cell lego promotion",
        "promotion_condition": (
            "requires a later admitted integration or lego row that names the "
            "exact parent receipts and passes strict runner admission; this "
            "INTEGRATION_MICRO row does not promote the lego"
        ),
        "blocked_until": (
            "blocked until a downstream queue row declares the exact graph-cell "
            "or higher-order integration target, parent receipts, and active "
            "stage gate for promotion"
        ),
        "demotion_condition": (
            "Demote this XGI-TopoNetX surface if either prior receipt is missing, "
            "noncanonical, not all_pass, not load-bearing, or older than its "
            "source probe; if XGI hyperedge membership no longer matches "
            "TopoNetX rank-2 cell vertices; if the shared pair incidence is "
            "not seen by both tools; or if fake pairs/empty fixtures fabricate "
            "higher-order agreement."
        ),
        "out_of_scope": [
            "no Hodge spectral agreement claim",
            "no hypergraph Laplacian claim",
            "no higher-order dynamics claim",
            "no graph-cell lego promotion",
            "no bridge, axis, or broad topology claim",
            "no proof of whole XGI or TopoNetX libraries",
        ],
        "criteria_checked": [
            "prior XGI incidence function receipt is canonical and load-bearing",
            "prior TopoNetX cell-incidence function receipt is canonical and load-bearing",
            "prior function receipts are fresh relative to their source probes",
            "XGI size-3 hyperedges match TopoNetX rank-2 cell vertices",
            "shared pair incidence is detected by both tools",
            "non-shared pair and omitted-vertex exclusions",
            "single-triad and empty-fixture boundaries",
        ],
        "summary": {
            "passed": sum(1 for test in flat_tests if test.get("passed")),
            "total": len(flat_tests),
        },
        "all_pass": all_pass,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Summary: {results['summary']['passed']}/{results['summary']['total']} passed")

    if not all_pass:
        raise SystemExit(1)
