#!/usr/bin/env python3
"""
tool_capability_torch.py

Tier A A0.7 tool-capability probe for PyTorch autograd.

This probe keeps scope thin: pytorch is the only tool in the manifest, and each
section depends on torch tensors, autograd, or optimizers rather than on a
fallback implementation. The file is canonical by process once committed and
enqueued, but Hermes does not execute it directly.
"""

import json
import os

classification = "canonical"
NAME = "tool_capability_torch"
SCOPE_NOTE = "Tier A PyTorch capability probe: isolated tensor, autograd, optimizer, and boundary behavior only."

TOOL_MANIFEST = {
    "pytorch": {
        "tried": False,
        "used": False,
        "reason": "PyTorch is the sole tensor/autograd tool under test; gradients, optimizer steps, and tensor boundary behavior all depend on torch runtime semantics.",
    }
}

TOOL_INTEGRATION_DEPTH = {"pytorch": "load_bearing"}
CANONICAL_TOOL_NAMES = (
    "pytorch",
    "pyg",
    "z3",
    "cvc5",
    "sympy",
    "clifford",
    "geomstats",
    "e3nn",
    "rustworkx",
    "xgi",
    "toponetx",
    "gudhi",
)
for _tool_name in CANONICAL_TOOL_NAMES:
    TOOL_MANIFEST.setdefault(
        _tool_name,
        {
            "tried": False,
            "used": False,
            "reason": f"not used; {NAME} isolates PyTorch capability only",
        },
    )
    TOOL_INTEGRATION_DEPTH.setdefault(_tool_name, None)


def _row_passes(row):
    if row.get("status") == "skipped":
        return False
    keys = (
        "matches_expected",
        "loss_decreased",
        "raised_runtime_error",
        "error_contains_scalar_requirement",
        "error_mentions_float_or_complex",
        "error_mentions_grad",
    )
    hits = [bool(row[key]) for key in keys if key in row]
    if "gradient_numel" in row and "sum" in row:
        hits.append(row["gradient_numel"] == 0 and row["sum"] == 0.0)
    return bool(hits) and all(hits)


def _section_passes(section):
    return bool(section) and all(_row_passes(row) for row in section.values())

try:
    import torch

    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    torch = None
    TOOL_MANIFEST["pytorch"]["reason"] = "PyTorch import failed on this machine; queue execution will show whether torch is installed and admits the autograd probe."


def _mark_torch_used() -> None:
    TOOL_MANIFEST["pytorch"]["used"] = True


def _tensor_to_data(value):
    if value is None:
        return None
    if torch is not None and isinstance(value, torch.Tensor):
        if value.ndim == 0:
            return value.detach().cpu().item()
        return value.detach().cpu().tolist()
    if isinstance(value, dict):
        return {str(k): _tensor_to_data(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_tensor_to_data(v) for v in value]
    return value


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    if not TOOL_MANIFEST["pytorch"]["tried"]:
        results["torch_import_gate"] = {"status": "skipped", "reason": "PyTorch not importable"}
        return results

    # Positive 1: scalar autograd on a quadratic matches analytic gradients.
    x = torch.tensor([2.0, -3.0], requires_grad=True)
    loss = (x[0] ** 2) + 3.0 * x[0] * x[1] + (x[1] ** 2)
    loss.backward()
    _mark_torch_used()
    expected_grad = torch.tensor([-5.0, 0.0])
    results["quadratic_autograd_gradient"] = {
        "status": "ok",
        "expected_gradient": _tensor_to_data(expected_grad),
        "actual_gradient": _tensor_to_data(x.grad),
        "matches_expected": bool(torch.allclose(x.grad, expected_grad, atol=1e-7, rtol=0.0)),
        "loss": _tensor_to_data(loss),
    }

    # Positive 2: SGD step moves a one-parameter regression loss downward.
    weight = torch.tensor([0.0], requires_grad=True)
    feature = torch.tensor([2.0])
    target = torch.tensor([4.0])
    optimizer = torch.optim.SGD([weight], lr=0.1)
    optimizer.zero_grad()
    prediction_before = weight * feature
    loss_before = torch.mean((prediction_before - target) ** 2)
    loss_before.backward()
    optimizer.step()
    with torch.no_grad():
        prediction_after = weight * feature
        loss_after = torch.mean((prediction_after - target) ** 2)
    _mark_torch_used()
    results["sgd_single_step_regression"] = {
        "status": "ok",
        "weight_after_step": _tensor_to_data(weight),
        "loss_before": _tensor_to_data(loss_before),
        "loss_after": _tensor_to_data(loss_after),
        "loss_decreased": bool(loss_after.item() < loss_before.item()),
        "gradient_before_step": [-16.0],
    }

    # Positive 3: Jacobian-vector product survives through a nonlinear map.
    point = torch.tensor([1.5, -0.5], requires_grad=True)
    mapped = torch.stack([point[0] * point[1], point[0] ** 2 + torch.sin(point[1])])
    seed = torch.tensor([2.0, -1.0])
    jvp = torch.autograd.grad(mapped, point, grad_outputs=seed)[0]
    _mark_torch_used()
    expected_jvp = torch.tensor([-4.0, 2.1224174381])
    results["vector_jacobian_product"] = {
        "status": "ok",
        "expected_vjp": _tensor_to_data(expected_jvp),
        "actual_vjp": _tensor_to_data(jvp),
        "matches_expected": bool(torch.allclose(jvp, expected_jvp, atol=1e-6, rtol=0.0)),
        "seed": _tensor_to_data(seed),
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    if not TOOL_MANIFEST["pytorch"]["tried"]:
        results["torch_import_gate"] = {"status": "skipped", "reason": "PyTorch not importable"}
        return results

    # Negative 1: backward on a non-scalar tensor without grad_outputs is excluded.
    vector = torch.tensor([1.0, 2.0], requires_grad=True)
    try:
        (vector ** 2).backward()
        error_text = None
    except RuntimeError as exc:
        error_text = str(exc)
    _mark_torch_used()
    results["exclude_backward_on_non_scalar_without_seed"] = {
        "status": "ok",
        "raised_runtime_error": error_text is not None,
        "error_contains_scalar_requirement": bool(error_text and "scalar" in error_text.lower()),
        "error": error_text,
    }

    # Negative 2: integer tensors do not admit requires_grad=True.
    try:
        torch.tensor([1, 2, 3], dtype=torch.int64, requires_grad=True)
        int_error = None
    except RuntimeError as exc:
        int_error = str(exc)
    _mark_torch_used()
    results["exclude_integer_autograd"] = {
        "status": "ok",
        "raised_runtime_error": int_error is not None,
        "error_mentions_float_or_complex": bool(int_error and ("floating point" in int_error.lower() or "complex" in int_error.lower())),
        "error": int_error,
    }

    # Negative 3: detached outputs are excluded from autograd.grad.
    source = torch.tensor([3.0], requires_grad=True)
    detached = (source * 2.0).detach()
    try:
        torch.autograd.grad(detached, source)
        detach_error = None
    except RuntimeError as exc:
        detach_error = str(exc)
    _mark_torch_used()
    results["exclude_detached_tensor_gradient"] = {
        "status": "ok",
        "raised_runtime_error": detach_error is not None,
        "error_mentions_grad": bool(detach_error and "grad" in detach_error.lower()),
        "error": detach_error,
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    if not TOOL_MANIFEST["pytorch"]["tried"]:
        results["torch_import_gate"] = {"status": "skipped", "reason": "PyTorch not importable"}
        return results

    # Boundary 1: an optimum with zero gradient stays representable.
    optimum = torch.tensor([0.0], requires_grad=True)
    zero_loss = optimum.pow(2).sum()
    zero_loss.backward()
    _mark_torch_used()
    results["zero_gradient_optimum"] = {
        "status": "ok",
        "expected_gradient": [0.0],
        "actual_gradient": _tensor_to_data(optimum.grad),
        "matches_expected": bool(torch.allclose(optimum.grad, torch.zeros_like(optimum), atol=1e-7, rtol=0.0)),
    }

    # Boundary 2: an empty tensor reduction admits a well-defined scalar sum and gradient.
    empty = torch.empty(0, requires_grad=True)
    empty_sum = empty.sum()
    empty_sum.backward()
    _mark_torch_used()
    results["empty_tensor_sum_gradient"] = {
        "status": "ok",
        "sum": _tensor_to_data(empty_sum),
        "gradient_shape": list(empty.grad.shape),
        "gradient_numel": int(empty.grad.numel()),
    }

    # Boundary 3: float64 gradients survive at small scale without underflow to None.
    tiny = torch.tensor([1e-12], dtype=torch.float64, requires_grad=True)
    tiny_loss = (tiny ** 2).sum()
    tiny_loss.backward()
    _mark_torch_used()
    expected_tiny_grad = torch.tensor([2e-12], dtype=torch.float64)
    results["tiny_float64_gradient"] = {
        "status": "ok",
        "expected_gradient": _tensor_to_data(expected_tiny_grad),
        "actual_gradient": _tensor_to_data(tiny.grad),
        "matches_expected": bool(torch.allclose(tiny.grad, expected_tiny_grad, atol=1e-18, rtol=1e-6)),
    }

    return results


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    summary = {
        "positive_all_pass": _section_passes(positive),
        "negative_all_pass": _section_passes(negative),
        "boundary_all_pass": _section_passes(boundary),
        "promotion_allowed": False,
        "claim_ceiling": "isolated_pytorch_capability_only",
        "scope_note": SCOPE_NOTE,
    }
    summary["all_pass"] = bool(summary["positive_all_pass"] and summary["negative_all_pass"] and summary["boundary_all_pass"])
    results = {
        "name": NAME,
        "classification": classification,
        "classification_note": SCOPE_NOTE,
        "divergence_log": SCOPE_NOTE,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, sort_keys=True)
    print(f"Results written to {out_path}")
