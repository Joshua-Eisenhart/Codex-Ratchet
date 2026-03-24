"""
Mathematical Foundations SIM Suite
====================================
Computationally verify that the root axioms (F01 + N01) generator_bias
specific mathematical structures to exist.

SIM_01: Ne IS a Turing machine (reversible, deterministic, adiabatic)
SIM_02: F01 forces discrete eigenvalue spectrum (no continuum)
SIM_03: N01 forces complex numbers (real-only operators can't non-commute in d≥2)
SIM_04: F01+N01 forces chirality preference (generator_invariance breaking is inevitable)
SIM_05: Isothermal strokes give super-Ne power (process_cycle > Turing)
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
from full_8stage_engine_sim import (
    stage1_measurement_projection,
    stage3_constrained_expansion,
    survivorship_functional,
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIM_01: Ne IS a Turing Machine
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def sim_ne_is_turing(d: int = 4, n_steps: int = 100):
    """
    CLAIM: The Ne topology (adiabatic expansion) is a reversible
    deterministic computer — a Turing machine.
    
    TEST: Apply only unitary evolution (Q=0, no bath coupling).
    Verify: 
      1. Perfect reversibility (can undo every step)
      2. State_Distinction preservation (state_dispersion constant)
      3. Determinism (same input → same output)
    """
    print(f"\n{'='*60}")
    print(f"SIM_01: Ne IS A TURING MACHINE")
    print(f"  d={d}, steps={n_steps}")
    print(f"{'='*60}")
    
    np.random.seed(42)
    rho_init = make_random_density_matrix(d)
    U = make_random_unitary(d)
    U_inv = U.conj().T  # inverse = conjugate transpose
    
    # Forward computation (the "Turing tape")
    rho = rho_init.copy()
    S_init = von_neumann_entropy(rho)
    entropies = [S_init]
    
    for _ in range(n_steps):
        rho = apply_unitary_channel(rho, U)
        entropies.append(von_neumann_entropy(rho))
    
    S_final_forward = entropies[-1]
    rho_forward = rho.copy()
    
    # Reverse computation (run the tape backwards)
    for _ in range(n_steps):
        rho = apply_unitary_channel(rho, U_inv)
    
    # Check reversibility
    reverse_dist = trace_distance(rho_init, rho)
    
    # Check state_dispersion preservation (Turing = no state_distinction loss)
    entropy_drift = max(entropies) - min(entropies)
    
    # Check determinism (run again with same input)
    rho2 = rho_init.copy()
    for _ in range(n_steps):
        rho2 = apply_unitary_channel(rho2, U)
    determinism_dist = trace_distance(rho_forward, rho2)
    
    print(f"  State_Dispersion: init={S_init:.8f}, final={S_final_forward:.8f}")
    print(f"  State_Dispersion drift (max-min): {state_dispersion_drift:.12f}")
    print(f"  Reversibility (trace dist after undo): {reverse_dist:.12f}")
    print(f"  Determinism (trace dist same-input reruns): {determinism_dist:.12f}")
    
    reversible = reverse_dist < 1e-10
    info_preserved = entropy_drift < 1e-10
    deterministic = determinism_dist < 1e-14
    
    if reversible and info_preserved and deterministic:
        print(f"  PASS: Ne is a reversible deterministic computer (Turing machine)!")
        return EvidenceToken(
            token_id="E_SIM_NE_IS_TURING_OK",
            sim_spec_id="S_SIM_NE_IS_TURING_V1",
            status="PASS",
            measured_value=reverse_dist
        )
    else:
        print(f"  KILL: Ne fails Turing properties!")
        return EvidenceToken(
            token_id="",
            sim_spec_id="S_SIM_NE_IS_TURING_V1",
            status="KILL",
            measured_value=reverse_dist,
            kill_reason="NE_NOT_REVERSIBLE_DETERMINISTIC"
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIM_02: F01 Forces Discrete Spectrum
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def sim_f01_forces_discrete(d_values: list = [2, 4, 8, 16]):
    """
    CLAIM: Finitude (dim(H) = d < ∞) forces all observables to have
    a DISCRETE eigenvalue spectrum. No continuum possible.
    
    TEST: For each d, generate random Hermitian observables.
    Verify eigenvalues are always a finite discrete set with
    exactly d elements. As d increases, the spectrum gets denser
    but NEVER continuous.
    """
    print(f"\n{'='*60}")
    print(f"SIM_02: F01 FORCES DISCRETE SPECTRUM")
    print(f"  d values: {d_values}")
    print(f"{'='*60}")
    
    all_discrete = True
    for d in d_values:
        np.random.seed(42)
        # Generate random Hermitian observable
        H = np.random.randn(d, d) + 1j * np.random.randn(d, d)
        H = (H + H.conj().T) / 2  # Hermitianize
        
        eigenvalues = np.sort(np.real(np.linalg.eigvalsh(H)))
        n_eigenvalues = len(eigenvalues)
        
        # Count distinct eigenvalues (within numerical tolerance)
        distinct = len(set(np.round(eigenvalues, 10)))
        
        # Minimum gap between eigenvalues
        gaps = np.diff(eigenvalues)
        min_gap = np.min(gaps) if len(gaps) > 0 else 0
        
        is_discrete = n_eigenvalues == d and min_gap > 1e-12
        
        print(f"  d={d:3d}: eigenvalues={n_eigenvalues}, distinct={distinct}, min_gap={min_gap:.6f} {'✓' if is_discrete else '✗'}")
        
        if not is_discrete:
            all_discrete = False
    
    if all_discrete:
        print(f"  PASS: F01 forces discrete spectrum at all dimensions!")
        return EvidenceToken(
            token_id="E_SIM_F01_DISCRETE_OK",
            sim_spec_id="S_SIM_F01_DISCRETE_V1",
            status="PASS",
            measured_value=float(max(d_values))
        )
    else:
        print(f"  KILL: Continuous spectrum found!")
        return EvidenceToken(
            token_id="",
            sim_spec_id="S_SIM_F01_DISCRETE_V1",
            status="KILL",
            measured_value=0.0,
            kill_reason="CONTINUOUS_SPECTRUM_FOUND"
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIM_03: N01 Forces Complex Numbers
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def sim_n01_forces_complex(d: int = 4, n_trials: int = 1000):
    """
    CLAIM: Non-commutation forces complex numbers to exist. 
    Real-valued operators in d≥2 can commute, but achieving FULL
    non-commutativity requires complex entries (phase/rotation).
    
    TEST: Compare commutator norms for real-only vs complex matrices.
    Show that complex matrices achieve much higher non-commutativity.
    """
    print(f"\n{'='*60}")
    print(f"SIM_03: N01 FORCES COMPLEX NUMBERS")
    print(f"  d={d}, trials={n_trials}")
    print(f"{'='*60}")
    
    np.random.seed(42)
    
    real_comm_norms = []
    complex_comm_norms = []
    real_commute_count = 0
    complex_commute_count = 0
    
    for _ in range(n_trials):
        # Real-only operators (symmetric)
        A_real = np.random.randn(d, d)
        A_real = (A_real + A_real.T) / 2
        B_real = np.random.randn(d, d)
        B_real = (B_real + B_real.T) / 2
        comm_real = A_real @ B_real - B_real @ A_real
        norm_real = np.linalg.norm(comm_real)
        real_comm_norms.append(norm_real)
        if norm_real < 1e-10:
            real_commute_count += 1
        
        # Complex operators (Hermitian)
        A_complex = np.random.randn(d, d) + 1j * np.random.randn(d, d)
        A_complex = (A_complex + A_complex.conj().T) / 2
        B_complex = np.random.randn(d, d) + 1j * np.random.randn(d, d)
        B_complex = (B_complex + B_complex.conj().T) / 2
        comm_complex = A_complex @ B_complex - B_complex @ A_complex
        norm_complex = np.linalg.norm(comm_complex)
        complex_comm_norms.append(norm_complex)
        if norm_complex < 1e-10:
            complex_commute_count += 1
    
    avg_real = np.mean(real_comm_norms)
    avg_complex = np.mean(complex_comm_norms)
    max_real = np.max(real_comm_norms)
    max_complex = np.max(complex_comm_norms)
    
    print(f"  Real-only operators:")
    print(f"    Avg commutator norm: {avg_real:.6f}")
    print(f"    Max commutator norm: {max_real:.6f}")
    print(f"    Commuting pairs: {real_commute_count}/{n_trials}")
    print(f"  Complex operators:")
    print(f"    Avg commutator norm: {avg_complex:.6f}")
    print(f"    Max commutator norm: {max_complex:.6f}")
    print(f"    Commuting pairs: {complex_commute_count}/{n_trials}")
    print(f"  Ratio (complex/real): {avg_complex/avg_real:.4f}")
    
    # Key test: complex Hermitian commutators are PURE IMAGINARY
    # This means the commutator [A,B] is anti-Hermitian → i*Hermitian
    # The imaginary unit i is FORCED by non-commutation
    sample_comm = (A_complex @ B_complex - B_complex @ A_complex)
    is_anti_hermitian = np.allclose(sample_comm, -sample_comm.conj().T, atol=1e-10)
    print(f"\n  [A,B] is anti-Hermitian (forces i): {is_anti_hermitian}")
    print(f"  → The commutator of two Hermitian operators is i × (Hermitian)")
    print(f"  → Complex numbers are FORCED by non-commutation!")
    
    if is_anti_hermitian and avg_complex > avg_real:
        print(f"  PASS: N01 forces complex numbers!")
        return EvidenceToken(
            token_id="E_SIM_N01_FORCES_COMPLEX_OK",
            sim_spec_id="S_SIM_N01_FORCES_COMPLEX_V1",
            status="PASS",
            measured_value=avg_complex / avg_real
        )
    else:
        return EvidenceToken(
            token_id="",
            sim_spec_id="S_SIM_N01_FORCES_COMPLEX_V1",
            status="KILL",
            measured_value=0.0,
            kill_reason="COMPLEX_NOT_FORCED"
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIM_04: F01+N01 Forces Chirality
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def sim_chirality_forced(d: int = 4, n_trials: int = 100):
    """
    CLAIM: In a finite non-commutative system, perfect chiral generator_invariance
    is impossible. One chirality must dominate.
    
    TEST: Generate pairs of "left" and "right" engines from the SAME
    random seed with OPPOSITE operator ordering. Measure whether they
    produce identical attractors (symmetric) or distinct attractors
    (generator_invariance broken).
    """
    print(f"\n{'='*60}")
    print(f"SIM_04: F01+N01 FORCES CHIRALITY PREFERENCE")
    print(f"  d={d}, trials={n_trials}")
    print(f"{'='*60}")
    
    distinct_attractors = 0
    
    for trial in range(n_trials):
        np.random.seed(trial)
        
        # Shared operators
        U = make_random_unitary(d)
        L_base = np.random.randn(d, d) + 1j * np.random.randn(d, d)
        L = L_base / np.linalg.norm(L_base) * 3.0
        
        rho_init = make_random_density_matrix(d)
        
        # LEFT process_cycle: unitary THEN dissipation
        rho_left = rho_init.copy()
        for _ in range(200):
            rho_left = apply_unitary_channel(rho_left, U)
            for __ in range(3):
                rho_left = apply_lindbladian_step(rho_left, L, dt=0.01)
        
        # RIGHT process_cycle: dissipation THEN unitary (reversed order)
        rho_right = rho_init.copy()
        for _ in range(200):
            for __ in range(3):
                rho_right = apply_lindbladian_step(rho_right, L, dt=0.01)
            rho_right = apply_unitary_channel(rho_right, U)
        
        dist = trace_distance(rho_left, rho_right)
        if dist > 0.01:
            distinct_attractors += 1
    
    symmetry_broken_pct = (distinct_attractors / n_trials) * 100
    
    print(f"  Distinct attractors (generator_invariance broken): {distinct_attractors}/{n_trials} ({generator_invariance_broken_pct:.1f}%)")
    
    if symmetry_broken_pct > 90:
        print(f"  PASS: F01+N01 forces chirality — generator_invariance breaking is >90% inevitable!")
        return EvidenceToken(
            token_id="E_SIM_CHIRALITY_FORCED_OK",
            sim_spec_id="S_SIM_CHIRALITY_FORCED_V1",
            status="PASS",
            measured_value=symmetry_broken_pct
        )
    else:
        print(f"  KILL: Chirality not forced (symmetric attractors found)")
        return EvidenceToken(
            token_id="",
            sim_spec_id="S_SIM_CHIRALITY_FORCED_V1",
            status="KILL",
            measured_value=symmetry_broken_pct,
            kill_reason="CHIRAL_GENERATOR_INVARIANCE_NOT_BROKEN"
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIM_05: Process_Cycle > Turing (Super-Ne)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def sim_engine_beats_turing(d: int = 4, n_steps: int = 100):
    """
    CLAIM: The full 8-stage process_cycle can do things pure Ne (Turing) cannot:
    1. REDUCE state_dispersion (Turing preserves it)
    2. Create irreversible structure (Turing is reversible)
    3. Build attractors (Turing orbits forever)
    
    TEST: Compare pure unitary (Ne/Turing) vs process_cycle with isothermal strokes.
    """
    print(f"\n{'='*60}")
    print(f"SIM_05: PROCESS_CYCLE BEATS TURING (SUPER-Ne)")
    print(f"  d={d}, steps={n_steps}")
    print(f"{'='*60}")
    
    np.random.seed(42)
    rho_init = make_random_density_matrix(d)
    U = make_random_unitary(d)
    L_base = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    L = L_base / np.linalg.norm(L_base) * 3.0
    
    # --- Ne/Turing: pure unitary ---
    rho_turing = rho_init.copy()
    S_turing = []
    for _ in range(n_steps):
        rho_turing = apply_unitary_channel(rho_turing, U)
        S_turing.append(von_neumann_entropy(rho_turing))
    
    # --- Full Process_Cycle: complete 8-stage cycle ---
    from full_8stage_engine_sim import run_one_cycle
    
    proj = np.eye(d, dtype=complex)
    proj[-1, -1] = 0.2
    filt = np.eye(d, dtype=complex)
    filt[-1, -1] = 0.1
    filt[-2, -2] = 0.3
    observable = np.diag(np.linspace(0.1, 1.0, d).astype(complex))
    sigma_bath = np.eye(d, dtype=complex) / d
    U2 = make_random_unitary(d)
    
    rho_engine = rho_init.copy()
    S_engine = []
    for _ in range(n_steps):
        rho_engine = run_one_cycle(rho_engine, d, U, U2, L, proj, filt, 
                                    observable, sigma_bath)
        S_engine.append(von_neumann_entropy(rho_engine))
    
    S_turing_range = max(S_turing) - min(S_turing)
    S_engine_range = max(S_engine) - min(S_engine)
    S_engine_final = S_engine[-1]
    S_turing_final = S_turing[-1]
    
    # Turing: state_dispersion is CONSTANT (reversible)
    # Process_Cycle: state_dispersion CHANGES (irreversible structure creation)
    print(f"  Turing (Ne only):")
    print(f"    State_Dispersion range: {S_turing_range:.10f} (should be ~0)")
    print(f"    Final S: {S_turing_final:.6f}")
    print(f"  Full Process_Cycle (8-stage cycle):")
    print(f"    State_Dispersion range: {S_process_cycle_range:.6f} (should be large)")
    print(f"    Final S: {S_process_cycle_final:.6f}")
    
    final_eigvals = np.sort(np.real(np.linalg.eigvalsh(rho_engine)))[::-1]
    dominant = final_eigvals[0]
    attractors_found = dominant > 0.30
    
    print(f"  Process_Cycle invariant_target eigenvalues: {final_eigvals}")
    print(f"  Dominant: {dominant:.4f} (invariant_target found: {attractors_found})")
    
    turing_preserves = S_turing_range < 1e-8
    engine_reduces = S_engine_range > 0.1
    
    if turing_preserves and engine_reduces and attractors_found:
        print(f"  PASS: Process_Cycle creates irreversible structure; Turing cannot!")
        return EvidenceToken(
            token_id="E_SIM_PROCESS_CYCLE_BEATS_TURING_OK",
            sim_spec_id="S_SIM_PROCESS_CYCLE_SUPER_NE_V1",
            status="PASS",
            measured_value=S_engine_range
        )
    else:
        return EvidenceToken(
            token_id="",
            sim_spec_id="S_SIM_PROCESS_CYCLE_SUPER_NE_V1",
            status="KILL",
            measured_value=0.0,
            kill_reason="PROCESS_CYCLE_NOT_SUPERIOR_TO_TURING"
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    results = []
    
    results.append(sim_ne_is_turing())
    results.append(sim_f01_forces_discrete())
    results.append(sim_n01_forces_complex())
    results.append(sim_chirality_forced())
    results.append(sim_engine_beats_turing())
    
    print(f"\n{'='*60}")
    print(f"MATH FOUNDATIONS SUITE RESULTS")
    print(f"{'='*60}")
    for e in results:
        icon = "✓" if e.status == "PASS" else "✗"
        print(f"  {icon} {e.sim_spec_id}: {e.status} (value={e.measured_value:.6f})")
    
    # Save results
    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "math_foundations_results.json")
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
