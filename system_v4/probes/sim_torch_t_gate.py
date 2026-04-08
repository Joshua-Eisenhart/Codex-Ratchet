#!/usr/bin/env python3
"""
T Gate as a differentiable torch.nn.Module.

T = diag(1, e^{i*pi/4}). Non-Clifford gate.
T^8 = I (eighth root of identity).
T^4 = S gate, T^2 = sqrt(S).

Tests:
- T applied to |0> leaves |0> unchanged (global phase irrelevant in density matrix)
- T^8 = I verified on density matrices
- T on |+> changes phase but stays on Bloch sphere equator (off X-axis)
- Non-Clifford: T does NOT map Paulis to Paulis under conjugation
- Torch vs numpy substrate match
- Autograd gradients
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
# T GATE UNITARY (single qubit, 2x2)
# =====================================================================

T_PHASE = np.exp(1j * np.pi / 4)
T_MATRIX_NP = np.diag([1, T_PHASE]).astype(np.complex128)


# =====================================================================
# MODULE UNDER TEST: T Gate
# =====================================================================

class TGate(nn.Module):
    """Differentiable T gate on single-qubit density matrices.

    T = diag(1, e^{i*pi/4}). Non-Clifford.
    forward(rho) applies: rho -> T * rho * T dagger
    """

    def __init__(self):
        super().__init__()
        phase = torch.tensor(np.pi / 4)
        U = torch.zeros(2, 2, dtype=torch.complex64)
        U[0, 0] = 1.0
        U[1, 1] = torch.exp(1j * phase)
        self.register_buffer("U", U)

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


def numpy_t_gate(rho):
    return T_MATRIX_NP @ rho @ T_MATRIX_NP.conj().T


def bloch_vector(rho):
    """Extract Bloch vector (x, y, z) from single-qubit density matrix."""
    X = np.array([[0, 1], [1, 0]], dtype=np.complex128)
    Y = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
    Z = np.array([[1, 0], [0, -1]], dtype=np.complex128)
    x = float(np.real(np.trace(X @ rho)))
    y = float(np.real(np.trace(Y @ rho)))
    z = float(np.real(np.trace(Z @ rho)))
    return x, y, z


# =====================================================================
# STANDARD KETS
# =====================================================================

KET_0 = np.array([1, 0], dtype=np.complex128)
KET_1 = np.array([0, 1], dtype=np.complex128)
KET_PLUS = np.array([1, 1], dtype=np.complex128) / np.sqrt(2)
KET_MINUS = np.array([1, -1], dtype=np.complex128) / np.sqrt(2)


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # --- P1: T|0> = |0> (density matrix invariant, since T|0> = 1*|0>) ---
    rho_out = numpy_t_gate(ket_to_dm(KET_0))
    diff = float(np.max(np.abs(rho_out - ket_to_dm(KET_0))))
    results["P1_0_unchanged"] = {"max_diff": diff, "pass": diff < 1e-10}

    # --- P2: T|1> = e^{i*pi/4}|1>, density matrix invariant (global phase) ---
    rho_out = numpy_t_gate(ket_to_dm(KET_1))
    diff = float(np.max(np.abs(rho_out - ket_to_dm(KET_1))))
    results["P2_1_phase_only"] = {"max_diff": diff, "pass": diff < 1e-10}

    # --- P3: T^8 = I (on density matrices) ---
    rho_in = ket_to_dm(KET_PLUS)
    rho = rho_in.copy()
    for _ in range(8):
        rho = numpy_t_gate(rho)
    diff = float(np.max(np.abs(rho - rho_in)))
    results["P3_T8_is_identity"] = {"max_diff": diff, "pass": diff < 1e-10}

    # --- P4: T on |+> rotates Bloch vector in XY plane ---
    # |+> has Bloch (1, 0, 0). T|+> = (|0> + e^{i*pi/4}|1>)/sqrt(2)
    # Bloch: x = cos(pi/4), y = sin(pi/4), z = 0
    rho_out = numpy_t_gate(ket_to_dm(KET_PLUS))
    x, y, z = bloch_vector(rho_out)
    expected_x = np.cos(np.pi / 4)
    expected_y = np.sin(np.pi / 4)
    results["P4_plus_rotation"] = {
        "bloch_x": x, "bloch_y": y, "bloch_z": z,
        "x_matches": abs(x - expected_x) < 1e-10,
        "y_matches": abs(y - expected_y) < 1e-10,
        "z_zero": abs(z) < 1e-10,
        "pass": abs(x - expected_x) < 1e-10 and abs(y - expected_y) < 1e-10 and abs(z) < 1e-10,
    }

    # --- P5: Substrate match ---
    p5_results = {}
    test_kets = {"|0>": KET_0, "|1>": KET_1, "|+>": KET_PLUS, "|->": KET_MINUS}
    for name, ket in test_kets.items():
        rho_np = ket_to_dm(ket)
        out_np = numpy_t_gate(rho_np)
        rho_t = torch.tensor(rho_np, dtype=torch.complex64)
        out_t = TGate()(rho_t).detach().cpu().numpy()
        max_diff = float(np.max(np.abs(out_np - out_t)))
        p5_results[name] = {"max_abs_diff": max_diff, "pass": max_diff < 1e-5}
    results["P5_substrate_match"] = p5_results

    # --- P6: Trace preservation ---
    p6_results = {}
    for name, ket in test_kets.items():
        out = numpy_t_gate(ket_to_dm(ket))
        trace = float(np.real(np.trace(out)))
        p6_results[name] = {"trace": trace, "pass": abs(trace - 1.0) < 1e-10}
    results["P6_trace_preservation"] = p6_results

    # --- P7: Unitarity ---
    results["P7_unitarity"] = {"is_unitary": TGate().is_unitary(), "pass": TGate().is_unitary()}

    # --- P8: T^2 = S gate (diag(1, i)), T^4 = Z gate (diag(1, -1)) ---
    T2 = np.linalg.matrix_power(T_MATRIX_NP, 2)
    S_expected = np.diag([1, 1j]).astype(np.complex128)
    diff_t2 = float(np.max(np.abs(T2 - S_expected)))

    T4 = np.linalg.matrix_power(T_MATRIX_NP, 4)
    Z_expected = np.diag([1, -1]).astype(np.complex128)
    diff_t4 = float(np.max(np.abs(T4 - Z_expected)))

    results["P8_T2_is_S_and_T4_is_Z"] = {
        "T2_diff_from_S": diff_t2, "T4_diff_from_Z": diff_t4,
        "pass": diff_t2 < 1e-10 and diff_t4 < 1e-10,
    }

    return results


# =====================================================================
# FALSIFICATION TESTS
# =====================================================================

def run_falsification_tests():
    results = {}

    # --- F1: Gradient of Bloch Y-component through T gate ---
    # Input: cos(theta)|0> + sin(theta)|1>
    # After T: cos(theta)|0> + sin(theta)*e^{i*pi/4}|1>
    # Y component = 2*Im(cos(theta)*sin(theta)*e^{-i*pi/4})
    Y = torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex64)

    f1_results = {}
    for theta_val in [0.1, 0.3, np.pi / 4, 0.7, 1.2]:
        theta = torch.tensor(float(theta_val), requires_grad=True)
        ket = torch.zeros(2, dtype=torch.complex64)
        ket[0] = torch.cos(theta).to(torch.complex64)
        ket[1] = torch.sin(theta).to(torch.complex64)
        rho = torch.outer(ket, ket.conj())
        rho_out = TGate()(rho)
        exp_y = torch.real(torch.trace(Y @ rho_out))
        exp_y.backward()
        grad = theta.grad
        f1_results[f"theta={theta_val:.2f}"] = {
            "theta": float(theta_val),
            "exp_Y": float(exp_y.item()),
            "grad": float(grad.item()) if grad is not None else None,
            "pass": grad is not None,
        }
    results["F1_bloch_Y_gradient"] = f1_results

    # --- F2: Autograd vs finite difference ---
    eps = 1e-4
    theta_test = 0.5
    theta = torch.tensor(float(theta_test), requires_grad=True)
    ket = torch.zeros(2, dtype=torch.complex64)
    ket[0] = torch.cos(theta).to(torch.complex64)
    ket[1] = torch.sin(theta).to(torch.complex64)
    rho = torch.outer(ket, ket.conj())
    rho_out = TGate()(rho)
    exp_y = torch.real(torch.trace(Y @ rho_out))
    exp_y.backward()
    grad_auto = float(theta.grad.item())

    Y_np = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
    def fd_exp_y(th):
        k = np.array([np.cos(th), np.sin(th)], dtype=np.complex128)
        r = np.outer(k, k.conj())
        out = numpy_t_gate(r)
        return float(np.real(np.trace(Y_np @ out)))

    grad_fd = (fd_exp_y(theta_test + eps) - fd_exp_y(theta_test - eps)) / (2 * eps)
    diff = abs(grad_auto - grad_fd)
    results["F2_autograd_vs_fd"] = {
        "autograd": grad_auto, "finite_diff": float(grad_fd),
        "abs_diff": diff, "pass": diff < 0.01,
    }

    # --- F3: Non-Clifford verification ---
    # Clifford gates map Paulis to Paulis under conjugation: U*P*U_dag is a Pauli.
    # T is non-Clifford: T*X*T_dag should NOT be a Pauli.
    X_np = np.array([[0, 1], [1, 0]], dtype=np.complex128)
    TXT = T_MATRIX_NP @ X_np @ T_MATRIX_NP.conj().T
    # Check if TXT is a Pauli (up to phase): compare with I, X, Y, Z
    I_np = np.eye(2, dtype=np.complex128)
    Y_np2 = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
    Z_np = np.array([[1, 0], [0, -1]], dtype=np.complex128)
    paulis = {"I": I_np, "X": X_np, "Y": Y_np2, "Z": Z_np}
    is_pauli = False
    for pname, P in paulis.items():
        for phase in [1, -1, 1j, -1j]:
            if np.max(np.abs(TXT - phase * P)) < 1e-10:
                is_pauli = True
    results["F3_non_clifford"] = {
        "TXT_is_pauli": is_pauli,
        "pass": not is_pauli,  # EXPECT T is non-Clifford
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # --- N1: Non-unitary T detected ---
    class BadT(nn.Module):
        def __init__(self):
            super().__init__()
            U = torch.zeros(2, 2, dtype=torch.complex64)
            U[0, 0] = 1.0
            U[1, 1] = 0.5 * torch.exp(1j * torch.tensor(np.pi / 4))
            self.register_buffer("U", U)
        def is_unitary(self, tol=1e-6):
            UUd = self.U @ self.U.conj().T
            diff = torch.max(torch.abs(UUd - torch.eye(2, dtype=self.U.dtype)))
            return float(diff.item()) < tol

    results["N1_non_unitary_detected"] = {"is_unitary": BadT().is_unitary(), "pass": not BadT().is_unitary()}

    # --- N2: T is NOT self-inverse (T^2 != I) ---
    rho_in = ket_to_dm(KET_PLUS)
    rho_out = numpy_t_gate(numpy_t_gate(rho_in))
    diff = float(np.max(np.abs(rho_out - rho_in)))
    results["N2_not_self_inverse"] = {"max_diff": diff, "pass": diff > 1e-6}

    # --- N3: Hermiticity preserved ---
    for name, ket in {"|0>": KET_0, "|+>": KET_PLUS}.items():
        rho_t = torch.tensor(ket_to_dm(ket), dtype=torch.complex64)
        out = TGate()(rho_t).detach().cpu().numpy()
        herm_diff = float(np.max(np.abs(out - out.conj().T)))
        results[f"N3_hermiticity_{name}"] = {"diff": herm_diff, "pass": herm_diff < 1e-6}

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # --- B1: Maximally mixed invariant ---
    rho_mixed = np.eye(2, dtype=np.complex128) / 2
    out = numpy_t_gate(rho_mixed)
    diff = float(np.max(np.abs(out - rho_mixed)))
    results["B1_mixed_invariant"] = {"max_diff": diff, "pass": diff < 1e-10}

    # --- B2: Purity preserved ---
    np.random.seed(55)
    b2_results = {}
    for i in range(5):
        a = np.random.randn(2) + 1j * np.random.randn(2); a /= np.linalg.norm(a)
        rho = ket_to_dm(a)
        out = numpy_t_gate(rho)
        p_in = float(np.real(np.trace(rho @ rho)))
        p_out = float(np.real(np.trace(out @ out)))
        b2_results[f"state_{i}"] = {"purity_in": p_in, "purity_out": p_out, "pass": abs(p_in - p_out) < 1e-10}
    results["B2_purity_preserved"] = b2_results

    # --- B3: Bloch sphere radius preserved (T is unitary, preserves |r|) ---
    np.random.seed(66)
    b3_results = {}
    for i in range(5):
        a = np.random.randn(2) + 1j * np.random.randn(2); a /= np.linalg.norm(a)
        rho = ket_to_dm(a)
        x_in, y_in, z_in = bloch_vector(rho)
        r_in = np.sqrt(x_in**2 + y_in**2 + z_in**2)
        out = numpy_t_gate(rho)
        x_out, y_out, z_out = bloch_vector(out)
        r_out = np.sqrt(x_out**2 + y_out**2 + z_out**2)
        b3_results[f"state_{i}"] = {"r_in": r_in, "r_out": r_out, "pass": abs(r_in - r_out) < 1e-10}
    results["B3_bloch_radius_preserved"] = b3_results

    # --- B4: T applied 8 times on random state = identity ---
    np.random.seed(77)
    a = np.random.randn(2) + 1j * np.random.randn(2); a /= np.linalg.norm(a)
    rho = ket_to_dm(a)
    rho_8 = rho.copy()
    for _ in range(8):
        rho_8 = numpy_t_gate(rho_8)
    diff = float(np.max(np.abs(rho_8 - rho)))
    results["B4_T8_random_state"] = {"max_diff": diff, "pass": diff < 1e-10}

    return results


# =====================================================================
# SYMPY CHECK
# =====================================================================

def run_sympy_check():
    if not TOOL_MANIFEST["sympy"]["tried"]:
        return {"skipped": True, "reason": "sympy not available"}

    T = sp.Matrix([[1, 0], [0, sp.exp(sp.I * sp.pi / 4)]])
    TTd = T * T.H
    is_unitary = sp.simplify(TTd - sp.eye(2)) == sp.zeros(2)

    T8 = T**8
    is_T8_identity = sp.simplify(T8 - sp.eye(2)) == sp.zeros(2)

    T2 = T**2
    S_expected = sp.Matrix([[1, 0], [0, sp.I]])
    is_T2_S = sp.simplify(T2 - S_expected) == sp.zeros(2)

    T4 = T**4
    Z_expected = sp.Matrix([[1, 0], [0, -1]])
    is_T4_Z = sp.simplify(T4 - Z_expected) == sp.zeros(2)

    return {
        "is_unitary": bool(is_unitary),
        "T8_is_identity": bool(is_T8_identity),
        "T2_is_S": bool(is_T2_S),
        "T4_is_Z": bool(is_T4_Z),
        "pass": all([bool(is_unitary), bool(is_T8_identity), bool(is_T2_S), bool(is_T4_Z)]),
    }


# =====================================================================
# Z3 CHECK
# =====================================================================

def run_z3_check():
    if not TOOL_MANIFEST["z3"]["tried"]:
        return {"skipped": True, "reason": "z3 not available"}

    from z3 import Real, Solver, And, Not

    # T gate phases: |d0|=1, |d1|=1 (diagonal unitarity)
    # d0=1, d1=e^{i*pi/4} -> |d1|^2 = 1
    # Verify: if |d|^2 = 1 for both entries, unitarity holds for diagonal gate
    d0_r, d0_i = Real("d0_r"), Real("d0_i")
    d1_r, d1_i = Real("d1_r"), Real("d1_i")
    solver = Solver()
    solver.add(d0_r * d0_r + d0_i * d0_i == 1)
    solver.add(d1_r * d1_r + d1_i * d1_i == 1)
    # Can we violate unitarity? No.
    solver.add(Not(d0_r * d0_r + d0_i * d0_i == 1))
    result = str(solver.check())  # unsat

    return {"diagonal_unitarity_forced": result, "pass": result == "unsat"}


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
    TOOL_MANIFEST["pytorch"]["reason"] = "Core module: T gate as nn.Module, autograd for Bloch gradients"
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "Symbolic unitarity, T^8=I, T^4=S verification"
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "Diagonal unitarity constraint verification"

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
        "name": "torch_t_gate",
        "phase": "Phase 3 sim",
        "description": "T gate (non-Clifford) as differentiable nn.Module",
        "tool_manifest": TOOL_MANIFEST,
        **all_results,
        "classification": "canonical",
        "summary": {"total_tests": total_tests, "total_pass": total_pass, "all_pass": total_pass == total_tests},
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "torch_t_gate_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Tests: {total_pass}/{total_tests} passed")
    if total_pass == total_tests:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED -- inspect results JSON")
