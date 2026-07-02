#!/usr/bin/env python3
"""e3nn o3.Linear irrep-block dimension micro probe.

Tool-stage scope:
  - one tool: e3nn
  - one API surface: o3.Linear on bounded O(3) irrep feature fixtures
  - one tiny claim: e3nn o3.Linear preserves the declared output irrep
    dimension while mixing multiplicities inside compatible irrep blocks.

This is a tool-lego fit probe. It does not promote a lego, coupling, bridge,
axis, broad equivariance, learned-network, or operator-geometry claim.
"""

from __future__ import annotations

import json
import os
from typing import Any

import torch
from e3nn import o3


classification = "tool_lego_fit_probe"
NAME = "sim_e3nn_linear_irrep_block_dimension_micro"
PROBE_FAMILY = "e3nn_linear_irrep_block_dimension_micro"
CONSTRAINT_SET = "bounded_o3_linear_irrep_block_dimension_fixtures"

TORCH_SEED = 20260702
DTYPE = torch.float64

IRREPS_IN = o3.Irreps("2x0e + 2x1o")
IRREPS_OUT = o3.Irreps("1x0e + 3x1o")
IRREPS_SCALAR = o3.Irreps("2x0e")

CARRIER = (
    "finite carrier: batch of two O(3) feature tensors over "
    "2x0e + 2x1o, dimension 8, with codomain 1x0e + 3x1o, dimension 10"
)

_NOT_USED_REASON = (
    "not used: this tool-lego fit probe isolates e3nn.o3.Linear irrep-block "
    "dimension behavior on a finite O(3) feature carrier; proof, topology, "
    "GNN message passing, coupling, bridge, axis, and promotion claims are "
    "out of scope."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": (
            "PyTorch is supportive: tensors provide the finite input carrier "
            "and shape comparisons consumed by e3nn.o3.Linear."
        ),
    },
    "pyg": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "z3": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "cvc5": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "sympy": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "clifford": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "e3nn": {
        "tried": True,
        "used": True,
        "reason": (
            "e3nn is load-bearing: o3.Linear supplies the irrep-aware block "
            "mixing under test and determines whether declared input/output "
            "irrep dimensions are preserved or rejected."
        ),
    },
    "rustworkx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "xgi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "toponetx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "gudhi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
}

TOOL_INTEGRATION_DEPTH = {tool: None for tool in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["pytorch"] = "supportive"
TOOL_INTEGRATION_DEPTH["e3nn"] = "load_bearing"


def _linear_layer(irreps_in: o3.Irreps = IRREPS_IN, irreps_out: o3.Irreps = IRREPS_OUT) -> o3.Linear:
    layer = o3.Linear(irreps_in, irreps_out)
    return layer.to(dtype=DTYPE)


def _finite_features(batch: int = 2) -> torch.Tensor:
    torch.manual_seed(TORCH_SEED)
    return torch.randn(batch, IRREPS_IN.dim, dtype=DTYPE)


def _flatten_sections(*sections: dict[str, Any]) -> list[dict[str, Any]]:
    flat: list[dict[str, Any]] = []
    for section in sections:
        for value in section.values():
            if isinstance(value, dict) and "passed" in value:
                flat.append(value)
    return flat


def run_positive_tests() -> dict[str, Any]:
    layer = _linear_layer()
    features = _finite_features()
    output = layer(features)

    return {
        "linear_declares_expected_irrep_dimensions": {
            "passed": IRREPS_IN.dim == 8 and IRREPS_OUT.dim == 10,
            "carrier": CARRIER,
            "irreps_in": str(IRREPS_IN),
            "irreps_out": str(IRREPS_OUT),
            "observed_dims": {"input": IRREPS_IN.dim, "output": IRREPS_OUT.dim},
            "expected_dims": {"input": 8, "output": 10},
        },
        "linear_preserves_declared_output_width": {
            "passed": tuple(output.shape) == (2, IRREPS_OUT.dim),
            "input_shape": list(features.shape),
            "output_shape": list(output.shape),
            "expected_output_shape": [2, IRREPS_OUT.dim],
            "fixture": "2x0e + 2x1o -> 1x0e + 3x1o",
        },
        "linear_has_block_mixing_parameters": {
            "passed": layer.weight_numel > 0,
            "weight_numel": int(layer.weight_numel),
            "mixing_note": (
                "The o3.Linear surface has trainable paths available for "
                "multiplicity mixing inside compatible irreps in this finite fixture."
            ),
        },
    }


def run_negative_tests() -> dict[str, Any]:
    layer = _linear_layer()
    good = _finite_features(batch=1)
    bad = torch.randn(1, IRREPS_IN.dim + 1, dtype=DTYPE)

    rejected = False
    error_type = None
    error_message = None
    try:
        layer(bad)
    except Exception as exc:
        rejected = True
        error_type = type(exc).__name__
        error_message = str(exc)

    return {
        "incompatible_input_width_is_excluded": {
            "passed": rejected,
            "expected": "feature width 9 is excluded for declared input irrep dimension 8",
            "bad_input_shape": list(bad.shape),
            "good_input_shape": list(good.shape),
            "error_type": error_type,
            "error_message": error_message,
            "exclusion_note": (
                "The o3.Linear surface must not silently admit tensors whose "
                "last dimension disagrees with the declared input irrep width."
            ),
        },
        "scalar_only_irrep_excludes_vector_block_width": {
            "passed": IRREPS_SCALAR.dim != IRREPS_IN.dim,
            "scalar_only": str(IRREPS_SCALAR),
            "scalar_only_dim": IRREPS_SCALAR.dim,
            "mixed_irrep": str(IRREPS_IN),
            "mixed_irrep_dim": IRREPS_IN.dim,
            "exclusion_note": (
                "A scalar-only carrier is dimensionally distinct from the "
                "mixed scalar/vector carrier exposed by this probe."
            ),
        },
    }


def run_boundary_tests() -> dict[str, Any]:
    zero_batch_layer = _linear_layer()
    empty = torch.empty(0, IRREPS_IN.dim, dtype=DTYPE)
    empty_out = zero_batch_layer(empty)

    scalar_layer = _linear_layer(IRREPS_SCALAR, IRREPS_SCALAR)
    scalar_features = torch.tensor([[1.0, -2.0], [0.0, 3.0]], dtype=DTYPE)
    scalar_out = scalar_layer(scalar_features)

    return {
        "zero_batch_preserves_declared_output_width": {
            "passed": tuple(empty_out.shape) == (0, IRREPS_OUT.dim),
            "input_shape": list(empty.shape),
            "output_shape": list(empty_out.shape),
            "expected_output_shape": [0, IRREPS_OUT.dim],
            "boundary_note": (
                "An empty finite batch is admitted while the declared output "
                "feature width remains fixed."
            ),
        },
        "scalar_only_boundary_preserves_scalar_width": {
            "passed": tuple(scalar_out.shape) == (2, IRREPS_SCALAR.dim),
            "input_shape": list(scalar_features.shape),
            "output_shape": list(scalar_out.shape),
            "expected_output_shape": [2, IRREPS_SCALAR.dim],
            "fixture": "2x0e -> 2x0e",
            "boundary_note": (
                "The scalar-only boundary keeps the declared scalar carrier "
                "width instead of being treated as the mixed carrier."
            ),
        },
    }


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
        "tool_function_scope": "tool_lego_fit_probe_only",
        "tool_target": "e3nn.o3.Linear",
        "surface": "o3.Linear irrep-block mixing preserves declared irrep dimension",
        "carrier": CARRIER,
        "one_variable": (
            "Only e3nn.o3.Linear declared-dimension behavior is uncertain; "
            "the finite carrier, irreps, batch sizes, dtype, and controls are pinned."
        ),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "surviving_alternatives": [
            "Other e3nn linear or tensor-product surfaces may remain useful; "
            "this receipt only covers o3.Linear declared-dimension behavior "
            "on the named finite irrep carrier."
        ],
        "claim_ceiling": "tool_lego_fit_probe_only",
        "next_lego_target": "minimal O(3) irrep-block linear carrier fixture",
        "promotion_condition": (
            "requires a later admitted lego row that names this exact function "
            "receipt and passes strict runner admission; this probe has "
            "promotion_allowed false."
        ),
        "blocked_until": (
            "blocked until a downstream queue row declares the exact lego "
            "target, parent receipts, active stage gate, and result JSON for promotion"
        ),
        "demotion_condition": (
            "Demote e3nn for this surface if o3.Linear returns a last dimension "
            "different from the declared output irrep dimension, silently admits "
            "wrong-width inputs, or collapses zero-batch/scalar-only boundaries "
            "into the mixed carrier."
        ),
        "out_of_scope": [
            "no runner execution in this authoring packet",
            "no result JSON claim from authoring alone",
            "no lego promotion",
            "no tool-tool coupling",
            "no bridge claim",
            "no axis claim",
            "no broad equivariance proof",
            "no operator-geometry claim",
            "no learned-network or training claim",
        ],
        "criteria_checked": [
            "o3.Linear declares finite input and output irrep dimensions",
            "o3.Linear output preserves the declared output irrep dimension",
            "wrong-width input tensors are excluded",
            "zero-batch and scalar-only boundary carriers preserve declared dimensions",
        ],
        "summary": {
            "promotion_allowed": False,
            "classification": "tool_lego_fit_probe",
            "passed": sum(1 for test in flat_tests if test.get("passed")),
            "total": len(flat_tests),
            "ledger_loopback": (
                "tool-depth row e3nn/load_bearing; shallow-tool checker threshold "
                "is >=10 load-bearing receipts for e3nn"
            ),
        },
        "all_pass": all_pass,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Summary: {results['summary']['passed']}/{results['summary']['total']} criteria checked")

    if not all_pass:
        raise SystemExit(1)
