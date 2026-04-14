#!/usr/bin/env python3
"""
sim_autograd_grad_Ic_axis0 -- gradient of von Neumann entropy S(rho(theta))
w.r.t. parameters theta, as Axis 0 candidate signal (nabla I_c).

pytorch load_bearing: autograd differentiates through eigendecomposition of a
parameterized Hermitian density matrix. Finite-difference (numpy) is decorative,
noisy cross-check only.
"""
import json, os
import numpy as np

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"


def rho_of_theta(theta):
    # 2-qubit parameterized density matrix via purification:
    #   |psi> = exp(-i sum_k theta_k H_k) |00>, rho = tr_B |psi><psi|
    # Here use a simpler route: softmax-weighted mixture of 4 pure states plus
    # small unitary rotation controlled by theta.
    d = 4
    # probabilities from first 4 params via softmax
    p = torch.softmax(theta[:4], dim=0)
    # rotation angles from next 3 params
    a, b, c = theta[4], theta[5], theta[6]
    # build a unitary U = exp(i (a X0 + b Y0 + c Z01)) on 2 qubits via matrix_exp
    X = torch.tensor([[0., 1.], [1., 0.]], dtype=torch.complex128)
    Y = torch.tensor([[0., -1j], [1j, 0.]], dtype=torch.complex128)
    Z = torch.tensor([[1., 0.], [0., -1.]], dtype=torch.complex128)
    I2 = torch.eye(2, dtype=torch.complex128)
    X0 = torch.kron(X, I2)
    Y0 = torch.kron(Y, I2)
    Z01 = torch.kron(Z, Z)
    H = a.to(torch.complex128) * X0 + b.to(torch.complex128) * Y0 + c.to(torch.complex128) * Z01
    U = torch.linalg.matrix_exp(1j * H)
    D = torch.diag(p.to(torch.complex128))
    rho = U @ D @ U.conj().T
    return rho


def vn_entropy(rho):
    evals = torch.linalg.eigvalsh(rho)
    evals = torch.clamp(evals.real, min=1e-12)
    return -(evals * torch.log(evals)).sum()


def run_positive_tests():
    r = {}
    torch.manual_seed(0)
    theta = torch.randn(7, dtype=torch.float64, requires_grad=True)
    rho = rho_of_theta(theta)
    S = vn_entropy(rho)
    S.backward()
    g_autograd = theta.grad.detach().numpy().copy()

    # Finite-difference cross-check (decorative, noisy)
    eps = 1e-5
    g_fd = np.zeros(7)
    for i in range(7):
        dt = torch.zeros(7, dtype=torch.float64)
        dt[i] = eps
        with torch.no_grad():
            Sp = vn_entropy(rho_of_theta(theta.detach() + dt)).item()
            Sm = vn_entropy(rho_of_theta(theta.detach() - dt)).item()
        g_fd[i] = (Sp - Sm) / (2 * eps)

    err = float(np.linalg.norm(g_autograd - g_fd) / (np.linalg.norm(g_fd) + 1e-12))
    r["grad_matches_fd"] = {"rel_err": err, "passed": err < 1e-4}
    r["grad_nonzero"] = {"norm": float(np.linalg.norm(g_autograd)),
                         "passed": np.linalg.norm(g_autograd) > 1e-6}
    # Take a gradient step (minimize -S, i.e. climb entropy); S should increase
    S0 = float(S.item())
    with torch.no_grad():
        theta2 = theta.detach() + 0.01 * theta.grad
    S1 = float(vn_entropy(rho_of_theta(theta2)).item())
    r["ascent_increases_S"] = {"S0": S0, "S1": S1, "passed": S1 >= S0 - 1e-10}
    return r


def run_negative_tests():
    r = {}
    # Pure state (all probability on one eigenvalue) => S=0 and grad of S w.r.t.
    # softmax logits that keep it pure should be ~0 in the pure limit.
    theta = torch.zeros(7, dtype=torch.float64, requires_grad=True)
    # Force near-pure: huge positive logit on index 0
    with torch.no_grad():
        theta[0] = 50.0
    theta.requires_grad_(True)
    S = vn_entropy(rho_of_theta(theta))
    r["pure_state_S_near_zero"] = {"S": float(S.item()), "passed": abs(S.item()) < 1e-6}

    # Non-Hermitian matrix should not be treated as density matrix -> eigvalsh would give wrong;
    # verify our rho is Hermitian.
    with torch.no_grad():
        rho = rho_of_theta(torch.randn(7, dtype=torch.float64))
        herm_err = float(torch.linalg.norm(rho - rho.conj().T).item())
    r["rho_hermitian"] = {"herm_err": herm_err, "passed": herm_err < 1e-10}
    return r


def run_boundary_tests():
    r = {}
    # Maximally mixed rho => S = log(4), grad w.r.t. unitary params = 0
    theta = torch.zeros(7, dtype=torch.float64, requires_grad=True)
    S = vn_entropy(rho_of_theta(theta))
    S.backward()
    r["maxmix_entropy"] = {"S": float(S.item()), "target": float(np.log(4)),
                           "passed": abs(S.item() - np.log(4)) < 1e-8}
    # Gradient w.r.t. unitary params (indices 4,5,6) should be ~0 at max mix
    g = theta.grad.detach().numpy()
    r["maxmix_unitary_grad_zero"] = {"grad_unitary": g[4:].tolist(),
                                     "passed": float(np.linalg.norm(g[4:])) < 1e-8}
    return r


if __name__ == "__main__":
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "autograd through eigvalsh of parameterized rho; FD is decorative noisy check"
    TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"

    results = {
        "name": "sim_autograd_grad_Ic_axis0",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "autograd_grad_Ic_axis0_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
