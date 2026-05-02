#!/usr/bin/env python3
"""TopoNetX cell incidence micro probe.

Tool-stage scope:
  - one tool: TopoNetX
  - one API surface: CellComplex.add_cell plus incidence_matrix(1/2)
  - one tiny claim: a bounded rank-2 cell exposes the intended vertex/edge
    incidence, rejects degenerate higher-order readings, and handles empty and
    single-cell boundaries.

This is pre-lego evidence. It does not promote a graph-cell lego, Hodge
spectral claim, bridge, axis, or broad TopoNetX proof.
"""

from __future__ import annotations

import json
import os
from typing import Any

import numpy as np
from toponetx.classes import CellComplex


classification = "canonical"
NAME = "sim_toponetx_cell_incidence_micro"
PROBE_FAMILY = "toponetx_cell_incidence_micro"
CONSTRAINT_SET = "tiny_rank2_cell_boundary_incidence_fixture"

_NOT_USED_REASON = (
    "not used: this micro probe isolates TopoNetX CellComplex rank-2 cell "
    "incidence only; graph dynamics, persistence, lego promotion, and broad "
    "cross-tool claims are out of scope."
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
            "TopoNetX is load-bearing: CellComplex.add_cell and "
            "incidence_matrix(1/2) produce the rank-2 cell boundary and "
            "face-incidence verdicts."
        ),
    },
    "gudhi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "numpy": {
        "tried": True,
        "used": True,
        "reason": (
            "NumPy is supportive: it densifies and inspects TopoNetX incidence "
            "matrices, but does not supply the cell-complex structure."
        ),
    },
}

TOOL_INTEGRATION_DEPTH = {tool: None for tool in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["toponetx"] = "load_bearing"
TOOL_INTEGRATION_DEPTH["numpy"] = "supportive"


def _dense(matrix: Any) -> np.ndarray:
    if hasattr(matrix, "toarray"):
        return np.asarray(matrix.toarray(), dtype=float)
    return np.asarray(matrix, dtype=float)


def _build_triangle_cell() -> CellComplex:
    complex_ = CellComplex()
    complex_.add_cell(["a", "b", "c"], rank=2)
    return complex_


def _cell_vertices(complex_: CellComplex) -> set[str]:
    cells = list(complex_.cells)
    if not cells:
        return set()
    return {str(item) for item in cells[0]}


def _edge_sets(complex_: CellComplex) -> set[frozenset[str]]:
    return {frozenset(str(item) for item in edge) for edge in complex_.edges}


def run_positive_tests() -> dict[str, Any]:
    complex_ = _build_triangle_cell()
    b1 = _dense(complex_.incidence_matrix(1))
    b2 = _dense(complex_.incidence_matrix(2))
    boundary_of_boundary = b1 @ b2

    return {
        "rank2_cell_shape_and_vertices": {
            "passed": tuple(complex_.shape[:3]) == (3, 3, 1)
            and _cell_vertices(complex_) == {"a", "b", "c"},
            "observed_shape": list(complex_.shape),
            "expected_shape_prefix": [3, 3, 1],
            "observed_cell_vertices": sorted(_cell_vertices(complex_)),
            "expected_cell_vertices": ["a", "b", "c"],
        },
        "rank2_cell_has_three_boundary_edges": {
            "passed": bool(
                _edge_sets(complex_)
                == {
                    frozenset({"a", "b"}),
                    frozenset({"a", "c"}),
                    frozenset({"b", "c"}),
                }
                and b2.shape == (3, 1)
                and np.all(np.abs(b2[:, 0]) == 1.0)
            ),
            "observed_edges": sorted([sorted(edge) for edge in _edge_sets(complex_)]),
            "incidence_matrix_2_shape": list(b2.shape),
            "incidence_matrix_2_abs_column": np.abs(b2[:, 0]).tolist(),
        },
        "boundary_of_boundary_is_zero": {
            "passed": bool(np.allclose(boundary_of_boundary, 0.0)),
            "max_abs_boundary_of_boundary": (
                float(np.max(np.abs(boundary_of_boundary)))
                if boundary_of_boundary.size
                else 0.0
            ),
        },
    }


def run_negative_tests() -> dict[str, Any]:
    edge_only = CellComplex()
    edge_only.add_cell(["a", "b"], rank=1)
    edge_shape = tuple(edge_only.shape)

    repeated = CellComplex()
    repeated_ok = False
    error_type = None
    try:
        repeated.add_cell(["a", "a", "b"], rank=2)
        repeated_shape = tuple(repeated.shape)
        repeated_ok = len(repeated_shape) < 3 or repeated_shape[2] == 0
    except Exception as exc:  # TopoNetX may reject directly.
        repeated_ok = True
        error_type = type(exc).__name__

    return {
        "rank1_edge_not_promoted_to_rank2_cell": {
            "passed": len(edge_shape) < 3 or edge_shape[2] == 0,
            "observed_shape": list(edge_shape),
            "exclusion_note": "A two-node edge is not a rank-2 cell receipt.",
        },
        "repeated_vertex_cell_rejected_or_normalized": {
            "passed": repeated_ok,
            "error_type": error_type,
            "exclusion_note": (
                "Degenerate repeated vertices must not fabricate a higher-order "
                "rank-2 cell."
            ),
        },
    }


def run_boundary_tests() -> dict[str, Any]:
    empty = CellComplex()
    single = CellComplex()
    single.add_node("solo")

    return {
        "empty_cell_complex_has_no_incidence": {
            "passed": len(empty.shape) == 0 or all(value == 0 for value in empty.shape),
            "observed_shape": list(empty.shape),
            "boundary_note": "The empty boundary does not fabricate cells.",
        },
        "single_vertex_has_no_boundary_edges": {
            "passed": single.shape[0] == 1 and (len(single.shape) < 2 or single.shape[1] == 0),
            "observed_shape": list(single.shape),
            "boundary_note": "A single vertex remains a 0-cell only.",
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
            "TopoNetX Hodge spectra, graph-cell promotion, dynamics, and "
            "cross-tool topology claims remain separate receipts."
        ],
        "claim_ceiling": "tool_function_micro_only",
        "next_lego_target": "minimal rank-2 cell incidence fixture before graph-cell promotion",
        "promotion_condition": (
            "requires a later admitted downstream row that names this exact "
            "function receipt and passes strict runner admission; this MICRO "
            "row does not promote the lego"
        ),
        "blocked_until": (
            "blocked until a downstream queue row declares the exact graph-cell "
            "target, parent receipt use, and active stage gate for promotion"
        ),
        "demotion_condition": (
            "Demote TopoNetX for this function surface if rank-2 cells do not "
            "produce the expected boundary edges, if incidence_matrix(2) does "
            "not expose the cell-to-edge boundary, if boundary-of-boundary is "
            "nonzero, or if rank-1/degenerate inputs fabricate rank-2 cells."
        ),
        "out_of_scope": [
            "no Hodge spectral agreement claim",
            "no graph-cell lego promotion",
            "no XGI or PyG cross-tool claim",
            "no bridge, axis, or broader topology claim",
            "no proof of the whole TopoNetX library",
        ],
        "criteria_checked": [
            "TopoNetX CellComplex rank-2 cell construction",
            "rank-2 cell boundary edge incidence",
            "boundary-of-boundary zero on the bounded fixture",
            "rank-1 and degenerate-input exclusion",
            "empty and single-vertex boundaries",
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
