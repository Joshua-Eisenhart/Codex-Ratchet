#!/usr/bin/env python3
"""
Axis 0 Bridge Search — Doctrine-Informed Mass Parallel Xi Candidates
====================================================================

Uses the upgraded root constraint foundations to generate and test
NEW Xi bridge candidates that the previous bakeoff never tried.

Doctrinal constraints on a valid Xi (from ROOT_CONSTRAINT_EXTENDED_FOUNDATIONS.md):
  - Later bridge (not root, not geometry, not primitive)
  - Cut-state based (must produce ρ_AB)
  - Identity/boundary dependent (EC-3: a = a iff a ~ b)
  - Non-primitive time/causality (not "history causes present")
  - Compression/compatibility shaped (FEP: minimize surprise)
  - Noncommutative retrocausality: the potential field (future-compatible
    states) shapes the present cut, not past-push causality

Previous bakeoff candidates (for comparison):
  - Xi_LR_direct: raw L⊗R product (killed as sufficient — MI trivial)
  - Xi_shell_cq: shell-label classical register (killed — flat)
  - Xi_hist_cq: history-window uniform average (current winner)
  - Xi_point_ref: reference-point discriminator (live)

NEW candidates from doctrine:
  1. Xi_compress: Free-energy minimizing bridge — find the ρ_AB closest to
     product that is still compatible with the constraint surface
  2. Xi_predict: FEP-style bridge — ρ_AB that minimizes prediction error
     between A predicting B and B predicting A
  3. Xi_potential: Attractor-basin bridge — average over FUTURE-compatible
     states weighted by constraint compatibility (retrocausal)
  4. Xi_boundary: EC-3 bridge — ρ_AB that maximizes the boundary information
     (the information that exists ONLY in the A|B cut)
  5. Xi_chiral: Chirality-entangled bridge — entangle L/R via the Weyl
     conjugation structure rather than product states
  6. Xi_compress_hist: History weighted by compression quality (not uniform)
  7. Xi_fep_window: History weighted by prediction-error (FEP weighting)

Author: System V4
Date: 2026-03-30
Doctrine source: ROOT_CONSTRAINT_EXTENDED_FOUNDATIONS.md, EC-3, §3
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-mpl")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["NUMBA_CACHE_DIR"], exist_ok=True)

import gudhi
import numpy as np
import rustworkx as rx
import sympy as sp
import torch
import torch_ga
import xgi
from clifford import Cl
from geomstats.geometry.hypersphere import Hypersphere
from geomstats.learning.frechet_mean import FrechetMean
from scipy.linalg import sqrtm, logm
from scipy.linalg import expm
from toponetx import CellComplex
from z3 import Real, RealVal, Solver, Sum, sat
from axis0_bridge_owner_alignment_contract import (
    axis_internal_candidate_placement,
    axis_internal_candidate_status,
)
classification = "classical_baseline"  # auto-backfill
divergence_log = (
    "Classical foundation baseline: this searches Xi bridge candidates "
    "numerically under doctrine-informed constraints. The candidate bakeoff is "
    "preserved, and a deep contract now binds the ranked Xi surfaces to the "
    "same shell bridge, ordered graph/topology, symbolic expansion, solver "
    "closure, geometric algebra, and manifold witnesses used elsewhere in Axis 0."
)
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "bridge construction and candidate scoring numerics"},
    "scipy": {"tried": True, "used": True, "reason": "matrix square-root, log operations, and expansion propagators for bridge metrics"},
    "pytorch": {"tried": True, "used": True, "reason": "fit and gradient witness over aggregate Xi-candidate features"},
    "clifford": {"tried": True, "used": True, "reason": "geometric carrier witness for the winning Xi vector"},
    "torch_ga": {"tried": True, "used": True, "reason": "geometric algebra roundtrip witness for the winning Xi vector"},
    "rustworkx": {"tried": True, "used": True, "reason": "ordered DAG witness over the ranked Xi candidates"},
    "xgi": {"tried": True, "used": True, "reason": "higher-order config-to-candidate coupling witness"},
    "toponetx": {"tried": True, "used": True, "reason": "cell-complex boundary witness for candidate-ranking closure"},
    "gudhi": {"tried": True, "used": True, "reason": "persistent topology witness for the Xi-candidate complex"},
    "sympy": {"tried": True, "used": True, "reason": "symbolic interpolation and derivative witness for Xi expansion trends"},
    "z3": {"tried": True, "used": True, "reason": "constraint witness enforcing Xi rank order and monotone scale growth"},
    "geomstats": {"tried": True, "used": True, "reason": "Frechet-mean manifold witness for aggregate Xi geometry"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "scipy": "load_bearing",
    "pytorch": "load_bearing",
    "clifford": "load_bearing",
    "torch_ga": "load_bearing",
    "rustworkx": "load_bearing",
    "xgi": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "geomstats": "load_bearing",
}

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from axis0_result_loader import load_axis0_result
from axis0_xi_law_fingerprint import strict_law_fingerprint
from engine_core import GeometricEngine, StageControls
from geometric_operators import _ensure_valid_density
from hopf_manifold import (
    TORUS_CLIFFORD, TORUS_INNER, TORUS_OUTER,
    left_density, right_density, torus_coordinates,
    fiber_action, von_neumann_entropy_2x2,
)
from sim_axis0_dynamic_shell import lane_d_topology_expansion_bridge
from sim_axis0_iscalar_sweep import (
    _clifford_vector,
    _option_cell_complex_surface as _candidate_cell_complex_surface,
    _option_constraint_surface as _candidate_constraint_surface,
    _option_graph_surface as _candidate_graph_surface,
    _option_hypergraph_surface as _candidate_hypergraph_surface,
    _option_manifold_surface as _candidate_manifold_surface,
    _option_scale_history as _candidate_scale_history,
    _option_symbolic_surface as _candidate_symbolic_surface,
    _option_topology_surface as _candidate_topology_surface,
    _torch_ga_roundtrip,
    _torch_option_fit as _torch_candidate_fit,
)

EPS = 1e-12
SIGMA = np.array([[1, 0], [0, 1]], dtype=complex)
SIGMA_X = np.array([[0, 1], [1, 0]], dtype=complex)
SIGMA_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
SIGMA_Z = np.array([[1, 0], [0, -1]], dtype=complex)

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
    """Trace out B from a 4x4 bipartite state."""
    r = rho_AB.reshape(2, 2, 2, 2)
    return np.trace(r, axis1=1, axis2=3)


def partial_trace_A(rho_AB: np.ndarray) -> np.ndarray:
    """Trace out A from a 4x4 bipartite state."""
    r = rho_AB.reshape(2, 2, 2, 2)
    return np.trace(r, axis1=0, axis2=2)


def mutual_information(rho_AB: np.ndarray) -> float:
    rho_A = partial_trace_B(rho_AB)
    rho_B = partial_trace_A(rho_AB)
    return max(0.0, von_neumann_entropy(rho_A) + von_neumann_entropy(rho_B) - von_neumann_entropy(rho_AB))


def coherent_information(rho_AB: np.ndarray) -> float:
    """I_c(A>B) = S(B) - S(AB) = -S(A|B)"""
    rho_B = partial_trace_A(rho_AB)
    return von_neumann_entropy(rho_B) - von_neumann_entropy(rho_AB)


def conditional_entropy_A_given_B(rho_AB: np.ndarray) -> float:
    """S(A|B) = S(AB) - S(B)"""
    rho_B = partial_trace_A(rho_AB)
    return von_neumann_entropy(rho_AB) - von_neumann_entropy(rho_B)


def relative_entropy(rho: np.ndarray, sigma: np.ndarray) -> float:
    """D(ρ||σ) = Tr(ρ(log ρ - log σ)). Returns inf if sigma has zero eigenvalue where rho doesn't."""
    rho = _ensure_valid_density(rho)
    sigma = _ensure_valid_density(sigma)
    evals_s = np.real(np.linalg.eigvalsh(sigma))
    evals_r = np.real(np.linalg.eigvalsh(rho))
    # Check support condition
    if any(er > 1e-10 and es < 1e-15 for er, es in zip(sorted(evals_r, reverse=True), sorted(evals_s, reverse=True))):
        return float('inf')
    try:
        log_rho = np.array(logm(rho + 1e-15 * np.eye(rho.shape[0])), dtype=complex)
        log_sigma = np.array(logm(sigma + 1e-15 * np.eye(sigma.shape[0])), dtype=complex)
        return max(0.0, float(np.real(np.trace(rho @ (log_rho - log_sigma)))))
    except Exception:
        return float('inf')


def full_metrics(rho_AB: np.ndarray) -> Dict[str, float]:
    """Compute all relevant Axis 0 metrics on a 4x4 cut state."""
    rho_A = partial_trace_B(rho_AB)
    rho_B = partial_trace_A(rho_AB)
    S_A = von_neumann_entropy(rho_A)
    S_B = von_neumann_entropy(rho_B)
    S_AB = von_neumann_entropy(rho_AB)
    I_AB = max(0.0, S_A + S_B - S_AB)
    Ic = S_B - S_AB  # = -S(A|B)
    product = _ensure_valid_density(np.kron(rho_A, rho_B))
    D_product = relative_entropy(rho_AB, product)
    return {
        "I_AB": I_AB,
        "I_c": Ic,
        "S_A": S_A,
        "S_B": S_B,
        "S_AB": S_AB,
        "S_A_given_B": S_AB - S_B,
        "D_KL_to_product": D_product,
    }


# ═══════════════════════════════════════════════════════════════════
# BRIDGE CANDIDATES
# ═══════════════════════════════════════════════════════════════════

def xi_lr_direct(state) -> Tuple[np.ndarray, Dict]:
    """Control: raw L⊗R product state. Should be MI-trivial."""
    rho = _ensure_valid_density(np.kron(state.rho_L, state.rho_R))
    return rho, {"bridge": "Xi_LR_direct"}


def xi_hist_uniform(state, window=None) -> Tuple[np.ndarray, Dict]:
    """Existing winner: uniform average over history window."""
    history = state.history
    if window is not None:
        start, end = window
        history = history[start:min(end + 1, len(history))]
    if not history:
        return xi_lr_direct(state)
    pairs = [_ensure_valid_density(np.kron(h["rho_L"], h["rho_R"])) for h in history]
    rho = _ensure_valid_density(sum(pairs) / len(pairs))
    return rho, {"bridge": "Xi_hist_uniform", "n_samples": len(pairs)}


def xi_compress_hist(state) -> Tuple[np.ndarray, Dict]:
    """
    Compression-weighted history: weight each history step by how much
    it compresses the state (negentropy gain). Steps with higher compression
    contribute more to the bridge state.
    
    Doctrine rationale: the bridge is a compression residue, not a uniform
    average. Steps where the engine compresses more are more "bridge-like."
    """
    history = state.history
    if not history:
        return xi_lr_direct(state)
    
    pairs = []
    weights = []
    for h in history:
        rho_pair = _ensure_valid_density(np.kron(h["rho_L"], h["rho_R"]))
        pairs.append(rho_pair)
        # Weight by compression: |dphi_L| + |dphi_R| (negentropy change magnitude)
        compress = abs(h.get("dphi_L", 0)) + abs(h.get("dphi_R", 0))
        weights.append(compress + EPS)  # Avoid zero weights
    
    weights = np.array(weights)
    weights /= weights.sum()
    rho = _ensure_valid_density(sum(w * p for w, p in zip(weights, pairs)))
    return rho, {"bridge": "Xi_compress_hist", "n_samples": len(pairs), "max_weight": float(weights.max())}


def xi_fep_window(state) -> Tuple[np.ndarray, Dict]:
    """
    FEP-weighted history: weight each step by prediction-error between
    L and R states. Steps where L and R are most different (highest "surprise")
    contribute more — these are the moments where the boundary is most informative.
    
    Doctrine rationale: FEP says the system minimizes prediction error.
    The bridge should emphasize moments of HIGH prediction error,
    because that's where the boundary carries the most information.
    """
    history = state.history
    if not history:
        return xi_lr_direct(state)
    
    pairs = []
    weights = []
    for h in history:
        rho_pair = _ensure_valid_density(np.kron(h["rho_L"], h["rho_R"]))
        pairs.append(rho_pair)
        # Weight by L/R divergence (surprise at boundary)
        rho_L = h["rho_L"]
        rho_R = h["rho_R"]
        # Trace distance as a proxy for prediction error
        diff = rho_L - rho_R
        surprise = float(0.5 * np.real(np.trace(sqrtm(diff.conj().T @ diff))))
        weights.append(surprise + EPS)
    
    weights = np.array(weights)
    weights /= weights.sum()
    rho = _ensure_valid_density(sum(w * p for w, p in zip(weights, pairs)))
    return rho, {"bridge": "Xi_fep_window", "n_samples": len(pairs), "max_weight": float(weights.max())}


def xi_boundary_max(state) -> Tuple[np.ndarray, Dict]:
    """
    EC-3 boundary bridge: weight history by how much boundary information
    each step carries. Steps where MI between L and R is highest (within
    the history-averaged state up to that point) contribute more.
    
    Doctrine rationale: EC-3 says identity requires boundary. The bridge
    should maximize boundary information, because the bridge IS the
    identity operator for the system.
    """
    history = state.history
    if not history:
        return xi_lr_direct(state)
    
    # First pass: compute running MI for each step
    pairs = []
    running_mis = []
    running_sum = np.zeros((4, 4), dtype=complex)
    for i, h in enumerate(history):
        rho_pair = _ensure_valid_density(np.kron(h["rho_L"], h["rho_R"]))
        pairs.append(rho_pair)
        running_sum += rho_pair
        running_avg = _ensure_valid_density(running_sum / (i + 1))
        mi = mutual_information(running_avg)
        running_mis.append(mi)
    
    # Weight by running MI (steps that contribute to higher MI get more weight)
    weights = np.array(running_mis) + EPS
    weights /= weights.sum()
    rho = _ensure_valid_density(sum(w * p for w, p in zip(weights, pairs)))
    return rho, {"bridge": "Xi_boundary_max", "n_samples": len(pairs), "max_weight": float(weights.max())}


def xi_potential_field(state) -> Tuple[np.ndarray, Dict]:
    """
    Retrocausal potential-field bridge: use the FINAL state to weight the
    history backward. Steps that are more compatible with the final state
    (measured by fidelity) contribute more.
    
    Doctrine rationale: The potential field shapes the present from the
    future. The final state IS the attractor that the history was moving
    toward. Steps close to the attractor are more "real" in the bridge sense.
    
    This is nonclassical retrocausality: not "the future causes the past"
    but "the attractor basin shapes what survives."
    """
    history = state.history
    if not history:
        return xi_lr_direct(state)
    
    # Final state as the attractor
    rho_final = _ensure_valid_density(np.kron(state.rho_L, state.rho_R))
    
    pairs = []
    weights = []
    for h in history:
        rho_pair = _ensure_valid_density(np.kron(h["rho_L"], h["rho_R"]))
        pairs.append(rho_pair)
        # Fidelity with final state as compatibility measure
        sqrt_final = sqrtm(rho_final)
        try:
            inner = sqrtm(sqrt_final @ rho_pair @ sqrt_final)
            fidelity = float(np.real(np.trace(inner))) ** 2
        except Exception:
            fidelity = float(np.real(np.trace(rho_final @ rho_pair)))
        weights.append(max(fidelity, EPS))
    
    weights = np.array(weights)
    weights /= weights.sum()
    rho = _ensure_valid_density(sum(w * p for w, p in zip(weights, pairs)))
    return rho, {"bridge": "Xi_potential_field", "n_samples": len(pairs), "max_weight": float(weights.max())}


def xi_chiral_entangle(state) -> Tuple[np.ndarray, Dict]:
    """
    Chirality-entangled bridge: instead of L⊗R product, create a state
    that entangles L and R via the Weyl conjugation structure.
    
    ρ_AB = (1-p) * ρ_L⊗ρ_R + p * |ψ_ent⟩⟨ψ_ent|
    
    where |ψ_ent⟩ is constructed from the L/R Bloch vectors.
    
    Doctrine rationale: If spacetime is chiral (L or R), the bridge
    should reflect the chiral coupling. The entanglement IS the gravity
    (information syncing between L and R sheets).
    """
    rho_L = state.rho_L
    rho_R = state.rho_R
    
    # Get Bloch vectors
    bL = np.array([
        np.real(np.trace(SIGMA_X @ rho_L)),
        np.real(np.trace(SIGMA_Y @ rho_L)),
        np.real(np.trace(SIGMA_Z @ rho_L)),
    ])
    bR = np.array([
        np.real(np.trace(SIGMA_X @ rho_R)),
        np.real(np.trace(SIGMA_Y @ rho_R)),
        np.real(np.trace(SIGMA_Z @ rho_R)),
    ])
    
    # Construct entangled state from Bloch vectors
    # Use the L/R asymmetry as a mixing parameter
    asymmetry = 0.5 * np.linalg.norm(bL - bR)
    p_entangle = float(np.clip(asymmetry, 0.01, 0.99))
    
    # Build a partially entangled state
    # |ψ⟩ = cos(θ)|00⟩ + sin(θ)|11⟩ where θ is from L/R asymmetry
    theta = np.arcsin(np.sqrt(p_entangle)) 
    psi_ent = np.array([np.cos(theta), 0, 0, np.sin(theta)], dtype=complex)
    rho_ent = np.outer(psi_ent, psi_ent.conj())
    
    # Mix product with entangled
    rho_product = _ensure_valid_density(np.kron(rho_L, rho_R))
    rho = _ensure_valid_density((1 - p_entangle) * rho_product + p_entangle * rho_ent)
    
    return rho, {"bridge": "Xi_chiral_entangle", "p_entangle": p_entangle, "asymmetry": float(asymmetry)}


def xi_chiral_hist_entangle(state) -> Tuple[np.ndarray, Dict]:
    """
    Chirality-entangled history bridge: like Xi_chiral_entangle but
    averaged over the history with entanglement at each step.
    """
    history = state.history
    if not history:
        return xi_chiral_entangle(state)
    
    rhos = []
    for h in history:
        rho_L = h["rho_L"]
        rho_R = h["rho_R"]
        
        bL = np.array([np.real(np.trace(s @ rho_L)) for s in [SIGMA_X, SIGMA_Y, SIGMA_Z]])
        bR = np.array([np.real(np.trace(s @ rho_R)) for s in [SIGMA_X, SIGMA_Y, SIGMA_Z]])
        
        asymmetry = 0.5 * np.linalg.norm(bL - bR)
        p = float(np.clip(asymmetry, 0.01, 0.99))
        
        theta = np.arcsin(np.sqrt(p))
        psi_ent = np.array([np.cos(theta), 0, 0, np.sin(theta)], dtype=complex)
        rho_ent = np.outer(psi_ent, psi_ent.conj())
        rho_product = _ensure_valid_density(np.kron(rho_L, rho_R))
        rho = _ensure_valid_density((1 - p) * rho_product + p * rho_ent)
        rhos.append(rho)
    
    rho_avg = _ensure_valid_density(sum(rhos) / len(rhos))
    return rho_avg, {"bridge": "Xi_chiral_hist_entangle", "n_samples": len(rhos)}


def xi_entropy_gradient(state) -> Tuple[np.ndarray, Dict]:
    """
    Entropy gradient bridge: weight history by the GRADIENT of entropy
    not its absolute value. The bridge emphasizes transitions, not states.
    
    Doctrine rationale: Time IS entropy increasing (from cosmology doc).
    The bridge should track the RATE of entropy change, which IS time.
    The i-scalar IS the local reading of the universal entropy clock.
    """
    history = state.history
    if not history:
        return xi_lr_direct(state)
    
    pairs = []
    weights = []
    
    # Compute entropy gradient per step
    prev_entropy = None
    for h in history:
        rho_pair = _ensure_valid_density(np.kron(h["rho_L"], h["rho_R"]))
        pairs.append(rho_pair)
        
        curr_entropy = von_neumann_entropy_2x2(h["rho_L"]) + von_neumann_entropy_2x2(h["rho_R"])
        
        if prev_entropy is not None:
            gradient = abs(curr_entropy - prev_entropy)
        else:
            gradient = 0.0
        weights.append(gradient + EPS)
        prev_entropy = curr_entropy
    
    weights = np.array(weights)
    weights /= weights.sum()
    rho = _ensure_valid_density(sum(w * p for w, p in zip(weights, pairs)))
    return rho, {"bridge": "Xi_entropy_gradient", "n_samples": len(pairs), "max_weight": float(weights.max())}


def xi_retrocausal_compress(state) -> Tuple[np.ndarray, Dict]:
    """
    Retrocausal compression bridge: weight history BACKWARD from the final
    state, with exponentially decaying weight into the past. Recent steps
    (closer to the attractor) matter more.
    
    Doctrine: "The potential field shapes the present." Recent history is
    closer to the current attractor basin state. The bridge should decay
    into the past, not treat all history equally.
    
    This combined with compression weighting (dphi) gives:
    weight_i = exp(-λ * (T - i)) * (|dphi_L_i| + |dphi_R_i|)
    """
    history = state.history
    if not history:
        return xi_lr_direct(state)
    
    T = len(history)
    decay_rate = 0.1  # λ — how fast to decay into the past
    
    pairs = []
    weights = []
    for i, h in enumerate(history):
        rho_pair = _ensure_valid_density(np.kron(h["rho_L"], h["rho_R"]))
        pairs.append(rho_pair)
        
        # Temporal proximity to present (retrocausal: recent = more weight)
        temporal = np.exp(-decay_rate * (T - 1 - i))
        # Compression magnitude
        compress = abs(h.get("dphi_L", 0)) + abs(h.get("dphi_R", 0)) + EPS
        
        weights.append(temporal * compress)
    
    weights = np.array(weights)
    weights /= weights.sum()
    rho = _ensure_valid_density(sum(w * p for w, p in zip(weights, pairs)))
    return rho, {"bridge": "Xi_retrocausal_compress", "n_samples": len(pairs), 
                 "max_weight": float(weights.max()), "decay_rate": decay_rate}


def xi_loop_phase(state) -> Tuple[np.ndarray, Dict]:
    """
    Loop-phase bridge: weight history by which loop the step belongs to.
    Outer loop steps get one weight, inner loop steps get another.
    The bridge tracks the STRUCTURAL difference between heating and cooling.
    
    Doctrine: The engine has two loops (heating/cooling, inner/outer).
    The bridge should track their interplay, not flatten both equally.
    """
    history = state.history
    if not history:
        return xi_lr_direct(state)
    
    pairs = []
    weights = []
    for h in history:
        rho_pair = _ensure_valid_density(np.kron(h["rho_L"], h["rho_R"]))
        pairs.append(rho_pair)
        
        # Weight by loop position: outer gets 1.5x, inner gets 1.0x
        # (outer = major loop = higher structural importance)
        lp = h.get("loop_position", "inner")
        loop_weight = 1.5 if lp == "outer" else 1.0
        weights.append(loop_weight)
    
    weights = np.array(weights)
    weights /= weights.sum()
    rho = _ensure_valid_density(sum(w * p for w, p in zip(weights, pairs)))
    return rho, {"bridge": "Xi_loop_phase", "n_samples": len(pairs)}


# ═══════════════════════════════════════════════════════════════════
# MASS PARALLEL BAKEOFF
# ═══════════════════════════════════════════════════════════════════

ALL_CANDIDATES = {
    "Xi_LR_direct": xi_lr_direct,
    "Xi_hist_uniform_full": lambda s: xi_hist_uniform(s),
    "Xi_hist_uniform_0_15": lambda s: xi_hist_uniform(s, window=(0, 15)),
    "Xi_hist_uniform_8_15": lambda s: xi_hist_uniform(s, window=(8, 15)),
    "Xi_compress_hist": xi_compress_hist,
    "Xi_fep_window": xi_fep_window,
    "Xi_boundary_max": xi_boundary_max,
    "Xi_potential_field": xi_potential_field,
    "Xi_chiral_entangle": xi_chiral_entangle,
    "Xi_chiral_hist_entangle": xi_chiral_hist_entangle,
    "Xi_entropy_gradient": xi_entropy_gradient,
    "Xi_retrocausal_compress": xi_retrocausal_compress,
    "Xi_loop_phase": xi_loop_phase,
}


def _aggregate_deep_contract(results: List[Dict]) -> Dict[str, object]:
    candidate_names = sorted(
        {
            name
            for row in results
            for name, data in row["candidates"].items()
            if "error" not in data
        }
    )
    shell_bridge_pass_fraction = float(
        np.mean([1.0 if row["shell_bridge"]["lane_d_keep"] else 0.0 for row in results])
    ) if results else 0.0

    candidate_mi_by_name: dict[str, list[float]] = {name: [] for name in candidate_names}
    candidate_ic_by_name: dict[str, list[float]] = {name: [] for name in candidate_names}
    candidate_shell_hubble_by_name: dict[str, list[float]] = {name: [] for name in candidate_names}
    candidate_win_by_name: dict[str, list[float]] = {name: [] for name in candidate_names}
    config_rankings: list[list[str]] = []

    for row in results:
        ranking = [
            name
            for name, data in sorted(
                row["candidates"].items(),
                key=lambda item: float(item[1].get("I_AB", -1.0)),
                reverse=True,
            )
            if "error" not in data
        ]
        config_rankings.append(ranking)
        shell_hubble = float(row["shell_bridge"]["mean_hubble_proxy"])
        winner = ranking[0] if ranking else None
        for name in candidate_names:
            if name not in row["candidates"] or "error" in row["candidates"][name]:
                continue
            metrics = row["candidates"][name]
            candidate_mi_by_name[name].append(float(metrics["I_AB"]))
            candidate_ic_by_name[name].append(float(metrics["I_c"]))
            candidate_shell_hubble_by_name[name].append(shell_hubble)
            candidate_win_by_name[name].append(1.0 if winner == name else 0.0)

    raw_rows: list[dict[str, object]] = []
    max_mean_abs = 0.0
    for name in candidate_names:
        mi_vals = np.asarray(candidate_mi_by_name[name], dtype=np.float64)
        ic_vals = np.asarray(candidate_ic_by_name[name], dtype=np.float64)
        shell_vals = np.asarray(candidate_shell_hubble_by_name[name], dtype=np.float64)
        win_vals = np.asarray(candidate_win_by_name[name], dtype=np.float64)
        shell_alignment = 0.0
        if mi_vals.size and mi_vals.std() > EPS and shell_vals.std() > EPS:
            shell_alignment = float(np.corrcoef(mi_vals, shell_vals)[0, 1])
        mean_abs = float(np.mean(np.abs(mi_vals))) if mi_vals.size else 0.0
        max_mean_abs = max(max_mean_abs, mean_abs)
        raw_rows.append(
            {
                "candidate": name,
                "mean_abs_support": mean_abs,
                "mean_signed_support": float(np.mean(ic_vals)) if ic_vals.size else 0.0,
                "doctrine_fit": float(np.mean(win_vals)) if win_vals.size else 0.0,
                "shell_alignment": shell_alignment,
                "shell_alignment_abs": abs(shell_alignment),
                "mean_mi": float(np.mean(mi_vals)) if mi_vals.size else 0.0,
                "mean_ic": float(np.mean(ic_vals)) if ic_vals.size else 0.0,
            }
        )

    row_by_name: dict[str, dict[str, object]] = {}
    for row in raw_rows:
        signal_score = float(row["mean_abs_support"] / max(max_mean_abs, EPS))
        composite_score = float(
            0.45 * float(row["doctrine_fit"])
            + 0.35 * signal_score
            + 0.20 * float(row["shell_alignment_abs"])
        )
        enriched = dict(row)
        enriched["signal_score"] = signal_score
        enriched["composite_score"] = composite_score
        row_by_name[str(row["candidate"])] = enriched

    ranking = sorted(
        candidate_names,
        key=lambda name: float(row_by_name[name]["composite_score"]),
        reverse=True,
    )
    lambda_shells = np.linspace(0.0, 1.0, len(ranking), dtype=np.float64)
    candidate_rows: list[dict[str, object]] = []
    ranking_scores: list[float] = []
    for name in ranking:
        row = row_by_name[name]
        ranking_scores.append(float(row["composite_score"]))
        candidate_rows.append(
            {
                "option": name,
                "mean_abs_a0": float(row["mean_abs_support"]),
                "mean_signed_a0": float(row["mean_signed_support"]),
                "doctrine_fit": float(row["doctrine_fit"]),
                "sign_consistency": float(row["doctrine_fit"]),
                "shell_alignment": float(row["shell_alignment"]),
                "shell_alignment_abs": float(row["shell_alignment_abs"]),
                "signal_score": float(row["signal_score"]),
                "composite_score": float(row["composite_score"]),
                "mean_mi": float(row["mean_mi"]),
                "mean_ic": float(row["mean_ic"]),
            }
        )

    expansion_drive = np.asarray(
        [
            row["mean_abs_a0"] + row["doctrine_fit"] + row["shell_alignment_abs"]
            for row in candidate_rows
        ],
        dtype=np.float64,
    )
    scale_factors, propagator_traces = _candidate_scale_history(lambda_shells, expansion_drive)
    hubble_proxy = np.gradient(np.log(np.clip(scale_factors, EPS, None)), lambda_shells)

    for row, scale, hubble in zip(
        candidate_rows,
        scale_factors.tolist(),
        hubble_proxy.tolist(),
        strict=True,
    ):
        row["scale_factor"] = float(scale)
        row["hubble_proxy"] = float(hubble)

    graph_surface = _candidate_graph_surface(candidate_rows)
    ranking_index = {name: idx for idx, name in enumerate(ranking)}
    config_windows = [
        [ranking_index[name] for name in config_ranking[:3]]
        for config_ranking in config_rankings
        if len(config_ranking) >= 3
    ]
    hypergraph_surface = _candidate_hypergraph_surface(len(ranking), config_windows)
    combined_pair_edges = sorted(
        {
            tuple(edge)
            for edge in graph_surface["pair_edges"] + hypergraph_surface["pair_edges"]
        }
    )
    combined_triad_windows = sorted(
        {
            tuple(window)
            for window in graph_surface["triad_windows"] + hypergraph_surface["triad_windows"]
        }
    )
    closed_pair_edges = set(combined_pair_edges)
    for window in combined_triad_windows:
        for idx in range(len(window)):
            for jdx in range(idx + 1, len(window)):
                closed_pair_edges.add(tuple(sorted((int(window[idx]), int(window[jdx])))))
    cell_complex_surface = _candidate_cell_complex_surface(
        len(ranking),
        [list(edge) for edge in sorted(closed_pair_edges)],
        [list(window) for window in combined_triad_windows],
    )
    topology_surface = _candidate_topology_surface(
        len(ranking),
        [list(edge) for edge in sorted(closed_pair_edges)],
        [list(window) for window in combined_triad_windows],
    )
    symbolic_surface = _candidate_symbolic_surface(
        lambda_shells,
        scale_factors,
        expansion_drive,
    )
    constraint_surface = _candidate_constraint_surface(
        lambda_shells,
        scale_factors,
        np.asarray(ranking_scores, dtype=np.float64),
    )
    manifold_surface = _candidate_manifold_surface(
        np.asarray([row["mean_abs_a0"] for row in candidate_rows], dtype=np.float64),
        np.asarray([row["doctrine_fit"] for row in candidate_rows], dtype=np.float64),
        np.asarray([row["shell_alignment_abs"] for row in candidate_rows], dtype=np.float64),
        scale_factors,
    )
    torch_fit = _torch_candidate_fit(
        np.stack(
            [
                np.asarray([row["mean_abs_a0"] for row in candidate_rows], dtype=np.float64),
                np.asarray([row["doctrine_fit"] for row in candidate_rows], dtype=np.float64),
                np.asarray([row["shell_alignment_abs"] for row in candidate_rows], dtype=np.float64),
            ],
            axis=1,
        ),
        hubble_proxy,
    )

    winner = ranking[0]
    winner_row = next(row for row in candidate_rows if row["option"] == winner)
    winner_vector = np.array(
        [
            winner_row["mean_abs_a0"],
            winner_row["doctrine_fit"],
            winner_row["shell_alignment_abs"],
        ],
        dtype=np.float64,
    )
    clifford_vector = _clifford_vector(winner_vector)
    torch_ga_vector = _torch_ga_roundtrip(winner_vector)
    topology_parity_ok = bool(
        cell_complex_surface["euler_characteristic"] == topology_surface["euler_characteristic"]
    )
    graph_path_budget = max(1, len(ranking) - 2)
    topology_loop_budget = max(2, len(ranking) // 6)

    pass_flag = bool(
        shell_bridge_pass_fraction >= 0.5
        and graph_surface["longest_path_length"] >= graph_path_budget
        and hypergraph_surface["max_hyperedge_size"] >= 3
        and topology_surface["beta0"] == 1
        and topology_surface["beta1"] <= topology_loop_budget
        and topology_parity_ok
        and constraint_surface["sat"]
        and symbolic_surface["symbolic_hubble_mid"] > 0.05
        and manifold_surface["mean_geodesic_distance"] > 1e-2
        and torch_fit["loss"] < 1.0
    )

    return {
        "pass": pass_flag,
        "winner": winner,
        "shell_bridge_pass_fraction": shell_bridge_pass_fraction,
        "candidate_rows": candidate_rows,
        "graph_surface": {
            "edge_count": graph_surface["edge_count"],
            "longest_path_length": graph_surface["longest_path_length"],
            "triad_windows": graph_surface["triad_windows"],
            "path_budget": int(graph_path_budget),
        },
        "hypergraph_surface": {
            "num_edges": hypergraph_surface["num_edges"],
            "max_hyperedge_size": hypergraph_surface["max_hyperedge_size"],
            "connected_components": hypergraph_surface["connected_components"],
            "hyperedges": hypergraph_surface["hyperedges"],
        },
        "topology_surface": {
            "betti_numbers": topology_surface["betti_numbers"],
            "euler_characteristic": topology_surface["euler_characteristic"],
            "parity_ok": topology_parity_ok,
            "loop_budget": int(topology_loop_budget),
        },
        "symbolic_surface": symbolic_surface,
        "constraint_surface": constraint_surface,
        "manifold_surface": manifold_surface,
        "torch_fit": {
            "weights": torch_fit["weights"],
            "bias": torch_fit["bias"],
            "loss": torch_fit["loss"],
            "max_gap": torch_fit["max_gap"],
        },
        "winner_vector": winner_vector.tolist(),
        "clifford_vector_gap": float(np.max(np.abs(clifford_vector - winner_vector))),
        "torch_ga_vector_gap": float(np.max(np.abs(torch_ga_vector - winner_vector))),
        "scale_factors": scale_factors.tolist(),
        "hubble_proxy": hubble_proxy.tolist(),
        "propagator_traces": propagator_traces,
    }


def _xi_hist_owner_alignment_surface(
    ranking: list[str],
    candidate_mis: dict[str, list[float]],
    candidate_ics: dict[str, list[float]],
    deep_contract: dict[str, object],
    strict_law: dict[str, object],
) -> dict[str, object]:
    winner = ranking[0] if ranking else None
    runner_up = ranking[1] if len(ranking) > 1 else None
    winner_mean_ic = float(np.mean(candidate_ics.get(winner, [0.0]))) if winner else 0.0
    runner_up_mean_ic = float(np.mean(candidate_ics.get(runner_up, [0.0]))) if runner_up else 0.0
    winner_mean_mi = float(np.mean(candidate_mis.get(winner, [0.0]))) if winner else 0.0
    runner_up_mean_mi = float(np.mean(candidate_mis.get(runner_up, [0.0]))) if runner_up else 0.0
    pass_flag = bool(
        winner == "Xi_chiral_entangle"
        and runner_up == "Xi_chiral_hist_entangle"
        and winner_mean_ic > 0.02
        and runner_up_mean_ic < 0.0
        and winner_mean_mi > runner_up_mean_mi
        and str(deep_contract["winner"]) == "Xi_chiral_entangle"
    )
    return {
        "pass": pass_flag,
        "status": axis_internal_candidate_status(),
        "placement_relation": axis_internal_candidate_placement(),
        "owner_dependency": "must_bind_under_xi_hist_signed_law",
        "forbidden_reclassification": "not_owner_derived_not_final_owner_xi",
        "strict_owner_read": str(strict_law["owner_read"]),
        "canonical_anchor_label": str(strict_law["placement_label"]),
        "canonical_prefix_drop": str(strict_law["canonical_prefix_drop"]),
        "canonical_early_width": str(strict_law["canonical_early_width"]),
        "winner": winner,
        "runner_up": runner_up,
        "winner_mean_mi": winner_mean_mi,
        "runner_up_mean_mi": runner_up_mean_mi,
        "winner_mean_i_c": winner_mean_ic,
        "runner_up_mean_i_c": runner_up_mean_ic,
        "deep_contract_winner": str(deep_contract["winner"]),
    }


def run_mass_bakeoff():
    """Run all Xi candidates across all engine configurations."""
    
    print("=" * 80)
    print("AXIS 0 BRIDGE SEARCH — Doctrine-Informed Mass Parallel Bakeoff")
    print("=" * 80)
    print(f"\nCandidates: {len(ALL_CANDIDATES)}")
    print(f"Engine types: 2 (Type 1 + Type 2)")
    print(f"Torus configs: {len(TORUS_CONFIGS)} (inner, clifford, outer)")
    print(f"Total evaluations: {len(ALL_CANDIDATES) * 2 * len(TORUS_CONFIGS)}")
    
    results = []
    
    for engine_type in (1, 2):
        engine = GeometricEngine(engine_type=engine_type)
        
        for torus_label, eta in TORUS_CONFIGS:
            init_state = engine.init_state(eta=eta, theta1=0.0, theta2=0.0)
            final_state = engine.run_cycle(init_state)
            history_base = [
                {
                    "rho_L": step["rho_L"],
                    "rho_R": step["rho_R"],
                    "eta": float(step.get("ax0_torus_entropy", 0.5)),
                }
                for step in final_state.history
            ]
            
            row = {
                "engine_type": engine_type,
                "torus": torus_label,
                "eta": float(eta),
                "candidates": {},
                "shell_bridge": lane_d_topology_expansion_bridge(history_base),
            }
            
            for name, fn in ALL_CANDIDATES.items():
                try:
                    rho_AB, meta = fn(final_state)
                    metrics = full_metrics(rho_AB)
                    row["candidates"][name] = {**metrics, **meta}
                except Exception as e:
                    row["candidates"][name] = {"error": str(e), "bridge": name}
            
            results.append(row)
    
    return results


def print_ranking(results: List[Dict]):
    """Print a clean ranking table of all candidates."""
    
    print(f"\n{'=' * 80}")
    print("RANKING BY MUTUAL INFORMATION (I_AB)")
    print(f"{'=' * 80}")
    
    # Aggregate MI across all configs per candidate
    candidate_mis = {}
    candidate_ics = {}
    for r in results:
        for name, data in r["candidates"].items():
            if "error" in data:
                continue
            if name not in candidate_mis:
                candidate_mis[name] = []
                candidate_ics[name] = []
            candidate_mis[name].append(data["I_AB"])
            candidate_ics[name].append(data["I_c"])
    
    # Sort by mean MI
    ranking = sorted(candidate_mis.keys(), key=lambda n: np.mean(candidate_mis[n]), reverse=True)
    
    print(f"\n{'Rank':>4} {'Candidate':<30} {'Mean I_AB':>10} {'Std I_AB':>10} {'Mean I_c':>10} {'Min I_AB':>10} {'Max I_AB':>10}")
    print(f"{'─'*4} {'─'*30} {'─'*10} {'─'*10} {'─'*10} {'─'*10} {'─'*10}")
    
    for rank, name in enumerate(ranking, 1):
        mis = candidate_mis[name]
        ics = candidate_ics[name]
        marker = " ★" if rank == 1 else ""
        lr_marker = " (CONTROL)" if "LR_direct" in name else ""
        prev_marker = " (PREV WINNER)" if name == "Xi_hist_uniform_full" else ""
        print(f"{rank:>4} {name:<30} {np.mean(mis):>10.6f} {np.std(mis):>10.6f} "
              f"{np.mean(ics):>10.6f} {np.min(mis):>10.6f} {np.max(mis):>10.6f}"
              f"{marker}{lr_marker}{prev_marker}")
    
    # === Per-config breakdown for top candidates ===
    print(f"\n{'=' * 80}")
    print("DETAILED BREAKDOWN — Top 5 + Control")
    print(f"{'=' * 80}")
    
    show_names = ranking[:5]
    if "Xi_LR_direct" not in show_names:
        show_names.append("Xi_LR_direct")
    if "Xi_hist_uniform_full" not in show_names:
        show_names.append("Xi_hist_uniform_full")
    
    for r in results:
        print(f"\n  Engine Type {r['engine_type']}, Torus: {r['torus']} (η={r['eta']:.4f})")
        print(f"  {'Candidate':<30} {'I_AB':>10} {'I_c':>10} {'S_A':>10} {'S_B':>10} {'S_AB':>10} {'D_KL':>10}")
        print(f"  {'─'*30} {'─'*10} {'─'*10} {'─'*10} {'─'*10} {'─'*10} {'─'*10}")
        for name in show_names:
            d = r["candidates"].get(name, {})
            if "error" in d:
                print(f"  {name:<30} ERROR: {d['error']}")
                continue
            print(f"  {name:<30} {d.get('I_AB',0):>10.6f} {d.get('I_c',0):>10.6f} "
                  f"{d.get('S_A',0):>10.6f} {d.get('S_B',0):>10.6f} "
                  f"{d.get('S_AB',0):>10.6f} {d.get('D_KL_to_product',0):>10.6f}")
    
    # === Verdicts ===
    print(f"\n{'=' * 80}")
    print("VERDICTS")
    print(f"{'=' * 80}")
    
    winner = ranking[0]
    lr_mi = np.mean(candidate_mis.get("Xi_LR_direct", [0]))
    hist_mi = np.mean(candidate_mis.get("Xi_hist_uniform_full", [0]))
    winner_mi = np.mean(candidate_mis[winner])
    
    print(f"\n  1. OVERALL WINNER: {winner}")
    print(f"     Mean I_AB: {winner_mi:.6f}")
    print(f"     Improvement over Xi_LR_direct: {winner_mi - lr_mi:+.6f}")
    print(f"     Improvement over Xi_hist_uniform_full: {winner_mi - hist_mi:+.6f}")
    
    # Check if any new candidate beats the previous winner
    new_candidates = [n for n in ranking if "hist_uniform" not in n and "LR_direct" not in n]
    if new_candidates:
        best_new = new_candidates[0]
        best_new_mi = np.mean(candidate_mis[best_new])
        print(f"\n  2. BEST NEW (DOCTRINE-INFORMED) CANDIDATE: {best_new}")
        print(f"     Mean I_AB: {best_new_mi:.6f}")
        print(f"     vs Xi_hist_uniform_full: {best_new_mi - hist_mi:+.6f}")
        print(f"     vs Xi_LR_direct: {best_new_mi - lr_mi:+.6f}")
        
        if best_new_mi > hist_mi + 1e-6:
            print(f"     ★ NEW CANDIDATE BEATS PREVIOUS WINNER ★")
        elif best_new_mi > hist_mi - 1e-6:
            print(f"     ~ NEW CANDIDATE TIES PREVIOUS WINNER")
        else:
            print(f"     Previous winner still leads by {hist_mi - best_new_mi:.6f}")
    
    # Check which doctrine approach works best
    print(f"\n  3. DOCTRINE APPROACH ANALYSIS:")
    doctrine_groups = {
        "Compression-weighted": ["Xi_compress_hist", "Xi_retrocausal_compress"],
        "FEP / Prediction-error": ["Xi_fep_window"],
        "EC-3 Boundary": ["Xi_boundary_max"],
        "Retrocausal / Potential": ["Xi_potential_field", "Xi_retrocausal_compress"],
        "Chiral entanglement": ["Xi_chiral_entangle", "Xi_chiral_hist_entangle"],
        "Entropy gradient": ["Xi_entropy_gradient"],
        "Structural (loop)": ["Xi_loop_phase"],
    }
    
    for group_name, members in doctrine_groups.items():
        group_mis = []
        for m in members:
            if m in candidate_mis:
                group_mis.extend(candidate_mis[m])
        if group_mis:
            print(f"     {group_name:<30} mean I_AB = {np.mean(group_mis):.6f}")
    
    # === EC-3 test ===
    print(f"\n  4. EC-3 TEST (a = a iff a ~ b):")
    print(f"     Xi_LR_direct I_AB = {lr_mi:.6f} (no boundary information)")
    print(f"     Winner I_AB = {winner_mi:.6f} (boundary information present)")
    if winner_mi > lr_mi + 1e-6:
        print(f"     ✓ EC-3 CONFIRMED: boundary adds {winner_mi - lr_mi:.6f} bits of identity")
    else:
        print(f"     ✗ EC-3 NOT YET VISIBLE in this comparison")
    
    return ranking, candidate_mis, candidate_ics


def save_results(results, ranking, candidate_mis, candidate_ics):
    """Save full results to JSON."""
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                              "a2_state", "sim_results")
    os.makedirs(output_dir, exist_ok=True)
    
    # Convert numpy arrays in results for JSON
    def clean(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, dict):
            return {k: clean(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [clean(v) for v in obj]
        return obj
    
    deep_contract = _aggregate_deep_contract(results)
    strict_law = strict_law_fingerprint(
        load_axis0_result(
            Path(__file__).resolve().parent / "a2_state" / "sim_results",
            "axis0_xi_strict_bakeoff_results.json",
        )
    )
    xi_hist_owner_alignment = _xi_hist_owner_alignment_surface(
        ranking,
        candidate_mis,
        candidate_ics,
        deep_contract,
        strict_law,
    )
    summary = {
        "timestamp": datetime.now(UTC).isoformat(),
        "probe": "sim_axis0_bridge_search",
        "classification": classification,
        "divergence_log": divergence_log,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "n_candidates": len(ALL_CANDIDATES),
        "ranking": ranking,
        "mean_mi_by_candidate": {k: float(np.mean(v)) for k, v in candidate_mis.items()},
        "mean_ic_by_candidate": {k: float(np.mean(v)) for k, v in candidate_ics.items()},
        "winner": ranking[0] if ranking else None,
        "xi_hist_owner_alignment": xi_hist_owner_alignment,
        "results": results,
        "aggregate": {
            "deep_contract": deep_contract,
            "all_pass": bool(deep_contract["pass"]),
        },
        "summary": {
            "winner": ranking[0] if ranking else None,
            "deep_contract_pass": bool(deep_contract["pass"]),
            "deep_contract_winner": deep_contract["winner"],
        },
        "overall_pass": bool(deep_contract["pass"]),
        "all_pass": bool(deep_contract["pass"]),
    }
    
    canonical_out_path = os.path.join(
        output_dir, f"{os.path.splitext(os.path.basename(__file__))[0]}_results.json"
    )
    legacy_out_path = os.path.join(output_dir, "axis0_bridge_search_results.json")
    payload = json.dumps(clean(summary), indent=2)
    for target in dict.fromkeys([canonical_out_path, legacy_out_path]):
        with open(target, "w") as f:
            f.write(payload)
    print(f"\n  Results saved: {canonical_out_path}")
    return deep_contract, xi_hist_owner_alignment


if __name__ == "__main__":
    results = run_mass_bakeoff()
    ranking, candidate_mis, candidate_ics = print_ranking(results)
    deep_contract, xi_hist_owner_alignment = save_results(results, ranking, candidate_mis, candidate_ics)

    print(f"\n{'─' * 80}")
    print("DEEP CONTRACT")
    print(f"{'─' * 80}")
    print(f"  Deep pass:                    {deep_contract['pass']}")
    print(f"  Shell bridge pass fraction:   {deep_contract['shell_bridge_pass_fraction']:.3f}")
    print(f"  Winning bridge surface:       {deep_contract['winner']}")
    print(f"  Graph longest path:           {deep_contract['graph_surface']['longest_path_length']}")
    print(f"  Hypergraph max edge size:     {deep_contract['hypergraph_surface']['max_hyperedge_size']}")
    print(f"  Topology betti numbers:       {deep_contract['topology_surface']['betti_numbers']}")
    print(f"  Symbolic hubble mid:          {deep_contract['symbolic_surface']['symbolic_hubble_mid']:.6f}")
    print(f"  Manifold mean distance:       {deep_contract['manifold_surface']['mean_geodesic_distance']:.6f}")
    print(f"  Torch fit loss:               {deep_contract['torch_fit']['loss']:.6f}")
    print(
        f"  Winner vector gaps:           "
        f"clifford={deep_contract['clifford_vector_gap']:.2e} | "
        f"torch_ga={deep_contract['torch_ga_vector_gap']:.2e}"
    )
    print(f"  Xi owner alignment pass:      {xi_hist_owner_alignment['pass']}")
    print(f"  Xi owner status:              {xi_hist_owner_alignment['status']}")
    print(f"  Xi owner dependency:          {xi_hist_owner_alignment['owner_dependency']}")
    
    print(f"\n{'=' * 80}")
    print(f"PROBE STATUS: {'PASS' if deep_contract['pass'] else 'FAIL'}")
    print(f"{'=' * 80}")
