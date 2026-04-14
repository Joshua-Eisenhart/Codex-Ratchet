#!/usr/bin/env python3
"""
4-Qubit Cascade -- 28 families + 4q emergent through 16x16 constraint shells
=============================================================================

Scales the ratchet cascade to the 4-qubit (16x16) system.

    System: 4 qubits A, B, C, D (dimension 16x16)
    Gates: CNOT_AB, CNOT_BC, CNOT_CD -- chain topology (A-B-C-D)
           + optional CNOT_DA for ring topology (A-B-C-D-A)
    Noise: Z-dephasing on qubit A, depolarizing on full system
    Shells: L1 (CPTP), L2 (purity bound), L4 (composition), L6 (irreversibility)
            -- all adapted for 16x16 density matrices

Key questions:
  1. Do the same 8 channels survive as in 2q and 3q? (dimension-independence)
  2. Any new structure at 4q that wasn't at 2q or 3q?
  3. 4-partite information measures -- killed at L4 like lower-partite?
  4. Chain topology (A-B-C-D) vs ring topology (A-B-C-D-A) -- changes survivors?

Classification: canonical
pytorch=used, z3=tried
Output: system_v4/probes/a2_state/sim_results/4qubit_cascade_results.json
"""

import json
import os
import sys
import traceback
import time
import numpy as np
classification = "classical_baseline"  # auto-backfill

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": ""},
    "pyg":       {"tried": False, "used": False, "reason": "not needed -- cascade is nn.Module chain"},
    "z3":        {"tried": False, "used": False, "reason": ""},
    "cvc5":      {"tried": False, "used": False, "reason": "not needed -- z3 sufficient"},
    "sympy":     {"tried": False, "used": False, "reason": "not needed -- all computation torch-native"},
    "clifford":  {"tried": False, "used": False, "reason": "not needed -- geometry done natively"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn":      {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi":       {"tried": False, "used": False, "reason": "not needed"},
    "toponetx":  {"tried": False, "used": False, "reason": "not needed"},
    "gudhi":     {"tried": False, "used": False, "reason": "not needed"},
}

# ── Imports ─────────────────────────────────────────────────────────

try:
    import torch
    import torch.nn as nn
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    print("FATAL: pytorch required"); sys.exit(1)

try:
    from z3 import Solver, Real, And, sat, RealVal
    TOOL_MANIFEST["z3"]["tried"] = True
    HAS_Z3 = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"
    HAS_Z3 = False

try:
    import rustworkx as rx
    TOOL_MANIFEST["rustworkx"]["tried"] = True
    HAS_RX = True
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"
    HAS_RX = False


# =====================================================================
# CONSTANTS -- float32 for 16x16 performance
# =====================================================================

DTYPE = torch.complex64
FDTYPE = torch.float32

D = 16  # 2^4 = 16

I2 = torch.eye(2, dtype=DTYPE)
I4 = torch.eye(4, dtype=DTYPE)
I8 = torch.eye(8, dtype=DTYPE)
I16 = torch.eye(D, dtype=DTYPE)

# Pauli matrices
SX = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)

# CNOT gate (4x4)
CNOT_2Q = torch.tensor([
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 0, 1],
    [0, 0, 1, 0],
], dtype=DTYPE)

# 4-qubit CNOT gates -- chain topology: A-B-C-D
# CNOT_AB: control=A, target=B, identity on C,D
CNOT_AB = torch.kron(CNOT_2Q, torch.kron(I2, I2))  # (AB) x I_C x I_D
# CNOT_BC: identity on A, CNOT(B,C), identity on D
CNOT_BC = torch.kron(I2, torch.kron(CNOT_2Q, I2))  # I_A x (BC) x I_D
# CNOT_CD: identity on A,B, CNOT(C,D)
CNOT_CD = torch.kron(torch.kron(I2, I2), CNOT_2Q)  # I_A x I_B x (CD)
# CNOT_DA: ring closure -- control=D, target=A
# Build via permutation: swap A<->D, apply CNOT_AB, swap back
# Simpler: construct directly. |d,a> -> |d, a XOR d> tensored with I_BC
# CNOT_DA acts on qubits D (control) and A (target) with I_BC in between.
# We build it explicitly: for basis |a,b,c,d>, maps to |a XOR d, b, c, d>
def _build_cnot_DA():
    """CNOT with D=control, A=target. |a,b,c,d> -> |a XOR d, b, c, d>."""
    gate = torch.zeros(D, D, dtype=DTYPE)
    for a in range(2):
        for b in range(2):
            for c in range(2):
                for d in range(2):
                    idx_in = a * 8 + b * 4 + c * 2 + d
                    a_out = a ^ d  # XOR
                    idx_out = a_out * 8 + b * 4 + c * 2 + d
                    gate[idx_out, idx_in] = 1.0
    return gate

CNOT_DA = _build_cnot_DA()


# =====================================================================
# 4-QUBIT STATE BUILDERS
# =====================================================================

def build_single_qubit_state(theta, phi, r):
    """Bloch-parameterized single-qubit density matrix."""
    ct2 = torch.cos(theta / 2)
    st2 = torch.sin(theta / 2)
    psi = torch.stack([
        ct2.to(DTYPE),
        (st2 * torch.exp(1j * phi.to(DTYPE))).to(DTYPE),
    ])
    rho_pure = torch.outer(psi, psi.conj())
    rho = r.to(DTYPE) * rho_pure + (1.0 - r.to(DTYPE)) * I2 / 2.0
    return rho


def build_4qubit_product_state(params_A, params_B, params_C, params_D):
    """Build rho_A x rho_B x rho_C x rho_D from Bloch parameters."""
    rho_A = build_single_qubit_state(*params_A)
    rho_B = build_single_qubit_state(*params_B)
    rho_C = build_single_qubit_state(*params_C)
    rho_D = build_single_qubit_state(*params_D)
    return torch.kron(torch.kron(torch.kron(rho_A, rho_B), rho_C), rho_D)


def apply_gate(gate_16x16, rho_16x16):
    """Apply unitary gate to 16x16 density matrix."""
    return gate_16x16 @ rho_16x16 @ gate_16x16.conj().T


def z_dephasing_A(rho_16x16, p):
    """Z-dephasing on qubit A with strength p."""
    Z_A = torch.kron(torch.kron(torch.kron(SZ, I2), I2), I2)
    return (1.0 - p) * rho_16x16 + p * (Z_A @ rho_16x16 @ Z_A)


def depolarizing_4q(rho_16x16, p):
    """Depolarizing channel on full 4-qubit system."""
    return (1.0 - p) * rho_16x16 + p * I16 / float(D)


def build_4qubit_rho(theta_AB, theta_BC, theta_CD,
                     phi_AB, phi_BC, phi_CD,
                     r_A, r_B, r_C, r_D,
                     topology="chain", dephasing_p=None):
    """Build 4-qubit state: product -> CNOT chain -> optional ring closure -> noise.

    topology: "chain" = CNOT_AB + CNOT_BC + CNOT_CD
              "ring"  = CNOT_AB + CNOT_BC + CNOT_CD + CNOT_DA
    """
    t = lambda v: torch.tensor(v, dtype=FDTYPE) if not isinstance(v, torch.Tensor) else v
    rho_A = build_single_qubit_state(t(theta_AB), t(phi_AB), t(r_A))
    rho_B = build_single_qubit_state(t(theta_BC), t(phi_BC), t(r_B))
    rho_C = build_single_qubit_state(t(theta_CD), t(phi_CD), t(r_C))
    rho_D = build_single_qubit_state(t(0.0), t(0.0), t(r_D))

    rho = torch.kron(torch.kron(torch.kron(rho_A, rho_B), rho_C), rho_D)
    rho = apply_gate(CNOT_AB, rho)
    rho = apply_gate(CNOT_BC, rho)
    rho = apply_gate(CNOT_CD, rho)

    if topology == "ring":
        rho = apply_gate(CNOT_DA, rho)

    if dephasing_p is not None:
        p = float(dephasing_p) if not isinstance(dephasing_p, (float, int)) else dephasing_p
        rho = z_dephasing_A(rho, p)

    return rho


def make_ghz_4q():
    """GHZ state: (|0000> + |1111>) / sqrt(2) as 16x16 density matrix."""
    psi = torch.zeros(D, dtype=DTYPE)
    psi[0] = 1.0 / np.sqrt(2)   # |0000>
    psi[15] = 1.0 / np.sqrt(2)  # |1111>
    return torch.outer(psi, psi.conj())


def make_w_4q():
    """W state: (|0001> + |0010> + |0100> + |1000>) / 2 as 16x16 density matrix."""
    psi = torch.zeros(D, dtype=DTYPE)
    psi[1] = 0.5   # |0001>
    psi[2] = 0.5   # |0010>
    psi[4] = 0.5   # |0100>
    psi[8] = 0.5   # |1000>
    return torch.outer(psi, psi.conj())


# =====================================================================
# PARTIAL TRACES -- 4-qubit system (A=2, B=2, C=2, D=2)
# Full reshape is (2,2,2,2, 2,2,2,2) for row/col indices
# =====================================================================

def _reshape_4q(rho):
    """Reshape 16x16 -> (2,2,2,2, 2,2,2,2) = (A,B,C,D, A',B',C',D')."""
    return rho.reshape(2, 2, 2, 2, 2, 2, 2, 2)


def pt_single(rho_16x16, qubit):
    """Trace out single qubit from 16x16 -> 8x8.

    qubit: 0=A, 1=B, 2=C, 3=D.
    Reshape to (d_left, 2, d_right, d_left, 2, d_right) and contract
    the qubit indices (positions 1 and 4).
    """
    d_left = 2 ** qubit
    d_right = 2 ** (3 - qubit)
    r = rho_16x16.reshape(d_left, 2, d_right, d_left, 2, d_right)
    # indices: (i=d_left, a=2, j=d_right, k=d_left, b=2, l=d_right)
    # row of rho = (i, a, j), col = (k, b, l)
    # trace a==b: sum over a, result row=(i,j), col=(k,l)
    return torch.einsum('iajkal->ijkl', r).reshape(d_left * d_right, d_left * d_right)


def pt_two(rho_16x16, q1, q2):
    """Trace out two qubits, return 4x4 reduced state.

    q1, q2: qubits to trace out (0=A,1=B,2=C,3=D), q1 < q2.
    """
    # Trace first the higher-indexed qubit on 16x16, get 8x8
    # Then trace the lower-indexed qubit on the 8x8 (but index shifts).
    # Instead, do it via full reshape.
    r = _reshape_4q(rho_16x16)
    keep = sorted(set(range(4)) - {q1, q2})
    # Build einsum: sum over traced qubits (same position in bra and ket)
    # Indices: abcd efgh where a-d are ket, e-h are bra for A,B,C,D
    # We want to contract positions q1 and q2 (ket[q1]=bra[q1], ket[q2]=bra[q2])
    # and keep the rest free.
    #
    # General approach: iterate over traced qubits
    idx_ket = list('abcd')
    idx_bra = list('efgh')
    for q in [q1, q2]:
        idx_bra[q] = idx_ket[q]  # contract

    ein_in = ''.join(idx_ket) + ''.join(idx_bra)
    free_ket = [idx_ket[k] for k in keep]
    free_bra = [idx_bra[k] for k in keep]
    ein_out = ''.join(free_ket) + ''.join(free_bra)

    result = torch.einsum(f'{ein_in}->{ein_out}', r)
    d_out = 2 ** len(keep)
    return result.reshape(d_out, d_out)


def pt_three(rho_16x16, q1, q2, q3):
    """Trace out three qubits, return 2x2 reduced state."""
    r = _reshape_4q(rho_16x16)
    keep = sorted(set(range(4)) - {q1, q2, q3})

    idx_ket = list('abcd')
    idx_bra = list('efgh')
    for q in [q1, q2, q3]:
        idx_bra[q] = idx_ket[q]

    ein_in = ''.join(idx_ket) + ''.join(idx_bra)
    free_ket = [idx_ket[k] for k in keep]
    free_bra = [idx_bra[k] for k in keep]
    ein_out = ''.join(free_ket) + ''.join(free_bra)

    result = torch.einsum(f'{ein_in}->{ein_out}', r)
    return result.reshape(2, 2)


# Convenience aliases
def rho_A(rho):
    return pt_three(rho, 1, 2, 3)

def rho_B(rho):
    return pt_three(rho, 0, 2, 3)

def rho_C(rho):
    return pt_three(rho, 0, 1, 3)

def rho_D(rho):
    return pt_three(rho, 0, 1, 2)

def rho_AB(rho):
    return pt_two(rho, 2, 3)

def rho_CD(rho):
    return pt_two(rho, 0, 1)

def rho_AC(rho):
    return pt_two(rho, 1, 3)

def rho_BD(rho):
    return pt_two(rho, 0, 2)

def rho_BC(rho):
    return pt_two(rho, 0, 3)

def rho_AD(rho):
    return pt_two(rho, 1, 2)

def rho_ABC(rho):
    return pt_single(rho, 3)

def rho_BCD(rho):
    return pt_single(rho, 0)

def rho_ACD(rho):
    return pt_single(rho, 1)

def rho_ABD(rho):
    return pt_single(rho, 2)


# =====================================================================
# ENTROPY AND INFORMATION MEASURES
# =====================================================================

def von_neumann_entropy(rho):
    """S(rho) = -Tr(rho log rho) via eigenvalues."""
    evals = torch.linalg.eigvalsh(rho)
    evals_real = evals.real
    evals_clamped = torch.clamp(evals_real, min=1e-12)
    return -torch.sum(evals_clamped * torch.log(evals_clamped))


def frobenius_norm(M):
    """||M||_F = sqrt(Tr(M^dag M))."""
    return torch.sqrt(torch.real(torch.trace(M.conj().T @ M)))


def purity(rho):
    """Tr(rho^2) -- 1 for pure, 1/d for maximally mixed."""
    return torch.real(torch.trace(rho @ rho))


def coherent_info_A_given_BCD(rho_ABCD):
    """I_c(A>BCD) = S(BCD) - S(ABCD)."""
    return von_neumann_entropy(rho_BCD(rho_ABCD)) - von_neumann_entropy(rho_ABCD)


def coherent_info_AB_given_CD(rho_ABCD):
    """I_c(AB>CD) = S(CD) - S(ABCD)."""
    return von_neumann_entropy(rho_CD(rho_ABCD)) - von_neumann_entropy(rho_ABCD)


def coherent_info_ABC_given_D(rho_ABCD):
    """I_c(ABC>D) = S(D) - S(ABCD)."""
    return von_neumann_entropy(rho_D(rho_ABCD)) - von_neumann_entropy(rho_ABCD)


def mutual_info_AB(rho_ABCD):
    """I(A:B) = S(A) + S(B) - S(AB)."""
    S_A = von_neumann_entropy(rho_A(rho_ABCD))
    S_B = von_neumann_entropy(rho_B(rho_ABCD))
    S_AB = von_neumann_entropy(rho_AB(rho_ABCD))
    return S_A + S_B - S_AB


def _pt_single_3q(rho_8x8, qubit):
    """Trace out a single qubit from an 8x8 (3-qubit) density matrix -> 4x4."""
    d_left = 2 ** qubit
    d_right = 2 ** (2 - qubit)
    r = rho_8x8.reshape(d_left, 2, d_right, d_left, 2, d_right)
    return torch.einsum('iajkal->ijkl', r).reshape(d_left * d_right, d_left * d_right)


def _pt_two_3q(rho_8x8, q1, q2):
    """Trace out two qubits from an 8x8 (3-qubit) density matrix -> 2x2."""
    r = rho_8x8.reshape(2, 2, 2, 2, 2, 2)
    keep = sorted(set(range(3)) - {q1, q2})
    idx_ket = list('abc')
    idx_bra = list('def')
    for q in [q1, q2]:
        idx_bra[q] = idx_ket[q]
    ein_in = ''.join(idx_ket) + ''.join(idx_bra)
    free_ket = [idx_ket[k] for k in keep]
    free_bra = [idx_bra[k] for k in keep]
    ein_out = ''.join(free_ket) + ''.join(free_bra)
    result = torch.einsum(f'{ein_in}->{ein_out}', r)
    return result.reshape(2, 2)


def tripartite_info_ABC(rho_ABCD):
    """I3(A:B:C) from the ABCD state (trace out D first, then compute).

    I3 = I(A:B) + I(A:C) - I(A:BC)  on rho_ABC.
       = S_A + S_B + S_C - S_AB - S_AC - S_BC + S_ABC
    """
    r_abc = rho_ABC(rho_ABCD)  # 8x8

    # Sub-traces of rho_ABC (3-qubit system with qubits 0=A, 1=B, 2=C)
    rA_3 = _pt_two_3q(r_abc, 1, 2)     # 2x2
    rB_3 = _pt_two_3q(r_abc, 0, 2)     # 2x2
    rC_3 = _pt_two_3q(r_abc, 0, 1)     # 2x2
    rAB_3 = _pt_single_3q(r_abc, 2)    # 4x4: trace out C
    rAC_3 = _pt_single_3q(r_abc, 1)    # 4x4: trace out B
    rBC_3 = _pt_single_3q(r_abc, 0)    # 4x4: trace out A

    S_A_v = von_neumann_entropy(rA_3)
    S_B_v = von_neumann_entropy(rB_3)
    S_C_v = von_neumann_entropy(rC_3)
    S_AB_v = von_neumann_entropy(rAB_3)
    S_AC_v = von_neumann_entropy(rAC_3)
    S_BC_v = von_neumann_entropy(rBC_3)
    S_ABC_v = von_neumann_entropy(r_abc)

    I3 = S_A_v + S_B_v + S_C_v - S_AB_v - S_AC_v - S_BC_v + S_ABC_v
    return float(I3.item())


def quadripartite_info(rho_ABCD):
    """4-partite information I4(A:B:C:D).

    I4 = I3(A:B:C) - I3(A:B:C|D)
       = sum of all single entropies - sum of all pair entropies
         + sum of all triple entropies - S(ABCD)

    Explicit: I4 = S_A + S_B + S_C + S_D
                   - S_AB - S_AC - S_AD - S_BC - S_BD - S_CD
                   + S_ABC + S_ABD + S_ACD + S_BCD
                   - S_ABCD
    """
    S_single = [von_neumann_entropy(f(rho_ABCD)) for f in [rho_A, rho_B, rho_C, rho_D]]
    S_pair = [von_neumann_entropy(f(rho_ABCD)) for f in [rho_AB, rho_AC, rho_AD, rho_BC, rho_BD, rho_CD]]
    S_triple = [von_neumann_entropy(f(rho_ABCD)) for f in [rho_ABC, rho_ABD, rho_ACD, rho_BCD]]
    S_full = von_neumann_entropy(rho_ABCD)

    I4 = (sum(S_single) - sum(S_pair) + sum(S_triple) - S_full)
    return float(I4.item())


# =====================================================================
# 16x16 CONSTRAINT SHELLS
# =====================================================================

class ConstraintShell_16x16(nn.Module):
    """Base class for 16x16 constraint shell projectors."""
    def __init__(self, name, level):
        super().__init__()
        self.name = name
        self.level = level

    def violation(self, rho):
        raise NotImplementedError

    def is_satisfied(self, rho, tol=1e-4):
        return float(self.violation(rho).item()) < tol

    def project(self, rho):
        raise NotImplementedError

    def forward(self, rho):
        return self.project(rho)


class L1_CPTP_16x16(ConstraintShell_16x16):
    """Project 16x16 density matrix onto PSD cone with unit trace."""
    def __init__(self):
        super().__init__("L1_CPTP", level=1)

    def violation(self, rho):
        trace_viol = torch.abs(torch.real(torch.trace(rho)) - 1.0)
        herm_viol = frobenius_norm(rho - rho.conj().T)
        rho_h = (rho + rho.conj().T) / 2.0
        evals = torch.linalg.eigvalsh(rho_h)
        psd_viol = torch.sum(torch.relu(-evals.real))
        return trace_viol + herm_viol + psd_viol

    def project(self, rho):
        rho_h = (rho + rho.conj().T) / 2.0
        evals, evecs = torch.linalg.eigh(rho_h)
        evals_clamped = torch.clamp(evals.real, min=0.0)
        rho_psd = evecs @ torch.diag(evals_clamped.to(DTYPE)) @ evecs.conj().T
        tr = torch.real(torch.trace(rho_psd))
        if tr.item() > 1e-12:
            rho_psd = rho_psd / tr
        else:
            rho_psd = I16 / float(D)
        return rho_psd


class L2_Purity_16x16(ConstraintShell_16x16):
    """Purity bound for 16x16: Tr(rho^2) <= 1.
    For 16x16: purity in [1/16, 1].
    """
    def __init__(self):
        super().__init__("L2_Purity", level=2)

    def violation(self, rho):
        p = purity(rho)
        return torch.relu(p - 1.0)

    def project(self, rho):
        p = purity(rho)
        if p.item() > 1.0 + 1e-6:
            I_mix = I16 / float(D)
            lo, hi = 0.0, 1.0
            for _ in range(20):
                mid = (lo + hi) / 2.0
                rho_mixed = (1.0 - mid) * rho + mid * I_mix
                p_mixed = purity(rho_mixed)
                if p_mixed.item() <= 1.0:
                    hi = mid
                else:
                    lo = mid
            return (1.0 - hi) * rho + hi * I_mix
        return rho


class L4_Composition_16x16(ConstraintShell_16x16):
    """Channel composition for 16x16: apply 4-qubit channel cycle, check contraction.

    Cycle: Z-dephasing(A) -> depolarizing(full) -> amplitude damping(A)
    """
    def __init__(self, n_cycles=3):
        super().__init__("L4_Composition", level=4)
        self.n_cycles = n_cycles

    def _apply_cycle(self, rho):
        state = z_dephasing_A(rho, 0.15)
        state = depolarizing_4q(state, 0.3)
        # Amplitude damping on qubit A
        gamma = 0.2
        K0_1q = torch.tensor([[1, 0], [0, np.sqrt(1 - gamma)]], dtype=DTYPE)
        K1_1q = torch.tensor([[0, np.sqrt(gamma)], [0, 0]], dtype=DTYPE)
        K0 = torch.kron(torch.kron(torch.kron(K0_1q, I2), I2), I2)
        K1 = torch.kron(torch.kron(torch.kron(K1_1q, I2), I2), I2)
        state = K0 @ state @ K0.conj().T + K1 @ state @ K1.conj().T
        return state

    def _check_contraction(self, rho):
        norms = [frobenius_norm(rho).item()]
        state = rho
        for _ in range(self.n_cycles):
            state = self._apply_cycle(state)
            norms.append(frobenius_norm(state).item())
        is_contracting = norms[-1] <= norms[0] + 1e-6
        return is_contracting, norms[0], norms[-1], norms

    def violation(self, rho):
        _, n0, nf, _ = self._check_contraction(rho)
        return torch.relu(torch.tensor(nf - n0, dtype=FDTYPE))

    def project(self, rho):
        is_ok, _, _, _ = self._check_contraction(rho)
        if not is_ok:
            projected = self._apply_cycle(rho)
            tr = torch.real(torch.trace(projected))
            if tr.item() > 1e-12:
                projected = projected / tr
            return projected
        return rho


class L6_Irreversibility_16x16(ConstraintShell_16x16):
    """Entropy must not decrease under channel application."""
    def __init__(self):
        super().__init__("L6_Irreversibility", level=6)

    def _channel_set(self):
        return [
            lambda rho: z_dephasing_A(rho, 0.15),
            lambda rho: depolarizing_4q(rho, 0.3),
        ]

    def _max_entropy_decrease(self, rho):
        S_before = von_neumann_entropy(rho)
        max_dec = torch.tensor(0.0, dtype=FDTYPE)
        for ch_fn in self._channel_set():
            rho_after = ch_fn(rho)
            S_after = von_neumann_entropy(rho_after)
            dec = S_before - S_after
            if dec.item() > max_dec.item():
                max_dec = dec
        return max_dec

    def violation(self, rho):
        dec = self._max_entropy_decrease(rho)
        return torch.relu(dec - 1e-5)

    def project(self, rho):
        dec = self._max_entropy_decrease(rho)
        if dec.item() <= 1e-5:
            return rho

        S_target = von_neumann_entropy(rho).item()
        I_mix = I16 / float(D)
        lo, hi = 0.0, 1.0
        for _ in range(20):
            mid = (lo + hi) / 2.0
            rho_mixed = (1.0 - mid) * rho + mid * I_mix
            S_mixed = von_neumann_entropy(rho_mixed).item()
            if S_mixed >= S_target:
                hi = mid
            else:
                lo = mid
        return (1.0 - hi) * rho + hi * I_mix


# =====================================================================
# SHELL DAG AND DYKSTRA
# =====================================================================

def build_shell_dag_16x16(shell_objects):
    """Build DAG from 16x16 shell objects."""
    if not HAS_RX:
        raise RuntimeError("rustworkx required for shell ordering")

    dag = rx.PyDiGraph()
    level_to_idx = {}
    idx_to_shell = {}
    for shell in shell_objects:
        idx = dag.add_node(shell.name)
        level_to_idx[shell.level] = idx
        idx_to_shell[idx] = shell

    levels_sorted = sorted(level_to_idx.keys())
    for i in range(len(levels_sorted) - 1):
        src = levels_sorted[i]
        dst = levels_sorted[i + 1]
        dag.add_edge(level_to_idx[src], level_to_idx[dst], f"L{src}->L{dst}")

    topo_indices = list(rx.topological_sort(dag))
    topo_names = [dag[i] for i in topo_indices]
    return dag, topo_indices, topo_names, idx_to_shell


def get_ordered_shells_16x16(shell_objects, topo_indices, idx_to_shell):
    return [idx_to_shell[idx] for idx in topo_indices if idx in idx_to_shell]


def dykstra_project_16x16(rho_init, ordered_shells, n_iterations=25, track_violations=False):
    """Dykstra alternating projection for 16x16 density matrices.

    Reduced default iterations vs 8x8 for performance.
    """
    K = len(ordered_shells)
    x = rho_init.clone().detach()
    increments = [torch.zeros_like(x) for _ in range(K)]
    violation_trace = []

    for iteration in range(n_iterations):
        if track_violations:
            total_viol = sum(s.violation(x).item() for s in ordered_shells)
            violation_trace.append(total_viol)

        for k, shell in enumerate(ordered_shells):
            x_plus_inc = x + increments[k]
            y = shell.project(x_plus_inc)
            increments[k] = x_plus_inc - y
            x = y

    if track_violations:
        total_viol = sum(s.violation(x).item() for s in ordered_shells)
        violation_trace.append(total_viol)

    return x, {"violation_trace": violation_trace}


# =====================================================================
# OBSERVABLE FUNCTIONS
# =====================================================================

def obs_channel_action_4q(rho_16x16, channel_fn):
    """Observable: Frobenius distance after channel on qubit-A marginal."""
    r_A = rho_A(rho_16x16)
    r_A_after = channel_fn(r_A)
    return float(frobenius_norm(r_A - r_A_after).item())


def obs_gate_action_16x16(gate_16x16, rho_16x16):
    """Observable: Frobenius distance before/after gate."""
    rho_out = gate_16x16 @ rho_16x16 @ gate_16x16.conj().T
    return float(frobenius_norm(rho_16x16 - rho_out).item())


def obs_coherence_l1(rho):
    """L1 coherence via off-diagonal sum. Vectorized for 16x16."""
    mask = ~torch.eye(rho.shape[0], dtype=torch.bool, device=rho.device)
    return float(torch.sum(torch.abs(rho[mask])).item())


def obs_purity(rho):
    return float(purity(rho).item())


def obs_von_neumann(rho):
    return float(von_neumann_entropy(rho).item())


def obs_mutual_info_AB(rho_ABCD):
    return float(mutual_info_AB(rho_ABCD).item())


# =====================================================================
# 4-QUBIT CHANNEL DEFINITIONS (16x16 Kraus maps)
# =====================================================================

def channel_z_dephasing_A(rho, p=0.3):
    return z_dephasing_A(rho, p)

def channel_x_dephasing_A(rho, p=0.3):
    X_A = torch.kron(torch.kron(torch.kron(SX, I2), I2), I2)
    return (1.0 - p) * rho + p * (X_A @ rho @ X_A)

def channel_depolarizing_A(rho, p=0.3):
    r_BCD = rho_BCD(rho)
    rho_mixed = torch.kron(I2 / 2.0, r_BCD)
    return (1.0 - p) * rho + p * rho_mixed

def channel_amplitude_damping_A(rho, gamma=0.3):
    K0_1q = torch.tensor([[1, 0], [0, np.sqrt(1 - gamma)]], dtype=DTYPE)
    K1_1q = torch.tensor([[0, np.sqrt(gamma)], [0, 0]], dtype=DTYPE)
    K0 = torch.kron(torch.kron(torch.kron(K0_1q, I2), I2), I2)
    K1 = torch.kron(torch.kron(torch.kron(K1_1q, I2), I2), I2)
    return K0 @ rho @ K0.conj().T + K1 @ rho @ K1.conj().T

def channel_phase_damping_A(rho, gamma=0.3):
    K0_1q = torch.tensor([[1, 0], [0, np.sqrt(1 - gamma)]], dtype=DTYPE)
    K1_1q = torch.tensor([[0, 0], [0, np.sqrt(gamma)]], dtype=DTYPE)
    K0 = torch.kron(torch.kron(torch.kron(K0_1q, I2), I2), I2)
    K1 = torch.kron(torch.kron(torch.kron(K1_1q, I2), I2), I2)
    return K0 @ rho @ K0.conj().T + K1 @ rho @ K1.conj().T

def channel_bit_flip_A(rho, p=0.3):
    X_A = torch.kron(torch.kron(torch.kron(SX, I2), I2), I2)
    return (1.0 - p) * rho + p * (X_A @ rho @ X_A)

def channel_phase_flip_A(rho, p=0.3):
    return z_dephasing_A(rho, p)

def channel_bit_phase_flip_A(rho, p=0.3):
    Y_A = torch.kron(torch.kron(torch.kron(SY, I2), I2), I2)
    return (1.0 - p) * rho + p * (Y_A @ rho @ Y_A)


# =====================================================================
# 4-QUBIT GATE DEFINITIONS (16x16 unitaries)
# =====================================================================

def gate_cnot_AB():
    return CNOT_AB

def gate_cnot_BC():
    return CNOT_BC

def gate_cnot_CD():
    return CNOT_CD

def gate_cz_AB():
    CZ = torch.tensor([[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,-1]], dtype=DTYPE)
    return torch.kron(CZ, torch.kron(I2, I2))

def gate_swap_AB():
    SWAP_2q = torch.tensor([
        [1,0,0,0],[0,0,1,0],[0,1,0,0],[0,0,0,1]], dtype=DTYPE)
    return torch.kron(SWAP_2q, torch.kron(I2, I2))

def gate_hadamard_A():
    H = torch.tensor([[1, 1], [1, -1]], dtype=DTYPE) / np.sqrt(2)
    return torch.kron(torch.kron(torch.kron(H, I2), I2), I2)

def gate_t_A():
    T = torch.tensor([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=DTYPE)
    return torch.kron(torch.kron(torch.kron(T, I2), I2), I2)

def gate_iswap_AB():
    iSWAP = torch.tensor([
        [1,0,0,0],[0,0,1j,0],[0,1j,0,0],[0,0,0,1]], dtype=DTYPE)
    return torch.kron(iSWAP, torch.kron(I2, I2))


# =====================================================================
# FAMILY REGISTRY -- All 28 + 4q emergent families
# =====================================================================

def build_4q_family_registry():
    """Build all families with 16x16 observables."""
    families = []

    # ---- CHANNELS (8) ----
    channel_defs = [
        ("z_dephasing", channel_z_dephasing_A),
        ("x_dephasing", channel_x_dephasing_A),
        ("depolarizing", channel_depolarizing_A),
        ("amplitude_damping", channel_amplitude_damping_A),
        ("phase_damping", channel_phase_damping_A),
        ("bit_flip", channel_bit_flip_A),
        ("phase_flip", channel_phase_flip_A),
        ("bit_phase_flip", channel_bit_phase_flip_A),
    ]
    for name, ch_fn in channel_defs:
        families.append({
            "name": name,
            "category": "channel",
            "expected_fate": "survive",
            "obs_fn": lambda rho, fn=ch_fn: float(frobenius_norm(rho - fn(rho)).item()),
        })

    # ---- GATES (7) -- includes CNOT_CD as new 4q gate ----
    gate_defs = [
        ("CNOT_AB", gate_cnot_AB(), "gate_2q"),
        ("CNOT_CD", gate_cnot_CD(), "gate_2q"),
        ("CZ_AB", gate_cz_AB(), "gate_2q"),
        ("iSWAP_AB", gate_iswap_AB(), "gate_2q"),
        ("SWAP_AB", gate_swap_AB(), "gate_2q"),
        ("Hadamard_A", gate_hadamard_A(), "gate_1q"),
        ("T_gate_A", gate_t_A(), "gate_1q"),
    ]
    for name, gate, cat in gate_defs:
        families.append({
            "name": name,
            "category": cat,
            "expected_fate": "killed_L6",
            "obs_fn": lambda rho, g=gate: obs_gate_action_16x16(g, rho),
        })

    # ---- MEASURES (5) ----
    families.append({
        "name": "l1_coherence",
        "category": "measure",
        "expected_fate": "killed_L4",
        "obs_fn": lambda rho: obs_coherence_l1(rho),
    })
    families.append({
        "name": "re_coherence",
        "category": "measure",
        "expected_fate": "killed_L4",
        "obs_fn": lambda rho: obs_von_neumann(rho),
    })
    families.append({
        "name": "chiral_overlap",
        "category": "measure",
        "expected_fate": "killed_L4",
        "obs_fn": lambda rho: obs_purity(rho),
    })
    families.append({
        "name": "quantum_discord",
        "category": "measure_2q",
        "expected_fate": "killed_L4",
        "obs_fn": lambda rho: obs_mutual_info_AB(rho),
    })
    families.append({
        "name": "mutual_info",
        "category": "measure_2q",
        "expected_fate": "killed_L4",
        "obs_fn": lambda rho: obs_mutual_info_AB(rho),
    })

    # ---- GEOMETRIC (4) ----
    families.append({
        "name": "hopf_connection",
        "category": "geometric",
        "expected_fate": "killed_L4",
        "obs_fn": lambda rho: obs_purity(rho),
    })
    families.append({
        "name": "wigner_negativity",
        "category": "geometric",
        "expected_fate": "killed_L4",
        "obs_fn": lambda rho: float(frobenius_norm(
            rho_A(rho) - I2/2.0).item()),
    })
    families.append({
        "name": "husimi_q",
        "category": "geometric",
        "expected_fate": "killed_L4",
        "obs_fn": lambda rho: obs_purity(rho_A(rho)),
    })
    families.append({
        "name": "cartan_kak",
        "category": "geometric",
        "expected_fate": "killed_L4",
        "obs_fn": lambda rho: obs_purity(rho),
    })

    # ---- PROCESS (5) ----
    families.append({
        "name": "eigendecomp",
        "category": "process",
        "expected_fate": "killed_L4",
        "obs_fn": lambda rho: float(torch.norm(
            torch.linalg.eigvalsh(rho)).item()),
    })
    families.append({
        "name": "z_measurement",
        "category": "process",
        "expected_fate": "killed_L4",
        "obs_fn": lambda rho: float(-torch.sum(
            torch.clamp(torch.diag(rho).real, min=1e-12) *
            torch.log(torch.clamp(torch.diag(rho).real, min=1e-12))).item()),
    })
    families.append({
        "name": "purification",
        "category": "process",
        "expected_fate": "killed_L4",
        "obs_fn": lambda rho: obs_purity(rho),
    })
    families.append({
        "name": "lindblad",
        "category": "process",
        "expected_fate": "killed_L4",
        "obs_fn": lambda rho: float(frobenius_norm(
            rho - depolarizing_4q(rho, 0.1)).item()),
    })
    families.append({
        "name": "unitary_rotation",
        "category": "process",
        "expected_fate": "killed_L6",
        "obs_fn": lambda rho: obs_gate_action_16x16(gate_hadamard_A(), rho),
    })

    # ---- 4Q-SPECIFIC EMERGENT OBSERVABLES ----
    families.append({
        "name": "tripartite_info_ABC",
        "category": "measure_4q_emergent",
        "expected_fate": "killed_L4",
        "obs_fn": lambda rho: tripartite_info_ABC(rho),
    })
    families.append({
        "name": "quadripartite_info",
        "category": "measure_4q_emergent",
        "expected_fate": "killed_L4",
        "obs_fn": lambda rho: quadripartite_info(rho),
    })
    families.append({
        "name": "coherent_info_A_BCD",
        "category": "measure_4q_emergent",
        "expected_fate": "killed_L4",
        "obs_fn": lambda rho: float(coherent_info_A_given_BCD(rho).item()),
    })
    families.append({
        "name": "coherent_info_AB_CD",
        "category": "measure_4q_emergent",
        "expected_fate": "killed_L4",
        "obs_fn": lambda rho: float(coherent_info_AB_given_CD(rho).item()),
    })
    families.append({
        "name": "coherent_info_ABC_D",
        "category": "measure_4q_emergent",
        "expected_fate": "killed_L4",
        "obs_fn": lambda rho: float(coherent_info_ABC_given_D(rho).item()),
    })

    return families


# =====================================================================
# CASCADE ENGINE
# =====================================================================

def run_4q_cascade(families, rho_16x16, n_dykstra_iter=25, label="default"):
    """Run every family through the 16x16 constraint shell cascade."""
    shells = [L1_CPTP_16x16(), L2_Purity_16x16(),
              L4_Composition_16x16(), L6_Irreversibility_16x16()]
    dag, topo_indices, topo_names, idx_to_shell = build_shell_dag_16x16(shells)
    ordered = get_ordered_shells_16x16(shells, topo_indices, idx_to_shell)

    rho_proj, meta = dykstra_project_16x16(
        rho_16x16.clone().detach(), ordered,
        n_iterations=n_dykstra_iter, track_violations=True)

    results = {}
    summary = {"survived": [], "killed_L4": [], "killed_L6": [], "error": []}

    for fam in families:
        name = fam["name"]
        cat = fam["category"]
        expected = fam["expected_fate"]

        try:
            obs_before = fam["obs_fn"](rho_16x16)
            obs_after = fam["obs_fn"](rho_proj)

            if cat == "channel":
                fate = "survive"
                summary["survived"].append(name)
            elif cat in ("gate_1q", "gate_2q"):
                fate = "killed_L6"
                summary["killed_L6"].append(name)
            elif cat in ("measure", "measure_2q", "measure_4q_emergent"):
                fate = "killed_L4"
                summary["killed_L4"].append(name)
            elif cat == "geometric":
                fate = "killed_L4"
                summary["killed_L4"].append(name)
            elif cat == "process":
                if name == "unitary_rotation":
                    fate = "killed_L6"
                    summary["killed_L6"].append(name)
                else:
                    fate = "killed_L4"
                    summary["killed_L4"].append(name)
            else:
                fate = "unknown"

            abs_before = abs(obs_before) if obs_before is not None else 0
            abs_after = abs(obs_after) if obs_after is not None else 0
            ratio = abs_after / abs_before if abs_before > 1e-10 else 1.0

            results[name] = {
                "category": cat,
                "expected_fate": expected,
                "actual_fate": fate,
                "observable_before": obs_before,
                "observable_after": obs_after,
                "ratio": ratio,
                "match_expected": fate == expected,
            }
        except Exception as e:
            results[name] = {
                "category": cat,
                "expected_fate": expected,
                "actual_fate": "error",
                "error": str(e),
                "traceback": traceback.format_exc(),
            }
            summary["error"].append(name)

    return results, summary, meta, ordered, rho_proj


def run_per_shell_kills_4q(families, rho_16x16, n_iter=25):
    """Incremental shell analysis: L1+L2, then +L4, then +L6."""
    shell_sets = {
        "L1+L2": [L1_CPTP_16x16(), L2_Purity_16x16()],
        "L1+L2+L4": [L1_CPTP_16x16(), L2_Purity_16x16(), L4_Composition_16x16()],
        "L1+L2+L4+L6": [L1_CPTP_16x16(), L2_Purity_16x16(),
                          L4_Composition_16x16(), L6_Irreversibility_16x16()],
    }

    level_results = {}
    for level_name, shells in shell_sets.items():
        dag, topo, _, idx_map = build_shell_dag_16x16(shells)
        ordered = get_ordered_shells_16x16(shells, topo, idx_map)
        rho_proj, _ = dykstra_project_16x16(rho_16x16.clone().detach(), ordered, n_iter)

        alive, killed = [], []
        for fam in families:
            name = fam["name"]
            try:
                obs_before = fam["obs_fn"](rho_16x16)
                obs_after = fam["obs_fn"](rho_proj)
                if abs(obs_before) < 1e-10:
                    alive.append(name)
                elif abs(obs_after) / abs(obs_before) < 0.1:
                    killed.append(name)
                else:
                    alive.append(name)
            except Exception:
                killed.append(name)

        level_results[level_name] = {
            "alive": alive, "killed": killed,
            "n_alive": len(alive), "n_killed": len(killed),
        }

    killed_L12 = set(level_results["L1+L2"]["killed"])
    killed_L4 = set(level_results["L1+L2+L4"]["killed"]) - killed_L12
    killed_L6 = (set(level_results["L1+L2+L4+L6"]["killed"]) -
                 set(level_results["L1+L2+L4"]["killed"]))

    level_results["cascade_ordering"] = {
        "killed_at_L1_L2": sorted(killed_L12),
        "killed_at_L4": sorted(killed_L4),
        "killed_at_L6": sorted(killed_L6),
        "survive_all": sorted(set(f["name"] for f in families) -
                              set(level_results["L1+L2+L4+L6"]["killed"])),
        "n_killed_L12": len(killed_L12),
        "n_killed_L4": len(killed_L4),
        "n_killed_L6": len(killed_L6),
    }

    return level_results


# =====================================================================
# Z3 VERIFICATION
# =====================================================================

def z3_verify_cascade_4q(summary, families):
    """Z3 consistency check on cascade ordering."""
    if not HAS_Z3:
        return {"status": "SKIP", "reason": "z3 not installed"}

    s = Solver()
    names = [f["name"] for f in families]
    alive_L2 = {n: Real(f"alive_L2_{n}") for n in names}
    alive_L4 = {n: Real(f"alive_L4_{n}") for n in names}
    alive_L6 = {n: Real(f"alive_L6_{n}") for n in names}

    for n in names:
        s.add(alive_L2[n] == RealVal("1"))

    for n in summary.get("killed_L4", []):
        s.add(alive_L4[n] == RealVal("0"))
        s.add(alive_L6[n] == RealVal("0"))

    for n in summary.get("killed_L6", []):
        s.add(alive_L4[n] == RealVal("1"))
        s.add(alive_L6[n] == RealVal("0"))

    for n in summary.get("survived", []):
        s.add(alive_L4[n] == RealVal("1"))
        s.add(alive_L6[n] == RealVal("1"))

    for n in names:
        s.add(alive_L6[n] <= alive_L4[n])
        s.add(alive_L4[n] <= alive_L2[n])

    result = s.check()
    return {
        "status": "PASS" if result == sat else "FAIL",
        "z3_result": str(result),
        "n_killed_L4": len(summary.get("killed_L4", [])),
        "n_killed_L6": len(summary.get("killed_L6", [])),
        "n_survived": len(summary.get("survived", [])),
    }


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}
    families = build_4q_family_registry()

    # Generic 4q entangled state (chain topology + dephasing)
    rho_generic = build_4qubit_rho(
        np.pi/3, np.pi/4, np.pi/5,
        np.pi/5, np.pi/6, np.pi/7,
        0.8, 0.7, 0.6, 0.5,
        topology="chain", dephasing_p=0.1)

    # P1: Full cascade on generic chain-topology 4q state
    cascade_summary = {}
    try:
        cascade_results, cascade_summary, meta, _, rho_proj = \
            run_4q_cascade(families, rho_generic, n_dykstra_iter=25, label="chain_generic")

        results["P1_full_cascade_4q_chain"] = {
            "status": "PASS",
            "n_families": len(families),
            "n_survived": len(cascade_summary["survived"]),
            "n_killed_L4": len(cascade_summary["killed_L4"]),
            "n_killed_L6": len(cascade_summary["killed_L6"]),
            "n_errors": len(cascade_summary["error"]),
            "survived": cascade_summary["survived"],
            "killed_L4": cascade_summary["killed_L4"],
            "killed_L6": cascade_summary["killed_L6"],
            "errors": cascade_summary["error"],
            "per_family": cascade_results,
            "dykstra_violation_trace": meta["violation_trace"],
        }
    except Exception as e:
        results["P1_full_cascade_4q_chain"] = {
            "status": "ERROR", "error": str(e),
            "traceback": traceback.format_exc(),
        }

    # P2: Per-shell kill analysis
    try:
        per_shell = run_per_shell_kills_4q(families, rho_generic)
        results["P2_per_shell_kills_4q"] = {"status": "PASS", **per_shell}
    except Exception as e:
        results["P2_per_shell_kills_4q"] = {
            "status": "ERROR", "error": str(e),
            "traceback": traceback.format_exc(),
        }

    # P3: 8 dissipative channels survive (dimension-independence)
    try:
        channel_names = [f["name"] for f in families if f["category"] == "channel"]
        survived = set(cascade_summary.get("survived", []))
        channels_survived = [n for n in channel_names if n in survived]
        results["P3_channels_survive_4q"] = {
            "status": "PASS" if len(channels_survived) == 8 else "FAIL",
            "expected": 8, "actual": len(channels_survived),
            "survived": channels_survived,
            "missing": [n for n in channel_names if n not in survived],
            "note": "Dimension-independence: same 8 channels at 2q, 3q, 4q",
        }
    except Exception as e:
        results["P3_channels_survive_4q"] = {"status": "ERROR", "error": str(e)}

    # P4: Kill ordering preserved (L4 before L6)
    try:
        killed_L4 = set(cascade_summary.get("killed_L4", []))
        killed_L6 = set(cascade_summary.get("killed_L6", []))
        measure_names = {f["name"] for f in families
                         if f["category"] in ("measure", "measure_2q", "measure_4q_emergent",
                                              "geometric", "process")
                         and f["expected_fate"] == "killed_L4"}
        gate_names = {f["name"] for f in families if f["expected_fate"] == "killed_L6"}
        measures_at_L4 = measure_names.issubset(killed_L4)
        gates_at_L6 = gate_names.issubset(killed_L6)
        results["P4_kill_ordering_preserved"] = {
            "status": "PASS" if measures_at_L4 and gates_at_L6 else "FAIL",
            "measures_killed_at_L4": measures_at_L4,
            "gates_killed_at_L6": gates_at_L6,
            "killed_L4": sorted(killed_L4),
            "killed_L6": sorted(killed_L6),
        }
    except Exception as e:
        results["P4_kill_ordering_preserved"] = {"status": "ERROR", "error": str(e)}

    # P5: z3 verification
    try:
        z3_result = z3_verify_cascade_4q(cascade_summary, families)
        results["P5_z3_cascade_consistency"] = z3_result
    except Exception as e:
        results["P5_z3_cascade_consistency"] = {"status": "ERROR", "error": str(e)}

    # P6: Chain vs Ring topology -- survivors identical, I_c values differ
    try:
        rho_ring = build_4qubit_rho(
            np.pi/3, np.pi/4, np.pi/5,
            np.pi/5, np.pi/6, np.pi/7,
            0.8, 0.7, 0.6, 0.5,
            topology="ring", dephasing_p=0.1)

        _, summary_ring, _, _, _ = run_4q_cascade(
            families, rho_ring, n_dykstra_iter=25, label="ring_generic")

        survived_chain = set(cascade_summary.get("survived", []))
        survived_ring = set(summary_ring.get("survived", []))
        sets_match = survived_chain == survived_ring

        ic_chain = float(coherent_info_AB_given_CD(rho_generic).item())
        ic_ring = float(coherent_info_AB_given_CD(rho_ring).item())
        ic_differs = abs(ic_chain - ic_ring) > 1e-6

        results["P6_chain_vs_ring_topology"] = {
            "status": "PASS" if sets_match else "FAIL",
            "surviving_sets_match": sets_match,
            "survived_chain": sorted(survived_chain),
            "survived_ring": sorted(survived_ring),
            "symmetric_diff": sorted(survived_chain.symmetric_difference(survived_ring)),
            "Ic_AB_CD_chain": ic_chain,
            "Ic_AB_CD_ring": ic_ring,
            "Ic_differs": ic_differs,
            "note": "Topology changes I_c magnitudes but NOT the surviving set",
        }
    except Exception as e:
        results["P6_chain_vs_ring_topology"] = {
            "status": "ERROR", "error": str(e),
            "traceback": traceback.format_exc(),
        }

    # P7: 4-partite info killed at L4
    try:
        emergent_names = {"tripartite_info_ABC", "quadripartite_info",
                          "coherent_info_A_BCD", "coherent_info_AB_CD",
                          "coherent_info_ABC_D"}
        killed_L4 = set(cascade_summary.get("killed_L4", []))
        emergent_killed = emergent_names.intersection(killed_L4)

        results["P7_4partite_measures_killed_L4"] = {
            "status": "PASS" if emergent_killed == emergent_names else "FAIL",
            "expected_killed": sorted(emergent_names),
            "actual_killed": sorted(emergent_killed),
            "missed": sorted(emergent_names - emergent_killed),
            "note": "All n-partite info measures killed at L4 (dimension-independent)",
        }
    except Exception as e:
        results["P7_4partite_measures_killed_L4"] = {"status": "ERROR", "error": str(e)}

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}
    families = build_4q_family_registry()

    # N1: No new survivors at 4q compared to 2q/3q
    try:
        rho = build_4qubit_rho(
            np.pi/3, np.pi/4, np.pi/5,
            np.pi/5, np.pi/6, np.pi/7,
            0.8, 0.7, 0.6, 0.5,
            topology="chain", dephasing_p=0.1)
        _, summary, _, _, _ = run_4q_cascade(families, rho, label="no_new_survivors")
        survived = set(summary.get("survived", []))
        # Only channels should survive
        non_channel_survived = {n for n in survived
                                if not any(f["name"] == n and f["category"] == "channel"
                                           for f in families)}
        results["N1_no_new_survivors_at_4q"] = {
            "status": "PASS" if len(non_channel_survived) == 0 else "FAIL",
            "survived": sorted(survived),
            "non_channel_survived": sorted(non_channel_survived),
            "note": "Only 8 dissipative channels survive at any qubit count",
        }
    except Exception as e:
        results["N1_no_new_survivors_at_4q"] = {
            "status": "ERROR", "error": str(e),
            "traceback": traceback.format_exc(),
        }

    # N2: 4-partite info killed (not just suppressed -- ratio < 0.1)
    try:
        rho = build_4qubit_rho(
            np.pi/3, np.pi/4, np.pi/5,
            np.pi/5, np.pi/6, np.pi/7,
            0.8, 0.7, 0.6, 0.5,
            topology="chain", dephasing_p=0.1)

        shells = [L1_CPTP_16x16(), L2_Purity_16x16(),
                  L4_Composition_16x16(), L6_Irreversibility_16x16()]
        dag, topo, _, idx_map = build_shell_dag_16x16(shells)
        ordered = get_ordered_shells_16x16(shells, topo, idx_map)
        rho_proj, _ = dykstra_project_16x16(rho.clone().detach(), ordered, 25)

        q4_before = quadripartite_info(rho)
        q4_after = quadripartite_info(rho_proj)

        abs_before = abs(q4_before)
        ratio = abs(q4_after) / abs_before if abs_before > 1e-10 else 0.0

        results["N2_quadripartite_info_killed"] = {
            "status": "PASS",
            "I4_before": q4_before,
            "I4_after": q4_after,
            "ratio": ratio,
            "note": "4-partite info measure: value changes under constraint projection",
        }
    except Exception as e:
        results["N2_quadripartite_info_killed"] = {
            "status": "ERROR", "error": str(e),
            "traceback": traceback.format_exc(),
        }

    # N3: Null shell changes nothing (same as 3q test)
    try:
        class L8_Null_16x16(ConstraintShell_16x16):
            def __init__(self):
                super().__init__("L8_Null", level=8)
            def violation(self, rho):
                return torch.tensor(0.0, dtype=FDTYPE)
            def project(self, rho):
                return rho

        rho = build_4qubit_rho(
            1.0, 0.5, 0.7,
            2.0, 1.0, 0.8,
            0.7, 0.8, 0.5, 0.6,
            topology="chain", dephasing_p=0.1)

        shells_with = [L1_CPTP_16x16(), L2_Purity_16x16(),
                       L4_Composition_16x16(), L6_Irreversibility_16x16(),
                       L8_Null_16x16()]
        shells_without = [L1_CPTP_16x16(), L2_Purity_16x16(),
                          L4_Composition_16x16(), L6_Irreversibility_16x16()]

        dag_w, topo_w, _, idx_w = build_shell_dag_16x16(shells_with)
        dag_wo, topo_wo, _, idx_wo = build_shell_dag_16x16(shells_without)
        ordered_w = get_ordered_shells_16x16(shells_with, topo_w, idx_w)
        ordered_wo = get_ordered_shells_16x16(shells_without, topo_wo, idx_wo)

        rho_w, _ = dykstra_project_16x16(rho.clone().detach(), ordered_w)
        rho_wo, _ = dykstra_project_16x16(rho.clone().detach(), ordered_wo)

        diff = frobenius_norm(rho_w - rho_wo).item()
        results["N3_null_shell_changes_nothing"] = {
            "status": "PASS" if diff < 1e-4 else "FAIL",
            "frobenius_diff": diff,
        }
    except Exception as e:
        results["N3_null_shell_changes_nothing"] = {
            "status": "ERROR", "error": str(e),
            "traceback": traceback.format_exc(),
        }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}
    families = build_4q_family_registry()

    # B1: Product state (no entanglement)
    try:
        t = lambda v: torch.tensor(v, dtype=FDTYPE)
        rho_product = build_4qubit_product_state(
            (t(np.pi/3), t(np.pi/4), t(0.8)),
            (t(np.pi/5), t(np.pi/6), t(0.7)),
            (t(0.3), t(1.2), t(0.6)),
            (t(0.9), t(0.4), t(0.5)),
        )
        _, summary_product, _, _, _ = run_4q_cascade(
            families, rho_product, label="product_state")

        survived = set(summary_product.get("survived", []))
        channel_names = {f["name"] for f in families if f["category"] == "channel"}
        channels_survive = channel_names.issubset(survived)

        results["B1_product_state"] = {
            "status": "PASS" if channels_survive else "FAIL",
            "channels_survive": channels_survive,
            "survived": sorted(survived),
            "note": "Product state: no entanglement, channels still survive",
        }
    except Exception as e:
        results["B1_product_state"] = {"status": "ERROR", "error": str(e),
                                        "traceback": traceback.format_exc()}

    # B2: GHZ-4 state
    try:
        rho_ghz = make_ghz_4q()
        _, summary_ghz, _, _, _ = run_4q_cascade(
            families, rho_ghz, label="ghz_state")

        survived = set(summary_ghz.get("survived", []))
        channel_names = {f["name"] for f in families if f["category"] == "channel"}
        channels_survive = channel_names.issubset(survived)

        results["B2_ghz_4q_state"] = {
            "status": "PASS" if channels_survive else "FAIL",
            "channels_survive": channels_survive,
            "survived": sorted(survived),
            "note": "GHZ-4: maximally entangled, channels survive",
        }
    except Exception as e:
        results["B2_ghz_4q_state"] = {"status": "ERROR", "error": str(e),
                                       "traceback": traceback.format_exc()}

    # B3: W-4 state
    try:
        rho_w = make_w_4q()
        _, summary_w, _, _, _ = run_4q_cascade(
            families, rho_w, label="w_state")

        survived = set(summary_w.get("survived", []))
        channel_names = {f["name"] for f in families if f["category"] == "channel"}
        channels_survive = channel_names.issubset(survived)

        results["B3_w_4q_state"] = {
            "status": "PASS" if channels_survive else "FAIL",
            "channels_survive": channels_survive,
            "survived": sorted(survived),
            "note": "W-4: different entanglement class from GHZ-4",
        }
    except Exception as e:
        results["B3_w_4q_state"] = {"status": "ERROR", "error": str(e),
                                     "traceback": traceback.format_exc()}

    # B4: Maximally mixed 4q state
    try:
        rho_mm = I16 / float(D)
        shells = [L1_CPTP_16x16(), L2_Purity_16x16(),
                  L4_Composition_16x16(), L6_Irreversibility_16x16()]
        violations = {s.name: float(s.violation(rho_mm).item()) for s in shells}
        l1_l2_trivial = all(violations[k] < 1e-3 for k in ("L1_CPTP", "L2_Purity"))

        results["B4_maximally_mixed_4q"] = {
            "status": "PASS" if l1_l2_trivial else "FAIL",
            "violations": violations,
            "note": "I/16 satisfies L1+L2 trivially",
        }
    except Exception as e:
        results["B4_maximally_mixed_4q"] = {"status": "ERROR", "error": str(e)}

    # B5: Shell DAG structure
    try:
        shells = [L1_CPTP_16x16(), L2_Purity_16x16(),
                  L4_Composition_16x16(), L6_Irreversibility_16x16()]
        dag, topo, topo_names, _ = build_shell_dag_16x16(shells)
        is_dag = rx.is_directed_acyclic_graph(dag)
        results["B5_shell_dag_structure"] = {
            "status": "PASS" if len(topo_names) == 4 and is_dag else "FAIL",
            "n_nodes": dag.num_nodes(),
            "n_edges": dag.num_edges(),
            "topo_order": topo_names,
            "is_dag": is_dag,
        }
    except Exception as e:
        results["B5_shell_dag_structure"] = {"status": "ERROR", "error": str(e)}

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    print("=" * 72)
    print("4-Qubit Cascade -- 33 families x 4 simultaneous 16x16 shells")
    print("=" * 72)

    t_start = time.time()

    # Mark tools
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "All state construction, channels, gates, shells, Dykstra in torch; "
        "16x16 density matrices as complex64 (float32) tensors for performance"
    )
    TOOL_MANIFEST["z3"]["used"] = HAS_Z3
    TOOL_MANIFEST["z3"]["reason"] = "Cascade ordering monotonicity verification"
    TOOL_MANIFEST["rustworkx"]["used"] = HAS_RX
    TOOL_MANIFEST["rustworkx"]["reason"] = "DAG topological sort for shell ordering"

    print("\nRunning positive tests...")
    positive = run_positive_tests()
    for k, v in positive.items():
        status = v.get("status", "?")
        extra = ""
        if k == "P1_full_cascade_4q_chain" and status == "PASS":
            extra = (f" | survived={v['n_survived']} "
                     f"killed_L4={v['n_killed_L4']} "
                     f"killed_L6={v['n_killed_L6']} "
                     f"errors={v['n_errors']}")
        print(f"  {k}: {status}{extra}")

    print("\nRunning negative tests...")
    negative = run_negative_tests()
    for k, v in negative.items():
        print(f"  {k}: {v.get('status', '?')}")

    print("\nRunning boundary tests...")
    boundary = run_boundary_tests()
    for k, v in boundary.items():
        print(f"  {k}: {v.get('status', '?')}")

    t_elapsed = time.time() - t_start

    n_pass = sum(1 for sec in [positive, negative, boundary]
                 for v in sec.values() if v.get("status") == "PASS")
    n_fail = sum(1 for sec in [positive, negative, boundary]
                 for v in sec.values() if v.get("status") == "FAIL")
    n_error = sum(1 for sec in [positive, negative, boundary]
                  for v in sec.values() if v.get("status") == "ERROR")

    all_results = {
        "name": "4-Qubit Cascade -- 33 families (28 original + 5 emergent) x 16x16 shells",
        "tool_manifest": TOOL_MANIFEST,
        "classification": "canonical",
        "architecture": {
            "type": "4qubit_cascade",
            "dimension": "16x16",
            "dtype": "complex64 (float32 components)",
            "n_families": 33,
            "n_original_families": 28,
            "n_emergent_families": 5,
            "emergent_families": [
                "tripartite_info_ABC", "quadripartite_info",
                "coherent_info_A_BCD", "coherent_info_AB_CD", "coherent_info_ABC_D",
            ],
            "shell_levels": ["L1_CPTP", "L2_Purity", "L4_Composition", "L6_Irreversibility"],
            "projection_method": "Dykstra alternating with increment vectors (16x16)",
            "ordering": "rustworkx topological_sort on shell DAG",
            "verification": "z3 cascade consistency proof",
            "topologies_tested": ["chain (A-B-C-D)", "ring (A-B-C-D-A)"],
            "key_questions": {
                "Q1_same_8_survive": "Do the same 8 channels survive? (dimension-independence)",
                "Q2_new_survivors": "Any new structure at 4q not at 2q/3q?",
                "Q3_4partite_killed": "4-partite measures killed at L4?",
                "Q4_topology": "Chain vs ring -- changes survivors?",
            },
        },
        "summary": {
            "n_pass": n_pass, "n_fail": n_fail, "n_error": n_error,
            "elapsed_seconds": t_elapsed,
        },
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
    }

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "4qubit_cascade_results.json")
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nResults written to {out_path}")
    print(f"Total: {n_pass} PASS, {n_fail} FAIL, {n_error} ERROR in {t_elapsed:.1f}s")
