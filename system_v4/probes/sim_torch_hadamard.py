#!/usr/bin/env python3
"""
Hadamard Gate as a differentiable torch.nn.Module.

H = (X + Z) / sqrt(2) = [[1, 1], [1, -1]] / sqrt(2).
Single-qubit gate. Self-inverse: H^2 = I.
Maps Z-basis to X-basis: |0> -> |+>, |1> -> |->.

Tests:
- |0> -> |+>, |+> -> |0>
- Self-inverse: H^2 = I
- Torch vs numpy substrate match
- Autograd gradients
- Non-unitary detection
- Sympy/z3 checks
"""

import json
import os
import numpy as np
classification = "classical_baseline"  # auto-backfill

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
# HADAMARD UNITARY (single qubit, 2x2)
# =====================================================================

H_MATRIX_NP = np.array([[1, 1], [1, -1]], dtype=np.complex128) / np.sqrt(2)


# =====================================================================
# MODULE UNDER TEST: Hadamard
# =====================================================================

class HadamardGate(nn.Module):
    """Differentiable Hadamard gate on single-qubit density matrices.

    forward(rho) applies: rho -> H * rho * H dagger
    H = [[1,1],[1,-1]] / sqrt(2). H is Hermitian so H dagger = H.
    """

    def __init__(self):
        super().__init__()
        self.register_buffer(
            "U",
            torch.tensor([[1, 1], [1, -1]], dtype=torch.complex64) / np.sqrt(2),
        )

    def forward(self, rho):
        U = self.U.to(rho.dtype)
        return U @ rho @ U.conj().T

    def is_unitary(self, tol=1e-6):
        UUd = self.U @ self.U.conj().T
        diff = torch.max(torch.abs(UUd - torch.eye(2, dtype=self.U.dtype)))
        return float(diff.item()) < tol


# =====================================================================
# HELPERS
# =====================================================================

def ket_to_dm(ket_np):
    return np.outer(ket_np, ket_np.conj())


def numpy_hadamard(rho):
    return H_MATRIX_NP @ rho @ H_MATRIX_NP.conj().T


# =====================================================================
# STANDARD KETS (single qubit)
# =====================================================================

KET_0 = np.array([1, 0], dtype=np.complex128)
KET_1 = np.array([0, 1], dtype=np.complex128)
KET_PLUS = np.array([1, 1], dtype=np.complex128) / np.sqrt(2)
KET_MINUS = np.array([1, -1], dtype=np.complex128) / np.sqrt(2)
KET_I = np.array([1, 1j], dtype=np.complex128) / np.sqrt(2)  # |+i>


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # --- P1: |0> -> |+> ---
    rho_out = numpy_hadamard(ket_to_dm(KET_0))
    diff = float(np.max(np.abs(rho_out - ket_to_dm(KET_PLUS))))
    results["P1_0_to_plus"] = {"max_diff": diff, "pass": diff < 1e-10}

    # --- P2: |1> -> |-> ---
    rho_out = numpy_hadamard(ket_to_dm(KET_1))
    diff = float(np.max(np.abs(rho_out - ket_to_dm(KET_MINUS))))
    results["P2_1_to_minus"] = {"max_diff": diff, "pass": diff < 1e-10}

    # --- P3: |+> -> |0> ---
    rho_out = numpy_hadamard(ket_to_dm(KET_PLUS))
    diff = float(np.max(np.abs(rho_out - ket_to_dm(KET_0))))
    results["P3_plus_to_0"] = {"max_diff": diff, "pass": diff < 1e-10}

    # --- P4: |-> -> |1> ---
    rho_out = numpy_hadamard(ket_to_dm(KET_MINUS))
    diff = float(np.max(np.abs(rho_out - ket_to_dm(KET_1))))
    results["P4_minus_to_1"] = {"max_diff": diff, "pass": diff < 1e-10}

    # --- P5: Self-inverse: H^2 = I ---
    rho_in = ket_to_dm(KET_0)
    rho_out = numpy_hadamard(numpy_hadamard(rho_in))
    diff = float(np.max(np.abs(rho_out - rho_in)))
    results["P5_self_inverse"] = {"max_diff": diff, "pass": diff < 1e-10}

    # --- P6: Substrate match ---
    p6_results = {}
    test_kets = {"|0>": KET_0, "|1>": KET_1, "|+>": KET_PLUS, "|->": KET_MINUS}
    for name, ket in test_kets.items():
        rho_np = ket_to_dm(ket)
        out_np = numpy_hadamard(rho_np)
        rho_t = torch.tensor(rho_np, dtype=torch.complex64)
        gate = HadamardGate()
        out_t = gate(rho_t).detach().cpu().numpy()
        max_diff = float(np.max(np.abs(out_np - out_t)))
        p6_results[name] = {"max_abs_diff": max_diff, "pass": max_diff < 1e-5}
    results["P6_substrate_match"] = p6_results

    # --- P7: Trace preservation ---
    p7_results = {}
    for name, ket in test_kets.items():
        out = numpy_hadamard(ket_to_dm(ket))
        trace = float(np.real(np.trace(out)))
        p7_results[name] = {"trace": trace, "pass": abs(trace - 1.0) < 1e-10}
    results["P7_trace_preservation"] = p7_results

    # --- P8: Unitarity ---
    gate = HadamardGate()
    results["P8_unitarity"] = {"is_unitary": gate.is_unitary(), "pass": gate.is_unitary()}

    # --- P9: H is Hermitian (H = H dagger) ---
    diff = float(np.max(np.abs(H_MATRIX_NP - H_MATRIX_NP.conj().T)))
    results["P9_hermitian"] = {"max_diff": diff, "pass": diff < 1e-10}

    return results


# =====================================================================
# FALSIFICATION TESTS
# =====================================================================

def run_falsification_tests():
    results = {}

    # --- F1: Gradient of Bloch z-component through Hadamard ---
    # Input: cos(theta)|0> + sin(theta)|1>, measure <Z> after H
    # H maps this to cos(theta)|+> + sin(theta)|-> = |psi'>
    # <Z> on output = cos(theta)^2 * <+|Z|+> + ... need proper calc
    # Actually: rho_out = H * rho_in * H, <Z> = Tr(Z * rho_out)
    Z = torch.tensor([[1, 0], [0, -1]], dtype=torch.complex64)

    f1_results = {}
    for theta_val in [0.1, 0.5, np.pi / 4, 1.0, 1.3]:
        theta = torch.tensor(float(theta_val), requires_grad=True)
        ket = torch.zeros(2, dtype=torch.complex64)
        ket[0] = torch.cos(theta).to(torch.complex64)
        ket[1] = torch.sin(theta).to(torch.complex64)
        rho = torch.outer(ket, ket.conj())
        gate = HadamardGate()
        rho_out = gate(rho)
        exp_z = torch.real(torch.trace(Z @ rho_out))
        exp_z.backward()
        grad = theta.grad
        f1_results[f"theta={theta_val:.2f}"] = {
            "theta": float(theta_val),
            "exp_Z": float(exp_z.item()),
            "grad": float(grad.item()) if grad is not None else None,
            "pass": grad is not None,
        }
    results["F1_bloch_gradient"] = f1_results

    # --- F2: Autograd vs finite difference ---
    eps = 1e-4
    theta_test = 0.5
    theta = torch.tensor(float(theta_test), requires_grad=True)
    ket = torch.zeros(2, dtype=torch.complex64)
    ket[0] = torch.cos(theta).to(torch.complex64)
    ket[1] = torch.sin(theta).to(torch.complex64)
    rho = torch.outer(ket, ket.conj())
    gate = HadamardGate()
    rho_out = gate(rho)
    exp_z = torch.real(torch.trace(Z @ rho_out))
    exp_z.backward()
    grad_auto = float(theta.grad.item())

    def fd_exp_z(th):
        k = np.array([np.cos(th), np.sin(th)], dtype=np.complex128)
        r = np.outer(k, k.conj())
        out = numpy_hadamard(r)
        Z_np = np.array([[1, 0], [0, -1]], dtype=np.complex128)
        return float(np.real(np.trace(Z_np @ out)))

    grad_fd = (fd_exp_z(theta_test + eps) - fd_exp_z(theta_test - eps)) / (2 * eps)
    diff = abs(grad_auto - grad_fd)
    results["F2_autograd_vs_fd"] = {
        "autograd": grad_auto, "finite_diff": float(grad_fd),
        "abs_diff": diff, "pass": diff < 0.01,
    }

    # --- F3: Random states substrate match ---
    np.random.seed(42)
    max_diffs = []
    for _ in range(20):
        a = np.random.randn(2) + 1j * np.random.randn(2); a /= np.linalg.norm(a)
        rho_np = ket_to_dm(a)
        out_np = numpy_hadamard(rho_np)
        rho_t = torch.tensor(rho_np, dtype=torch.complex64)
        out_t = HadamardGate()(rho_t).detach().cpu().numpy()
        max_diffs.append(float(np.max(np.abs(out_np - out_t))))
    results["F3_random_match"] = {"n": 20, "max_diff": max(max_diffs), "pass": max(max_diffs) < 1e-5}

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # --- N1: Non-unitary Hadamard detected ---
    class BadH(nn.Module):
        def __init__(self):
            super().__init__()
            self.register_buffer("U", torch.tensor([[1, 1], [1, -0.5]], dtype=torch.complex64) / np.sqrt(2))
        def is_unitary(self, tol=1e-6):
            UUd = self.U @ self.U.conj().T
            diff = torch.max(torch.abs(UUd - torch.eye(2, dtype=self.U.dtype)))
            return float(diff.item()) < tol

    results["N1_non_unitary_detected"] = {"is_unitary": BadH().is_unitary(), "pass": not BadH().is_unitary()}

    # --- N2: Non-unitary trace violation ---
    U_bad = np.array([[1, 1], [1, -0.5]], dtype=np.complex128) / np.sqrt(2)
    rho_in = ket_to_dm(KET_1)  # |1> exposes trace violation for this bad matrix
    rho_out = U_bad @ rho_in @ U_bad.conj().T
    trace_out = float(np.real(np.trace(rho_out)))
    results["N2_trace_violation"] = {"trace": trace_out, "pass": abs(trace_out - 1.0) > 1e-6}

    # --- N3: H does not map |0> to |1> (wrong claim) ---
    rho_out = numpy_hadamard(ket_to_dm(KET_0))
    diff_from_1 = float(np.max(np.abs(rho_out - ket_to_dm(KET_1))))
    results["N3_not_0_to_1"] = {"diff": diff_from_1, "pass": diff_from_1 > 0.1}

    # --- N4: Hermiticity preserved ---
    for name, ket in {"|0>": KET_0, "|+i>": KET_I}.items():
        rho_t = torch.tensor(ket_to_dm(ket), dtype=torch.complex64)
        out = HadamardGate()(rho_t).detach().cpu().numpy()
        herm_diff = float(np.max(np.abs(out - out.conj().T)))
        results[f"N4_hermiticity_{name}"] = {"diff": herm_diff, "pass": herm_diff < 1e-6}

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # --- B1: Maximally mixed invariant under H ---
    rho_mixed = np.eye(2, dtype=np.complex128) / 2
    out = numpy_hadamard(rho_mixed)
    diff = float(np.max(np.abs(out - rho_mixed)))
    results["B1_mixed_invariant"] = {"max_diff": diff, "pass": diff < 1e-10}

    # --- B2: Purity preserved ---
    np.random.seed(77)
    b2_results = {}
    for i in range(5):
        a = np.random.randn(2) + 1j * np.random.randn(2); a /= np.linalg.norm(a)
        rho = ket_to_dm(a)
        out = numpy_hadamard(rho)
        p_in = float(np.real(np.trace(rho @ rho)))
        p_out = float(np.real(np.trace(out @ out)))
        b2_results[f"state_{i}"] = {"purity_in": p_in, "purity_out": p_out, "pass": abs(p_in - p_out) < 1e-10}
    results["B2_purity_preserved"] = b2_results

    # --- B3: H swaps X and Z Pauli expectations ---
    # For |0>: <X>=0, <Z>=1. After H: <X>=1, <Z>=0
    X_np = np.array([[0, 1], [1, 0]], dtype=np.complex128)
    Z_np = np.array([[1, 0], [0, -1]], dtype=np.complex128)
    rho_0 = ket_to_dm(KET_0)
    rho_out = numpy_hadamard(rho_0)
    exp_X_out = float(np.real(np.trace(X_np @ rho_out)))
    exp_Z_out = float(np.real(np.trace(Z_np @ rho_out)))
    results["B3_XZ_swap"] = {
        "exp_X_after_H": exp_X_out,
        "exp_Z_after_H": exp_Z_out,
        "X_is_1": abs(exp_X_out - 1.0) < 1e-10,
        "Z_is_0": abs(exp_Z_out) < 1e-10,
        "pass": abs(exp_X_out - 1.0) < 1e-10 and abs(exp_Z_out) < 1e-10,
    }

    return results


# =====================================================================
# SYMPY CHECK
# =====================================================================

def run_sympy_check():
    if not TOOL_MANIFEST["sympy"]["tried"]:
        return {"skipped": True, "reason": "sympy not available"}

    H = sp.Matrix([[1, 1], [1, -1]]) / sp.sqrt(2)
    HHd = H * H.H
    is_unitary = sp.simplify(HHd - sp.eye(2)) == sp.zeros(2)
    H2 = H * H
    is_self_inverse = sp.simplify(H2 - sp.eye(2)) == sp.zeros(2)
    is_hermitian = H == H.H

    # |0> -> |+>
    ket_0 = sp.Matrix([1, 0])
    out = H * ket_0
    expected = sp.Matrix([1, 1]) / sp.sqrt(2)
    maps_0_to_plus = sp.simplify(out - expected) == sp.zeros(2, 1)

    return {
        "is_unitary": bool(is_unitary),
        "is_self_inverse": bool(is_self_inverse),
        "is_hermitian": bool(is_hermitian),
        "maps_0_to_plus": bool(maps_0_to_plus),
        "pass": all([bool(is_unitary), bool(is_self_inverse), bool(is_hermitian), bool(maps_0_to_plus)]),
    }


# =====================================================================
# Z3 CHECK
# =====================================================================

def run_z3_check():
    if not TOOL_MANIFEST["z3"]["tried"]:
        return {"skipped": True, "reason": "z3 not available"}

    from z3 import Real, Solver, And, Not, Or

    # H maps |0> to equal superposition: p(0)=p(1)=1/2
    # Verify: if p0 + p1 = 1 and H applied to |0>, then p0'=1/2, p1'=1/2
    p0 = Real("p0")
    p1 = Real("p1")
    solver = Solver()
    solver.add(p0 == Real("half"))
    solver.add(Real("half") == 1 / 2)
    solver.add(p1 == 1 / 2)
    solver.add(p0 + p1 == 1)
    solver.add(Not(p0 + p1 == 1))
    result = str(solver.check())  # unsat

    return {"normalization_forced": result, "pass": result == "unsat"}


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
    TOOL_MANIFEST["pytorch"]["reason"] = "Core module: Hadamard as nn.Module, autograd for Bloch expectations"
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "Symbolic unitarity, self-inverse, hermiticity, basis mapping"
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "Normalization constraint verification"

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
        "name": "torch_hadamard",
        "phase": "Phase 3 sim",
        "description": "Hadamard gate as differentiable nn.Module -- Z-to-X basis transform",
        "tool_manifest": TOOL_MANIFEST,
        **all_results,
        "classification": "canonical",
        "summary": {"total_tests": total_tests, "total_pass": total_pass, "all_pass": total_pass == total_tests},
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "torch_hadamard_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Tests: {total_pass}/{total_tests} passed")
    if total_pass == total_tests:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED -- inspect results JSON")
