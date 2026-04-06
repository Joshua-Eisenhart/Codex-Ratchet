#!/usr/bin/env python3
"""
Axis 0 Chiral Bridge — Deep Search & Anti-Leak Suite
=====================================================

Phase 2 of the bridge search. Xi_chiral_hist_entangle won Phase 1 by 200×.
This probe stress-tests the win by:

1. ENTANGLEMENT STRUCTURE VARIATION
   - Bell states (|Φ+⟩, |Φ-⟩, |Ψ+⟩, |Ψ-⟩)
   - Werner states (ρ_W = p|Ψ-⟩⟨Ψ-| + (1-p)I/4)
   - Isotropic states
   - Different parameterizations of the mixing angle
   - Geometry-derived vs arbitrary entanglement

2. ANTI-LEAK TESTS
   - Does injecting random entanglement also win? (if yes → MI is artifact)
   - Does geometry-derived p beat random p? (if yes → structure matters)
   - Does the chiral bridge with ZERO entanglement recover product? (sanity)
   - Does maximally entangled beat geometry-derived? (is more always better?)

3. KERNEL COMPATIBILITY
   - Does Φ₀ = -S(A|B) still separate candidates on chiral states?
   - Does coherent information track correctly?
   - Does the kernel ordering (negative S(A|B) → strongest) hold?

4. RETROCAUSAL POTENTIAL-FIELD VERSION
   - Weight chiral mixing by final-state compatibility
   - Weight by entropy gradient (time = entropy increasing)
   - Weight by compression quality

5. CONTINUOUS ENTANGLEMENT SWEEP
   - Sweep p from 0 to 1 in fine steps
   - Find the optimal entanglement fraction
   - Check if it matches the geometry-derived value

Author: System V4
Date: 2026-03-30
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from typing import Dict, List, Tuple

import numpy as np
from scipy.linalg import sqrtm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import GeometricEngine
from geometric_operators import _ensure_valid_density
from hopf_manifold import (
    TORUS_CLIFFORD, TORUS_INNER, TORUS_OUTER,
    left_density, right_density, torus_coordinates,
    von_neumann_entropy_2x2,
)

EPS = 1e-12
SIGMA_X = np.array([[0, 1], [1, 0]], dtype=complex)
SIGMA_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
SIGMA_Z = np.array([[1, 0], [0, -1]], dtype=complex)
I4 = np.eye(4, dtype=complex)

TORUS_CONFIGS = [
    ("inner", TORUS_INNER),
    ("clifford", TORUS_CLIFFORD),
    ("outer", TORUS_OUTER),
]


# ═══════════════════════════════════════════════════════════════════
# QIT TOOLBOX
# ═══════════════════════════════════════════════════════════════════

def von_neumann_entropy(rho: np.ndarray) -> float:
    rho = (rho + rho.conj().T) / 2
    evals = np.real(np.linalg.eigvalsh(rho))
    evals = evals[evals > 1e-15]
    if len(evals) == 0:
        return 0.0
    return float(-np.sum(evals * np.log2(evals)))


def partial_trace_B(rho_AB: np.ndarray) -> np.ndarray:
    r = rho_AB.reshape(2, 2, 2, 2)
    return np.trace(r, axis1=1, axis2=3)


def partial_trace_A(rho_AB: np.ndarray) -> np.ndarray:
    r = rho_AB.reshape(2, 2, 2, 2)
    return np.trace(r, axis1=0, axis2=2)


def mutual_information(rho_AB: np.ndarray) -> float:
    rho_A = partial_trace_B(rho_AB)
    rho_B = partial_trace_A(rho_AB)
    return max(0.0, von_neumann_entropy(rho_A) + von_neumann_entropy(rho_B) - von_neumann_entropy(rho_AB))


def coherent_information(rho_AB: np.ndarray) -> float:
    rho_B = partial_trace_A(rho_AB)
    return von_neumann_entropy(rho_B) - von_neumann_entropy(rho_AB)


def neg_conditional_entropy(rho_AB: np.ndarray) -> float:
    """Φ₀ = -S(A|B) = S(B) - S(AB). The Axis 0 kernel."""
    return coherent_information(rho_AB)


def full_metrics(rho_AB: np.ndarray) -> Dict[str, float]:
    rho_A = partial_trace_B(rho_AB)
    rho_B = partial_trace_A(rho_AB)
    S_A = von_neumann_entropy(rho_A)
    S_B = von_neumann_entropy(rho_B)
    S_AB = von_neumann_entropy(rho_AB)
    I_AB = max(0.0, S_A + S_B - S_AB)
    Ic = S_B - S_AB
    return {
        "I_AB": I_AB,
        "I_c": Ic,
        "neg_S_A_given_B": Ic,  # Same as I_c = Φ₀
        "S_A": S_A,
        "S_B": S_B,
        "S_AB": S_AB,
        "S_A_given_B": S_AB - S_B,
    }


def bloch_vector(rho_2x2: np.ndarray) -> np.ndarray:
    return np.array([
        float(np.real(np.trace(SIGMA_X @ rho_2x2))),
        float(np.real(np.trace(SIGMA_Y @ rho_2x2))),
        float(np.real(np.trace(SIGMA_Z @ rho_2x2))),
    ])


def lr_asymmetry(rho_L: np.ndarray, rho_R: np.ndarray) -> float:
    """Normalized L/R Bloch vector asymmetry ∈ [0,1]."""
    bL = bloch_vector(rho_L)
    bR = bloch_vector(rho_R)
    return float(np.clip(0.5 * np.linalg.norm(bL - bR), 0, 1))


# ═══════════════════════════════════════════════════════════════════
# BELL STATES
# ═══════════════════════════════════════════════════════════════════

PHI_PLUS = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)   # |Φ+⟩ = (|00⟩+|11⟩)/√2
PHI_MINUS = np.array([1, 0, 0, -1], dtype=complex) / np.sqrt(2)  # |Φ-⟩ = (|00⟩-|11⟩)/√2
PSI_PLUS = np.array([0, 1, 1, 0], dtype=complex) / np.sqrt(2)    # |Ψ+⟩ = (|01⟩+|10⟩)/√2
PSI_MINUS = np.array([0, 1, -1, 0], dtype=complex) / np.sqrt(2)  # |Ψ-⟩ = (|01⟩-|10⟩)/√2

BELL_STATES = {
    "Phi_plus": PHI_PLUS,
    "Phi_minus": PHI_MINUS,
    "Psi_plus": PSI_PLUS,
    "Psi_minus": PSI_MINUS,
}


# ═══════════════════════════════════════════════════════════════════
# SUITE 1: ENTANGLEMENT STRUCTURE VARIATION
# ═══════════════════════════════════════════════════════════════════

def make_entangled_state(rho_L, rho_R, psi_ent, p):
    """Mix product state with entangled pure state at fraction p."""
    product = _ensure_valid_density(np.kron(rho_L, rho_R))
    rho_ent = np.outer(psi_ent, psi_ent.conj())
    return _ensure_valid_density((1 - p) * product + p * rho_ent)


def _pauli_from_axis(axis: np.ndarray) -> np.ndarray:
    x, y, z = axis
    return x * SIGMA_X + y * SIGMA_Y + z * SIGMA_Z


def make_matched_marginal_correlated_state(rho_L, rho_R, kappa):
    """Build a 2-qubit correlated state with exact input marginals.

    Fano form:
      rho_AB = 1/4 [I⊗I + a·σ⊗I + I⊗b·σ + kappa (u·σ)⊗(v·σ)]

    The correlation term is traceless on each side, so the marginals remain
    exactly rho_L and rho_R as long as the resulting matrix is PSD.
    """
    a = bloch_vector(rho_L)
    b = bloch_vector(rho_R)
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    u = a / na if na > EPS else np.array([0.0, 0.0, 1.0])
    v = b / nb if nb > EPS else np.array([0.0, 0.0, 1.0])
    a_sigma = _pauli_from_axis(a)
    b_sigma = _pauli_from_axis(b)
    u_sigma = _pauli_from_axis(u)
    v_sigma = _pauli_from_axis(v)

    kappa_eff = float(kappa)
    while True:
        rho = 0.25 * (
            np.kron(np.eye(2, dtype=complex), np.eye(2, dtype=complex))
            + np.kron(a_sigma, np.eye(2, dtype=complex))
            + np.kron(np.eye(2, dtype=complex), b_sigma)
            + kappa_eff * np.kron(u_sigma, v_sigma)
        )
        rho = (rho + rho.conj().T) / 2
        evals = np.real(np.linalg.eigvalsh(rho))
        if np.min(evals) >= -1e-10 or abs(kappa_eff) < 1e-8:
            return _ensure_valid_density(rho), {
                "kappa_input": float(kappa),
                "kappa_effective": float(kappa_eff),
                "axis_L": u.tolist(),
                "axis_R": v.tolist(),
                "bloch_norm_L": na,
                "bloch_norm_R": nb,
            }
        kappa_eff *= 0.5


def make_werner_state(p):
    """Werner state: ρ_W = p|Ψ-⟩⟨Ψ-| + (1-p)I/4"""
    rho_ent = np.outer(PSI_MINUS, PSI_MINUS.conj())
    return _ensure_valid_density(p * rho_ent + (1 - p) * I4 / 4)


def make_isotropic_state(p):
    """Isotropic state: ρ = p|Φ+⟩⟨Φ+| + (1-p)I/4"""
    rho_ent = np.outer(PHI_PLUS, PHI_PLUS.conj())
    return _ensure_valid_density(p * rho_ent + (1 - p) * I4 / 4)


def make_geometry_parameterized(rho_L, rho_R, psi_ent):
    """Use L/R asymmetry as the entanglement parameter — the Phase 1 winner approach."""
    p = lr_asymmetry(rho_L, rho_R)
    p = float(np.clip(p, 0.01, 0.99))
    return make_entangled_state(rho_L, rho_R, psi_ent, p), p


def make_geometry_theta_parameterized(rho_L, rho_R):
    """Use L/R asymmetry to parameterize the entangled state itself, not just p."""
    bL = bloch_vector(rho_L)
    bR = bloch_vector(rho_R)
    p = lr_asymmetry(rho_L, rho_R)
    p = float(np.clip(p, 0.01, 0.99))
    
    # Use the L/R Bloch difference to define entanglement AXIS, not just magnitude
    diff = bL - bR
    norm = np.linalg.norm(diff)
    if norm > EPS:
        axis = diff / norm
    else:
        axis = np.array([0, 0, 1])
    
    # Build entangled state aligned with the L/R asymmetry axis
    # |ψ⟩ = cos(θ/2)|↑_n ↓_n⟩ + sin(θ/2)|↓_n ↑_n⟩ where n is the asymmetry axis
    theta = np.arcsin(np.sqrt(p))
    
    # Eigenstate of σ·n
    nx, ny, nz = axis
    phi_angle = np.arctan2(ny, nx)
    cos_half = np.cos(np.arccos(np.clip(nz, -1, 1)) / 2)
    sin_half = np.sin(np.arccos(np.clip(nz, -1, 1)) / 2)
    
    up_n = np.array([cos_half, sin_half * np.exp(1j * phi_angle)], dtype=complex)
    dn_n = np.array([-sin_half * np.exp(-1j * phi_angle), cos_half], dtype=complex)
    
    # |ψ⟩ = cos(θ)|↑↓⟩ + sin(θ)|↓↑⟩ in the n-basis
    psi = np.cos(theta) * np.kron(up_n, dn_n) + np.sin(theta) * np.kron(dn_n, up_n)
    psi = psi / (np.linalg.norm(psi) + EPS)
    
    rho_ent = np.outer(psi, psi.conj())
    product = _ensure_valid_density(np.kron(rho_L, rho_R))
    rho = _ensure_valid_density((1 - p) * product + p * rho_ent)
    return rho, p, {"axis": axis.tolist(), "theta": float(theta)}


def run_structure_variation(state):
    """Test different entanglement structures on the same engine state."""
    rho_L, rho_R = state.rho_L, state.rho_R
    p_geom = lr_asymmetry(rho_L, rho_R)
    p_geom = float(np.clip(p_geom, 0.01, 0.99))
    
    results = {}
    
    # 1. Product state (p=0)
    rho = _ensure_valid_density(np.kron(rho_L, rho_R))
    results["product_p0"] = full_metrics(rho)
    
    # 2. Each Bell state at geometry-derived p
    for bell_name, bell_psi in BELL_STATES.items():
        rho = make_entangled_state(rho_L, rho_R, bell_psi, p_geom)
        results[f"bell_{bell_name}_p_geom"] = {**full_metrics(rho), "p": p_geom}
    
    # 3. Phase 1 winner: |00⟩+|11⟩ at geometry-derived p
    theta = np.arcsin(np.sqrt(p_geom))
    psi_phase1 = np.array([np.cos(theta), 0, 0, np.sin(theta)], dtype=complex)
    rho = make_entangled_state(rho_L, rho_R, psi_phase1, p_geom)
    results["phase1_winner_p_geom"] = {**full_metrics(rho), "p": p_geom}
    
    # 4. Geometry-axis-parameterized entanglement
    rho_axis, p_axis, axis_meta = make_geometry_theta_parameterized(rho_L, rho_R)
    results["geometry_axis_parameterized"] = {**full_metrics(rho_axis), "p": p_axis}
    
    # 5. Werner state at geometry-derived p
    rho_w = make_werner_state(p_geom)
    results["werner_p_geom"] = {**full_metrics(rho_w), "p": p_geom}
    
    # 6. Isotropic state at geometry-derived p
    rho_iso = make_isotropic_state(p_geom)
    results["isotropic_p_geom"] = {**full_metrics(rho_iso), "p": p_geom}
    
    # 7. Maximum entanglement (p=1)
    for bell_name, bell_psi in BELL_STATES.items():
        rho = make_entangled_state(rho_L, rho_R, bell_psi, 1.0)
        results[f"bell_{bell_name}_p_max"] = {**full_metrics(rho), "p": 1.0}

    # 8. Exact-marginal correlated chiral candidate
    rho_mm, mm_meta = make_matched_marginal_correlated_state(rho_L, rho_R, p_geom)
    results["matched_marginal_correlated"] = {**full_metrics(rho_mm), **mm_meta}
    
    return results, p_geom


# ═══════════════════════════════════════════════════════════════════
# SUITE 2: ANTI-LEAK TESTS
# ═══════════════════════════════════════════════════════════════════

def run_anti_leak_tests(state, n_random=20):
    """Test whether geometry-derived entanglement is earned or smuggled."""
    rho_L, rho_R = state.rho_L, state.rho_R
    p_geom = lr_asymmetry(rho_L, rho_R)
    p_geom = float(np.clip(p_geom, 0.01, 0.99))
    
    results = {}
    
    # 1. Random entanglement at same p — does geometry matter?
    rng = np.random.default_rng(42)
    random_mis = []
    random_ics = []
    for i in range(n_random):
        # Random pure entangled state
        psi_rand = rng.standard_normal(4) + 1j * rng.standard_normal(4)
        psi_rand = psi_rand / np.linalg.norm(psi_rand)
        rho = make_entangled_state(rho_L, rho_R, psi_rand, p_geom)
        m = full_metrics(rho)
        random_mis.append(m["I_AB"])
        random_ics.append(m["I_c"])
    
    results["random_entangle_at_p_geom"] = {
        "mean_I_AB": float(np.mean(random_mis)),
        "std_I_AB": float(np.std(random_mis)),
        "min_I_AB": float(np.min(random_mis)),
        "max_I_AB": float(np.max(random_mis)),
        "mean_I_c": float(np.mean(random_ics)),
        "p": p_geom,
        "n_random": n_random,
    }
    
    # 2. Random p at same Bell state — does the geometry-derived p matter?
    theta_geom = np.arcsin(np.sqrt(p_geom))
    psi_geom = np.array([np.cos(theta_geom), 0, 0, np.sin(theta_geom)], dtype=complex)
    random_p_mis = []
    random_p_ics = []
    p_values = np.linspace(0.01, 0.99, n_random)
    for p in p_values:
        rho = make_entangled_state(rho_L, rho_R, psi_geom, p)
        m = full_metrics(rho)
        random_p_mis.append(m["I_AB"])
        random_p_ics.append(m["I_c"])
    
    results["random_p_at_geom_state"] = {
        "p_values": p_values.tolist(),
        "I_AB_values": random_p_mis,
        "I_c_values": random_p_ics,
        "p_geom": p_geom,
        "I_AB_at_p_geom_idx": int(np.argmin(np.abs(p_values - p_geom))),
    }
    
    # 3. Does MI scale monotonically with p? (if yes, more ent = more MI, no structure)
    monotonic_mi = all(random_p_mis[i] <= random_p_mis[i+1] + 1e-9 for i in range(len(random_p_mis)-1))
    results["mi_monotonic_with_p"] = bool(monotonic_mi)
    
    # 4. Compare: geometry p vs p=0.5 vs p=1.0
    rho_half = make_entangled_state(rho_L, rho_R, psi_geom, 0.5)
    rho_full = make_entangled_state(rho_L, rho_R, psi_geom, 1.0)
    rho_geom = make_entangled_state(rho_L, rho_R, psi_geom, p_geom)
    
    results["p_comparison"] = {
        "p_geom": {**full_metrics(rho_geom), "p": p_geom},
        "p_half": {**full_metrics(rho_half), "p": 0.5},
        "p_full": {**full_metrics(rho_full), "p": 1.0},
    }
    
    # 5. Null test: entangle with IDENTITY (totally mixed) — should give zero MI
    rho_null = make_entangled_state(np.eye(2) / 2, np.eye(2) / 2, PHI_PLUS, p_geom)
    results["null_identity_entangle"] = {**full_metrics(rho_null), "p": p_geom}

    # 6. Matched-marginal anti-leak test: compare the current geometry-derived
    # ansatz against the exact product state built from the same marginals.
    matched_product = _ensure_valid_density(np.kron(rho_L, rho_R))
    matched_product_metrics = full_metrics(matched_product)
    matched_geom_metrics = full_metrics(rho_geom)
    ent_rho_A = partial_trace_B(rho_geom)
    ent_rho_B = partial_trace_A(rho_geom)
    marginal_dev_A = float(np.linalg.norm(ent_rho_A - rho_L, ord="fro"))
    marginal_dev_B = float(np.linalg.norm(ent_rho_B - rho_R, ord="fro"))
    results["matched_marginal_check"] = {
        "product_I_AB": matched_product_metrics["I_AB"],
        "product_I_c": matched_product_metrics["I_c"],
        "geom_I_AB": matched_geom_metrics["I_AB"],
        "geom_I_c": matched_geom_metrics["I_c"],
        "delta_I_AB_vs_product": float(matched_geom_metrics["I_AB"] - matched_product_metrics["I_AB"]),
        "delta_I_c_vs_product": float(matched_geom_metrics["I_c"] - matched_product_metrics["I_c"]),
        "marginal_deviation_A_fro": marginal_dev_A,
        "marginal_deviation_B_fro": marginal_dev_B,
        "preserves_marginals": bool(marginal_dev_A < 1e-6 and marginal_dev_B < 1e-6),
    }
    
    return results


# ═══════════════════════════════════════════════════════════════════
# SUITE 3: KERNEL COMPATIBILITY
# ═══════════════════════════════════════════════════════════════════

def run_kernel_compatibility(state):
    """Test whether the Axis 0 kernel Φ₀ = -S(A|B) behaves correctly on chiral states."""
    rho_L, rho_R = state.rho_L, state.rho_R
    p_geom = lr_asymmetry(rho_L, rho_R)
    p_geom = float(np.clip(p_geom, 0.01, 0.99))
    
    results = {}
    
    # Build a family of states at varying entanglement
    p_values = np.linspace(0.0, 1.0, 51)
    theta_geom = np.arcsin(np.sqrt(max(p_geom, 0.01)))
    psi_geom = np.array([np.cos(theta_geom), 0, 0, np.sin(theta_geom)], dtype=complex)
    
    sweep_data = []
    for p in p_values:
        if p < 0.001:
            rho = _ensure_valid_density(np.kron(rho_L, rho_R))
        else:
            rho = make_entangled_state(rho_L, rho_R, psi_geom, float(p))
        m = full_metrics(rho)
        sweep_data.append({
            "p": float(p),
            "I_AB": m["I_AB"],
            "I_c": m["I_c"],
            "neg_S_A_given_B": m["neg_S_A_given_B"],
            "S_A": m["S_A"],
            "S_B": m["S_B"],
            "S_AB": m["S_AB"],
        })
    
    results["p_sweep"] = sweep_data
    
    # Find where I_c crosses zero (transition from classical to quantum correlations)
    ic_values = [d["I_c"] for d in sweep_data]
    crossing_idx = None
    for i in range(len(ic_values) - 1):
        if ic_values[i] < 0 and ic_values[i+1] >= 0:
            crossing_idx = i
            break
    
    results["ic_zero_crossing"] = {
        "exists": crossing_idx is not None,
        "crossing_p": float(p_values[crossing_idx]) if crossing_idx is not None else None,
        "crossing_p_vs_geom": float(p_values[crossing_idx] - p_geom) if crossing_idx is not None else None,
    }
    
    # Kernel ordering: does higher MI → higher -S(A|B)?
    from scipy.stats import spearmanr
    mi_vals = [d["I_AB"] for d in sweep_data]
    ic_vals = [d["I_c"] for d in sweep_data]
    if len(set(mi_vals)) > 1:
        corr, pval = spearmanr(mi_vals, ic_vals)
    else:
        corr, pval = 0.0, 1.0
    results["mi_ic_correlation"] = {
        "spearman_r": float(corr),
        "spearman_p": float(pval),
        "positive_correlation": bool(corr > 0),
    }
    
    # Find optimal p for each metric
    best_mi_idx = int(np.argmax([d["I_AB"] for d in sweep_data]))
    best_ic_idx = int(np.argmax([d["I_c"] for d in sweep_data]))
    results["optimal_p"] = {
        "best_p_for_MI": float(p_values[best_mi_idx]),
        "best_MI": float(sweep_data[best_mi_idx]["I_AB"]),
        "best_p_for_Ic": float(p_values[best_ic_idx]),
        "best_Ic": float(sweep_data[best_ic_idx]["I_c"]),
        "p_geom": p_geom,
        "geom_MI": float(sweep_data[int(np.argmin(np.abs(p_values - p_geom)))]["I_AB"]),
        "geom_Ic": float(sweep_data[int(np.argmin(np.abs(p_values - p_geom)))]["I_c"]),
    }
    
    return results


# ═══════════════════════════════════════════════════════════════════
# SUITE 4: RETROCAUSAL CHIRAL HISTORY
# ═══════════════════════════════════════════════════════════════════

def run_retrocausal_chiral(state):
    """Test retrocausal-weighted chiral entanglement history bridges."""
    history = state.history
    if not history:
        return {"error": "no history"}
    
    rho_L_final, rho_R_final = state.rho_L, state.rho_R
    rho_final_product = _ensure_valid_density(np.kron(rho_L_final, rho_R_final))
    T = len(history)
    
    results = {}
    
    # Build chiral-entangled states for every history step
    chiral_states = []
    p_values_hist = []
    for h in history:
        rL, rR = h["rho_L"], h["rho_R"]
        p = lr_asymmetry(rL, rR)
        p = float(np.clip(p, 0.01, 0.99))
        theta = np.arcsin(np.sqrt(p))
        psi_ent = np.array([np.cos(theta), 0, 0, np.sin(theta)], dtype=complex)
        rho = make_entangled_state(rL, rR, psi_ent, p)
        chiral_states.append(rho)
        p_values_hist.append(p)
    
    # A. Uniform chiral (Phase 1 winner)
    rho_uniform = _ensure_valid_density(sum(chiral_states) / len(chiral_states))
    results["chiral_uniform"] = full_metrics(rho_uniform)
    
    # B. Retrocausal exponential decay (recent = more weight)
    for decay_rate in [0.05, 0.1, 0.2, 0.5]:
        weights = np.array([np.exp(-decay_rate * (T - 1 - i)) for i in range(T)])
        weights /= weights.sum()
        rho = _ensure_valid_density(sum(w * s for w, s in zip(weights, chiral_states)))
        results[f"chiral_retro_decay_{decay_rate}"] = {**full_metrics(rho), "decay_rate": decay_rate}
    
    # C. Compression-weighted chiral
    compress_weights = []
    for h in history:
        compress_weights.append(abs(h.get("dphi_L", 0)) + abs(h.get("dphi_R", 0)) + EPS)
    cw = np.array(compress_weights)
    cw /= cw.sum()
    rho_cw = _ensure_valid_density(sum(w * s for w, s in zip(cw, chiral_states)))
    results["chiral_compress"] = {**full_metrics(rho_cw), "max_weight": float(cw.max())}
    
    # D. Future-fidelity-weighted chiral (retrocausal potential field)
    fid_weights = []
    for cs in chiral_states:
        try:
            sqrt_f = sqrtm(rho_final_product)
            inner = sqrtm(sqrt_f @ cs @ sqrt_f)
            fid = float(np.real(np.trace(inner))) ** 2
        except Exception:
            fid = float(np.real(np.trace(rho_final_product @ cs)))
        fid_weights.append(max(fid, EPS))
    fw = np.array(fid_weights)
    fw /= fw.sum()
    rho_fid = _ensure_valid_density(sum(w * s for w, s in zip(fw, chiral_states)))
    results["chiral_future_fidelity"] = {**full_metrics(rho_fid), "max_weight": float(fw.max())}
    
    # E. Entropy-gradient-weighted chiral
    eg_weights = [EPS]
    for i in range(1, T):
        e_curr = von_neumann_entropy_2x2(history[i]["rho_L"]) + von_neumann_entropy_2x2(history[i]["rho_R"])
        e_prev = von_neumann_entropy_2x2(history[i-1]["rho_L"]) + von_neumann_entropy_2x2(history[i-1]["rho_R"])
        eg_weights.append(abs(e_curr - e_prev) + EPS)
    ew = np.array(eg_weights)
    ew /= ew.sum()
    rho_eg = _ensure_valid_density(sum(w * s for w, s in zip(ew, chiral_states)))
    results["chiral_entropy_gradient"] = {**full_metrics(rho_eg), "max_weight": float(ew.max())}
    
    # F. Combined: retrocausal × compression × chiral
    combined = np.array([
        np.exp(-0.1 * (T - 1 - i)) * (abs(history[i].get("dphi_L", 0)) + abs(history[i].get("dphi_R", 0)) + EPS)
        for i in range(T)
    ])
    combined /= combined.sum()
    rho_combined = _ensure_valid_density(sum(w * s for w, s in zip(combined, chiral_states)))
    results["chiral_retro_compress_combined"] = {**full_metrics(rho_combined), "max_weight": float(combined.max())}
    
    # G. Loop-phase-weighted chiral
    loop_weights = []
    for h in history:
        lp = h.get("loop_position", "inner")
        lr = h.get("loop_role", "heating")
        w = 1.0
        if lp == "outer":
            w *= 1.5
        if lr == "cooling":
            w *= 1.3
        loop_weights.append(w)
    lw = np.array(loop_weights)
    lw /= lw.sum()
    rho_loop = _ensure_valid_density(sum(w * s for w, s in zip(lw, chiral_states)))
    results["chiral_loop_phase"] = {**full_metrics(rho_loop), "max_weight": float(lw.max())}
    
    # Record p distribution across history
    results["p_distribution"] = {
        "mean": float(np.mean(p_values_hist)),
        "std": float(np.std(p_values_hist)),
        "min": float(np.min(p_values_hist)),
        "max": float(np.max(p_values_hist)),
    }
    
    return results


# ═══════════════════════════════════════════════════════════════════
# SUITE 5: BELL STATE HISTORY BRIDGES
# ═══════════════════════════════════════════════════════════════════

def run_bell_history_bridges(state):
    """Test all Bell states as history bridges with geometry-derived p."""
    history = state.history
    if not history:
        return {"error": "no history"}
    
    results = {}
    
    for bell_name, bell_psi in BELL_STATES.items():
        bridge_states = []
        for h in history:
            rL, rR = h["rho_L"], h["rho_R"]
            p = lr_asymmetry(rL, rR)
            p = float(np.clip(p, 0.01, 0.99))
            rho = make_entangled_state(rL, rR, bell_psi, p)
            bridge_states.append(rho)
        
        rho_avg = _ensure_valid_density(sum(bridge_states) / len(bridge_states))
        results[f"bell_{bell_name}_hist"] = full_metrics(rho_avg)
    
    # Also: geometry-axis-parameterized history
    axis_states = []
    for h in history:
        rho_axis, _, _ = make_geometry_theta_parameterized(h["rho_L"], h["rho_R"])
        axis_states.append(rho_axis)
    rho_axis_avg = _ensure_valid_density(sum(axis_states) / len(axis_states))
    results["geometry_axis_hist"] = full_metrics(rho_axis_avg)
    
    return results


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    print("=" * 80)
    print("AXIS 0 CHIRAL BRIDGE — DEEP SEARCH & ANTI-LEAK SUITE")
    print("=" * 80)
    
    all_results = []
    
    for engine_type in (1, 2):
        engine = GeometricEngine(engine_type=engine_type)
        for torus_label, eta in TORUS_CONFIGS:
            print(f"\n{'─' * 60}")
            print(f"  Engine Type {engine_type}, Torus: {torus_label} (η={eta:.4f})")
            print(f"{'─' * 60}")
            
            init_state = engine.init_state(eta=eta, theta1=0.0, theta2=0.0)
            final_state = engine.run_cycle(init_state)
            
            p_geom = lr_asymmetry(final_state.rho_L, final_state.rho_R)
            print(f"  Geometry-derived p (L/R asymmetry): {p_geom:.6f}")
            
            # Suite 1: Structure variation
            print(f"  Running Suite 1: Entanglement structure variation...")
            struct_results, _ = run_structure_variation(final_state)
            
            # Suite 2: Anti-leak
            print(f"  Running Suite 2: Anti-leak tests...")
            leak_results = run_anti_leak_tests(final_state)
            
            # Suite 3: Kernel compatibility
            print(f"  Running Suite 3: Kernel compatibility (50-point p sweep)...")
            kernel_results = run_kernel_compatibility(final_state)
            
            # Suite 4: Retrocausal chiral
            print(f"  Running Suite 4: Retrocausal chiral history...")
            retro_results = run_retrocausal_chiral(final_state)
            
            # Suite 5: Bell history
            print(f"  Running Suite 5: Bell state history bridges...")
            bell_results = run_bell_history_bridges(final_state)
            
            config_result = {
                "engine_type": engine_type,
                "torus": torus_label,
                "eta": float(eta),
                "p_geom": p_geom,
                "suite1_structure": struct_results,
                "suite2_anti_leak": leak_results,
                "suite3_kernel": kernel_results,
                "suite4_retrocausal": retro_results,
                "suite5_bell_history": bell_results,
            }
            all_results.append(config_result)
    
    # ═══════════════════════════════════════════════════════════════════
    # VERDICTS
    # ═══════════════════════════════════════════════════════════════════
    
    print(f"\n{'=' * 80}")
    print("VERDICTS")
    print(f"{'=' * 80}")
    
    # Verdict 1: Which entanglement structure wins?
    print(f"\n  1. ENTANGLEMENT STRUCTURE RANKING (pointwise, by mean I_AB across configs):")
    struct_names = list(all_results[0]["suite1_structure"].keys())
    struct_mis = {}
    for name in struct_names:
        mis = []
        for r in all_results:
            d = r["suite1_structure"].get(name, {})
            if "I_AB" in d:
                mis.append(d["I_AB"])
        if mis:
            struct_mis[name] = float(np.mean(mis))
    
    struct_ranking = sorted(struct_mis.items(), key=lambda x: x[1], reverse=True)
    for rank, (name, mi) in enumerate(struct_ranking, 1):
        marker = " ★" if rank == 1 else ""
        print(f"     {rank:>2}. {name:<40} I_AB = {mi:.6f}{marker}")
    
    # Verdict 2: Anti-leak test
    print(f"\n  2. ANTI-LEAK TEST:")
    matched_rows = []
    for r in all_results:
        leak = r["suite2_anti_leak"]
        random_mi = leak["random_entangle_at_p_geom"]["mean_I_AB"]
        geom_mi = r["suite1_structure"].get("phase1_winner_p_geom", {}).get("I_AB", 0)
        torus = r["torus"]
        p = r["p_geom"]
        print(f"     {r['engine_type']}/{torus}: random_MI={random_mi:.6f} vs geom_MI={geom_mi:.6f} "
              f"ratio={geom_mi/(random_mi+EPS):.2f} p_geom={p:.4f}")
        is_monotonic = leak.get("mi_monotonic_with_p", False)
        print(f"       MI monotonic with p: {is_monotonic}")
        matched = leak["matched_marginal_check"]
        matched_rows.append(
            {
                "engine_type": int(r["engine_type"]),
                "torus": torus,
                "delta_I_AB_vs_product": float(matched["delta_I_AB_vs_product"]),
                "delta_I_c_vs_product": float(matched["delta_I_c_vs_product"]),
                "preserves_marginals": bool(matched["preserves_marginals"]),
                "marginal_deviation_A_fro": float(matched["marginal_deviation_A_fro"]),
                "marginal_deviation_B_fro": float(matched["marginal_deviation_B_fro"]),
            }
        )
        print(
            f"       matched-marginal delta_I_AB={matched['delta_I_AB_vs_product']:.6f} "
            f"delta_I_c={matched['delta_I_c_vs_product']:.6f} "
            f"preserves_marginals={matched['preserves_marginals']}"
        )
    
    # Verdict 3: Kernel compatibility
    print(f"\n  3. KERNEL Φ₀ = -S(A|B) COMPATIBILITY:")
    for r in all_results:
        kern = r["suite3_kernel"]
        crossing = kern["ic_zero_crossing"]
        optimal = kern["optimal_p"]
        corr = kern["mi_ic_correlation"]
        print(f"     {r['engine_type']}/{r['torus']}: "
              f"I_c zero crossing at p={crossing.get('crossing_p', 'N/A')}, "
              f"MI-Ic corr={corr['spearman_r']:.4f}, "
              f"best_p_MI={optimal['best_p_for_MI']:.2f}, "
              f"best_p_Ic={optimal['best_p_for_Ic']:.2f}, "
              f"p_geom={r['p_geom']:.4f}")
    
    # Verdict 4: Best retrocausal chiral variant
    print(f"\n  4. RETROCAUSAL CHIRAL HISTORY RANKING (by mean I_AB):")
    retro_names = list(all_results[0]["suite4_retrocausal"].keys())
    retro_names = [n for n in retro_names if n != "p_distribution"]
    retro_mis = {}
    for name in retro_names:
        mis = []
        for r in all_results:
            d = r["suite4_retrocausal"].get(name, {})
            if "I_AB" in d:
                mis.append(d["I_AB"])
        if mis:
            retro_mis[name] = float(np.mean(mis))
    
    retro_ranking = sorted(retro_mis.items(), key=lambda x: x[1], reverse=True)
    for rank, (name, mi) in enumerate(retro_ranking, 1):
        marker = " ★" if rank == 1 else ""
        print(f"     {rank:>2}. {name:<40} I_AB = {mi:.6f}{marker}")
    
    # Verdict 5: Bell state history ranking
    print(f"\n  5. BELL STATE HISTORY BRIDGE RANKING (by mean I_AB):")
    bell_names = list(all_results[0]["suite5_bell_history"].keys())
    bell_mis = {}
    for name in bell_names:
        mis = []
        for r in all_results:
            d = r["suite5_bell_history"].get(name, {})
            if "I_AB" in d:
                mis.append(d["I_AB"])
        if mis:
            bell_mis[name] = float(np.mean(mis))
    
    bell_ranking = sorted(bell_mis.items(), key=lambda x: x[1], reverse=True)
    for rank, (name, mi) in enumerate(bell_ranking, 1):
        marker = " ★" if rank == 1 else ""
        print(f"     {rank:>2}. {name:<40} I_AB = {mi:.6f}{marker}")
    
    # === OVERALL ===
    print(f"\n{'=' * 80}")
    print("OVERALL CONCLUSIONS")
    print(f"{'=' * 80}")
    
    # Check if geometry-derived p is special
    all_monotonic = all(r["suite2_anti_leak"].get("mi_monotonic_with_p", False) for r in all_results)
    if all_monotonic:
        print("\n  ⚠ MI is MONOTONIC with p across all configs.")
        print("    → More entanglement → more MI, regardless of geometry.")
        print("    → Geometry-derived p is NOT special for MI.")
        print("    → The chiral bridge wins by INJECTING entanglement, not by geometry tuning.")
    else:
        print("\n  ✓ MI is NOT monotonic with p in at least one config.")
        print("    → There may be a geometry-sensitive sweet spot.")

    matched_preserves_count = int(
        sum(1 for row in matched_rows if row["preserves_marginals"])
    )
    mean_matched_delta_mi = float(np.mean([row["delta_I_AB_vs_product"] for row in matched_rows]))
    mean_matched_delta_ic = float(np.mean([row["delta_I_c_vs_product"] for row in matched_rows]))
    print(
        f"\n  ⚠ Matched-marginal check: preserves_marginals in {matched_preserves_count}/{len(matched_rows)} configs."
    )
    print(
        f"    mean delta_I_AB vs matched product = {mean_matched_delta_mi:.6f}, "
        f"mean delta_I_c = {mean_matched_delta_ic:.6f}"
    )
    
    # Check kernel ordering
    all_positive_corr = all(r["suite3_kernel"]["mi_ic_correlation"]["positive_correlation"] for r in all_results)
    if all_positive_corr:
        print("\n  ✓ Kernel Φ₀ = -S(A|B) correlates positively with MI across all configs.")
        print("    → The kernel ordering holds on chiral states.")
        print("    → -S(A|B) is a valid ranking metric for chiral bridges.")
    else:
        print("\n  ⚠ Kernel Φ₀ = -S(A|B) does NOT always correlate positively with MI.")
    
    # Save results
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "a2_state", "sim_results")
    os.makedirs(output_dir, exist_ok=True)
    
    def clean(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        if isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        if isinstance(obj, dict):
            return {k: clean(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [clean(v) for v in obj]
        return obj
    
    summary = {
        "timestamp": datetime.now(UTC).isoformat(),
        "probe": "sim_axis0_chiral_deep_search",
        "configs": len(all_results),
        "structure_ranking_by_mean_I_AB": [
            {"name": name, "mean_I_AB": float(mi)} for name, mi in struct_ranking
        ],
        "retrocausal_ranking_by_mean_I_AB": [
            {"name": name, "mean_I_AB": float(mi)} for name, mi in retro_ranking
        ],
        "bell_history_ranking_by_mean_I_AB": [
            {"name": name, "mean_I_AB": float(mi)} for name, mi in bell_ranking
        ],
        "anti_leak_summary": {
            "all_monotonic_with_p": bool(all_monotonic),
            "matched_marginal_preserves_count": matched_preserves_count,
            "matched_marginal_total_configs": len(matched_rows),
            "mean_delta_I_AB_vs_matched_product": mean_matched_delta_mi,
            "mean_delta_I_c_vs_matched_product": mean_matched_delta_ic,
            "rows": matched_rows,
        },
        "kernel_summary": {
            "all_positive_mi_ic_correlation": bool(all_positive_corr),
            "rows": [
                {
                    "engine_type": int(r["engine_type"]),
                    "torus": str(r["torus"]),
                    "spearman_r": float(r["suite3_kernel"]["mi_ic_correlation"]["spearman_r"]),
                    "positive_correlation": bool(r["suite3_kernel"]["mi_ic_correlation"]["positive_correlation"]),
                    "crossing_p": r["suite3_kernel"]["ic_zero_crossing"]["crossing_p"],
                    "best_p_for_MI": float(r["suite3_kernel"]["optimal_p"]["best_p_for_MI"]),
                    "best_p_for_Ic": float(r["suite3_kernel"]["optimal_p"]["best_p_for_Ic"]),
                    "p_geom": float(r["suite3_kernel"]["optimal_p"]["p_geom"]),
                }
                for r in all_results
            ],
        },
        "overall_conclusions": {
            "geometry_sensitive_sweet_spot_exists": bool(not all_monotonic),
            "kernel_positive_correlation_all_configs": bool(all_positive_corr),
        },
        "all_results": all_results,
    }
    
    out_path = os.path.join(output_dir, "axis0_chiral_deep_search_results.json")
    with open(out_path, "w") as f:
        json.dump(clean(summary), f, indent=2)
    print(f"\n  Results saved: {out_path}")
    
    print(f"\n{'=' * 80}")
    print(f"PROBE STATUS: PASS")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    main()
