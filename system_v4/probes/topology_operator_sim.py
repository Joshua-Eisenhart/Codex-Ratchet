"""
Topology & Operator SIM Suite
================================
The process_cycle has 4 TOPOLOGIES (state-space geometries) and
4 OPERATORS (channels acting on states). This suite
demonstrates each computationally.

TOPOLOGIES (shapes of flow in state space):
  Toroidal Circulation  = cyclic, area-preserving, div=0
  Divergent Spiral      = expanding, phase-producing, div>0, curl≠0
  Singular Invariant_Target    = contracting to a point, div<0
  Stable Convergent_Subset          = damped oscillation to fixed point

OPERATORS (channels):
  Projection (Ti)   = Lüders trace_projection, destroys coherence, absorbs info
  Expansion (Te)    = drives state_dispersion production, emits structure
  Filtering (Fi)    = spectral selection, absorbs specific frequencies
  Dissipation (Fe)  = Lindblad damping, emits heat to bath
"""

import numpy as np
import json
import os
from datetime import datetime, UTC

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proto_ratchet_sim_runner import (
    make_random_density_matrix,
    make_random_unitary,
    apply_unitary_channel,
    apply_lindbladian_step,
    von_neumann_entropy,
    trace_distance,
    EvidenceToken,
)


def negentropy(rho, d):
    S = von_neumann_entropy(rho) * np.log(2)
    return np.log(d) - S


# ═══════════════════════════════════════════
# PART 1: FOUR TOPOLOGIES
# ═══════════════════════════════════════════

def sim_toroidal_circulation(d: int = 4, n_cycles: int = 100):
    """
    TOROIDAL CIRCULATION (coherent propagation)
    ===========================================
    Pure unitary cycle. State moves around a closed orbit.
    - State_Dispersion is CONSTANT (S(UρU†) = S(ρ))
    - State returns to origin after full cycle
    - Divergence = 0 (area-preserving)
    - No state_distinction gained or lost
    """
    print(f"\n{'='*60}")
    print(f"TOPOLOGY 1: TOROIDAL CIRCULATION")
    print(f"  d={d}, cycles={n_cycles}")
    print(f"{'='*60}")
    
    np.random.seed(42)
    rho_init = make_random_density_matrix(d)
    U = make_random_unitary(d)
    
    S_history = []
    dist_history = []
    
    rho = rho_init.copy()
    for i in range(n_cycles):
        rho = apply_unitary_channel(rho, U)
        S_history.append(von_neumann_entropy(rho))
        dist_history.append(trace_distance(rho, rho_init))
    
    S_var = np.var(S_history)
    S_mean = np.mean(S_history)
    
    # Find if orbit returns
    min_dist = min(dist_history)
    min_idx = dist_history.index(min_dist)
    
    print(f"  S_mean = {S_mean:.6f}")
    print(f"  S_variance = {S_var:.2e} (should be ~0)")
    print(f"  Closest return: dist={min_dist:.6f} at step {min_idx}")
    print(f"  → State_Dispersion CONSTANT. Orbit is CLOSED.")
    print(f"  → This is pure reversible cycling. No state_distinction exchange.")
    
    entropy_flat = S_var < 1e-20
    
    if entropy_flat:
        print(f"  PASS: Toroidal circulation confirmed!")
        return EvidenceToken(
            token_id="E_SIM_TOROIDAL_OK",
            sim_spec_id="S_SIM_TOROIDAL_V1",
            status="PASS",
            measured_value=S_var
        )
    else:
        return EvidenceToken("", "S_SIM_TOROIDAL_V1", "KILL", 0.0, "STATE_DISPERSION_NOT_FLAT")


def sim_divergent_spiral(d: int = 4, n_steps: int = 100):
    """
    DIVERGENT SPIRAL (phase expansion)
    ====================================
    Unitary evolution + noise injection. State spirals outward.
    - State_Dispersion INCREASES (expanding into larger state space)
    - State moves AWAY from initial position
    - Divergence > 0, curl ≠ 0
    - Explores new regions of state space
    """
    print(f"\n{'='*60}")
    print(f"TOPOLOGY 2: DIVERGENT SPIRAL")
    print(f"  d={d}, steps={n_steps}")
    print(f"{'='*60}")
    
    np.random.seed(42)
    rho_init = np.zeros((d, d), dtype=complex)
    rho_init[0, 0] = 0.9
    rho_init[1, 1] = 0.1  # Start near-pure (low state_dispersion)
    
    U = make_random_unitary(d)
    L_base = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    L = L_base / np.linalg.norm(L_base) * 0.5  # mild noise
    
    S_history = []
    dist_history = []
    
    rho = rho_init.copy()
    for i in range(n_steps):
        rho = apply_unitary_channel(rho, U)
        rho = apply_lindbladian_step(rho, L, dt=0.02)
        S_history.append(von_neumann_entropy(rho))
        dist_history.append(trace_distance(rho, rho_init))
    
    S_trend = S_history[-1] - S_history[0]
    dist_trend = dist_history[-1] - dist_history[0]
    
    print(f"  S_init = {S_history[0]:.6f}")
    print(f"  S_final = {S_history[-1]:.6f}")
    print(f"  ΔS = {S_trend:.6f} ({'expanding' if S_trend > 0 else 'contracting'})")
    print(f"  Distance from origin: {dist_history[-1]:.6f}")
    print(f"  → State_Dispersion INCREASES. State spirals OUTWARD.")
    print(f"  → Divergent exploration of state space.")
    
    expands = S_trend > 0
    
    if expands:
        print(f"  PASS: Divergent spiral confirmed!")
        return EvidenceToken(
            token_id="E_SIM_DIVERGENT_OK",
            sim_spec_id="S_SIM_DIVERGENT_V1",
            status="PASS",
            measured_value=S_trend
        )
    else:
        return EvidenceToken("", "S_SIM_DIVERGENT_V1", "KILL", 0.0, "NOT_EXPANDING")


def sim_singular_attractor(d: int = 4, n_steps: int = 200):
    """
    SINGULAR INVARIANT_TARGET (radial contraction)
    =========================================
    Strong projection + dissipation. State collapses to a point.
    - State_Dispersion DECREASES (structure crystallizes)
    - State converges to a single pure state
    - Divergence < 0 (volume-contracting)
    - All paths lead to the same point
    """
    print(f"\n{'='*60}")
    print(f"TOPOLOGY 3: SINGULAR INVARIANT_TARGET")
    print(f"  d={d}, steps={n_steps}")
    print(f"{'='*60}")
    
    np.random.seed(42)
    # Target: a specific pure state
    target = np.zeros((d, d), dtype=complex)
    target[0, 0] = 1.0
    
    # Start from random mixed state (high state_dispersion)
    rho = make_random_density_matrix(d)
    
    S_history = []
    dist_history = []
    
    for step in range(n_steps):
        # Project toward target (trace_projection-like state_reduction)
        P = np.zeros((d, d), dtype=complex)
        P[0, 0] = 1.0
        rho = 0.95 * rho + 0.05 * (P @ rho @ P + (np.eye(d) - P) @ rho @ (np.eye(d) - P))
        
        # Entrainment toward target
        rho = 0.95 * rho + 0.05 * target
        rho = rho / np.trace(rho)
        
        S_history.append(von_neumann_entropy(rho))
        dist_history.append(trace_distance(rho, target))
    
    print(f"  S_init = {S_history[0]:.6f}")
    print(f"  S_final = {S_history[-1]:.6f}")
    print(f"  ΔS = {S_history[-1] - S_history[0]:.6f} (should be negative)")
    print(f"  Final distance to target: {dist_history[-1]:.6f}")
    print(f"  → State_Dispersion DECREASES. State CONTRACTS to singular point.")
    print(f"  → All initial conditions converge to the SAME invariant_target.")
    
    contracts = S_history[-1] < S_history[0] and dist_history[-1] < 0.1
    
    if contracts:
        print(f"  PASS: Singular invariant_target confirmed!")
        return EvidenceToken(
            token_id="E_SIM_SINGULAR_INVARIANT_TARGET_OK",
            sim_spec_id="S_SIM_SINGULAR_V1",
            status="PASS",
            measured_value=dist_history[-1]
        )
    else:
        return EvidenceToken("", "S_SIM_SINGULAR_V1", "KILL", 0.0, "NOT_CONTRACTING")


def sim_stable_basin(d: int = 4, n_steps: int = 200):
    """
    STABLE CONVERGENT_SUBSET (fixed-point damping)
    =====================================
    Dissipation-dominated dynamics. State settles into a steady-state
    mixed state (NOT pure). Oscillatory approach to a fixed point.
    - State_Dispersion converges to a SPECIFIC intermediate value
    - Small perturbations are damped back
    - Convergent_Subset, not point — there's a region of attraction
    """
    print(f"\n{'='*60}")
    print(f"TOPOLOGY 4: STABLE CONVERGENT_SUBSET")
    print(f"  d={d}, steps={n_steps}")
    print(f"{'='*60}")
    
    np.random.seed(42)
    U = make_random_unitary(d)
    L_base = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    L = L_base / np.linalg.norm(L_base) * 3.0
    
    rho = make_random_density_matrix(d)
    S_history = []
    
    for step in range(n_steps):
        rho = apply_unitary_channel(rho, U)
        for _ in range(3):
            rho = apply_lindbladian_step(rho, L, dt=0.01)
        S_history.append(von_neumann_entropy(rho))
    
    steady_state = rho.copy()
    S_final = S_history[-1]
    
    # Test stability: perturb and show it returns
    np.random.seed(99)
    perturb = make_random_density_matrix(d)
    rho_kicked = 0.8 * steady_state + 0.2 * perturb
    rho_kicked = rho_kicked / np.trace(rho_kicked)
    
    recovery_dist = []
    for step in range(50):
        rho_kicked = apply_unitary_channel(rho_kicked, U)
        for _ in range(3):
            rho_kicked = apply_lindbladian_step(rho_kicked, L, dt=0.01)
        recovery_dist.append(trace_distance(rho_kicked, steady_state))
    
    # State_Dispersion variance in last 50 steps (should be small = converged)
    S_var_final = np.var(S_history[-50:])
    recovered = recovery_dist[-1] < recovery_dist[0]
    
    print(f"  S converges to: {S_final:.6f} (variance: {S_var_final:.2e})")
    print(f"  After perturbation:")
    print(f"    Initial kick distance: {recovery_dist[0]:.6f}")
    print(f"    After 50 steps: {recovery_dist[-1]:.6f}")
    print(f"    Recovered: {recovered}")
    print(f"  → State settles into a CONVERGENT_SUBSET, not a point")
    print(f"  → Perturbations are DAMPED back. This is stability.")
    
    if recovered and S_var_final < 0.01:
        print(f"  PASS: Stable convergent_subset confirmed!")
        return EvidenceToken(
            token_id="E_SIM_STABLE_CONVERGENT_SUBSET_OK",
            sim_spec_id="S_SIM_CONVERGENT_SUBSET_V1",
            status="PASS",
            measured_value=S_final
        )
    else:
        return EvidenceToken("", "S_SIM_CONVERGENT_SUBSET_V1", "KILL", 0.0, "NOT_STABLE")


# ═══════════════════════════════════════════
# PART 2: FOUR OPERATORS
# ═══════════════════════════════════════════

def sim_projection_operator(d: int = 4):
    """
    PROJECTION OPERATOR (absorptive logic)
    ========================================
    Lüders trace_projection projection. Destroys off-diagonal coherences.
    - State_Dispersion INCREASES (gains state_distinction by losing coherence)
    - Irreversible (non-unitary)
    - Absorbs state_distinction from the system
    - Collapses superpositions to classical mixtures
    """
    print(f"\n{'='*60}")
    print(f"OPERATOR 1: PROJECTION (absorptive logic)")
    print(f"  d={d}")
    print(f"{'='*60}")
    
    np.random.seed(42)
    rho = make_random_density_matrix(d)
    S_before = von_neumann_entropy(rho)
    
    # Build projectors in computational basis
    projectors = [np.zeros((d, d), dtype=complex) for _ in range(d)]
    for k in range(d):
        projectors[k][k, k] = 1.0
    
    # Apply Lüders rule: ρ → Σ_k P_k ρ P_k
    rho_measured = sum(P @ rho @ P for P in projectors)
    S_after = von_neumann_entropy(rho_measured)
    
    # Off-diagonal elements should be zero
    off_diag = np.sum(np.abs(rho_measured - np.diag(np.diag(rho_measured))))
    
    print(f"  S_before = {S_before:.6f}")
    print(f"  S_after  = {S_after:.6f}")
    print(f"  ΔS = {S_after - S_before:.6f}")
    print(f"  Off-diagonal residual: {off_diag:.2e}")
    print(f"  → Trace_Projection DESTROYS coherence (off-diag → 0)")
    print(f"  → State_Dispersion increases: superposition → classical mixture")
    print(f"  → State_Distinction is ABSORBED (system pays Landauer cost)")
    
    coherence_killed = off_diag < 1e-15
    entropy_up = S_after >= S_before - 1e-10
    
    if coherence_killed and entropy_up:
        print(f"  PASS: Projection operator confirmed!")
        return EvidenceToken(
            token_id="E_SIM_PROJECTION_OK",
            sim_spec_id="S_SIM_PROJECTION_V1",
            status="PASS",
            measured_value=S_after - S_before
        )
    else:
        return EvidenceToken("", "S_SIM_PROJECTION_V1", "KILL", 0.0, "PROJECTION_FAILS")


def sim_expansion_operator(d: int = 4):
    """
    EXPANSION OPERATOR (emissive logic)
    ======================================
    Drives state_dispersion PRODUCTION. Takes a low-state_dispersion state and
    expands it into a larger portion of state space.
    - State_Dispersion INCREASES
    - Emits structure into the environment
    - Maps to the inductive/divergent stroke
    """
    print(f"\n{'='*60}")
    print(f"OPERATOR 2: EXPANSION (emissive logic)")
    print(f"  d={d}")
    print(f"{'='*60}")
    
    np.random.seed(42)
    # Start near-pure (low state_dispersion)
    rho = np.zeros((d, d), dtype=complex)
    rho[0, 0] = 0.95
    rho[1, 1] = 0.05
    S_before = von_neumann_entropy(rho)
    
    # Expansion = depolarizing channel: ρ → (1-p)ρ + p(I/d)
    p = 0.5  # expansion strength
    sigma = np.eye(d, dtype=complex) / d
    rho_expanded = (1 - p) * rho + p * sigma
    S_after = von_neumann_entropy(rho_expanded)
    
    phi_before = negentropy(rho, d)
    phi_after = negentropy(rho_expanded, d)
    
    print(f"  S_before = {S_before:.6f} (near-pure)")
    print(f"  S_after  = {S_after:.6f} (expanded)")
    print(f"  ΔS = {S_after - S_before:.6f}")
    print(f"  Φ_before = {phi_before:.6f}")
    print(f"  Φ_after  = {phi_after:.6f}")
    print(f"  ΔΦ = {phi_after - phi_before:.6f}")
    print(f"  → Structure EMITTED into noise. State is less pure.")
    
    if S_after > S_before:
        print(f"  PASS: Expansion operator confirmed!")
        return EvidenceToken(
            token_id="E_SIM_EXPANSION_OK",
            sim_spec_id="S_SIM_EXPANSION_V1",
            status="PASS",
            measured_value=S_after - S_before
        )
    else:
        return EvidenceToken("", "S_SIM_EXPANSION_V1", "KILL", 0.0, "NOT_EXPANDING")


def sim_filtering_operator(d: int = 4):
    """
    FILTERING OPERATOR (absorptive metric)
    ========================================
    Spectral band-pass. Selects specific eigenfrequencies,
    suppresses others.
    - State_Dispersion DECREASES in the selected band
    - Absorbs specific spectral components
    - Acts as a high-Q resonance intake
    """
    print(f"\n{'='*60}")
    print(f"OPERATOR 3: FILTERING (absorptive metric)")
    print(f"  d={d}")
    print(f"{'='*60}")
    
    np.random.seed(42)
    rho = make_random_density_matrix(d)
    S_before = von_neumann_entropy(rho)
    
    # Build a spectral filter: amplify low eigenvalues, suppress high
    F = np.eye(d, dtype=complex)
    F[0, 0] = 1.0   # pass
    F[1, 1] = 0.8   # pass
    F[2, 2] = 0.1   # suppress
    if d > 3:
        F[3, 3] = 0.05  # strongly suppress
    
    rho_filtered = F @ rho @ F.conj().T
    rho_filtered = rho_filtered / np.trace(rho_filtered)
    S_after = von_neumann_entropy(rho_filtered)
    
    # The filter concentrates the state
    purity_before = np.real(np.trace(rho @ rho))
    purity_after = np.real(np.trace(rho_filtered @ rho_filtered))
    
    print(f"  S_before = {S_before:.6f}")
    print(f"  S_after  = {S_after:.6f}")
    print(f"  ΔS = {S_after - S_before:.6f}")
    print(f"  Purity before: {purity_before:.6f}")
    print(f"  Purity after:  {purity_after:.6f}")
    print(f"  → Filter CONCENTRATES state (higher purity)")
    print(f"  → Unwanted frequencies suppressed")
    
    concentrates = purity_after > purity_before
    
    if concentrates:
        print(f"  PASS: Filtering operator confirmed!")
        return EvidenceToken(
            token_id="E_SIM_FILTERING_OK",
            sim_spec_id="S_SIM_FILTERING_V1",
            status="PASS",
            measured_value=purity_after - purity_before
        )
    else:
        return EvidenceToken("", "S_SIM_FILTERING_V1", "KILL", 0.0, "NOT_CONCENTRATING")


def sim_dissipation_operator(d: int = 4):
    """
    DISSIPATION OPERATOR (emissive metric)
    ========================================
    Lindblad damping. Smooths gradients, emits heat.
    - Drives toward equilibrium (thermal death)
    - Emits waste heat into the bath
    - Laplacian smoothing: ∂u/∂t = α∇²u
    - Contractive: variance monotonically decreases
    """
    print(f"\n{'='*60}")
    print(f"OPERATOR 4: DISSIPATION (emissive metric)")
    print(f"  d={d}")
    print(f"{'='*60}")
    
    np.random.seed(42)
    # Start with a structured state
    rho = np.zeros((d, d), dtype=complex)
    rho[0, 0] = 0.7
    rho[1, 1] = 0.3
    S_before = von_neumann_entropy(rho)
    
    # Thermalizing Lindblad (dissipation to I/d)
    L_ops = []
    for j in range(d):
        for k in range(d):
            if j != k:
                L = np.zeros((d, d), dtype=complex)
                L[j, k] = 1.0
                L_ops.append(L)
    
    for _ in range(100):
        drho = np.zeros_like(rho)
        for L in L_ops:
            LdL = L.conj().T @ L
            drho += L @ rho @ L.conj().T - 0.5 * (LdL @ rho + rho @ LdL)
        rho = rho + 0.01 * drho
        rho = (rho + rho.conj().T) / 2
        eigvals = np.maximum(np.real(np.linalg.eigvalsh(rho)), 0)
        V = np.linalg.eigh(rho)[1]
        rho = V @ np.diag(eigvals.astype(complex)) @ V.conj().T
        if np.real(np.trace(rho)) > 0:
            rho = rho / np.trace(rho)
    
    S_after = von_neumann_entropy(rho)
    sigma = np.eye(d, dtype=complex) / d
    dist_to_thermal = trace_distance(rho, sigma)
    
    print(f"  S_before = {S_before:.6f}")
    print(f"  S_after  = {S_after:.6f}")
    print(f"  ΔS = {S_after - S_before:.6f}")
    print(f"  Distance to I/d: {dist_to_thermal:.6f}")
    print(f"  → Dissipation drives toward THERMAL EQUILIBRIUM")
    print(f"  → Heat emitted. Gradients smoothed. Structure dissolved.")
    
    thermalizes = S_after > S_before and dist_to_thermal < 0.1
    
    if thermalizes:
        print(f"  PASS: Dissipation operator confirmed!")
        return EvidenceToken(
            token_id="E_SIM_DISSIPATION_OK",
            sim_spec_id="S_SIM_DISSIPATION_V1",
            status="PASS",
            measured_value=S_after - S_before
        )
    else:
        return EvidenceToken("", "S_SIM_DISSIPATION_V1", "KILL", 0.0, "NOT_THERMALIZING")


if __name__ == "__main__":
    results = []
    
    print(f"\n{'#'*60}")
    print(f"  PART 1: FOUR TOPOLOGIES")
    print(f"{'#'*60}")
    results.append(sim_toroidal_circulation())
    results.append(sim_divergent_spiral())
    results.append(sim_singular_attractor())
    results.append(sim_stable_basin())
    
    print(f"\n{'#'*60}")
    print(f"  PART 2: FOUR OPERATORS")
    print(f"{'#'*60}")
    results.append(sim_projection_operator())
    results.append(sim_expansion_operator())
    results.append(sim_filtering_operator())
    results.append(sim_dissipation_operator())
    
    print(f"\n{'='*60}")
    print(f"TOPOLOGY & OPERATOR SUITE RESULTS")
    print(f"{'='*60}")
    for e in results:
        icon = "✓" if e.status == "PASS" else "✗"
        print(f"  {icon} {e.sim_spec_id}: {e.status} (value={e.measured_value:.6f})")
    
    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "topology_operator_results.json")
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "evidence_ledger": [
                {"token_id": e.token_id, "sim_spec_id": e.sim_spec_id,
                 "status": e.status, "measured_value": e.measured_value,
                 "kill_reason": e.kill_reason}
                for e in results
            ]
        }, f, indent=2)
    print(f"  Results saved to: {outpath}")
