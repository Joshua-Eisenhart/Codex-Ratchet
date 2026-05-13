#!/usr/bin/env python3
"""
sim_pytorch_autograd_gradient_micro.py

Tool-stage MICRO probe for one PyTorch/autograd function surface.

Function/API surface under test:
  torch.autograd.grad(outputs, inputs, create_graph=True)

Tiny claim:
  On a scalar differentiable constraint, torch.autograd.grad returns the
  expected first derivative, preserves the graph for a second derivative, and
  rejects detached or non-scalar misuse surfaces.

This is a function micro receipt, not a lego promotion and not a PyG graph test.
"""

from __future__ import annotations

import json
import os
from typing import Any

from receipt_boundary import apply_default_receipt_boundary


classification = "canonical"

MICRO_PACKET = {
    "tool_target": "pytorch / autograd",
    "function_surface": "torch.autograd.grad(outputs, inputs, create_graph=True)",
    "micro_claim": (
        "autograd.grad computes exact first and second derivatives for one "
        "tiny scalar constraint and rejects detached/non-scalar misuse"
    ),
    "lego_target": "minimal differentiable scalar fixture; no lego promotion",
    "function_receipt": "new",
    "prior_function_receipts": [],
    "why_this_lego": (
        "a weighted quadratic exposes gradient, Hessian, flat-axis boundary, "
        "and misuse rejection without graph or density-matrix uncertainty"
    ),
    "positive_case": "gradient and Hessian diagonal match analytic values",
    "negative_case": "detached inputs and vector outputs without grad_outputs are excluded",
    "boundary_case": "zero-weight axis produces an admitted zero gradient, not NaN",
    "demotion_condition": (
        "demote this surface if gradients silently detach, lose second-order "
        "structure, or fail to reject invalid autograd requests"
    ),
    "out_of_scope": [
        "PyG message passing",
        "density-matrix entropy",
        "lego-stage promotion",
        "tool-tool coupling",
    ],
    "loopback_target": (
        "system_v5/docs/plans/plans/TOOL_CAPABILITY_AND_INTEGRATION_LEDGER.md"
        "#pytorch--autograd"
    ),
}

TOOL_MANIFEST: dict[str, dict[str, Any]] = {
    "pytorch": {
        "tried": False,
        "used": False,
        "reason": "tool under micro test: torch.autograd.grad first/second derivatives",
    },
    "pyg": {
        "tried": False,
        "used": False,
        "reason": "not needed; no graph message passing in this function micro probe",
    },
    "z3": {
        "tried": False,
        "used": False,
        "reason": "not needed; misuse rejection is empirical runtime behavior, not SMT",
    },
    "cvc5": {
        "tried": False,
        "used": False,
        "reason": "not needed; no solver-side arithmetic claim",
    },
    "sympy": {
        "tried": False,
        "used": False,
        "reason": "not needed; analytic gradient is encoded directly in the fixture",
    },
    "clifford": {
        "tried": False,
        "used": False,
        "reason": "not needed; no geometric algebra surface",
    },
    "geomstats": {
        "tried": False,
        "used": False,
        "reason": "not needed; no manifold metric surface",
    },
    "e3nn": {
        "tried": False,
        "used": False,
        "reason": "not needed; no equivariant tensor surface",
    },
    "rustworkx": {
        "tried": False,
        "used": False,
        "reason": "not needed; no graph topology surface",
    },
    "xgi": {
        "tried": False,
        "used": False,
        "reason": "not needed; no hypergraph surface",
    },
    "toponetx": {
        "tried": False,
        "used": False,
        "reason": "not needed; no cell-complex surface",
    },
    "gudhi": {
        "tried": False,
        "used": False,
        "reason": "not needed; no persistence surface",
    },
}

TOOL_INTEGRATION_DEPTH: dict[str, str | None] = {
    "clifford": None,
    "cvc5": None,
    "e3nn": None,
    "geomstats": None,
    "gudhi": None,
    "pyg": None,
    "pytorch": "load_bearing",
    "rustworkx": None,
    "sympy": None,
    "toponetx": None,
    "xgi": None,
    "z3": None,
}

try:
    import torch

    TORCH_OK = True
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
except Exception as exc:  # pragma: no cover - runtime environment dependent
    torch = None  # type: ignore[assignment]
    TORCH_OK = False
    TOOL_MANIFEST["pytorch"]["reason"] = f"not installed or unavailable: {exc}"


def scalar_constraint(theta: Any, weights: Any | None = None, coupling: float = 0.25) -> Any:
    """Weighted quadratic scalar with one cross term."""
    if weights is None:
        weights = torch.tensor([2.0, 3.0, 5.0], dtype=theta.dtype, device=theta.device)
    return 0.5 * (weights * theta.square()).sum() + coupling * theta[0] * theta[2]


def analytic_gradient(theta: Any, weights: Any | None = None, coupling: float = 0.25) -> Any:
    if weights is None:
        weights = torch.tensor([2.0, 3.0, 5.0], dtype=theta.dtype, device=theta.device)
    grad = weights * theta
    grad = grad.clone()
    grad[0] = grad[0] + coupling * theta[2]
    grad[2] = grad[2] + coupling * theta[0]
    return grad


def run_positive_tests() -> dict[str, dict[str, Any]]:
    if not TORCH_OK:
        return {"torch_available": {"pass": False, "detail": "pytorch unavailable"}}

    theta = torch.tensor([1.25, -0.5, 0.75], dtype=torch.float64, requires_grad=True)
    value = scalar_constraint(theta)
    grad = torch.autograd.grad(value, theta, create_graph=True)[0]
    expected = analytic_gradient(theta.detach())

    hessian_diag = []
    for i in range(theta.numel()):
        second = torch.autograd.grad(grad[i], theta, retain_graph=True)[0]
        hessian_diag.append(float(second[i].detach()))

    expected_diag = [2.0, 3.0, 5.0]
    return {
        "autograd_grad_matches_analytic": {
            "pass": bool(torch.allclose(grad.detach(), expected, atol=1e-10)),
            "gradient": [float(x) for x in grad.detach()],
            "expected": [float(x) for x in expected],
        },
        "create_graph_second_derivative": {
            "pass": all(abs(a - b) < 1e-10 for a, b in zip(hessian_diag, expected_diag)),
            "hessian_diag": hessian_diag,
            "expected_diag": expected_diag,
        },
        "input_grad_field_not_populated": {
            "pass": theta.grad is None,
            "detail": "torch.autograd.grad returned the gradient without mutating theta.grad",
        },
    }


def run_negative_tests() -> dict[str, dict[str, Any]]:
    if not TORCH_OK:
        return {"torch_available": {"pass": False, "detail": "pytorch unavailable"}}

    detached_raised = False
    detached_error = ""
    detached = torch.tensor([1.0, 2.0, 3.0], dtype=torch.float64)
    try:
        torch.autograd.grad(scalar_constraint(detached), detached)
    except RuntimeError as exc:
        detached_raised = True
        detached_error = type(exc).__name__

    nonscalar_raised = False
    nonscalar_error = ""
    theta = torch.tensor([1.0, 2.0, 3.0], dtype=torch.float64, requires_grad=True)
    try:
        torch.autograd.grad(theta.square(), theta)
    except RuntimeError as exc:
        nonscalar_raised = True
        nonscalar_error = type(exc).__name__

    return {
        "detached_input_excluded": {
            "pass": detached_raised,
            "error_type": detached_error,
        },
        "nonscalar_output_without_grad_outputs_excluded": {
            "pass": nonscalar_raised,
            "error_type": nonscalar_error,
        },
    }


def run_boundary_tests() -> dict[str, dict[str, Any]]:
    if not TORCH_OK:
        return {"torch_available": {"pass": False, "detail": "pytorch unavailable"}}

    theta = torch.tensor([1.0, 4.0, -2.0], dtype=torch.float64, requires_grad=True)
    weights = torch.tensor([2.0, 0.0, 5.0], dtype=torch.float64)
    value = scalar_constraint(theta, weights=weights, coupling=0.0)
    grad = torch.autograd.grad(value, theta, create_graph=True)[0]
    if grad[1].requires_grad:
        second_axis_1 = torch.autograd.grad(grad[1], theta, retain_graph=True)[0][1]
    else:
        second_axis_1 = torch.tensor(0.0, dtype=torch.float64)

    return {
        "flat_axis_zero_gradient_is_admitted": {
            "pass": float(grad[1].detach()) == 0.0 and float(second_axis_1.detach()) == 0.0,
            "gradient": [float(x) for x in grad.detach()],
            "axis_1_second_derivative": float(second_axis_1.detach()),
            "note": "zero sensitivity is a boundary result, not an autograd failure",
        }
    }


def _all_pass(section: dict[str, dict[str, Any]]) -> bool:
    return all(bool(item.get("pass", False)) for item in section.values())


def build_results() -> dict[str, Any]:
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    summary = {
        "positive_all_pass": _all_pass(positive),
        "negative_all_pass": _all_pass(negative),
        "boundary_all_pass": _all_pass(boundary),
    }
    summary["all_pass"] = all(summary.values())

    return {
        "name": "sim_pytorch_autograd_gradient_micro",
        "tool_stage": "stage_1_2_function_micro_probe",
        "micro_packet": MICRO_PACKET,
        "probe_family": "M_torch_autograd_grad_micro",
        "constraint_set": "C_scalar_differentiable_gradient_contract",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
        "criteria_checked": [
            "C1 first derivative matches analytic gradient",
            "C2 create_graph preserves second derivative structure",
            "C3 autograd.grad does not mutate input .grad",
            "C4 detached input is excluded",
            "C5 non-scalar output without grad_outputs is excluded",
            "C6 flat-axis zero gradient is admitted as boundary",
        ],
        "operation_sequence": [
            "construct a three-coordinate float64 tensor with requires_grad=True",
            "evaluate one weighted quadratic scalar constraint with a cross term",
            "call torch.autograd.grad with create_graph=True for the first derivative",
            "differentiate first-derivative coordinates to read second-derivative diagonal entries",
            "run detached-input and non-scalar-output misuse controls",
            "run a zero-weight coordinate boundary control",
        ],
        "carrier_topology": (
            "three-coordinate real tensor carrier for one scalar differentiable constraint; "
            "no graph, density matrix, manifold, or coupled tool carrier"
        ),
        "observable": (
            "first-derivative vector, second-derivative diagonal entries, input .grad mutation state, "
            "runtime misuse exceptions, and zero-gradient boundary value"
        ),
        "pass_fail_predicate": (
            "autograd gradient equals analytic gradient, second derivatives match the weighted quadratic diagonal, "
            "input .grad remains unset, misuse controls raise RuntimeError, and zero-weight coordinate gives zero gradient"
        ),
        "graveyards": [
            "detached tensor input is rejected",
            "non-scalar output without grad_outputs is rejected",
            "zero-weight coordinate remains zero rather than inventing sensitivity",
        ],
        "baselines": [
            "closed-form weighted quadratic gradient",
            "closed-form weighted quadratic Hessian diagonal",
            "PyTorch runtime error behavior for invalid autograd requests",
        ],
        "alternative_formulations": [
            "torch.Tensor.backward scalar-gradient fixture",
            "torch.func jacrev/hessian fixture",
            "SymPy exact derivative companion for the same scalar constraint",
            "downstream density-entropy gradient fixture",
        ],
        "tool_function_needs": {
            "pytorch": [
                "torch.tensor",
                "Tensor.square",
                "torch.autograd.grad",
                "torch.allclose",
            ]
        },
        "lego_coupling_target": "differentiable_constraint_micro",
        "surviving_alternatives": [
            "PyG MessagePassing/autograd should remain a separate MICRO row",
            "density-matrix entropy gradients should remain a downstream fixture",
        ],
        "classification": classification,
        "out_of_scope_observed": [],
    }


if __name__ == "__main__":
    results = build_results()
    results = apply_default_receipt_boundary(
        results,
        source_name="sim_pytorch_autograd_gradient_micro",
        target="Use as bounded PyTorch autograd.grad function evidence before differentiable constraint or entropy-gradient lego fit packets.",
    )
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_pytorch_autograd_gradient_micro_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"summary.all_pass = {results['summary']['all_pass']}")
    if not results["summary"]["all_pass"]:
        raise SystemExit(1)
