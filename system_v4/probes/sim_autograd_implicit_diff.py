#!/usr/bin/env python3
"""
sim_autograd_implicit_diff -- implicit function theorem for root of
F(x, theta) = x - tanh(theta * x) - theta = 0. Compare:
  (a) dx/dtheta via IFT:   -(dF/dx)^{-1} (dF/dtheta)
  (b) dx/dtheta via autograd on unrolled Newton iterations.

pytorch load_bearing: autograd through unrolled iterative solver; IFT cross-check.
"""
import json, os
import numpy as np

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": "not needed"}
                 for k in ["pytorch","pyg","z3","cvc5","sympy","clifford",
                           "geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"


def F(x, theta):
    return x - torch.tanh(theta * x) - theta


def newton_solve(theta, x0=None, n_iter=40):
    if x0 is None:
        x = theta.clone()
    else:
        x = x0
    for _ in range(n_iter):
        fx = F(x, theta)
        # dF/dx = 1 - theta * (1 - tanh(theta x)^2)
        dfdx = 1.0 - theta * (1.0 - torch.tanh(theta * x)**2)
        x = x - fx / dfdx
    return x


def run_positive_tests():
    r = {}
    for theta_val in [0.3, 0.7, -0.4]:
        theta = torch.tensor(theta_val, dtype=torch.float64, requires_grad=True)
        x_star = newton_solve(theta)
        x_star.backward()
        g_unroll = theta.grad.item()

        # IFT: dx/dtheta = -(dF/dx)^-1 * dF/dtheta
        with torch.no_grad():
            xv = x_star.item(); tv = theta.item()
            dFdx = 1.0 - tv * (1.0 - np.tanh(tv * xv)**2)
            dFdtheta = -xv * (1.0 - np.tanh(tv * xv)**2) - 1.0
            g_ift = -dFdtheta / dFdx
        err = abs(g_unroll - g_ift) / (abs(g_ift) + 1e-12)
        r[f"theta={theta_val}"] = {"unroll": g_unroll, "ift": g_ift,
                                   "rel_err": err, "passed": err < 1e-8}
    return r


def run_negative_tests():
    r = {}
    # At theta=1 with x=0 init, dF/dx = 1 - 1*(1 - 0) = 0; Newton undefined there.
    # Use theta near 1 with perturbed init; ensure Newton doesn't blow up with proper init.
    theta = torch.tensor(0.99, dtype=torch.float64, requires_grad=True)
    x0 = torch.tensor(1.5, dtype=torch.float64)
    x_star = newton_solve(theta, x0=x0, n_iter=60)
    res = abs(F(x_star, theta).item())
    r["near_singular_converges"] = {"residual": res, "passed": res < 1e-8}
    return r


def run_boundary_tests():
    r = {}
    # theta=0: F = x - 0 - 0 = x, root x=0, dx/dtheta|0:
    # dFdx=1, dFdtheta at (0,0) = -x*(1) - 1 = -1 => dx/dtheta = 1.
    theta = torch.tensor(0.0, dtype=torch.float64, requires_grad=True)
    x_star = newton_solve(theta, x0=torch.tensor(0.1, dtype=torch.float64), n_iter=30)
    x_star.backward()
    r["theta_zero_grad_is_one"] = {"grad": theta.grad.item(),
                                   "passed": abs(theta.grad.item() - 1.0) < 1e-8}
    return r


if __name__ == "__main__":
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "autograd unrolled through Newton vs implicit function theorem"
    TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"
    results = {
        "name": "sim_autograd_implicit_diff",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "autograd_implicit_diff_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
