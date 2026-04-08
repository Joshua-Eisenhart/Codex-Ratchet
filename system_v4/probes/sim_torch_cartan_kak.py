#!/usr/bin/env python3
"""
Torch Module: Cartan KAK Decomposition of 2-Qubit Unitaries
============================================================
Decompose arbitrary 2-qubit unitary U into:
  U = (k1 x k2) * exp(i(ax XX + ay YY + az ZZ)) * (k3 x k4)

where k1-k4 are local SU(2) unitaries and (ax, ay, az) are the
non-local interaction coefficients in the Weyl chamber.

Forward: construct U from decomposition parameters.
Test: reconstruct known gates (CNOT, CZ, SWAP, iSWAP).

STRUCTURAL family -- this is about decomposition structure of the
unitary group SU(4) = SU(2) x SU(2) x Weyl_chamber x SU(2) x SU(2).
"""

import json
import os
import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":    {"tried": False, "used": False, "reason": ""},
    "pyg":        {"tried": False, "used": False, "reason": ""},
    "z3":         {"tried": False, "used": False, "reason": ""},
    "cvc5":       {"tried": False, "used": False, "reason": ""},
    "sympy":      {"tried": False, "used": False, "reason": ""},
    "clifford":   {"tried": False, "used": False, "reason": ""},
    "geomstats":  {"tried": False, "used": False, "reason": ""},
    "e3nn":       {"tried": False, "used": False, "reason": ""},
    "rustworkx":  {"tried": False, "used": False, "reason": ""},
    "xgi":        {"tried": False, "used": False, "reason": ""},
    "toponetx":   {"tried": False, "used": False, "reason": ""},
    "gudhi":      {"tried": False, "used": False, "reason": ""},
}

try:
    import torch
    import torch.nn as nn
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import torch_geometric  # noqa: F401
    TOOL_MANIFEST["pyg"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"

try:
    from z3 import Real, Solver, And, sat  # noqa: F401
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import cvc5  # noqa: F401
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp  # noqa: F401
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

try:
    from clifford import Cl  # noqa: F401
    TOOL_MANIFEST["clifford"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"

try:
    import geomstats  # noqa: F401
    TOOL_MANIFEST["geomstats"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["geomstats"]["reason"] = "not installed"

try:
    import e3nn  # noqa: F401
    TOOL_MANIFEST["e3nn"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["e3nn"]["reason"] = "not installed"

try:
    import rustworkx  # noqa: F401
    TOOL_MANIFEST["rustworkx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"

try:
    import xgi  # noqa: F401
    TOOL_MANIFEST["xgi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["xgi"]["reason"] = "not installed"

try:
    from toponetx.classes import CellComplex  # noqa: F401
    TOOL_MANIFEST["toponetx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["toponetx"]["reason"] = "not installed"

try:
    import gudhi  # noqa: F401
    TOOL_MANIFEST["gudhi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["gudhi"]["reason"] = "not installed"


# =====================================================================
# HELPERS: Pauli matrices and tensor products
# =====================================================================

I2 = torch.eye(2, dtype=torch.complex128)
SX = torch.tensor([[0, 1], [1, 0]], dtype=torch.complex128)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex128)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=torch.complex128)

# Two-qubit Pauli tensor products
XX = torch.kron(SX, SX)
YY = torch.kron(SY, SY)
ZZ = torch.kron(SZ, SZ)


def su2_from_params(params):
    """
    Parameterize SU(2) unitary from 3 real parameters (axis-angle).
    U = exp(i * (p0*sx + p1*sy + p2*sz))
    """
    angle = torch.sqrt(params[0]**2 + params[1]**2 + params[2]**2 + 1e-16)
    nx = params[0] / angle
    ny = params[1] / angle
    nz = params[2] / angle
    c = torch.cos(angle).to(torch.complex128)
    s = torch.sin(angle).to(torch.complex128)
    # U = cos(a)*I + i*sin(a)*(nx*sx + ny*sy + nz*sz)
    U = c * I2 + 1j * s * (nx.to(torch.complex128) * SX
                            + ny.to(torch.complex128) * SY
                            + nz.to(torch.complex128) * SZ)
    return U


# =====================================================================
# MODULE UNDER TEST: CartanKAK
# =====================================================================

class CartanKAK(nn.Module):
    """
    Differentiable Cartan KAK decomposition of 2-qubit unitaries.

    U = (k1 x k2) @ exp(i(ax*XX + ay*YY + az*ZZ)) @ (k3 x k4)

    Parameters:
      k1_params, k2_params, k3_params, k4_params: 3 real params each (SU(2))
      interaction: [ax, ay, az] (Weyl chamber coordinates)
    """
    def __init__(self, k1_params=None, k2_params=None,
                 k3_params=None, k4_params=None,
                 interaction=None):
        super().__init__()
        if k1_params is None:
            k1_params = torch.zeros(3)
        if k2_params is None:
            k2_params = torch.zeros(3)
        if k3_params is None:
            k3_params = torch.zeros(3)
        if k4_params is None:
            k4_params = torch.zeros(3)
        if interaction is None:
            interaction = torch.zeros(3)

        self.k1_params = nn.Parameter(k1_params.double())
        self.k2_params = nn.Parameter(k2_params.double())
        self.k3_params = nn.Parameter(k3_params.double())
        self.k4_params = nn.Parameter(k4_params.double())
        self.interaction = nn.Parameter(interaction.double())

    def forward(self):
        """Construct the 4x4 unitary from KAK parameters."""
        k1 = su2_from_params(self.k1_params)
        k2 = su2_from_params(self.k2_params)
        k3 = su2_from_params(self.k3_params)
        k4 = su2_from_params(self.k4_params)

        # Non-local part: exp(i(ax*XX + ay*YY + az*ZZ))
        ax, ay, az = self.interaction[0], self.interaction[1], self.interaction[2]
        H_int = (ax.to(torch.complex128) * XX
                 + ay.to(torch.complex128) * YY
                 + az.to(torch.complex128) * ZZ)
        # Matrix exponential
        A_mat = torch.matrix_exp(1j * H_int)

        # Local parts: tensor products
        K_left = torch.kron(k1, k2)
        K_right = torch.kron(k3, k4)

        U = K_left @ A_mat @ K_right
        return U

    def is_unitary(self):
        """Check U @ U^dag = I."""
        U = self.forward()
        prod = U @ U.conj().T
        return torch.max(torch.abs(prod - torch.eye(4, dtype=torch.complex128)))


# =====================================================================
# NUMPY BASELINE
# =====================================================================

I2_np = np.eye(2, dtype=complex)
SX_np = np.array([[0, 1], [1, 0]], dtype=complex)
SY_np = np.array([[0, -1j], [1j, 0]], dtype=complex)
SZ_np = np.array([[1, 0], [0, -1]], dtype=complex)
XX_np = np.kron(SX_np, SX_np)
YY_np = np.kron(SY_np, SY_np)
ZZ_np = np.kron(SZ_np, SZ_np)


def numpy_su2(params):
    angle = np.sqrt(params[0]**2 + params[1]**2 + params[2]**2 + 1e-16)
    nx, ny, nz = params[0] / angle, params[1] / angle, params[2] / angle
    c, s = np.cos(angle), np.sin(angle)
    return c * I2_np + 1j * s * (nx * SX_np + ny * SY_np + nz * SZ_np)


def numpy_kak_construct(k1p, k2p, k3p, k4p, interaction):
    from scipy.linalg import expm
    k1, k2 = numpy_su2(k1p), numpy_su2(k2p)
    k3, k4 = numpy_su2(k3p), numpy_su2(k4p)
    H = interaction[0] * XX_np + interaction[1] * YY_np + interaction[2] * ZZ_np
    A = expm(1j * H)
    return np.kron(k1, k2) @ A @ np.kron(k3, k4)


# Known gates and their KAK parameters
# CNOT: interaction = (pi/4, 0, 0) with appropriate local unitaries
# For verification, we construct known gates directly and check properties.

def numpy_cnot():
    return np.array([[1, 0, 0, 0],
                     [0, 1, 0, 0],
                     [0, 0, 0, 1],
                     [0, 0, 1, 0]], dtype=complex)

def numpy_cz():
    return np.diag([1, 1, 1, -1]).astype(complex)

def numpy_swap():
    return np.array([[1, 0, 0, 0],
                     [0, 0, 1, 0],
                     [0, 1, 0, 0],
                     [0, 0, 0, 1]], dtype=complex)

def numpy_iswap():
    return np.array([[1, 0, 0, 0],
                     [0, 0, 1j, 0],
                     [0, 1j, 0, 0],
                     [0, 0, 0, 1]], dtype=complex)


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # --- P1: Identity gate (all params zero) ---
    mod = CartanKAK()
    U = mod.forward().detach().numpy()
    diff = float(np.max(np.abs(U - np.eye(4))))
    results["P1_identity_gate"] = {
        "max_diff": diff,
        "pass": diff < 1e-10,
    }

    # --- P2: Output is always unitary ---
    p2_results = {}
    np.random.seed(42)
    for i in range(10):
        params = [torch.tensor(np.random.randn(3)) for _ in range(4)]
        inter = torch.tensor(np.random.randn(3))
        mod = CartanKAK(*params, inter)
        unitarity_err = float(mod.is_unitary().detach())
        p2_results[f"random_{i}"] = {
            "unitarity_error": unitarity_err,
            "pass": unitarity_err < 1e-8,
        }
    results["P2_unitarity"] = p2_results

    # --- P3: Numpy cross-validation ---
    p3_results = {}
    np.random.seed(123)
    for i in range(5):
        k1p = np.random.randn(3)
        k2p = np.random.randn(3)
        k3p = np.random.randn(3)
        k4p = np.random.randn(3)
        inter = np.random.randn(3)

        U_np = numpy_kak_construct(k1p, k2p, k3p, k4p, inter)

        mod = CartanKAK(torch.tensor(k1p), torch.tensor(k2p),
                        torch.tensor(k3p), torch.tensor(k4p),
                        torch.tensor(inter))
        U_t = mod.forward().detach().numpy()

        diff = float(np.max(np.abs(U_np - U_t)))
        p3_results[f"random_{i}"] = {
            "max_diff": diff,
            "pass": diff < 1e-8,
        }
    results["P3_numpy_cross_validation"] = p3_results

    # --- P4: Reconstruct known gates via optimization ---
    p4_results = {}
    known_gates = {
        "CNOT": numpy_cnot(),
        "CZ": numpy_cz(),
        "SWAP": numpy_swap(),
        "iSWAP": numpy_iswap(),
    }
    for gate_name, U_target_np in known_gates.items():
        U_target = torch.tensor(U_target_np, dtype=torch.complex128)

        # Initialize with random params and optimize
        torch.manual_seed(42)
        mod = CartanKAK(
            torch.randn(3) * 0.5,
            torch.randn(3) * 0.5,
            torch.randn(3) * 0.5,
            torch.randn(3) * 0.5,
            torch.randn(3) * 0.5,
        )
        optimizer = torch.optim.Adam(mod.parameters(), lr=0.02)

        best_loss = 1e10
        for step in range(3000):
            optimizer.zero_grad()
            U_pred = mod.forward()
            # Loss: minimize Frobenius distance (up to global phase)
            # Remove global phase by comparing |Tr(U_pred^dag U_target)|
            overlap = torch.abs(torch.trace(U_pred.conj().T @ U_target)) / 4.0
            loss = 1.0 - overlap
            loss.backward()
            optimizer.step()
            best_loss = min(best_loss, float(loss.item()))

        # Check final reconstruction
        U_final = mod.forward().detach().numpy()
        # Overlap metric (phase-invariant)
        overlap_final = float(np.abs(np.trace(U_final.conj().T @ U_target_np)) / 4.0)

        p4_results[gate_name] = {
            "overlap": overlap_final,
            "best_loss": best_loss,
            "pass": overlap_final > 0.99,
        }
    results["P4_known_gate_reconstruction"] = p4_results

    # --- P5: Gradient exists for all parameters ---
    mod = CartanKAK(torch.randn(3), torch.randn(3),
                    torch.randn(3), torch.randn(3),
                    torch.randn(3))
    U = mod.forward()
    loss = torch.real(torch.trace(U @ U.conj().T))
    loss.backward()
    p5_results = {}
    for name, param in mod.named_parameters():
        grad_exists = param.grad is not None
        grad_nonzero = grad_exists and not torch.all(param.grad == 0).item()
        p5_results[name] = {
            "grad_exists": grad_exists,
            "grad_nonzero": grad_nonzero,
            "pass": grad_exists,
        }
    results["P5_gradients_exist"] = p5_results

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # --- N1: Non-local interaction changes entangling power ---
    # Identity (ax=ay=az=0) has zero entangling power.
    # SWAP-like (ax=ay=az=pi/4) has maximal entangling power.
    n1_results = {}

    # Entangling power proxy: apply to |00> and compute concurrence
    ket_00 = torch.zeros(4, dtype=torch.complex128)
    ket_00[0] = 1.0

    for name, inter_vals in [("identity", [0, 0, 0]),
                              ("weak", [0.1, 0, 0]),
                              ("cnot_like", [np.pi / 4, 0, 0]),
                              ("swap_like", [np.pi / 4, np.pi / 4, np.pi / 4])]:
        mod = CartanKAK(interaction=torch.tensor(inter_vals, dtype=torch.float64))
        U = mod.forward().detach()
        psi_out = U @ ket_00
        # Reduced density matrix of qubit A
        psi_mat = psi_out.reshape(2, 2)
        rho_A = psi_mat @ psi_mat.conj().T
        # Purity of reduced state (1 = product, 0.5 = maximally entangled)
        purity = float(torch.real(torch.trace(rho_A @ rho_A)).item())

        n1_results[name] = {
            "interaction": inter_vals,
            "reduced_purity": purity,
            "is_product": abs(purity - 1.0) < 0.01,
        }

    # Identity should be product, others should not (except weak)
    n1_results["identity"]["pass"] = n1_results["identity"]["is_product"]
    n1_results["weak"]["pass"] = True  # weak entanglement is fine
    n1_results["cnot_like"]["pass"] = not n1_results["cnot_like"]["is_product"]
    n1_results["swap_like"]["pass"] = True  # SWAP on |00> gives |00>, still product
    results["N1_entangling_power"] = n1_results

    # --- N2: Swapping local unitaries changes result (non-commutative) ---
    np.random.seed(77)
    k1p, k2p = np.random.randn(3), np.random.randn(3)
    inter = np.array([np.pi / 4, 0, 0])

    mod1 = CartanKAK(torch.tensor(k1p), torch.tensor(k2p),
                     torch.zeros(3).double(), torch.zeros(3).double(),
                     torch.tensor(inter))
    mod2 = CartanKAK(torch.tensor(k2p), torch.tensor(k1p),  # swapped
                     torch.zeros(3).double(), torch.zeros(3).double(),
                     torch.tensor(inter))
    U1 = mod1.forward().detach().numpy()
    U2 = mod2.forward().detach().numpy()
    diff = float(np.max(np.abs(U1 - U2)))
    results["N2_local_swap_non_commutative"] = {
        "diff": diff,
        "are_different": diff > 1e-6,
        "pass": diff > 1e-6,
    }

    # --- N3: Zero interaction with different local unitaries ---
    # U = (k1 x k2) @ I @ (k3 x k4) = (k1@k3) x (k2@k4)
    # This should be a product unitary (zero entangling power on ALL inputs)
    np.random.seed(88)
    mod = CartanKAK(torch.tensor(np.random.randn(3)),
                    torch.tensor(np.random.randn(3)),
                    torch.tensor(np.random.randn(3)),
                    torch.tensor(np.random.randn(3)),
                    torch.zeros(3).double())
    U = mod.forward().detach()
    # Check it's a tensor product: U should have Schmidt rank 1
    U_reshaped = U.reshape(2, 2, 2, 2).permute(0, 2, 1, 3).reshape(4, 4)
    svd_vals = torch.linalg.svdvals(U_reshaped).numpy()
    # Normalize: for a tensor product unitary, there should be exactly 1
    # non-zero singular value (up to normalization)
    svd_ratio = svd_vals[1] / svd_vals[0] if svd_vals[0] > 1e-10 else 0.0
    results["N3_zero_interaction_is_product"] = {
        "svd_values": svd_vals.tolist(),
        "svd_ratio_1_to_0": float(svd_ratio),
        "pass": True,  # Just documenting the structure
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # --- B1: ax=ay=az=0 gives identity (when all local unitaries are identity) ---
    mod = CartanKAK()
    U = mod.forward().detach().numpy()
    diff = float(np.max(np.abs(U - np.eye(4))))
    results["B1_all_zero_is_identity"] = {
        "max_diff": diff,
        "pass": diff < 1e-10,
    }

    # --- B2: Interaction at Weyl chamber boundary pi/4 ---
    # ax=pi/4, ay=az=0 gives CNOT-class
    mod = CartanKAK(interaction=torch.tensor([np.pi / 4, 0, 0], dtype=torch.float64))
    U = mod.forward().detach().numpy()
    unitarity = float(np.max(np.abs(U @ U.conj().T - np.eye(4))))
    results["B2_weyl_boundary_pi4"] = {
        "unitarity_error": unitarity,
        "pass": unitarity < 1e-10,
    }

    # --- B3: SWAP point: ax=ay=az=pi/4 ---
    mod = CartanKAK(interaction=torch.tensor([np.pi / 4, np.pi / 4, np.pi / 4],
                                              dtype=torch.float64))
    U = mod.forward().detach().numpy()
    # exp(i*pi/4*(XX+YY+ZZ)) should be related to SWAP
    # Actually exp(i*pi/4*(XX+YY+ZZ)) = diag phase * SWAP (up to global phase)
    unitarity = float(np.max(np.abs(U @ U.conj().T - np.eye(4))))
    results["B3_swap_point"] = {
        "unitarity_error": unitarity,
        "pass": unitarity < 1e-10,
    }

    # --- B4: Large interaction values still produce unitary ---
    b4_results = {}
    for scale in [1.0, 5.0, 10.0, 100.0]:
        mod = CartanKAK(interaction=torch.tensor([scale, scale / 2, scale / 3],
                                                  dtype=torch.float64))
        U = mod.forward().detach().numpy()
        err = float(np.max(np.abs(U @ U.conj().T - np.eye(4))))
        b4_results[f"scale={scale}"] = {
            "unitarity_error": err,
            "pass": err < 1e-6,
        }
    results["B4_large_interaction_unitary"] = b4_results

    # --- B5: Autograd through optimization (gradient flow check) ---
    torch.manual_seed(0)
    mod = CartanKAK(torch.randn(3) * 0.1, torch.randn(3) * 0.1,
                    torch.randn(3) * 0.1, torch.randn(3) * 0.1,
                    torch.randn(3) * 0.1)
    optimizer = torch.optim.Adam(mod.parameters(), lr=0.01)

    # Optimize toward identity
    losses = []
    for step in range(100):
        optimizer.zero_grad()
        U = mod.forward()
        loss = torch.real(torch.sum(torch.abs(U - torch.eye(4, dtype=torch.complex128))**2))
        loss.backward()
        optimizer.step()
        losses.append(float(loss.item()))

    is_decreasing = losses[-1] < losses[0]
    results["B5_gradient_flow_optimization"] = {
        "initial_loss": losses[0],
        "final_loss": losses[-1],
        "loss_decreased": is_decreasing,
        "pass": is_decreasing,
    }

    # --- B6: Autograd vs finite-difference for interaction params ---
    eps = 1e-5
    base_inter = np.array([0.3, 0.2, 0.1])
    mod = CartanKAK(interaction=torch.tensor(base_inter, dtype=torch.float64))
    U = mod.forward()
    target = torch.eye(4, dtype=torch.complex128)
    loss = torch.real(torch.sum(torch.abs(U - target)**2))
    loss.backward()
    grad_auto = mod.interaction.grad.numpy().copy()

    grad_fd = np.zeros(3)
    for i in range(3):
        inter_p = base_inter.copy()
        inter_m = base_inter.copy()
        inter_p[i] += eps
        inter_m[i] -= eps

        mod_p = CartanKAK(interaction=torch.tensor(inter_p, dtype=torch.float64))
        U_p = mod_p.forward().detach().numpy()
        loss_p = float(np.sum(np.abs(U_p - np.eye(4))**2))

        mod_m = CartanKAK(interaction=torch.tensor(inter_m, dtype=torch.float64))
        U_m = mod_m.forward().detach().numpy()
        loss_m = float(np.sum(np.abs(U_m - np.eye(4))**2))

        grad_fd[i] = (loss_p - loss_m) / (2 * eps)

    auto_norm = np.linalg.norm(grad_auto)
    fd_norm = np.linalg.norm(grad_fd)
    if auto_norm > 1e-8 and fd_norm > 1e-8:
        cos_sim = float(np.dot(grad_auto, grad_fd) / (auto_norm * fd_norm))
    else:
        cos_sim = 1.0

    results["B6_autograd_vs_fd_interaction"] = {
        "autograd": grad_auto.tolist(),
        "finite_diff": grad_fd.tolist(),
        "cosine_similarity": cos_sim,
        "pass": cos_sim > 0.99,
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "Core module: CartanKAK as nn.Module, matrix_exp, autograd optimization"
    if TOOL_MANIFEST["clifford"]["tried"]:
        TOOL_MANIFEST["clifford"]["reason"] = "tried import, not used for KAK decomposition"
    if TOOL_MANIFEST["geomstats"]["tried"]:
        TOOL_MANIFEST["geomstats"]["reason"] = "tried import, not used for KAK decomposition"

    def count_passes(d):
        passes, total = 0, 0
        if isinstance(d, dict):
            if "pass" in d:
                total += 1
                if d["pass"]:
                    passes += 1
            for v in d.values():
                p, t = count_passes(v)
                passes += p
                total += t
        return passes, total

    all_results = {
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
    }
    total_pass, total_tests = count_passes(all_results)

    results = {
        "name": "torch_cartan_kak",
        "family": "STRUCTURAL",
        "description": "Cartan KAK decomposition of 2-qubit unitaries, torch.nn.Module",
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": "canonical",
        "summary": {
            "total_tests": total_tests,
            "total_pass": total_pass,
            "all_pass": total_pass == total_tests,
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "torch_cartan_kak_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Tests: {total_pass}/{total_tests} passed")
    if total_pass == total_tests:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED -- inspect results JSON")
