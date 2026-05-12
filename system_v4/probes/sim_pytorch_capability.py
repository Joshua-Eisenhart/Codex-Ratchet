#!/usr/bin/env python3
"""
sim_pytorch_capability.py -- Tool-capability isolation sim for pytorch.

Governing rule (durable, owner+Hermes 2026-04-13):
pytorch is load_bearing across the ratchet (autograd, nn.Module forward/backward,
tensor ops) but had no bounded capability probe. This exercises ONLY the
primitives we rely on -- NOT the full ratchet.

Decorative = `import torch` with no autograd/backward actually run.
Load-bearing = gradient values / tensor shape ops are the claim.
"""

classification = "canonical"

import json
import os

from receipt_boundary import apply_default_receipt_boundary

_NOT_USED_REASON = (
    "not used: this bounded PyTorch capability receipt isolates tensor, autograd, "
    "nn.Module, optimizer, and shape APIs; other tool families require separate receipts."
)

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "under test"},
    "pyg":       {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "z3":        {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "cvc5":      {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "sympy":     {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "clifford":  {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "e3nn":      {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "xgi":       {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "toponetx":  {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "gudhi":     {"tried": False, "used": False, "reason": _NOT_USED_REASON},
}

TOOL_INTEGRATION_DEPTH = {
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
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "load-bearing capability under test: PyTorch autograd backward/grad, "
        "nn.Module forward/backward, optimizer step, tensor shape, and matmul APIs decide the receipt verdicts."
    )
    TORCH_OK = True
    TORCH_VERSION = torch.__version__
except Exception as exc:
    TORCH_OK = False
    TORCH_VERSION = None
    TOOL_MANIFEST["pytorch"]["reason"] = f"not installed: {exc}"


def run_positive_tests():
    r = {}
    if not TORCH_OK:
        r["pytorch_available"] = {"pass": False, "detail": "pytorch missing"}
        return r
    r["pytorch_available"] = {"pass": True, "version": TORCH_VERSION}

    # 1. Autograd on scalar loss: d/dx (x^2) at x=3 is 6.
    x = torch.tensor(3.0, requires_grad=True)
    loss = x ** 2
    loss.backward()
    r["autograd_scalar"] = {
        "pass": abs(float(x.grad) - 6.0) < 1e-6,
        "grad": float(x.grad),
        "expected": 6.0,
    }

    # 2. Autograd on vector inner-product: d/dw (w . v) = v.
    w = torch.tensor([1.0, 2.0, 3.0], requires_grad=True)
    v = torch.tensor([0.5, -1.0, 2.0])
    out = torch.dot(w, v)
    out.backward()
    r["autograd_vector_dot"] = {
        "pass": torch.allclose(w.grad, v),
        "grad": w.grad.tolist(),
        "expected": v.tolist(),
    }

    # 3. nn.Module forward/backward: tiny linear layer, one SGD step reduces MSE loss.
    torch.manual_seed(0)
    model = torch.nn.Linear(3, 1, bias=False)
    x_in = torch.randn(16, 3)
    y_true = x_in.sum(dim=1, keepdim=True)
    opt = torch.optim.SGD(model.parameters(), lr=0.1)
    loss_fn = torch.nn.MSELoss()
    l0 = float(loss_fn(model(x_in), y_true))
    opt.zero_grad()
    l = loss_fn(model(x_in), y_true)
    l.backward()
    opt.step()
    l1 = float(loss_fn(model(x_in), y_true))
    r["nn_module_step_reduces_loss"] = {
        "pass": l1 < l0,
        "loss_before": l0,
        "loss_after": l1,
    }

    # 4. Tensor shape ops: reshape / permute / matmul.
    A = torch.arange(12, dtype=torch.float32).reshape(3, 4)
    B = A.permute(1, 0)
    C = A @ B  # (3,4)@(4,3) = (3,3)
    r["shape_ops"] = {
        "pass": A.shape == (3, 4) and B.shape == (4, 3) and C.shape == (3, 3),
        "A_shape": list(A.shape),
        "B_shape": list(B.shape),
        "C_shape": list(C.shape),
    }

    return r


def run_negative_tests():
    r = {}
    if not TORCH_OK:
        r["pytorch_available"] = {"pass": False, "detail": "pytorch missing"}
        return r

    # Tensor without requires_grad cannot backward.
    x = torch.tensor(2.0)
    raised = False
    err = None
    try:
        (x ** 2).backward()
    except Exception as exc:
        raised = True
        err = type(exc).__name__
    r["no_requires_grad_raises"] = {
        "pass": raised,
        "error_type": err,
    }

    # Shape mismatch in matmul must raise.
    raised2 = False
    err2 = None
    try:
        _ = torch.randn(3, 4) @ torch.randn(5, 2)
    except Exception as exc:
        raised2 = True
        err2 = type(exc).__name__
    r["shape_mismatch_raises"] = {
        "pass": raised2,
        "error_type": err2,
    }

    # Non-trainable scalar: 0 * x has zero gradient, not NaN.
    w = torch.tensor(5.0, requires_grad=True)
    loss = 0.0 * w
    loss.backward()
    r["zero_gradient_is_zero"] = {
        "pass": float(w.grad) == 0.0,
        "grad": float(w.grad),
    }
    return r


def run_boundary_tests():
    r = {}
    if not TORCH_OK:
        r["pytorch_available"] = {"pass": False, "detail": "pytorch missing"}
        return r

    # Empty tensor shape ops.
    e = torch.zeros(0, 3)
    r["empty_tensor"] = {
        "pass": e.shape == (0, 3) and e.numel() == 0,
        "shape": list(e.shape),
    }

    # Large-ish autograd (100-dim quadratic): grad = 2*x.
    x = torch.randn(100, requires_grad=True)
    loss = (x ** 2).sum()
    loss.backward()
    r["highdim_autograd"] = {
        "pass": torch.allclose(x.grad, 2 * x.detach(), atol=1e-5),
    }

    # Double backward (grad of grad).
    x = torch.tensor(3.0, requires_grad=True)
    y = x ** 3  # dy/dx = 3x^2, d2y/dx2 = 6x.
    grad1 = torch.autograd.grad(y, x, create_graph=True)[0]
    grad2 = torch.autograd.grad(grad1, x)[0]
    r["double_backward"] = {
        "pass": abs(float(grad1) - 27.0) < 1e-5 and abs(float(grad2) - 18.0) < 1e-5,
        "first": float(grad1),
        "second": float(grad2),
    }

    return r


def _all_pass(section):
    return all(bool(v.get("pass", False)) for v in section.values())


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    summary = {
        "positive_all_pass": _all_pass(pos),
        "negative_all_pass": _all_pass(neg),
        "boundary_all_pass": _all_pass(bnd),
    }
    summary["all_pass"] = all(summary.values())

    results = {
        "name": "sim_pytorch_capability",
        "purpose": "Tool-capability isolation probe for pytorch -- primitives only, not full ratchet.",
        "pytorch_version": TORCH_VERSION,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "witness_file": "system_v4/probes/sim_bridge_to_rhoab_construction.py",
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
        "classification": "canonical",
        "surviving_alternatives": [
            "This receipt covers only bounded PyTorch primitive capability; it does not promote density-matrix, QIT, bridge, axis, GStack, or nonclassical admission claims."
        ],
        "demotion_condition": (
            "Demote this PyTorch capability receipt if scalar/vector autograd, "
            "module training step, tensor shape/matmul checks, gradient error controls, "
            "empty tensor behavior, high-dimensional gradient, or double-backward controls fail on rerun."
        ),
        "out_of_scope": [
            "no density-matrix lego promotion",
            "no QIT engine claim",
            "no bridge claim",
            "no axis claim",
            "no GStack claim",
            "no nonclassical admission",
        ],
    }
    results = apply_default_receipt_boundary(
        results,
        source_name="sim_pytorch_capability",
        target="Use as bounded PyTorch primitive capability evidence before exact tensor/autograd lego-fit or coupling packets.",
    )

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "pytorch_capability_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"summary.all_pass = {summary['all_pass']}")
