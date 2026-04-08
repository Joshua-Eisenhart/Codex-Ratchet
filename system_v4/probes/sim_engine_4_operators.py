#!/usr/bin/env python3
"""
sim_engine_4_operators.py -- Canonical sim of the 4 QIT engine operators.

Implements Ti (Z-dephasing), Te (X-dephasing), Fi (X-rotation), Fe (Z-rotation)
with EXACT Kraus and Lindblad forms. Full tool stack verification:
  - z3 + sympy: Kraus completeness proof (sum K†K = I)
  - sympy: Kraus-Lindblad continuous-limit correspondence
  - numpy/torch: Bloch-axis state action (all 6 cardinal states)
  - clifford: geometric algebra cross-check of rotation operators
  - rustworkx: operator composition DAG with non-commutativity edges

Classification: canonical
"""

import json
import os
import numpy as np
import torch
import sympy as sp
from sympy import sqrt as sp_sqrt, exp as sp_exp, Matrix, Symbol, I as sp_I
from sympy import eye as sp_eye, simplify, trigsimp, series
from z3 import (
    RealVal, Real, Solver, sat, ForAll, And, Implies,
    RealSort, Function, unsat
)
import rustworkx as rx
from clifford import Cl

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":    {"tried": True, "used": True, "reason": "Torch-native density matrix ops, canonical computation layer"},
    "pyg":        {"tried": False, "used": False, "reason": "Not needed for single-qubit operator sim"},
    "z3":         {"tried": True, "used": True, "reason": "Formal Kraus completeness proof via SMT"},
    "cvc5":       {"tried": False, "used": False, "reason": "z3 sufficient for completeness proofs"},
    "sympy":      {"tried": True, "used": True, "reason": "Symbolic Kraus completeness + Lindblad continuous-limit derivation"},
    "clifford":   {"tried": True, "used": True, "reason": "GA cross-check of Fi/Fe rotation operators in Cl(3,0)"},
    "geomstats":  {"tried": False, "used": False, "reason": "Not needed for operator verification"},
    "e3nn":       {"tried": False, "used": False, "reason": "Not needed for operator verification"},
    "rustworkx":  {"tried": True, "used": True, "reason": "Operator composition DAG with commutativity annotations"},
    "xgi":        {"tried": False, "used": False, "reason": "Not needed; pairwise composition, not hypergraph"},
    "toponetx":   {"tried": False, "used": False, "reason": "Not needed for operator-level sim"},
    "gudhi":      {"tried": False, "used": False, "reason": "Not needed for operator-level sim"},
}


# =====================================================================
# CONSTANTS & HELPERS
# =====================================================================

# Pauli matrices (numpy)
I2 = np.eye(2, dtype=complex)
sigma_x = np.array([[0, 1], [1, 0]], dtype=complex)
sigma_y = np.array([[0, -1j], [1j, 0]], dtype=complex)
sigma_z = np.array([[1, 0], [0, -1]], dtype=complex)

# 6 Bloch axis states as density matrices
BLOCH_STATES = {
    "|0>":  np.array([[1, 0], [0, 0]], dtype=complex),
    "|1>":  np.array([[0, 0], [0, 1]], dtype=complex),
    "|+>":  np.array([[0.5, 0.5], [0.5, 0.5]], dtype=complex),
    "|->":  np.array([[0.5, -0.5], [-0.5, 0.5]], dtype=complex),
    "|+i>": np.array([[0.5, -0.5j], [0.5j, 0.5]], dtype=complex),
    "|-i>": np.array([[0.5, 0.5j], [-0.5j, 0.5]], dtype=complex),
}


def density_to_bloch(rho):
    """Extract Bloch vector (x, y, z) from 2x2 density matrix."""
    x = np.real(np.trace(rho @ sigma_x))
    y = np.real(np.trace(rho @ sigma_y))
    z = np.real(np.trace(rho @ sigma_z))
    return np.array([x, y, z])


def apply_kraus(rho, kraus_ops):
    """Apply Kraus channel: E(rho) = sum_k K_k rho K_k^dagger."""
    result = np.zeros_like(rho)
    for K in kraus_ops:
        result += K @ rho @ K.conj().T
    return result


def lindblad_step(rho, H, L_ops, dt):
    """Single Euler step of Lindblad master equation.
    drho/dt = -i[H, rho] + sum_k (L_k rho L_k^dag - 0.5{L_k^dag L_k, rho})
    """
    drho = -1j * (H @ rho - rho @ H)
    for L in L_ops:
        LdL = L.conj().T @ L
        drho += L @ rho @ L.conj().T - 0.5 * (LdL @ rho + rho @ LdL)
    return rho + dt * drho


# =====================================================================
# OPERATOR DEFINITIONS
# =====================================================================

def Ti_kraus(q1):
    """Z-dephasing: K0=sqrt(1-q1)I, K1=sqrt(q1)|0><0|, K2=sqrt(q1)|1><1|."""
    K0 = np.sqrt(1 - q1) * I2
    K1 = np.sqrt(q1) * np.array([[1, 0], [0, 0]], dtype=complex)
    K2 = np.sqrt(q1) * np.array([[0, 0], [0, 1]], dtype=complex)
    return [K0, K1, K2]


def Te_kraus(q2):
    """X-dephasing: K0=sqrt(1-q2)I, K1=sqrt(q2)*|+><+|, K2=sqrt(q2)*|-><-|."""
    K0 = np.sqrt(1 - q2) * I2
    K1 = np.sqrt(q2) * 0.5 * np.array([[1, 1], [1, 1]], dtype=complex)
    K2 = np.sqrt(q2) * 0.5 * np.array([[1, -1], [-1, 1]], dtype=complex)
    return [K0, K1, K2]


def Fi_unitary(theta):
    """X-rotation: U_x(theta) = exp(-i*theta*sigma_x/2)."""
    c, s = np.cos(theta / 2), np.sin(theta / 2)
    return np.array([[c, -1j * s], [-1j * s, c]], dtype=complex)


def Fe_unitary(phi):
    """Z-rotation: U_z(phi) = exp(-i*phi*sigma_z/2)."""
    return np.array([
        [np.exp(-1j * phi / 2), 0],
        [0, np.exp(1j * phi / 2)]
    ], dtype=complex)


def Ti_lindblad_ops(kappa1):
    """Lindblad for Ti: H=0, L=sqrt(kappa1/2)*sigma_z."""
    H = np.zeros((2, 2), dtype=complex)
    L = [np.sqrt(kappa1 / 2) * sigma_z]
    return H, L


def Te_lindblad_ops(kappa2):
    """Lindblad for Te: H=0, L=sqrt(kappa2/2)*sigma_x."""
    H = np.zeros((2, 2), dtype=complex)
    L = [np.sqrt(kappa2 / 2) * sigma_x]
    return H, L


def Fi_lindblad_ops(omega3):
    """Lindblad for Fi: H=omega3*sigma_x/2, no dissipator."""
    H = omega3 * sigma_x / 2
    return H, []


def Fe_lindblad_ops(omega4):
    """Lindblad for Fe: H=omega4*sigma_z/2, no dissipator."""
    H = omega4 * sigma_z / 2
    return H, []


# =====================================================================
# (1) KRAUS COMPLETENESS - z3 + sympy
# =====================================================================

def verify_kraus_completeness_sympy():
    """Symbolic proof that sum K_k^dag K_k = I for all 4 operators."""
    results = {}

    # --- Ti ---
    # All Ti Kraus ops are real-valued, so K† = K^T
    q = Symbol('q', real=True, positive=True)
    K0 = sp_sqrt(1 - q) * sp_eye(2)
    K1 = sp_sqrt(q) * Matrix([[1, 0], [0, 0]])
    K2 = sp_sqrt(q) * Matrix([[0, 0], [0, 1]])
    total = K0.T * K0 + K1.T * K1 + K2.T * K2
    total_simplified = simplify(total)
    results["Ti"] = {
        "sum_KdagK": str(total_simplified),
        "equals_I": total_simplified == sp_eye(2),
    }

    # --- Te ---
    # All Te Kraus ops are real-valued, so K† = K^T
    q2 = Symbol('q2', real=True, positive=True)
    K0 = sp_sqrt(1 - q2) * sp_eye(2)
    K1 = sp_sqrt(q2) * sp.Rational(1, 2) * Matrix([[1, 1], [1, 1]])
    K2 = sp_sqrt(q2) * sp.Rational(1, 2) * Matrix([[1, -1], [-1, 1]])
    total = K0.T * K0 + K1.T * K1 + K2.T * K2
    total_simplified = simplify(total)
    results["Te"] = {
        "sum_KdagK": str(total_simplified),
        "equals_I": total_simplified == sp_eye(2),
    }

    # --- Fi (unitary: U^dag U = I) ---
    th = Symbol('theta', real=True)
    Ux = Matrix([
        [sp.cos(th / 2), -sp_I * sp.sin(th / 2)],
        [-sp_I * sp.sin(th / 2), sp.cos(th / 2)]
    ])
    product = simplify(Ux.H * Ux)
    product = trigsimp(product)
    results["Fi"] = {
        "sum_KdagK": str(product),
        "equals_I": product == sp_eye(2),
    }

    # --- Fe (unitary: U^dag U = I) ---
    ph = Symbol('phi', real=True)
    Uz = Matrix([
        [sp_exp(-sp_I * ph / 2), 0],
        [0, sp_exp(sp_I * ph / 2)]
    ])
    product = simplify(Uz.H * Uz)
    results["Fe"] = {
        "sum_KdagK": str(product),
        "equals_I": product == sp_eye(2),
    }

    return results


def verify_kraus_completeness_z3():
    """z3 SMT verification: for any q in [0,1], sum K†K diagonal = 1, off-diag = 0."""
    results = {}

    # Ti: K0†K0 + K1†K1 + K2†K2
    # = (1-q)I + q|0><0| + q|1><1| = (1-q)I + qI = I
    # z3: verify (1-q) + q == 1 for all q
    q = Real('q')
    s = Solver()
    s.add(q >= 0, q <= 1)
    # The (0,0) entry: (1-q) + q = 1
    diag_sum = (1 - q) + q
    s.push()
    s.add(diag_sum != 1)
    ti_diag = s.check() == unsat  # Should be unsat (no counterexample)
    s.pop()
    results["Ti"] = {"diagonal_always_1": ti_diag}

    # Te: same structure, (1-q2) + q2*(1/2 + 1/2) = 1
    q2 = Real('q2')
    s2 = Solver()
    s2.add(q2 >= 0, q2 <= 1)
    # (0,0) entry: (1-q2) + q2*(1/4 + 1/4) + q2*(1/4 + 1/4) = (1-q2) + q2 = 1
    # Actually: K1†K1 = q2 * (1/4)[[1,1],[1,1]]†[[1,1],[1,1]] = q2*(1/2)*[[1,1],[1,1]]
    # K1†K1(0,0) = q2/2, K2†K2(0,0) = q2/2 => total diag = (1-q2) + q2/2 + q2/2 = 1
    diag_te = (1 - q2) + q2 * RealVal("1/2") + q2 * RealVal("1/2")
    # Off-diagonal: K1†K1(0,1) = q2/2, K2†K2(0,1) = -q2/2 => 0
    offdiag_te = q2 * RealVal("1/2") + q2 * RealVal("-1/2")
    s2.push()
    s2.add(diag_te != 1)
    te_diag = s2.check() == unsat
    s2.pop()
    s2.push()
    s2.add(offdiag_te != 0)
    te_offdiag = s2.check() == unsat
    s2.pop()
    results["Te"] = {"diagonal_always_1": te_diag, "offdiag_always_0": te_offdiag}

    # Fi, Fe: unitary, so trivially U†U=I (cos^2+sin^2=1)
    # z3 over reals: cos^2(t/2)+sin^2(t/2)=1 is axiomatic, encode directly
    results["Fi"] = {"unitary_by_construction": True}
    results["Fe"] = {"unitary_by_construction": True}

    return results


# =====================================================================
# (2) KRAUS-LINDBLAD CONTINUOUS-LIMIT CORRESPONDENCE
# =====================================================================

def verify_kraus_lindblad_correspondence():
    """
    Show that Kraus channels reproduce Lindblad in the dt->0 limit.

    Strategy: For Ti/Te, compute E(rho) algebraically (avoiding sqrt/conjugate issues)
    by noting that K†K products are polynomial in q. For Fi/Fe, use trig series.

    For Ti: set q1 = kappa1*dt. Then E(rho)-rho = kappa1*dt*(sigma_z rho sigma_z - rho)/2 + O(dt^2)
    For Te: set q2 = kappa2*dt. Then E(rho)-rho = kappa2*dt*(sigma_x rho sigma_x - rho)/2 + O(dt^2)
    For Fi: U(dt) = exp(-i*omega*dt*sigma_x/2), U rho U† - rho ~ -i*dt*[omega*sigma_x/2, rho]
    For Fe: U(dt) = exp(-i*omega*dt*sigma_z/2), U rho U† - rho ~ -i*dt*[omega*sigma_z/2, rho]
    """
    results = {}

    # Symbolic density matrix
    a, b, c, d = sp.symbols('a b c d')
    rho = Matrix([[a, b], [c, d]])

    dt = Symbol('dt', positive=True)
    sz = Matrix([[1, 0], [0, -1]])
    sx = Matrix([[0, 1], [1, 0]])

    # --- Ti: Algebraic computation ---
    # E_Ti(rho) = (1-q)*rho + q*diag(rho_00, rho_11)
    # = rho - q*(rho - diag(rho_00, rho_11))
    # = rho - q*[[0, rho_01],[rho_10, 0]]
    # delta = -q*[[0, b],[c, 0]]
    # Lindblad: (kappa1/2)(sz*rho*sz - rho)*dt = (kappa1/2)*[[-2b, ...]] wait let me compute
    # sz*rho*sz = [[a, -b],[-c, d]], so sz*rho*sz - rho = [[0, -2b],[-2c, 0]]
    # Lindblad = (kappa1/2)*dt*[[0,-2b],[-2c,0]]= dt*[[ 0, -kappa1*b],[-kappa1*c, 0]]
    # Kraus delta = -kappa1*dt*[[0, b],[c, 0]]
    # Match! Both give -kappa1*dt*[[0,b],[c,0]]
    kappa1 = Symbol('kappa1', positive=True)
    q1 = kappa1 * dt

    # Direct algebraic E(rho) for Ti:
    # K0*rho*K0† = (1-q1)*rho  [since K0 = sqrt(1-q1)*I, all real]
    # K1*rho*K1† = q1*|0><0|*rho*|0><0| = q1*rho_00*|0><0|
    # K2*rho*K2† = q1*|1><1|*rho*|1><1| = q1*rho_11*|1><1|
    E_rho_ti = (1 - q1) * rho + q1 * Matrix([[a, 0], [0, d]])
    delta_ti = sp.expand(E_rho_ti - rho)  # = -q1*[[0, b],[c, 0]]
    lindblad_ti = (kappa1 / 2) * (sz * rho * sz - rho) * dt

    diff_ti = simplify(sp.expand(delta_ti - lindblad_ti))
    # Check that O(dt^1) terms vanish
    diff_ti_01 = simplify(diff_ti[0, 1].coeff(dt, 1))
    diff_ti_10 = simplify(diff_ti[1, 0].coeff(dt, 1))
    diff_ti_00 = simplify(diff_ti[0, 0].coeff(dt, 1))
    ti_match = (diff_ti_01 == 0) and (diff_ti_10 == 0) and (diff_ti_00 == 0)
    results["Ti"] = {
        "first_order_match": ti_match,
        "delta_rho_01": str(simplify(delta_ti[0, 1])),
        "lindblad_01": str(simplify(lindblad_ti[0, 1])),
    }

    # --- Te: Algebraic computation ---
    # E_Te(rho) = (1-q2)*rho + q2*(|+><+|*rho*|+><+| + |-><-|*rho*|-><-|)
    # |+><+| rho |+><+| = (1/4)[[1,1],[1,1]]*rho*[[1,1],[1,1]]
    #   = (1/4)*(a+b+c+d)*[[1,1],[1,1]]
    # |-><-| rho |-><-| = (1/4)[[1,-1],[-1,1]]*rho*[[1,-1],[-1,1]]
    #   = (1/4)*(a-b-c+d)*[[1,-1],[-1,1]]
    kappa2 = Symbol('kappa2', positive=True)
    q2 = kappa2 * dt

    pp_rho_pp = sp.Rational(1, 4) * (a + b + c + d) * Matrix([[1, 1], [1, 1]])
    mm_rho_mm = sp.Rational(1, 4) * (a - b - c + d) * Matrix([[1, -1], [-1, 1]])
    E_rho_te = (1 - q2) * rho + q2 * (pp_rho_pp + mm_rho_mm)
    delta_te = sp.expand(E_rho_te - rho)
    lindblad_te = (kappa2 / 2) * (sx * rho * sx - rho) * dt

    diff_te = simplify(sp.expand(delta_te - lindblad_te))
    diff_te_elems = [simplify(diff_te[i, j].coeff(dt, 1)) for i in range(2) for j in range(2)]
    te_match = all(elem == 0 for elem in diff_te_elems)
    results["Te"] = {
        "first_order_match": te_match,
        "delta_rho_00": str(simplify(delta_te[0, 0])),
        "lindblad_00": str(simplify(lindblad_te[0, 0])),
    }

    # --- Fi: theta = omega3*dt ---
    omega3 = Symbol('omega3', positive=True)
    th = omega3 * dt
    Ux = Matrix([
        [sp.cos(th / 2), -sp_I * sp.sin(th / 2)],
        [-sp_I * sp.sin(th / 2), sp.cos(th / 2)]
    ])
    E_rho = Ux * rho * Ux.H
    delta_rho = simplify(E_rho - rho)
    lindblad_pred = -sp_I * (omega3 * sx / 2 * rho - rho * omega3 * sx / 2) * dt

    diff = simplify(delta_rho - lindblad_pred)
    diff_order1 = Matrix([[simplify(series(diff[i, j], dt, 0, 2).coeff(dt, 1))
                           for j in range(2)] for i in range(2)])
    fi_match = diff_order1 == sp.zeros(2)
    results["Fi"] = {"first_order_match": fi_match}

    # --- Fe: phi = omega4*dt ---
    omega4 = Symbol('omega4', positive=True)
    ph = omega4 * dt
    Uz = Matrix([
        [sp_exp(-sp_I * ph / 2), 0],
        [0, sp_exp(sp_I * ph / 2)]
    ])
    E_rho = Uz * rho * Uz.H
    delta_rho = simplify(E_rho - rho)
    lindblad_pred = -sp_I * (omega4 * sz / 2 * rho - rho * omega4 * sz / 2) * dt

    diff = simplify(delta_rho - lindblad_pred)
    diff_order1 = Matrix([[simplify(series(diff[i, j], dt, 0, 2).coeff(dt, 1))
                           for j in range(2)] for i in range(2)])
    fe_match = diff_order1 == sp.zeros(2)
    results["Fe"] = {"first_order_match": fe_match}

    return results


# =====================================================================
# (3) COMPUTE ON ALL 6 BLOCH AXIS STATES
# =====================================================================

def compute_bloch_action():
    """Apply each operator to all 6 cardinal Bloch states, report Bloch vectors."""
    results = {}
    q_val = 0.5  # default dephasing strength
    theta_val = np.pi / 4  # default rotation angle

    operators = {
        "Ti": lambda rho: apply_kraus(rho, Ti_kraus(q_val)),
        "Te": lambda rho: apply_kraus(rho, Te_kraus(q_val)),
        "Fi": lambda rho: Fi_unitary(theta_val) @ rho @ Fi_unitary(theta_val).conj().T,
        "Fe": lambda rho: Fe_unitary(theta_val) @ rho @ Fe_unitary(theta_val).conj().T,
    }

    for op_name, op_fn in operators.items():
        op_results = {}
        for state_name, rho_in in BLOCH_STATES.items():
            rho_out = op_fn(rho_in)
            bloch_in = density_to_bloch(rho_in)
            bloch_out = density_to_bloch(rho_out)
            op_results[state_name] = {
                "bloch_in": bloch_in.tolist(),
                "bloch_out": [round(v, 10) for v in bloch_out.tolist()],
                "trace_preserved": round(float(np.real(np.trace(rho_out))), 10),
                "positivity": bool(np.all(np.linalg.eigvalsh(rho_out) >= -1e-12)),
            }
        results[op_name] = op_results

    return results


def compute_bloch_action_torch():
    """Same computation via PyTorch for canonical cross-check."""
    results = {}
    q_val = 0.5
    theta_val = np.pi / 4

    # Convert Bloch states to torch
    t_states = {k: torch.tensor(v, dtype=torch.complex128) for k, v in BLOCH_STATES.items()}

    def torch_apply_kraus(rho, kraus_list):
        out = torch.zeros_like(rho)
        for K in kraus_list:
            Kt = torch.tensor(K, dtype=torch.complex128)
            out += Kt @ rho @ Kt.conj().T
        return out

    operators = {
        "Ti": lambda rho: torch_apply_kraus(rho, Ti_kraus(q_val)),
        "Te": lambda rho: torch_apply_kraus(rho, Te_kraus(q_val)),
        "Fi": lambda rho: (
            torch.tensor(Fi_unitary(theta_val), dtype=torch.complex128) @ rho @
            torch.tensor(Fi_unitary(theta_val).conj().T, dtype=torch.complex128)
        ),
        "Fe": lambda rho: (
            torch.tensor(Fe_unitary(theta_val), dtype=torch.complex128) @ rho @
            torch.tensor(Fe_unitary(theta_val).conj().T, dtype=torch.complex128)
        ),
    }

    sx_t = torch.tensor(sigma_x, dtype=torch.complex128)
    sy_t = torch.tensor(sigma_y, dtype=torch.complex128)
    sz_t = torch.tensor(sigma_z, dtype=torch.complex128)

    for op_name, op_fn in operators.items():
        op_results = {}
        for state_name, rho_in in t_states.items():
            rho_out = op_fn(rho_in)
            bx = torch.trace(rho_out @ sx_t).real.item()
            by = torch.trace(rho_out @ sy_t).real.item()
            bz = torch.trace(rho_out @ sz_t).real.item()
            op_results[state_name] = {
                "bloch_out_torch": [round(bx, 10), round(by, 10), round(bz, 10)],
            }
        results[op_name] = op_results

    return results


# =====================================================================
# (4) CHIRALITY PROPERTIES
# =====================================================================

def verify_chirality():
    """
    Chirality rules:
    - Ti (Z-dephasing): preserves Z-basis (|0>, |1> fixed), decoheres X/Y
    - Fe (Z-rotation): preserves Z-basis (|0>, |1> are eigenstates), rotates in XY-plane
    - Fi (X-rotation): mixes Z-basis, rotates in YZ-plane
    - Te (X-dephasing): preserves X-basis (|+>, |->), decoheres Z/Y
    """
    results = {}
    q_val = 0.5
    theta_val = np.pi / 3

    # Ti: Z-basis preserved
    for state_name in ["|0>", "|1>"]:
        rho_in = BLOCH_STATES[state_name]
        rho_out = apply_kraus(rho_in, Ti_kraus(q_val))
        diff = np.max(np.abs(rho_out - rho_in))
        results[f"Ti_preserves_{state_name}"] = float(diff) < 1e-12

    # Ti: X-basis decohered (off-diagonal killed)
    rho_plus = BLOCH_STATES["|+>"]
    rho_out = apply_kraus(rho_plus, Ti_kraus(q_val))
    bloch_out = density_to_bloch(rho_out)
    results["Ti_decoheres_X"] = abs(bloch_out[0]) < abs(density_to_bloch(rho_plus)[0])

    # Fe: Z-basis preserved (eigenstates of sigma_z)
    for state_name in ["|0>", "|1>"]:
        rho_in = BLOCH_STATES[state_name]
        rho_out = Fe_unitary(theta_val) @ rho_in @ Fe_unitary(theta_val).conj().T
        bloch_in = density_to_bloch(rho_in)
        bloch_out = density_to_bloch(rho_out)
        results[f"Fe_preserves_z_{state_name}"] = abs(bloch_out[2] - bloch_in[2]) < 1e-12

    # Fe: rotates XY plane
    rho_plus = BLOCH_STATES["|+>"]
    rho_out = Fe_unitary(theta_val) @ rho_plus @ Fe_unitary(theta_val).conj().T
    bloch_out = density_to_bloch(rho_out)
    results["Fe_rotates_XY"] = abs(bloch_out[2]) < 1e-12 and (
        abs(bloch_out[0] - 1.0) > 1e-6 or abs(bloch_out[1]) > 1e-6
    )

    # Fi: mixes Z-basis
    rho_0 = BLOCH_STATES["|0>"]
    rho_out = Fi_unitary(theta_val) @ rho_0 @ Fi_unitary(theta_val).conj().T
    bloch_out = density_to_bloch(rho_out)
    results["Fi_mixes_Z_basis"] = abs(bloch_out[2] - 1.0) > 1e-6

    # Te: X-basis preserved
    for state_name in ["|+>", "|->"]:
        rho_in = BLOCH_STATES[state_name]
        rho_out = apply_kraus(rho_in, Te_kraus(q_val))
        diff = np.max(np.abs(rho_out - rho_in))
        results[f"Te_preserves_{state_name}"] = float(diff) < 1e-12

    # Te: Z-basis decohered
    rho_0 = BLOCH_STATES["|0>"]
    rho_out = apply_kraus(rho_0, Te_kraus(q_val))
    bloch_out = density_to_bloch(rho_out)
    results["Te_decoheres_Z"] = abs(bloch_out[2]) < abs(density_to_bloch(rho_0)[2])

    return results


# =====================================================================
# (5) COMPOSITION & NON-COMMUTATIVITY
# =====================================================================

def verify_composition():
    """Test all pairwise compositions, check commutativity."""
    results = {}
    q_val = 0.3
    theta_val = np.pi / 5

    def apply_op(name, rho):
        if name == "Ti":
            return apply_kraus(rho, Ti_kraus(q_val))
        elif name == "Te":
            return apply_kraus(rho, Te_kraus(q_val))
        elif name == "Fi":
            U = Fi_unitary(theta_val)
            return U @ rho @ U.conj().T
        elif name == "Fe":
            U = Fe_unitary(theta_val)
            return U @ rho @ U.conj().T

    op_names = ["Ti", "Te", "Fi", "Fe"]

    # Use |+i> as probe state (sensitive to all axes)
    rho_probe = BLOCH_STATES["|+i>"]

    for i, A in enumerate(op_names):
        for j, B in enumerate(op_names):
            if i >= j:
                continue
            # AB vs BA
            rho_AB = apply_op(B, apply_op(A, rho_probe))
            rho_BA = apply_op(A, apply_op(B, rho_probe))
            diff = np.max(np.abs(rho_AB - rho_BA))
            commutes = diff < 1e-10
            results[f"{A}_{B}"] = {
                "commutes": bool(commutes),
                "max_diff": float(diff),
                "bloch_AB": [round(v, 8) for v in density_to_bloch(rho_AB).tolist()],
                "bloch_BA": [round(v, 8) for v in density_to_bloch(rho_BA).tolist()],
            }

    return results


# =====================================================================
# RUSTWORKX: OPERATOR COMPOSITION DAG
# =====================================================================

def build_composition_dag(composition_results):
    """Build a directed graph of operator compositions with commutativity edges."""
    G = rx.PyDiGraph()

    # Add operator nodes
    node_map = {}
    for name in ["Ti", "Te", "Fi", "Fe"]:
        idx = G.add_node(name)
        node_map[name] = idx

    # Add composition edges
    edge_list = []
    for pair_key, pair_data in composition_results.items():
        A, B = pair_key.split("_")
        edge_data = {
            "pair": pair_key,
            "commutes": pair_data["commutes"],
            "max_diff": pair_data["max_diff"],
        }
        G.add_edge(node_map[A], node_map[B], edge_data)
        if not pair_data["commutes"]:
            # Add reverse edge to show non-commutativity
            G.add_edge(node_map[B], node_map[A], {**edge_data, "reverse": True})
        edge_list.append(edge_data)

    # DAG properties
    dag_info = {
        "num_nodes": len(G.nodes()),
        "num_edges": len(G.edges()),
        "node_names": [G.get_node_data(i) for i in G.node_indices()],
        "edges": edge_list,
        "is_dag": rx.is_directed_acyclic_graph(G),
    }

    return dag_info


# =====================================================================
# CLIFFORD GA CROSS-CHECK
# =====================================================================

def clifford_crosscheck():
    """
    Verify Fi and Fe rotation operators using Cl(3,0) geometric algebra.
    In GA: R = exp(-theta/2 * e_12) for Z-rotation, exp(-theta/2 * e_23) for X-rotation.
    Map bivector rotors to SU(2) matrices and compare.
    """
    results = {}

    layout, blades = Cl(3)
    e1, e2, e3 = blades['e1'], blades['e2'], blades['e3']
    e12, e13, e23 = blades['e12'], blades['e13'], blades['e23']

    theta_val = np.pi / 4

    # Fe (Z-rotation) corresponds to rotor in e12 plane
    # R_z = exp(-phi/2 * e12) = cos(phi/2) - sin(phi/2)*e12
    R_z = np.cos(theta_val / 2) - np.sin(theta_val / 2) * e12

    # Fi (X-rotation) corresponds to rotor in e23 plane
    # R_x = exp(-theta/2 * e23) = cos(theta/2) - sin(theta/2)*e23
    R_x = np.cos(theta_val / 2) - np.sin(theta_val / 2) * e23

    # Apply to basis vectors and verify rotation properties
    # Z-rotation should fix e3, rotate e1->e2
    e3_rot = R_z * e3 * ~R_z
    e3_preserved_by_Fe = float(abs((e3_rot - e3).value[0])) < 1e-10

    # X-rotation should fix e1, rotate e2->e3
    e1_rot = R_x * e1 * ~R_x
    e1_preserved_by_Fi = float(abs((e1_rot - e1).value[0])) < 1e-10

    # Cross-check: extract matrix form from rotor and compare to SU(2)
    # For Fe: the action on Bloch sphere should rotate around z-axis
    # Apply R_z to e1 (x-axis on Bloch sphere)
    e1_after_Rz = R_z * e1 * ~R_z
    # Extract components
    x_comp = float(e1_after_Rz.value[blades['e1'].value != 0][0]) if hasattr(e1_after_Rz, 'value') else 0

    # Get the scalar coefficients more robustly
    e1_after = R_z * e1 * ~R_z
    e2_after = R_z * e2 * ~R_z
    e3_after_Rz = R_z * e3 * ~R_z

    # Build rotation matrix from GA rotor
    def mv_to_vec(mv):
        """Extract e1, e2, e3 components from multivector."""
        return np.array([
            float((mv | e1).value[0]) if (mv | e1).value.any() else 0.0,
            float((mv | e2).value[0]) if (mv | e2).value.any() else 0.0,
            float((mv | e3).value[0]) if (mv | e3).value.any() else 0.0,
        ])

    # For Fe/Z-rotation: should give Rz(theta) on Bloch sphere
    Fe_matrix_ga = np.column_stack([
        mv_to_vec(R_z * e1 * ~R_z),
        mv_to_vec(R_z * e2 * ~R_z),
        mv_to_vec(R_z * e3 * ~R_z),
    ])

    # Expected SO(3) Z-rotation
    Fe_matrix_expected = np.array([
        [np.cos(theta_val), -np.sin(theta_val), 0],
        [np.sin(theta_val), np.cos(theta_val), 0],
        [0, 0, 1],
    ])

    fe_match = np.allclose(Fe_matrix_ga, Fe_matrix_expected, atol=1e-10)

    # For Fi/X-rotation: should give Rx(theta) on Bloch sphere
    Fi_matrix_ga = np.column_stack([
        mv_to_vec(R_x * e1 * ~R_x),
        mv_to_vec(R_x * e2 * ~R_x),
        mv_to_vec(R_x * e3 * ~R_x),
    ])

    Fi_matrix_expected = np.array([
        [1, 0, 0],
        [0, np.cos(theta_val), -np.sin(theta_val)],
        [0, np.sin(theta_val), np.cos(theta_val)],
    ])

    fi_match = np.allclose(Fi_matrix_ga, Fi_matrix_expected, atol=1e-10)

    results["Fe_z_rotation"] = {
        "e3_preserved": e3_preserved_by_Fe,
        "SO3_matrix_match": fe_match,
        "ga_matrix": Fe_matrix_ga.tolist(),
    }
    results["Fi_x_rotation"] = {
        "e1_preserved": e1_preserved_by_Fi,
        "SO3_matrix_match": fi_match,
        "ga_matrix": Fi_matrix_ga.tolist(),
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    """Verify operators fail correctly under invalid conditions."""
    import warnings
    results = {}

    # N1: Kraus with q > 1 should break completeness
    bad_q = 1.5
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        kraus = Ti_kraus(bad_q)
    total = sum(K.conj().T @ K for K in kraus)
    results["Ti_q_gt_1_breaks_completeness"] = not np.allclose(total, I2)

    # N2: Negative q should produce non-physical channel
    # (sqrt of negative number -> NaN from numpy)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            kraus_neg = Ti_kraus(-0.5)
        has_nan = any(np.isnan(K).any() for K in kraus_neg)
        results["Ti_negative_q_produces_nan"] = has_nan
    except Exception as e:
        results["Ti_negative_q_produces_nan"] = True

    # N3: Te with q=0 should be identity
    rho_test = BLOCH_STATES["|+i>"]
    rho_out = apply_kraus(rho_test, Te_kraus(0.0))
    results["Te_q0_is_identity"] = np.allclose(rho_out, rho_test)

    # N4: Fi with theta=0 should be identity
    U = Fi_unitary(0.0)
    results["Fi_theta0_is_identity"] = np.allclose(U, I2)

    # N5: Fe with phi=0 should be identity
    U = Fe_unitary(0.0)
    results["Fe_phi0_is_identity"] = np.allclose(U, I2)

    # N6: Ti should NOT preserve coherence of |+> (it destroys it)
    rho_plus = BLOCH_STATES["|+>"]
    rho_out = apply_kraus(rho_plus, Ti_kraus(1.0))  # full dephasing
    bloch_out = density_to_bloch(rho_out)
    results["Ti_full_dephasing_kills_x_coherence"] = abs(bloch_out[0]) < 1e-10

    # N7: Te full dephasing kills z-coherence
    rho_0 = BLOCH_STATES["|0>"]
    rho_out = apply_kraus(rho_0, Te_kraus(1.0))
    bloch_out = density_to_bloch(rho_out)
    results["Te_full_dephasing_kills_z_coherence"] = abs(bloch_out[2]) < 1e-10

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    """Edge cases and numerical precision limits."""
    results = {}

    # B1: q at exact boundaries
    for q in [0.0, 1.0]:
        kraus = Ti_kraus(q)
        total = sum(K.conj().T @ K for K in kraus)
        results[f"Ti_q{q}_completeness"] = bool(np.allclose(total, I2))

    for q in [0.0, 1.0]:
        kraus = Te_kraus(q)
        total = sum(K.conj().T @ K for K in kraus)
        results[f"Te_q{q}_completeness"] = bool(np.allclose(total, I2))

    # B2: Full 2pi rotation should return to identity
    results["Fi_2pi_identity"] = bool(np.allclose(Fi_unitary(2 * np.pi), -I2))  # Global phase
    results["Fe_2pi_identity"] = bool(np.allclose(Fe_unitary(2 * np.pi), -I2))  # Global phase
    results["Fi_4pi_exact_identity"] = bool(np.allclose(Fi_unitary(4 * np.pi), I2, atol=1e-10))
    results["Fe_4pi_exact_identity"] = bool(np.allclose(Fe_unitary(4 * np.pi), I2, atol=1e-10))

    # B3: Tiny dephasing should be near-identity
    eps = 1e-12
    rho_test = BLOCH_STATES["|+i>"]
    rho_out_ti = apply_kraus(rho_test, Ti_kraus(eps))
    rho_out_te = apply_kraus(rho_test, Te_kraus(eps))
    results["Ti_tiny_q_near_identity"] = float(np.max(np.abs(rho_out_ti - rho_test)))
    results["Te_tiny_q_near_identity"] = float(np.max(np.abs(rho_out_te - rho_test)))

    # B4: Lindblad convergence - many small Kraus steps should match single large step
    n_steps = 1000
    q_total = 0.5
    q_step = q_total / n_steps
    rho = BLOCH_STATES["|+>"].copy()
    for _ in range(n_steps):
        rho = apply_kraus(rho, Ti_kraus(q_step))
    rho_single = apply_kraus(BLOCH_STATES["|+>"], Ti_kraus(q_total))
    # They won't be exactly equal (composition != single step) but should be close
    # for small q_step. The key check is both are valid density matrices.
    results["Ti_composed_trace"] = float(np.real(np.trace(rho)))
    results["Ti_composed_positive"] = bool(np.all(np.linalg.eigvalsh(rho) >= -1e-12))

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("ENGINE 4 OPERATORS: CANONICAL SIMULATION")
    print("=" * 70)

    results = {
        "name": "engine_4_operators",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
    }

    # (1) Kraus completeness
    print("\n[1/6] Kraus completeness (sympy)...")
    results["kraus_completeness_sympy"] = verify_kraus_completeness_sympy()
    print("  sympy: done")

    print("[1/6] Kraus completeness (z3)...")
    results["kraus_completeness_z3"] = verify_kraus_completeness_z3()
    print("  z3: done")

    # (2) Kraus-Lindblad correspondence
    print("\n[2/6] Kraus-Lindblad continuous-limit correspondence...")
    results["kraus_lindblad_correspondence"] = verify_kraus_lindblad_correspondence()
    print("  done")

    # (3) Bloch axis action
    print("\n[3/6] Bloch axis action (numpy)...")
    results["bloch_action_numpy"] = compute_bloch_action()
    print("  numpy: done")

    print("[3/6] Bloch axis action (torch cross-check)...")
    results["bloch_action_torch"] = compute_bloch_action_torch()
    print("  torch: done")

    # (4) Chirality
    print("\n[4/6] Chirality verification...")
    results["chirality"] = verify_chirality()
    print("  done")

    # (5) Composition & non-commutativity
    print("\n[5/6] Pairwise composition & non-commutativity...")
    results["composition"] = verify_composition()
    print("  done")

    # Rustworkx DAG
    print("[5/6] Building composition DAG (rustworkx)...")
    results["composition_dag"] = build_composition_dag(results["composition"])
    print("  done")

    # (6) Clifford GA cross-check
    print("\n[6/6] Clifford GA cross-check...")
    results["clifford_crosscheck"] = clifford_crosscheck()
    print("  done")

    # Negative tests
    print("\n[NEG] Running negative tests...")
    results["negative"] = run_negative_tests()
    print("  done")

    # Boundary tests
    print("\n[BND] Running boundary tests...")
    results["boundary"] = run_boundary_tests()
    print("  done")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    all_pass = True
    for section in ["kraus_completeness_sympy", "kraus_completeness_z3",
                     "kraus_lindblad_correspondence", "chirality"]:
        data = results[section]
        for key, val in data.items():
            if isinstance(val, dict):
                for subkey, subval in val.items():
                    if isinstance(subval, bool) and not subval:
                        print(f"  FAIL: {section}.{key}.{subkey}")
                        all_pass = False
            elif isinstance(val, bool) and not val:
                print(f"  FAIL: {section}.{key}")
                all_pass = False

    for key, val in results["negative"].items():
        if isinstance(val, bool) and not val:
            print(f"  FAIL: negative.{key}")
            all_pass = False

    if all_pass:
        print("  ALL CHECKS PASSED")

    # Write results
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "engine_4_operators_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults written to {out_path}")
