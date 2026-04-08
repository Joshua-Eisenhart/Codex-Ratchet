#!/usr/bin/env python3
"""
Phase 7 Baseline Validation -- Falsification Protocol

Systematic comparison of all 28 irreducible torch modules against numpy baselines.
Tests 4 disconfirmation criteria from PYTORCH_RATCHET_BUILD_PLAN.md.
Current limitation: the graph-topology criterion is only implemented on an
explicit topology subset, not yet across all 28 families.

  1. Gradient triviality: autograd vs finite-difference
  2. Graph topology independence: chain vs star vs parallel
  3. Forward sufficiency: forward-only rejection vs backward selection
  4. Substrate equivalence: torch vs numpy on 100 random states

If all tested criteria show null on their covered families, the claim weakens.
Full falsification still requires complete criterion coverage, especially for C2.
This is the honest test. No bias toward confirming or denying.

Classification: canonical
Output: system_v4/probes/a2_state/sim_results/phase7_baseline_validation_results.json
"""

import json
import os
import time
import numpy as np
from collections import OrderedDict

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

# Classification of how deeply each tool is integrated into the result.
# load_bearing  = result materially depends on this tool
# supportive    = useful cross-check / helper but not decisive
# decorative    = present only at manifest/import level
# not_applicable = not used in this sim
TOOL_INTEGRATION_DEPTH = {
    "pytorch":   "load_bearing",    # All 28 torch modules; autograd gradient test; graph topology test; substrate equivalence
    "pyg":       "not_applicable",  # Not used -- this is a falsification protocol, not a graph sim
    "z3":        "not_applicable",  # Not used
    "cvc5":      "not_applicable",  # Not used
    "sympy":     "not_applicable",  # Not used
    "clifford":  "not_applicable",  # Not used
    "geomstats": "not_applicable",  # Not used
    "e3nn":      "not_applicable",  # Not used
    "rustworkx": "not_applicable",  # Not used
    "xgi":       "not_applicable",  # Not used
    "toponetx":  "not_applicable",  # Not used
    "gudhi":     "not_applicable",  # Not used
}

try:
    import torch
    import torch.nn as nn
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "Core substrate: all 28 torch modules, autograd gradients, graph topology tests"
except ImportError:
    raise RuntimeError("PyTorch is required for Phase 7 validation")

# =====================================================================
# PAULI MATRICES (shared)
# =====================================================================

PAULIS_NP = [
    np.array([[0, 1], [1, 0]], dtype=np.complex128),       # X
    np.array([[0, -1j], [1j, 0]], dtype=np.complex128),    # Y
    np.array([[1, 0], [0, -1]], dtype=np.complex128),       # Z
]

PAULIS_T = [
    torch.tensor([[0, 1], [1, 0]], dtype=torch.complex128),
    torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex128),
    torch.tensor([[1, 0], [0, -1]], dtype=torch.complex128),
]

I2_NP = np.eye(2, dtype=np.complex128)
I2_T = torch.eye(2, dtype=torch.complex128)
I4_NP = np.eye(4, dtype=np.complex128)
I4_T = torch.eye(4, dtype=torch.complex128)

# =====================================================================
# HELPER: random states
# =====================================================================

def random_bloch(rng, r_max=0.95):
    """Random Bloch vector with norm in [0.1, r_max]."""
    v = rng.randn(3)
    r = rng.uniform(0.1, r_max)
    return v / np.linalg.norm(v) * r


def random_2q_density(rng):
    """Random 4x4 density matrix from a proper partial trace.

    Sample a random pure state on two qubits plus a 2D environment,
    then trace out the environment. This produces a bona fide mixed
    two-qubit state with rank at most 2.
    """
    psi = rng.randn(8) + 1j * rng.randn(8)
    psi /= np.linalg.norm(psi)

    # Reshape as a 4 x 2 amplitude matrix for AB x E, then trace out E.
    psi_ab_e = psi.reshape(4, 2)
    rho = psi_ab_e @ psi_ab_e.conj().T
    rho /= np.trace(rho)
    return rho


def test_random_2q_density_baseline(rng, n_samples=8, tol=1e-10):
    """Sanity check that the 2-qubit baseline is an actual mixed state."""
    purity_values = []
    min_eigs = []
    hermitian_errors = []
    trace_errors = []

    for _ in range(n_samples):
        rho = random_2q_density(rng)
        hermitian_errors.append(float(np.max(np.abs(rho - rho.conj().T))))
        trace_errors.append(float(abs(np.trace(rho) - 1.0)))
        purity = float(np.real(np.trace(rho @ rho)))
        purity_values.append(purity)
        min_eigs.append(float(np.min(np.linalg.eigvalsh(rho))))

    mixed_count = sum(p < 1.0 - 1e-8 for p in purity_values)
    return {
        "n_samples": n_samples,
        "hermitian_max_error": float(max(hermitian_errors)),
        "trace_max_error": float(max(trace_errors)),
        "min_eigenvalue_min": float(min(min_eigs)),
        "purity_min": float(min(purity_values)),
        "purity_max": float(max(purity_values)),
        "mixed_count": int(mixed_count),
        "all_mixed": mixed_count == n_samples,
        "verdict": "PASS" if (
            max(hermitian_errors) < tol
            and max(trace_errors) < tol
            and min(min_eigs) >= -1e-10
            and mixed_count == n_samples
        ) else "FAIL",
    }


def random_pure_state(rng, d=2):
    """Random pure state vector of dimension d."""
    psi = rng.randn(d) + 1j * rng.randn(d)
    psi /= np.linalg.norm(psi)
    return psi


# =====================================================================
# NUMPY BASELINES for all 28 families
# =====================================================================

def np_density_matrix(bloch):
    rho = I2_NP / 2
    for i, s in enumerate(PAULIS_NP):
        rho = rho + bloch[i] * s / 2
    return rho


def np_purity(rho):
    return np.real(np.trace(rho @ rho))


def np_von_neumann(rho):
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > 1e-15]
    return float(-np.sum(evals * np.log2(evals + 1e-30)))


def np_purification(bloch):
    """Purification: return purity of density matrix (the observable)."""
    rho = np_density_matrix(bloch)
    return np_purity(rho)


def np_channel_apply(kraus_ops, rho):
    """Apply channel via Kraus operators."""
    out = np.zeros_like(rho)
    for K in kraus_ops:
        out += K @ rho @ K.conj().T
    return out


def np_z_dephasing(p, rho):
    K0 = np.sqrt(1 - p) * I2_NP
    K1 = np.sqrt(p) * PAULIS_NP[2]
    return np_channel_apply([K0, K1], rho)


def np_x_dephasing(p, rho):
    K0 = np.sqrt(1 - p) * I2_NP
    K1 = np.sqrt(p) * PAULIS_NP[0]
    return np_channel_apply([K0, K1], rho)


def np_depolarizing(p, rho):
    return (1 - p) * rho + p * I2_NP / 2


def np_amplitude_damping(gamma, rho):
    K0 = np.array([[1, 0], [0, np.sqrt(1 - gamma)]], dtype=np.complex128)
    K1 = np.array([[0, np.sqrt(gamma)], [0, 0]], dtype=np.complex128)
    return np_channel_apply([K0, K1], rho)


def np_phase_damping(lam, rho):
    K0 = np.array([[1, 0], [0, np.sqrt(1 - lam)]], dtype=np.complex128)
    K1 = np.array([[0, 0], [0, np.sqrt(lam)]], dtype=np.complex128)
    return np_channel_apply([K0, K1], rho)


def np_bit_flip(p, rho):
    K0 = np.sqrt(1 - p) * I2_NP
    K1 = np.sqrt(p) * PAULIS_NP[0]
    return np_channel_apply([K0, K1], rho)


def np_phase_flip(p, rho):
    K0 = np.sqrt(1 - p) * I2_NP
    K1 = np.sqrt(p) * PAULIS_NP[2]
    return np_channel_apply([K0, K1], rho)


def np_bit_phase_flip(p, rho):
    K0 = np.sqrt(1 - p) * I2_NP
    K1 = np.sqrt(p) * PAULIS_NP[1]
    return np_channel_apply([K0, K1], rho)


def np_unitary_rotation(theta, axis_idx, rho):
    """Rotation around Pauli axis by angle theta."""
    U = np.cos(theta / 2) * I2_NP - 1j * np.sin(theta / 2) * PAULIS_NP[axis_idx]
    return U @ rho @ U.conj().T


def np_z_measurement(rho):
    """Z-measurement: return probabilities and post-measurement states."""
    P0 = np.array([[1, 0], [0, 0]], dtype=np.complex128)
    P1 = np.array([[0, 0], [0, 1]], dtype=np.complex128)
    p0 = np.real(np.trace(P0 @ rho))
    p1 = np.real(np.trace(P1 @ rho))
    return np.array([p0, p1])


# 2-qubit gates (4x4)
CNOT_NP = np.array([[1,0,0,0],[0,1,0,0],[0,0,0,1],[0,0,1,0]], dtype=np.complex128)
CZ_NP = np.diag([1, 1, 1, -1]).astype(np.complex128)
SWAP_NP = np.array([[1,0,0,0],[0,0,1,0],[0,1,0,0],[0,0,0,1]], dtype=np.complex128)
H_NP = np.array([[1, 1], [1, -1]], dtype=np.complex128) / np.sqrt(2)
T_NP = np.diag([1, np.exp(1j * np.pi / 4)]).astype(np.complex128)
ISWAP_NP = np.array([[1,0,0,0],[0,0,1j,0],[0,1j,0,0],[0,0,0,1]], dtype=np.complex128)


def np_gate_apply_1q(U, rho):
    return U @ rho @ U.conj().T


def np_gate_apply_2q(U, rho):
    return U @ rho @ U.conj().T


def np_cartan_kak(a, b, c, rho_2q):
    """Simplified Cartan KAK: exp(-i*(a*XX + b*YY + c*ZZ))."""
    XX = np.kron(PAULIS_NP[0], PAULIS_NP[0])
    YY = np.kron(PAULIS_NP[1], PAULIS_NP[1])
    ZZ = np.kron(PAULIS_NP[2], PAULIS_NP[2])
    H = a * XX + b * YY + c * ZZ
    U = np.eye(4, dtype=np.complex128)
    # Matrix exponential via eigendecomposition
    evals, evecs = np.linalg.eigh(H)
    U = evecs @ np.diag(np.exp(-1j * evals)) @ evecs.conj().T
    return U @ rho_2q @ U.conj().T


def np_eigenvalue_decomposition(rho):
    """Return sorted eigenvalues."""
    return np.sort(np.real(np.linalg.eigvalsh(rho)))


def np_husimi_q(rho, alpha):
    """Husimi Q function at coherent state |alpha>. For qubit, |alpha> ~ cos(|a|)|0> + e^{i*arg(a)}*sin(|a|)|1>."""
    r = np.abs(alpha)
    phi = np.angle(alpha)
    psi = np.array([np.cos(r), np.exp(1j * phi) * np.sin(r)], dtype=np.complex128)
    return float(np.real(psi.conj() @ rho @ psi)) / np.pi


def np_l1_coherence(rho):
    """L1 coherence = sum of absolute off-diagonal elements."""
    d = rho.shape[0]
    total = 0.0
    for i in range(d):
        for j in range(d):
            if i != j:
                total += np.abs(rho[i, j])
    return total


def np_relative_entropy_coherence(rho):
    """Relative entropy of coherence = S(diag(rho)) - S(rho)."""
    diag_rho = np.diag(np.diag(rho))
    return np_von_neumann(diag_rho) - np_von_neumann(rho)


def np_wigner_negativity(rho):
    """Wigner negativity volume for qubit: 1 - 1/sqrt(2) * |bloch|.
    For mixed state: uses simplified discrete Wigner function proxy."""
    evals = np.linalg.eigvalsh(rho)
    # For qubit: W_min = (1 - |r|) / 2, negative volume ~ max(0, 2*min_eval - 1/2)
    # Simplified: return sum of negative Wigner values (proxy via eigenvalues)
    wigner_vals = (2 * evals - 0.5)
    neg_volume = float(np.sum(np.abs(wigner_vals[wigner_vals < 0])))
    return neg_volume


def np_hopf_connection(theta, phi):
    """Hopf map: S3 -> S2. Given angles on S3, return point on S2 (Bloch sphere)."""
    psi = np.array([np.cos(theta / 2), np.exp(1j * phi) * np.sin(theta / 2)], dtype=np.complex128)
    # Bloch vector from pure state
    rho = np.outer(psi, psi.conj())
    bx = 2 * np.real(rho[0, 1])
    by = 2 * np.imag(rho[1, 0])
    bz = np.real(rho[0, 0] - rho[1, 1])
    return np.array([bx, by, bz])


def np_chiral_overlap(psi_L, psi_R):
    """Overlap between left and right chiral components."""
    return float(np.abs(np.dot(psi_L.conj(), psi_R)) ** 2)


def np_mutual_information(rho_AB):
    """I(A:B) = S(A) + S(B) - S(AB)."""
    # Partial traces for 2-qubit system
    rho_A = np.trace(rho_AB.reshape(2, 2, 2, 2), axis1=1, axis2=3)
    rho_B = np.trace(rho_AB.reshape(2, 2, 2, 2), axis1=0, axis2=2)
    return np_von_neumann(rho_A) + np_von_neumann(rho_B) - np_von_neumann(rho_AB)


def np_quantum_discord(rho_AB):
    """Simplified quantum discord via measurement on B in Z basis.
    D(A|B) = I(A:B) - J(A|B) where J is classical correlation."""
    mi = np_mutual_information(rho_AB)
    # Measure B in Z basis
    P0 = np.kron(I2_NP, np.array([[1, 0], [0, 0]], dtype=np.complex128))
    P1 = np.kron(I2_NP, np.array([[0, 0], [0, 1]], dtype=np.complex128))
    p0 = np.real(np.trace(P0 @ rho_AB))
    p1 = np.real(np.trace(P1 @ rho_AB))
    # Conditional states
    S_cond = 0.0
    for p_k, P_k in [(p0, P0), (p1, P1)]:
        if p_k > 1e-12:
            rho_k = P_k @ rho_AB @ P_k / p_k
            rho_A_k = np.trace(rho_k.reshape(2, 2, 2, 2), axis1=1, axis2=3)
            S_cond += p_k * np_von_neumann(rho_A_k)
    rho_A = np.trace(rho_AB.reshape(2, 2, 2, 2), axis1=1, axis2=3)
    J = np_von_neumann(rho_A) - S_cond
    return mi - J


# =====================================================================
# TORCH MODULES for all 28 families
# =====================================================================

class TorchDensityMatrix(nn.Module):
    """Family 1: Density matrix from Bloch vector."""
    def __init__(self, bloch):
        super().__init__()
        self.bloch = nn.Parameter(torch.tensor(bloch, dtype=torch.float64))

    def forward(self):
        rho = I2_T.clone() / 2
        for i, s in enumerate(PAULIS_T):
            rho = rho + self.bloch[i].to(torch.complex128) * s / 2
        return rho

    def observable(self):
        """Purity."""
        rho = self.forward()
        return torch.real(torch.trace(rho @ rho))


class TorchPurification(nn.Module):
    """Family 2: Purification -- purity as differentiable observable."""
    def __init__(self, bloch):
        super().__init__()
        self.bloch = nn.Parameter(torch.tensor(bloch, dtype=torch.float64))

    def forward(self):
        rho = I2_T.clone() / 2
        for i, s in enumerate(PAULIS_T):
            rho = rho + self.bloch[i].to(torch.complex128) * s / 2
        return torch.real(torch.trace(rho @ rho))

    def observable(self):
        return self.forward()


class TorchChannelBase(nn.Module):
    """Base class for single-parameter channels."""
    def __init__(self, param, bloch):
        super().__init__()
        self.param = nn.Parameter(torch.tensor([param], dtype=torch.float64))
        self.bloch = torch.tensor(bloch, dtype=torch.float64)

    def _make_rho(self):
        rho = I2_T.clone() / 2
        for i, s in enumerate(PAULIS_T):
            rho = rho + self.bloch[i].to(torch.complex128) * s / 2
        return rho

    def _apply_kraus(self, kraus_ops, rho):
        out = torch.zeros_like(rho)
        for K in kraus_ops:
            out = out + K @ rho @ K.conj().T
        return out


class TorchZDephasing(TorchChannelBase):
    """Family 3."""
    def forward(self):
        rho = self._make_rho()
        p = torch.clamp(self.param[0], 0, 1)
        K0 = torch.sqrt(1 - p).to(torch.complex128) * I2_T
        K1 = torch.sqrt(p).to(torch.complex128) * PAULIS_T[2]
        return self._apply_kraus([K0, K1], rho)

    def observable(self):
        rho_out = self.forward()
        return torch.real(torch.trace(rho_out @ rho_out))


class TorchXDephasing(TorchChannelBase):
    """Family 4."""
    def forward(self):
        rho = self._make_rho()
        p = torch.clamp(self.param[0], 0, 1)
        K0 = torch.sqrt(1 - p).to(torch.complex128) * I2_T
        K1 = torch.sqrt(p).to(torch.complex128) * PAULIS_T[0]
        return self._apply_kraus([K0, K1], rho)

    def observable(self):
        rho_out = self.forward()
        return torch.real(torch.trace(rho_out @ rho_out))


class TorchDepolarizing(TorchChannelBase):
    """Family 5."""
    def forward(self):
        rho = self._make_rho()
        p = torch.clamp(self.param[0], 0, 1)
        return (1 - p) * rho + p * I2_T / 2

    def observable(self):
        rho_out = self.forward()
        return torch.real(torch.trace(rho_out @ rho_out))


class TorchAmplitudeDamping(TorchChannelBase):
    """Family 6."""
    def forward(self):
        rho = self._make_rho()
        g = torch.clamp(self.param[0], 0, 1)
        K0 = torch.zeros(2, 2, dtype=torch.complex128)
        K0[0, 0] = 1.0
        K0[1, 1] = torch.sqrt(1 - g).to(torch.complex128)
        K1 = torch.zeros(2, 2, dtype=torch.complex128)
        K1[0, 1] = torch.sqrt(g).to(torch.complex128)
        return self._apply_kraus([K0, K1], rho)

    def observable(self):
        rho_out = self.forward()
        return torch.real(torch.trace(rho_out @ rho_out))


class TorchPhaseDamping(TorchChannelBase):
    """Family 7."""
    def forward(self):
        rho = self._make_rho()
        lam = torch.clamp(self.param[0], 0, 1)
        K0 = torch.zeros(2, 2, dtype=torch.complex128)
        K0[0, 0] = 1.0
        K0[1, 1] = torch.sqrt(1 - lam).to(torch.complex128)
        K1 = torch.zeros(2, 2, dtype=torch.complex128)
        K1[1, 1] = torch.sqrt(lam).to(torch.complex128)
        return self._apply_kraus([K0, K1], rho)

    def observable(self):
        rho_out = self.forward()
        return torch.real(torch.trace(rho_out @ rho_out))


class TorchBitFlip(TorchChannelBase):
    """Family 8."""
    def forward(self):
        rho = self._make_rho()
        p = torch.clamp(self.param[0], 0, 1)
        K0 = torch.sqrt(1 - p).to(torch.complex128) * I2_T
        K1 = torch.sqrt(p).to(torch.complex128) * PAULIS_T[0]
        return self._apply_kraus([K0, K1], rho)

    def observable(self):
        rho_out = self.forward()
        return torch.real(torch.trace(rho_out @ rho_out))


class TorchPhaseFlip(TorchChannelBase):
    """Family 9."""
    def forward(self):
        rho = self._make_rho()
        p = torch.clamp(self.param[0], 0, 1)
        K0 = torch.sqrt(1 - p).to(torch.complex128) * I2_T
        K1 = torch.sqrt(p).to(torch.complex128) * PAULIS_T[2]
        return self._apply_kraus([K0, K1], rho)

    def observable(self):
        rho_out = self.forward()
        return torch.real(torch.trace(rho_out @ rho_out))


class TorchBitPhaseFlip(TorchChannelBase):
    """Family 10."""
    def forward(self):
        rho = self._make_rho()
        p = torch.clamp(self.param[0], 0, 1)
        K0 = torch.sqrt(1 - p).to(torch.complex128) * I2_T
        K1 = torch.sqrt(p).to(torch.complex128) * PAULIS_T[1]
        return self._apply_kraus([K0, K1], rho)

    def observable(self):
        rho_out = self.forward()
        return torch.real(torch.trace(rho_out @ rho_out))


class TorchUnitaryRotation(TorchChannelBase):
    """Family 11: parameterized rotation around Z axis."""
    def forward(self):
        rho = self._make_rho()
        theta = self.param[0]
        c = torch.cos(theta / 2).to(torch.complex128)
        s = torch.sin(theta / 2).to(torch.complex128)
        U = c * I2_T - 1j * s * PAULIS_T[2]
        return U @ rho @ U.conj().T

    def observable(self):
        rho_out = self.forward()
        return torch.real(torch.trace(rho_out @ rho_out))


class TorchZMeasurement(nn.Module):
    """Family 12: Z-measurement probabilities."""
    def __init__(self, bloch):
        super().__init__()
        self.bloch = nn.Parameter(torch.tensor(bloch, dtype=torch.float64))

    def forward(self):
        rho = I2_T.clone() / 2
        for i, s in enumerate(PAULIS_T):
            rho = rho + self.bloch[i].to(torch.complex128) * s / 2
        P0 = torch.tensor([[1, 0], [0, 0]], dtype=torch.complex128)
        p0 = torch.real(torch.trace(P0 @ rho))
        p1 = 1.0 - p0
        return torch.stack([p0, p1])

    def observable(self):
        probs = self.forward()
        # Observable: probability of |0>
        return probs[0]


class TorchGate2Q(nn.Module):
    """Base for 2-qubit gate families."""
    def __init__(self, gate_np, bloch_A, bloch_B):
        super().__init__()
        self.gate = torch.tensor(gate_np, dtype=torch.complex128)
        self.bloch_A = nn.Parameter(torch.tensor(bloch_A, dtype=torch.float64))
        self.bloch_B = nn.Parameter(torch.tensor(bloch_B, dtype=torch.float64))

    def _make_rho_2q(self):
        rho_A = I2_T.clone() / 2
        rho_B = I2_T.clone() / 2
        for i, s in enumerate(PAULIS_T):
            rho_A = rho_A + self.bloch_A[i].to(torch.complex128) * s / 2
            rho_B = rho_B + self.bloch_B[i].to(torch.complex128) * s / 2
        return torch.kron(rho_A, rho_B)

    def forward(self):
        rho = self._make_rho_2q()
        return self.gate @ rho @ self.gate.conj().T

    def observable(self):
        rho_out = self.forward()
        return torch.real(torch.trace(rho_out @ rho_out))


class TorchCNOT(TorchGate2Q):
    """Family 13."""
    def __init__(self, bloch_A, bloch_B):
        super().__init__(CNOT_NP, bloch_A, bloch_B)


class TorchCZ(TorchGate2Q):
    """Family 14."""
    def __init__(self, bloch_A, bloch_B):
        super().__init__(CZ_NP, bloch_A, bloch_B)


class TorchSWAP(TorchGate2Q):
    """Family 15."""
    def __init__(self, bloch_A, bloch_B):
        super().__init__(SWAP_NP, bloch_A, bloch_B)


class TorchHadamard(nn.Module):
    """Family 16."""
    def __init__(self, bloch):
        super().__init__()
        self.bloch = nn.Parameter(torch.tensor(bloch, dtype=torch.float64))
        self.H = torch.tensor(H_NP, dtype=torch.complex128)

    def forward(self):
        rho = I2_T.clone() / 2
        for i, s in enumerate(PAULIS_T):
            rho = rho + self.bloch[i].to(torch.complex128) * s / 2
        return self.H @ rho @ self.H.conj().T

    def observable(self):
        rho_out = self.forward()
        return torch.real(torch.trace(rho_out @ rho_out))


class TorchTGate(nn.Module):
    """Family 17."""
    def __init__(self, bloch):
        super().__init__()
        self.bloch = nn.Parameter(torch.tensor(bloch, dtype=torch.float64))
        self.T_gate = torch.tensor(T_NP, dtype=torch.complex128)

    def forward(self):
        rho = I2_T.clone() / 2
        for i, s in enumerate(PAULIS_T):
            rho = rho + self.bloch[i].to(torch.complex128) * s / 2
        return self.T_gate @ rho @ self.T_gate.conj().T

    def observable(self):
        rho_out = self.forward()
        return torch.real(torch.trace(rho_out @ rho_out))


class TorchiSWAP(TorchGate2Q):
    """Family 18."""
    def __init__(self, bloch_A, bloch_B):
        super().__init__(ISWAP_NP, bloch_A, bloch_B)


class TorchCartanKAK(nn.Module):
    """Family 19: Cartan KAK decomposition."""
    def __init__(self, abc, bloch_A, bloch_B):
        super().__init__()
        self.abc = nn.Parameter(torch.tensor(abc, dtype=torch.float64))
        self.bloch_A = nn.Parameter(torch.tensor(bloch_A, dtype=torch.float64))
        self.bloch_B = nn.Parameter(torch.tensor(bloch_B, dtype=torch.float64))

    def forward(self):
        rho_A = I2_T.clone() / 2
        rho_B = I2_T.clone() / 2
        for i, s in enumerate(PAULIS_T):
            rho_A = rho_A + self.bloch_A[i].to(torch.complex128) * s / 2
            rho_B = rho_B + self.bloch_B[i].to(torch.complex128) * s / 2
        rho = torch.kron(rho_A, rho_B)
        XX = torch.kron(PAULIS_T[0], PAULIS_T[0])
        YY = torch.kron(PAULIS_T[1], PAULIS_T[1])
        ZZ = torch.kron(PAULIS_T[2], PAULIS_T[2])
        H = self.abc[0].to(torch.complex128) * XX + self.abc[1].to(torch.complex128) * YY + self.abc[2].to(torch.complex128) * ZZ
        evals, evecs = torch.linalg.eigh(H)
        U = evecs @ torch.diag(torch.exp(-1j * evals)) @ evecs.conj().T
        return U @ rho @ U.conj().T

    def observable(self):
        rho_out = self.forward()
        return torch.real(torch.trace(rho_out @ rho_out))


class TorchEigenDecomp(nn.Module):
    """Family 20: eigenvalue decomposition."""
    def __init__(self, bloch):
        super().__init__()
        self.bloch = nn.Parameter(torch.tensor(bloch, dtype=torch.float64))

    def forward(self):
        rho = I2_T.clone() / 2
        for i, s in enumerate(PAULIS_T):
            rho = rho + self.bloch[i].to(torch.complex128) * s / 2
        return torch.linalg.eigvalsh(rho)

    def observable(self):
        evals = self.forward()
        return evals[0]  # Minimum eigenvalue


class TorchHusimiQ(nn.Module):
    """Family 21: Husimi Q function."""
    def __init__(self, bloch, alpha):
        super().__init__()
        self.bloch = nn.Parameter(torch.tensor(bloch, dtype=torch.float64))
        self.alpha = alpha  # complex number

    def forward(self):
        rho = I2_T.clone() / 2
        for i, s in enumerate(PAULIS_T):
            rho = rho + self.bloch[i].to(torch.complex128) * s / 2
        r = abs(self.alpha)
        phi = np.angle(self.alpha)
        psi = torch.tensor([np.cos(r), np.exp(1j * phi) * np.sin(r)], dtype=torch.complex128)
        return torch.real(psi.conj() @ rho @ psi) / np.pi

    def observable(self):
        return self.forward()


class TorchL1Coherence(nn.Module):
    """Family 22: L1 coherence."""
    def __init__(self, bloch):
        super().__init__()
        self.bloch = nn.Parameter(torch.tensor(bloch, dtype=torch.float64))

    def forward(self):
        rho = I2_T.clone() / 2
        for i, s in enumerate(PAULIS_T):
            rho = rho + self.bloch[i].to(torch.complex128) * s / 2
        # Off-diagonal absolute values
        mask = 1.0 - torch.eye(2, dtype=torch.complex128)
        return torch.sum(torch.abs(rho * mask))

    def observable(self):
        return self.forward()


class TorchRECoherence(nn.Module):
    """Family 23: Relative entropy of coherence."""
    def __init__(self, bloch):
        super().__init__()
        self.bloch = nn.Parameter(torch.tensor(bloch, dtype=torch.float64))

    def _von_neumann(self, rho):
        evals = torch.linalg.eigvalsh(rho)
        evals = torch.clamp(evals.real, min=1e-15)
        return -torch.sum(evals * torch.log2(evals + 1e-30))

    def forward(self):
        rho = I2_T.clone() / 2
        for i, s in enumerate(PAULIS_T):
            rho = rho + self.bloch[i].to(torch.complex128) * s / 2
        diag_rho = torch.diag(torch.diag(rho))
        return self._von_neumann(diag_rho) - self._von_neumann(rho)

    def observable(self):
        return self.forward()


class TorchWignerNegativity(nn.Module):
    """Family 24: Wigner negativity proxy."""
    def __init__(self, bloch):
        super().__init__()
        self.bloch = nn.Parameter(torch.tensor(bloch, dtype=torch.float64))

    def forward(self):
        rho = I2_T.clone() / 2
        for i, s in enumerate(PAULIS_T):
            rho = rho + self.bloch[i].to(torch.complex128) * s / 2
        evals = torch.linalg.eigvalsh(rho)
        wigner_vals = 2 * evals.real - 0.5
        neg_mask = (wigner_vals < 0).float()
        return torch.sum(torch.abs(wigner_vals) * neg_mask)

    def observable(self):
        return self.forward()


class TorchHopfConnection(nn.Module):
    """Family 25: Hopf map S3 -> S2."""
    def __init__(self, angles):
        super().__init__()
        # angles = [theta, phi]
        self.angles = nn.Parameter(torch.tensor(angles, dtype=torch.float64))

    def forward(self):
        theta, phi = self.angles[0], self.angles[1]
        psi_0 = torch.cos(theta / 2).to(torch.complex128)
        psi_1 = (torch.exp(1j * phi.to(torch.complex128)) * torch.sin(theta / 2).to(torch.complex128))
        psi = torch.stack([psi_0, psi_1])
        rho = torch.outer(psi, psi.conj())
        bx = 2 * torch.real(rho[0, 1])
        by = 2 * torch.imag(rho[1, 0])
        bz = torch.real(rho[0, 0] - rho[1, 1])
        return torch.stack([bx, by, bz])

    def observable(self):
        b = self.forward()
        return torch.norm(b)  # Should be 1 for pure state


class TorchChiralOverlap(nn.Module):
    """Family 26: Chiral overlap between L and R components."""
    def __init__(self, params):
        super().__init__()
        # params = 4 real numbers -> 2 complex components for psi_L, 2 for psi_R
        self.params = nn.Parameter(torch.tensor(params, dtype=torch.float64))

    def forward(self):
        p = self.params
        psi_L = torch.stack([p[0].to(torch.complex128) + 1j * p[1].to(torch.complex128),
                             torch.tensor(0.0, dtype=torch.complex128)])
        psi_R = torch.stack([torch.tensor(0.0, dtype=torch.complex128),
                             p[2].to(torch.complex128) + 1j * p[3].to(torch.complex128)])
        psi_L = psi_L / torch.norm(psi_L)
        psi_R = psi_R / torch.norm(psi_R)
        overlap = torch.abs(torch.dot(psi_L.conj(), psi_R)) ** 2
        return overlap

    def observable(self):
        return self.forward()


class TorchMutualInformation(nn.Module):
    """Family 27: Mutual information for 2-qubit system."""
    def __init__(self, bloch_A, bloch_B):
        super().__init__()
        self.bloch_A = nn.Parameter(torch.tensor(bloch_A, dtype=torch.float64))
        self.bloch_B = nn.Parameter(torch.tensor(bloch_B, dtype=torch.float64))

    def _von_neumann(self, rho):
        evals = torch.linalg.eigvalsh(rho)
        evals = torch.clamp(evals.real, min=1e-15)
        return -torch.sum(evals * torch.log2(evals + 1e-30))

    def forward(self):
        rho_A = I2_T.clone() / 2
        rho_B = I2_T.clone() / 2
        for i, s in enumerate(PAULIS_T):
            rho_A = rho_A + self.bloch_A[i].to(torch.complex128) * s / 2
            rho_B = rho_B + self.bloch_B[i].to(torch.complex128) * s / 2
        rho_AB = torch.kron(rho_A, rho_B)
        S_A = self._von_neumann(rho_A)
        S_B = self._von_neumann(rho_B)
        S_AB = self._von_neumann(rho_AB)
        return S_A + S_B - S_AB

    def observable(self):
        return self.forward()


class TorchQuantumDiscord(nn.Module):
    """Family 28: Quantum discord (Z-measurement on B)."""
    def __init__(self, bloch_A, bloch_B):
        super().__init__()
        self.bloch_A = nn.Parameter(torch.tensor(bloch_A, dtype=torch.float64))
        self.bloch_B = nn.Parameter(torch.tensor(bloch_B, dtype=torch.float64))

    def _von_neumann(self, rho):
        evals = torch.linalg.eigvalsh(rho)
        evals = torch.clamp(evals.real, min=1e-15)
        return -torch.sum(evals * torch.log2(evals + 1e-30))

    def forward(self):
        rho_A = I2_T.clone() / 2
        rho_B = I2_T.clone() / 2
        for i, s in enumerate(PAULIS_T):
            rho_A = rho_A + self.bloch_A[i].to(torch.complex128) * s / 2
            rho_B = rho_B + self.bloch_B[i].to(torch.complex128) * s / 2
        rho_AB = torch.kron(rho_A, rho_B)
        # MI
        S_A = self._von_neumann(rho_A)
        S_B = self._von_neumann(rho_B)
        S_AB = self._von_neumann(rho_AB)
        mi = S_A + S_B - S_AB
        # Classical correlation J(A|B) via Z-measurement on B
        P0_B = torch.tensor([[1, 0], [0, 0]], dtype=torch.complex128)
        P1_B = torch.tensor([[0, 0], [0, 1]], dtype=torch.complex128)
        P0 = torch.kron(I2_T, P0_B)
        P1 = torch.kron(I2_T, P1_B)
        p0 = torch.real(torch.trace(P0 @ rho_AB))
        p1 = torch.real(torch.trace(P1 @ rho_AB))
        S_cond = torch.tensor(0.0, dtype=torch.float64)
        for p_k, P_k in [(p0, P0), (p1, P1)]:
            if p_k.item() > 1e-12:
                rho_k = P_k @ rho_AB @ P_k / p_k
                # Partial trace over B: contract B indices (axis1=1, axis2=3 in (a,b,a',b') reshape)
                rho_A_k = torch.einsum("ijkj->ik", rho_k.reshape(2, 2, 2, 2))
                S_cond = S_cond + p_k * self._von_neumann(rho_A_k)
        J = S_A - S_cond
        return mi - J

    def observable(self):
        return self.forward()


# =====================================================================
# FAMILY REGISTRY: maps name -> (torch_factory, numpy_observable, param_gen)
# =====================================================================

def build_family_registry(rng):
    """Build a registry mapping family name to factory functions.
    Each entry: (make_torch_module, compute_numpy_observable, gen_params)
    """

    def gen_bloch():
        return random_bloch(rng).tolist()

    def gen_bloch_pair():
        return gen_bloch(), gen_bloch()

    def gen_channel_param():
        return float(rng.uniform(0.05, 0.5))

    registry = OrderedDict()

    # 1. density_matrix
    registry["density_matrix"] = {
        "torch_factory": lambda: TorchDensityMatrix(gen_bloch()),
        "numpy_obs": lambda m: float(np_purity(np_density_matrix(np.array(m.bloch.detach().numpy())))),
        "param_name": "bloch",
    }
    # 2. purification
    registry["purification"] = {
        "torch_factory": lambda: TorchPurification(gen_bloch()),
        "numpy_obs": lambda m: float(np_purification(np.array(m.bloch.detach().numpy()))),
        "param_name": "bloch",
    }
    # 3-10: channels
    def _make_channel_entry(torch_cls, np_fn, name):
        def factory():
            b = gen_bloch()
            p = gen_channel_param()
            return torch_cls(p, b)
        def np_obs(m):
            b = np.array(m.bloch.numpy())
            p = float(m.param.detach().numpy()[0])
            rho = np_density_matrix(b)
            rho_out = np_fn(p, rho)
            return float(np_purity(rho_out))
        return {"torch_factory": factory, "numpy_obs": np_obs, "param_name": "param"}

    registry["z_dephasing"] = _make_channel_entry(TorchZDephasing, np_z_dephasing, "z_dephasing")
    registry["x_dephasing"] = _make_channel_entry(TorchXDephasing, np_x_dephasing, "x_dephasing")
    registry["depolarizing"] = _make_channel_entry(TorchDepolarizing, np_depolarizing, "depolarizing")
    registry["amplitude_damping"] = _make_channel_entry(TorchAmplitudeDamping, np_amplitude_damping, "amplitude_damping")
    registry["phase_damping"] = _make_channel_entry(TorchPhaseDamping, np_phase_damping, "phase_damping")
    registry["bit_flip"] = _make_channel_entry(TorchBitFlip, np_bit_flip, "bit_flip")
    registry["phase_flip"] = _make_channel_entry(TorchPhaseFlip, np_phase_flip, "phase_flip")
    registry["bit_phase_flip"] = _make_channel_entry(TorchBitPhaseFlip, np_bit_phase_flip, "bit_phase_flip")

    # 11. unitary_rotation
    def make_unitary():
        b = gen_bloch()
        theta = float(rng.uniform(0.1, np.pi))
        return TorchUnitaryRotation(theta, b)
    def np_unitary_obs(m):
        b = np.array(m.bloch.numpy())
        theta = float(m.param.detach().numpy()[0])
        rho = np_density_matrix(b)
        rho_out = np_unitary_rotation(theta, 2, rho)
        return float(np_purity(rho_out))
    registry["unitary_rotation"] = {"torch_factory": make_unitary, "numpy_obs": np_unitary_obs, "param_name": "param"}

    # 12. z_measurement
    def make_zmeas():
        return TorchZMeasurement(gen_bloch())
    def np_zmeas_obs(m):
        b = np.array(m.bloch.detach().numpy())
        rho = np_density_matrix(b)
        probs = np_z_measurement(rho)
        return float(probs[0])
    registry["z_measurement"] = {"torch_factory": make_zmeas, "numpy_obs": np_zmeas_obs, "param_name": "bloch"}

    # 13-15, 18: 2-qubit gates
    def _make_gate_entry(torch_cls, np_gate, name):
        def factory():
            bA, bB = gen_bloch_pair()
            return torch_cls(bA, bB)
        def np_obs(m):
            bA = np.array(m.bloch_A.detach().numpy())
            bB = np.array(m.bloch_B.detach().numpy())
            rho_A = np_density_matrix(bA)
            rho_B = np_density_matrix(bB)
            rho_AB = np.kron(rho_A, rho_B)
            rho_out = np_gate_apply_2q(np_gate, rho_AB)
            return float(np_purity(rho_out))
        return {"torch_factory": factory, "numpy_obs": np_obs, "param_name": "bloch_A"}

    registry["CNOT"] = _make_gate_entry(TorchCNOT, CNOT_NP, "CNOT")
    registry["CZ"] = _make_gate_entry(TorchCZ, CZ_NP, "CZ")
    registry["SWAP"] = _make_gate_entry(TorchSWAP, SWAP_NP, "SWAP")
    registry["iSWAP"] = _make_gate_entry(TorchiSWAP, ISWAP_NP, "iSWAP")

    # 16. Hadamard
    def make_hadamard():
        return TorchHadamard(gen_bloch())
    def np_had_obs(m):
        b = np.array(m.bloch.detach().numpy())
        rho = np_density_matrix(b)
        rho_out = np_gate_apply_1q(H_NP, rho)
        return float(np_purity(rho_out))
    registry["Hadamard"] = {"torch_factory": make_hadamard, "numpy_obs": np_had_obs, "param_name": "bloch"}

    # 17. T_gate
    def make_tgate():
        return TorchTGate(gen_bloch())
    def np_tgate_obs(m):
        b = np.array(m.bloch.detach().numpy())
        rho = np_density_matrix(b)
        rho_out = np_gate_apply_1q(T_NP, rho)
        return float(np_purity(rho_out))
    registry["T_gate"] = {"torch_factory": make_tgate, "numpy_obs": np_tgate_obs, "param_name": "bloch"}

    # 19. cartan_kak
    def make_kak():
        bA, bB = gen_bloch_pair()
        abc = [float(rng.uniform(0.1, 1.0)) for _ in range(3)]
        return TorchCartanKAK(abc, bA, bB)
    def np_kak_obs(m):
        bA = np.array(m.bloch_A.detach().numpy())
        bB = np.array(m.bloch_B.detach().numpy())
        abc = m.abc.detach().numpy()
        rho_A = np_density_matrix(bA)
        rho_B = np_density_matrix(bB)
        rho_AB = np.kron(rho_A, rho_B)
        rho_out = np_cartan_kak(abc[0], abc[1], abc[2], rho_AB)
        return float(np_purity(rho_out))
    registry["cartan_kak"] = {"torch_factory": make_kak, "numpy_obs": np_kak_obs, "param_name": "abc"}

    # 20. eigenvalue_decomposition
    def make_eigen():
        return TorchEigenDecomp(gen_bloch())
    def np_eigen_obs(m):
        b = np.array(m.bloch.detach().numpy())
        rho = np_density_matrix(b)
        evals = np_eigenvalue_decomposition(rho)
        return float(evals[0])
    registry["eigenvalue_decomposition"] = {"torch_factory": make_eigen, "numpy_obs": np_eigen_obs, "param_name": "bloch"}

    # 21. husimi_q
    def make_husimi():
        alpha = complex(rng.uniform(-1, 1), rng.uniform(-1, 1))
        return TorchHusimiQ(gen_bloch(), alpha)
    def np_husimi_obs(m):
        b = np.array(m.bloch.detach().numpy())
        rho = np_density_matrix(b)
        return float(np_husimi_q(rho, m.alpha))
    registry["husimi_q"] = {"torch_factory": make_husimi, "numpy_obs": np_husimi_obs, "param_name": "bloch"}

    # 22. l1_coherence
    def make_l1c():
        return TorchL1Coherence(gen_bloch())
    def np_l1c_obs(m):
        b = np.array(m.bloch.detach().numpy())
        rho = np_density_matrix(b)
        return float(np_l1_coherence(rho))
    registry["l1_coherence"] = {"torch_factory": make_l1c, "numpy_obs": np_l1c_obs, "param_name": "bloch"}

    # 23. relative_entropy_coherence
    def make_rec():
        return TorchRECoherence(gen_bloch())
    def np_rec_obs(m):
        b = np.array(m.bloch.detach().numpy())
        rho = np_density_matrix(b)
        return float(np_relative_entropy_coherence(rho))
    registry["relative_entropy_coherence"] = {"torch_factory": make_rec, "numpy_obs": np_rec_obs, "param_name": "bloch"}

    # 24. wigner_negativity
    def make_wigner():
        return TorchWignerNegativity(gen_bloch())
    def np_wigner_obs(m):
        b = np.array(m.bloch.detach().numpy())
        rho = np_density_matrix(b)
        return float(np_wigner_negativity(rho))
    registry["wigner_negativity"] = {"torch_factory": make_wigner, "numpy_obs": np_wigner_obs, "param_name": "bloch"}

    # 25. hopf_connection
    def make_hopf():
        angles = [float(rng.uniform(0.1, np.pi)), float(rng.uniform(0.1, 2 * np.pi))]
        return TorchHopfConnection(angles)
    def np_hopf_obs(m):
        angles = m.angles.detach().numpy()
        bvec = np_hopf_connection(angles[0], angles[1])
        return float(np.linalg.norm(bvec))
    registry["hopf_connection"] = {"torch_factory": make_hopf, "numpy_obs": np_hopf_obs, "param_name": "angles"}

    # 26. chiral_overlap
    def make_chiral():
        params = rng.randn(4).tolist()
        return TorchChiralOverlap(params)
    def np_chiral_obs(m):
        p = m.params.detach().numpy()
        psi_L = np.array([p[0] + 1j * p[1], 0.0], dtype=np.complex128)
        psi_R = np.array([0.0, p[2] + 1j * p[3]], dtype=np.complex128)
        psi_L /= np.linalg.norm(psi_L)
        psi_R /= np.linalg.norm(psi_R)
        return float(np_chiral_overlap(psi_L, psi_R))
    registry["chiral_overlap"] = {"torch_factory": make_chiral, "numpy_obs": np_chiral_obs, "param_name": "params"}

    # 27. mutual_information
    def make_mi():
        bA, bB = gen_bloch_pair()
        return TorchMutualInformation(bA, bB)
    def np_mi_obs(m):
        bA = np.array(m.bloch_A.detach().numpy())
        bB = np.array(m.bloch_B.detach().numpy())
        rho_A = np_density_matrix(bA)
        rho_B = np_density_matrix(bB)
        rho_AB = np.kron(rho_A, rho_B)
        return float(np_mutual_information(rho_AB))
    registry["mutual_information"] = {"torch_factory": make_mi, "numpy_obs": np_mi_obs, "param_name": "bloch_A"}

    # 28. quantum_discord
    def make_discord():
        bA, bB = gen_bloch_pair()
        return TorchQuantumDiscord(bA, bB)
    def np_discord_obs(m):
        bA = np.array(m.bloch_A.detach().numpy())
        bB = np.array(m.bloch_B.detach().numpy())
        rho_A = np_density_matrix(bA)
        rho_B = np_density_matrix(bB)
        rho_AB = np.kron(rho_A, rho_B)
        return float(np_quantum_discord(rho_AB))
    registry["quantum_discord"] = {"torch_factory": make_discord, "numpy_obs": np_discord_obs, "param_name": "bloch_A"}

    return registry


# =====================================================================
# CRITERION 1: Gradient Triviality
# =====================================================================

def test_gradient_triviality(family_name, registry_entry, rng, n_trials=10):
    """Compare autograd gradient vs finite-difference gradient.
    Returns: cosine similarity, magnitude ratio, whether autograd adds value."""
    eps = 1e-5
    results = []

    for trial in range(n_trials):
        module = registry_entry["torch_factory"]()
        param_name = registry_entry["param_name"]
        param = getattr(module, param_name)

        # Autograd gradient
        module.zero_grad()
        try:
            obs = module.observable()
            obs.backward()
            grad_auto = param.grad.detach().numpy().copy()
        except Exception as e:
            results.append({
                "trial": trial, "error": str(e), "autograd_works": False,
            })
            continue

        obs_val = float(obs.item())

        # Finite-difference gradient
        param_np = param.detach().numpy().copy()
        grad_fd = np.zeros_like(param_np)
        for i in range(len(param_np.flat)):
            p_plus = param_np.copy()
            p_minus = param_np.copy()
            p_plus.flat[i] += eps
            p_minus.flat[i] -= eps

            # Reconstruct module with perturbed params (via numpy observable)
            # Create fresh modules
            m_plus = registry_entry["torch_factory"]()
            m_minus = registry_entry["torch_factory"]()
            with torch.no_grad():
                getattr(m_plus, param_name).copy_(torch.tensor(p_plus, dtype=torch.float64))
                getattr(m_minus, param_name).copy_(torch.tensor(p_minus, dtype=torch.float64))
            try:
                obs_plus = float(m_plus.observable().item())
                obs_minus = float(m_minus.observable().item())
            except Exception:
                obs_plus = registry_entry["numpy_obs"](m_plus)
                obs_minus = registry_entry["numpy_obs"](m_minus)
            grad_fd.flat[i] = (obs_plus - obs_minus) / (2 * eps)

        # Cosine similarity
        auto_norm = np.linalg.norm(grad_auto)
        fd_norm = np.linalg.norm(grad_fd)
        if auto_norm > 1e-10 and fd_norm > 1e-10:
            cos_sim = float(np.dot(grad_auto.flat, grad_fd.flat) / (auto_norm * fd_norm))
            mag_ratio = float(auto_norm / fd_norm)
        elif auto_norm < 1e-10 and fd_norm < 1e-10:
            cos_sim = 1.0
            mag_ratio = 1.0
        else:
            cos_sim = 0.0
            mag_ratio = float(auto_norm / (fd_norm + 1e-30))

        max_component_diff = float(np.max(np.abs(grad_auto.flat[:] - grad_fd.flat[:])))

        results.append({
            "trial": trial,
            "obs_value": obs_val,
            "autograd_works": True,
            "cosine_similarity": cos_sim,
            "magnitude_ratio": mag_ratio,
            "max_component_diff": max_component_diff,
            "autograd_norm": float(auto_norm),
            "fd_norm": float(fd_norm),
        })

    # Aggregate
    working = [r for r in results if r.get("autograd_works", False)]
    if not working:
        return {
            "family": family_name,
            "n_trials": n_trials,
            "autograd_failures": len(results),
            "verdict": "AUTOGRAD_FAILED",
            "substrate_matters": False,
        }

    cos_sims = [r["cosine_similarity"] for r in working]
    mag_ratios = [r["magnitude_ratio"] for r in working]
    max_diffs = [r["max_component_diff"] for r in working]

    mean_cos = float(np.mean(cos_sims))
    min_cos = float(np.min(cos_sims))
    mean_mag = float(np.mean(mag_ratios))
    mean_diff = float(np.mean(max_diffs))

    # Gradient is "trivial" if autograd matches FD perfectly
    # (cos_sim > 0.999 and mag_ratio in [0.95, 1.05])
    trivial = min_cos > 0.999 and all(0.95 < mr < 1.05 for mr in mag_ratios)

    # But autograd is CHEAPER (no 2*n forward passes), so even if trivial,
    # check computational cost
    n_params = len(getattr(module, param_name).detach().numpy().flat)
    autograd_cost = 1  # 1 forward + 1 backward ~ 2-3 forward passes
    fd_cost = 2 * n_params  # 2n forward passes

    return {
        "family": family_name,
        "n_trials": n_trials,
        "n_working": len(working),
        "n_params": n_params,
        "mean_cosine_similarity": mean_cos,
        "min_cosine_similarity": min_cos,
        "mean_magnitude_ratio": mean_mag,
        "mean_max_component_diff": mean_diff,
        "gradient_directionally_identical": min_cos > 0.999,
        "gradient_magnitude_identical": all(0.95 < mr < 1.05 for mr in mag_ratios),
        "gradient_trivial": trivial,
        "autograd_cost_relative": autograd_cost,
        "fd_cost_relative": fd_cost,
        "autograd_cheaper": autograd_cost < fd_cost,
        "verdict": "NULL_direction" if trivial else "NON_NULL_direction",
        "substrate_matters_for_gradient": not trivial or (autograd_cost < fd_cost),
        "details": results,
    }


# =====================================================================
# CRITERION 2: Graph Topology Independence
# =====================================================================

TOPOLOGY_FAMILIES = ["density_matrix", "z_dephasing", "CNOT", "mutual_information"]


def test_graph_topology(family_name, registry_entry, rng, n_trials=5):
    """Test whether computational graph topology affects constraint cascade.
    Chain: sequential composition. Star: parallel then merge. Parallel: independent."""

    results = []
    for trial in range(n_trials):
        module = registry_entry["torch_factory"]()
        param_name = registry_entry["param_name"]
        param = getattr(module, param_name)

        # === CHAIN topology: observable -> loss -> gradient ===
        module.zero_grad()
        try:
            obs_chain = module.observable()
            loss_chain = obs_chain ** 2  # Add extra chain link
            loss_chain.backward()
            grad_chain = param.grad.detach().numpy().copy()
            obs_chain_val = float(obs_chain.item())
        except Exception as e:
            results.append({"trial": trial, "error": str(e), "topology_matters": False})
            continue

        # === STAR topology: observable computed via 2 independent paths merged ===
        module.zero_grad()
        try:
            obs1 = module.observable()
        except Exception:
            results.append({"trial": trial, "error": "star forward failed", "topology_matters": False})
            continue
        # Recompute observable from scratch (fresh graph)
        module.zero_grad()
        obs2 = module.observable()
        # Star merge: average of two computations
        obs_star = (obs1 + obs2) / 2
        loss_star = obs_star ** 2
        loss_star.backward()
        grad_star = param.grad.detach().numpy().copy()

        # === PARALLEL topology: Two independent losses, accumulate gradients ===
        module.zero_grad()
        obs_p1 = module.observable()
        loss_p1 = obs_p1 ** 2
        loss_p1.backward(retain_graph=False)
        grad_p1 = param.grad.detach().numpy().copy()

        module.zero_grad()
        obs_p2 = module.observable()
        loss_p2 = obs_p2 ** 2
        loss_p2.backward()
        grad_p2 = param.grad.detach().numpy().copy()
        # Parallel = average of independent gradients
        grad_parallel = (grad_p1 + grad_p2) / 2

        # Compare: chain gradient direction vs star vs parallel
        def cosine_sim(a, b):
            na, nb = np.linalg.norm(a), np.linalg.norm(b)
            if na < 1e-10 or nb < 1e-10:
                return 1.0 if (na < 1e-10 and nb < 1e-10) else 0.0
            return float(np.dot(a.flat, b.flat) / (na * nb))

        # Chain vs Star: star gradient should be grad_chain (since obs is deterministic)
        # The real test: does the GRAPH STRUCTURE change the DIRECTION?
        cs_chain_star = cosine_sim(grad_chain, grad_star)
        cs_chain_parallel = cosine_sim(grad_chain, grad_parallel)
        cs_star_parallel = cosine_sim(grad_star, grad_parallel)

        # For a deterministic function, all three should agree perfectly
        all_agree = (cs_chain_star > 0.999 and cs_chain_parallel > 0.999)

        results.append({
            "trial": trial,
            "obs_value": obs_chain_val,
            "cos_chain_vs_star": cs_chain_star,
            "cos_chain_vs_parallel": cs_chain_parallel,
            "cos_star_vs_parallel": cs_star_parallel,
            "all_topologies_agree": all_agree,
        })

    working = [r for r in results if "cos_chain_vs_star" in r]
    if not working:
        return {
            "family": family_name,
            "tested": family_name in TOPOLOGY_FAMILIES,
            "verdict": "FAILED_TO_TEST",
            "topology_matters": False,
        }

    all_agree = all(r["all_topologies_agree"] for r in working)
    mean_cs = float(np.mean([r["cos_chain_vs_star"] for r in working]))

    return {
        "family": family_name,
        "tested": True,
        "n_trials": len(working),
        "all_topologies_agree": all_agree,
        "mean_cos_chain_vs_star": mean_cs,
        "verdict": "NULL_topology" if all_agree else "NON_NULL_topology",
        "topology_matters": not all_agree,
        "details": results,
    }


# =====================================================================
# CRITERION 3: Forward Sufficiency
# =====================================================================

def test_forward_sufficiency(family_name, registry_entry, rng, n_candidates=50, n_survivors=5):
    """Compare forward-only rejection sampling vs backward-pass selection.
    Forward: generate candidates, pick top-k by observable.
    Backward: gradient descent toward observable extremum."""

    results = {}

    # Forward-only: generate n_candidates, pick top n_survivors
    t0 = time.perf_counter()
    forward_obs = []
    forward_params = []
    for _ in range(n_candidates):
        m = registry_entry["torch_factory"]()
        try:
            obs_val = float(m.observable().item())
        except Exception:
            continue
        forward_obs.append(obs_val)
        param = getattr(m, registry_entry["param_name"])
        forward_params.append(param.detach().numpy().copy())
    t_forward = time.perf_counter() - t0

    if len(forward_obs) < n_survivors:
        return {
            "family": family_name,
            "verdict": "INSUFFICIENT_CANDIDATES",
            "forward_sufficiency": None,
        }

    # Sort by observable (descending -- maximize)
    sorted_idx = np.argsort(forward_obs)[::-1]
    forward_survivors = [forward_obs[i] for i in sorted_idx[:n_survivors]]
    forward_best = forward_survivors[0]

    # Backward: start from median candidate, gradient ascent for n_candidates steps
    t0 = time.perf_counter()
    median_idx = sorted_idx[len(sorted_idx) // 2]
    m_opt = registry_entry["torch_factory"]()
    param = getattr(m_opt, registry_entry["param_name"])
    with torch.no_grad():
        param.copy_(torch.tensor(forward_params[median_idx], dtype=torch.float64))

    lr = 0.01
    backward_trajectory = []
    for step in range(n_candidates):
        m_opt.zero_grad()
        try:
            obs = m_opt.observable()
            (-obs).backward()  # Negate for gradient ascent
        except Exception:
            break
        with torch.no_grad():
            param.data += lr * param.grad
        backward_trajectory.append(float(obs.item()))
    t_backward = time.perf_counter() - t0

    backward_best = max(backward_trajectory) if backward_trajectory else float("-inf")

    # Compare
    forward_flops = n_candidates  # Each is 1 forward pass
    backward_flops = n_candidates * 2  # Each step is forward + backward ~ 2 forward

    results = {
        "family": family_name,
        "n_candidates": n_candidates,
        "n_survivors": n_survivors,
        "forward_best_obs": float(forward_best),
        "backward_best_obs": float(backward_best),
        "backward_beats_forward": backward_best > forward_best + 1e-8,
        "forward_time_s": t_forward,
        "backward_time_s": t_backward,
        "forward_flops_relative": forward_flops,
        "backward_flops_relative": backward_flops,
        "backward_cheaper": t_backward < t_forward,
        "same_precision": abs(forward_best - backward_best) < 1e-4,
        "verdict": "NULL_forward_sufficient" if (backward_best <= forward_best + 1e-8) else "NON_NULL_backward_superior",
        "substrate_matters_for_selection": backward_best > forward_best + 1e-8,
    }
    return results


# =====================================================================
# CRITERION 4: Substrate Equivalence
# =====================================================================

def test_substrate_equivalence(family_name, registry_entry, rng, n_states=100):
    """Compute key observable via torch and numpy on n_states random states.
    Measure max absolute difference."""

    diffs = []
    torch_vals = []
    numpy_vals = []

    for _ in range(n_states):
        m = registry_entry["torch_factory"]()
        try:
            t_val = float(m.observable().item())
            n_val = registry_entry["numpy_obs"](m)
        except Exception as e:
            continue
        diffs.append(abs(t_val - n_val))
        torch_vals.append(t_val)
        numpy_vals.append(n_val)

    if not diffs:
        return {
            "family": family_name,
            "verdict": "FAILED_TO_COMPUTE",
            "substrate_equivalent": None,
        }

    max_diff = float(max(diffs))
    mean_diff = float(np.mean(diffs))
    median_diff = float(np.median(diffs))

    # Threshold: < 1e-6 means effectively identical
    substrate_equivalent = max_diff < 1e-6

    return {
        "family": family_name,
        "n_states": len(diffs),
        "max_abs_diff": max_diff,
        "mean_abs_diff": mean_diff,
        "median_abs_diff": median_diff,
        "torch_mean": float(np.mean(torch_vals)),
        "numpy_mean": float(np.mean(numpy_vals)),
        "substrate_equivalent": substrate_equivalent,
        "verdict": "NULL_equivalent" if substrate_equivalent else "NON_NULL_divergent",
    }


# =====================================================================
# MAIN ORCHESTRATION
# =====================================================================

def run_all_tests():
    rng = np.random.RandomState(42)
    baseline_sanity = test_random_2q_density_baseline(np.random.RandomState(1234))
    registry = build_family_registry(rng)
    family_names = list(registry.keys())

    print(f"Phase 7 Baseline Validation: {len(family_names)} families")
    print("=" * 70)
    print(f"2q baseline sanity: {baseline_sanity['verdict']}")

    all_results = OrderedDict()
    criterion_summary = {
        "C1_gradient_triviality": {},
        "C2_graph_topology": {},
        "C3_forward_sufficiency": {},
        "C4_substrate_equivalence": {},
    }

    for i, fname in enumerate(family_names):
        print(f"\n[{i+1:2d}/28] {fname}")
        entry = registry[fname]
        family_result = {}

        # C1: Gradient triviality
        print(f"  C1: gradient triviality...", end=" ", flush=True)
        c1 = test_gradient_triviality(fname, entry, rng)
        family_result["C1_gradient_triviality"] = c1
        criterion_summary["C1_gradient_triviality"][fname] = c1.get("verdict", "UNKNOWN")
        print(c1.get("verdict", "?"))

        # C2: Graph topology (only for subset)
        if fname in TOPOLOGY_FAMILIES:
            print(f"  C2: graph topology...", end=" ", flush=True)
            c2 = test_graph_topology(fname, entry, rng)
            family_result["C2_graph_topology"] = c2
            criterion_summary["C2_graph_topology"][fname] = c2.get("verdict", "UNKNOWN")
            print(c2.get("verdict", "?"))
        else:
            family_result["C2_graph_topology"] = {"tested": False, "reason": "not in topology subset"}
            criterion_summary["C2_graph_topology"][fname] = "NOT_TESTED"

        # C3: Forward sufficiency
        print(f"  C3: forward sufficiency...", end=" ", flush=True)
        c3 = test_forward_sufficiency(fname, entry, rng)
        family_result["C3_forward_sufficiency"] = c3
        criterion_summary["C3_forward_sufficiency"][fname] = c3.get("verdict", "UNKNOWN")
        print(c3.get("verdict", "?"))

        # C4: Substrate equivalence
        print(f"  C4: substrate equivalence...", end=" ", flush=True)
        c4 = test_substrate_equivalence(fname, entry, rng)
        family_result["C4_substrate_equivalence"] = c4
        criterion_summary["C4_substrate_equivalence"][fname] = c4.get("verdict", "UNKNOWN")
        print(c4.get("verdict", "?"))

        all_results[fname] = family_result

    # =====================================================================
    # OVERALL VERDICT
    # =====================================================================

    print("\n" + "=" * 70)
    print("OVERALL ANALYSIS")
    print("=" * 70)

    # Count nulls vs non-nulls per criterion
    verdict_counts = {}
    for crit_name, crit_results in criterion_summary.items():
        nulls = sum(1 for v in crit_results.values() if "NULL" in v and "NON_NULL" not in v)
        non_nulls = sum(1 for v in crit_results.values() if "NON_NULL" in v)
        not_tested = sum(1 for v in crit_results.values() if v in ("NOT_TESTED", "UNKNOWN", "FAILED_TO_TEST"))
        verdict_counts[crit_name] = {
            "null_count": nulls,
            "non_null_count": non_nulls,
            "not_tested": not_tested,
            "total": len(crit_results),
        }
        print(f"  {crit_name}: {nulls} null, {non_nulls} non-null, {not_tested} not tested")

    # Per-family summary: which criteria show null vs non-null?
    family_verdicts = {}
    for fname in family_names:
        fv = {}
        for crit in ["C1_gradient_triviality", "C2_graph_topology", "C3_forward_sufficiency", "C4_substrate_equivalence"]:
            v = criterion_summary[crit].get(fname, "NOT_TESTED")
            fv[crit] = v
        # Does substrate matter for this family?
        non_null_criteria = [c for c, v in fv.items() if "NON_NULL" in v]
        null_criteria = [c for c, v in fv.items() if "NULL" in v and "NON_NULL" not in v]
        fv["non_null_criteria"] = non_null_criteria
        fv["null_criteria"] = null_criteria
        fv["substrate_matters"] = len(non_null_criteria) > 0
        family_verdicts[fname] = fv

    # Overall: is the PyTorch claim falsified?
    any_non_null = any(fv["substrate_matters"] for fv in family_verdicts.values())
    all_null = not any_non_null

    # Which structural features predict sensitivity?
    sensitive_families = [f for f, fv in family_verdicts.items() if fv["substrate_matters"]]
    insensitive_families = [f for f, fv in family_verdicts.items() if not fv["substrate_matters"]]

    # Classify: what kind of families are sensitive?
    # 1q vs 2q, channel vs gate vs observable
    def classify_family(fname):
        if fname in ("CNOT", "CZ", "SWAP", "iSWAP", "cartan_kak", "mutual_information", "quantum_discord"):
            return "2q"
        return "1q"

    sensitive_1q = [f for f in sensitive_families if classify_family(f) == "1q"]
    sensitive_2q = [f for f in sensitive_families if classify_family(f) == "2q"]

    overall_verdict = {
        "pytorch_claim_falsified": all_null,
        "any_family_shows_divergence": any_non_null,
        "n_sensitive_families": len(sensitive_families),
        "n_insensitive_families": len(insensitive_families),
        "sensitive_families": sensitive_families,
        "insensitive_families": insensitive_families,
        "sensitive_1q": sensitive_1q,
        "sensitive_2q": sensitive_2q,
        "interpretation": (
            "All currently tested criteria show null on their covered families. "
            "This is only a provisional falsification signal because C2 graph-topology "
            "coverage remains limited to the topology subset."
        ) if all_null else (
            f"{len(sensitive_families)} families show substrate sensitivity. "
            f"PyTorch provides value beyond numpy for: {', '.join(sensitive_families)}. "
            f"C2 graph-topology coverage currently spans {len(TOPOLOGY_FAMILIES)} families. "
            f"Structural features: "
            f"{'2q families overrepresented' if len(sensitive_2q) > len(sensitive_1q) else '1q families overrepresented' if len(sensitive_1q) > len(sensitive_2q) else 'balanced'}."
        ),
    }

    if all_null:
        print("\n  VERDICT: PyTorch claim FALSIFIED -- numpy is sufficient")
    else:
        print(f"\n  VERDICT: {len(sensitive_families)}/28 families show substrate sensitivity")
        print(f"  Sensitive: {', '.join(sensitive_families)}")

    return {
        "name": "phase7_baseline_validation",
        "phase": "Phase 7",
        "description": "Systematic falsification protocol: 28 families; C1/C3/C4 full coverage, C2 graph-topology currently limited to a topology subset",
        "date": "2026-04-07",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "baseline_sanity": baseline_sanity,
        "n_families": len(family_names),
        "families_tested": family_names,
        "criterion_summary": verdict_counts,
        "family_verdicts": family_verdicts,
        "overall_verdict": overall_verdict,
        "per_family_details": all_results,
        "classification": "canonical",
    }


# =====================================================================
# ENTRY POINT
# =====================================================================

if __name__ == "__main__":
    results = run_all_tests()

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "phase7_baseline_validation_results.json")

    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nResults written to {out_path}")

    # Quick stats
    ov = results["overall_verdict"]
    print(f"\nFINAL: falsified={ov['pytorch_claim_falsified']}, "
          f"sensitive={ov['n_sensitive_families']}/28, "
          f"insensitive={ov['n_insensitive_families']}/28")
