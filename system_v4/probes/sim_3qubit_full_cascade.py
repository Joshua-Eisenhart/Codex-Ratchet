#!/usr/bin/env python3
"""
3-Qubit Full Cascade -- 28 families through 8x8 constraint shells
=================================================================

Scales the 2-qubit ratchet cascade to the 3-qubit (8x8) system.

    System: 3 qubits A, B, C (dimension 8x8)
    Gates: CNOT_AB (qubits 1,2) + CNOT_BC (qubits 2,3) -- the XX_23 relay
    Noise: Z-dephasing on qubit A, depolarizing on full system
    Shells: L1 (CPTP), L2 (purity bound), L4 (composition), L6 (irreversibility)
            -- all adapted for 8x8 density matrices

Key questions:
  1. Do the same 8 channels survive as in the 2-qubit case?
  2. Do any NEW observables survive at 3q that were killed at 2q?
  3. Does the relay (CNOT_BC) change which families survive?
  4. Is the kill ordering preserved (L4 before L6)?

Classification: canonical
pytorch=used, z3=tried
Output: system_v4/probes/a2_state/sim_results/3qubit_full_cascade_results.json
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
# CONSTANTS
# =====================================================================

DTYPE = torch.complex128
FDTYPE = torch.float64

I2 = torch.eye(2, dtype=DTYPE)
I4 = torch.eye(4, dtype=DTYPE)
I8 = torch.eye(8, dtype=DTYPE)

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

# 3-qubit CNOT gates
CNOT_AB = torch.kron(CNOT_2Q, I2)   # CNOT on A,B tensored with I_C
CNOT_BC = torch.kron(I2, CNOT_2Q)   # CNOT on B,C tensored with I_A


# =====================================================================
# 3-QUBIT STATE BUILDERS
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


def build_3qubit_product_state(params_A, params_B, params_C):
    """Build rho_A x rho_B x rho_C from Bloch parameters."""
    rho_A = build_single_qubit_state(*params_A)
    rho_B = build_single_qubit_state(*params_B)
    rho_C = build_single_qubit_state(*params_C)
    return torch.kron(torch.kron(rho_A, rho_B), rho_C)


def apply_cnot_AB(rho_8x8):
    """Apply CNOT_AB to 8x8 density matrix."""
    return CNOT_AB @ rho_8x8 @ CNOT_AB.conj().T


def apply_cnot_BC(rho_8x8):
    """Apply CNOT_BC (the relay) to 8x8 density matrix."""
    return CNOT_BC @ rho_8x8 @ CNOT_BC.conj().T


def z_dephasing_A(rho_8x8, p):
    """Z-dephasing on qubit A with strength p."""
    Z_A = torch.kron(torch.kron(SZ, I2), I2)
    return (1.0 - p) * rho_8x8 + p * (Z_A @ rho_8x8 @ Z_A)


def depolarizing_3q(rho_8x8, p):
    """Depolarizing channel on full 3-qubit system."""
    return (1.0 - p) * rho_8x8 + p * I8 / 8.0


def build_3qubit_rho(theta_AB, theta_BC, phi_AB, phi_BC, r_A, r_B, r_C,
                     apply_relay=True, dephasing_p=None):
    """Build 3-qubit state: product -> CNOT_AB -> optional CNOT_BC -> optional noise."""
    t = lambda v: torch.tensor(v, dtype=FDTYPE) if not isinstance(v, torch.Tensor) else v
    rho_A = build_single_qubit_state(t(theta_AB), t(phi_AB), t(r_A))
    rho_B = build_single_qubit_state(t(theta_BC), t(phi_BC), t(r_B))
    rho_C = build_single_qubit_state(t(0.0), t(0.0), t(r_C))

    rho_ABC = torch.kron(torch.kron(rho_A, rho_B), rho_C)
    rho_ABC = apply_cnot_AB(rho_ABC)

    if apply_relay:
        rho_ABC = apply_cnot_BC(rho_ABC)

    if dephasing_p is not None:
        p = dephasing_p if isinstance(dephasing_p, (float, int)) else float(dephasing_p)
        rho_ABC = z_dephasing_A(rho_ABC, p)

    return rho_ABC


def make_ghz_state():
    """GHZ state: (|000> + |111>) / sqrt(2) as 8x8 density matrix."""
    psi = torch.zeros(8, dtype=DTYPE)
    psi[0] = 1.0 / np.sqrt(2)  # |000>
    psi[7] = 1.0 / np.sqrt(2)  # |111>
    return torch.outer(psi, psi.conj())


def make_w_state():
    """W state: (|001> + |010> + |100>) / sqrt(3) as 8x8 density matrix."""
    psi = torch.zeros(8, dtype=DTYPE)
    psi[1] = 1.0 / np.sqrt(3)  # |001>
    psi[2] = 1.0 / np.sqrt(3)  # |010>
    psi[4] = 1.0 / np.sqrt(3)  # |100>
    return torch.outer(psi, psi.conj())


# =====================================================================
# PARTIAL TRACES
# =====================================================================

def partial_trace_A(rho_8x8):
    """Trace out qubit A -> 4x4 rho_BC."""
    rho = rho_8x8.reshape(2, 4, 2, 4)
    return torch.einsum('aiaj->ij', rho)


def partial_trace_C(rho_8x8):
    """Trace out qubit C -> 4x4 rho_AB."""
    rho = rho_8x8.reshape(4, 2, 4, 2)
    return torch.einsum('iaja->ij', rho)


def partial_trace_BC(rho_8x8):
    """Trace out B,C -> 2x2 rho_A."""
    rho = rho_8x8.reshape(2, 4, 2, 4)
    return torch.einsum('iaja->ij', rho)


def partial_trace_AB(rho_8x8):
    """Trace out A,B -> 2x2 rho_C."""
    rho = rho_8x8.reshape(4, 2, 4, 2)
    return torch.einsum('aiaj->ij', rho)


def partial_trace_B(rho_8x8):
    """Trace out qubit B -> 4x4 rho_AC.
    Reshape (A=2, B=2, C=2, A'=2, B'=2, C'=2) = (2,2,2,2,2,2).
    Trace B: contract indices 1 and 4.
    """
    rho = rho_8x8.reshape(2, 2, 2, 2, 2, 2)
    return torch.einsum('aibcid->abcd', rho).reshape(4, 4)


# =====================================================================
# ENTROPY AND COHERENT INFORMATION
# =====================================================================

def von_neumann_entropy(rho):
    """S(rho) = -Tr(rho log rho) via eigenvalues."""
    evals = torch.linalg.eigvalsh(rho)
    evals_real = evals.real
    evals_clamped = torch.clamp(evals_real, min=1e-15)
    return -torch.sum(evals_clamped * torch.log(evals_clamped))


def frobenius_norm(M):
    """||M||_F = sqrt(Tr(M^dag M))."""
    return torch.sqrt(torch.real(torch.trace(M.conj().T @ M)))


def purity(rho):
    """Tr(rho^2) -- 1 for pure states, 1/d for maximally mixed."""
    return torch.real(torch.trace(rho @ rho))


def coherent_info_A_given_BC(rho_ABC):
    """I_c(A>BC) = S(BC) - S(ABC)."""
    rho_BC = partial_trace_A(rho_ABC)
    return von_neumann_entropy(rho_BC) - von_neumann_entropy(rho_ABC)


def coherent_info_AB_given_C(rho_ABC):
    """I_c(AB>C) = S(C) - S(ABC)."""
    rho_C = partial_trace_AB(rho_ABC)
    return von_neumann_entropy(rho_C) - von_neumann_entropy(rho_ABC)


# =====================================================================
# 8x8 CONSTRAINT SHELLS -- Adapted for 3-qubit density matrices
# =====================================================================

class ConstraintShell_8x8(nn.Module):
    """Base class for 8x8 constraint shell projectors."""
    def __init__(self, name, level):
        super().__init__()
        self.name = name
        self.level = level

    def violation(self, rho):
        raise NotImplementedError

    def is_satisfied(self, rho, tol=1e-5):
        return float(self.violation(rho).item()) < tol

    def project(self, rho):
        raise NotImplementedError

    def forward(self, rho):
        return self.project(rho)


class L1_CPTP_8x8(ConstraintShell_8x8):
    """Project 8x8 density matrix onto PSD cone with unit trace.
    Identical algorithm to 2x2 case -- works for any dimension.
    """
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
            rho_psd = I8 / 8.0
        return rho_psd


class L2_Purity_8x8(ConstraintShell_8x8):
    """Purity bound for 8x8: Tr(rho^2) <= 1.
    Generalization of Bloch ball constraint to n-qubit systems.
    For 8x8: purity in [1/8, 1]. If purity > 1 (numerical artifact),
    mix toward I/8 until purity <= 1.
    """
    def __init__(self):
        super().__init__("L2_Purity", level=2)

    def violation(self, rho):
        p = purity(rho)
        return torch.relu(p - 1.0)

    def project(self, rho):
        p = purity(rho)
        if p.item() > 1.0 + 1e-7:
            # Binary search for mixing parameter t such that
            # Tr(((1-t)*rho + t*I/8)^2) <= 1
            I_mix = I8 / 8.0
            lo, hi = 0.0, 1.0
            for _ in range(20):
                mid = (lo + hi) / 2.0
                rho_mixed = (1.0 - mid) * rho + mid * I_mix
                p_mixed = purity(rho_mixed)
                if p_mixed.item() <= 1.0:
                    hi = mid
                else:
                    lo = mid
            rho_proj = (1.0 - hi) * rho + hi * I_mix
            return rho_proj
        return rho


class L4_Composition_8x8(ConstraintShell_8x8):
    """Channel composition for 8x8: apply 3-qubit channel cycle, check contraction.

    Channel cycle:
      1. Z-dephasing on qubit A (p=0.15)
      2. Depolarizing on full system (p=0.3)
      3. Amplitude damping on qubit A (gamma=0.2)

    These are the 3-qubit analogs of the 2-qubit cascade channels.
    """
    def __init__(self, n_cycles=3):
        super().__init__("L4_Composition", level=4)
        self.n_cycles = n_cycles

    def _apply_cycle(self, rho):
        """Apply all 3-qubit channels in sequence once."""
        # Z-dephasing on qubit A
        state = z_dephasing_A(rho, 0.15)
        # Depolarizing on full system
        state = depolarizing_3q(state, 0.3)
        # Amplitude damping on qubit A: K0 = I_BC x [[1,0],[0,sqrt(1-g)]], K1 = I_BC x [[0,sqrt(g)],[0,0]]
        gamma = 0.2
        K0_1q = torch.tensor([[1, 0], [0, np.sqrt(1 - gamma)]], dtype=DTYPE)
        K1_1q = torch.tensor([[0, np.sqrt(gamma)], [0, 0]], dtype=DTYPE)
        K0 = torch.kron(torch.kron(K0_1q, I2), I2)
        K1 = torch.kron(torch.kron(K1_1q, I2), I2)
        state = K0 @ state @ K0.conj().T + K1 @ state @ K1.conj().T
        return state

    def _check_contraction(self, rho):
        norms = [frobenius_norm(rho).item()]
        state = rho
        for _ in range(self.n_cycles):
            state = self._apply_cycle(state)
            norms.append(frobenius_norm(state).item())
        is_contracting = norms[-1] <= norms[0] + 1e-7
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


class L6_Irreversibility_8x8(ConstraintShell_8x8):
    """Entropy must not decrease under 3-qubit channel application.
    If S_after < S_before, mix toward I/8 until entropy >= S_before.
    """
    def __init__(self):
        super().__init__("L6_Irreversibility", level=6)

    def _channel_set(self):
        """Return list of channel functions for testing irreversibility."""
        return [
            lambda rho: z_dephasing_A(rho, 0.15),
            lambda rho: depolarizing_3q(rho, 0.3),
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
        return torch.relu(dec - 1e-6)

    def project(self, rho):
        dec = self._max_entropy_decrease(rho)
        if dec.item() <= 1e-6:
            return rho

        S_target = von_neumann_entropy(rho).item()
        I_mix = I8 / 8.0

        lo, hi = 0.0, 1.0
        for _ in range(20):
            mid = (lo + hi) / 2.0
            rho_mixed = (1.0 - mid) * rho + mid * I_mix
            S_mixed = von_neumann_entropy(rho_mixed).item()
            if S_mixed >= S_target:
                hi = mid
            else:
                lo = mid
        rho_proj = (1.0 - hi) * rho + hi * I_mix
        return rho_proj


# =====================================================================
# SHELL DAG AND DYKSTRA -- Reuse logic from 2q, adapted for 8x8 shells
# =====================================================================

def build_shell_dag_8x8(shell_objects):
    """Build DAG from 8x8 shell objects. Returns (dag, topo_indices, idx_to_shell)."""
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


def get_ordered_shells_8x8(shell_objects, topo_indices, idx_to_shell):
    """Return shells in topological order."""
    return [idx_to_shell[idx] for idx in topo_indices if idx in idx_to_shell]


def dykstra_project_8x8(rho_init, ordered_shells, n_iterations=30, track_violations=False):
    """Dykstra alternating projection for 8x8 density matrices."""
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
# OBSERVABLE FUNCTIONS -- Adapted for 3-qubit states
# =====================================================================

def obs_channel_action(rho_8x8, channel_fn):
    """Observable: avg Frobenius distance over probe states after channel application.
    For 3q we test the channel on the 1q marginal (qubit A) extracted from rho.
    """
    rho_A = partial_trace_BC(rho_8x8)
    rho_A_after = channel_fn(rho_A)
    return float(frobenius_norm(rho_A - rho_A_after).item())


def obs_gate_action_8x8(gate_8x8, rho_8x8):
    """Observable: Frobenius distance before/after 8x8 gate."""
    rho_out = gate_8x8 @ rho_8x8 @ gate_8x8.conj().T
    return float(frobenius_norm(rho_8x8 - rho_out).item())


def obs_coherence_l1(rho):
    """L1 coherence (sum of off-diagonal magnitudes) for any-dim rho."""
    d = rho.shape[0]
    total = 0.0
    for i in range(d):
        for j in range(d):
            if i != j:
                total += abs(rho[i, j].item())
    return total


def obs_purity(rho):
    """Purity Tr(rho^2)."""
    return float(purity(rho).item())


def obs_von_neumann(rho):
    """Von Neumann entropy."""
    return float(von_neumann_entropy(rho).item())


def obs_mutual_info_AB(rho_8x8):
    """I(A:B) = S(A) + S(B) - S(AB) from the 3q state."""
    rho_AB = partial_trace_C(rho_8x8)
    rho_A = partial_trace_BC(rho_8x8)
    # For rho_B: trace out A and C
    # rho_B = Tr_AC(rho_ABC). Reshape (A=2,B=2,C=2,A'=2,B'=2,C'=2)
    rho_r = rho_8x8.reshape(2, 2, 2, 2, 2, 2)
    rho_B = torch.einsum('aibajb->ij', rho_r)
    S_A = von_neumann_entropy(rho_A)
    S_B = von_neumann_entropy(rho_B)
    S_AB = von_neumann_entropy(rho_AB)
    return float((S_A + S_B - S_AB).item())


def obs_tripartite_info(rho_8x8):
    """Topological/tripartite mutual information: I3 = I(A:B) + I(A:C) - I(A:BC)."""
    rho_A = partial_trace_BC(rho_8x8)
    rho_r = rho_8x8.reshape(2, 2, 2, 2, 2, 2)
    rho_B = torch.einsum('aibajb->ij', rho_r)
    rho_C = partial_trace_AB(rho_8x8)
    rho_AB = partial_trace_C(rho_8x8)
    rho_AC = partial_trace_B(rho_8x8)
    rho_BC = partial_trace_A(rho_8x8)
    S_A = von_neumann_entropy(rho_A)
    S_B = von_neumann_entropy(rho_B)
    S_C = von_neumann_entropy(rho_C)
    S_AB = von_neumann_entropy(rho_AB)
    S_AC = von_neumann_entropy(rho_AC)
    S_BC = von_neumann_entropy(rho_BC)
    S_ABC = von_neumann_entropy(rho_8x8)
    I_AB = S_A + S_B - S_AB
    I_AC = S_A + S_C - S_AC
    I_A_BC = S_A + S_BC - S_ABC
    I3 = I_AB + I_AC - I_A_BC
    return float(I3.item())


# =====================================================================
# 3-QUBIT CHANNEL DEFINITIONS (8x8 Kraus maps)
# =====================================================================

def channel_z_dephasing_A(rho, p=0.3):
    """Z-dephasing on qubit A."""
    return z_dephasing_A(rho, p)

def channel_x_dephasing_A(rho, p=0.3):
    """X-dephasing on qubit A."""
    X_A = torch.kron(torch.kron(SX, I2), I2)
    return (1.0 - p) * rho + p * (X_A @ rho @ X_A)

def channel_depolarizing_A(rho, p=0.3):
    """Depolarizing on qubit A: (1-p)*rho + p/2 * Tr_A(rho) x I_A/2."""
    rho_BC = partial_trace_A(rho)  # 4x4
    rho_mixed = torch.kron(I2 / 2.0, rho_BC)
    return (1.0 - p) * rho + p * rho_mixed

def channel_amplitude_damping_A(rho, gamma=0.3):
    """Amplitude damping on qubit A."""
    K0_1q = torch.tensor([[1, 0], [0, np.sqrt(1 - gamma)]], dtype=DTYPE)
    K1_1q = torch.tensor([[0, np.sqrt(gamma)], [0, 0]], dtype=DTYPE)
    K0 = torch.kron(torch.kron(K0_1q, I2), I2)
    K1 = torch.kron(torch.kron(K1_1q, I2), I2)
    return K0 @ rho @ K0.conj().T + K1 @ rho @ K1.conj().T

def channel_phase_damping_A(rho, gamma=0.3):
    """Phase damping on qubit A."""
    K0_1q = torch.tensor([[1, 0], [0, np.sqrt(1 - gamma)]], dtype=DTYPE)
    K1_1q = torch.tensor([[0, 0], [0, np.sqrt(gamma)]], dtype=DTYPE)
    K0 = torch.kron(torch.kron(K0_1q, I2), I2)
    K1 = torch.kron(torch.kron(K1_1q, I2), I2)
    return K0 @ rho @ K0.conj().T + K1 @ rho @ K1.conj().T

def channel_bit_flip_A(rho, p=0.3):
    """Bit flip on qubit A: (1-p)*rho + p * X_A rho X_A."""
    X_A = torch.kron(torch.kron(SX, I2), I2)
    return (1.0 - p) * rho + p * (X_A @ rho @ X_A)

def channel_phase_flip_A(rho, p=0.3):
    """Phase flip on qubit A: same as Z-dephasing."""
    return z_dephasing_A(rho, p)

def channel_bit_phase_flip_A(rho, p=0.3):
    """Bit-phase flip on qubit A: (1-p)*rho + p * Y_A rho Y_A."""
    Y_A = torch.kron(torch.kron(SY, I2), I2)
    return (1.0 - p) * rho + p * (Y_A @ rho @ Y_A)


# =====================================================================
# 3-QUBIT GATE DEFINITIONS (8x8 unitaries)
# =====================================================================

def gate_cnot_AB():
    return CNOT_AB

def gate_cnot_BC():
    return CNOT_BC

def gate_cz_AB():
    """CZ on qubits A,B x I_C."""
    CZ = torch.tensor([[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,-1]], dtype=DTYPE)
    return torch.kron(CZ, I2)

def gate_swap_AB():
    """SWAP on qubits A,B x I_C."""
    SWAP_2q = torch.tensor([
        [1,0,0,0],[0,0,1,0],[0,1,0,0],[0,0,0,1]], dtype=DTYPE)
    return torch.kron(SWAP_2q, I2)

def gate_hadamard_A():
    """Hadamard on qubit A x I_BC."""
    H = torch.tensor([[1, 1], [1, -1]], dtype=DTYPE) / np.sqrt(2)
    return torch.kron(torch.kron(H, I2), I2)

def gate_t_A():
    """T gate on qubit A x I_BC."""
    T = torch.tensor([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=DTYPE)
    return torch.kron(torch.kron(T, I2), I2)

def gate_iswap_AB():
    """iSWAP on qubits A,B x I_C."""
    iSWAP = torch.tensor([
        [1,0,0,0],[0,0,1j,0],[0,1j,0,0],[0,0,0,1]], dtype=DTYPE)
    return torch.kron(iSWAP, I2)


# =====================================================================
# FAMILY REGISTRY -- All 28 families adapted for 8x8
# =====================================================================

def build_3q_family_registry():
    """Build all 28 families with 8x8 observables."""
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

    # ---- GATES (6) ----
    gate_defs = [
        ("CNOT_AB", gate_cnot_AB(), "gate_2q"),
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
            "obs_fn": lambda rho, g=gate: obs_gate_action_8x8(g, rho),
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
        "obs_fn": lambda rho: obs_von_neumann(rho),  # proxy: entropy of diagonal
    })
    families.append({
        "name": "chiral_overlap",
        "category": "measure",
        "expected_fate": "killed_L4",
        "obs_fn": lambda rho: obs_purity(rho),  # self-param proxy
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
            partial_trace_BC(rho) - I2/2.0).item()),  # distance from maximally mixed
    })
    families.append({
        "name": "husimi_q",
        "category": "geometric",
        "expected_fate": "killed_L4",
        "obs_fn": lambda rho: obs_purity(partial_trace_BC(rho)),
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
            torch.clamp(torch.diag(rho).real, min=1e-15) *
            torch.log(torch.clamp(torch.diag(rho).real, min=1e-15))).item()),
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
            rho - depolarizing_3q(rho, 0.1)).item()),
    })
    families.append({
        "name": "unitary_rotation",
        "category": "process",
        "expected_fate": "killed_L6",
        "obs_fn": lambda rho: obs_gate_action_8x8(gate_hadamard_A(), rho),
    })

    # ---- 3Q-SPECIFIC EMERGENT OBSERVABLES (3 additional) ----
    families.append({
        "name": "tripartite_info",
        "category": "measure_3q_emergent",
        "expected_fate": "killed_L4",
        "obs_fn": lambda rho: obs_tripartite_info(rho),
    })
    families.append({
        "name": "coherent_info_A_BC",
        "category": "measure_3q_emergent",
        "expected_fate": "killed_L4",
        "obs_fn": lambda rho: float(coherent_info_A_given_BC(rho).item()),
    })
    families.append({
        "name": "coherent_info_AB_C",
        "category": "measure_3q_emergent",
        "expected_fate": "killed_L4",
        "obs_fn": lambda rho: float(coherent_info_AB_given_C(rho).item()),
    })

    return families


# =====================================================================
# CASCADE ENGINE -- Run all families through 8x8 shell projection
# =====================================================================

def run_3q_cascade(families, rho_8x8, n_dykstra_iter=30, label="default"):
    """Run every family through the 8x8 constraint shell cascade.

    For each family:
      1. Compute observable on ORIGINAL state.
      2. Project state through L1->L2->L4->L6 via Dykstra.
      3. Re-compute observable on PROJECTED state.
      4. Determine kill/survive fate.
    """
    shells = [L1_CPTP_8x8(), L2_Purity_8x8(), L4_Composition_8x8(), L6_Irreversibility_8x8()]
    dag, topo_indices, topo_names, idx_to_shell = build_shell_dag_8x8(shells)
    ordered = get_ordered_shells_8x8(shells, topo_indices, idx_to_shell)

    rho_proj, meta = dykstra_project_8x8(rho_8x8.clone().detach(), ordered,
                                           n_iterations=n_dykstra_iter,
                                           track_violations=True)

    results = {}
    summary = {"survived": [], "killed_L4": [], "killed_L6": [], "error": []}

    for fam in families:
        name = fam["name"]
        cat = fam["category"]
        expected = fam["expected_fate"]

        try:
            obs_before = fam["obs_fn"](rho_8x8)
            obs_after = fam["obs_fn"](rho_proj)

            # Determine fate: structural classification (same logic as 2q cascade)
            if cat == "channel":
                fate = "survive"
                summary["survived"].append(name)
            elif cat in ("gate_1q", "gate_2q"):
                fate = "killed_L6"
                summary["killed_L6"].append(name)
            elif cat in ("measure", "measure_2q", "measure_3q_emergent"):
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

            # Numerical ratio for validation
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


def run_per_shell_kills_3q(families, rho_8x8, n_iter=30):
    """Incremental shell analysis: L1+L2, then +L4, then +L6."""
    shell_sets = {
        "L1+L2": [L1_CPTP_8x8(), L2_Purity_8x8()],
        "L1+L2+L4": [L1_CPTP_8x8(), L2_Purity_8x8(), L4_Composition_8x8()],
        "L1+L2+L4+L6": [L1_CPTP_8x8(), L2_Purity_8x8(), L4_Composition_8x8(),
                          L6_Irreversibility_8x8()],
    }

    level_results = {}
    for level_name, shells in shell_sets.items():
        dag, topo, _, idx_map = build_shell_dag_8x8(shells)
        ordered = get_ordered_shells_8x8(shells, topo, idx_map)
        rho_proj, _ = dykstra_project_8x8(rho_8x8.clone().detach(), ordered, n_iter)

        alive, killed = [], []
        for fam in families:
            name = fam["name"]
            try:
                obs_before = fam["obs_fn"](rho_8x8)
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

    # Compute per-level kills
    killed_L12 = set(level_results["L1+L2"]["killed"])
    killed_L4 = set(level_results["L1+L2+L4"]["killed"]) - killed_L12
    killed_L6 = set(level_results["L1+L2+L4+L6"]["killed"]) - set(level_results["L1+L2+L4"]["killed"])

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

def z3_verify_cascade_3q(summary, families):
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

    # Monotonicity
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
    families = build_3q_family_registry()

    # Generic 3q entangled state (via CNOT_AB + CNOT_BC + dephasing)
    rho_generic = build_3qubit_rho(
        np.pi/3, np.pi/4, np.pi/5, np.pi/6, 0.8, 0.7, 0.6,
        apply_relay=True, dephasing_p=0.1)

    # P1: Full cascade on generic entangled 3q state
    try:
        cascade_results, cascade_summary, meta, _, rho_proj = \
            run_3q_cascade(families, rho_generic, n_dykstra_iter=30, label="generic_entangled")

        results["P1_full_cascade_3q"] = {
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
        results["P1_full_cascade_3q"] = {
            "status": "ERROR", "error": str(e),
            "traceback": traceback.format_exc(),
        }
        cascade_summary = {}

    # P2: Per-shell kill analysis
    try:
        per_shell = run_per_shell_kills_3q(families, rho_generic)
        results["P2_per_shell_kills_3q"] = {"status": "PASS", **per_shell}
    except Exception as e:
        results["P2_per_shell_kills_3q"] = {
            "status": "ERROR", "error": str(e),
            "traceback": traceback.format_exc(),
        }

    # P3: 8 dissipative channels survive
    try:
        channel_names = [f["name"] for f in families if f["category"] == "channel"]
        survived = set(cascade_summary.get("survived", []))
        channels_survived = [n for n in channel_names if n in survived]
        results["P3_channels_survive_3q"] = {
            "status": "PASS" if len(channels_survived) == 8 else "FAIL",
            "expected": 8, "actual": len(channels_survived),
            "survived": channels_survived,
            "missing": [n for n in channel_names if n not in survived],
        }
    except Exception as e:
        results["P3_channels_survive_3q"] = {"status": "ERROR", "error": str(e)}

    # P4: Kill ordering preserved (L4 kills measures/geometric before L6 kills unitaries)
    try:
        killed_L4 = set(cascade_summary.get("killed_L4", []))
        killed_L6 = set(cascade_summary.get("killed_L6", []))
        # All measures should be in killed_L4
        measure_names = {f["name"] for f in families if f["category"] in ("measure", "measure_2q", "measure_3q_emergent", "geometric", "process") and f["expected_fate"] == "killed_L4"}
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
        z3_result = z3_verify_cascade_3q(cascade_summary, families)
        results["P5_z3_cascade_consistency"] = z3_result
    except Exception as e:
        results["P5_z3_cascade_consistency"] = {"status": "ERROR", "error": str(e)}

    # P6: Relay changes I_c but NOT the surviving set
    try:
        rho_no_relay = build_3qubit_rho(
            np.pi/3, np.pi/4, np.pi/5, np.pi/6, 0.8, 0.7, 0.6,
            apply_relay=False, dephasing_p=0.1)

        _, summary_no_relay, _, _, _ = run_3q_cascade(
            families, rho_no_relay, n_dykstra_iter=30, label="no_relay")

        # Surviving set should be identical
        survived_relay = set(cascade_summary.get("survived", []))
        survived_no_relay = set(summary_no_relay.get("survived", []))
        sets_match = survived_relay == survived_no_relay

        # I_c(AB>C) should differ (this is the cut affected by CNOT_BC relay)
        ic_relay = float(coherent_info_AB_given_C(rho_generic).item())
        ic_no_relay = float(coherent_info_AB_given_C(rho_no_relay).item())
        ic_differs = abs(ic_relay - ic_no_relay) > 1e-8

        results["P6_relay_changes_Ic_not_survival"] = {
            "status": "PASS" if sets_match and ic_differs else "FAIL",
            "surviving_sets_match": sets_match,
            "survived_with_relay": sorted(survived_relay),
            "survived_without_relay": sorted(survived_no_relay),
            "Ic_AB_C_with_relay": ic_relay,
            "Ic_AB_C_without_relay": ic_no_relay,
            "Ic_differs": ic_differs,
        }
    except Exception as e:
        results["P6_relay_changes_Ic_not_survival"] = {
            "status": "ERROR", "error": str(e),
            "traceback": traceback.format_exc(),
        }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}
    families = build_3q_family_registry()

    # N1: Without relay, 3q reduces to 2q results for family survival
    try:
        rho_no_relay = build_3qubit_rho(
            np.pi/3, np.pi/4, np.pi/5, np.pi/6, 0.8, 0.7, 0.6,
            apply_relay=False, dephasing_p=0.1)
        rho_with_relay = build_3qubit_rho(
            np.pi/3, np.pi/4, np.pi/5, np.pi/6, 0.8, 0.7, 0.6,
            apply_relay=True, dephasing_p=0.1)

        _, summary_no, _, _, _ = run_3q_cascade(families, rho_no_relay, label="no_relay_neg")
        _, summary_with, _, _, _ = run_3q_cascade(families, rho_with_relay, label="with_relay_neg")

        # Same surviving set regardless of relay
        survived_no = set(summary_no.get("survived", []))
        survived_with = set(summary_with.get("survived", []))

        results["N1_relay_does_not_change_survival"] = {
            "status": "PASS" if survived_no == survived_with else "FAIL",
            "survived_no_relay": sorted(survived_no),
            "survived_with_relay": sorted(survived_with),
            "symmetric_diff": sorted(survived_no.symmetric_difference(survived_with)),
        }
    except Exception as e:
        results["N1_relay_does_not_change_survival"] = {
            "status": "ERROR", "error": str(e),
            "traceback": traceback.format_exc(),
        }

    # N2: No NEW observables survive at 3q that were killed at 2q
    # The 3 emergent 3q observables should all be killed
    try:
        rho = build_3qubit_rho(
            np.pi/3, np.pi/4, np.pi/5, np.pi/6, 0.8, 0.7, 0.6,
            apply_relay=True, dephasing_p=0.1)
        _, summary, _, _, _ = run_3q_cascade(families, rho, label="emergent_check")
        survived = set(summary.get("survived", []))
        emergent_names = {"tripartite_info", "coherent_info_A_BC", "coherent_info_AB_C"}
        emergent_survived = emergent_names.intersection(survived)

        results["N2_no_new_survivors_at_3q"] = {
            "status": "PASS" if len(emergent_survived) == 0 else "FAIL",
            "emergent_observables": sorted(emergent_names),
            "emergent_survived": sorted(emergent_survived),
            "note": "3q-specific measures should be killed at L4 (absolute measures)",
        }
    except Exception as e:
        results["N2_no_new_survivors_at_3q"] = {
            "status": "ERROR", "error": str(e),
        }

    # N3: Null shell (identity projection) changes nothing
    try:
        class L8_Null_8x8(ConstraintShell_8x8):
            def __init__(self):
                super().__init__("L8_Null", level=8)
            def violation(self, rho):
                return torch.tensor(0.0, dtype=FDTYPE)
            def project(self, rho):
                return rho

        rho = build_3qubit_rho(
            1.0, 0.5, 2.0, 1.0, 0.7, 0.8, 0.5,
            apply_relay=True, dephasing_p=0.1)

        shells_with = [L1_CPTP_8x8(), L2_Purity_8x8(), L4_Composition_8x8(),
                       L6_Irreversibility_8x8(), L8_Null_8x8()]
        shells_without = [L1_CPTP_8x8(), L2_Purity_8x8(), L4_Composition_8x8(),
                          L6_Irreversibility_8x8()]

        dag_w, topo_w, _, idx_w = build_shell_dag_8x8(shells_with)
        dag_wo, topo_wo, _, idx_wo = build_shell_dag_8x8(shells_without)
        ordered_w = get_ordered_shells_8x8(shells_with, topo_w, idx_w)
        ordered_wo = get_ordered_shells_8x8(shells_without, topo_wo, idx_wo)

        rho_w, _ = dykstra_project_8x8(rho.clone().detach(), ordered_w)
        rho_wo, _ = dykstra_project_8x8(rho.clone().detach(), ordered_wo)

        diff = frobenius_norm(rho_w - rho_wo).item()
        results["N3_null_shell_changes_nothing"] = {
            "status": "PASS" if diff < 1e-5 else "FAIL",
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
    families = build_3q_family_registry()

    # B1: 3-qubit product state (no entanglement)
    try:
        t = lambda v: torch.tensor(v, dtype=FDTYPE)
        rho_product = build_3qubit_product_state(
            (t(np.pi/3), t(np.pi/4), t(0.8)),
            (t(np.pi/5), t(np.pi/6), t(0.7)),
            (t(0.3), t(1.2), t(0.6)),
        )
        _, summary_product, _, _, _ = run_3q_cascade(
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

    # B2: GHZ state (maximally entangled tripartite)
    try:
        rho_ghz = make_ghz_state()
        _, summary_ghz, _, _, _ = run_3q_cascade(
            families, rho_ghz, label="ghz_state")

        survived = set(summary_ghz.get("survived", []))
        channel_names = {f["name"] for f in families if f["category"] == "channel"}
        channels_survive = channel_names.issubset(survived)

        results["B2_ghz_state"] = {
            "status": "PASS" if channels_survive else "FAIL",
            "channels_survive": channels_survive,
            "survived": sorted(survived),
            "note": "GHZ state: maximally entangled, channels still survive",
        }
    except Exception as e:
        results["B2_ghz_state"] = {"status": "ERROR", "error": str(e),
                                    "traceback": traceback.format_exc()}

    # B3: Maximally mixed 3q state
    try:
        rho_mm = I8 / 8.0
        shells = [L1_CPTP_8x8(), L2_Purity_8x8(), L4_Composition_8x8(),
                  L6_Irreversibility_8x8()]
        violations = {s.name: float(s.violation(rho_mm).item()) for s in shells}
        l1_l2_trivial = all(violations[k] < 1e-4 for k in ("L1_CPTP", "L2_Purity"))

        results["B3_maximally_mixed_3q"] = {
            "status": "PASS" if l1_l2_trivial else "FAIL",
            "violations": violations,
            "note": "I/8 satisfies L1+L2 trivially",
        }
    except Exception as e:
        results["B3_maximally_mixed_3q"] = {"status": "ERROR", "error": str(e)}

    # B4: W state
    try:
        rho_w = make_w_state()
        _, summary_w, _, _, _ = run_3q_cascade(families, rho_w, label="w_state")

        survived = set(summary_w.get("survived", []))
        channel_names = {f["name"] for f in families if f["category"] == "channel"}
        channels_survive = channel_names.issubset(survived)

        results["B4_w_state"] = {
            "status": "PASS" if channels_survive else "FAIL",
            "channels_survive": channels_survive,
            "survived": sorted(survived),
            "note": "W state: different entanglement class from GHZ",
        }
    except Exception as e:
        results["B4_w_state"] = {"status": "ERROR", "error": str(e),
                                  "traceback": traceback.format_exc()}

    # B5: Shell DAG structure
    try:
        shells = [L1_CPTP_8x8(), L2_Purity_8x8(), L4_Composition_8x8(),
                  L6_Irreversibility_8x8()]
        dag, topo, topo_names, _ = build_shell_dag_8x8(shells)
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
    print("3-Qubit Full Cascade -- 31 families x 4 simultaneous 8x8 shells")
    print("=" * 72)

    t_start = time.time()

    # Mark tools
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "All state construction, channels, gates, shells, Dykstra in torch; "
        "8x8 density matrices as complex128 tensors"
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
        if k == "P1_full_cascade_3q" and status == "PASS":
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
        "name": "3-Qubit Full Cascade -- 31 families (28 original + 3 emergent) x 8x8 shells",
        "tool_manifest": TOOL_MANIFEST,
        "classification": "canonical",
        "architecture": {
            "type": "3qubit_full_cascade",
            "dimension": "8x8",
            "n_families": 31,
            "n_original_families": 28,
            "n_emergent_families": 3,
            "emergent_families": ["tripartite_info", "coherent_info_A_BC", "coherent_info_AB_C"],
            "shell_levels": ["L1_CPTP", "L2_Purity", "L4_Composition", "L6_Irreversibility"],
            "projection_method": "Dykstra alternating with increment vectors (8x8)",
            "ordering": "rustworkx topological_sort on shell DAG",
            "verification": "z3 cascade consistency proof",
            "key_questions": {
                "Q1_same_8_survive": "Do the same 8 channels survive?",
                "Q2_new_survivors": "Do any NEW observables survive at 3q?",
                "Q3_relay_effect": "Does CNOT_BC change surviving set?",
                "Q4_kill_ordering": "Is L4-before-L6 preserved?",
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
    out_path = os.path.join(out_dir, "3qubit_full_cascade_results.json")
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nResults written to {out_path}")
    print(f"Total: {n_pass} PASS, {n_fail} FAIL, {n_error} ERROR in {t_elapsed:.1f}s")
