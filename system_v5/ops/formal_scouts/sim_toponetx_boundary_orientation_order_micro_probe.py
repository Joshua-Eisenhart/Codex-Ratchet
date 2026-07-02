#!/usr/bin/env python3
"""Formal scout for TopoNetX attached-cell boundary orientation order."""

from __future__ import annotations

import hashlib
import json
import pathlib

import toponetx as tnx


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "sim_toponetx_boundary_orientation_order_micro_probe_results.json"

NAME = "sim_toponetx_boundary_orientation_order_micro_probe"
SIM_ID = "toponetx_boundary_orientation_order_micro_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: observed TopoNetX attached 2-cell construction and "
    "boundary orientation order on one finite carrier with reversed, erased, "
    "and triangulated-surrogate controls. This is local tool-function evidence, "
    "not promoted bridge, axis, engine, topology theorem, layer completion, or "
    "target-system evidence."
)
ROOT_CONSTRAINTS_IN_FORCE = ["F01_FINITE_CARRIER_PROBE_OPERATOR_PATH_SET", "N01_ORDER_SENSITIVE_CONTROL"]
FINITE_MAP = (
    "TopoNetXCellBoundary : finite cyclic 1-skeleton plus one attached square "
    "2-cell -> signed B2 incidence column, B1*B2 boundary-of-boundary check, "
    "and non-simplicial cell-vs-triangulation witness"
)
DOMAIN = {
    "carrier": "finite CellComplex with vertices 0..3, cyclic edges, and one rank-2 attached square cell",
    "controls": [
        "reversed cyclic orientation",
        "erased attached 2-cell",
        "triangulated two-simplex surrogate with diagonal",
    ],
}
CODOMAIN_OR_OUTPUT = {
    "signed_boundary_column": "finite rank-2 incidence vector over oriented edges",
    "boundary_of_boundary_zero": "B1*B2 has no nonzero entries",
    "non_simplicial_witness": "one attached square cell differs from two-triangle simplex surrogate",
}

TOOL_MANIFEST = {
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing CellComplex construction of a non-simplicial attached 2-cell and incidence-matrix boundary receipt",
    },
    "python": {
        "tried": True,
        "used": True,
        "reason": "supportive finite orientation arithmetic and pass/fail checks",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive result receipt serialization",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive canonical result path construction",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive stable observable digest",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "toponetx": "load_bearing",
    "python": "supportive",
    "json": "supportive",
    "pathlib": "supportive",
    "hashlib": "supportive",
}


def stable_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def cyclic_edges(vertices: list[int]) -> list[list[int]]:
    return [[vertices[index], vertices[(index + 1) % len(vertices)]] for index in range(len(vertices))]


def matrix_column_entries(row_index: dict[object, int], matrix: object) -> list[dict[str, object]]:
    array = matrix.toarray()
    ordered_rows = sorted(row_index.items(), key=lambda item: item[1])
    entries = []
    for label, row in ordered_rows:
        value = float(array[row][0]) if matrix.shape[1] else 0.0
        entries.append({"edge": list(label), "coefficient": value})
    return entries


def nonzero_abs_max(matrix: object) -> float:
    if matrix.nnz == 0:
        return 0.0
    return max(abs(float(value)) for value in matrix.data)


def cell_boundary_observable(vertices: list[int]) -> dict[str, object]:
    complex_ = tnx.CellComplex()
    for edge in cyclic_edges(vertices):
        complex_.add_cell(edge, rank=1)
    complex_.add_cell(list(vertices), rank=2)
    edge_index, cell_index, incidence_2 = complex_.incidence_matrix(2, signed=True, index=True)
    _vertex_index, _edge_index_1, incidence_1 = complex_.incidence_matrix(1, signed=True, index=True)
    boundary_of_boundary = incidence_1 @ incidence_2
    signed_edge_labels = [
        f"{row['coefficient']}:{row['edge'][0]}|{row['edge'][1]}"
        for row in matrix_column_entries(edge_index, incidence_2)
    ]
    return {
        "cell_vertices": list(vertices),
        "rank_0_cell_count": len(list(complex_.skeleton(0))),
        "rank_1_cell_count": len(list(complex_.skeleton(1))),
        "rank_2_cell_count": len(list(complex_.skeleton(2))),
        "rank_2_cells": [str(cell) for cell in complex_.skeleton(2)],
        "edge_index": {str(key): int(value) for key, value in edge_index.items()},
        "cell_index": {str(key): int(value) for key, value in cell_index.items()},
        "signed_boundary_entries": matrix_column_entries(edge_index, incidence_2),
        "signed_edge_labels": signed_edge_labels,
        "incidence_shape": [int(incidence_2.shape[0]), int(incidence_2.shape[1])],
        "incidence_nonzero_count": int(incidence_2.nnz),
        "boundary_of_boundary_shape": [int(boundary_of_boundary.shape[0]), int(boundary_of_boundary.shape[1])],
        "boundary_of_boundary_nonzero_count": int(boundary_of_boundary.nnz),
        "boundary_of_boundary_abs_max": nonzero_abs_max(boundary_of_boundary),
    }


def erased_cell_observable(vertices: list[int]) -> dict[str, object]:
    complex_ = tnx.CellComplex()
    for edge in cyclic_edges(vertices):
        complex_.add_cell(edge, rank=1)
    incidence_2 = complex_.incidence_matrix(2, signed=True)
    return {
        "rank_0_cell_count": len(list(complex_.skeleton(0))),
        "rank_1_cell_count": len(list(complex_.skeleton(1))),
        "rank_2_cell_count": len(list(complex_.skeleton(2))),
        "incidence_shape": [int(incidence_2.shape[0]), int(incidence_2.shape[1])],
        "incidence_nonzero_count": int(incidence_2.nnz),
    }


def triangulated_surrogate_observable() -> dict[str, object]:
    complex_ = tnx.SimplicialComplex()
    complex_.add_simplex([0, 1, 2])
    complex_.add_simplex([0, 2, 3])
    edge_index, simplex_index, incidence_2 = complex_.incidence_matrix(2, signed=True, index=True)
    return {
        "edge_count": len(edge_index),
        "rank_2_simplex_count": len(simplex_index),
        "edge_index": {str(key): int(value) for key, value in edge_index.items()},
        "simplex_index": {str(key): int(value) for key, value in simplex_index.items()},
        "incidence_shape": [int(incidence_2.shape[0]), int(incidence_2.shape[1])],
        "incidence_nonzero_count": int(incidence_2.nnz),
    }


def main() -> None:
    baseline = cell_boundary_observable([0, 1, 2, 3])
    reversed_control = cell_boundary_observable([0, 3, 2, 1])
    erased_control = erased_cell_observable([0, 1, 2, 3])
    triangulated_control = triangulated_surrogate_observable()
    changed_observable = baseline["signed_edge_labels"] != reversed_control["signed_edge_labels"]
    same_support = sorted(
        "|".join(str(part) for part in sorted(row["edge"])) for row in baseline["signed_boundary_entries"]
    ) == sorted(
        "|".join(str(part) for part in sorted(row["edge"])) for row in reversed_control["signed_boundary_entries"]
    )
    erased_kills_attached_cell = erased_control["incidence_shape"][1] == 0 and erased_control["rank_2_cell_count"] == 0
    triangulation_not_equivalent = (
        triangulated_control["incidence_shape"] != baseline["incidence_shape"]
        and triangulated_control["edge_count"] == 5
        and triangulated_control["rank_2_simplex_count"] == 2
        and baseline["rank_2_cell_count"] == 1
    )
    checks = {
        "classification_is_formal_scout": CLASSIFICATION == "formal_scout",
        "execution_kind_is_nonclassical": SIM_EXECUTION_KIND == "nonclassical",
        "promotion_disabled": PROMOTION_ALLOWED is False,
        "finite_cell_complex_ran": baseline["incidence_shape"] == [4, 1] and baseline["incidence_nonzero_count"] == 4,
        "boundary_of_boundary_zero": baseline["boundary_of_boundary_nonzero_count"] == 0,
        "same_unoriented_boundary_support": same_support,
        "reversed_control_changed_observable": changed_observable,
        "erased_control_kills_attached_cell": erased_kills_attached_cell,
        "triangulated_surrogate_not_equivalent": triangulation_not_equivalent,
    }
    positive = {
        "toponetx_attached_cell_boundary_incidence_runs": {
            "pass": checks["finite_cell_complex_ran"],
            "incidence_shape": baseline["incidence_shape"],
        },
        "boundary_of_boundary_zero_for_attached_cell": {
            "pass": checks["boundary_of_boundary_zero"],
            "boundary_of_boundary_abs_max": baseline["boundary_of_boundary_abs_max"],
        },
        "orientation_reversal_changes_signed_boundary": {
            "pass": checks["reversed_control_changed_observable"],
            "observable": "signed_edge_labels",
        },
    }
    graveyard_companions = {
        "unoriented_boundary_support_control_preserved": {
            "pass": checks["same_unoriented_boundary_support"],
            "reason": "the orientation negative changes signed order while preserving unoriented edge support",
        },
        "erased_attached_cell_control_fails_boundary_claim": {
            "pass": checks["erased_control_kills_attached_cell"],
            "reason": "removing the rank-2 cell leaves no B2 column, so the attached-cell claim is gone",
        },
        "triangulated_surrogate_control_not_same_carrier": {
            "pass": checks["triangulated_surrogate_not_equivalent"],
            "reason": "two triangles plus a diagonal is a different cell carrier than one attached square 2-cell",
        },
        "promotion_remains_disabled": {
            "pass": PROMOTION_ALLOWED is False,
            "reason": "tool-function evidence stays scout-only",
        },
    }
    boundary = {
        "finite_fixture_only": {
            "pass": checks["finite_cell_complex_ran"],
            "claim": "bounded to one finite four-edge CellComplex fixture",
        },
        "not_topology_theorem_or_engine_claim": {
            "pass": True,
            "claim": "does not promote a topology theorem, bridge, axis, engine, layer, or target-system result",
        },
    }
    nearby_variants = {
        "total": len(graveyard_companions),
        "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
    }
    result = {
        "name": NAME,
        "sim_id": SIM_ID,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "root_constraints_in_force": ROOT_CONSTRAINTS_IN_FORCE,
        "finite_map": FINITE_MAP,
        "domain": DOMAIN,
        "codomain_or_output": CODOMAIN_OR_OUTPUT,
        "fixture": "finite non-simplicial square 2-cell attached to a cyclic 1-skeleton",
        "baseline": baseline,
        "reversed_control_negative": reversed_control,
        "erased_attached_cell_negative": erased_control,
        "triangulated_surrogate_negative": triangulated_control,
        "changed_observable_required": True,
        "changed_observable": changed_observable,
        "observable_digest": stable_hash(
            {
                "baseline": baseline,
                "reversed_control": reversed_control,
                "erased_control": erased_control,
                "triangulated_control": triangulated_control,
            }
        ),
        "checks": checks,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": [
            "v5 formal scout receipt only",
            "TopoNetX attached-cell boundary micro-probe, not a canonical sim or promoted lego",
            "nonclassical execution kind with promotion explicitly blocked",
        ],
        "all_pass": all(checks.values()),
        "pass": all(checks.values()),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"path": str(OUT_PATH), "pass": result["pass"], "changed": changed_observable}, sort_keys=True))


if __name__ == "__main__":
    main()
