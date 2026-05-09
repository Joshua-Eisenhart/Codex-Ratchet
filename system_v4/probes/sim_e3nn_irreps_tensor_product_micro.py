#!/usr/bin/env python3
"""e3nn irreps tensor product micro probe.

Tool-stage scope:
  - one tool: e3nn
  - one API surface: o3.Irreps plus tensor product layers on tiny O(3) irreps
  - one tiny claim: e3nn parses bounded irrep declarations, tensor product
    layers preserve declared input/output dimensions, and incompatible feature
    widths are rejected.

This is pre-lego evidence. It does not promote a lego, coupling, bridge, broad
equivariance claim, or operator-geometry claim.
"""

import json
import os

import torch
from e3nn import o3

classification = "canonical"
NAME = "sim_e3nn_irreps_tensor_product_micro"
PROBE_FAMILY = "e3nn_irreps_tensor_product_micro"
CONSTRAINT_SET = "bounded_o3_irreps_tensor_product_dimension_fixtures"

_NOT_USED_REASON = (
    "not used: this micro probe isolates e3nn o3.Irreps and tensor product "
    "layer dimension behavior only; cross-tool coupling and lego promotion "
    "are out of scope."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": (
            "PyTorch is supportive: e3nn tensor product layers consume and "
            "return torch.Tensor feature fixtures, but e3nn supplies the "
            "load-bearing irrep and tensor-product semantics."
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
            "e3nn is load-bearing: o3.Irreps, "
            "o3.FullyConnectedTensorProduct, and o3.TensorProduct produce "
            "the declared-dimension and width-rejection verdicts."
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

TORCH_SEED = 1729
IRREPS_VECTOR = o3.Irreps("1x1o")
IRREPS_VECTOR_PAIR_OUT = o3.Irreps("1x0e + 1x1e + 1x2e")
IRREPS_MIXED = o3.Irreps("1x0e + 1x1o")
IRREPS_SCALAR_ONLY = o3.Irreps("2x0e")


def _fully_connected_layer():
    return o3.FullyConnectedTensorProduct(
        IRREPS_VECTOR,
        IRREPS_VECTOR,
        IRREPS_VECTOR_PAIR_OUT,
    )


def _explicit_tensor_product_layer():
    return o3.TensorProduct(
        IRREPS_VECTOR,
        IRREPS_VECTOR,
        IRREPS_VECTOR_PAIR_OUT,
        instructions=[
            (0, 0, 0, "uuu", True),
            (0, 0, 1, "uuu", True),
            (0, 0, 2, "uuu", True),
        ],
    )


def _flatten_sections(*sections):
    flat = []
    for section in sections:
        for value in section.values():
            if isinstance(value, dict) and "passed" in value:
                flat.append(value)
    return flat


def run_positive_tests():
    torch.manual_seed(TORCH_SEED)
    batch = 2
    x = torch.randn(batch, IRREPS_VECTOR.dim)
    y = torch.randn(batch, IRREPS_VECTOR.dim)

    fully_connected = _fully_connected_layer()
    explicit_tensor_product = _explicit_tensor_product_layer()
    fc_out = fully_connected(x, y)
    explicit_out = explicit_tensor_product(x, y)

    return {
        "irreps_parse_declared_dimensions": {
            "passed": (
                IRREPS_VECTOR.dim == 3
                and IRREPS_MIXED.dim == 4
                and IRREPS_VECTOR_PAIR_OUT.dim == 9
            ),
            "fixtures": {
                "vector": str(IRREPS_VECTOR),
                "mixed": str(IRREPS_MIXED),
                "vector_pair_out": str(IRREPS_VECTOR_PAIR_OUT),
            },
            "observed_dims": {
                "vector": IRREPS_VECTOR.dim,
                "mixed": IRREPS_MIXED.dim,
                "vector_pair_out": IRREPS_VECTOR_PAIR_OUT.dim,
            },
            "expected_dims": {
                "vector": 3,
                "mixed": 4,
                "vector_pair_out": 9,
            },
        },
        "fully_connected_tensor_product_preserves_declared_output_width": {
            "passed": tuple(fc_out.shape) == (batch, IRREPS_VECTOR_PAIR_OUT.dim),
            "input_shape": list(x.shape),
            "output_shape": list(fc_out.shape),
            "expected_output_shape": [batch, IRREPS_VECTOR_PAIR_OUT.dim],
            "fixture": "1x1o x 1x1o -> 1x0e + 1x1e + 1x2e",
        },
        "explicit_tensor_product_preserves_declared_output_width": {
            "passed": tuple(explicit_out.shape) == (batch, IRREPS_VECTOR_PAIR_OUT.dim),
            "input_shape": list(x.shape),
            "output_shape": list(explicit_out.shape),
            "expected_output_shape": [batch, IRREPS_VECTOR_PAIR_OUT.dim],
            "fixture": "manual instructions for 1o x 1o -> 0e + 1e + 2e",
        },
    }


def run_negative_tests():
    layer = _fully_connected_layer()
    good = torch.randn(1, IRREPS_VECTOR.dim)
    bad = torch.randn(1, IRREPS_VECTOR.dim + 1)
    rejected = False
    error_type = None
    error_message = None

    try:
        layer(bad, good)
    except Exception as exc:
        rejected = True
        error_type = type(exc).__name__
        error_message = str(exc)

    scalar_only = o3.Irreps("1x0e")

    return {
        "incompatible_feature_width_is_rejected": {
            "passed": rejected,
            "expected": "feature width 4 is rejected for declared 1x1o input dim 3",
            "bad_input_shape": list(bad.shape),
            "good_input_shape": list(good.shape),
            "error_type": error_type,
            "error_message": error_message,
            "exclusion_note": (
                "The layer must not silently accept tensors whose last "
                "dimension disagrees with the declared input irrep width."
            ),
        },
        "scalar_only_irrep_does_not_admit_vector_width": {
            "passed": scalar_only.dim != IRREPS_VECTOR.dim,
            "scalar_only": str(scalar_only),
            "scalar_only_dim": scalar_only.dim,
            "vector_irrep": str(IRREPS_VECTOR),
            "vector_dim": IRREPS_VECTOR.dim,
            "exclusion_note": (
                "A scalar-only declaration is dimensionally distinct from a "
                "vector irrep declaration in this tiny fixture."
            ),
        },
    }


def run_boundary_tests():
    zero_batch_layer = _fully_connected_layer()
    empty_x = torch.empty(0, IRREPS_VECTOR.dim)
    empty_y = torch.empty(0, IRREPS_VECTOR.dim)
    empty_out = zero_batch_layer(empty_x, empty_y)

    scalar_layer = o3.FullyConnectedTensorProduct(
        IRREPS_SCALAR_ONLY,
        o3.Irreps("1x0e"),
        IRREPS_SCALAR_ONLY,
    )
    scalar_x = torch.tensor([[1.0, -2.0], [0.0, 3.0]])
    scalar_y = torch.tensor([[0.5], [2.0]])
    scalar_out = scalar_layer(scalar_x, scalar_y)

    return {
        "zero_batch_preserves_declared_output_width": {
            "passed": tuple(empty_out.shape) == (0, IRREPS_VECTOR_PAIR_OUT.dim),
            "input_shape": list(empty_x.shape),
            "output_shape": list(empty_out.shape),
            "expected_output_shape": [0, IRREPS_VECTOR_PAIR_OUT.dim],
            "boundary_note": (
                "Zero rows are allowed as an empty batch while the declared "
                "feature width remains enforced."
            ),
        },
        "scalar_only_tensor_product_preserves_scalar_width": {
            "passed": tuple(scalar_out.shape) == (2, IRREPS_SCALAR_ONLY.dim),
            "input_shape": list(scalar_x.shape),
            "output_shape": list(scalar_out.shape),
            "expected_output_shape": [2, IRREPS_SCALAR_ONLY.dim],
            "fixture": "2x0e x 1x0e -> 2x0e",
            "boundary_note": (
                "Scalar-only irreps remain in the same declared scalar feature "
                "width for this bounded product layer fixture."
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
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "surviving_alternatives": [
            "Other e3nn O(3) operations may remain useful; this micro receipt "
            "only covers Irreps parsing and bounded tensor product layer "
            "dimension behavior."
        ],
        "claim_ceiling": "tool_function_micro_only",
        "next_lego_target": "minimal irrep tensor-product fixture before operator geometry claims",
        "promotion_condition": (
            "requires a later admitted lego row that names this exact function "
            "receipt and passes strict runner admission; this MICRO row does "
            "not promote the lego"
        ),
        "blocked_until": (
            "blocked until a downstream queue row declares the exact lego "
            "target, parent receipts, and active stage gate for promotion"
        ),
        "demotion_condition": (
            "Demote e3nn for this function surface if o3.Irreps reports "
            "incorrect dimensions for the bounded fixtures, if "
            "FullyConnectedTensorProduct or TensorProduct returns a last "
            "dimension different from the declared output irrep dimension, or "
            "if incompatible feature widths are silently accepted."
        ),
        "out_of_scope": [
            "no lego promotion",
            "no tool-tool coupling",
            "no bridge claim",
            "no broad equivariance proof",
            "no operator-geometry claim",
            "no proof of the whole e3nn library",
            "no training, optimization, or learned-weight claim",
        ],
        "criteria_checked": [
            "e3nn o3.Irreps parses tiny scalar/vector declarations",
            "FullyConnectedTensorProduct preserves declared output dimension",
            "TensorProduct with explicit instructions preserves declared output dimension",
            "incompatible feature width is rejected",
            "zero-batch and scalar-only boundary fixtures preserve declared dimensions",
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
