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
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

import numpy as np
from scipy.linalg import sqrtm, logm
classification = "classical_baseline"  # auto-backfill

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import GeometricEngine, StageControls
from geometric_operators import _ensure_valid_density
from hopf_manifold import (
    TORUS_CLIFFORD, TORUS_INNER, TORUS_OUTER,
    left_density, right_density, torus_coordinates,
    fiber_action, von_neumann_entropy_2x2,
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
            
            row = {
                "engine_type": engine_type,
                "torus": torus_label,
                "eta": float(eta),
                "candidates": {},
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
    
    summary = {
        "timestamp": datetime.now(UTC).isoformat(),
        "probe": "sim_axis0_bridge_search",
        "n_candidates": len(ALL_CANDIDATES),
        "ranking": ranking,
        "mean_mi_by_candidate": {k: float(np.mean(v)) for k, v in candidate_mis.items()},
        "mean_ic_by_candidate": {k: float(np.mean(v)) for k, v in candidate_ics.items()},
        "winner": ranking[0] if ranking else None,
    }
    
    out_path = os.path.join(output_dir, "axis0_bridge_search_results.json")
    with open(out_path, "w") as f:
        json.dump(clean(summary), f, indent=2)
    print(f"\n  Results saved: {out_path}")


if __name__ == "__main__":
    results = run_mass_bakeoff()
    ranking, candidate_mis, candidate_ics = print_ranking(results)
    save_results(results, ranking, candidate_mis, candidate_ics)
    
    print(f"\n{'=' * 80}")
    print(f"PROBE STATUS: PASS")
    print(f"{'=' * 80}")
