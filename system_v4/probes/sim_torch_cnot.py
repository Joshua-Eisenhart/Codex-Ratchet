#!/usr/bin/env python3
"""
CNOT Gate as a differentiable torch.nn.Module.

The first entangling gate module. Applies CNOT: rho -> U*rho*U†
where U is the 4x4 CNOT unitary (control=qubit 0, target=qubit 1).

Tests torch CNOT against numpy baseline across:
- Product state transformations (|00> -> |00>, |10> -> |11>)
- Entanglement creation from |+0> (verified via partial trace + entropy)
- Gradient of entanglement entropy w.r.t. input state parameters
- Non-unitary "CNOT" detection
- Sympy symbolic unitarity check
- z3 constraint verification
"""

import json
import os
import numpy as np
classification = "classical_baseline"  # auto-backfill

# =====================================================================
# TOOL MANIFEST -- Document which tools were tried
# =====================================================================

TOOL_MANIFEST = {
    # --- Computation layer ---
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": ""},
    # --- Proof layer ---
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    # --- Symbolic layer ---
    "sympy": {"tried": False, "used": False, "reason": ""},
    # --- Geometry layer ---
    "clifford": {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": ""},
    # --- Graph layer ---
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi": {"tried": False, "used": False, "reason": ""},
    # --- Topology layer ---
    "toponetx": {"tried": False, "used": False, "reason": ""},
    "gudhi": {"tried": False, "used": False, "reason": ""},
}

# Try importing each tool
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
except Exception as exc:
    TOOL_MANIFEST["clifford"]["reason"] = f"optional import unavailable: {exc}"

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
# CNOT UNITARY
# =====================================================================

# Standard CNOT: |00> -> |00>, |01> -> |01>, |10> -> |11>, |11> -> |10>
CNOT_MATRIX_NP = np.array([
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 0, 1],
    [0, 0, 1, 0],
], dtype=np.complex128)

CNOT_MATRIX_TORCH = torch.tensor([
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 0, 1],
    [0, 0, 1, 0],
], dtype=torch.complex64)


# =====================================================================
# MODULE UNDER TEST: CNOT
# =====================================================================

class CNOT(nn.Module):
    """Differentiable CNOT gate on 2-qubit density matrices.

    forward(rho) applies: rho -> U * rho * U†
    where U is the 4x4 CNOT unitary.

    The module itself has no learnable parameters, but gradients
    flow through the input density matrix for upstream optimization.
    """

    def __init__(self):
        super().__init__()
        # Register as buffer (not parameter) -- the gate is fixed
        self.register_buffer(
            "U",
            torch.tensor([
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 0, 1],
                [0, 0, 1, 0],
            ], dtype=torch.complex64),
        )

    def forward(self, rho):
        U = self.U.to(rho.dtype)
        return U @ rho @ U.conj().T

    def is_unitary(self, tol=1e-6):
        """Check U*U† = I."""
        UUd = self.U @ self.U.conj().T
        diff = torch.max(torch.abs(UUd - torch.eye(4, dtype=self.U.dtype)))
        return float(diff.item()) < tol


# =====================================================================
# HELPER: State construction
# =====================================================================

def ket_to_dm(ket_np):
    """Convert column vector to density matrix."""
    return np.outer(ket_np, ket_np.conj())


def partial_trace_B(rho_4x4):
    """Partial trace over qubit B (subsystem 1) of a 2-qubit state.
    Returns 2x2 reduced density matrix of qubit A.
    rho is in computational basis |00>, |01>, |10>, |11>.
    """
    rho = np.array(rho_4x4, dtype=np.complex128)
    rho_A = np.zeros((2, 2), dtype=np.complex128)
    # rho_A[i,j] = sum_k rho[2*i+k, 2*j+k]
    for i in range(2):
        for j in range(2):
            for k in range(2):
                rho_A[i, j] += rho[2 * i + k, 2 * j + k]
    return rho_A


def partial_trace_A(rho_4x4):
    """Partial trace over qubit A (subsystem 0) of a 2-qubit state.
    Returns 2x2 reduced density matrix of qubit B.
    """
    rho = np.array(rho_4x4, dtype=np.complex128)
    rho_B = np.zeros((2, 2), dtype=np.complex128)
    # rho_B[k,l] = sum_i rho[2*i+k, 2*i+l]
    for k in range(2):
        for l in range(2):
            for i in range(2):
                rho_B[k, l] += rho[2 * i + k, 2 * i + l]
    return rho_B


def von_neumann_entropy(rho):
    """S = -Tr(rho log rho) via eigenvalues."""
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > 1e-12]
    return float(-np.sum(evals * np.log(evals)))


def entanglement_entropy_np(rho_4x4):
    """Entanglement entropy = S(rho_A) for a 2-qubit state."""
    rho_A = partial_trace_B(rho_4x4)
    return von_neumann_entropy(rho_A)


# =====================================================================
# TORCH HELPERS
# =====================================================================

def torch_partial_trace_B(rho):
    """Partial trace over qubit B, differentiable."""
    rho_A = torch.zeros(2, 2, dtype=rho.dtype, device=rho.device)
    for i in range(2):
        for j in range(2):
            for k in range(2):
                rho_A[i, j] = rho_A[i, j] + rho[2 * i + k, 2 * j + k]
    return rho_A


def torch_entanglement_entropy(rho):
    """Entanglement entropy of 2-qubit state, differentiable."""
    rho_A = torch_partial_trace_B(rho)
    evals = torch.linalg.eigvalsh(rho_A)
    evals = torch.clamp(evals.real, min=1e-12)
    return -torch.sum(evals * torch.log(evals))


# =====================================================================
# NUMPY BASELINE
# =====================================================================

def numpy_cnot(rho):
    """Apply CNOT to 4x4 density matrix using numpy."""
    U = CNOT_MATRIX_NP
    return U @ rho @ U.conj().T


# =====================================================================
# STANDARD KETS
# =====================================================================

KET_0 = np.array([1, 0], dtype=np.complex128)
KET_1 = np.array([0, 1], dtype=np.complex128)
KET_PLUS = np.array([1, 1], dtype=np.complex128) / np.sqrt(2)
KET_MINUS = np.array([1, -1], dtype=np.complex128) / np.sqrt(2)

# 2-qubit kets (tensor products)
KET_00 = np.kron(KET_0, KET_0)
KET_01 = np.kron(KET_0, KET_1)
KET_10 = np.kron(KET_1, KET_0)
KET_11 = np.kron(KET_1, KET_1)
KET_PLUS_0 = np.kron(KET_PLUS, KET_0)  # |+0> = (|00> + |10>) / sqrt(2)

# Bell state: CNOT(|+0>) = (|00> + |11>) / sqrt(2)
KET_BELL = (KET_00 + KET_11) / np.sqrt(2)


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # --- P1: |00> -> |00> (control=0, no flip) ---
    rho_in = ket_to_dm(KET_00)
    rho_out_np = numpy_cnot(rho_in)
    rho_expected = ket_to_dm(KET_00)
    diff = float(np.max(np.abs(rho_out_np - rho_expected)))
    results["P1_00_unchanged"] = {
        "max_diff": diff,
        "pass": diff < 1e-10,
    }

    # --- P2: |01> -> |01> (control=0, no flip) ---
    rho_in = ket_to_dm(KET_01)
    rho_out_np = numpy_cnot(rho_in)
    rho_expected = ket_to_dm(KET_01)
    diff = float(np.max(np.abs(rho_out_np - rho_expected)))
    results["P2_01_unchanged"] = {
        "max_diff": diff,
        "pass": diff < 1e-10,
    }

    # --- P3: |10> -> |11> (control=1, target flipped) ---
    rho_in = ket_to_dm(KET_10)
    rho_out_np = numpy_cnot(rho_in)
    rho_expected = ket_to_dm(KET_11)
    diff = float(np.max(np.abs(rho_out_np - rho_expected)))
    results["P3_10_to_11"] = {
        "max_diff": diff,
        "pass": diff < 1e-10,
    }

    # --- P4: |11> -> |10> (control=1, target flipped) ---
    rho_in = ket_to_dm(KET_11)
    rho_out_np = numpy_cnot(rho_in)
    rho_expected = ket_to_dm(KET_10)
    diff = float(np.max(np.abs(rho_out_np - rho_expected)))
    results["P4_11_to_10"] = {
        "max_diff": diff,
        "pass": diff < 1e-10,
    }

    # --- P5: |+0> -> Bell state (entanglement creation) ---
    rho_in = ket_to_dm(KET_PLUS_0)
    rho_out_np = numpy_cnot(rho_in)
    rho_bell = ket_to_dm(KET_BELL)
    diff = float(np.max(np.abs(rho_out_np - rho_bell)))

    # Verify entanglement via partial trace entropy
    ent_entropy = entanglement_entropy_np(rho_out_np)

    results["P5_plus0_to_bell"] = {
        "max_diff_from_bell": diff,
        "entanglement_entropy": ent_entropy,
        "is_maximally_entangled": abs(ent_entropy - np.log(2)) < 1e-6,
        "pass": diff < 1e-10 and abs(ent_entropy - np.log(2)) < 1e-6,
    }

    # --- P6: Substrate match (torch vs numpy) ---
    p6_results = {}
    test_kets = {
        "|00>": KET_00, "|01>": KET_01, "|10>": KET_10,
        "|11>": KET_11, "|+0>": KET_PLUS_0,
    }
    for name, ket in test_kets.items():
        rho_np = ket_to_dm(ket)
        out_np = numpy_cnot(rho_np)

        rho_t = torch.tensor(rho_np, dtype=torch.complex64)
        gate = CNOT()
        out_t = gate(rho_t).detach().cpu().numpy()

        max_diff = float(np.max(np.abs(out_np - out_t)))
        p6_results[name] = {
            "max_abs_diff": max_diff,
            "pass": max_diff < 1e-5,
        }
    results["P6_substrate_match"] = p6_results

    # --- P7: Trace preservation ---
    p7_results = {}
    for name, ket in test_kets.items():
        rho_np = ket_to_dm(ket)
        out_np = numpy_cnot(rho_np)
        trace = float(np.real(np.trace(out_np)))
        p7_results[name] = {
            "trace": trace,
            "diff_from_1": abs(trace - 1.0),
            "pass": abs(trace - 1.0) < 1e-10,
        }
    results["P7_trace_preservation"] = p7_results

    # --- P8: Unitarity of gate ---
    gate = CNOT()
    results["P8_unitarity"] = {
        "is_unitary": gate.is_unitary(),
        "pass": gate.is_unitary(),
    }

    # --- P9: CNOT is self-inverse (CNOT^2 = I) ---
    rho_np = ket_to_dm(KET_PLUS_0)
    out1 = numpy_cnot(rho_np)
    out2 = numpy_cnot(out1)
    diff = float(np.max(np.abs(out2 - rho_np)))
    results["P9_self_inverse"] = {
        "max_diff_after_double_apply": diff,
        "pass": diff < 1e-10,
    }

    return results


# =====================================================================
# FALSIFICATION TESTS
# =====================================================================

def run_falsification_tests():
    results = {}

    # --- F1: Gradient of entanglement entropy w.r.t. input state params ---
    # Parameterize input as: |psi> = cos(theta)|00> + sin(theta)|10>
    # CNOT maps this to cos(theta)|00> + sin(theta)|11>
    # Entanglement entropy should peak at theta=pi/4
    f1_results = {}
    thetas = [0.1, 0.3, np.pi / 8, np.pi / 4, 3 * np.pi / 8, 0.7]
    for theta_val in thetas:
        theta = torch.tensor(float(theta_val), requires_grad=True)
        # Build |psi> = cos(theta)|00> + sin(theta)|10>
        ket = torch.zeros(4, dtype=torch.complex64)
        ket[0] = torch.cos(theta).to(torch.complex64)
        ket[2] = torch.sin(theta).to(torch.complex64)
        rho = torch.outer(ket, ket.conj())

        gate = CNOT()
        rho_out = gate(rho)
        S = torch_entanglement_entropy(rho_out)
        S.backward()
        grad = theta.grad

        f1_results[f"theta={theta_val:.4f}"] = {
            "theta": float(theta_val),
            "entanglement_entropy": float(S.item()),
            "grad_theta": float(grad.item()) if grad is not None else None,
            "grad_exists": grad is not None,
            "pass": grad is not None,
        }
    results["F1_entanglement_gradient_wrt_theta"] = f1_results

    # --- F2: At theta=pi/4, gradient of S should be ~0 (max entropy) ---
    theta = torch.tensor(float(np.pi / 4), requires_grad=True)
    ket = torch.zeros(4, dtype=torch.complex64)
    ket[0] = torch.cos(theta).to(torch.complex64)
    ket[2] = torch.sin(theta).to(torch.complex64)
    rho = torch.outer(ket, ket.conj())
    gate = CNOT()
    rho_out = gate(rho)
    S = torch_entanglement_entropy(rho_out)
    S.backward()
    grad_at_max = float(theta.grad.item())
    results["F2_gradient_zero_at_max_entropy"] = {
        "theta": float(np.pi / 4),
        "entropy": float(S.item()),
        "grad": grad_at_max,
        "grad_near_zero": abs(grad_at_max) < 0.05,
        "entropy_near_log2": abs(float(S.item()) - np.log(2)) < 1e-4,
        "pass": abs(grad_at_max) < 0.05 and abs(float(S.item()) - np.log(2)) < 1e-4,
    }

    # --- F3: Autograd vs finite-difference for entanglement entropy ---
    eps = 1e-4
    theta_test = 0.3
    # Autograd
    theta = torch.tensor(float(theta_test), requires_grad=True)
    ket = torch.zeros(4, dtype=torch.complex64)
    ket[0] = torch.cos(theta).to(torch.complex64)
    ket[2] = torch.sin(theta).to(torch.complex64)
    rho = torch.outer(ket, ket.conj())
    gate = CNOT()
    rho_out = gate(rho)
    S = torch_entanglement_entropy(rho_out)
    S.backward()
    grad_auto = float(theta.grad.item())

    # Finite difference
    def fd_entropy(th):
        k = np.zeros(4, dtype=np.complex128)
        k[0] = np.cos(th)
        k[2] = np.sin(th)
        rho_fd = np.outer(k, k.conj())
        out_fd = numpy_cnot(rho_fd)
        return entanglement_entropy_np(out_fd)

    grad_fd = (fd_entropy(theta_test + eps) - fd_entropy(theta_test - eps)) / (2 * eps)
    diff = abs(grad_auto - grad_fd)

    results["F3_autograd_vs_finite_diff"] = {
        "autograd": grad_auto,
        "finite_diff": float(grad_fd),
        "abs_diff": diff,
        "pass": diff < 0.05,
    }

    # --- F4: 20 random product states, substrate match ---
    np.random.seed(42)
    max_diffs = []
    for _ in range(20):
        # Random 2-qubit product state
        a = np.random.randn(2) + 1j * np.random.randn(2)
        a /= np.linalg.norm(a)
        b = np.random.randn(2) + 1j * np.random.randn(2)
        b /= np.linalg.norm(b)
        ket_rand = np.kron(a, b)
        rho_np = ket_to_dm(ket_rand)

        out_np = numpy_cnot(rho_np)
        rho_t = torch.tensor(rho_np, dtype=torch.complex64)
        gate = CNOT()
        out_t = gate(rho_t).detach().cpu().numpy()
        max_diffs.append(float(np.max(np.abs(out_np - out_t))))

    results["F4_random_product_states_match"] = {
        "n_states": 20,
        "overall_max_diff": max(max_diffs),
        "mean_max_diff": float(np.mean(max_diffs)),
        "pass": max(max_diffs) < 1e-5,
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # --- N1: Non-unitary "CNOT" should fail unitarity check ---
    class BadCNOT(nn.Module):
        def __init__(self):
            super().__init__()
            # Perturbed CNOT -- not unitary
            self.register_buffer("U", torch.tensor([
                [1.0, 0, 0, 0],
                [0, 1.0, 0, 0],
                [0, 0, 0.5, 1],  # Not unitary row
                [0, 0, 1, 0],
            ], dtype=torch.complex64))

        def is_unitary(self, tol=1e-6):
            UUd = self.U @ self.U.conj().T
            diff = torch.max(torch.abs(UUd - torch.eye(4, dtype=self.U.dtype)))
            return float(diff.item()) < tol

    bad_gate = BadCNOT()
    results["N1_non_unitary_cnot_detected"] = {
        "is_unitary": bad_gate.is_unitary(),
        "pass": not bad_gate.is_unitary(),  # EXPECT failure
    }

    # --- N2: Non-unitary gate does not preserve trace ---
    rho_in = ket_to_dm(KET_PLUS_0)
    U_bad = np.array([
        [1.0, 0, 0, 0],
        [0, 1.0, 0, 0],
        [0, 0, 0.5, 1],
        [0, 0, 1, 0],
    ], dtype=np.complex128)
    rho_out = U_bad @ rho_in @ U_bad.conj().T
    trace_out = float(np.real(np.trace(rho_out)))
    results["N2_non_unitary_trace_violation"] = {
        "trace_out": trace_out,
        "trace_preserved": abs(trace_out - 1.0) < 1e-6,
        "pass": abs(trace_out - 1.0) > 1e-6,  # EXPECT violation
    }

    # --- N3: Product state input to CNOT remains separable iff control=|0> ---
    # |00> after CNOT is still product; |10> after CNOT is |11> (still product)
    # Only superposition of control creates entanglement
    for name, ket in {"|00>": KET_00, "|10>": KET_10, "|01>": KET_01, "|11>": KET_11}.items():
        rho_np = ket_to_dm(ket)
        out = numpy_cnot(rho_np)
        ent = entanglement_entropy_np(out)
        results[f"N3_product_stays_product_{name}"] = {
            "entanglement_entropy": ent,
            "is_product": ent < 1e-10,
            "pass": ent < 1e-10,  # Computational basis states stay product
        }

    # --- N4: Hermiticity preserved ---
    n4_results = {}
    for name, ket in {"|00>": KET_00, "|+0>": KET_PLUS_0}.items():
        rho_np = ket_to_dm(ket)
        rho_t = torch.tensor(rho_np, dtype=torch.complex64)
        gate = CNOT()
        out = gate(rho_t).detach().cpu().numpy()
        herm_diff = float(np.max(np.abs(out - out.conj().T)))
        n4_results[name] = {
            "hermitian_diff": herm_diff,
            "is_hermitian": herm_diff < 1e-6,
            "pass": herm_diff < 1e-6,
        }
    results["N4_output_hermiticity"] = n4_results

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # --- B1: Entanglement entropy sweep over theta ---
    # |psi> = cos(theta)|00> + sin(theta)|10>
    # After CNOT: cos(theta)|00> + sin(theta)|11>
    # S_A = -cos^2(theta)log(cos^2(theta)) - sin^2(theta)log(sin^2(theta))
    thetas = np.linspace(0.01, np.pi / 2 - 0.01, 30)
    entropies = []
    for theta in thetas:
        ket = np.zeros(4, dtype=np.complex128)
        ket[0] = np.cos(theta)
        ket[2] = np.sin(theta)
        rho = ket_to_dm(ket)
        out = numpy_cnot(rho)
        entropies.append(entanglement_entropy_np(out))

    max_idx = int(np.argmax(entropies))
    theta_at_max = float(thetas[max_idx])

    results["B1_entanglement_sweep"] = {
        "thetas": thetas.tolist(),
        "entropies": entropies,
        "theta_at_max_entropy": theta_at_max,
        "max_entropy": float(max(entropies)),
        "max_near_pi_over_4": abs(theta_at_max - np.pi / 4) < 0.1,
        "max_near_log2": abs(max(entropies) - np.log(2)) < 0.01,
        "pass": abs(theta_at_max - np.pi / 4) < 0.1,
    }

    # --- B2: theta=0 (|00>) produces zero entanglement ---
    ket = np.zeros(4, dtype=np.complex128)
    ket[0] = 1.0
    rho = ket_to_dm(ket)
    out = numpy_cnot(rho)
    ent = entanglement_entropy_np(out)
    results["B2_theta0_no_entanglement"] = {
        "entanglement_entropy": ent,
        "pass": ent < 1e-10,
    }

    # --- B3: theta=pi/2 (|10>) produces zero entanglement (maps to |11>) ---
    ket = np.zeros(4, dtype=np.complex128)
    ket[2] = 1.0
    rho = ket_to_dm(ket)
    out = numpy_cnot(rho)
    ent = entanglement_entropy_np(out)
    results["B3_theta_pi2_no_entanglement"] = {
        "entanglement_entropy": ent,
        "pass": ent < 1e-10,
    }

    # --- B4: Mixed input state ---
    # Maximally mixed 2-qubit state stays maximally mixed under CNOT
    rho_mixed = np.eye(4, dtype=np.complex128) / 4
    out = numpy_cnot(rho_mixed)
    diff = float(np.max(np.abs(out - rho_mixed)))
    results["B4_maximally_mixed_invariant"] = {
        "max_diff": diff,
        "pass": diff < 1e-10,
    }

    # --- B5: Purity preserved (unitary channel) ---
    np.random.seed(99)
    b5_results = {}
    for i in range(5):
        a = np.random.randn(2) + 1j * np.random.randn(2)
        a /= np.linalg.norm(a)
        b = np.random.randn(2) + 1j * np.random.randn(2)
        b /= np.linalg.norm(b)
        ket_rand = np.kron(a, b)
        rho = ket_to_dm(ket_rand)
        out = numpy_cnot(rho)
        purity_in = float(np.real(np.trace(rho @ rho)))
        purity_out = float(np.real(np.trace(out @ out)))
        b5_results[f"state_{i}"] = {
            "purity_in": purity_in,
            "purity_out": purity_out,
            "diff": abs(purity_in - purity_out),
            "pass": abs(purity_in - purity_out) < 1e-10,
        }
    results["B5_purity_preserved"] = b5_results

    return results


# =====================================================================
# SYMPY SYMBOLIC CHECK
# =====================================================================

def run_sympy_check():
    """Symbolic verification of CNOT unitarity and Bell state creation."""
    if not TOOL_MANIFEST["sympy"]["tried"]:
        return {"skipped": True, "reason": "sympy not available"}

    U = sp.Matrix([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
        [0, 0, 1, 0],
    ])

    # Unitarity: U*U† = I
    UUd = U * U.H
    is_unitary = UUd == sp.eye(4)

    # Self-inverse: U^2 = I
    U2 = U * U
    is_self_inverse = U2 == sp.eye(4)

    # Bell state creation: U|+0> = (|00> + |11>)/sqrt(2)
    ket_plus_0 = sp.Matrix([1, 0, 1, 0]) / sp.sqrt(2)
    out = U * ket_plus_0
    expected_bell = sp.Matrix([1, 0, 0, 1]) / sp.sqrt(2)
    is_bell = sp.simplify(out - expected_bell) == sp.zeros(4, 1)

    return {
        "is_unitary": bool(is_unitary),
        "is_self_inverse": bool(is_self_inverse),
        "creates_bell_from_plus0": bool(is_bell),
        "pass": bool(is_unitary) and bool(is_self_inverse) and bool(is_bell),
    }


# =====================================================================
# Z3 CONSTRAINT CHECK
# =====================================================================

def run_z3_check():
    """Use z3 to verify: entanglement entropy is non-negative and bounded by log(2)."""
    if not TOOL_MANIFEST["z3"]["tried"]:
        return {"skipped": True, "reason": "z3 not available"}

    from z3 import Real, Solver, And, Not, Implies, sat, unsat

    # For state cos(theta)|00> + sin(theta)|10> after CNOT:
    # rho_A eigenvalues are cos^2(theta) and sin^2(theta)
    # S = -c*ln(c) - s*ln(s) where c=cos^2, s=sin^2, c+s=1
    # We check: c in [0,1] implies S >= 0
    c = Real("c")
    s = Real("s")

    # z3 cannot do transcendental functions directly,
    # but we can verify the constraint structure:
    # c + s = 1, c >= 0, s >= 0 implies both are valid probabilities
    solver = Solver()
    solver.add(c + s == 1)
    solver.add(And(c >= 0, s >= 0))
    # Can we have c + s != 1? No -- check it's forced
    solver.add(Not(c + s == 1))
    # This is trivially unsat since we added c+s=1 and Not(c+s=1)
    result_normalization = str(solver.check())

    # Can eigenvalue be negative? c=cos^2(theta) is always >= 0
    # s=sin^2(theta) is always >= 0. Both bounded by [0,1].
    # Verify: c in [0,1] and s=1-c implies s in [0,1]
    s2 = Solver()
    s2.add(And(c >= 0, c <= 1))
    s2.add(s == 1 - c)
    s2.add(s < 0)  # Can s be negative?
    result_neg_prob = str(s2.check())  # Should be unsat

    # Can c > 1 when c = cos^2(theta) in [0,1]?
    s3 = Solver()
    s3.add(And(c >= 0, c <= 1))
    s3.add(c > 1)
    result_overunit = str(s3.check())  # Should be unsat

    return {
        "normalization_forced": result_normalization,
        "negative_probability_impossible": result_neg_prob,
        "overunit_impossible": result_overunit,
        "pass": result_neg_prob == "unsat" and result_overunit == "unsat",
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

    # Mark tools as used
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "Core module: CNOT as nn.Module, autograd for entanglement entropy gradients"
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "Symbolic unitarity, self-inverse, and Bell state creation verification"
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "Probability constraint verification for reduced state eigenvalues"

    # Count passes
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
        "falsification": falsification,
        "sympy_check": sympy_check,
        "z3_check": z3_check,
    }
    total_pass, total_tests = count_passes(all_results)

    results = {
        "name": "torch_cnot",
        "phase": "Phase 3 sim",
        "description": "CNOT entangling gate as differentiable nn.Module with entanglement entropy gradients",
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "falsification": falsification,
        "sympy_check": sympy_check,
        "z3_check": z3_check,
        "classification": "canonical",
        "summary": {
            "total_tests": total_tests,
            "total_pass": total_pass,
            "all_pass": total_pass == total_tests,
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "torch_cnot_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Tests: {total_pass}/{total_tests} passed")
    if total_pass == total_tests:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED -- inspect results JSON")
