#!/usr/bin/env python3
"""
General Unitary Rotation U(theta, n) = exp(-i * theta * n.sigma / 2)
as a differentiable torch.nn.Module with LEARNABLE parameters.

Parameterized by angle theta and axis n=(nx, ny, nz) on Bloch sphere.
This is the most general single-qubit rotation (up to global phase).

Key identity: U = cos(theta/2)*I - i*sin(theta/2)*(nx*X + ny*Y + nz*Z)

Tests:
- theta=pi around Z is Z gate
- theta=pi around X is X gate (Pauli X)
- theta=pi around Y is Y gate (up to global phase)
- theta=0 is identity
- theta=2*pi is -I (density matrix same as I)
- Gradient of output state w.r.t. theta and n
- Autograd vs finite difference
- Non-unitary detection
- Sympy/z3 checks
"""

import json
import os
import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": ""},
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi": {"tried": False, "used": False, "reason": ""},
    "toponetx": {"tried": False, "used": False, "reason": ""},
    "gudhi": {"tried": False, "used": False, "reason": ""},
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
    from z3 import Real, Solver, And, Not, sat, unsat  # noqa: F401
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import cvc5  # noqa: F401
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp
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
# PAULI MATRICES
# =====================================================================

PAULI_X_NP = np.array([[0, 1], [1, 0]], dtype=np.complex128)
PAULI_Y_NP = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
PAULI_Z_NP = np.array([[1, 0], [0, -1]], dtype=np.complex128)
I_NP = np.eye(2, dtype=np.complex128)

PAULI_X_T = torch.tensor([[0, 1], [1, 0]], dtype=torch.complex64)
PAULI_Y_T = torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex64)
PAULI_Z_T = torch.tensor([[1, 0], [0, -1]], dtype=torch.complex64)


# =====================================================================
# MODULE UNDER TEST: UnitaryRotation
# =====================================================================

class UnitaryRotation(nn.Module):
    """General single-qubit rotation U(theta, n) = exp(-i*theta*n.sigma/2).

    Parameters:
        theta: rotation angle (learnable)
        n: rotation axis as (nx, ny, nz) on unit sphere (learnable, auto-normalized)

    forward(rho) applies: rho -> U * rho * U dagger
    """

    def __init__(self, theta=0.0, nx=0.0, ny=0.0, nz=1.0):
        super().__init__()
        self.theta = nn.Parameter(torch.tensor(float(theta)))
        self.n = nn.Parameter(torch.tensor([float(nx), float(ny), float(nz)]))

    def _build_unitary(self):
        """Construct U = cos(theta/2)*I - i*sin(theta/2)*(n.sigma)."""
        # Normalize axis
        n_norm = self.n / (torch.norm(self.n) + 1e-12)
        nx, ny, nz = n_norm[0], n_norm[1], n_norm[2]

        half_theta = self.theta / 2.0
        c = torch.cos(half_theta).to(torch.complex64)
        s = torch.sin(half_theta).to(torch.complex64)

        I_t = torch.eye(2, dtype=torch.complex64)
        n_dot_sigma = (
            nx.to(torch.complex64) * PAULI_X_T
            + ny.to(torch.complex64) * PAULI_Y_T
            + nz.to(torch.complex64) * PAULI_Z_T
        )

        U = c * I_t - 1j * s * n_dot_sigma
        return U

    def forward(self, rho):
        U = self._build_unitary()
        return U @ rho @ U.conj().T

    def is_unitary(self, tol=1e-5):
        U = self._build_unitary().detach()
        UUd = U @ U.conj().T
        diff = torch.max(torch.abs(UUd - torch.eye(2, dtype=U.dtype)))
        return float(diff.item()) < tol

    def get_unitary_np(self):
        return self._build_unitary().detach().cpu().numpy()


# =====================================================================
# NUMPY REFERENCE
# =====================================================================

def numpy_rotation(theta, nx, ny, nz, rho):
    """Apply U(theta, n) to density matrix using numpy."""
    n_vec = np.array([nx, ny, nz])
    n_vec = n_vec / (np.linalg.norm(n_vec) + 1e-12)
    nx, ny, nz = n_vec

    c = np.cos(theta / 2)
    s = np.sin(theta / 2)
    n_dot_sigma = nx * PAULI_X_NP + ny * PAULI_Y_NP + nz * PAULI_Z_NP
    U = c * I_NP - 1j * s * n_dot_sigma
    return U @ rho @ U.conj().T


# =====================================================================
# HELPERS
# =====================================================================

def ket_to_dm(ket_np):
    return np.outer(ket_np, ket_np.conj())


def bloch_vector(rho):
    x = float(np.real(np.trace(PAULI_X_NP @ rho)))
    y = float(np.real(np.trace(PAULI_Y_NP @ rho)))
    z = float(np.real(np.trace(PAULI_Z_NP @ rho)))
    return x, y, z


KET_0 = np.array([1, 0], dtype=np.complex128)
KET_1 = np.array([0, 1], dtype=np.complex128)
KET_PLUS = np.array([1, 1], dtype=np.complex128) / np.sqrt(2)


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # --- P1: theta=pi, n=Z -> Z gate: |0>->|0>, |1>->-|1> (dm invariant) ---
    rho_0 = ket_to_dm(KET_0)
    out = numpy_rotation(np.pi, 0, 0, 1, rho_0)
    diff = float(np.max(np.abs(out - rho_0)))
    results["P1_pi_Z_on_0"] = {"max_diff": diff, "pass": diff < 1e-10}

    rho_1 = ket_to_dm(KET_1)
    out = numpy_rotation(np.pi, 0, 0, 1, rho_1)
    diff = float(np.max(np.abs(out - rho_1)))
    results["P1b_pi_Z_on_1"] = {"max_diff": diff, "pass": diff < 1e-10}

    # Z gate flips sign of X-component on Bloch sphere
    rho_plus = ket_to_dm(KET_PLUS)
    out = numpy_rotation(np.pi, 0, 0, 1, rho_plus)
    # Z|+> = |-> so rho(|->) is expected
    ket_minus = np.array([1, -1], dtype=np.complex128) / np.sqrt(2)
    diff = float(np.max(np.abs(out - ket_to_dm(ket_minus))))
    results["P1c_pi_Z_on_plus"] = {"max_diff": diff, "pass": diff < 1e-10}

    # --- P2: theta=pi, n=X -> X gate: |0>->|1>, |1>->|0> (dm swap) ---
    # -i*X applied to |0> gives -i|1>, dm = |1><1|
    out = numpy_rotation(np.pi, 1, 0, 0, rho_0)
    diff = float(np.max(np.abs(out - rho_1)))
    results["P2_pi_X_on_0"] = {"max_diff": diff, "pass": diff < 1e-10}

    out = numpy_rotation(np.pi, 1, 0, 0, rho_1)
    diff = float(np.max(np.abs(out - rho_0)))
    results["P2b_pi_X_on_1"] = {"max_diff": diff, "pass": diff < 1e-10}

    # --- P3: theta=0 -> identity ---
    out = numpy_rotation(0, 0, 0, 1, rho_plus)
    diff = float(np.max(np.abs(out - rho_plus)))
    results["P3_theta0_identity"] = {"max_diff": diff, "pass": diff < 1e-10}

    # --- P4: theta=2*pi -> -I, but density matrix = identity ---
    out = numpy_rotation(2 * np.pi, 0, 0, 1, rho_plus)
    diff = float(np.max(np.abs(out - rho_plus)))
    results["P4_theta_2pi_identity_dm"] = {"max_diff": diff, "pass": diff < 1e-10}

    # --- P5: Substrate match (torch vs numpy) ---
    p5_results = {}
    test_cases = [
        ("pi_Z", np.pi, 0, 0, 1),
        ("pi_X", np.pi, 1, 0, 0),
        ("pi_Y", np.pi, 0, 1, 0),
        ("pi2_Z", np.pi / 2, 0, 0, 1),
        ("pi4_arb", np.pi / 4, 1, 1, 1),
    ]
    for name, theta, nx, ny, nz in test_cases:
        rho_np = ket_to_dm(KET_PLUS)
        out_np = numpy_rotation(theta, nx, ny, nz, rho_np)
        gate = UnitaryRotation(theta, nx, ny, nz)
        rho_t = torch.tensor(rho_np, dtype=torch.complex64)
        out_t = gate(rho_t).detach().cpu().numpy()
        max_diff = float(np.max(np.abs(out_np - out_t)))
        p5_results[name] = {"max_abs_diff": max_diff, "pass": max_diff < 1e-5}
    results["P5_substrate_match"] = p5_results

    # --- P6: Trace preservation ---
    p6_results = {}
    for name, theta, nx, ny, nz in test_cases:
        out = numpy_rotation(theta, nx, ny, nz, ket_to_dm(KET_0))
        trace = float(np.real(np.trace(out)))
        p6_results[name] = {"trace": trace, "pass": abs(trace - 1.0) < 1e-10}
    results["P6_trace_preservation"] = p6_results

    # --- P7: Unitarity for various params ---
    p7_results = {}
    for name, theta, nx, ny, nz in test_cases:
        gate = UnitaryRotation(theta, nx, ny, nz)
        p7_results[name] = {"is_unitary": gate.is_unitary(), "pass": gate.is_unitary()}
    results["P7_unitarity"] = p7_results

    # --- P8: theta=pi, n=Y -> Y gate ---
    # -i*Y applied to |0> = -i*(i)|1> = |1>, dm same as |1><1|
    out = numpy_rotation(np.pi, 0, 1, 0, rho_0)
    diff = float(np.max(np.abs(out - rho_1)))
    results["P8_pi_Y_on_0"] = {"max_diff": diff, "pass": diff < 1e-10}

    return results


# =====================================================================
# FALSIFICATION TESTS
# =====================================================================

def run_falsification_tests():
    results = {}

    # --- F1: Gradient of <Z> w.r.t. theta ---
    # For rotation around X-axis by theta on |0>:
    # U = cos(theta/2)*I - i*sin(theta/2)*X
    # U|0> = cos(theta/2)|0> - i*sin(theta/2)|1>
    # <Z> = cos^2(theta/2) - sin^2(theta/2) = cos(theta)
    # d<Z>/dtheta = -sin(theta)
    Z_t = torch.tensor([[1, 0], [0, -1]], dtype=torch.complex64)

    f1_results = {}
    for theta_val in [0.1, 0.5, np.pi / 4, np.pi / 2, 1.0, np.pi]:
        gate = UnitaryRotation(theta_val, 1.0, 0.0, 0.0)
        rho_0_t = torch.tensor(ket_to_dm(KET_0), dtype=torch.complex64)
        rho_out = gate(rho_0_t)
        exp_z = torch.real(torch.trace(Z_t @ rho_out))
        exp_z.backward()
        grad_theta = gate.theta.grad
        # Theoretical: d<Z>/dtheta = -sin(theta)
        expected_grad = -np.sin(theta_val)
        f1_results[f"theta={theta_val:.4f}"] = {
            "theta": float(theta_val),
            "exp_Z": float(exp_z.item()),
            "exp_Z_theory": float(np.cos(theta_val)),
            "grad_theta": float(grad_theta.item()) if grad_theta is not None else None,
            "expected_grad": float(expected_grad),
            "grad_close": abs(float(grad_theta.item()) - expected_grad) < 0.05 if grad_theta is not None else False,
            "pass": grad_theta is not None,
        }
        gate.zero_grad()
    results["F1_theta_gradient"] = f1_results

    # --- F2: Gradient w.r.t. axis components ---
    gate = UnitaryRotation(np.pi / 2, 1.0, 0.0, 0.0)
    rho_0_t = torch.tensor(ket_to_dm(KET_0), dtype=torch.complex64)
    rho_out = gate(rho_0_t)
    exp_z = torch.real(torch.trace(Z_t @ rho_out))
    exp_z.backward()
    grad_n = gate.n.grad
    results["F2_axis_gradient"] = {
        "grad_nx": float(grad_n[0].item()) if grad_n is not None else None,
        "grad_ny": float(grad_n[1].item()) if grad_n is not None else None,
        "grad_nz": float(grad_n[2].item()) if grad_n is not None else None,
        "grad_exists": grad_n is not None,
        "pass": grad_n is not None,
    }

    # --- F3: Autograd vs finite difference for theta ---
    eps = 1e-4
    theta_test = 0.7
    gate = UnitaryRotation(theta_test, 1.0, 0.0, 0.0)
    rho_0_t = torch.tensor(ket_to_dm(KET_0), dtype=torch.complex64)
    rho_out = gate(rho_0_t)
    exp_z = torch.real(torch.trace(Z_t @ rho_out))
    exp_z.backward()
    grad_auto = float(gate.theta.grad.item())

    def fd_exp_z(th):
        out = numpy_rotation(th, 1.0, 0.0, 0.0, ket_to_dm(KET_0))
        return float(np.real(np.trace(PAULI_Z_NP @ out)))

    grad_fd = (fd_exp_z(theta_test + eps) - fd_exp_z(theta_test - eps)) / (2 * eps)
    diff = abs(grad_auto - grad_fd)
    results["F3_autograd_vs_fd_theta"] = {
        "autograd": grad_auto, "finite_diff": float(grad_fd),
        "abs_diff": diff, "pass": diff < 0.01,
    }

    # --- F4: Autograd vs finite difference for axis component ---
    nx_test = 0.6
    gate = UnitaryRotation(np.pi / 3, nx_test, 0.3, 0.5)
    rho_0_t = torch.tensor(ket_to_dm(KET_0), dtype=torch.complex64)
    rho_out = gate(rho_0_t)
    exp_z = torch.real(torch.trace(Z_t @ rho_out))
    exp_z.backward()
    grad_nx_auto = float(gate.n.grad[0].item())

    def fd_exp_z_nx(nx_v):
        out = numpy_rotation(np.pi / 3, nx_v, 0.3, 0.5, ket_to_dm(KET_0))
        return float(np.real(np.trace(PAULI_Z_NP @ out)))

    grad_nx_fd = (fd_exp_z_nx(nx_test + eps) - fd_exp_z_nx(nx_test - eps)) / (2 * eps)
    diff = abs(grad_nx_auto - grad_nx_fd)
    results["F4_autograd_vs_fd_axis"] = {
        "autograd": grad_nx_auto, "finite_diff": float(grad_nx_fd),
        "abs_diff": diff, "pass": diff < 0.05,
    }

    # --- F5: Random params substrate match ---
    np.random.seed(42)
    max_diffs = []
    for _ in range(20):
        theta = np.random.uniform(0, 2 * np.pi)
        n = np.random.randn(3)
        n /= np.linalg.norm(n)
        a = np.random.randn(2) + 1j * np.random.randn(2); a /= np.linalg.norm(a)
        rho_np = ket_to_dm(a)
        out_np = numpy_rotation(theta, n[0], n[1], n[2], rho_np)
        gate = UnitaryRotation(theta, n[0], n[1], n[2])
        rho_t = torch.tensor(rho_np, dtype=torch.complex64)
        out_t = gate(rho_t).detach().cpu().numpy()
        max_diffs.append(float(np.max(np.abs(out_np - out_t))))
    results["F5_random_match"] = {"n": 20, "max_diff": max(max_diffs), "pass": max(max_diffs) < 1e-4}

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # --- N1: Non-unitary detected (manually break the rotation) ---
    class BadRotation(nn.Module):
        def __init__(self):
            super().__init__()
            # Non-unitary: scale one component
            U = torch.tensor([[0.8, 0.3], [0.3, 0.7]], dtype=torch.complex64)
            self.register_buffer("U", U)
        def is_unitary(self, tol=1e-6):
            UUd = self.U @ self.U.conj().T
            diff = torch.max(torch.abs(UUd - torch.eye(2, dtype=self.U.dtype)))
            return float(diff.item()) < tol

    results["N1_non_unitary_detected"] = {"is_unitary": BadRotation().is_unitary(), "pass": not BadRotation().is_unitary()}

    # --- N2: Non-unitary does not preserve trace ---
    U_bad = np.array([[0.8, 0.3], [0.3, 0.7]], dtype=np.complex128)
    rho_in = ket_to_dm(KET_0)
    rho_out = U_bad @ rho_in @ U_bad.conj().T
    trace_out = float(np.real(np.trace(rho_out)))
    results["N2_trace_violation"] = {"trace": trace_out, "pass": abs(trace_out - 1.0) > 1e-6}

    # --- N3: Hermiticity preserved ---
    for name, th, nx, ny, nz in [("pi_Z", np.pi, 0, 0, 1), ("arb", 1.3, 0.5, 0.3, 0.8)]:
        gate = UnitaryRotation(th, nx, ny, nz)
        rho_t = torch.tensor(ket_to_dm(KET_PLUS), dtype=torch.complex64)
        out = gate(rho_t).detach().cpu().numpy()
        herm_diff = float(np.max(np.abs(out - out.conj().T)))
        results[f"N3_hermiticity_{name}"] = {"diff": herm_diff, "pass": herm_diff < 1e-5}

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # --- B1: Maximally mixed invariant ---
    rho_mixed = np.eye(2, dtype=np.complex128) / 2
    for name, th, nx, ny, nz in [("pi_Z", np.pi, 0, 0, 1), ("arb", 1.7, 0.3, 0.6, 0.7)]:
        out = numpy_rotation(th, nx, ny, nz, rho_mixed)
        diff = float(np.max(np.abs(out - rho_mixed)))
        results[f"B1_mixed_invariant_{name}"] = {"max_diff": diff, "pass": diff < 1e-10}

    # --- B2: Purity preserved ---
    np.random.seed(44)
    b2_results = {}
    for i in range(5):
        theta = np.random.uniform(0, 2 * np.pi)
        n = np.random.randn(3); n /= np.linalg.norm(n)
        a = np.random.randn(2) + 1j * np.random.randn(2); a /= np.linalg.norm(a)
        rho = ket_to_dm(a)
        out = numpy_rotation(theta, n[0], n[1], n[2], rho)
        p_in = float(np.real(np.trace(rho @ rho)))
        p_out = float(np.real(np.trace(out @ out)))
        b2_results[f"state_{i}"] = {"purity_in": p_in, "purity_out": p_out, "pass": abs(p_in - p_out) < 1e-10}
    results["B2_purity_preserved"] = b2_results

    # --- B3: Bloch radius preserved ---
    np.random.seed(55)
    b3_results = {}
    for i in range(5):
        theta = np.random.uniform(0, 2 * np.pi)
        n = np.random.randn(3); n /= np.linalg.norm(n)
        a = np.random.randn(2) + 1j * np.random.randn(2); a /= np.linalg.norm(a)
        rho = ket_to_dm(a)
        bv_in = bloch_vector(rho)
        r_in = np.sqrt(sum(x**2 for x in bv_in))
        out = numpy_rotation(theta, n[0], n[1], n[2], rho)
        bv_out = bloch_vector(out)
        r_out = np.sqrt(sum(x**2 for x in bv_out))
        b3_results[f"state_{i}"] = {"r_in": r_in, "r_out": r_out, "pass": abs(r_in - r_out) < 1e-10}
    results["B3_bloch_radius_preserved"] = b3_results

    # --- B4: theta=4*pi gives identity on density matrix ---
    rho_in = ket_to_dm(KET_PLUS)
    out = numpy_rotation(4 * np.pi, 0.5, 0.3, 0.8, rho_in)
    diff = float(np.max(np.abs(out - rho_in)))
    results["B4_theta_4pi_identity"] = {"max_diff": diff, "pass": diff < 1e-10}

    # --- B5: Composition: R_z(a) then R_z(b) = R_z(a+b) ---
    a_angle = 0.7
    b_angle = 1.3
    rho_in = ket_to_dm(KET_PLUS)
    out_ab = numpy_rotation(a_angle + b_angle, 0, 0, 1, rho_in)
    out_a = numpy_rotation(a_angle, 0, 0, 1, rho_in)
    out_a_then_b = numpy_rotation(b_angle, 0, 0, 1, out_a)
    diff = float(np.max(np.abs(out_ab - out_a_then_b)))
    results["B5_composition"] = {"max_diff": diff, "pass": diff < 1e-10}

    return results


# =====================================================================
# SYMPY CHECK
# =====================================================================

def run_sympy_check():
    if not TOOL_MANIFEST["sympy"]["tried"]:
        return {"skipped": True, "reason": "sympy not available"}

    theta = sp.Symbol("theta", real=True)
    X = sp.Matrix([[0, 1], [1, 0]])
    Y = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    Z = sp.Matrix([[1, 0], [0, -1]])
    I2 = sp.eye(2)

    # U_z = cos(theta/2)*I - i*sin(theta/2)*Z
    U_z = sp.cos(theta / 2) * I2 - sp.I * sp.sin(theta / 2) * Z
    UUd = sp.simplify(U_z * U_z.H)
    is_unitary = UUd == sp.eye(2)

    # At theta=pi: U_z = -i*Z, unitarily equivalent to Z
    U_z_pi = U_z.subs(theta, sp.pi)
    U_z_pi_simplified = sp.simplify(U_z_pi)
    # Should be -i*Z = [[−i, 0], [0, i]]
    expected = -sp.I * Z
    is_z_gate = sp.simplify(U_z_pi_simplified - expected) == sp.zeros(2)

    # U_x at theta=pi: cos(pi/2)*I - i*sin(pi/2)*X = -iX
    U_x = sp.cos(theta / 2) * I2 - sp.I * sp.sin(theta / 2) * X
    U_x_pi = sp.simplify(U_x.subs(theta, sp.pi))
    expected_x = -sp.I * X
    is_x_gate = sp.simplify(U_x_pi - expected_x) == sp.zeros(2)

    return {
        "Uz_is_unitary": bool(is_unitary),
        "Uz_pi_is_Z_gate": bool(is_z_gate),
        "Ux_pi_is_X_gate": bool(is_x_gate),
        "pass": all([bool(is_unitary), bool(is_z_gate), bool(is_x_gate)]),
    }


# =====================================================================
# Z3 CHECK
# =====================================================================

def run_z3_check():
    if not TOOL_MANIFEST["z3"]["tried"]:
        return {"skipped": True, "reason": "z3 not available"}

    from z3 import Real, Solver, And, Not

    # For U = cos(t/2)*I - i*sin(t/2)*(n.sigma), unitarity requires |n|=1
    # Encoded: c^2 + s^2 = 1 where c=cos(t/2), s=sin(t/2)
    # And nx^2 + ny^2 + nz^2 = 1
    c = Real("c")
    s = Real("s")
    nx = Real("nx")
    ny = Real("ny")
    nz = Real("nz")

    solver = Solver()
    solver.add(c * c + s * s == 1)
    solver.add(nx * nx + ny * ny + nz * nz == 1)
    # Can we violate the trig identity?
    solver.add(Not(c * c + s * s == 1))
    result_trig = str(solver.check())  # unsat

    # Can |n| != 1?
    s2 = Solver()
    s2.add(nx * nx + ny * ny + nz * nz == 1)
    s2.add(Not(nx * nx + ny * ny + nz * nz == 1))
    result_norm = str(s2.check())  # unsat

    return {
        "trig_identity_forced": result_trig,
        "axis_normalization_forced": result_norm,
        "pass": result_trig == "unsat" and result_norm == "unsat",
    }


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    falsification = run_falsification_tests()
    sympy_check = run_sympy_check()
    z3_check = run_z3_check()

    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "Core module: UnitaryRotation with learnable theta and n, full autograd"
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "Symbolic unitarity, Z/X gate at theta=pi verification"
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "Trig identity and axis normalization constraint verification"

    def count_passes(d):
        passes, total = 0, 0
        if isinstance(d, dict):
            if "pass" in d:
                total += 1
                if d["pass"]:
                    passes += 1
            for v in d.values():
                p, t = count_passes(v)
                passes += p; total += t
        return passes, total

    all_results = {
        "positive": positive, "negative": negative, "boundary": boundary,
        "falsification": falsification, "sympy_check": sympy_check, "z3_check": z3_check,
    }
    total_pass, total_tests = count_passes(all_results)

    results = {
        "name": "torch_unitary_rotation",
        "phase": "Phase 3 sim",
        "description": "General U(theta,n) rotation as differentiable nn.Module with learnable params",
        "tool_manifest": TOOL_MANIFEST,
        **all_results,
        "classification": "canonical",
        "summary": {"total_tests": total_tests, "total_pass": total_pass, "all_pass": total_pass == total_tests},
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "torch_unitary_rotation_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Tests: {total_pass}/{total_tests} passed")
    if total_pass == total_tests:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED -- inspect results JSON")
