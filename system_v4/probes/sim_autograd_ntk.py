#!/usr/bin/env python3
"""
sim_autograd_ntk -- Neural Tangent Kernel on a 2-layer linear net.
K(x, x') = <nabla_theta f(x;theta), nabla_theta f(x';theta)>.
For f(x) = w2^T W1 x with W1 in R^{h x d}, w2 in R^h, the NTK has closed form:
K(x,x') = ||w2||^2 * (x . x') + (W1 x).(W1 x').

pytorch load_bearing: per-sample parameter gradients via autograd.grad; closed
form is the cross-check.
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


def flat_grad(f, params):
    gs = torch.autograd.grad(f, params, retain_graph=True, create_graph=False)
    return torch.cat([g.reshape(-1) for g in gs])


def run_positive_tests():
    r = {}
    torch.manual_seed(5)
    d, h = 4, 6
    W1 = torch.randn(h, d, dtype=torch.float64, requires_grad=True)
    w2 = torch.randn(h, dtype=torch.float64, requires_grad=True)
    X = torch.randn(5, d, dtype=torch.float64)

    def f(x):
        return w2 @ (W1 @ x)

    N = X.shape[0]
    K_auto = np.zeros((N, N))
    grads = []
    for i in range(N):
        g = flat_grad(f(X[i]), [W1, w2])
        grads.append(g.detach().numpy())
    G = np.stack(grads)  # N x P
    K_auto = G @ G.T

    # Closed form
    with torch.no_grad():
        w2n2 = float((w2 * w2).sum().item())
        XW = (X @ W1.T).numpy()  # N x h
        Xn = X.numpy()
        K_closed = w2n2 * (Xn @ Xn.T) + XW @ XW.T
    err = float(np.linalg.norm(K_auto - K_closed) / np.linalg.norm(K_closed))
    r["ntk_matches_closed_form"] = {"rel_err": err, "passed": err < 1e-10}
    # PSD check
    eigs = np.linalg.eigvalsh(K_auto)
    r["ntk_psd"] = {"min_eig": float(eigs.min()), "passed": eigs.min() > -1e-10}
    return r


def run_negative_tests():
    r = {}
    # Orthogonal inputs with zero inner product in BOTH layers => NTK off-diagonal should be ~0 only
    # if we pick a special w2 and W1. Simpler: if we ZERO all params, grads are zero => K = 0.
    torch.manual_seed(0)
    d, h = 3, 4
    W1 = torch.zeros(h, d, dtype=torch.float64, requires_grad=True)
    w2 = torch.zeros(h, dtype=torch.float64, requires_grad=True)
    x = torch.randn(d, dtype=torch.float64)
    # f(x) = 0 identically; grad w.r.t. W1 is w2 outer x = 0; w.r.t. w2 is W1 x = 0.
    g = flat_grad(w2 @ (W1 @ x), [W1, w2])
    r["zero_params_zero_grad"] = {"grad_norm": float(torch.linalg.norm(g)),
                                  "passed": float(torch.linalg.norm(g)) < 1e-12}
    return r


def run_boundary_tests():
    r = {}
    # Single input: K is 1x1 positive scalar
    torch.manual_seed(9)
    d, h = 3, 5
    W1 = torch.randn(h, d, dtype=torch.float64, requires_grad=True)
    w2 = torch.randn(h, dtype=torch.float64, requires_grad=True)
    x = torch.randn(d, dtype=torch.float64)
    g = flat_grad(w2 @ (W1 @ x), [W1, w2])
    k = float((g * g).sum().item())
    w2n2 = float((w2 * w2).sum().item())
    closed = w2n2 * float((x * x).sum().item()) + float(((W1 @ x) * (W1 @ x)).sum().item())
    r["single_point_ntk"] = {"auto": k, "closed": closed,
                             "passed": abs(k - closed) / closed < 1e-10}
    return r


if __name__ == "__main__":
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "per-sample parameter gradients via autograd.grad; NTK assembled from them"
    TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"
    results = {
        "name": "sim_autograd_ntk",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "autograd_ntk_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
