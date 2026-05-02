#!/usr/bin/env python3
"""TopoNetX CellComplex Hodge Laplacian micro probe.

Tool-stage scope:
  - one tool: TopoNetX
  - one API surface: CellComplex.hodge_laplacian_matrix(k)
  - one tiny claim: bounded CellComplex fixtures return finite Hodge
    Laplacian matrices with expected k-cell dimensions and tiny-kernel
    behavior for filled, hollow, empty, and single-edge boundaries.

This is pre-lego evidence. It does not promote a graph-cell lego, Hodge
spectral agreement claim, bridge, axis, cross-tool topology claim, or broad
TopoNetX proof.
"""

from __future__ import annotations

import json
import os
from typing import Any

import numpy as np
from toponetx.classes import CellComplex


classification = "canonical"
NAME = "sim_toponetx_hodge_laplacian_micro"
PROBE_FAMILY = "toponetx_cell_complex_hodge_laplacian_micro"
CONSTRAINT_SET = "tiny_cellcomplex_hodge_laplacian_fixture"

_NOT_USED_REASON = (
    "not used: this micro probe isolates TopoNetX "
    "CellComplex.hodge_laplacian_matrix(k) only; graph dynamics, persistence, "
    "cross-tool coupling, lego promotion, bridge, and axis claims are out of scope."
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
    "xgi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": (
            "TopoNetX is load-bearing: CellComplex.hodge_laplacian_matrix(k) "
            "emits the bounded k-cell operators that this receipt inspects."
        ),
    },
    "gudhi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "numpy": {
        "tried": True,
        "used": True,
        "reason": (
            "NumPy is supportive: it densifies TopoNetX sparse matrices and "
            "checks finite values, symmetry, eigenvalues, and tiny nullities "
            "without supplying the cell-complex operator."
        ),
    },
}

TOOL_INTEGRATION_DEPTH = {tool: None for tool in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["toponetx"] = "load_bearing"
TOOL_INTEGRATION_DEPTH["numpy"] = "supportive"

TOL = 1e-8


def _dense(matrix: Any) -> np.ndarray:
    if hasattr(matrix, "toarray"):
        return np.asarray(matrix.toarray(), dtype=float)
    return np.asarray(matrix, dtype=float)


def _hodge(complex_: CellComplex, k: int) -> np.ndarray:
    return _dense(complex_.hodge_laplacian_matrix(k))


def _filled_square_cell() -> CellComplex:
    complex_ = CellComplex()
    complex_.add_cell(["a", "b", "c", "d"], rank=2)
    return complex_


def _hollow_square_edges() -> CellComplex:
    complex_ = CellComplex()
    for edge in (["a", "b"], ["b", "c"], ["c", "d"], ["d", "a"]):
        complex_.add_cell(edge, rank=1)
    return complex_


def _kernel_dim(matrix: np.ndarray) -> int:
    if matrix.size == 0:
        return 0
    symmetric = (matrix + matrix.T) / 2.0
    eigenvalues = np.linalg.eigvalsh(symmetric)
    return int(np.sum(np.abs(eigenvalues) < TOL))


def _matrix_summary(matrix: np.ndarray) -> dict[str, Any]:
    if matrix.size == 0:
        return {
            "shape": list(matrix.shape),
            "finite": True,
            "symmetric_max_error": 0.0,
            "min_eigenvalue": None,
            "kernel_dim": 0,
        }

    symmetric = (matrix + matrix.T) / 2.0
    eigenvalues = np.linalg.eigvalsh(symmetric)
    return {
        "shape": list(matrix.shape),
        "finite": bool(np.isfinite(matrix).all()),
        "symmetric_max_error": float(np.max(np.abs(matrix - matrix.T))),
        "min_eigenvalue": float(np.min(eigenvalues)),
        "kernel_dim": _kernel_dim(matrix),
    }


def run_positive_tests() -> dict[str, Any]:
    complex_ = _filled_square_cell()
    l0 = _hodge(complex_, 0)
    l1 = _hodge(complex_, 1)
    l2 = _hodge(complex_, 2)
    l0_summary = _matrix_summary(l0)
    l1_summary = _matrix_summary(l1)
    l2_summary = _matrix_summary(l2)

    return {
        "filled_square_hodge_dimensions_match_k_cells": {
            "passed": l0.shape == (4, 4) and l1.shape == (4, 4) and l2.shape == (1, 1),
            "observed_shape": list(complex_.shape),
            "l0_summary": l0_summary,
            "l1_summary": l1_summary,
            "l2_summary": l2_summary,
            "expected_laplacian_shapes": {"L0": [4, 4], "L1": [4, 4], "L2": [1, 1]},
        },
        "filled_square_hodge_matrices_are_finite_symmetric_psd": {
            "passed": bool(
                all(summary["finite"] for summary in (l0_summary, l1_summary, l2_summary))
                and max(
                    l0_summary["symmetric_max_error"],
                    l1_summary["symmetric_max_error"],
                    l2_summary["symmetric_max_error"],
                )
                < TOL
                and min(
                    l0_summary["min_eigenvalue"],
                    l1_summary["min_eigenvalue"],
                    l2_summary["min_eigenvalue"],
                )
                >= -TOL
            ),
            "admission_note": (
                "This only receipts finite symmetric positive-semidefinite "
                "operators on one tiny CellComplex fixture."
            ),
        },
        "filled_square_tiny_kernel_receipt": {
            "passed": (
                l0_summary["kernel_dim"] == 1
                and l1_summary["kernel_dim"] == 0
                and l2_summary["kernel_dim"] == 0
            ),
            "observed_kernel_dims": {
                "L0": l0_summary["kernel_dim"],
                "L1": l1_summary["kernel_dim"],
                "L2": l2_summary["kernel_dim"],
            },
            "expected_kernel_dims": {"L0": 1, "L1": 0, "L2": 0},
        },
    }


def run_negative_tests() -> dict[str, Any]:
    filled = _filled_square_cell()
    hollow = _hollow_square_edges()
    filled_l1 = _hodge(filled, 1)
    hollow_l1 = _hodge(hollow, 1)

    malformed_rank_rejected = False
    malformed_error_type = None
    try:
        filled.hodge_laplacian_matrix(3)
    except Exception as exc:
        malformed_rank_rejected = True
        malformed_error_type = type(exc).__name__

    return {
        "hollow_square_not_equal_to_filled_square_l1_kernel": {
            "passed": _kernel_dim(hollow_l1) == 1 and _kernel_dim(filled_l1) == 0,
            "filled_l1_summary": _matrix_summary(filled_l1),
            "hollow_l1_summary": _matrix_summary(hollow_l1),
            "exclusion_note": (
                "The missing rank-2 cell is visible to the Hodge Laplacian "
                "operator on this bounded fixture; this is not a cross-tool "
                "or broad topology claim."
            ),
        },
        "out_of_range_rank_rejected": {
            "passed": malformed_rank_rejected,
            "rank_requested": 3,
            "error_type": malformed_error_type,
            "exclusion_note": "A rank beyond this tiny CellComplex must not fabricate an operator.",
        },
    }


def run_boundary_tests() -> dict[str, Any]:
    empty = CellComplex()
    single_edge = CellComplex()
    single_edge.add_cell(["a", "b"], rank=1)

    empty_l0 = _hodge(empty, 0)
    edge_l0 = _hodge(single_edge, 0)
    edge_l1 = _hodge(single_edge, 1)

    return {
        "empty_complex_hodge_l0_is_empty_operator": {
            "passed": empty_l0.shape == (0, 0) and _matrix_summary(empty_l0)["finite"],
            "observed_shape": list(empty.shape),
            "l0_summary": _matrix_summary(empty_l0),
            "boundary_note": "The empty CellComplex does not fabricate 0-cell operator rows.",
        },
        "single_edge_hodge_receipt_has_no_l1_kernel": {
            "passed": edge_l0.shape == (2, 2)
            and edge_l1.shape == (1, 1)
            and _kernel_dim(edge_l0) == 1
            and _kernel_dim(edge_l1) == 0,
            "observed_shape": list(single_edge.shape),
            "l0_summary": _matrix_summary(edge_l0),
            "l1_summary": _matrix_summary(edge_l1),
            "boundary_note": "A single bounded edge is only a minimal 1-cell fixture.",
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
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "surviving_alternatives": [
            "Other TopoNetX CellComplex APIs, SimplicialComplex Hodge APIs, "
            "persistent homology tools, graph-cell promotion, and scientific "
            "bridge claims remain separate receipts."
        ],
        "claim_ceiling": "tool_function_micro_only",
        "next_lego_target": (
            "none in this row; a downstream queue item would need to name an "
            "exact admissible target and parent receipt"
        ),
        "promotion_condition": (
            "requires a later admitted downstream row that names this exact "
            "function receipt and passes strict runner admission; this MICRO "
            "row does not promote any lego"
        ),
        "blocked_until": (
            "blocked until a downstream queue row declares the exact target, "
            "parent receipt use, and active stage gate for promotion"
        ),
        "demotion_condition": (
            "Demote TopoNetX for this function surface if "
            "CellComplex.hodge_laplacian_matrix(k) does not return finite "
            "square operators for bounded k-cell fixtures, if the tiny filled "
            "square and hollow square L1 kernel receipts collapse to the same "
            "verdict, if out-of-range rank fabricates an operator, or if empty "
            "and single-edge boundaries cannot be reported."
        ),
        "out_of_scope": [
            "no GUDHI cross-check",
            "no graph-cell lego promotion",
            "no Hodge spectral agreement claim beyond this tiny operation receipt",
            "no SimplicialComplex hodge claim",
            "no tool-tool coupling",
            "no bridge, axis, or broader topology claim",
            "no proof of the whole TopoNetX library",
        ],
        "criteria_checked": [
            "TopoNetX CellComplex.hodge_laplacian_matrix(k) returns bounded k-cell operators",
            "finite symmetric positive-semidefinite matrices on the filled-square fixture",
            "tiny filled-square L0/L1/L2 kernel dimensions",
            "hollow-square and out-of-range-rank exclusions",
            "empty and single-edge boundary behavior",
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
