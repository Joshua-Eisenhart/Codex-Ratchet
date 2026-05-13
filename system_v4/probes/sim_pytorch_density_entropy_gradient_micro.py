#!/usr/bin/env python3
"""PyTorch density-matrix entropy gradient micro probe.

Tool-stage scope:
  - one tool: PyTorch/autograd
  - one API surface: torch.linalg.eigvalsh plus torch.autograd.grad
  - one tiny claim: PyTorch returns finite entropy gradients for a normalized
    positive 2x2 density matrix and rejects detached or non-PSD misuse.

This is pre-lego evidence. It does not promote a lego, coupling, bridge, or
stack claim.
"""

from __future__ import annotations

import json
import os

import torch

from receipt_boundary import apply_default_receipt_boundary

classification = "canonical"
NAME = "sim_pytorch_density_entropy_gradient_micro"
PROBE_FAMILY = "pytorch_density_entropy_gradient_micro"
CONSTRAINT_SET = "bounded_two_by_two_density_entropy_fixture"

_NOT_USED_REASON = (
    "not used: this micro probe isolates PyTorch eigvalsh and autograd over a "
    "2x2 density matrix; graph, solver, topology, and lego promotion are out of scope."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": (
            "PyTorch is load-bearing: torch.linalg.eigvalsh and "
            "torch.autograd.grad produce the entropy and gradient verdicts."
        ),
    },
    "pyg": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "z3": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "cvc5": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "sympy": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "clifford": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "e3nn": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "xgi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "toponetx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "gudhi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
}

TOOL_INTEGRATION_DEPTH = {tool: None for tool in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"

DTYPE = torch.float64
EPS = 1e-10


def density_from_theta(theta):
    """Map two unconstrained parameters to a trace-one PSD 2x2 matrix."""
    p = torch.sigmoid(theta[0])
    limit = torch.sqrt(torch.clamp(p * (1.0 - p), min=EPS))
    offdiag = 0.25 * torch.tanh(theta[1]) * limit
    return torch.stack(
        (
            torch.stack((p, offdiag)),
            torch.stack((offdiag, 1.0 - p)),
        )
    )


def entropy_from_density(rho):
    if not torch.allclose(torch.trace(rho), torch.tensor(1.0, dtype=rho.dtype), atol=1e-8):
        raise ValueError("density matrix trace must be one")
    if not torch.allclose(rho, rho.T, atol=1e-8):
        raise ValueError("density matrix must be symmetric Hermitian in this real fixture")
    eigvals = torch.linalg.eigvalsh(rho)
    if bool(torch.min(eigvals).detach() < -1e-8):
        raise ValueError("density matrix must be positive semidefinite")
    clipped = torch.clamp(eigvals, min=EPS)
    return -torch.sum(clipped * torch.log(clipped))


def entropy_from_theta(theta):
    return entropy_from_density(density_from_theta(theta))


def finite_difference_gradient(theta, step=1e-5):
    values = []
    for index in range(theta.numel()):
        direction = torch.zeros_like(theta)
        direction[index] = step
        plus = entropy_from_theta((theta.detach() + direction).clone())
        minus = entropy_from_theta((theta.detach() - direction).clone())
        values.append(float((plus - minus) / (2.0 * step)))
    return torch.tensor(values, dtype=DTYPE)


def _as_list(tensor):
    return [float(value) for value in tensor.detach().reshape(-1)]


def run_positive_tests():
    theta = torch.tensor([0.4, -0.3], dtype=DTYPE, requires_grad=True)
    entropy = entropy_from_theta(theta)
    grad = torch.autograd.grad(entropy, theta, create_graph=True)[0]
    finite_grad = finite_difference_gradient(theta)
    rho = density_from_theta(theta)
    eigvals = torch.linalg.eigvalsh(rho)

    return {
        "density_entropy_gradient_matches_finite_difference": {
            "passed": torch.allclose(grad.detach(), finite_grad, atol=1e-5, rtol=1e-5),
            "autograd_gradient": _as_list(grad),
            "finite_difference_gradient": _as_list(finite_grad),
            "entropy": float(entropy.detach()),
        },
        "density_matrix_is_normalized_and_psd": {
            "passed": (
                abs(float(torch.trace(rho).detach()) - 1.0) < 1e-10
                and float(torch.min(eigvals).detach()) >= -1e-10
            ),
            "trace": float(torch.trace(rho).detach()),
            "eigvals": _as_list(eigvals),
        },
    }


def run_negative_tests():
    detached_raised = False
    detached_error = ""
    detached = torch.tensor([0.2, 0.1], dtype=DTYPE)
    try:
        torch.autograd.grad(entropy_from_theta(detached), detached)
    except RuntimeError as exc:
        detached_raised = True
        detached_error = type(exc).__name__

    non_psd_raised = False
    non_psd_error = ""
    bad_rho = torch.tensor([[0.5, 0.75], [0.75, 0.5]], dtype=DTYPE)
    try:
        entropy_from_density(bad_rho)
    except ValueError as exc:
        non_psd_raised = True
        non_psd_error = type(exc).__name__

    return {
        "detached_parameters_excluded": {
            "passed": detached_raised,
            "expected": "autograd.grad rejects inputs without a gradient graph",
            "error_type": detached_error,
        },
        "non_psd_density_excluded": {
            "passed": non_psd_raised,
            "expected": "entropy fixture rejects a trace-one matrix with a negative eigenvalue",
            "error_type": non_psd_error,
            "eigvals": _as_list(torch.linalg.eigvalsh(bad_rho)),
        },
    }


def run_boundary_tests():
    mixed_theta = torch.tensor([0.0, 0.0], dtype=DTYPE, requires_grad=True)
    mixed_entropy = entropy_from_theta(mixed_theta)
    mixed_grad = torch.autograd.grad(mixed_entropy, mixed_theta, create_graph=True)[0]

    near_pure_theta = torch.tensor([12.0, 0.0], dtype=DTYPE, requires_grad=True)
    near_pure_entropy = entropy_from_theta(near_pure_theta)
    near_pure_grad = torch.autograd.grad(near_pure_entropy, near_pure_theta, create_graph=True)[0]

    return {
        "maximally_mixed_boundary_has_zero_gradient": {
            "passed": torch.allclose(mixed_grad.detach(), torch.zeros_like(mixed_grad), atol=1e-8),
            "expected_entropy": float(torch.log(torch.tensor(2.0, dtype=DTYPE))),
            "entropy": float(mixed_entropy.detach()),
            "gradient": _as_list(mixed_grad),
        },
        "near_pure_boundary_gradient_remains_finite": {
            "passed": bool(torch.isfinite(near_pure_entropy).item() and torch.all(torch.isfinite(near_pure_grad)).item()),
            "entropy": float(near_pure_entropy.detach()),
            "gradient": _as_list(near_pure_grad),
            "eigvals": _as_list(torch.linalg.eigvalsh(density_from_theta(near_pure_theta))),
        },
    }


def _flatten_sections(*sections):
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
            "Higher-dimensional density matrices, complex Hermitian inputs, PyG message passing, and bridge claims remain separate future micro surfaces."
        ],
        "demotion_condition": (
            "Demote PyTorch for this surface if eigvalsh/autograd.grad fail to "
            "produce finite entropy gradients on normalized PSD matrices, if "
            "detached inputs are silently accepted, or if non-PSD matrices are "
            "admitted by the fixture."
        ),
        "out_of_scope": [
            "no PyG message passing",
            "no density-matrix lego promotion",
            "no tool-tool coupling",
            "no bridge claim",
            "no proof of the whole PyTorch linear algebra surface",
        ],
        "criteria_checked": [
            "PyTorch eigvalsh entropy on trace-one PSD density matrix",
            "PyTorch autograd entropy gradient against finite difference",
            "detached and non-PSD misuse exclusion",
            "maximally mixed and near-pure boundary behavior",
        ],
        "operation_sequence": [
            "map two real parameters to one normalized symmetric positive 2x2 density matrix",
            "compute eigenvalues with torch.linalg.eigvalsh",
            "compute von Neumann entropy from clipped eigenvalues",
            "differentiate entropy with torch.autograd.grad",
            "compare the autograd gradient against a finite-difference baseline",
            "run detached-parameter and non-PSD density controls",
            "run maximally mixed and near-pure boundary controls",
        ],
        "carrier_topology": (
            "two-parameter real chart into trace-one positive 2x2 density matrices; "
            "no graph, topology, manifold, or tool-coupling carrier"
        ),
        "observable": (
            "density trace, eigenvalues, entropy scalar, entropy-gradient vector, finite-difference gradient, "
            "misuse exceptions, and boundary-gradient finiteness"
        ),
        "pass_fail_predicate": (
            "density is normalized and PSD, autograd entropy gradient matches finite differences, detached parameters "
            "and non-PSD matrices are rejected, maximally mixed gradient is zero, and near-pure entropy gradient is finite"
        ),
        "graveyards": [
            "detached parameters are rejected by autograd",
            "trace-one matrix with a negative eigenvalue is rejected",
            "nonzero maximally mixed gradient would falsify the boundary control",
        ],
        "baselines": [
            "finite-difference entropy gradient",
            "closed trace-one PSD checks by eigenvalue readout",
            "maximally mixed entropy and zero-gradient boundary",
        ],
        "alternative_formulations": [
            "SymPy exact 2x2 eigenvalue entropy derivative",
            "QuTiP density-object entropy-gradient finite difference",
            "larger Hermitian density-matrix chart",
            "complex Hermitian off-diagonal fixture",
        ],
        "tool_function_needs": {
            "pytorch": [
                "torch.linalg.eigvalsh",
                "torch.autograd.grad",
                "torch.trace",
                "torch.allclose",
                "torch.isfinite",
            ]
        },
        "lego_coupling_target": "density_matrix_entropy_gradient_micro",
        "summary": {"passed": sum(1 for test in flat_tests if test.get("passed")), "total": len(flat_tests)},
        "all_pass": all_pass,
    }
    results = apply_default_receipt_boundary(
        results,
        source_name=NAME,
        target=(
            "Use as bounded PyTorch eigvalsh/autograd entropy-gradient function evidence "
            "before density-matrix or entropy-gradient lego-fit packets."
        ),
    )

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Summary: {results['summary']['passed']}/{results['summary']['total']} passed")

    if not all_pass:
        raise SystemExit(1)
