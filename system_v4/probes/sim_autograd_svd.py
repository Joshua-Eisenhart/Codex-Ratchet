#!/usr/bin/env python3
"""
sim_autograd_svd -- autograd through torch.linalg.svd. d sigma_k / dA_ij = u_ki v_kj
(singular value gradient). Verified vs analytic rank-1 identity and FD on low-rank matrix.

pytorch load_bearing: SVD backward (Papadopoulo/Lourakis / Ionescu) is baked into
autograd; analytic formula is Hellmann-Feynman for singular values.
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


def run_positive_tests():
    r = {}
    torch.manual_seed(3)
    # 4x3 low-rank matrix (effective rank 2) with small noise
    u = torch.randn(4, 2, dtype=torch.float64)
    v = torch.randn(3, 2, dtype=torch.float64)
    A0 = u @ v.T + 0.05 * torch.randn(4, 3, dtype=torch.float64)
    A = A0.clone().requires_grad_(True)
    U, S, Vh = torch.linalg.svd(A, full_matrices=False)
    s0 = S[0]
    s0.backward()
    g_auto = A.grad.detach().numpy().copy()

    # Analytic: d sigma_0 / dA = u_0 v_0^T
    with torch.no_grad():
        g_anal = (U[:, 0:1] @ Vh[0:1, :]).numpy()
    err = float(np.linalg.norm(g_auto - g_anal) / (np.linalg.norm(g_anal) + 1e-12))
    r["autograd_vs_rank1_formula"] = {"rel_err": err, "passed": err < 1e-9}

    # FD cross-check
    eps = 1e-5
    g_fd = np.zeros_like(g_auto)
    A_np = A0.detach().numpy()
    for i in range(4):
        for j in range(3):
            Ap = A_np.copy(); Ap[i,j] += eps
            Am = A_np.copy(); Am[i,j] -= eps
            sp = np.linalg.svd(Ap, compute_uv=False)[0]
            sm = np.linalg.svd(Am, compute_uv=False)[0]
            g_fd[i,j] = (sp - sm) / (2*eps)
    err_fd = float(np.linalg.norm(g_auto - g_fd) / (np.linalg.norm(g_fd) + 1e-12))
    r["autograd_vs_fd"] = {"rel_err": err_fd, "passed": err_fd < 1e-4}
    return r


def run_negative_tests():
    r = {}
    # SVD grad on all-zero matrix is ill-defined (zero singular values, degenerate).
    # Check that a small non-zero matrix still yields finite gradient.
    A = 1e-3 * torch.eye(3, dtype=torch.float64, requires_grad=True) + \
        torch.zeros(3, 3, dtype=torch.float64)
    A = A.detach().requires_grad_(True)
    S = torch.linalg.svd(A, full_matrices=False).S
    S[0].backward()
    g = A.grad.detach().numpy()
    r["tiny_matrix_finite_grad"] = {"grad_norm": float(np.linalg.norm(g)),
                                    "all_finite": bool(np.all(np.isfinite(g))),
                                    "passed": bool(np.all(np.isfinite(g)))}
    return r


def run_boundary_tests():
    r = {}
    # Identity matrix: singular values all 1, U=V=I, so d sigma_k/dA = e_k e_k^T.
    A = torch.eye(4, dtype=torch.float64, requires_grad=True)
    U, S, Vh = torch.linalg.svd(A, full_matrices=False)
    S[2].backward()
    g = A.grad.detach().numpy()
    expected = np.zeros((4,4)); expected[2,2] = 1.0
    err = float(np.linalg.norm(g - expected))
    r["identity_sigma_k_grad"] = {"err": err, "passed": err < 1e-9}
    return r


if __name__ == "__main__":
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "autograd through linalg.svd; validated against u v^T analytic formula"
    TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"
    results = {
        "name": "sim_autograd_svd",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "autograd_svd_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
