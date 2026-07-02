#!/usr/bin/env python3
"""e3nn Wigner-3j zero-block selection-rule micro probe.

Tool-stage scope only:
  - one tool family: e3nn o3, with torch only as the tensor backend;
  - one API surface: o3.wigner_3j(l1, l2, l3);
  - one bounded claim: e3nn exposes the finite real-basis l=1 Wigner-3j
    tensor with repeated-axis zero blocks and nonzero distinct-axis entries,
    while adjacent invalid or lower-rank carriers are excluded or bounded.

This file is a tool-lego fit probe. It does not promote a lego, coupling,
bridge, axis, GStack, QIT, nonclassical, or target-system claim.
"""

from __future__ import annotations

import json
import os
from typing import Any

from receipt_boundary import apply_default_receipt_boundary

classification = "tool_lego_fit_probe"
NAME = "sim_e3nn_wigner_3j_zero_blocks_micro"
PROBE_FAMILY = "e3nn_wigner_3j_selection_rule_zero_blocks"
CONSTRAINT_SET = "bounded_l1_real_o3_wigner_3j_zero_block_fixture"

SURFACE = "e3nn.o3.wigner_3j selection-rule zero-blocks"
CARRIER = (
    "finite real O(3) carrier: one l=1 x l=1 x l=1 Wigner-3j tensor "
    "fixture with index set {0,1,2}^3"
)
COVERED_CHECK = (
    "new: existing e3nn load-bearing receipts cover capability, Wigner-D, "
    "spherical harmonics, tensor-product layers, and FullTensorProduct "
    "decomposition counts; no result receipt found for o3.wigner_3j "
    "selection-rule zero-blocks"
)
LEDGER_LOOPBACK = (
    "tool-depth row e3nn/load_bearing; contributes one candidate toward the "
    "shallow-tool checker threshold >=10 load-bearing e3nn receipts after runner evidence"
)
CLAIM_CEILING = (
    "local tool-lego fit only: e3nn.o3.wigner_3j returns the bounded l=1 "
    "real-basis tensor whose repeated-axis entries are zero and whose "
    "distinct-axis entries are nonzero; promotion_allowed=false; no QIT, "
    "GStack, axis, bridge, nonclassical, coupling, or target-system claim"
)

_NOT_USED_REASON = (
    "not used: this micro probe isolates one e3nn.o3.wigner_3j zero-block "
    "selection-rule surface; other tools require separate receipts."
)

TOOL_MANIFEST: dict[str, dict[str, Any]] = {
    "pytorch": {
        "tried": False,
        "used": False,
        "reason": "supportive tensor backend required by e3nn; not the selection-rule surface under test",
    },
    "pyg": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "z3": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "cvc5": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "sympy": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "clifford": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "e3nn": {
        "tried": False,
        "used": False,
        "reason": (
            "load-bearing target: e3nn.o3.wigner_3j decides the bounded "
            "l=1 real-basis repeated-axis zero-block predicate"
        ),
    },
    "rustworkx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "xgi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "toponetx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "gudhi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
}

TOOL_INTEGRATION_DEPTH = {tool: None for tool in TOOL_MANIFEST}

TORCH_OK = False
E3NN_OK = False
TORCH_IMPORT_ERROR = None
E3NN_IMPORT_ERROR = None
E3NN_VERSION = None

try:
    import torch

    TORCH_OK = True
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_INTEGRATION_DEPTH["pytorch"] = "supportive"
except Exception as exc:  # pragma: no cover - environment receipt path
    torch = None  # type: ignore[assignment]
    TORCH_IMPORT_ERROR = f"{type(exc).__name__}: {exc}"
    TOOL_MANIFEST["pytorch"]["reason"] = f"blocked: torch import failed: {TORCH_IMPORT_ERROR}"

try:
    import e3nn
    from e3nn import o3

    E3NN_OK = True
    E3NN_VERSION = getattr(e3nn, "__version__", "unknown")
    TOOL_MANIFEST["e3nn"]["tried"] = True
    TOOL_MANIFEST["e3nn"]["used"] = True
    TOOL_INTEGRATION_DEPTH["e3nn"] = "load_bearing"
except Exception as exc:  # pragma: no cover - environment receipt path
    o3 = None  # type: ignore[assignment]
    E3NN_IMPORT_ERROR = f"{type(exc).__name__}: {exc}"
    TOOL_MANIFEST["e3nn"]["reason"] = f"blocked: e3nn import failed: {E3NN_IMPORT_ERROR}"


def _row_admitted(row: dict[str, Any]) -> bool:
    return bool(row.get("passed"))


def _section_admitted(section: dict[str, dict[str, Any]]) -> bool:
    return bool(section) and all(_row_admitted(row) for row in section.values())


def _blocked_section() -> dict[str, dict[str, Any]]:
    return {
        "dependency_gate": {
            "passed": False,
            "status": "blocked",
            "torch_available": TORCH_OK,
            "e3nn_available": E3NN_OK,
            "torch_import_error": TORCH_IMPORT_ERROR,
            "e3nn_import_error": E3NN_IMPORT_ERROR,
            "blocked_reason": (
                "e3nn and torch are both required for this wigner_3j zero-block "
                "tool-lego fit fixture"
            ),
        }
    }


def _wigner_111() -> Any:
    return o3.wigner_3j(1, 1, 1, dtype=torch.float64)


def _repeated_axis_coords() -> list[tuple[int, int, int]]:
    return [
        (i, j, k)
        for i in range(3)
        for j in range(3)
        for k in range(3)
        if len({i, j, k}) < 3
    ]


def _distinct_axis_coords() -> list[tuple[int, int, int]]:
    return [
        (i, j, k)
        for i in range(3)
        for j in range(3)
        for k in range(3)
        if len({i, j, k}) == 3
    ]


def _max_abs_at(tensor: Any, coords: list[tuple[int, int, int]]) -> float:
    values = [tensor[i, j, k].abs() for i, j, k in coords]
    return float(torch.stack(values).max().item()) if values else 0.0


def _min_abs_at(tensor: Any, coords: list[tuple[int, int, int]]) -> float:
    values = [tensor[i, j, k].abs() for i, j, k in coords]
    return float(torch.stack(values).min().item()) if values else 0.0


def run_positive_tests() -> dict[str, dict[str, Any]]:
    if not (TORCH_OK and E3NN_OK):
        return _blocked_section()

    tensor = _wigner_111()
    distinct_coords = _distinct_axis_coords()
    distinct_min_abs = _min_abs_at(tensor, distinct_coords)

    return {
        "distinct_axis_entries_are_admitted": {
            "passed": distinct_min_abs > 0.0,
            "observed_shape": list(tensor.shape),
            "expected_shape": [3, 3, 3],
            "distinct_axis_coords": [list(coord) for coord in distinct_coords],
            "distinct_min_abs": distinct_min_abs,
            "admission_note": (
                "The finite l=1 real-basis carrier is admitted only for "
                "the six distinct-axis Wigner-3j tensor entries."
            ),
        },
        "normalized_tensor_readout_is_admitted": {
            "passed": bool(torch.isclose(torch.linalg.norm(tensor), torch.tensor(1.0, dtype=tensor.dtype), atol=1e-12)),
            "observed_norm": float(torch.linalg.norm(tensor).item()),
            "expected_norm": 1.0,
            "admission_note": "e3nn documents the Wigner-3j tensor with unit contraction norm.",
        },
    }


def run_negative_tests() -> dict[str, dict[str, Any]]:
    if not (TORCH_OK and E3NN_OK):
        return _blocked_section()

    tensor = _wigner_111()
    repeated_coords = _repeated_axis_coords()
    repeated_max_abs = _max_abs_at(tensor, repeated_coords)
    triangle_rejected = False
    triangle_error = None

    try:
        o3.wigner_3j(1, 1, 3, dtype=torch.float64)
    except Exception as exc:
        triangle_rejected = True
        triangle_error = f"{type(exc).__name__}: {exc}"

    return {
        "repeated_axis_block_is_excluded": {
            "passed": repeated_max_abs == 0.0,
            "observed_shape": list(tensor.shape),
            "repeated_axis_coords_count": len(repeated_coords),
            "repeated_axis_max_abs": repeated_max_abs,
            "exclusion_note": (
                "Repeated-axis entries are excluded from the l=1 real-basis "
                "Wigner-3j tensor support."
            ),
        },
        "triangle_rule_violation_is_excluded": {
            "passed": triangle_rejected,
            "candidate": "o3.wigner_3j(1, 1, 3)",
            "error": triangle_error,
            "exclusion_note": (
                "The adjacent l=3 readout is excluded for the l=1 x l=1 "
                "finite carrier under the triangle selection rule."
            ),
        },
    }


def run_boundary_tests() -> dict[str, dict[str, Any]]:
    if not (TORCH_OK and E3NN_OK):
        return _blocked_section()

    scalar = o3.wigner_3j(0, 0, 0, dtype=torch.float64)
    vector_scalar_vector = o3.wigner_3j(1, 0, 1, dtype=torch.float64)
    vector_pair_rank2 = o3.wigner_3j(1, 1, 2, dtype=torch.float64)

    return {
        "scalar_scalar_scalar_is_single_nonzero_boundary": {
            "passed": list(scalar.shape) == [1, 1, 1] and float(scalar.abs().item()) > 0.0,
            "observed_shape": list(scalar.shape),
            "observed_abs": float(scalar.abs().item()),
            "boundary_note": "The l=0 boundary has no repeated-axis zero block because the carrier has one scalar coordinate.",
        },
        "vector_scalar_vector_has_lower_rank_selection_boundary": {
            "passed": list(vector_scalar_vector.shape) == [3, 1, 3]
            and int((vector_scalar_vector.abs() > 1e-12).sum().item()) == 3,
            "observed_shape": list(vector_scalar_vector.shape),
            "nonzero_count": int((vector_scalar_vector.abs() > 1e-12).sum().item()),
            "boundary_note": "The scalar middle factor restricts support to a lower-rank vector-vector matching boundary.",
        },
        "rank2_vector_pair_is_not_the_l1_zero_block_fixture": {
            "passed": list(vector_pair_rank2.shape) == [3, 3, 5]
            and int((vector_pair_rank2.abs() > 1e-12).sum().item()) != 6,
            "observed_shape": list(vector_pair_rank2.shape),
            "nonzero_count": int((vector_pair_rank2.abs() > 1e-12).sum().item()),
            "boundary_note": "The l=2 adjacent output is admissible as a separate fixture, not as this l=1 zero-block receipt.",
        },
    }


def build_result() -> dict[str, Any]:
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    summary = {
        "positive_all_pass": _section_admitted(positive),
        "negative_all_pass": _section_admitted(negative),
        "boundary_all_pass": _section_admitted(boundary),
        "torch_available": TORCH_OK,
        "e3nn_available": E3NN_OK,
        "e3nn_version": E3NN_VERSION,
        "promotion_allowed": False,
        "surface": SURFACE,
        "covered_check": COVERED_CHECK,
        "ledger_loopback": LEDGER_LOOPBACK,
    }
    summary["all_pass"] = bool(
        TORCH_OK
        and E3NN_OK
        and summary["positive_all_pass"]
        and summary["negative_all_pass"]
        and summary["boundary_all_pass"]
    )

    result = {
        "name": NAME,
        "probe_family": PROBE_FAMILY,
        "constraint_set": CONSTRAINT_SET,
        "classification": classification,
        "status": "admitted" if summary["all_pass"] else "blocked",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "surface": SURFACE,
        "carrier": CARRIER,
        "one_variable": "only the e3nn.o3.wigner_3j zero-block selection behavior is uncertain",
        "covered_check": COVERED_CHECK,
        "ledger_loopback": LEDGER_LOOPBACK,
        "operation_sequence": [
            "construct o3.wigner_3j(1, 1, 1) as the finite carrier tensor",
            "read repeated-axis and distinct-axis support blocks",
            "run triangle-rule, scalar, vector-scalar-vector, and rank-2 adjacent controls",
        ],
        "carrier_topology": {
            "carrier": CARRIER,
            "topology": "finite one-tensor representation fixture; no graph, cell complex, manifold, bridge, or axis topology",
            "index_set": "{0,1,2}^3",
            "irreps": {"input_1": "l=1", "input_2": "l=1", "input_3": "l=1"},
        },
        "observable": "zero and nonzero support pattern in e3nn.o3.wigner_3j(1, 1, 1)",
        "pass_fail_predicate": (
            "admitted iff imports are available, wigner_3j(1,1,1) has shape "
            "(3,3,3), distinct-axis entries are nonzero, repeated-axis entries "
            "are zero, triangle-rule violation is excluded, and boundary "
            "fixtures remain distinct"
        ),
        "graveyards": [
            "repeated-axis entries admitted as nonzero support",
            "distinct-axis entries collapsed to zero",
            "triangle-rule violation accepted as a valid tensor",
            "adjacent scalar or l=2 boundary treated as this l=1 zero-block receipt",
            "any promotion beyond local tool-lego fit",
        ],
        "baselines": {
            "manual_support_count": "l=1 real-basis antisymmetric support has six distinct-axis entries",
            "manual_zero_block": "any repeated coordinate in the three l=1 axes is outside the support block",
            "scalar_boundary": "l=0 x l=0 x l=0 is a one-coordinate nonzero boundary",
        },
        "alternative_formulations": [
            "symbolic Wigner-3j coefficients in sympy as a separate cross-tool receipt",
            "Clebsch-Gordan coefficient relation as a separate tool-lego fit probe",
            "o3.FullTensorProduct decomposition counts as an already separate e3nn receipt",
        ],
        "exact_tool_function_needs": [
            "e3nn.o3.wigner_3j",
            "torch import only as e3nn backend and tensor readout helper",
        ],
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": False,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
        "surviving_alternatives": [
            "Other e3nn Wigner, Clebsch-Gordan, and tensor-product API surfaces remain separate receipts.",
            "This receipt does not decide any downstream lego, coupling, QIT, GStack, axis, bridge, or nonclassical surface.",
        ],
        "next_lego_target": "minimal finite SO(3) Wigner-3j selection-rule fixture before operator-family geometry claims",
        "promotion_condition": (
            "No promotion from this receipt. A later admitted lego row must name "
            "this exact function receipt, declare the stage gate, and pass strict runner admission."
        ),
        "blocked_until": (
            "blocked from QIT, GStack, axis, bridge, nonclassical, coupling, or "
            "target-system claims until separate downstream receipts and stage-gate admission exist"
        ),
        "demotion_condition": (
            "Demote e3nn for this surface if wigner_3j(1,1,1) reports nonzero "
            "repeated-axis entries, zero distinct-axis entries, non-unit "
            "contraction norm, or admits a triangle-rule violation."
        ),
        "out_of_scope": [
            "no lego promotion",
            "no tool-tool coupling",
            "no bridge claim",
            "no axis claim",
            "no GStack claim",
            "no QIT claim",
            "no nonclassical admission",
            "no target-system admission",
            "no proof of the whole e3nn library",
        ],
        "blocked_reason": None
        if summary["all_pass"]
        else "blocked because e3nn/torch imports or bounded zero-block predicates did not all admit",
    }
    return apply_default_receipt_boundary(
        result,
        source_name=NAME,
        target=result["next_lego_target"],
    )


if __name__ == "__main__":
    results = build_result()
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Summary: all_pass={results['all_pass']}")
    if not results["all_pass"]:
        raise SystemExit(1)
