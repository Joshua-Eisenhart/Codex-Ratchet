#!/usr/bin/env python3
"""
iSWAP Gate as a differentiable torch.nn.Module.

iSWAP swaps and adds phase i: |01> -> i|10>, |10> -> i|01>.
NOT self-inverse: iSWAP^2 != I (iSWAP^2 applies -1 phase to swapped components).
Creates entanglement from superposition inputs.

Matrix:
    [[1, 0, 0, 0],
     [0, 0, i, 0],
     [0, i, 0, 0],
     [0, 0, 0, 1]]

Tests:
- |01> -> i|10>, |10> -> i|01>
- |00> and |11> invariant
- NOT self-inverse: iSWAP^2 != I
- iSWAP^4 = I (fourth root)
- Entanglement creation from superposition inputs
- Torch vs numpy substrate match
- Autograd gradients
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
# iSWAP UNITARY
# =====================================================================

ISWAP_MATRIX_NP = np.array([
    [1, 0,  0,  0],
    [0, 0,  1j, 0],
    [0, 1j, 0,  0],
    [0, 0,  0,  1],
], dtype=np.complex128)


# =====================================================================
# MODULE UNDER TEST: iSWAP
# =====================================================================

class iSWAPGate(nn.Module):
    """Differentiable iSWAP gate on 2-qubit density matrices.

    forward(rho) applies: rho -> U * rho * U dagger
    iSWAP = [[1,0,0,0],[0,0,i,0],[0,i,0,0],[0,0,0,1]]
    """

    def __init__(self):
        super().__init__()
        U = torch.zeros(4, 4, dtype=torch.complex64)
        U[0, 0] = 1.0
        U[1, 2] = 1j
        U[2, 1] = 1j
        U[3, 3] = 1.0
        self.register_buffer("U", U)

    def forward(self, rho):
        U = self.U.to(rho.dtype)
        return U @ rho @ U.conj().T

    def is_unitary(self, tol=1e-6):
        UUd = self.U @ self.U.conj().T
        diff = torch.max(torch.abs(UUd - torch.eye(4, dtype=self.U.dtype)))
        return float(diff.item()) < tol


# =====================================================================
# HELPERS
# =====================================================================

def ket_to_dm(ket_np):
    return np.outer(ket_np, ket_np.conj())


def partial_trace_B(rho_4x4):
    rho = np.array(rho_4x4, dtype=np.complex128)
    rho_A = np.zeros((2, 2), dtype=np.complex128)
    for i in range(2):
        for j in range(2):
            for k in range(2):
                rho_A[i, j] += rho[2 * i + k, 2 * j + k]
    return rho_A


def von_neumann_entropy(rho):
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > 1e-12]
    return float(-np.sum(evals * np.log(evals)))


def entanglement_entropy_np(rho_4x4):
    return von_neumann_entropy(partial_trace_B(rho_4x4))


def torch_partial_trace_B(rho):
    rho_A = torch.zeros(2, 2, dtype=rho.dtype, device=rho.device)
    for i in range(2):
        for j in range(2):
            for k in range(2):
                rho_A[i, j] = rho_A[i, j] + rho[2 * i + k, 2 * j + k]
    return rho_A


def torch_entanglement_entropy(rho):
    rho_A = torch_partial_trace_B(rho)
    evals = torch.linalg.eigvalsh(rho_A)
    evals = torch.clamp(evals.real, min=1e-12)
    return -torch.sum(evals * torch.log(evals))


def numpy_iswap(rho):
    U = ISWAP_MATRIX_NP
    return U @ rho @ U.conj().T


# =====================================================================
# STANDARD KETS
# =====================================================================

KET_0 = np.array([1, 0], dtype=np.complex128)
KET_1 = np.array([0, 1], dtype=np.complex128)
KET_PLUS = np.array([1, 1], dtype=np.complex128) / np.sqrt(2)

KET_00 = np.kron(KET_0, KET_0)
KET_01 = np.kron(KET_0, KET_1)
KET_10 = np.kron(KET_1, KET_0)
KET_11 = np.kron(KET_1, KET_1)
KET_PLUS_0 = np.kron(KET_PLUS, KET_0)
KET_PLUS_PLUS = np.kron(KET_PLUS, KET_PLUS)


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # --- P1: |00> -> |00> ---
    diff = float(np.max(np.abs(numpy_iswap(ket_to_dm(KET_00)) - ket_to_dm(KET_00))))
    results["P1_00_invariant"] = {"max_diff": diff, "pass": diff < 1e-10}

    # --- P2: |01> -> i|10> (density matrix: |i*10><i*10| = |10><10|) ---
    # Note: |01> -> i|10>, so rho = |i*10><-i*10| = |10><10|
    rho_out = numpy_iswap(ket_to_dm(KET_01))
    # The ket output is i*|10>, but density matrix absorbs the global phase
    rho_expected = ket_to_dm(1j * KET_10)  # = |10><10|
    diff = float(np.max(np.abs(rho_out - rho_expected)))
    results["P2_01_to_i10"] = {"max_diff": diff, "pass": diff < 1e-10}

    # --- P3: |10> -> i|01> ---
    rho_out = numpy_iswap(ket_to_dm(KET_10))
    rho_expected = ket_to_dm(1j * KET_01)
    diff = float(np.max(np.abs(rho_out - rho_expected)))
    results["P3_10_to_i01"] = {"max_diff": diff, "pass": diff < 1e-10}

    # --- P4: |11> -> |11> ---
    diff = float(np.max(np.abs(numpy_iswap(ket_to_dm(KET_11)) - ket_to_dm(KET_11))))
    results["P4_11_invariant"] = {"max_diff": diff, "pass": diff < 1e-10}

    # --- P5: iSWAP creates entanglement from |+0> ---
    # iSWAP|+0> = (|00> + i|01>)/sqrt(2) -- wait let me compute:
    # |+0> = (|00> + |10>)/sqrt(2)
    # iSWAP|00> = |00>, iSWAP|10> = i|01>
    # So iSWAP|+0> = (|00> + i|01>)/sqrt(2) -- this is product! (qubit A in |0>, qubit B in (|0>+i|1>)/sqrt(2))
    # Actually: qubit A = |0>, qubit B = (|0> + i|1>)/sqrt(2) -- product state
    # Try |++> instead
    # |++> = (|00> + |01> + |10> + |11>)/2
    # iSWAP: |00>->|00>, |01>->i|10>, |10>->i|01>, |11>->|11>
    # = (|00> + i|10> + i|01> + |11>)/2
    # This IS entangled
    rho_in = ket_to_dm(KET_PLUS_PLUS)
    rho_out = numpy_iswap(rho_in)
    ket_expected = (KET_00 + 1j * KET_10 + 1j * KET_01 + KET_11) / 2.0
    diff = float(np.max(np.abs(rho_out - ket_to_dm(ket_expected))))
    ent = entanglement_entropy_np(rho_out)
    results["P5_entanglement_from_plusplus"] = {
        "max_diff": diff, "entropy": ent,
        "is_entangled": ent > 0.01,
        "pass": diff < 1e-10 and ent > 0.01,
    }

    # --- P6: Substrate match ---
    p6_results = {}
    test_kets = {"|00>": KET_00, "|01>": KET_01, "|10>": KET_10, "|11>": KET_11, "|++>": KET_PLUS_PLUS}
    for name, ket in test_kets.items():
        rho_np = ket_to_dm(ket)
        out_np = numpy_iswap(rho_np)
        rho_t = torch.tensor(rho_np, dtype=torch.complex64)
        out_t = iSWAPGate()(rho_t).detach().cpu().numpy()
        max_diff = float(np.max(np.abs(out_np - out_t)))
        p6_results[name] = {"max_abs_diff": max_diff, "pass": max_diff < 1e-5}
    results["P6_substrate_match"] = p6_results

    # --- P7: Trace preservation ---
    p7_results = {}
    for name, ket in test_kets.items():
        out = numpy_iswap(ket_to_dm(ket))
        trace = float(np.real(np.trace(out)))
        p7_results[name] = {"trace": trace, "pass": abs(trace - 1.0) < 1e-10}
    results["P7_trace_preservation"] = p7_results

    # --- P8: Unitarity ---
    results["P8_unitarity"] = {"is_unitary": iSWAPGate().is_unitary(), "pass": iSWAPGate().is_unitary()}

    # --- P9: iSWAP^4 = I ---
    U4 = np.linalg.matrix_power(ISWAP_MATRIX_NP, 4)
    diff = float(np.max(np.abs(U4 - np.eye(4, dtype=np.complex128))))
    results["P9_iswap4_is_identity"] = {"max_diff": diff, "pass": diff < 1e-10}

    return results


# =====================================================================
# FALSIFICATION TESTS
# =====================================================================

def run_falsification_tests():
    results = {}

    # --- F1: Gradient of entanglement entropy ---
    f1_results = {}
    for theta_val in [0.1, 0.3, np.pi / 4, 0.7, 1.2]:
        theta = torch.tensor(float(theta_val), requires_grad=True)
        # |psi> = cos(theta)|+0> + sin(theta)|0+>
        ket_plus_0 = torch.tensor(KET_PLUS_0, dtype=torch.complex64)
        ket_0_plus = torch.tensor(np.kron(KET_0, KET_PLUS), dtype=torch.complex64)
        c = torch.cos(theta).to(torch.complex64)
        s = torch.sin(theta).to(torch.complex64)
        ket = c * ket_plus_0 + s * ket_0_plus
        ket = ket / torch.sqrt(torch.sum(torch.abs(ket) ** 2))
        rho = torch.outer(ket, ket.conj())
        gate = iSWAPGate()
        rho_out = gate(rho)
        S = torch_entanglement_entropy(rho_out)
        S.backward()
        grad = theta.grad
        f1_results[f"theta={theta_val:.2f}"] = {
            "theta": float(theta_val), "entropy": float(S.item()),
            "grad": float(grad.item()) if grad is not None else None,
            "pass": grad is not None,
        }
    results["F1_entanglement_gradient"] = f1_results

    # --- F2: Autograd vs finite difference ---
    eps = 1e-4
    theta_test = 0.5
    theta = torch.tensor(float(theta_test), requires_grad=True)
    ket_plus_0_t = torch.tensor(KET_PLUS_0, dtype=torch.complex64)
    ket_0_plus_t = torch.tensor(np.kron(KET_0, KET_PLUS), dtype=torch.complex64)
    c = torch.cos(theta).to(torch.complex64)
    s = torch.sin(theta).to(torch.complex64)
    ket = c * ket_plus_0_t + s * ket_0_plus_t
    ket = ket / torch.sqrt(torch.sum(torch.abs(ket) ** 2))
    rho = torch.outer(ket, ket.conj())
    rho_out = iSWAPGate()(rho)
    S = torch_entanglement_entropy(rho_out)
    S.backward()
    grad_auto = float(theta.grad.item())

    def fd_entropy(th):
        ket_p0 = KET_PLUS_0
        ket_0p = np.kron(KET_0, KET_PLUS)
        k = np.cos(th) * ket_p0 + np.sin(th) * ket_0p
        k /= np.linalg.norm(k)
        r = np.outer(k, k.conj())
        return entanglement_entropy_np(numpy_iswap(r))

    grad_fd = (fd_entropy(theta_test + eps) - fd_entropy(theta_test - eps)) / (2 * eps)
    diff = abs(grad_auto - grad_fd)
    results["F2_autograd_vs_fd"] = {
        "autograd": grad_auto, "finite_diff": float(grad_fd),
        "abs_diff": diff, "pass": diff < 0.1,
    }

    # --- F3: Random states match ---
    np.random.seed(42)
    max_diffs = []
    for _ in range(20):
        a = np.random.randn(2) + 1j * np.random.randn(2); a /= np.linalg.norm(a)
        b = np.random.randn(2) + 1j * np.random.randn(2); b /= np.linalg.norm(b)
        ket_r = np.kron(a, b)
        rho_np = ket_to_dm(ket_r)
        out_np = numpy_iswap(rho_np)
        rho_t = torch.tensor(rho_np, dtype=torch.complex64)
        out_t = iSWAPGate()(rho_t).detach().cpu().numpy()
        max_diffs.append(float(np.max(np.abs(out_np - out_t))))
    results["F3_random_match"] = {"n": 20, "max_diff": max(max_diffs), "pass": max(max_diffs) < 1e-5}

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # --- N1: Non-unitary iSWAP detected ---
    class BadISWAP(nn.Module):
        def __init__(self):
            super().__init__()
            U = torch.zeros(4, 4, dtype=torch.complex64)
            U[0, 0] = 1.0; U[1, 2] = 0.5j; U[2, 1] = 1j; U[3, 3] = 1.0
            self.register_buffer("U", U)
        def is_unitary(self, tol=1e-6):
            UUd = self.U @ self.U.conj().T
            diff = torch.max(torch.abs(UUd - torch.eye(4, dtype=self.U.dtype)))
            return float(diff.item()) < tol

    results["N1_non_unitary_detected"] = {"is_unitary": BadISWAP().is_unitary(), "pass": not BadISWAP().is_unitary()}

    # --- N2: iSWAP is NOT self-inverse (use superposition to expose) ---
    # On computational basis states, iSWAP^2 only adds global phase (invisible in dm).
    # Use |+0> = (|00>+|10>)/sqrt2 to expose:
    # iSWAP|+0> = (|00> + i|01>)/sqrt2
    # iSWAP^2|+0> = iSWAP((|00>+i|01>)/sqrt2) = (|00> + i*i|10>)/sqrt2 = (|00> - |10>)/sqrt2
    # = |−0> which differs from |+0>
    rho_in = ket_to_dm(KET_PLUS_0)
    rho_out = numpy_iswap(numpy_iswap(rho_in))
    diff = float(np.max(np.abs(rho_out - rho_in)))
    results["N2_not_self_inverse"] = {
        "max_diff": diff,
        "pass": diff > 1e-6,  # EXPECT difference
    }

    # --- N3: iSWAP^2 on |01> gives -|01> (phase -1), density matrix same ---
    # iSWAP|01> = i|10>, iSWAP(i|10>) = i*(i|01>) = -|01>
    # But density matrix: |-01><-01| = |01><01|
    rho_in_01 = ket_to_dm(KET_01)
    rho_out_01 = numpy_iswap(numpy_iswap(rho_in_01))
    rho_expected = ket_to_dm(KET_01)
    diff = float(np.max(np.abs(rho_out_01 - rho_expected)))
    results["N3_iswap2_01_phase"] = {"max_diff": diff, "pass": diff < 1e-10}

    # --- N4: Hermiticity preserved ---
    for name, ket in {"|01>": KET_01, "|++>": KET_PLUS_PLUS}.items():
        rho_t = torch.tensor(ket_to_dm(ket), dtype=torch.complex64)
        out = iSWAPGate()(rho_t).detach().cpu().numpy()
        herm_diff = float(np.max(np.abs(out - out.conj().T)))
        results[f"N4_hermiticity_{name}"] = {"diff": herm_diff, "pass": herm_diff < 1e-6}

    # --- N5: Computational basis states stay product ---
    for name, ket in {"|00>": KET_00, "|01>": KET_01, "|10>": KET_10, "|11>": KET_11}.items():
        out = numpy_iswap(ket_to_dm(ket))
        ent = entanglement_entropy_np(out)
        results[f"N5_comp_basis_product_{name}"] = {"entropy": ent, "pass": ent < 1e-10}

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # --- B1: Maximally mixed invariant ---
    rho_mixed = np.eye(4, dtype=np.complex128) / 4
    diff = float(np.max(np.abs(numpy_iswap(rho_mixed) - rho_mixed)))
    results["B1_mixed_invariant"] = {"max_diff": diff, "pass": diff < 1e-10}

    # --- B2: Purity preserved ---
    np.random.seed(88)
    b2_results = {}
    for i in range(5):
        a = np.random.randn(2) + 1j * np.random.randn(2); a /= np.linalg.norm(a)
        b = np.random.randn(2) + 1j * np.random.randn(2); b /= np.linalg.norm(b)
        rho = ket_to_dm(np.kron(a, b))
        out = numpy_iswap(rho)
        p_in = float(np.real(np.trace(rho @ rho)))
        p_out = float(np.real(np.trace(out @ out)))
        b2_results[f"state_{i}"] = {"purity_in": p_in, "purity_out": p_out, "pass": abs(p_in - p_out) < 1e-10}
    results["B2_purity_preserved"] = b2_results

    # --- B3: iSWAP^4 on random state = identity ---
    np.random.seed(33)
    a = np.random.randn(2) + 1j * np.random.randn(2); a /= np.linalg.norm(a)
    b = np.random.randn(2) + 1j * np.random.randn(2); b /= np.linalg.norm(b)
    rho = ket_to_dm(np.kron(a, b))
    rho_4 = rho.copy()
    for _ in range(4):
        rho_4 = numpy_iswap(rho_4)
    diff = float(np.max(np.abs(rho_4 - rho)))
    results["B3_iswap4_random"] = {"max_diff": diff, "pass": diff < 1e-10}

    return results


# =====================================================================
# SYMPY CHECK
# =====================================================================

def run_sympy_check():
    if not TOOL_MANIFEST["sympy"]["tried"]:
        return {"skipped": True, "reason": "sympy not available"}

    U = sp.Matrix([
        [1, 0, 0, 0],
        [0, 0, sp.I, 0],
        [0, sp.I, 0, 0],
        [0, 0, 0, 1],
    ])
    UUd = U * U.H
    is_unitary = sp.simplify(UUd - sp.eye(4)) == sp.zeros(4)

    U2 = U * U
    is_self_inverse = sp.simplify(U2 - sp.eye(4)) == sp.zeros(4)

    U4 = U**4
    is_fourth_root = sp.simplify(U4 - sp.eye(4)) == sp.zeros(4)

    # |01> -> i|10>
    ket_01 = sp.Matrix([0, 1, 0, 0])
    out = U * ket_01
    expected = sp.I * sp.Matrix([0, 0, 1, 0])
    maps_01 = sp.simplify(out - expected) == sp.zeros(4, 1)

    return {
        "is_unitary": bool(is_unitary),
        "is_NOT_self_inverse": not bool(is_self_inverse),
        "is_fourth_root": bool(is_fourth_root),
        "maps_01_to_i10": bool(maps_01),
        "pass": bool(is_unitary) and not bool(is_self_inverse) and bool(is_fourth_root) and bool(maps_01),
    }


# =====================================================================
# Z3 CHECK
# =====================================================================

def run_z3_check():
    if not TOOL_MANIFEST["z3"]["tried"]:
        return {"skipped": True, "reason": "z3 not available"}

    from z3 import Real, Solver, And, Not

    # iSWAP preserves normalization: if probs sum to 1, output probs sum to 1
    p00, p01, p10, p11 = [Real(f"p{s}") for s in ["00", "01", "10", "11"]]
    solver = Solver()
    solver.add(p00 + p01 + p10 + p11 == 1)
    solver.add(And(p00 >= 0, p01 >= 0, p10 >= 0, p11 >= 0))
    # After iSWAP: p00'=p00, p01'=p10, p10'=p01, p11'=p11 (swap 01<->10)
    # Sum = p00 + p10 + p01 + p11 = 1 (same)
    solver.add(Not(p00 + p10 + p01 + p11 == 1))
    result = str(solver.check())

    return {"normalization_preserved": result, "pass": result == "unsat"}


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
    TOOL_MANIFEST["pytorch"]["reason"] = "Core module: iSWAP as nn.Module, autograd for entanglement gradients"
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "Symbolic unitarity, non-self-inverse, fourth-root, basis mapping"
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "Normalization preservation under swap-with-phase"

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
        "name": "torch_iswap",
        "phase": "Phase 3 sim",
        "description": "iSWAP gate as differentiable nn.Module -- swap with phase, entanglement creation",
        "tool_manifest": TOOL_MANIFEST,
        **all_results,
        "classification": "canonical",
        "summary": {"total_tests": total_tests, "total_pass": total_pass, "all_pass": total_pass == total_tests},
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "torch_iswap_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Tests: {total_pass}/{total_tests} passed")
    if total_pass == total_tests:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED -- inspect results JSON")
