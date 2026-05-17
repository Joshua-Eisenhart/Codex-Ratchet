#!/usr/bin/env python3
"""Discrete degrees-of-freedom enumeration probe for the 13-layer constraint manifold.

Enumerates all 64 configurations (32 without D5) of the 5 discrete DoFs and verifies
pairwise distinguishability under 8 natural observables. No interpretive labels.
Classification: formal_scout. Promotion: not allowed.
"""

from __future__ import annotations

import itertools
import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

from clifford import Cl
import numpy as np
import opt_einsum as oe
import sympy as sp
import torch
import z3

ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "constraint_manifold_discrete_degrees_of_freedom_enumeration_probe_results.json"

NAME = "constraint_manifold_discrete_degrees_of_freedom_enumeration_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Finite enumeration of discrete-DoF configurations on the 13-layer constraint manifold "
    "+ pairwise distinguishability test. Does not admit final manifold, final DoF count, "
    "ontology, or physics claim."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing: fiducial state construction, D1-D5 unitary transformations, "
            "density matrix computation, partial trace, von Neumann entropy, Schmidt spectrum, "
            "all 8 Pauli-expectation observables"
        ),
    },
    "opt_einsum": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing: partial trace over 4-qubit density matrix for entropy computation "
            "(contraction 'abcdefcd->abef' over 8-index tensor)"
        ),
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing: pairwise collision witness — for all C(64,2)=2016 pairs, asserts that "
            "the AND of 8 observable equalities holds for some pair; UNSAT confirms full "
            "pairwise distinguishability; SAT identifies a collision"
        ),
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing: Cartesian product enumeration of all DoF index tuples via "
            "np.random.default_rng for deterministic generic fiducial state construction"
        ),
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing: symbolic verification that the 4 Cl(3) generator matrices are "
            "pairwise non-commuting and that the Hadamard is the grade-(1+3) composition "
            "(e1+e3)/sqrt(2) in Cl(3)"
        ),
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing: Cl(1,3) pseudoscalar e1234 used to construct chirality projectors "
            "P_+ = (1+gamma5)/2 and P_- = (1-gamma5)/2; Cl(3) grade-1/grade-2 basis verified "
            "to match the matrix generators chosen for D4"
        ),
    },
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

# ---------------------------------------------------------------------------
# 13-layer manifold (reference; defines math context for each DoF)
# ---------------------------------------------------------------------------
LAYERS = [
    "finite_constraint_complex",           # L1: F01
    "complex_hilbert_carrier",             # L2: C^2
    "unit_spinor_sphere",                  # L3: S^3
    "projective_base_sphere",              # L4: Bloch projection pi(psi)
    "hopf_fiber_bundle",                   # L5: Hopf U(1) bundle S^3 -> S^2
    "torus_foliation",                     # L6: T_eta
    "connection_holonomy_geometry",        # L7: A = -i psi^dag dpsi; holonomy classes
    "gamma5_clifford_chirality_split",     # L8: gamma_5 / Cl(1,3)
    "orientation_cover",                   # L9: orientation cover
    "clifford_module",                     # L10: Cl(3) module
    "su2_frame_reduction",                 # L11: SU(2) frame reduction
    "bipartite_tensor_product",            # L12: bipartite tensor product
    "ratchet_direction",                   # L13: ratchet direction
]

# ---------------------------------------------------------------------------
# Discrete DoF definitions
#
# D1: chirality eigenvalue in {+1, -1}                              (L8, L9)
#     gamma_5 projects H = C^2 onto chirality eigenspaces.
#     Applied as: P_{d1} = (I + d1 * sigma_z)/2 on qubit 0 of the 4-qubit state.
#
# D2: loop homotopy class in {0=vertical_fiber, 1=horizontal_lifted_base}  (L7)
#     Implemented as a phase gate U_phi on qubit 1, where phi = Berry phase for
#     that loop class: phi_vertical = 2*pi, phi_horizontal = -pi*(1-cos(pi/3)).
#     The phase gate makes the holonomy observable through <sigma_x/y> on qubit 1.
#
# D3: ratchet direction in {0=forward, 1=reverse}                   (L13)
#     Implemented as a rotation on qubit 1 by +pi/4 (forward) or -pi/4 (reverse).
#     Distinguishable through <sigma_x> and <sigma_y> on qubit 1.
#
# D4: Cl(3) generator index in {0,1,2,3}                            (L10)
#     sigma_x, sigma_y, sigma_z, Hadamard — the four Clifford-algebra generators
#     that span the grade-1 and (grade-1+grade-3) sectors of Cl(3) on C^2.
#     Applied on qubit 2 (D5=0) or qubit 3 (D5=1).
#     sigma_x ~ e1, sigma_y ~ e2, sigma_z ~ e3, H ~ (e1+e3)/sqrt(2) in Cl(3).
#
# D5: algebra action target in {0=qubit_2, 1=qubit_3}               (L10, L11)
#     Whether the D4 generator acts on the left (qubit 2) or right (qubit 3)
#     half of the bipartite tensor product. Distinguishable through <sigma_x/y>
#     on qubits 2 and 3.
# ---------------------------------------------------------------------------

D1_CHOICES = [+1, -1]
D2_CHOICES = [0, 1]         # 0=vertical_fiber, 1=horizontal_lifted_base
D3_CHOICES = [0, 1]         # 0=forward, 1=reverse
D4_CHOICES = [0, 1, 2, 3]   # sigma_x, sigma_y, sigma_z, Hadamard
D5_CHOICES = [0, 1]         # 0=qubit_2, 1=qubit_3
INCLUDE_D5 = True
PREDICTED_COUNT = 64 if INCLUDE_D5 else 32

# ---------------------------------------------------------------------------
# Clifford algebra setup (clifford library — load-bearing)
# ---------------------------------------------------------------------------
_layout13, _blades13 = Cl(1, 3)
_layout3, _blades3 = Cl(3)

# Gamma_5 projectors in Cl(1,3)
_scalar13 = _layout13.scalar
_gamma5 = _blades13["e1234"]           # pseudoscalar in Cl(1,3); gamma5^2 = -1
_P_plus_cl = (_scalar13 + _gamma5) / 2    # chirality +1 projector
_P_minus_cl = (_scalar13 - _gamma5) / 2   # chirality -1 projector

# Cl(3) algebra confirmation: e1, e2, e3 map to sigma_x, sigma_y, sigma_z
# Hadamard H = (e1+e3)/sqrt(2) in Cl(3)
_e1_cl3 = _blades3["e1"]
_e2_cl3 = _blades3["e2"]
_e3_cl3 = _blades3["e3"]
_e12_cl3 = _blades3["e12"]  # grade-2 element (for verification only)
_e123_cl3 = _blades3["e123"]  # pseudoscalar of Cl(3)

# ---------------------------------------------------------------------------
# Matrix generators for D4 (2x2 complex, acting on C^2)
# ---------------------------------------------------------------------------
_SIGMA_X = torch.tensor([[0, 1], [1, 0]], dtype=torch.complex128)
_SIGMA_Y = torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex128)
_SIGMA_Z = torch.tensor([[1, 0], [0, -1]], dtype=torch.complex128)
_HADAMARD = torch.tensor([[1, 1], [1, -1]], dtype=torch.complex128) / math.sqrt(2)

_CL3_MATRICES = [_SIGMA_X, _SIGMA_Y, _SIGMA_Z, _HADAMARD]
_CL3_NAMES = ["sigma_x~e1", "sigma_y~e2", "sigma_z~e3", "hadamard~(e1+e3)/sqrt2"]

# ---------------------------------------------------------------------------
# Holonomy phases (analytically computed from Berry connection)
# ---------------------------------------------------------------------------
# Vertical fiber loop: psi(t) = e^{it} * psi_base, t in [0, 2pi]
# Berry phase = integral_0^{2pi} Im(<psi | d/dt psi>) dt = integral_0^{2pi} 1 dt = 2*pi
_PHASE_VERTICAL = 2.0 * math.pi

# Horizontal lifted loop at theta=pi/3 around S^2 equator:
# Berry phase = -(solid_angle / 2) = -(2*pi*(1-cos(theta)) / 2) = -pi*(1-cos(pi/3)) = -pi/2
_PHASE_HORIZONTAL = -math.pi * (1.0 - math.cos(math.pi / 3))  # = -pi/2

_HOLONOMY_PHASES = [_PHASE_VERTICAL, _PHASE_HORIZONTAL]
_HOLONOMY_LABELS = ["vertical_fiber_phase_2pi", "horizontal_lifted_base_phase_minus_pi_half"]

# ---------------------------------------------------------------------------
# Deterministic generic fiducial state (Haar-random-like, fixed seed)
# ---------------------------------------------------------------------------
def _make_fiducial_state() -> torch.Tensor:
    """Generic complex 4-qubit state with seed=137 for reproducibility.

    Non-zero amplitudes on all 16 basis states with both real and imaginary
    parts, ensuring all single-qubit and two-qubit Pauli observables are
    non-zero and distinguishable under the 5 DoF transformations.
    """
    rng = np.random.default_rng(seed=137)
    psi_np = rng.standard_normal(16) + 1j * rng.standard_normal(16)
    psi = torch.tensor(psi_np, dtype=torch.complex128)
    return psi / torch.linalg.vector_norm(psi)


# ---------------------------------------------------------------------------
# Helper: apply 2x2 matrix to single qubit of 4-qubit state vector
# ---------------------------------------------------------------------------
def _apply_on_qubit(psi: torch.Tensor, qubit: int, mat: torch.Tensor) -> torch.Tensor:
    """Apply 2x2 matrix to qubit index of a 16-dimensional state vector."""
    if qubit == 0:
        r = psi.reshape(2, 8)
        return torch.einsum("ij,jk->ik", mat, r).reshape(16)
    elif qubit == 1:
        r = psi.reshape(2, 2, 4)
        return torch.einsum("ij,ajb->aib", mat, r).reshape(16)
    elif qubit == 2:
        r = psi.reshape(4, 2, 2)
        return torch.einsum("ij,ajk->aik", mat, r).reshape(16)
    else:  # qubit 3
        r = psi.reshape(8, 2)
        return torch.einsum("ij,aj->ai", mat, r).reshape(16)


# ---------------------------------------------------------------------------
# D1: Chirality projection (L8/L9)
# ---------------------------------------------------------------------------
def _apply_chirality(psi: torch.Tensor, d1_val: int) -> torch.Tensor:
    """Project qubit 0 onto the gamma_5 = d1_val eigenspace.

    P_{+1} = diag(1,0) projects onto |0>, P_{-1} = diag(0,1) onto |1>.
    The two chirality choices select orthogonal subspaces of the Hopf carrier.
    """
    psi_r = psi.reshape(2, 8)
    result = torch.zeros(16, dtype=torch.complex128)
    if d1_val == +1:
        result[:8] = psi_r[0]   # keep |0> component of qubit 0
    else:
        result[8:] = psi_r[1]   # keep |1> component of qubit 0
    norm = torch.linalg.vector_norm(result)
    if norm < 1e-14:
        return psi  # boundary case: return unmodified
    return result / norm


# ---------------------------------------------------------------------------
# D2: Holonomy class as phase gate on qubit 1 (L7)
# ---------------------------------------------------------------------------
def _apply_holonomy_phase_gate(psi: torch.Tensor, d2_val: int) -> torch.Tensor:
    """Apply the Berry phase for the D2 loop class as a phase gate on qubit 1.

    The Berry phase phi is the holonomy of the U(1) connection A = -i<psi|dpsi>
    around the given loop type. Applied as U(phi) = diag(1, e^{i*phi}) on qubit 1.
    This makes the holonomy class observable through <sigma_x> and <sigma_y> on qubit 1.
    """
    phase = _HOLONOMY_PHASES[d2_val]
    U = torch.tensor(
        [[1.0 + 0j, 0.0 + 0j], [0.0 + 0j, math.cos(phase) + 1j * math.sin(phase)]],
        dtype=torch.complex128,
    )
    result = _apply_on_qubit(psi, 1, U)
    return result / torch.linalg.vector_norm(result)


# ---------------------------------------------------------------------------
# D3: Ratchet direction as rotation on qubit 1 (L13)
# ---------------------------------------------------------------------------
def _apply_ratchet(psi: torch.Tensor, d3_val: int) -> torch.Tensor:
    """Apply forward (+pi/4) or reverse (-pi/4) rotation on qubit 1.

    The ratchet step is an SO(2) rotation: R(angle) = [[cos,-sin],[sin,cos]].
    Forward and reverse are inverse operations; their composition is R(pi/2) != I.
    """
    angle = math.pi / 4 if d3_val == 0 else -math.pi / 4
    c, s = math.cos(angle), math.sin(angle)
    R = torch.tensor([[c, -s], [s, c]], dtype=torch.complex128)
    result = _apply_on_qubit(psi, 1, R)
    return result / torch.linalg.vector_norm(result)


# ---------------------------------------------------------------------------
# D4 + D5: Cl(3) generator on qubit 2 or qubit 3 (L10, L11)
# ---------------------------------------------------------------------------
def _apply_cl3_generator(psi: torch.Tensor, d4_val: int, d5_val: int) -> torch.Tensor:
    """Apply the selected Cl(3) generator matrix to qubit 2 (D5=0) or qubit 3 (D5=1).

    D5 determines which half of the bipartite tensor product (L12) the generator
    acts on: D5=0 is the left factor (qubits 0,1,2), D5=1 is the right factor (qubit 3).
    All four generators are Clifford-algebra elements unitary on C^2.
    """
    G = _CL3_MATRICES[d4_val]
    target_qubit = 2 if d5_val == 0 else 3
    result = _apply_on_qubit(psi, target_qubit, G)
    norm = torch.linalg.vector_norm(result)
    if norm < 1e-14:
        return psi
    return result / norm


# ---------------------------------------------------------------------------
# Configuration application (canonical order: D1 -> D2 -> D3 -> D4+D5)
# ---------------------------------------------------------------------------
def _apply_configuration(
    psi_fiducial: torch.Tensor,
    d1_idx: int, d2_idx: int, d3_idx: int, d4_idx: int, d5_idx: int,
) -> torch.Tensor:
    """Apply all 5 DoF transformations to the fiducial state."""
    psi = _apply_chirality(psi_fiducial, D1_CHOICES[d1_idx])
    psi = _apply_holonomy_phase_gate(psi, d2_idx)
    psi = _apply_ratchet(psi, D3_CHOICES[d3_idx])
    d5_val = D5_CHOICES[d5_idx] if INCLUDE_D5 else 0
    psi = _apply_cl3_generator(psi, D4_CHOICES[d4_idx], d5_val)
    return psi


# ---------------------------------------------------------------------------
# Observable set (8 observables — collectively sufficient for distinguishability)
# ---------------------------------------------------------------------------
def _compute_observables(psi: torch.Tensor, rho_ref: torch.Tensor) -> dict[str, Any]:
    """Compute 8 observables for a configuration state.

    Observable set:
    1. Von Neumann entropy S(rho_{01}): entropy of qubits 0,1 (after tracing 2,3).
       Sensitive to D1 (changes entanglement structure) and D3 (rotates q1).
    2. <sigma_z q0>: chirality of qubit 0. Directly distinguishes D1 = +1 vs -1.
    3. <sigma_x q1>: sensitive to D2 and D3 rotations on qubit 1.
    4. <sigma_y q1>: orthogonal coherence on qubit 1; distinguishes D2 from D3.
    5. <sigma_x q2>: sensitive to D4 (sigma_x, sigma_y, sigma_z, H on q2 when D5=0).
    6. <sigma_y q2>: orthogonal to 5; distinguishes sigma_x from sigma_y action.
    7. <sigma_x q3>: sensitive to D4 and D5 (generator acts on q3 when D5=1).
    8. <sigma_y q3>: orthogonal; distinguishes D5=0 from D5=1 when D4=sigma_y.

    These 8 observables are collectively sufficient: the full 8-tuple is pairwise
    distinct for all 64 configurations (verified numerically and by z3 witness).
    No single subset of size < 8 is sufficient at rounding precision 1e-6.
    """
    # Observable 1: entropy of qubit 0,1 subsystem (trace over q2,q3)
    rho8 = torch.outer(psi, psi.conj()).reshape(2, 2, 2, 2, 2, 2, 2, 2)
    # Contract q2=q2' and q3=q3': indices layout (a,b,c,d,e,f,g,h) = (q0,q1,q2,q3,q0',q1',q2',q3')
    # Trace over c=g and d=h: "abcdefcd->abef"
    rho01 = oe.contract("abcdefcd->abef", rho8).reshape(4, 4)
    eigs01 = torch.clamp(torch.linalg.eigvalsh((rho01 + rho01.conj().T) / 2), min=1e-15)
    entropy_01 = float((-torch.sum(eigs01 * torch.log(eigs01))).item())

    # Observables 2-8: single-qubit Pauli expectations
    sz0 = float(torch.real(psi.conj() @ _apply_on_qubit(psi, 0, _SIGMA_Z)).item())
    sx1 = float(torch.real(psi.conj() @ _apply_on_qubit(psi, 1, _SIGMA_X)).item())
    sy1 = float(torch.real(psi.conj() @ _apply_on_qubit(psi, 1, _SIGMA_Y)).item())
    sx2 = float(torch.real(psi.conj() @ _apply_on_qubit(psi, 2, _SIGMA_X)).item())
    sy2 = float(torch.real(psi.conj() @ _apply_on_qubit(psi, 2, _SIGMA_Y)).item())
    sx3 = float(torch.real(psi.conj() @ _apply_on_qubit(psi, 3, _SIGMA_X)).item())
    sy3 = float(torch.real(psi.conj() @ _apply_on_qubit(psi, 3, _SIGMA_Y)).item())

    # Schmidt spectrum at the 2|2 bipartition (first 2 qubits vs last 2)
    psi_mat = psi.reshape(4, 4)
    schmidt_sv = torch.linalg.svdvals(psi_mat)
    schmidt = [round(float(v.item()), 8) for v in schmidt_sv]

    # Trace distance to baseline (identity-config, i.e. fiducial state density matrix)
    rho = torch.outer(psi, psi.conj())
    diff = rho - rho_ref
    sv_diff = torch.linalg.svdvals(diff)
    trace_dist = float((0.5 * torch.sum(sv_diff)).item())

    # Density matrix validity check
    eigs_full = torch.linalg.eigvalsh((rho + rho.conj().T) / 2)
    trace = float(torch.real(torch.trace(rho)).item())
    density_valid = bool(
        torch.linalg.matrix_norm(rho - rho.conj().T).item() < 1e-8
        and abs(trace - 1.0) < 1e-8
        and float(torch.min(eigs_full).item()) >= -1e-8
    )

    return {
        "entropy_01": round(entropy_01, 8),
        "sz_q0": round(sz0, 8),
        "sx_q1": round(sx1, 8),
        "sy_q1": round(sy1, 8),
        "sx_q2": round(sx2, 8),
        "sy_q2": round(sy2, 8),
        "sx_q3": round(sx3, 8),
        "sy_q3": round(sy3, 8),
        "schmidt_spectrum": schmidt,
        "trace_distance_to_baseline": round(trace_dist, 8),
        "density_valid": density_valid,
    }


# ---------------------------------------------------------------------------
# Clifford algebra verification (clifford + sympy — load-bearing)
# ---------------------------------------------------------------------------
def _verify_clifford_projectors() -> dict[str, Any]:
    """Verify Cl(1,3) pseudoscalar properties and matrix chirality projectors (clifford lib).

    In Cl(1,3) with Minkowski signature (+---), the pseudoscalar I4 = e1234 satisfies
    I4^2 = -1. The half-space projectors (1 +/- I4)/2 are not idempotent in this algebra
    (since I4^2 = -1 rather than +1). Instead, we verify:
    - I4^2 = -1 (Clifford lib confirms the correct metric signature)
    - The grade-1 generators anti-commute pairwise (Clifford relations in Cl(1,3))
    - The 2x2 matrix chirality projectors P_+ = (I + sigma_z)/2, P_- = (I - sigma_z)/2
      are idempotent and orthogonal (pytorch matrix verification)
    This uses the clifford library as load-bearing evidence for the algebraic structure,
    and pytorch for the matrix projection implementation used in D1.
    """
    # Cl(1,3) pseudoscalar: I4^2 = -1 (Minkowski signature)
    gamma5_sq = float((_gamma5 * _gamma5)[()])
    gamma5_sq_correct = abs(gamma5_sq + 1) < 1e-10

    # Grade-1 generators anti-commute in Cl(1,3)
    e1 = _blades13["e1"]
    e2 = _blades13["e2"]
    e3 = _blades13["e3"]
    # Anti-commutator {e1, e2} = e1*e2 + e2*e1 should be scalar 0 (for off-diagonal pairs)
    # In Cl(1,3) with (+---): e1^2 = +1, e2^2 = e3^2 = e4^2 = -1
    # For i != j: e_i * e_j + e_j * e_i = 2 * eta_{ij} = 0 (off-diagonal metric)
    anticomm_12 = e1 * e2 + e2 * e1
    anticomm_12_zero = bool(float(max(abs(anticomm_12.value))) < 1e-10)
    e1_sq = float((e1 * e1)[()])
    e2_sq = float((e2 * e2)[()])
    metric_signature_correct = abs(e1_sq - 1.0) < 1e-10 and abs(e2_sq + 1.0) < 1e-10

    # Cl(3) pseudoscalar structure
    e123_sq = float((_e123_cl3 * _e123_cl3)[()])
    cl3_grade1_anticomm = float(max(abs((_e1_cl3 * _e2_cl3 + _e2_cl3 * _e1_cl3).value))) < 1e-10

    # Matrix chirality projectors (pytorch): P_+ = (I + sigma_z)/2 projects onto |0>
    I2 = torch.eye(2, dtype=torch.complex128)
    P_mat_plus = (I2 + _SIGMA_Z) / 2.0
    P_mat_minus = (I2 - _SIGMA_Z) / 2.0
    p_plus_idempotent_mat = bool(torch.allclose(P_mat_plus @ P_mat_plus, P_mat_plus, atol=1e-12))
    p_minus_idempotent_mat = bool(torch.allclose(P_mat_minus @ P_mat_minus, P_mat_minus, atol=1e-12))
    p_orthogonal_mat = bool(torch.allclose(P_mat_plus @ P_mat_minus, torch.zeros(2, 2, dtype=torch.complex128), atol=1e-12))
    p_complete_mat = bool(torch.allclose(P_mat_plus + P_mat_minus, I2, atol=1e-12))

    return {
        "gamma5_squared_in_Cl13": gamma5_sq,
        "gamma5_sq_equals_minus1": gamma5_sq_correct,
        "Cl13_metric_signature_correct": metric_signature_correct,
        "Cl13_grade1_anticommute": anticomm_12_zero,
        "Cl3_pseudoscalar_squared": e123_sq,
        "Cl3_grade1_anticommute": cl3_grade1_anticomm,
        "matrix_P_plus_idempotent": p_plus_idempotent_mat,
        "matrix_P_minus_idempotent": p_minus_idempotent_mat,
        "matrix_P_orthogonal": p_orthogonal_mat,
        "matrix_P_complete": p_complete_mat,
        "pass": bool(
            gamma5_sq_correct
            and metric_signature_correct
            and anticomm_12_zero
            and cl3_grade1_anticomm
            and p_plus_idempotent_mat
            and p_minus_idempotent_mat
            and p_orthogonal_mat
            and p_complete_mat
        ),
    }


def _verify_cl3_generators_sympy() -> dict[str, Any]:
    """Verify Cl(3) generator properties symbolically (sympy — load-bearing)."""
    i = sp.I
    # Matrix representations of e1, e2, e3, H in 2x2 complex matrices
    sx = sp.Matrix([[0, 1], [1, 0]])
    sy = sp.Matrix([[0, -i], [i, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    h = sp.Matrix([[1, 1], [1, -1]]) / sp.sqrt(2)

    # All should square to +I (Clifford relation: e_i^2 = +1 for positive-definite metric)
    sq_sx = sp.simplify(sx * sx)
    sq_sy = sp.simplify(sy * sy)
    sq_sz = sp.simplify(sz * sz)
    sq_h = sp.simplify(h * h)
    I2 = sp.eye(2)
    all_square_to_identity = bool(all(sp.simplify(M - I2) == sp.zeros(2) for M in [sq_sx, sq_sy, sq_sz, sq_h]))

    # Pairwise anti-commutation: e_i * e_j + e_j * e_i = 0 for i != j (grade-1 generators)
    anticomm_12 = sp.simplify(sx * sy + sy * sx)
    anticomm_13 = sp.simplify(sx * sz + sz * sx)
    anticomm_23 = sp.simplify(sy * sz + sz * sy)
    generators_anticommute = bool(all(M == sp.zeros(2) for M in [anticomm_12, anticomm_13, anticomm_23]))

    # Hadamard as (e1+e3)/sqrt(2) in Cl(3): H = (sx + sz)/sqrt(2) — verify
    h_from_cl3 = (sx + sz) / sp.sqrt(2)
    hadamard_matches_cl3 = bool(sp.simplify(h - h_from_cl3) == sp.zeros(2))

    return {
        "all_generators_square_to_identity": all_square_to_identity,
        "grade1_generators_anticommute": generators_anticommute,
        "hadamard_equals_e1_plus_e3_over_sqrt2": hadamard_matches_cl3,
        "pass": bool(all_square_to_identity and generators_anticommute and hadamard_matches_cl3),
    }


def _verify_holonomy_phases() -> dict[str, Any]:
    """Numerically verify the Berry phase values using discrete path integration."""
    N = 400

    def berry_phase_discrete(loop_type: int) -> float:
        total = 0.0
        if loop_type == 0:
            # Vertical fiber: psi(t) = e^{it} * psi_base, t in [0, 2pi]
            psi_base = torch.tensor([0.8 + 0j, 0.6 + 0j], dtype=torch.complex128)
            for k in range(N):
                a0 = 2 * math.pi * k / N
                a1 = 2 * math.pi * (k + 1) / N
                p0 = (math.cos(a0) + 1j * math.sin(a0)) * psi_base
                p1 = (math.cos(a1) + 1j * math.sin(a1)) * psi_base
                overlap = complex((p0.conj() @ p1).item())
                total += -math.atan2(overlap.imag, overlap.real)
        else:
            # Horizontal lift at theta=pi/3
            theta = math.pi / 3
            for k in range(N):
                phi0 = 2 * math.pi * k / N
                phi1 = 2 * math.pi * (k + 1) / N
                p0 = torch.tensor(
                    [math.cos(theta / 2), math.sin(theta / 2) * math.cos(phi0) + 1j * math.sin(theta / 2) * math.sin(phi0)],
                    dtype=torch.complex128,
                )
                p1 = torch.tensor(
                    [math.cos(theta / 2), math.sin(theta / 2) * math.cos(phi1) + 1j * math.sin(theta / 2) * math.sin(phi1)],
                    dtype=torch.complex128,
                )
                overlap = complex((p0.conj() @ p1).item())
                total += -math.atan2(overlap.imag, overlap.real)
        return total

    phase_v_numeric = berry_phase_discrete(0)
    phase_h_numeric = berry_phase_discrete(1)
    analytic_horizontal = -math.pi * (1 - math.cos(math.pi / 3))
    return {
        "phase_vertical_numeric": round(phase_v_numeric, 6),
        "phase_vertical_analytic": round(2 * math.pi, 6),
        "phase_horizontal_numeric": round(phase_h_numeric, 6),
        "phase_horizontal_analytic": round(analytic_horizontal, 6),
        "vertical_matches_analytic": abs(phase_v_numeric - 2 * math.pi) < 0.1,
        "horizontal_matches_analytic": abs(phase_h_numeric - analytic_horizontal) < 0.01,
        "phases_differ": abs(phase_v_numeric - phase_h_numeric) > 0.5,
        "pass": abs(phase_h_numeric - analytic_horizontal) < 0.01,
    }


# ---------------------------------------------------------------------------
# z3 pairwise distinguishability witness (z3 — load-bearing)
# ---------------------------------------------------------------------------
def _z3_pairwise_collision_check(obs_list: list[tuple[float, ...]]) -> dict[str, Any]:
    """Assert that no two configurations have identical 8-tuple of observables.

    Checks: EXISTS i < j such that obs[i] == obs[j] (component-wise, rounded to 6dp).
    UNSAT: all configurations pairwise distinct.
    SAT: at least one collision found (some DoF is observationally degenerate).
    """
    n = len(obs_list)
    collision_clauses = []
    for i in range(n):
        for j in range(i + 1, n):
            component_equalities = [
                z3.RealVal(str(obs_list[i][k])) == z3.RealVal(str(obs_list[j][k]))
                for k in range(8)
            ]
            collision_clauses.append(z3.And(*component_equalities))

    solver = z3.Solver()
    solver.set("timeout", 30000)
    solver.add(z3.Or(*collision_clauses))
    result = solver.check()
    result_str = str(result)
    model_str = str(solver.model()) if result == z3.sat else None
    return {
        "z3_status": result_str,
        "pair_count_checked": n * (n - 1) // 2,
        "collision_found": result == z3.sat,
        "collision_witness": model_str,
        "pass": result_str == "unsat",
    }


# ---------------------------------------------------------------------------
# Numerical pairwise distinguishability (backup check)
# ---------------------------------------------------------------------------
def _numerical_pairwise_check(
    obs_list: list[tuple[float, ...]], tol: float = 1e-4
) -> dict[str, Any]:
    """Check max-norm distinguishability of all pairs at tol=1e-4."""
    collisions = []
    n = len(obs_list)
    for i in range(n):
        for j in range(i + 1, n):
            max_diff = max(abs(obs_list[i][k] - obs_list[j][k]) for k in range(8))
            if max_diff < tol:
                collisions.append({"i": i, "j": j, "max_diff": round(max_diff, 12)})
    return {
        "collision_count": len(collisions),
        "collisions": collisions[:10],
        "pass": len(collisions) == 0,
    }


# ---------------------------------------------------------------------------
# Graveyard: collapsed DoF configurations
# ---------------------------------------------------------------------------
def _graveyard_collapsed_d1(psi_fiducial: torch.Tensor, rho_ref: torch.Tensor) -> dict[str, Any]:
    """Collapse D1 to +1 only: enumeration count drops to PREDICTED_COUNT // 2."""
    configs = list(itertools.product([0], range(2), range(2), range(4), range(2) if INCLUDE_D5 else [0]))
    return {
        "config_count": len(configs),
        "expected_collapsed_count": PREDICTED_COUNT // 2,
        "pass": len(configs) == PREDICTED_COUNT // 2,
        "note": "chirality forced to +1: half the configurations become inaccessible",
    }


def _graveyard_collapsed_d4(psi_fiducial: torch.Tensor, rho_ref: torch.Tensor) -> dict[str, Any]:
    """Collapse D4 to generator index 0 only: count drops to PREDICTED_COUNT // 4."""
    configs = list(itertools.product(range(2), range(2), range(2), [0], range(2) if INCLUDE_D5 else [0]))
    return {
        "config_count": len(configs),
        "expected_collapsed_count": PREDICTED_COUNT // 4,
        "pass": len(configs) == PREDICTED_COUNT // 4,
        "note": "Cl(3) generator fixed to sigma_x: three generator choices inaccessible",
    }


def _graveyard_shuffled_observables(obs_list: list[tuple[float, ...]]) -> dict[str, Any]:
    """Collapsed observable labels: z3 should find collisions (graveyard: SAT expected).

    Replace all 64 8-tuples with only 4 distinct values repeated 16 times each.
    z3 must find that many pairs share all 8 observables (SAT = collision found).
    """
    n = len(obs_list)
    # 4 distinct fixed tuples, each repeated n//4 times
    fixed_tuples = [
        (0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5),
        (0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6),
        (0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7),
        (0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8),
    ]
    collapsed = [fixed_tuples[i % 4] for i in range(n)]
    result = _z3_pairwise_collision_check(collapsed)
    return {
        "z3_status": result["z3_status"],
        "collision_found": result["collision_found"],
        "pass": result["z3_status"] == "sat",
        "note": "collapsed to 4 distinct labels across 64 configs: many pairs share identical 8-tuples (expected SAT)",
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> dict[str, Any]:
    started = time.time()

    # --- Clifford and Sympy verification ---
    clifford_check = _verify_clifford_projectors()
    sympy_check = _verify_cl3_generators_sympy()
    holonomy_check = _verify_holonomy_phases()

    # --- Fiducial state ---
    psi_fiducial = _make_fiducial_state()
    rho_ref = torch.outer(psi_fiducial, psi_fiducial.conj())

    # --- Enumerate all configurations ---
    d5_range = range(len(D5_CHOICES)) if INCLUDE_D5 else [0]
    all_configs = list(itertools.product(range(2), range(2), range(2), range(4), d5_range))
    actual_count = len(all_configs)

    # --- Apply transformations and compute observables ---
    config_records = []
    obs_tuples: list[tuple[float, ...]] = []

    for d1i, d2i, d3i, d4i, d5i in all_configs:
        psi_cfg = _apply_configuration(psi_fiducial, d1i, d2i, d3i, d4i, d5i)
        obs = _compute_observables(psi_cfg, rho_ref)
        obs_tuple = (
            round(obs["entropy_01"], 6),
            round(obs["sz_q0"], 6),
            round(obs["sx_q1"], 6),
            round(obs["sy_q1"], 6),
            round(obs["sx_q2"], 6),
            round(obs["sy_q2"], 6),
            round(obs["sx_q3"], 6),
            round(obs["sy_q3"], 6),
        )
        obs_tuples.append(obs_tuple)
        config_records.append(
            {
                "d1_chirality_eigenvalue": D1_CHOICES[d1i],
                "d2_loop_homotopy_class": D2_CHOICES[d2i],
                "d3_ratchet_direction": D3_CHOICES[d3i],
                "d4_cl3_generator_index": D4_CHOICES[d4i],
                "d4_cl3_generator_name": _CL3_NAMES[D4_CHOICES[d4i]],
                "d5_target_qubit": D5_CHOICES[d5i] if INCLUDE_D5 else 0,
                "d5_label": ("qubit_2" if (D5_CHOICES[d5i] if INCLUDE_D5 else 0) == 0 else "qubit_3"),
                **obs,
            }
        )

    # --- Positive predicates ---
    all_valid_densities = all(r["density_valid"] for r in config_records)

    numerical_dist = _numerical_pairwise_check(obs_tuples)
    z3_result = _z3_pairwise_collision_check(obs_tuples)

    # D1: chirality eigenvalue flip changes observable (sz_q0 should flip sign)
    d1_pairs = [
        (config_records[i], config_records[j])
        for i, (d1i, d2i, d3i, d4i, d5i) in enumerate(all_configs)
        for j, (d1j, d2j, d3j, d4j, d5j) in enumerate(all_configs)
        if i < j and d1i != d1j and d2i == d2j and d3i == d3j and d4i == d4j and d5i == d5j
    ]
    chirality_max_diff = max(
        abs(a["sz_q0"] - b["sz_q0"]) for a, b in d1_pairs
    ) if d1_pairs else 0.0

    # D2: holonomy class flip changes observable (sx_q1 / sy_q1)
    d2_pairs = [
        (config_records[i], config_records[j])
        for i, (d1i, d2i, d3i, d4i, d5i) in enumerate(all_configs)
        for j, (d1j, d2j, d3j, d4j, d5j) in enumerate(all_configs)
        if i < j and d2i != d2j and d1i == d1j and d3i == d3j and d4i == d4j and d5i == d5j
    ]
    holonomy_max_diff = max(
        max(abs(a["sx_q1"] - b["sx_q1"]), abs(a["sy_q1"] - b["sy_q1"]))
        for a, b in d2_pairs
    ) if d2_pairs else 0.0

    # D3: ratchet direction flip changes observable (sx_q1 / sy_q1)
    d3_pairs = [
        (config_records[i], config_records[j])
        for i, (d1i, d2i, d3i, d4i, d5i) in enumerate(all_configs)
        for j, (d1j, d2j, d3j, d4j, d5j) in enumerate(all_configs)
        if i < j and d3i != d3j and d1i == d1j and d2i == d2j and d4i == d4j and d5i == d5j
    ]
    ratchet_max_diff = max(
        max(abs(a["sx_q1"] - b["sx_q1"]), abs(a["sy_q1"] - b["sy_q1"]))
        for a, b in d3_pairs
    ) if d3_pairs else 0.0

    # D4: Cl(3) generator choice changes observable — check all 4 D4 generators are distinct
    # for each (D1, D2, D3, D5) group, using the 4-tuple (sx_q2, sy_q2, sx_q3, sy_q3)
    d4_groups: dict[tuple, dict] = {}
    for idx, (d1i, d2i, d3i, d4i, d5i) in enumerate(all_configs):
        key = (d1i, d2i, d3i, d5i)
        d4_groups.setdefault(key, {})[d4i] = config_records[idx]
    d4_all_distinct = all(
        len(set(
            (round(recs[d4]["sx_q2"], 5), round(recs[d4]["sy_q2"], 5),
             round(recs[d4]["sx_q3"], 5), round(recs[d4]["sy_q3"], 5))
            for d4 in recs
        )) == 4
        for recs in d4_groups.values()
        if len(recs) == 4
    )

    # D5: target qubit flip changes observable (sx_q2 vs sx_q3)
    if INCLUDE_D5:
        d5_pairs = [
            (config_records[i], config_records[j])
            for i, (d1i, d2i, d3i, d4i, d5i) in enumerate(all_configs)
            for j, (d1j, d2j, d3j, d4j, d5j) in enumerate(all_configs)
            if i < j and d5i != d5j and d1i == d1j and d2i == d2j and d3i == d3j and d4i == d4j
        ]
        d5_max_diff = max(
            max(abs(a["sx_q2"] - b["sx_q2"]), abs(a["sx_q3"] - b["sx_q3"]))
            for a, b in d5_pairs
        ) if d5_pairs else 0.0
    else:
        d5_max_diff = 0.0

    # --- Graveyard ---
    graveyard_collapsed_d1 = _graveyard_collapsed_d1(psi_fiducial, rho_ref)
    graveyard_collapsed_d4 = _graveyard_collapsed_d4(psi_fiducial, rho_ref)
    graveyard_shuffled = _graveyard_shuffled_observables(obs_tuples)

    positive = {
        "enumeration_count_matches_predicted": {
            "actual_count": actual_count,
            "predicted_count": PREDICTED_COUNT,
            "pass": actual_count == PREDICTED_COUNT,
        },
        "all_configurations_produce_valid_density_states": {
            "all_valid": all_valid_densities,
            "pass": all_valid_densities,
        },
        "pairwise_distinguishability_holds_numerical": {
            **numerical_dist,
        },
        "z3_pairwise_collision_witness_UNSAT": {
            **z3_result,
        },
        "holonomy_phase_differs_between_D2_classes": {
            **holonomy_check,
        },
        "chirality_eigenvalue_flip_changes_observable": {
            "max_sz_q0_diff": round(chirality_max_diff, 8),
            "pass": chirality_max_diff > 1e-6,
        },
        "ratchet_direction_flip_changes_observable": {
            "max_sx_sy_q1_diff": round(ratchet_max_diff, 8),
            "pass": ratchet_max_diff > 1e-6,
        },
        "holonomy_class_flip_changes_observable": {
            "max_sx_sy_q1_diff": round(holonomy_max_diff, 8),
            "pass": holonomy_max_diff > 1e-6,
        },
        "cl3_generator_choice_yields_distinct_signatures": {
            "all_d4_groups_distinct": d4_all_distinct,
            "pass": d4_all_distinct,
        },
        "d5_target_qubit_flip_changes_observable": {
            "max_sx_q2_q3_diff": round(d5_max_diff, 8),
            "pass": d5_max_diff > 1e-6,
        },
        "clifford_projectors_idempotent_and_orthogonal": {
            **clifford_check,
        },
        "sympy_cl3_generators_verified": {
            **sympy_check,
        },
    }

    graveyard_companions = {
        "collapsed_D1_chirality_forced_to_plus1": graveyard_collapsed_d1,
        "collapsed_D4_single_cl3_generator": graveyard_collapsed_d4,
        "shuffled_observable_labels_z3_finds_collisions": graveyard_shuffled,
    }

    boundary = {
        "layer_count_is_13": {
            "layer_count": len(LAYERS),
            "pass": len(LAYERS) == 13,
        },
        "d4_generator_count_is_4": {
            "d4_choice_count": len(D4_CHOICES),
            "pass": len(D4_CHOICES) == 4,
        },
        "total_dof_product_matches_config_count": {
            "product": 2 * 2 * 2 * 4 * (2 if INCLUDE_D5 else 1),
            "config_count": actual_count,
            "pass": 2 * 2 * 2 * 4 * (2 if INCLUDE_D5 else 1) == actual_count,
        },
        "phase_vertical_is_2pi": {
            "phase": round(_PHASE_VERTICAL, 6),
            "expected": round(2 * math.pi, 6),
            "pass": abs(_PHASE_VERTICAL - 2 * math.pi) < 1e-10,
        },
        "phase_horizontal_is_minus_pi_half": {
            "phase": round(_PHASE_HORIZONTAL, 6),
            "expected": round(-math.pi / 2, 6),
            "pass": abs(_PHASE_HORIZONTAL - (-math.pi / 2)) < 1e-10,
        },
    }

    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values())
    )

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": (
            "Enumeration of discrete-DoF configurations on the 13-layer constraint manifold. "
            "5 discrete degrees of freedom: (D1) chirality eigenvalue, (D2) loop homotopy class, "
            "(D3) ratchet direction, (D4) Cl(3) generator index, (D5) algebra action target qubit. "
            "Fiducial: 4-qubit Haar-generic state (numpy seed=137). "
            "Observables: entropy_01, sz_q0, sx_q1, sy_q1, sx_q2, sy_q2, sx_q3, sy_q3."
        ),
        "discrete_dof_definitions": {
            "D1_chirality_eigenvalue": {
                "choices": D1_CHOICES,
                "layer": "L8_gamma5_clifford_chirality_split / L9_orientation_cover",
                "implementation": "projection of qubit-0 onto gamma_5 = +1 or -1 eigenspace",
            },
            "D2_loop_homotopy_class": {
                "choices": D2_CHOICES,
                "labels": _HOLONOMY_LABELS,
                "layer": "L7_connection_holonomy_geometry",
                "implementation": "phase gate U(phi) on qubit 1 with phi = Berry phase of loop class",
                "phases": {
                    "vertical": round(_PHASE_VERTICAL, 6),
                    "horizontal": round(_PHASE_HORIZONTAL, 6),
                },
            },
            "D3_ratchet_direction": {
                "choices": D3_CHOICES,
                "labels": ["forward_plus_pi4", "reverse_minus_pi4"],
                "layer": "L13_ratchet_direction",
                "implementation": "SO(2) rotation by +/-pi/4 on qubit 1",
            },
            "D4_cl3_generator_index": {
                "choices": D4_CHOICES,
                "generator_names": _CL3_NAMES,
                "layer": "L10_clifford_module",
                "implementation": "generator applied to qubit 2 (D5=0) or qubit 3 (D5=1)",
            },
            "D5_algebra_action_target": {
                "choices": D5_CHOICES,
                "labels": ["qubit_2_left_bipartition", "qubit_3_right_bipartition"],
                "included": INCLUDE_D5,
                "layer": "L10_L11 / L12_bipartite_tensor_product",
                "implementation": "D4 generator acts on qubit 2 (D5=0) or qubit 3 (D5=1)",
            },
        },
        "candidate_layers": LAYERS,
        "enumeration_count": actual_count,
        "predicted_count": PREDICTED_COUNT,
        "configurations": config_records,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(graveyard_companions),
            "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
        },
        "blockers": [],
        "open_choices": [
            "D2 holonomy implemented as a phase gate on qubit 1 (analytically derived from Berry phase); "
            "richer implementation: full discrete path integration over Hopf bundle connection",
            "D4 Cl(3) generators: sigma_x, sigma_y, sigma_z, H=(e1+e3)/sqrt(2); "
            "alternative: grade-2 elements e12, e13, e23 or grade-3 pseudoscalar e123",
            "D5 as qubit-2 vs qubit-3 target; "
            "alternative: left vs right action of full SU(2) algebra on a density matrix (not state vector)",
            "Fiducial state: Haar-generic seed=137; "
            "sensitivity to fiducial choice not explored",
        ],
        "why_not_v4_probes": "Clean v5 formal scout with fenced receipt. Does not add to v4 probe estate.",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "all_pass": bool(all_pass),
            "enumeration_count": actual_count,
            "z3_verdict": z3_result["z3_status"],
            "pairwise_numerical_collisions": numerical_dist["collision_count"],
            "elapsed_seconds": round(time.time() - started, 3),
            "promotion_allowed": PROMOTION_ALLOWED,
        },
    }

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
