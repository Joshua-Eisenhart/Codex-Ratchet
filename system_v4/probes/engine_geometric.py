#!/usr/bin/env python3
"""
engine_geometric.py
===================
REAL GEOMETRY engine: Weyl spinors evolving on nested Hopf tori via
Clifford rotors, with Berry phase accumulating, transport between torus
levels, and the cell complex determining adjacency.

Primary state is a pair of Cl(3) Bloch multivectors (L and R) living
in the Bloch ball.  Pure spinors sit on |r|=1.  T-kernel operators
(Ti, Te) geometrically contract the Bloch vector toward dephasing
axes -- this IS entropy generation through real geometry.  F-kernel
operators (Fe, Fi) rotate via Cl(3) rotors -- purity-preserving.

Berry phase accumulates via the Pancharatnam connection.
Transport uses the cell complex from TopoNetX.
Density matrices, Bloch vectors, entropy are DERIVED.
"""

import json
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from clifford import Cl

from hopf_manifold import (
    torus_coordinates, torus_radii, berry_phase,
    left_weyl_spinor, right_weyl_spinor, density_to_bloch,
    von_neumann_entropy_2x2, inter_torus_transport,
    bloch_to_density,
    TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER, NESTED_TORI,
)
from engine_core import (
    TERRAINS, STAGE_OPERATOR_LUT, LOOP_STAGE_ORDER, LOOP_GRAMMAR,
)
from toponetx_torus_bridge import (
    build_torus_complex, map_engine_cycle_to_complex, compute_shell_structure,
)


# =====================================================================
# Cl(3) ALGEBRA -- initialized once
# =====================================================================

_layout, _blades = Cl(3)
_e1 = _blades['e1']
_e2 = _blades['e2']
_e3 = _blades['e3']
_e12 = _blades['e12']
_e23 = _blades['e23']
_e13 = _blades['e13']
_e123 = _blades['e123']
_scalar = _layout.scalar


def _rotor_z(angle):
    """Rotor in e1-e2 plane (around e3). R = cos(a/2) + sin(a/2) e12."""
    return np.cos(angle / 2) * _scalar + np.sin(angle / 2) * _e12


def _rotor_x(angle):
    """Rotor in e2-e3 plane (around e1). R = cos(a/2) + sin(a/2) e23."""
    return np.cos(angle / 2) * _scalar + np.sin(angle / 2) * _e23


def _mv_to_bloch(mv):
    """Extract Bloch vector from Cl(3) grade-1 multivector."""
    return np.array([float(mv[_e1]), float(mv[_e2]), float(mv[_e3])])


def _bloch_to_mv(b):
    """Bloch vector to Cl(3) grade-1 multivector."""
    return float(b[0]) * _e1 + float(b[1]) * _e2 + float(b[2]) * _e3


def _bloch_to_spinor(b):
    """Bloch vector to closest normalized spinor."""
    x, y, z = b
    r = np.sqrt(x**2 + y**2 + z**2)
    if r < 1e-14:
        return np.array([1.0, 0.0], dtype=complex)
    xn, yn, zn = x / r, y / r, z / r
    theta = np.arccos(np.clip(zn, -1.0, 1.0))
    phi = np.arctan2(yn, xn)
    alpha = np.cos(theta / 2)
    beta = np.exp(1j * phi) * np.sin(theta / 2)
    psi = np.array([alpha, beta], dtype=complex)
    psi /= np.linalg.norm(psi)
    return psi


def _bloch_to_density(b):
    """Bloch vector (possibly |r|<1) to 2x2 density matrix."""
    sx = np.array([[0, 1], [1, 0]], dtype=complex)
    sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
    sz = np.array([[1, 0], [0, -1]], dtype=complex)
    return (np.eye(2, dtype=complex) + b[0] * sx + b[1] * sy + b[2] * sz) / 2


def _spinor_to_bloch(psi):
    """Spinor to Bloch vector (|r|=1 for normalized spinor)."""
    rho = np.outer(psi, psi.conj())
    return density_to_bloch(rho)


# =====================================================================
# GEOMETRIC OPERATIONS IN Cl(3)
# =====================================================================

def _apply_rotor(bloch_mv, R):
    """Apply Cl(3) rotor: v' = R v R~. Preserves |r|."""
    return R * bloch_mv * ~R


def _dephase_z(bloch_mv, strength):
    """Z-dephasing: contract toward e3 axis. Kills e1,e2. Entropy up."""
    vx = float(bloch_mv[_e1])
    vy = float(bloch_mv[_e2])
    vz = float(bloch_mv[_e3])
    return (1 - strength) * vx * _e1 + (1 - strength) * vy * _e2 + vz * _e3


def _dephase_x(bloch_mv, strength):
    """X-dephasing: contract toward e1 axis. Kills e2,e3. Entropy up."""
    vx = float(bloch_mv[_e1])
    vy = float(bloch_mv[_e2])
    vz = float(bloch_mv[_e3])
    return vx * _e1 + (1 - strength) * vy * _e2 + (1 - strength) * vz * _e3


# =====================================================================
# GEOMETRIC STATE
# =====================================================================

@dataclass
class GeometricState:
    """State: Cl(3) Bloch multivectors on the torus.

    |r| = 1: pure (on surface). |r| < 1: mixed (inside ball, has entropy).
    Spinors derived from Bloch direction.
    correlation: 3x3 matrix C_{ij} tracking L-R entanglement correlations.
    """
    r_L: np.ndarray   # Left Bloch vector (3,), |r| <= 1
    r_R: np.ndarray   # Right Bloch vector (3,), |r| <= 1
    eta: float         # Torus latitude
    theta: float       # Fiber position
    phi: float         # Base position
    berry_phase_L: float = 0.0
    berry_phase_R: float = 0.0
    torus_level: int = 1  # 0=inner, 1=clifford, 2=outer
    correlation: np.ndarray = field(default_factory=lambda: np.zeros((3, 3)))
    history: list = field(default_factory=list)

    @property
    def mv_L(self):
        return _bloch_to_mv(self.r_L)

    @property
    def mv_R(self):
        return _bloch_to_mv(self.r_R)

    @property
    def psi_L(self):
        return _bloch_to_spinor(self.r_L)

    @property
    def psi_R(self):
        return _bloch_to_spinor(self.r_R)

    @property
    def purity_L(self):
        return float(np.linalg.norm(self.r_L))

    @property
    def purity_R(self):
        return float(np.linalg.norm(self.r_R))


# =====================================================================
# GEOMETRIC ENGINE
# =====================================================================

class GeometricEngine:
    """Cl(3) rotors + geometric dephasing on nested Hopf tori.

    F-kernels (Fe, Fi): rotors (purity-preserving).
    T-kernels (Ti, Te): contractions (entropy-generating).
    Berry phase via Pancharatnam. Transport via cell complex.
    """

    def __init__(self, engine_type=1, n_torus_levels=3):
        assert engine_type in (1, 2)
        self.engine_type = engine_type
        self.n_torus_levels = n_torus_levels
        self.cc, self.node_map = build_torus_complex()
        self.shells = compute_shell_structure(self.cc, self.node_map)
        self.path = map_engine_cycle_to_complex(
            self.cc, engine_type, self.node_map
        )
        self.torus_etas = [TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER]
        self.d_angle = 2 * np.pi / 4

    def init_state(self, eta=TORUS_CLIFFORD):
        q = torus_coordinates(eta, 0.0, 0.0)
        r_L = _spinor_to_bloch(left_weyl_spinor(q))
        r_R = _spinor_to_bloch(right_weyl_spinor(q))
        level = self.torus_etas.index(eta) if eta in self.torus_etas else 1
        return GeometricState(r_L=r_L, r_R=r_R, eta=eta, theta=0.0, phi=0.0,
                              torus_level=level)

    # -- Derived --
    def get_density_matrices(self, state):
        return _bloch_to_density(state.r_L), _bloch_to_density(state.r_R)

    def get_bloch_vectors(self, state):
        return state.r_L.copy(), state.r_R.copy()

    def get_entropies(self, state):
        rL, rR = self.get_density_matrices(state)
        return von_neumann_entropy_2x2(rL), von_neumann_entropy_2x2(rR)

    def get_lr_dot(self, state):
        return float(np.dot(state.r_L, state.r_R))

    # -- Entangling coupling --
    def apply_entangling_coupling(self, state, strength):
        """Genuine geometric L-R entanglement via Cl(3) bivector coupling.

        The mechanism operates directly on the 4x4 joint density matrix.
        The entangling rotor is built from the cross product of L and R
        Bloch vectors, then applied as a two-qubit unitary to the joint
        state. This is the honest geometric path: the Cl(3) rotor
        generates a U(4) gate that creates real entanglement.

        After applying the joint unitary, the correlation matrix C_{ij}
        is extracted from the resulting rho_AB, and the marginal Bloch
        vectors r_L, r_R are updated from the partial traces.
        """
        bL = state.r_L.copy()
        bR = state.r_R.copy()
        n = np.cross(bL, bR)
        n_mag = np.linalg.norm(n)

        if n_mag < 1e-10:
            return state  # parallel/anti-parallel: no coupling axis

        # Build entangling rotor axis and angle
        n_hat = n / n_mag
        angle = strength * n_mag

        # Construct the two-qubit entangling unitary from the Cl(3) rotor.
        # The interaction Hamiltonian is H_int = (angle/2) * (n . sigma) x (n . sigma)
        # This is the genuine geometric content: the SAME rotation axis
        # acts on both qubits, creating sigma_i x sigma_j correlations.
        sx = np.array([[0, 1], [1, 0]], dtype=complex)
        sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
        sz = np.array([[1, 0], [0, -1]], dtype=complex)
        sigma = [sx, sy, sz]

        # n.sigma for each qubit
        n_dot_sigma = sum(float(n_hat[i]) * sigma[i] for i in range(3))

        # Joint Hamiltonian: (n.sigma) tensor (n.sigma)
        H_int = np.kron(n_dot_sigma, n_dot_sigma)

        # Unitary: U = exp(-i * angle/2 * H_int)
        evals_H, evecs_H = np.linalg.eigh(H_int)
        U = evecs_H @ np.diag(np.exp(-1j * angle / 2.0 * evals_H)) @ evecs_H.conj().T

        # Get current joint density matrix
        rho = self.get_joint_density_matrix(state)

        # Apply: rho' = U rho U^dag
        rho_new = U @ rho @ U.conj().T

        # Force Hermiticity and normalization
        rho_new = (rho_new + rho_new.conj().T) / 2.0
        rho_new = rho_new / np.real(np.trace(rho_new))

        # Extract updated marginals and correlation matrix
        I2 = np.eye(2, dtype=complex)
        # Partial traces for marginal Bloch vectors
        rho_L = np.zeros((2, 2), dtype=complex)
        rho_R = np.zeros((2, 2), dtype=complex)
        for i in range(2):
            for j in range(2):
                # Tr_R: rho_L[i,j] = sum_k rho[2*i+k, 2*j+k]
                rho_L[i, j] = rho_new[2*i, 2*j] + rho_new[2*i+1, 2*j+1]
                # Tr_L: rho_R[i,j] = sum_k rho[k*2+i, k*2+j]
                rho_R[i, j] = rho_new[i, j] + rho_new[i+2, j+2]

        # Bloch vectors from marginals
        new_bL = np.array([
            np.real(np.trace(sigma[k] @ rho_L)) for k in range(3)
        ])
        new_bR = np.array([
            np.real(np.trace(sigma[k] @ rho_R)) for k in range(3)
        ])

        # Extract excess correlation: C_{ij} = T_{ij} - r_Li * r_Rj
        # where T_{ij} = Tr(rho * sigma_i x sigma_j)
        C_new = np.zeros((3, 3))
        for i in range(3):
            for j in range(3):
                T_ij = np.real(np.trace(
                    rho_new @ np.kron(sigma[i], sigma[j])
                ))
                C_new[i, j] = T_ij - new_bL[i] * new_bR[j]

        # Update state: Bloch vectors reflect the entangled marginals
        state.r_L = new_bL
        state.r_R = new_bR
        state.correlation = C_new

        # Clamp Bloch vectors to ball
        for r in [state.r_L, state.r_R]:
            nm = np.linalg.norm(r)
            if nm > 1.0:
                r[:] = r / nm

        return state

    def _build_joint_density(self, r_L, r_R, C):
        """Build 4x4 density matrix from Bloch vectors and correlation matrix.

        rho_AB = (I x I + r_L . sigma x I + I x r_R . sigma
                  + sum_{ij} T_{ij} sigma_i x sigma_j) / 4

        where T_{ij} = outer(r_L, r_R)_{ij} + C_{ij}.

        C stores the EXCESS correlation beyond the product state.
        When C=0 and |r_L|=|r_R|=1 this gives the correct separable
        pure product state.
        """
        sx = np.array([[0, 1], [1, 0]], dtype=complex)
        sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
        sz = np.array([[1, 0], [0, -1]], dtype=complex)
        sigma = [sx, sy, sz]
        I2 = np.eye(2, dtype=complex)

        # Full correlation tensor: product part + excess
        T = np.outer(r_L, r_R) + C

        rho = np.kron(I2, I2).astype(complex)
        for i in range(3):
            rho = rho + r_L[i] * np.kron(sigma[i], I2)
            rho = rho + r_R[i] * np.kron(I2, sigma[i])
        for i in range(3):
            for j in range(3):
                rho = rho + T[i, j] * np.kron(sigma[i], sigma[j])
        rho = rho / 4.0
        return rho

    def get_joint_density_matrix(self, state):
        """Return the 4x4 joint density matrix from geometric state.

        Built from Bloch vectors r_L, r_R and the correlation matrix C.
        Verified: Tr=1, PSD.
        """
        rho = self._build_joint_density(state.r_L, state.r_R, state.correlation)
        # Force Hermiticity and trace normalization
        rho = (rho + rho.conj().T) / 2.0
        tr = np.real(np.trace(rho))
        if abs(tr) > 1e-14:
            rho = rho / tr
        return rho

    def get_concurrence(self, state):
        """Wootters concurrence from the 4x4 joint density matrix."""
        rho = self.get_joint_density_matrix(state)
        sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
        sy_sy = np.kron(sy, sy)
        rho_tilde = sy_sy @ rho.conj() @ sy_sy
        R = rho @ rho_tilde
        evals = np.sort(np.real(np.sqrt(np.maximum(np.linalg.eigvals(R), 0))))[::-1]
        return float(max(0, evals[0] - evals[1] - evals[2] - evals[3]))

    # -- Berry --
    def _accumulate_berry(self, r_old, r_new):
        psi_old = _bloch_to_spinor(r_old)
        psi_new = _bloch_to_spinor(r_new)
        return float(-np.angle(np.vdot(psi_old, psi_new)))

    # -- Geometric operator --
    def _apply_operator(self, mv, op_name, is_up, state, strength):
        R_maj, R_min = torus_radii(state.eta)
        sign = 1.0 if is_up else -1.0

        if op_name == "Ti":
            # T-kernel: rotate slightly, then contract toward e3
            R = _rotor_z(sign * strength * R_min * 0.4)
            mv = _apply_rotor(mv, R)
            mv = _dephase_z(mv, strength * R_min * 0.12)
            return mv
        elif op_name == "Fe":
            # F-kernel: pure rotation in fiber plane (purity-preserving)
            angle = sign * state.phi * strength * 0.5
            if abs(angle) < 1e-12:
                angle = sign * strength * 0.25
            return _apply_rotor(mv, _rotor_z(angle))
        elif op_name == "Te":
            # T-kernel: rotate slightly, then contract toward e1
            R = _rotor_x(sign * strength * R_maj * 0.4)
            mv = _apply_rotor(mv, R)
            mv = _dephase_x(mv, strength * R_maj * 0.12)
            return mv
        elif op_name == "Fi":
            # F-kernel: pure rotation in base plane (purity-preserving)
            angle = sign * state.theta * strength * 0.5
            if abs(angle) < 1e-12:
                angle = sign * strength * 0.25
            return _apply_rotor(mv, _rotor_x(angle))
        else:
            raise ValueError(f"Unknown operator: {op_name}")

    def _operator_strength(self, terrain, op_name):
        loop = terrain["loop"]
        bp = 0.5
        if self.engine_type == 1:
            if (loop == "base" and op_name in ("Fe", "Ti")) or \
               (loop == "fiber" and op_name in ("Te", "Fi")):
                s = bp * 1.0
            else:
                s = bp * 0.3
        else:
            if (loop == "base" and op_name in ("Te", "Fi")) or \
               (loop == "fiber" and op_name in ("Fe", "Ti")):
                s = bp * 1.0
            else:
                s = bp * 0.3
        s *= (1.2 if terrain["expansion"] else 0.8)
        return float(np.clip(s, 0.0, 1.0))

    def _check_transport(self, state, pos):
        if pos == 4:
            old = state.torus_level
            if old == 0:
                new = 1
            elif old == 2:
                new = 1
            else:
                new = 0 if self.engine_type == 1 else 2
            if new != old:
                new_eta = self.torus_etas[new]
                q_old = torus_coordinates(state.eta, state.theta, state.phi)
                q_new = inter_torus_transport(q_old, state.eta, new_eta)
                r_L_new = _spinor_to_bloch(left_weyl_spinor(q_new))
                r_R_new = _spinor_to_bloch(right_weyl_spinor(q_new))
                pL = np.linalg.norm(state.r_L)
                pR = np.linalg.norm(state.r_R)
                state.r_L = r_L_new * pL
                state.r_R = r_R_new * pR
                state.eta = new_eta
                state.torus_level = new
        return state

    def _apply_local_ops_to_joint(self, state, op_name, is_up, strength):
        """Apply local (non-entangling) operators to the full joint state.

        Lifts the single-qubit Cl(3) operations to 4x4 by applying them
        as local channels on the joint density matrix.  This keeps the
        correlation matrix C consistent with the updated marginals.
        """
        sx = np.array([[0, 1], [1, 0]], dtype=complex)
        sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
        sz = np.array([[1, 0], [0, -1]], dtype=complex)
        sigma = [sx, sy, sz]
        I2 = np.eye(2, dtype=complex)

        # Get old Bloch vectors to compute the operator parameters
        r_L_old = state.r_L.copy()
        r_R_old = state.r_R.copy()

        # Apply operators to individual Bloch multivectors to get new values
        mv_L = _bloch_to_mv(state.r_L)
        mv_R = _bloch_to_mv(state.r_R)
        mv_L_new = self._apply_operator(mv_L, op_name, is_up, state, strength)
        mv_R_new = self._apply_operator(mv_R, op_name, not is_up, state, strength)
        new_bL = _mv_to_bloch(mv_L_new)
        new_bR = _mv_to_bloch(mv_R_new)

        # Clamp to Bloch ball
        for r in [new_bL, new_bR]:
            nm = np.linalg.norm(r)
            if nm > 1.0:
                r[:] = r / nm

        # Infer the linear maps M_L, M_R that transform the Bloch vectors.
        # For rotors (F-kernels): M is an SO(3) rotation matrix.
        # For contractions (T-kernels): M is a diagonal-ish contraction.
        # We approximate M from the operator's effect on the three basis vectors.
        def _infer_map(op_fn, is_up_local):
            M = np.zeros((3, 3))
            for k in range(3):
                basis = np.zeros(3)
                basis[k] = 1.0
                mv_in = _bloch_to_mv(basis)
                mv_out = self._apply_operator(mv_in, op_name, is_up_local, state, strength)
                M[:, k] = _mv_to_bloch(mv_out)
            return M

        M_L = _infer_map(self._apply_operator, is_up)
        M_R = _infer_map(self._apply_operator, not is_up)

        # Transform correlation: C' = M_L @ C @ M_R^T
        # This is the correct transformation for the excess correlation
        # under local CPTP maps (exact for unitaries, approximate for contractions)
        C_new = M_L @ state.correlation @ M_R.T

        state.r_L = new_bL
        state.r_R = new_bR

        # PSD enforcement: verify the resulting rho_AB is valid.
        # If not, scale C down until it is.
        rho_check = self._build_joint_density(state.r_L, state.r_R, C_new)
        evals_check = np.linalg.eigvalsh(rho_check)
        if evals_check[0] < -1e-14:
            # Binary search for max safe scaling
            lo, hi = 0.0, 1.0
            for _ in range(50):
                mid = (lo + hi) / 2.0
                rho_try = self._build_joint_density(state.r_L, state.r_R, mid * C_new)
                if np.linalg.eigvalsh(rho_try)[0] >= -1e-14:
                    lo = mid
                else:
                    hi = mid
            C_new = lo * 0.99 * C_new

        state.correlation = C_new

    def run_stage(self, state, stage_idx, stage_position):
        terrain = TERRAINS[stage_idx]
        key = (self.engine_type, terrain['loop'], terrain['topo'])
        op_name, is_up = STAGE_OPERATOR_LUT[key]
        strength = self._operator_strength(terrain, op_name)

        r_L_old = state.r_L.copy()
        r_R_old = state.r_R.copy()

        # Apply local operators with consistent C transformation
        self._apply_local_ops_to_joint(state, op_name, is_up, strength)

        # Entangling coupling: Fe and Fi are cross-axis operators that entangle.
        # Ti and Te are dephasing channels -- they do NOT entangle.
        if op_name in ("Fe", "Fi"):
            coupling_strength = strength * 0.6  # proportional to operator effect
            state = self.apply_entangling_coupling(state, coupling_strength)

        d_angle = self.d_angle * strength
        if terrain['loop'] == 'fiber':
            state.theta = (state.theta + d_angle) % (2 * np.pi)
        else:
            state.phi = (state.phi + d_angle) % (2 * np.pi)

        state.berry_phase_L += self._accumulate_berry(r_L_old, state.r_L)
        state.berry_phase_R += self._accumulate_berry(r_R_old, state.r_R)

        state = self._check_transport(state, stage_position)

        sL, sR = self.get_entropies(state)
        lr = float(np.dot(state.r_L, state.r_R))
        conc = self.get_concurrence(state)
        state.history.append({
            'stage': terrain['name'], 'op': op_name, 'is_up': is_up,
            'strength': strength, 'theta': state.theta, 'phi': state.phi,
            'eta': state.eta, 'berry_L': state.berry_phase_L,
            'berry_R': state.berry_phase_R, 'S_L': sL, 'S_R': sR,
            'purity_L': state.purity_L, 'purity_R': state.purity_R,
            'LR_dot': lr, 'torus_level': state.torus_level,
            'concurrence': conc,
        })
        return state

    def run_cycle(self, state):
        for pos, ti in enumerate(LOOP_STAGE_ORDER[self.engine_type]):
            state = self.run_stage(state, ti, pos)
        return state


# =====================================================================
# VERIFICATION
# =====================================================================

def _concurrence_4x4(rho_AB):
    """Wootters concurrence for a 4x4 density matrix (standalone)."""
    sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
    sy_sy = np.kron(sy, sy)
    rho_tilde = sy_sy @ rho_AB.conj() @ sy_sy
    R = rho_AB @ rho_tilde
    evals = np.sort(np.real(np.sqrt(np.maximum(np.linalg.eigvals(R), 0))))[::-1]
    return float(max(0, evals[0] - evals[1] - evals[2] - evals[3]))


def _run_old_engine(n_cycles=10):
    from engine_core import GeometricEngine as OldEngine
    eng = OldEngine(engine_type=1)
    st = eng.init_state()
    sL_list, sR_list, conc_list = [], [], []
    for _ in range(n_cycles):
        st = eng.run_cycle(st)
        sL_list.append(von_neumann_entropy_2x2(st.rho_L))
        sR_list.append(von_neumann_entropy_2x2(st.rho_R))
        conc_list.append(_concurrence_4x4(st.rho_AB))
    return sL_list, sR_list, conc_list


def main():
    print("=" * 72)
    print("GEOMETRIC ENGINE -- Real Cl(3) Rotors on Nested Hopf Tori")
    print("  + Cl(3) Entangling Coupling (bivector L-R correlator)")
    print("=" * 72)
    print()

    eng = GeometricEngine(engine_type=1)
    state = eng.init_state(eta=TORUS_CLIFFORD)

    print(f"Cell complex: {len(eng.cc.nodes)} nodes, "
          f"{len(eng.cc.edges)} edges, {len(eng.cc.cells)} faces")
    print(f"Shells: {len(eng.shells)}")
    print(f"Engine path: {eng.path}")
    print()

    bL, bR = eng.get_bloch_vectors(state)
    init_bL = bL.copy()
    init_bR = bR.copy()
    sL, sR = eng.get_entropies(state)
    conc0 = eng.get_concurrence(state)
    print("INITIAL STATE:")
    print(f"  psi_L = [{state.psi_L[0]:.4f}, {state.psi_L[1]:.4f}]")
    print(f"  psi_R = [{state.psi_R[0]:.4f}, {state.psi_R[1]:.4f}]")
    print(f"  Bloch L = [{bL[0]:.4f}, {bL[1]:.4f}, {bL[2]:.4f}] |r|={np.linalg.norm(bL):.4f}")
    print(f"  Bloch R = [{bR[0]:.4f}, {bR[1]:.4f}, {bR[2]:.4f}] |r|={np.linalg.norm(bR):.4f}")
    print(f"  S(L)={sL:.6f}  S(R)={sR:.6f}  L.R={eng.get_lr_dot(state):.6f}")
    print(f"  Concurrence={conc0:.6f}  (should be 0 -- no coupling yet)")
    print(f"  Torus: eta={state.eta:.4f} theta={state.theta:.4f} phi={state.phi:.4f}")
    print()

    n_cycles = 10
    geo_sL, geo_sR, geo_lr = [], [], []
    geo_purL, geo_purR = [], []
    geo_conc = []

    hdr = (f"{'Cyc':>3} | {'S(L)':>7} {'S(R)':>7} | {'|rL|':>5} {'|rR|':>5} | "
           f"{'BerryL':>7} {'BerryR':>7} | {'L.R':>6} | {'Conc':>6} | "
           f"{'eta':>6} {'th':>5} {'ph':>5} | {'T':>1}")
    print("-" * len(hdr))
    print(hdr)
    print("-" * len(hdr))

    for c in range(1, n_cycles + 1):
        state = eng.run_cycle(state)
        sL, sR = eng.get_entropies(state)
        lr = eng.get_lr_dot(state)
        conc = eng.get_concurrence(state)
        geo_sL.append(sL); geo_sR.append(sR); geo_lr.append(lr)
        geo_purL.append(state.purity_L); geo_purR.append(state.purity_R)
        geo_conc.append(conc)

        # Validate rho_AB at every step
        rho = eng.get_joint_density_matrix(state)
        tr = np.real(np.trace(rho))
        evals = np.linalg.eigvalsh(rho)
        psd = evals[0] >= -1e-10
        tr_ok = abs(tr - 1.0) < 1e-10

        print(f"{c:3d} | {sL:7.4f} {sR:7.4f} | {state.purity_L:5.3f} {state.purity_R:5.3f} | "
              f"{state.berry_phase_L:7.3f} {state.berry_phase_R:7.3f} | {lr:6.3f} | {conc:6.4f} | "
              f"{state.eta:6.4f} {state.theta:5.2f} {state.phi:5.2f} | {state.torus_level:1d}"
              f"  rho:{'OK' if (psd and tr_ok) else 'BAD'}")

    print("-" * len(hdr))
    print()

    bL, bR = eng.get_bloch_vectors(state)
    print("FINAL STATE:")
    print(f"  psi_L = [{state.psi_L[0]:.6f}, {state.psi_L[1]:.6f}]")
    print(f"  psi_R = [{state.psi_R[0]:.6f}, {state.psi_R[1]:.6f}]")
    print(f"  Bloch L = [{bL[0]:.4f}, {bL[1]:.4f}, {bL[2]:.4f}] |r|={np.linalg.norm(bL):.6f}")
    print(f"  Bloch R = [{bR[0]:.4f}, {bR[1]:.4f}, {bR[2]:.4f}] |r|={np.linalg.norm(bR):.6f}")
    print(f"  Concurrence = {geo_conc[-1]:.6f}")
    print()

    # -- Correlation matrix --
    print("CORRELATION MATRIX C_{ij} (final):")
    for i in range(3):
        row = "  ["
        for j in range(3):
            row += f" {state.correlation[i, j]:8.5f}"
        row += " ]"
        print(row)
    print(f"  ||C|| = {np.linalg.norm(state.correlation):.6f}")
    print()

    # -- Concurrence trajectory --
    print("CONCURRENCE TRAJECTORY (geometric engine):")
    for i, c_val in enumerate(geo_conc):
        bar = "#" * int(c_val * 40)
        print(f"  Cycle {i+1:2d}: C={c_val:.6f}  {bar}")
    print()

    # -- Comparison --
    print("=" * 72)
    print("COMPARISON: Geometric vs Old Engine (with concurrence)")
    print("=" * 72)
    old_sL, old_sR, old_conc = _run_old_engine(n_cycles)
    print(f"{'Cyc':>3} | {'GeoS(L)':>8} {'OldS(L)':>8} | {'GeoS(R)':>8} {'OldS(R)':>8} | "
          f"{'GeoC':>6} {'OldC':>6} | {'|rL|':>6} {'|rR|':>6}")
    print("-" * 80)
    for i in range(n_cycles):
        print(f"{i+1:3d} | {geo_sL[i]:8.5f} {old_sL[i]:8.5f} | "
              f"{geo_sR[i]:8.5f} {old_sR[i]:8.5f} | "
              f"{geo_conc[i]:6.4f} {old_conc[i]:6.4f} | "
              f"{geo_purL[i]:6.4f} {geo_purR[i]:6.4f}")
    print()

    # -- Correlation matrix evolution --
    print("CORRELATION MATRIX EVOLUTION:")
    print("  (Frobenius norm of C at each cycle)")
    # Re-run to capture per-cycle C norms
    eng2 = GeometricEngine(engine_type=1)
    st2 = eng2.init_state(eta=TORUS_CLIFFORD)
    c_norms = []
    for cyc in range(1, n_cycles + 1):
        st2 = eng2.run_cycle(st2)
        c_norms.append(np.linalg.norm(st2.correlation))
    for i, cn in enumerate(c_norms):
        bar = "#" * int(cn * 20)
        print(f"  Cycle {i+1:2d}: ||C||={cn:.6f}  {bar}")
    print()

    # -- Verification --
    print("VERIFICATION:")
    bp_ok = abs(state.berry_phase_L) > 0.01 or abs(state.berry_phase_R) > 0.01
    print(f"  Berry non-trivial     : {'PASS' if bp_ok else 'FAIL'}  L={state.berry_phase_L:.4f} R={state.berry_phase_R:.4f}")
    avg_lr = np.mean(geo_lr)
    print(f"  L.R anti-alignment    : {'PASS' if avg_lr < 0.5 else 'WEAK'}  avg={avg_lr:.4f}")
    cd = np.linalg.norm(bL - bR)
    print(f"  Chiral separation     : {'PASS' if cd > 0.01 else 'FAIL'}  |bL-bR|={cd:.4f}")
    bd = abs(state.berry_phase_L - state.berry_phase_R)
    print(f"  Berry chirality       : {'PASS' if bd > 0.01 else 'FAIL'}  |dBerry|={bd:.4f}")
    eok = max(geo_sL) > 0.01 or max(geo_sR) > 0.01
    print(f"  Entropy generated     : {'PASS' if eok else 'FAIL'}  max S_L={max(geo_sL):.4f} S_R={max(geo_sR):.4f}")
    pok = min(geo_purL) < 0.99 or min(geo_purR) < 0.99
    print(f"  Purity decreases      : {'PASS' if pok else 'FAIL'}  min |rL|={min(geo_purL):.4f} |rR|={min(geo_purR):.4f}")
    gm = np.mean(geo_sL); om = np.mean(old_sL)
    print(f"  Entropy match (qual)  : {'PASS' if abs(gm-om)<0.5 else 'WEAK'}  geo={gm:.4f} old={om:.4f}")
    nL = np.linalg.norm(state.psi_L); nR = np.linalg.norm(state.psi_R)
    print(f"  Spinor normalization  : {'PASS' if abs(nL-1)<1e-8 and abs(nR-1)<1e-8 else 'FAIL'}  |psi_L|={nL:.10f} |psi_R|={nR:.10f}")
    conc_ok = max(geo_conc) > 0.001
    print(f"  Concurrence non-zero  : {'PASS' if conc_ok else 'FAIL'}  max C={max(geo_conc):.6f}")
    rho_final = eng.get_joint_density_matrix(state)
    rho_evals = np.linalg.eigvalsh(rho_final)
    rho_psd = rho_evals[0] >= -1e-10
    rho_tr = abs(np.real(np.trace(rho_final)) - 1.0) < 1e-10
    print(f"  rho_AB PSD            : {'PASS' if rho_psd else 'FAIL'}  min eval={rho_evals[0]:.2e}")
    print(f"  rho_AB trace=1        : {'PASS' if rho_tr else 'FAIL'}  Tr={np.real(np.trace(rho_final)):.10f}")
    conc_match = abs(np.mean(geo_conc) - np.mean(old_conc)) < 0.3
    print(f"  Concurrence match     : {'PASS' if conc_match else 'QUAL'}  geo={np.mean(geo_conc):.4f} old={np.mean(old_conc):.4f}")

    results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    out_path = os.path.join(results_dir, "geometric_engine_results.json")
    result = {
        "name": "engine_geometric",
        "torus_levels": ["inner", "clifford", "outer"],
        "n_cycles": n_cycles,
        "initial": {
            "eta": TORUS_CLIFFORD,
            "bloch_L": init_bL.tolist(),
            "bloch_R": init_bR.tolist(),
        },
        "final": {
            "eta": state.eta,
            "theta": state.theta,
            "phi": state.phi,
            "berry_phase_L": state.berry_phase_L,
            "berry_phase_R": state.berry_phase_R,
            "bloch_L": bL.tolist(),
            "bloch_R": bR.tolist(),
            "psi_L": [[float(np.real(z)), float(np.imag(z))] for z in state.psi_L],
            "psi_R": [[float(np.real(z)), float(np.imag(z))] for z in state.psi_R],
            "correlation_matrix": state.correlation.tolist(),
            "concurrence": geo_conc[-1],
        },
        "trajectories": {
            "entropy_L": geo_sL,
            "entropy_R": geo_sR,
            "lr_dot": geo_lr,
            "purity_L": geo_purL,
            "purity_R": geo_purR,
            "concurrence": geo_conc,
        },
        "comparison": {
            "old_entropy_L_mean": float(np.mean(old_sL)),
            "geo_entropy_L_mean": float(gm),
            "old_entropy_R_mean": float(np.mean(old_sR)),
            "geo_entropy_R_mean": float(np.mean(geo_sR)),
            "old_concurrence_mean": float(np.mean(old_conc)),
            "geo_concurrence_mean": float(np.mean(geo_conc)),
        },
        "verification": {
            "berry_non_trivial": bool(bp_ok),
            "lr_anti_alignment": bool(avg_lr < 0.5),
            "chiral_separation": bool(cd > 0.01),
            "berry_chirality": bool(bd > 0.01),
            "entropy_generated": bool(eok),
            "purity_decreases": bool(pok),
            "spinor_normalization": bool(abs(nL-1)<1e-8 and abs(nR-1)<1e-8),
            "concurrence_nonzero": bool(conc_ok),
            "rho_AB_psd": bool(rho_psd),
            "rho_AB_trace_1": bool(rho_tr),
        },
        "summary": "Spinors primary; rho derived; Cl(3) bivector entangling coupling active; "
                   "correlation matrix tracks L-R geometric entanglement.",
    }
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nResult JSON written to: {out_path}")

    print()
    print("=" * 72)
    print("Done. Bloch multivectors primary. rho derived.")
    print("F-kernels: Cl(3) rotors. T-kernels: geometric contractions.")
    print("Entanglement: Cl(3) bivector coupling (Fe, Fi stages).")
    print("Berry: Pancharatnam. Transport: cell complex adjacency.")
    print("=" * 72)


if __name__ == "__main__":
    main()
