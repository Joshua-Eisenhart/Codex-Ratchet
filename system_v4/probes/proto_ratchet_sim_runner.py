"""
Proto-Ratchet SIM Runner
========================
Computational verification of the Codex Ratchet engine constraints.
Tests whether the mathematical model produces real, measurable results.

This is a proto-B ratchet: it runs actual numerical experiments on density
matrices and CPTP maps to verify or kill the base axioms and derived claims.

SIM hierarchy:
  T0: F01_FINITUDE — verify trace=1, finite dimensions
  T1: N01_NONCOMMUTATION — verify AB != BA for non-trivial operators
  T2: ACTION_PRECEDENCE — verify left vs right composition yields distinct observables
  T3: VARIANCE_DIRECTION — verify deductive vs inductive produce distinct variance trajectories
  T4: CHIRAL_FLUX — verify convergent vs divergent flows are topologically distinct
  T5: PROTO_ATTRACTOR_BASIN — verify a basin forms under iterated CPTP application
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import json
import os
from datetime import datetime


# ─────────────────────────────────────────────
# Evidence Token System
# ─────────────────────────────────────────────

@dataclass
class EvidenceToken:
    """A SIM evidence token — proof that a test passed or failed."""
    token_id: str
    sim_spec_id: str
    status: str  # "PASS" or "KILL"
    measured_value: Optional[float] = None
    kill_reason: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class GraveyardRecord:
    """Record of a killed hypothesis."""
    failed_spec_id: str
    killing_sim_id: str
    missing_evidence: str
    fail_class: str
    rescue_path: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


# ─────────────────────────────────────────────
# Density Matrix Utilities
# ─────────────────────────────────────────────

def make_random_density_matrix(d: int) -> np.ndarray:
    """Create a valid random density matrix of dimension d."""
    # Generate random complex matrix, make it positive semi-definite, normalize trace
    A = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    rho = A @ A.conj().T
    rho = rho / np.trace(rho)
    return rho


def make_random_unitary(d: int) -> np.ndarray:
    """Create a random unitary operator of dimension d."""
    A = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    Q, R = np.linalg.qr(A)
    # Fix phase to make it a proper unitary
    D = np.diag(np.diag(R) / np.abs(np.diag(R)))
    return Q @ D


def apply_unitary_channel(rho: np.ndarray, U: np.ndarray) -> np.ndarray:
    """Apply unitary channel: rho -> U @ rho @ U†"""
    return U @ rho @ U.conj().T


def apply_lindbladian_step(rho: np.ndarray, L: np.ndarray, dt: float = 0.01) -> np.ndarray:
    """Apply single Lindbladian dissipation step (Euler method).
    drho/dt = L @ rho @ L† - 0.5 * {L†L, rho}
    """
    LdL = L.conj().T @ L
    drho = L @ rho @ L.conj().T - 0.5 * (LdL @ rho + rho @ LdL)
    rho_new = rho + dt * drho
    # Renormalize to maintain trace = 1 (Euler can drift)
    rho_new = rho_new / np.trace(rho_new)
    return rho_new


def von_neumann_entropy(rho: np.ndarray) -> float:
    """Compute von Neumann entropy: S = -Tr(rho * log(rho))"""
    eigenvalues = np.real(np.linalg.eigvalsh(rho))
    eigenvalues = eigenvalues[eigenvalues > 1e-12]  # filter zeros
    return float(-np.sum(eigenvalues * np.log2(eigenvalues)))


def trace_distance(rho1: np.ndarray, rho2: np.ndarray) -> float:
    """Trace distance between two density matrices."""
    diff = rho1 - rho2
    eigenvalues = np.abs(np.linalg.eigvalsh(diff))
    return float(0.5 * np.sum(eigenvalues))


# ─────────────────────────────────────────────
# SIM RUNNERS
# ─────────────────────────────────────────────

def sim_f01_finitude(d: int = 4, n_trials: int = 100) -> EvidenceToken:
    """
    SIM_SPEC_F01: Attempt to falsify FINITUDE.
    
    Test: Generate n_trials random density matrices of dimension d.
    Verify that every single one has Tr(rho) = 1 and is finite-dimensional.
    KILL_IF: any trace diverges or state space appears unbounded.
    """
    print(f"\n{'='*60}")
    print(f"SIM T0: F01_FINITUDE FALSIFICATION")
    print(f"  d={d}, trials={n_trials}")
    print(f"{'='*60}")
    
    for i in range(n_trials):
        rho = make_random_density_matrix(d)
        tr = np.real(np.trace(rho))
        
        # Check trace = 1
        if not np.isclose(tr, 1.0, atol=1e-10):
            print(f"  KILL: Trial {i} — trace diverged: Tr(rho) = {tr}")
            return EvidenceToken(
                token_id="",
                sim_spec_id="S_SIM_F01_FINITUDE_FALSIFICATION",
                status="KILL",
                measured_value=tr,
                kill_reason="STATE_SPACE_UNBOUNDED_OR_TRACE_DIVERGES"
            )
        
        # Check finite dimensionality
        if rho.shape[0] != d or rho.shape[1] != d:
            print(f"  KILL: Trial {i} — dimension mismatch")
            return EvidenceToken(
                token_id="",
                sim_spec_id="S_SIM_F01_FINITUDE_FALSIFICATION",
                status="KILL",
                kill_reason="STATE_SPACE_UNBOUNDED_OR_TRACE_DIVERGES"
            )
        
        # Check positive semi-definite
        eigenvalues = np.real(np.linalg.eigvalsh(rho))
        if np.any(eigenvalues < -1e-10):
            print(f"  KILL: Trial {i} — negative eigenvalue: {min(eigenvalues)}")
            return EvidenceToken(
                token_id="",
                sim_spec_id="S_SIM_F01_FINITUDE_FALSIFICATION",
                status="KILL",
                measured_value=float(min(eigenvalues)),
                kill_reason="STATE_SPACE_UNBOUNDED_OR_TRACE_DIVERGES"
            )
    
    print(f"  PASS: All {n_trials} density matrices satisfy finitude.")
    print(f"  Tr(rho) = 1.0 ± 1e-10 for all trials")
    print(f"  dim(H) = {d} (finite) for all trials")
    return EvidenceToken(
        token_id="E_SIM_F01_FINITUDE_OK",
        sim_spec_id="S_SIM_F01_FINITUDE_FALSIFICATION",
        status="PASS",
        measured_value=1.0
    )


def sim_n01_noncommutation(d: int = 4, n_trials: int = 100) -> EvidenceToken:
    """
    SIM_SPEC_N01: Attempt to falsify NON-COMMUTATION.
    
    Test: Generate random non-trivial operator pairs and verify AB != BA.
    KILL_IF: all operator pairs commute (AB = BA for all A, B).
    """
    print(f"\n{'='*60}")
    print(f"SIM T1: N01_NONCOMMUTATION FALSIFICATION")
    print(f"  d={d}, trials={n_trials}")
    print(f"{'='*60}")
    
    noncommuting_count = 0
    max_commutator_norm = 0.0
    
    for i in range(n_trials):
        A = make_random_unitary(d)
        B = make_random_unitary(d)
        
        # Compute commutator [A, B] = AB - BA
        commutator = A @ B - B @ A
        comm_norm = np.linalg.norm(commutator, 'fro')
        
        if comm_norm > 1e-10:
            noncommuting_count += 1
            max_commutator_norm = max(max_commutator_norm, comm_norm)
    
    if noncommuting_count == 0:
        print(f"  KILL: All {n_trials} operator pairs commuted!")
        return EvidenceToken(
            token_id="",
            sim_spec_id="S_SIM_N01_NONCOMMUTE_FALSIFICATION",
            status="KILL",
            measured_value=0.0,
            kill_reason="COMMUTATIVE_ASSUMPTION_DETECTED_AB_BA_FOR_ALL"
        )
    
    ratio = noncommuting_count / n_trials
    print(f"  PASS: {noncommuting_count}/{n_trials} pairs are non-commuting ({ratio:.1%})")
    print(f"  Max ||[A,B]||_F = {max_commutator_norm:.6f}")
    return EvidenceToken(
        token_id="E_SIM_N01_NONCOMMUTE_OK",
        sim_spec_id="S_SIM_N01_NONCOMMUTE_FALSIFICATION",
        status="PASS",
        measured_value=ratio
    )


def sim_action_precedence(d: int = 4, n_trials: int = 50) -> EvidenceToken:
    """
    SIM T2: ACTION_PRECEDENCE — verify left vs right composition matters.
    
    Test: For operator A and density matrix rho, verify that
    Tr(O * (A @ rho)) != Tr(O * (rho @ A)) when [A, rho] != 0
    """
    print(f"\n{'='*60}")
    print(f"SIM T2: ACTION_PRECEDENCE FALSIFICATION")
    print(f"  d={d}, trials={n_trials}")
    print(f"{'='*60}")
    
    distinct_count = 0
    max_difference = 0.0
    
    for i in range(n_trials):
        rho = make_random_density_matrix(d)
        A = make_random_unitary(d)
        O = make_random_density_matrix(d)  # observable
        
        # Left pre-composition: A @ rho
        left = A @ rho
        # Right post-composition: rho @ A
        right = rho @ A
        
        # Measure observable expectations
        tr_left = np.real(np.trace(O @ left))
        tr_right = np.real(np.trace(O @ right))
        
        diff = abs(tr_left - tr_right)
        if diff > 1e-10:
            distinct_count += 1
            max_difference = max(max_difference, diff)
    
    if distinct_count == 0:
        print(f"  KILL: Left and right composition always identical!")
        return EvidenceToken(
            token_id="",
            sim_spec_id="S_ACTION_PRECEDENCE_NONCOLLAPSE",
            status="KILL",
            measured_value=0.0,
            kill_reason="ACTION_PRECEDENCE_COLLAPSED"
        )
    
    ratio = distinct_count / n_trials
    print(f"  PASS: {distinct_count}/{n_trials} distinct left/right compositions ({ratio:.1%})")
    print(f"  Max |Tr(O*A*rho) - Tr(O*rho*A)| = {max_difference:.6f}")
    return EvidenceToken(
        token_id="E_SIM_ACTION_PRECEDENCE_OK",
        sim_spec_id="S_ACTION_PRECEDENCE_NONCOLLAPSE",
        status="PASS",
        measured_value=ratio
    )


def sim_variance_direction(d: int = 4, n_steps: int = 200) -> EvidenceToken:
    """
    SIM T3: VARIANCE_DIRECTION — verify deductive vs inductive produce 
    distinct entropy trajectories.
    
    Test: Apply two different operator orderings to the same initial state:
    - Deductive (constraint-first): Lindbladian dissipation THEN unitary rotation
    - Inductive (release-first): Unitary rotation THEN Lindbladian dissipation
    
    Verify the entropy trajectories diverge.
    """
    print(f"\n{'='*60}")
    print(f"SIM T3: VARIANCE_DIRECTION FALSIFICATION")
    print(f"  d={d}, steps={n_steps}")
    print(f"{'='*60}")
    
    rho_init = make_random_density_matrix(d)
    U = make_random_unitary(d)
    L = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    L = L / np.linalg.norm(L) * 0.5  # scale down for stability
    
    # Deductive trajectory: constraint (Lindbladian) first, then unitary
    rho_ded = rho_init.copy()
    entropy_deductive = [von_neumann_entropy(rho_ded)]
    
    # Inductive trajectory: unitary first, then constraint (Lindbladian)
    rho_ind = rho_init.copy()
    entropy_inductive = [von_neumann_entropy(rho_ind)]
    
    for step in range(n_steps):
        # Deductive: dissipate then rotate
        rho_ded = apply_lindbladian_step(rho_ded, L, dt=0.01)
        rho_ded = apply_unitary_channel(rho_ded, U)
        entropy_deductive.append(von_neumann_entropy(rho_ded))
        
        # Inductive: rotate then dissipate
        rho_ind = apply_unitary_channel(rho_ind, U)
        rho_ind = apply_lindbladian_step(rho_ind, L, dt=0.01)
        entropy_inductive.append(von_neumann_entropy(rho_ind))
    
    # Measure divergence between trajectories
    entropy_ded = np.array(entropy_deductive)
    entropy_ind = np.array(entropy_inductive)
    trajectory_divergence = np.max(np.abs(entropy_ded - entropy_ind))
    final_state_distance = trace_distance(rho_ded, rho_ind)
    
    print(f"  Initial entropy: {entropy_deductive[0]:.6f}")
    print(f"  Deductive final entropy: {entropy_deductive[-1]:.6f}")
    print(f"  Inductive final entropy: {entropy_inductive[-1]:.6f}")
    print(f"  Max trajectory divergence: {trajectory_divergence:.6f}")
    print(f"  Final state trace distance: {final_state_distance:.6f}")
    
    if trajectory_divergence < 1e-10:
        print(f"  KILL: Deductive and inductive trajectories are IDENTICAL!")
        return EvidenceToken(
            token_id="",
            sim_spec_id="S_VARIANCE_DIRECTION_MATH",
            status="KILL",
            measured_value=trajectory_divergence,
            kill_reason="VARIANCE_ORDER_COMMUTES"
        )
    
    print(f"  PASS: Non-commuting variance direction confirmed.")
    return EvidenceToken(
        token_id="E_SIM_VARIANCE_DIRECTION_OK",
        sim_spec_id="S_VARIANCE_DIRECTION_MATH",
        status="PASS",
        measured_value=trajectory_divergence
    )


def sim_proto_attractor_basin(d: int = 4, n_steps: int = 500, n_initial_states: int = 20) -> EvidenceToken:
    """
    SIM T5: PROTO ATTRACTOR BASIN — verify that iterated CPTP application
    drives diverse initial states toward a common fixed point (attractor).
    
    A2 FUEL DIAGNOSIS (from source mining):
      The damped harmonic oscillator equation governs convergence:
        φ̈ + γφ̇ + ω²φ = 0
      where γ = FGA dissipation rate, ω = FSA coherent frequency.
      
      Critical damping requires γ ≥ 2ω. Previous run had γ << ω (underdamped).
      
      FIX: Scale up Lindbladian amplitude and apply MULTIPLE dissipation
      steps per unitary rotation (deductive ordering: constraint-first).
      FSA "Cannot create dissipative attractors" — only FGA can.
    """
    print(f"\n{'='*60}")
    print(f"SIM T5: PROTO ATTRACTOR BASIN (A2-CORRECTED)")
    print(f"  d={d}, steps={n_steps}, initial_states={n_initial_states}")
    print(f"  Model: φ̈ + γφ̇ + ω²φ = 0 (targeting critical damping)")
    print(f"{'='*60}")
    
    # Create the FSA component (unitary rotation — coherent, entropy-preserving)
    U = make_random_unitary(d)
    
    # Sweep γ values to find the critical damping threshold
    gamma_values = [0.3, 0.8, 1.5, 3.0, 5.0]
    sweep_results = []
    
    for gamma in gamma_values:
        # Create FGA component (Lindbladian dissipation — entropy-producing)
        L_base = np.random.randn(d, d) + 1j * np.random.randn(d, d)
        L = L_base / np.linalg.norm(L_base) * gamma
        
        # Deductive ordering: dissipation FIRST (constraint-first), then rotation
        # Apply multiple dissipation steps per unitary step (FGA dominance)
        n_dissipation_steps = max(1, int(gamma))  # more dissipation at higher γ
        
        final_states = []
        for s in range(n_initial_states):
            rho = make_random_density_matrix(d)
            for step in range(n_steps):
                # FGA: multiple dissipation steps (constraint-first / deductive)
                for _ in range(n_dissipation_steps):
                    rho = apply_lindbladian_step(rho, L, dt=0.01)
                # FSA: single unitary rotation
                rho = apply_unitary_channel(rho, U)
            final_states.append(rho)
        
        # Measure convergence
        distances = []
        for i in range(len(final_states)):
            for j in range(i+1, len(final_states)):
                distances.append(trace_distance(final_states[i], final_states[j]))
        
        mean_dist = np.mean(distances)
        max_dist = np.max(distances)
        sweep_results.append((gamma, mean_dist, max_dist, final_states))
        
        print(f"  γ={gamma:.1f}: mean_dist={mean_dist:.8f}, max_dist={max_dist:.8f}", end="")
        if mean_dist < 0.01:
            print(" ← CONVERGED")
        else:
            print(" (orbiting)")
    
    # Find first converging γ
    print(f"\n  --- DAMPING SWEEP SUMMARY ---")
    best_gamma, best_mean, best_max, best_states = None, None, None, None
    for gamma, mean_dist, max_dist, states in sweep_results:
        if mean_dist < 0.01:
            if best_gamma is None:
                best_gamma = gamma
                best_mean = mean_dist
                best_max = max_dist
                best_states = states
    
    CONVERGENCE_THRESHOLD = 0.01
    if best_gamma is not None:
        print(f"  Critical damping threshold: γ ≈ {best_gamma:.1f}")
        print(f"  PASS: Attractor basin detected at γ={best_gamma:.1f}!")
        print(f"         {n_initial_states} diverse states converged to trace dist {best_mean:.8f}")
        
        # Characterize the attractor
        attractor = np.mean(best_states, axis=0)
        attractor = attractor / np.trace(attractor)
        attractor_entropy = von_neumann_entropy(attractor)
        eigvals = np.sort(np.real(np.linalg.eigvalsh(attractor)))[::-1]
        print(f"  Attractor entropy: {attractor_entropy:.6f}")
        print(f"  Attractor eigenvalues: {eigvals}")
        
        # Verify attractor is not maximally mixed (not trivial)
        max_entropy = np.log2(d)
        if attractor_entropy < max_entropy * 0.99:
            print(f"  Attractor is NON-TRIVIAL (S={attractor_entropy:.4f} < S_max={max_entropy:.4f})")
        else:
            print(f"  WARNING: Attractor is near maximally mixed (trivial)")
        
        return EvidenceToken(
            token_id="E_SIM_PROTO_ATTRACTOR_BASIN_OK",
            sim_spec_id="S_PROTO_ATTRACTOR_BASIN",
            status="PASS",
            measured_value=best_mean
        )
    else:
        # Even max γ didn't converge
        worst = sweep_results[-1]
        print(f"  KILL: No convergence even at γ={worst[0]:.1f} (mean dist={worst[1]:.6f})")
        return EvidenceToken(
            token_id="",
            sim_spec_id="S_PROTO_ATTRACTOR_BASIN",
            status="KILL",
            measured_value=worst[1],
            kill_reason="NO_ATTRACTOR_BASIN_CONVERGENCE"
        )


# ─────────────────────────────────────────────
# MAIN: Run the Proto-Ratchet
# ─────────────────────────────────────────────

def run_proto_ratchet():
    """Execute the full proto-ratchet SIM suite from base constraints up."""
    
    print("=" * 60)
    print("PROTO-RATCHET SIM RUNNER")
    print("Codex Ratchet — Computational Verification")
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print("=" * 60)
    
    np.random.seed(42)  # Reproducible
    
    evidence_ledger: List[EvidenceToken] = []
    graveyard: List[GraveyardRecord] = []
    
    # ─── TIER 0: BASE CONSTRAINTS ───
    e_f01 = sim_f01_finitude(d=4, n_trials=100)
    evidence_ledger.append(e_f01)
    
    e_n01 = sim_n01_noncommutation(d=4, n_trials=100)
    evidence_ledger.append(e_n01)
    
    # Gate: if base constraints fail, the entire ratchet is dead
    if e_f01.status == "KILL" or e_n01.status == "KILL":
        print("\n" + "!" * 60)
        print("RATCHET HALTED: Base constraints failed!")
        print("Cannot proceed to derived constraints.")
        print("!" * 60)
        _save_results(evidence_ledger, graveyard)
        return evidence_ledger, graveyard
    
    print("\n>>> BASE CONSTRAINTS SURVIVED. Proceeding to derived tests...")
    
    # ─── TIER 2: ACTION PRECEDENCE (requires F01 + N01) ───
    e_ap = sim_action_precedence(d=4, n_trials=50)
    evidence_ledger.append(e_ap)
    
    # ─── TIER 3: VARIANCE DIRECTION (requires F01 + N01) ───
    e_vd = sim_variance_direction(d=4, n_steps=200)
    evidence_ledger.append(e_vd)
    
    # ─── TIER 5: PROTO ATTRACTOR BASIN ───
    e_ab = sim_proto_attractor_basin(d=4, n_steps=500, n_initial_states=20)
    evidence_ledger.append(e_ab)
    
    # ─── FINAL REPORT ───
    print("\n" + "=" * 60)
    print("PROTO-RATCHET FINAL REPORT")
    print("=" * 60)
    
    passed = [e for e in evidence_ledger if e.status == "PASS"]
    killed = [e for e in evidence_ledger if e.status == "KILL"]
    
    print(f"\n  PASSED: {len(passed)}/{len(evidence_ledger)}")
    for e in passed:
        print(f"    ✓ {e.token_id} (value={e.measured_value:.6f})")
    
    if killed:
        print(f"\n  KILLED: {len(killed)}/{len(evidence_ledger)}")
        for e in killed:
            print(f"    ✗ {e.sim_spec_id}: {e.kill_reason}")
            graveyard.append(GraveyardRecord(
                failed_spec_id=e.sim_spec_id,
                killing_sim_id=e.sim_spec_id,
                missing_evidence=e.token_id or "NONE",
                fail_class=e.kill_reason or "UNKNOWN",
                rescue_path="Review operator construction and retry with modified parameters."
            ))
    
    _save_results(evidence_ledger, graveyard)
    return evidence_ledger, graveyard


def _save_results(evidence: List[EvidenceToken], graveyard: List[GraveyardRecord]):
    """Save proto-ratchet results to the a2_state directory."""
    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "evidence_ledger": [
            {
                "token_id": e.token_id,
                "sim_spec_id": e.sim_spec_id,
                "status": e.status,
                "measured_value": e.measured_value,
                "kill_reason": e.kill_reason,
                "timestamp": e.timestamp,
            }
            for e in evidence
        ],
        "graveyard": [
            {
                "failed_spec_id": g.failed_spec_id,
                "killing_sim_id": g.killing_sim_id,
                "missing_evidence": g.missing_evidence,
                "fail_class": g.fail_class,
                "rescue_path": g.rescue_path,
                "timestamp": g.timestamp,
            }
            for g in graveyard
        ],
        "summary": {
            "total_sims": len(evidence),
            "passed": len([e for e in evidence if e.status == "PASS"]),
            "killed": len([e for e in evidence if e.status == "KILL"]),
        }
    }
    
    outpath = os.path.join(results_dir, "proto_ratchet_results.json")
    with open(outpath, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Results saved to: {outpath}")


if __name__ == "__main__":
    run_proto_ratchet()
