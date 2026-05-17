#!/usr/bin/env python3
"""
sim_paired_chiral_bipartite_logarithmic_negativity_coupling_probe.py
====================================================================

Formal scout — wide-exploration probe from Gemini proposal #2
(provider_receipts/20260515T205043Z_gemini_qit_engines_operational_wide_exploration.json).

Question (constraint-admissibility framing):
  When the Type 1 and Type 2 operational QIT engines are placed on a SHARED
  2-qubit (4-dim) carrier rho_12, with a manifold-derived interaction
  Hamiltonian H_int = J * (sigma_z (x) sigma_z) coupling the two subsystems,
  does the joint state admit non-zero bipartite logarithmic negativity?

  Two readings survive ahead of the probe:
    R1. The two engines couple — joint evolution on the shared carrier admits
        non-zero log negativity across a J sweep, monotone in coupling strength.
    R2. The two engines run side-by-side under H_int but the chiral structure
        (H_TYPE_TWO = -H_TYPE_ONE plus mirrored Lindblad operators) cancels
        out the entanglement source so log negativity stays at zero even at
        large J.

  This scout sweeps J in {0.0, 0.1, 0.3, 0.5, 0.7, 1.0, 2.0} and tracks
  per-substage logarithmic negativity, mutual information, and a concurrence
  proxy for the joint rho_12 across the 32-substage operational walk
  (8 main stages x 4 substages per Type 1, schedule from canonical specs).
  Shuffled-coupling, product-state-only, and large-J / negative-J boundary
  probes serve as negative checks.

Probe family M:
  M = {bipartite_logarithmic_negativity, mutual_information,
       concurrence_proxy} on rho_12 under joint Lindblad evolution.

Constraint set C:
  C = {Lindblad positivity, trace preservation, hermiticity,
       J >= 0 in main sweep, partial-transpose negativity criterion
       under Peres-Horodecki}.

Status:
  classification = "formal_scout"
  promotion_allowed = False
  claim_ceiling: probe-only; not lego, not bridge, not canonical.

Interpreter: /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3

Source alignment:
  - canonical_qit_engine_specs.py (H_TYPE_ONE, H_TYPE_TWO, PERCEPTION_L_MATRICES,
    OPERATOR_GENERATORS, TYPE_ONE_TOPOLOGIES, TYPE_TWO_TOPOLOGIES,
    ENGINE_SCHEDULE_TYPE_ONE/TWO, OPERATOR_BASE_ANGLES)
  - engine_core.py (Lindblad RHS pattern, RK45 solver settings)
"""

from __future__ import annotations

import json
import math
import os
import pathlib
import sys
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import numpy as np
from scipy.integrate import solve_ivp
from scipy.linalg import expm

_ROOT = pathlib.Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from canonical_qit_engine_specs import (
    DTYPE,
    I2,
    H_TYPE_ONE,
    H_TYPE_TWO,
    SX,
    SY,
    SZ,
    PERCEPTION_L_MATRICES,
    MIRROR,
    OPERATOR_GENERATORS,
    OPERATOR_BASE_ANGLES,
    TYPE_ONE_TOPOLOGIES,
    TYPE_TWO_TOPOLOGIES,
    ENGINE_SCHEDULE_TYPE_ONE,
    ENGINE_SCHEDULE_TYPE_TWO,
    N_SUBSTAGES_PER_MAIN,
)

# =====================================================================
# Tool imports
# =====================================================================

TOOL_MANIFEST: dict[str, dict[str, Any]] = {
    "numpy": {"tried": True, "used": True,
              "reason": "load-bearing 4x4 complex density matrix algebra and Pauli tensor products"},
    "scipy": {"tried": True, "used": True,
              "reason": "load-bearing solve_ivp RK45 joint Lindblad integrator and expm operator unitaries"},
    "quimb": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    # Standard SIM_TEMPLATE slots not used here but recorded for manifest completeness.
    "pytorch": {"tried": False, "used": False,
                "reason": "joint 4x4 evolution stays in numpy; no torch autograd needed for scout"},
    "z3": {"tried": False, "used": False,
           "reason": "out-of-scope for scout; symbolic check via sympy instead"},
}

TOOL_INTEGRATION_DEPTH: dict[str, str | None] = {
    "numpy": "load_bearing",
    "scipy": "load_bearing",
    "quimb": None,
    "sympy": None,
    "pytorch": None,
    "z3": None,
}

try:
    import quimb as qu  # noqa: F401
    TOOL_MANIFEST["quimb"]["tried"] = True
    TOOL_MANIFEST["quimb"]["used"] = True
    TOOL_MANIFEST["quimb"]["reason"] = (
        "load-bearing partial transpose + trace-norm path for bipartite "
        "logarithmic negativity on rho_12"
    )
    TOOL_INTEGRATION_DEPTH["quimb"] = "load_bearing"
    QUIMB_AVAILABLE = True
except ImportError:
    TOOL_MANIFEST["quimb"]["reason"] = "not installed; falling back to numpy partial transpose"
    QUIMB_AVAILABLE = False

try:
    import sympy as sp  # noqa: F401
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = (
        "supportive symbolic verification of partial-transpose identity on a small Bell-state case"
    )
    TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"
    SYMPY_AVAILABLE = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"
    SYMPY_AVAILABLE = False


# =====================================================================
# Constants
# =====================================================================

NAME = "sim_paired_chiral_bipartite_logarithmic_negativity_coupling_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only. Probes whether Type 1 and Type 2 QIT engines, coupled "
    "on a shared 2-qubit carrier via H_int = J*(sigma_z (x) sigma_z), admit "
    "non-zero bipartite logarithmic negativity. The receipt does not authorize "
    "lego promotion, coupling-program advancement, bridge claims, axis claims, "
    "or canonical status. Surviving candidates remain candidates."
)

# Initial-state choice surfaced to the result JSON so downstream JSON-only
# readers (audit P3 finding 2026-05-15) see the rationale, not just peak E_N.
INITIAL_STATE_CHOICE = (
    "|+><+| (x) |+><+| chosen so H_int = J*(sigma_z (x) sigma_z) has non-trivial "
    "action; |00><00| gives zero entanglement"
)

RESULT_DIR = _ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "paired_chiral_bipartite_logarithmic_negativity_coupling_probe_results.json"

ODE_RTOL = 1e-7
ODE_ATOL = 1e-9
DT_PER_SUBSTAGE = 0.5   # time per substage in the Lindblad evolution
                       # total walk time = 32 * 0.5 = 16; long enough for
                       # J=0.5 coupling to drive non-trivial entanglement
                       # via H_int = J*sigma_z (x) sigma_z on |+>|+>;
                       # Lindblad rate-scaled by topology rate (~0.13-0.28)
                       # keeps decoherence on a comparable timescale.

J_SWEEP = [0.0, 0.1, 0.3, 0.5, 0.7, 1.0, 2.0]
J_BOUNDARY = [-0.5, 50.0]  # boundary probes: negative J, very large J

# Positive predicates (acceptance thresholds)
THRESH_J0_NEAR_ZERO = 1e-6     # at J=0, peak E_N must stay below this
THRESH_J_MID_MIN = 0.1         # at J=0.5, peak E_N must exceed this
THRESH_J_HIGH_MIN = 0.3        # at J=1.0, peak E_N must exceed this
THRESH_SPEARMAN_MIN = 0.5      # spearman(J, peak E_N) must exceed this in monotone region


# =====================================================================
# 4x4 operator builders
# =====================================================================

def kron2(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """Kronecker product on 2x2 matrices, returning 4x4 complex128."""
    return np.kron(A, B).astype(DTYPE)


I4 = np.eye(4, dtype=DTYPE)


def H_int(j_coupling: float, mode: str = "zz") -> np.ndarray:
    """
    Manifold-derived interaction Hamiltonian on the shared 2-qubit carrier.
      mode="zz":   H_int = J * (sigma_z (x) sigma_z)   — entangling source
      mode="x_id": H_int = J * (sigma_x (x) I)         — single-side, no entanglement source
    """
    if mode == "zz":
        return float(j_coupling) * kron2(SZ, SZ)
    elif mode == "x_id":
        return float(j_coupling) * kron2(SX, I2)
    else:
        raise ValueError(f"unknown H_int mode: {mode}")


def operator_unitary_2x2(op_name: str, sign: int) -> np.ndarray:
    """2x2 operator unitary U = exp(-i * sign * theta_base * G_op)."""
    G = OPERATOR_GENERATORS[op_name]
    theta = OPERATOR_BASE_ANGLES[op_name] * float(sign)
    return expm(-1j * theta * G).astype(DTYPE)


def apply_op_4x4(rho_12: np.ndarray, U_2x2: np.ndarray, side: int) -> np.ndarray:
    """Apply U on side ∈ {0, 1} to the 4x4 joint state."""
    if side == 0:
        U = kron2(U_2x2, I2)
    elif side == 1:
        U = kron2(I2, U_2x2)
    else:
        raise ValueError(side)
    return (U @ rho_12 @ U.conj().T).astype(DTYPE)


def lift_L(L_2x2: np.ndarray, side: int) -> np.ndarray:
    """Lift a single-side Lindblad collapse operator to the 4x4 joint space."""
    if side == 0:
        return kron2(L_2x2, I2)
    elif side == 1:
        return kron2(I2, L_2x2)
    raise ValueError(side)


# =====================================================================
# Density-matrix utilities
# =====================================================================

def hermitize(rho: np.ndarray) -> np.ndarray:
    return ((rho + rho.conj().T) / 2.0).astype(DTYPE)


def normalize_density(rho: np.ndarray) -> np.ndarray:
    rho = hermitize(rho)
    tr = np.trace(rho).real
    if tr <= 1e-15:
        return rho
    return (rho / tr).astype(DTYPE)


def is_valid_density(rho: np.ndarray, tol: float = 1e-6) -> bool:
    if not np.allclose(rho, rho.conj().T, atol=tol):
        return False
    eigs = np.linalg.eigvalsh(hermitize(rho)).real
    if eigs.min() < -tol:
        return False
    if abs(np.trace(rho).real - 1.0) > tol:
        return False
    return True


def partial_trace_4x4(rho_12: np.ndarray, keep: int) -> np.ndarray:
    """
    Partial trace of a 4x4 bipartite density matrix into a 2x2 reduced state.
      keep=0 → return rho_A = Tr_B(rho_12)
      keep=1 → return rho_B = Tr_A(rho_12)
    """
    R = rho_12.reshape(2, 2, 2, 2)  # (a, b, a', b')
    if keep == 0:
        # sum over b: rho_A[a, a'] = sum_b R[a, b, a', b]
        return np.einsum("abcb->ac", R).astype(DTYPE)
    elif keep == 1:
        # sum over a: rho_B[b, b'] = sum_a R[a, b, a, b']
        return np.einsum("abad->bd", R).astype(DTYPE)
    raise ValueError(keep)


def partial_transpose_B_4x4(rho_12: np.ndarray) -> np.ndarray:
    """Partial transpose on subsystem B (the second factor) for a 4x4 state."""
    R = rho_12.reshape(2, 2, 2, 2)  # (a, b, a', b')
    # Swap b and b' indices
    R_pt = np.transpose(R, (0, 3, 2, 1))
    return R_pt.reshape(4, 4).astype(DTYPE)


def trace_norm(M: np.ndarray) -> float:
    """||M||_1 = sum of singular values."""
    sv = np.linalg.svd(M, compute_uv=False)
    return float(sv.sum())


def logarithmic_negativity_numpy(rho_12: np.ndarray) -> float:
    """E_N(rho_12) = log_2 ||rho_12^{T_B}||_1."""
    rho_pt = partial_transpose_B_4x4(rho_12)
    tn = trace_norm(rho_pt)
    return float(np.log2(max(tn, 1e-15)))


def logarithmic_negativity(rho_12: np.ndarray) -> float:
    """
    Logarithmic negativity via quimb if available (load-bearing), else numpy fallback.
    Both reduce to log_2 of the trace norm of the partial transpose on subsystem B.
    """
    if QUIMB_AVAILABLE:
        try:
            return float(qu.logneg(rho_12, [2, 2]))
        except Exception:
            return logarithmic_negativity_numpy(rho_12)
    return logarithmic_negativity_numpy(rho_12)


def von_neumann_entropy(rho: np.ndarray) -> float:
    eigs = np.linalg.eigvalsh(hermitize(rho)).real
    eigs = np.clip(eigs, 1e-15, 1.0)
    eigs = eigs / eigs.sum()
    return float(-(eigs * np.log2(eigs)).sum())


def mutual_information(rho_12: np.ndarray) -> float:
    rho_A = partial_trace_4x4(rho_12, keep=0)
    rho_B = partial_trace_4x4(rho_12, keep=1)
    return max(0.0, von_neumann_entropy(rho_A) + von_neumann_entropy(rho_B) - von_neumann_entropy(rho_12))


def concurrence_proxy(rho_12: np.ndarray) -> float:
    """
    Wootters concurrence on the 2-qubit state rho_12.
    For mixed states: C = max(0, sqrt(l1) - sqrt(l2) - sqrt(l3) - sqrt(l4)) where
    l_i are eigenvalues of R = rho * (Y(x)Y) * rho.conj() * (Y(x)Y) in decreasing order.
    """
    Y_Y = kron2(SY, SY)
    R = rho_12 @ Y_Y @ rho_12.conj() @ Y_Y
    # Eigenvalues of R can be complex due to floating-point; take real parts.
    eigs = np.linalg.eigvals(R).real
    eigs = np.clip(eigs, 0.0, None)
    sqrt_eigs = np.sqrt(np.sort(eigs)[::-1])
    c = sqrt_eigs[0] - sqrt_eigs[1] - sqrt_eigs[2] - sqrt_eigs[3]
    return float(max(0.0, c))


# =====================================================================
# Joint Lindblad evolution on the 4x4 carrier
# =====================================================================

def joint_lindblad_rhs(t: float, rho_flat: np.ndarray,
                      H_total: np.ndarray,
                      L_list: list[np.ndarray]) -> np.ndarray:
    """
    Joint Lindblad RHS on the 4x4 carrier.
      d rho / dt = -i [H_total, rho] + sum_k (L_k rho L_k^† - 1/2 {L_k^† L_k, rho})
    """
    rho = rho_flat.reshape(4, 4).astype(DTYPE)
    commutator = H_total @ rho - rho @ H_total
    dissipator = np.zeros_like(rho)
    for L in L_list:
        Ldag = L.conj().T
        dissipator += L @ rho @ Ldag - 0.5 * (Ldag @ L @ rho + rho @ Ldag @ L)
    drho = -1j * commutator + dissipator
    return drho.reshape(-1)


def joint_lindblad_step(rho_12: np.ndarray,
                       H_total: np.ndarray,
                       L_list: list[np.ndarray],
                       dt: float) -> np.ndarray:
    """RK45 step of the joint Lindblad on the 4x4 carrier, packed real+imag for solve_ivp."""
    rho0 = rho_12.reshape(-1).astype(DTYPE)
    packed = np.concatenate([rho0.real, rho0.imag])

    def rhs_real(t: float, y_packed: np.ndarray) -> np.ndarray:
        n = len(y_packed) // 2
        y = (y_packed[:n] + 1j * y_packed[n:]).astype(DTYPE)
        dy = joint_lindblad_rhs(t, y, H_total, L_list)
        return np.concatenate([dy.real, dy.imag])

    sol = solve_ivp(rhs_real, (0.0, dt), packed, method="RK45",
                    rtol=ODE_RTOL, atol=ODE_ATOL)
    y_final = sol.y[:, -1]
    n = len(y_final) // 2
    rho_final = (y_final[:n] + 1j * y_final[n:]).reshape(4, 4).astype(DTYPE)
    return normalize_density(rho_final)


# =====================================================================
# Type 2 Lindblad (mirrored)
# =====================================================================

def L_perception(perception: str, engine_type: int) -> np.ndarray:
    """
    Per-perception 2x2 Lindblad collapse for an engine type, mirrored for Type 2,
    scaled by sqrt(topology_rate) so the Lindblad rate matches the canonical
    per-topology rate from TYPE_ONE_TOPOLOGIES / TYPE_TWO_TOPOLOGIES.

    Convention: dissipator = L rho L^dag - 1/2 {L^dag L, rho} with L = sqrt(gamma) * L_base.
    """
    L_base = PERCEPTION_L_MATRICES[perception]
    if engine_type == 0:
        topo = TYPE_ONE_TOPOLOGIES[perception]
        L = L_base
    else:
        topo = TYPE_TWO_TOPOLOGIES[perception]
        L = (MIRROR @ L_base @ MIRROR)
    gamma = float(topo["rate"])
    return (math.sqrt(gamma) * L).astype(DTYPE)


# =====================================================================
# 32-substage walk on the joint carrier
# =====================================================================

def joint_substage_walk(j_coupling: float,
                       int_mode: str = "zz",
                       product_only: bool = False) -> dict[str, Any]:
    """
    Walk the 32-substage operational schedule on the shared 2-qubit carrier.

    Each of the 8 main stages has 4 substages (operator, terrain, manifold,
    loop placement). We model the substages as a small repeated joint Lindblad
    step at the (perception, loop_class) Hamiltonians and operator rotations,
    coupling through H_int on every substage.

    Parameters:
      j_coupling: coupling strength J
      int_mode: "zz" canonical or "x_id" shuffled (single-side, no entanglement source)
      product_only: if True, evolve rho_A and rho_B independently and return
                    rho_A (x) rho_B at each substage (entanglement source removed
                    by construction)

    Returns dict with per-substage E_N, MI, concurrence, and Hamiltonian/Lindblad
    bookkeeping (substage count, peak metrics).

    Initial state: |+>|+> = (|0>+|1>)/sqrt(2) (x) (|0>+|1>)/sqrt(2). Chosen so
    that H_int = J*(sigma_z (x) sigma_z) has non-trivial action — diagonal
    sigma_z (x) sigma_z annihilates |00>, so a product state on the X-axis
    is required to exercise the entangling source. This is still a separable
    initial state: E_N(|+><+| (x) |+><+|) = 0 by construction at t=0.
    """
    plus = np.array([1.0, 1.0], dtype=DTYPE) / math.sqrt(2.0)
    rho_A0 = np.outer(plus, plus.conj()).astype(DTYPE)
    rho_B0 = rho_A0.copy()
    rho_12 = np.kron(rho_A0, rho_B0).astype(DTYPE)

    # For product-only baseline:
    rho_A = rho_A0.copy()
    rho_B = rho_B0.copy()

    en_trace: list[float] = []
    mi_trace: list[float] = []
    conc_trace: list[float] = []
    purity_trace: list[float] = []

    sched1 = ENGINE_SCHEDULE_TYPE_ONE
    sched2 = ENGINE_SCHEDULE_TYPE_TWO

    n_main = len(sched1)  # 8
    n_sub = N_SUBSTAGES_PER_MAIN  # 4

    for main_idx in range(n_main):
        perc1, loop1 = sched1[main_idx]
        perc2, loop2 = sched2[main_idx]
        topo1 = TYPE_ONE_TOPOLOGIES[perc1]
        topo2 = TYPE_TWO_TOPOLOGIES[perc2]
        op1, sign1 = topo1[loop1]["op"], int(topo1[loop1]["sign"])
        op2, sign2 = topo2[loop2]["op"], int(topo2[loop2]["sign"])

        L1_2x2 = L_perception(perc1, engine_type=0)
        L2_2x2 = L_perception(perc2, engine_type=1)
        L_joint_1 = lift_L(L1_2x2, side=0)
        L_joint_2 = lift_L(L2_2x2, side=1)

        # Build joint H. H_TYPE_ONE acts on side 0, H_TYPE_TWO on side 1, plus H_int.
        H_total = (
            kron2(H_TYPE_ONE, I2)
            + kron2(I2, H_TYPE_TWO)
            + H_int(j_coupling, mode=int_mode)
        )

        for substage_idx in range(n_sub):
            # Apply a brief operator rotation at substage 0 of each main stage on each side.
            if substage_idx == 0:
                U1 = operator_unitary_2x2(op1, sign1)
                U2 = operator_unitary_2x2(op2, sign2)
                if not product_only:
                    rho_12 = apply_op_4x4(rho_12, U1, side=0)
                    rho_12 = apply_op_4x4(rho_12, U2, side=1)
                else:
                    rho_A = U1 @ rho_A @ U1.conj().T
                    rho_B = U2 @ rho_B @ U2.conj().T

            # Joint Lindblad step
            if not product_only:
                rho_12 = joint_lindblad_step(
                    rho_12, H_total, [L_joint_1, L_joint_2], DT_PER_SUBSTAGE
                )
            else:
                # Independent single-side Lindblad steps (no joint H_int reaches the product)
                H_A = H_TYPE_ONE
                H_B = H_TYPE_TWO
                rho_A = _single_side_step(rho_A, H_A, L1_2x2, DT_PER_SUBSTAGE)
                rho_B = _single_side_step(rho_B, H_B, L2_2x2, DT_PER_SUBSTAGE)
                rho_12 = np.kron(rho_A, rho_B).astype(DTYPE)
                rho_12 = normalize_density(rho_12)

            # Measure
            en_trace.append(logarithmic_negativity(rho_12))
            mi_trace.append(mutual_information(rho_12))
            conc_trace.append(concurrence_proxy(rho_12))
            purity_trace.append(float(np.real(np.trace(rho_12 @ rho_12))))

    return {
        "n_substages": len(en_trace),
        "log_negativity_trace": en_trace,
        "mutual_information_trace": mi_trace,
        "concurrence_trace": conc_trace,
        "purity_trace": purity_trace,
        "peak_log_negativity": float(max(en_trace)) if en_trace else 0.0,
        "peak_mutual_information": float(max(mi_trace)) if mi_trace else 0.0,
        "peak_concurrence": float(max(conc_trace)) if conc_trace else 0.0,
        "final_log_negativity": float(en_trace[-1]) if en_trace else 0.0,
        "final_mutual_information": float(mi_trace[-1]) if mi_trace else 0.0,
        "rho_12_valid": bool(is_valid_density(rho_12, tol=1e-3)),
    }


def _single_side_step(rho: np.ndarray, H: np.ndarray, L: np.ndarray, dt: float) -> np.ndarray:
    """Single-side 2x2 Lindblad step (used by product_only baseline)."""
    rho0 = rho.reshape(-1).astype(DTYPE)
    packed = np.concatenate([rho0.real, rho0.imag])

    def rhs_real(t: float, y_packed: np.ndarray) -> np.ndarray:
        n = len(y_packed) // 2
        y = (y_packed[:n] + 1j * y_packed[n:]).reshape(2, 2).astype(DTYPE)
        Ldag = L.conj().T
        commut = H @ y - y @ H
        diss = L @ y @ Ldag - 0.5 * (Ldag @ L @ y + y @ Ldag @ L)
        dy = -1j * commut + diss
        return np.concatenate([dy.reshape(-1).real, dy.reshape(-1).imag])

    sol = solve_ivp(rhs_real, (0.0, dt), packed, method="RK45",
                    rtol=ODE_RTOL, atol=ODE_ATOL)
    y_final = sol.y[:, -1]
    n = len(y_final) // 2
    rho_f = (y_final[:n] + 1j * y_final[n:]).reshape(2, 2).astype(DTYPE)
    return normalize_density(rho_f)


# =====================================================================
# Spearman rank correlation (no scipy.stats dependency on this slot)
# =====================================================================

def spearman(x: list[float], y: list[float]) -> float:
    n = len(x)
    if n != len(y) or n < 2:
        return 0.0

    def rank(arr: list[float]) -> list[float]:
        idx = sorted(range(n), key=lambda i: arr[i])
        ranks = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and arr[idx[j + 1]] == arr[idx[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0  # 1-indexed average rank
            for k in range(i, j + 1):
                ranks[idx[k]] = avg
            i = j + 1
        return ranks

    rx = rank(x)
    ry = rank(y)
    mx = sum(rx) / n
    my = sum(ry) / n
    num = sum((rx[i] - mx) * (ry[i] - my) for i in range(n))
    denom_x = math.sqrt(sum((rx[i] - mx) ** 2 for i in range(n)))
    denom_y = math.sqrt(sum((ry[i] - my) ** 2 for i in range(n)))
    if denom_x < 1e-15 or denom_y < 1e-15:
        return 0.0
    return float(num / (denom_x * denom_y))


# =====================================================================
# Sympy partial-transpose verification (supportive)
# =====================================================================

def sympy_partial_transpose_check() -> dict[str, Any]:
    """
    Supportive symbolic verification of the partial-transpose identity on the
    Bell state |Phi+> = (|00>+|11>)/sqrt(2). Its partial transpose has
    eigenvalues {1/2, 1/2, 1/2, -1/2}, so ||rho^{T_B}||_1 = 2 and log_neg = 1.
    """
    if not SYMPY_AVAILABLE:
        return {"status": "skipped", "reason": "sympy not available"}
    import sympy as spm
    half = spm.Rational(1, 2)
    # Bell state density rho = 1/2 [[1,0,0,1],[0,0,0,0],[0,0,0,0],[1,0,0,1]]
    rho = spm.Matrix([
        [half, 0, 0, half],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [half, 0, 0, half],
    ])
    # Partial transpose on B swaps |01><10| with |00><11| structure.
    # PT on B: rho^{T_B}[a,b,a',b'] = rho[a,b',a',b].
    pt = spm.zeros(4, 4)
    for a in range(2):
        for b in range(2):
            for ap in range(2):
                for bp in range(2):
                    i = 2 * a + b
                    j = 2 * ap + bp
                    i2 = 2 * a + bp
                    j2 = 2 * ap + b
                    pt[i, j] = rho[i2, j2]
    eigval_mult = pt.eigenvals()  # dict: eigenvalue -> multiplicity
    # Sum of |eigenvalue| * multiplicity (trace norm of a Hermitian matrix)
    tn = sum(abs(e) * m for e, m in eigval_mult.items())
    log_neg = spm.log(tn, 2)
    return {
        "status": "ok",
        "bell_state_partial_transpose_eigenvalues": {str(e): int(m) for e, m in eigval_mult.items()},
        "bell_state_trace_norm": str(tn),
        "bell_state_log_negativity": str(log_neg),
        "matches_expected_1": bool(spm.simplify(tn - 2) == 0),
    }


# =====================================================================
# Positive admission tests (canonical sweep)
# =====================================================================

def run_positive_tests() -> dict[str, Any]:
    """Sweep J ∈ J_SWEEP with the canonical zz coupling; measure E_N at each J."""
    per_j: dict[str, Any] = {}
    js: list[float] = []
    peaks: list[float] = []
    finals: list[float] = []
    for j in J_SWEEP:
        rec = joint_substage_walk(j, int_mode="zz", product_only=False)
        per_j[f"J_{j}"] = rec
        js.append(j)
        peaks.append(rec["peak_log_negativity"])
        finals.append(rec["final_log_negativity"])

    sp_corr = spearman(js, peaks)

    # Predicate checks
    j0_peak = per_j["J_0.0"]["peak_log_negativity"]
    j_mid_peak = per_j["J_0.5"]["peak_log_negativity"]
    j_high_peak = per_j["J_1.0"]["peak_log_negativity"]

    cond_j0 = j0_peak < THRESH_J0_NEAR_ZERO
    cond_mid = j_mid_peak > THRESH_J_MID_MIN
    cond_high = j_high_peak > THRESH_J_HIGH_MIN
    cond_spearman = sp_corr > THRESH_SPEARMAN_MIN

    return {
        "per_j": per_j,
        "js": js,
        "peaks": peaks,
        "finals": finals,
        "spearman_J_vs_peak_E_N": sp_corr,
        "predicate_J0_near_zero": {
            "value": j0_peak,
            "threshold": THRESH_J0_NEAR_ZERO,
            "survived": bool(cond_j0),
        },
        "predicate_J_mid_couples": {
            "value": j_mid_peak,
            "threshold": THRESH_J_MID_MIN,
            "survived": bool(cond_mid),
        },
        "predicate_J_high_strong": {
            "value": j_high_peak,
            "threshold": THRESH_J_HIGH_MIN,
            "survived": bool(cond_high),
        },
        "predicate_spearman_monotone": {
            "value": sp_corr,
            "threshold": THRESH_SPEARMAN_MIN,
            "survived": bool(cond_spearman),
        },
    }


# =====================================================================
# Negative exclusion tests
# =====================================================================

def run_negative_tests() -> dict[str, Any]:
    """
    Two exclusion probes:
      1. Shuffled-coupling: H_int = J * (sigma_x (x) I). Single-side; cannot
         source entanglement. At J=1.0, peak E_N should remain near zero.
      2. Product-state-only: track rho_A (x) rho_B independently. Construction
         excludes entanglement by definition; peak E_N(rho_A (x) rho_B) ≈ 0.
    """
    shuffled = joint_substage_walk(j_coupling=1.0, int_mode="x_id", product_only=False)
    product = joint_substage_walk(j_coupling=1.0, int_mode="zz", product_only=True)

    cond_shuffled = shuffled["peak_log_negativity"] < 1e-3
    cond_product = product["peak_log_negativity"] < 1e-6

    return {
        "shuffled_coupling_x_id_at_J_1.0": shuffled,
        "product_state_only_at_J_1.0": product,
        "predicate_shuffled_excludes_entanglement": {
            "value": shuffled["peak_log_negativity"],
            "threshold": 1e-3,
            "excluded": bool(cond_shuffled),
        },
        "predicate_product_excludes_entanglement": {
            "value": product["peak_log_negativity"],
            "threshold": 1e-6,
            "excluded": bool(cond_product),
        },
    }


# =====================================================================
# Boundary probes
# =====================================================================

def run_boundary_tests() -> dict[str, Any]:
    """
    Boundary probes:
      - Negative J (sign-flipped Hamiltonian): entanglement should still appear.
      - Very large J (J=50): frozen subspace / strong-coupling regime; E_N may
        plateau or saturate rather than continue growing.
    Both are reported, neither is required to pass for all_pass; they document
    where M loses resolution.
    """
    recs: dict[str, Any] = {}
    for j in J_BOUNDARY:
        rec = joint_substage_walk(j, int_mode="zz", product_only=False)
        recs[f"J_{j}"] = rec
    neg_J = recs[f"J_{J_BOUNDARY[0]}"]
    big_J = recs[f"J_{J_BOUNDARY[1]}"]
    return {
        "boundary_J_records": recs,
        "negative_J_still_couples": bool(neg_J["peak_log_negativity"] > 1e-3),
        "very_large_J_peak_E_N": big_J["peak_log_negativity"],
        "very_large_J_purity_final": big_J["purity_trace"][-1] if big_J["purity_trace"] else None,
        "boundary_note": (
            "Negative J flips the Hamiltonian sign but the entangling source "
            "(sigma_z (x) sigma_z) still couples the two engines. Very large J "
            "drives the joint state toward the sigma_z (x) sigma_z eigenbasis; "
            "E_N may saturate or oscillate."
        ),
    }


# =====================================================================
# Main
# =====================================================================

def main() -> dict[str, Any]:
    t0 = time.time()

    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    sympy_check = sympy_partial_transpose_check()

    # Acceptance logic
    p_j0 = positive["predicate_J0_near_zero"]["survived"]
    p_mid = positive["predicate_J_mid_couples"]["survived"]
    p_high = positive["predicate_J_high_strong"]["survived"]
    p_sp = positive["predicate_spearman_monotone"]["survived"]
    n_shuf = negative["predicate_shuffled_excludes_entanglement"]["excluded"]
    n_prod = negative["predicate_product_excludes_entanglement"]["excluded"]

    criteria_checked = [
        "C1_J0_peak_E_N_near_zero",
        "C2_J0.5_peak_E_N_exceeds_0.1",
        "C3_J1.0_peak_E_N_exceeds_0.3",
        "C4_spearman_J_vs_peak_E_N_positive_monotone",
        "C5_shuffled_x_id_coupling_excludes_entanglement",
        "C6_product_state_only_excludes_entanglement",
    ]

    all_pass = bool(p_j0 and p_mid and p_high and p_sp and n_shuf and n_prod)

    # Surviving alternatives — both readings remain candidates without further work.
    # Schema upgrade (audit P3 finding 2026-05-15): list[dict] with
    # {reading, status} so JSON-only readers see the initial-state-choice
    # caveat as an open candidate even when all_pass=True.
    surviving_alternatives: list[dict[str, str]] = [
        {
            "reading": (
                "different initial-state choices may give different peak E_N "
                "curves"
            ),
            "status": "open",
        },
    ]
    if not p_mid or not p_high:
        surviving_alternatives.append({
            "reading": (
                "R2 survives: chiral cancellation may suppress entanglement at "
                "this J range; extend J sweep or use non-mirrored Lindblad to "
                "rule out."
            ),
            "status": "open",
        })
    if not n_shuf:
        surviving_alternatives.append({
            "reading": (
                "Shuffled-coupling did not exclude entanglement — "
                "partial-transpose criterion may still admit it under x_id "
                "mode; investigate H_int symmetry."
            ),
            "status": "open",
        })

    elapsed = time.time() - t0

    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        # claim_ceiling upgraded from str to dict so the initial-state-choice
        # caveat is co-located with the ceiling text in the JSON. Plain
        # `claim_ceiling_text` retained for backwards-compatible readers.
        "claim_ceiling": {
            "text": CLAIM_CEILING,
            "initial_state_choice": INITIAL_STATE_CHOICE,
            "out_of_scope": [
                "computational-basis initial states",
                "alternative entangling Hamiltonians beyond sigma_z (x) sigma_z",
            ],
            "surviving_alternatives_summary": [
                {
                    "reading": (
                        "different initial-state choices may give different "
                        "peak E_N curves"
                    ),
                    "status": "open",
                },
            ],
        },
        "claim_ceiling_text": CLAIM_CEILING,
        "probe_family": (
            "M_bipartite_log_negativity_mutual_information_concurrence_on_rho_12_under_joint_lindblad"
        ),
        "constraint_set": (
            "C_lindblad_positivity_trace_preservation_hermiticity_with_J_zz_coupling_and_peres_horodecki"
        ),
        "interpreter": "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "config": {
            "J_sweep": J_SWEEP,
            "J_boundary": J_BOUNDARY,
            "dt_per_substage": DT_PER_SUBSTAGE,
            "ode_rtol": ODE_RTOL,
            "ode_atol": ODE_ATOL,
            "n_main_stages": 8,
            "n_substages_per_main": N_SUBSTAGES_PER_MAIN,
            "n_total_substages_per_walk": 32,
            "carrier_dim": 4,
            "H_int_mode_canonical": "zz",
            "H_int_mode_shuffled": "x_id",
        },
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "sympy_partial_transpose_check": sympy_check,
        "surviving_alternatives": surviving_alternatives,
        "next_lego_target": "none",
        "promotion_condition": (
            "requires a separate reconciled queue row before lego/coupling use; "
            "scout-only evidence does not authorize promotion"
        ),
        "blocked_until": (
            "tool-stage gate and per-axis lego catalogue admit a coupling-program "
            "row that maps to bipartite negativity on the paired engines"
        ),
        "demotion_condition": (
            "demote if any acceptance criterion C1-C6 fails on rerun, or if the "
            "result is cited outside the formal-scout ceiling"
        ),
        "out_of_scope": [
            "no lego promotion from this scout result alone",
            "no bridge, axis, engine-canonical, or coupling-program claim",
            "no extension beyond 2-qubit carriers",
            "no CHSH or symbolic Bell-inequality violation proofs",
            "no trainable readouts",
            "computational-basis initial states",
            "alternative entangling Hamiltonians beyond sigma_z (x) sigma_z",
        ],
        "all_pass": all_pass,
        "criteria_checked": criteria_checked,
        "elapsed_seconds": elapsed,
    }

    return results


if __name__ == "__main__":
    results = main()

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print("=" * 78)
    print(f"{NAME}")
    print("=" * 78)
    print(f"classification          : {results['classification']}")
    print(f"promotion_allowed       : {results['promotion_allowed']}")
    print(f"all_pass                : {results['all_pass']}")
    print(f"criteria_checked        : {len(results['criteria_checked'])} criteria")
    print(f"elapsed_seconds         : {results['elapsed_seconds']:.2f}")
    print()
    print("Per-J peak log negativity (canonical zz coupling):")
    for j, peak in zip(results["positive"]["js"], results["positive"]["peaks"]):
        marker = ""
        if abs(j - 0.5) < 1e-9:
            marker = "  <-- J=0.5 predicate"
        elif abs(j - 1.0) < 1e-9:
            marker = "  <-- J=1.0 predicate"
        print(f"  J={j:5.2f}  peak_E_N = {peak:.6f}{marker}")
    print()
    print(f"Spearman(J, peak E_N)   : {results['positive']['spearman_J_vs_peak_E_N']:.4f}")
    print(f"Shuffled x_id peak E_N  : {results['negative']['shuffled_coupling_x_id_at_J_1.0']['peak_log_negativity']:.6e}")
    print(f"Product-only peak E_N   : {results['negative']['product_state_only_at_J_1.0']['peak_log_negativity']:.6e}")
    print(f"Boundary J=-0.5 peak    : {results['boundary']['boundary_J_records']['J_-0.5']['peak_log_negativity']:.6f}")
    print(f"Boundary J=50 peak      : {results['boundary']['boundary_J_records']['J_50.0']['peak_log_negativity']:.6f}")
    print()
    print(f"Result JSON: {OUT_PATH}")
    print("=" * 78)

    sys.exit(0 if results["all_pass"] else 1)
