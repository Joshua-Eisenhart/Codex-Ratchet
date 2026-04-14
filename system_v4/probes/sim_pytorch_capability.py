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

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "under test"},
    "pyg":       {"tried": False, "used": False, "reason": "separate pyg probe"},
    "z3":        {"tried": False, "used": False, "reason": "not needed"},
    "cvc5":      {"tried": False, "used": False, "reason": "not needed"},
    "sympy":     {"tried": False, "used": False, "reason": "not needed"},
    "clifford":  {"tried": False, "used": False, "reason": "not geometry-relevant"},
    "geomstats": {"tried": False, "used": False, "reason": "not geometry-relevant"},
    "e3nn":      {"tried": False, "used": False, "reason": "not geometry-relevant"},
    "rustworkx": {"tried": False, "used": False, "reason": "not graph-relevant"},
    "xgi":       {"tried": False, "used": False, "reason": "not graph-relevant"},
    "toponetx":  {"tried": False, "used": False, "reason": "not topology-relevant"},
    "gudhi":     {"tried": False, "used": False, "reason": "not topology-relevant"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "pyg": None, "z3": None, "cvc5": None, "sympy": None,
    "clifford": None, "geomstats": None, "e3nn": None,
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "capability under test -- autograd, nn.Module, tensor ops"
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
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "pytorch_capability_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"summary.all_pass = {summary['all_pass']}")
