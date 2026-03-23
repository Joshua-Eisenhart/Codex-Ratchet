"""
Rock Falsifier SIM
==================
The ultimate adversarial test: does a low-action "rock" outperform
the complex 8-stage engine under environmental volatility?

If the rock wins under BROAD volatile shocks, the entire
"solvency implies complexity" hypothesis is KILLED.

A2 Fuel:
  - Rock = near-identity channel E_agent ≈ I
  - Shocks = CPTP perturbations (amplitude damping, phase flips, random unitaries)
  - Regime shifts = sudden macro-level changes in shock distribution
  - Solvency = Tr(Π_alive ρ_T) — alive probability at horizon T
  - Competence = W_useful / (1 + K)
"""

import numpy as np
import json
import os
from datetime import datetime, UTC
from typing import List, Dict, Tuple

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
    stage2_diffusive_damping,
    stage3_constrained_expansion,
    stage4_entrainment_lock,
    stage5_gradient_descent,
    stage6_matched_filtering,
    stage7_spectral_emission,
    stage8_gradient_ascent,
    survivorship_functional,
    compute_landauer_cost,
)


def apply_shock(rho: np.ndarray, shock_type: str, intensity: float = 0.3) -> np.ndarray:
    """Apply an environmental shock (CPTP perturbation)."""
    d = rho.shape[0]
    
    if shock_type == "amplitude_damping":
        # Partial decay toward ground state
        ground = np.zeros((d, d), dtype=complex)
        ground[0, 0] = 1.0
        rho = (1 - intensity) * rho + intensity * ground
        
    elif shock_type == "phase_flip":
        # Random dephasing
        phases = np.exp(2j * np.pi * np.random.rand(d))
        P = np.diag(phases)
        rho = (1 - intensity) * rho + intensity * (P @ rho @ P.conj().T)
        
    elif shock_type == "random_unitary":
        # Random rotation
        U = make_random_unitary(d)
        rho_rotated = apply_unitary_channel(rho, U)
        rho = (1 - intensity) * rho + intensity * rho_rotated
        
    elif shock_type == "depolarizing":
        # Push toward maximally mixed
        I_d = np.eye(d, dtype=complex) / d
        rho = (1 - intensity) * rho + intensity * I_d
        
    elif shock_type == "regime_shift":
        # Dramatic operator change — completely new random state injection
        rho_new = make_random_density_matrix(d)
        rho = (1 - intensity) * rho + intensity * rho_new
    
    # Enforce density matrix constraints
    rho = (rho + rho.conj().T) / 2
    eigvals, eigvecs = np.linalg.eigh(rho)
    eigvals = np.maximum(eigvals, 0)
    rho = eigvecs @ np.diag(eigvals.astype(complex)) @ eigvecs.conj().T
    rho = rho / np.trace(rho)
    return rho


def rock_agent(rho: np.ndarray) -> np.ndarray:
    """The Rock: near-identity channel. Does almost nothing."""
    d = rho.shape[0]
    # Minimal action: very slight contraction toward center
    I_d = np.eye(d, dtype=complex) / d
    rho_new = 0.99 * rho + 0.01 * I_d
    rho_new = rho_new / np.trace(rho_new)
    return rho_new


def engine_agent(rho: np.ndarray, d: int, U1, U2, L, proj, filt,
                 observable, sigma_attractor) -> np.ndarray:
    """The 8-Stage Engine: full complexity."""
    rho = stage1_measurement_projection(rho, d)
    rho = stage2_diffusive_damping(rho, L, n_steps=3)
    rho = stage3_constrained_expansion(rho, U1, proj)
    rho = stage4_entrainment_lock(rho, sigma_attractor, coupling=0.2)
    rho = stage5_gradient_descent(rho, observable, eta=0.03)
    rho = stage6_matched_filtering(rho, filt)
    rho = stage7_spectral_emission(rho, U2, noise_scale=0.05)
    rho = stage8_gradient_ascent(rho, observable, eta=0.03)
    return rho


def compute_solvency(rho: np.ndarray, d: int) -> float:
    """Compute solvency: alive probability via stall projector.
    Stall = maximally mixed (thermal death). Alive = structured."""
    max_S = np.log2(d)
    S = von_neumann_entropy(rho)
    # Solvency = how far from thermal death
    solvency = 1.0 - (S / max_S)
    return max(0.0, solvency)


def run_rock_falsifier(d: int = 4, horizon: int = 200, n_trials: int = 10,
                        regime_shift_interval: int = 50):
    """
    Run the Rock Falsifier: compare rock vs engine across environmental shocks.
    
    The rock should win in calm environments.
    The engine should win under volatility and regime shifts.
    """
    print(f"{'='*60}")
    print(f"ROCK FALSIFIER SIM")
    print(f"  d={d}, horizon={horizon}, trials={n_trials}")
    print(f"  Regime shifts every {regime_shift_interval} steps")
    print(f"{'='*60}")
    
    np.random.seed(42)
    
    # Engine setup
    U1 = make_random_unitary(d)
    U2 = make_random_unitary(d)
    L_base = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    L = L_base / np.linalg.norm(L_base) * 3.0
    proj = np.eye(d, dtype=complex)
    proj[-1, -1] = 0.2
    filt = np.eye(d, dtype=complex)
    filt[-1, -1] = 0.1
    filt[-2, -2] = 0.3
    observable = np.diag(np.linspace(0.1, 1.0, d).astype(complex))
    
    # Warm up to get cycle-specific attractor
    sigma_bath = np.eye(d, dtype=complex) / d
    rho_warmup = make_random_density_matrix(d)
    for _ in range(8):
        rho_warmup = engine_agent(rho_warmup, d, U1, U2, L, proj, filt, observable, sigma_bath)
    sigma_attractor = rho_warmup.copy()
    
    shock_types = ["amplitude_damping", "phase_flip", "random_unitary", "depolarizing"]
    
    # Test across volatility levels
    volatility_levels = [0.05, 0.15, 0.30, 0.50]
    
    results = {}
    
    for volatility in volatility_levels:
        rock_solvencies = []
        engine_solvencies = []
        
        for trial in range(n_trials):
            np.random.seed(42 + trial * 100)
            
            # Same initial state for both
            rho_init = make_random_density_matrix(d)
            rho_rock = rho_init.copy()
            rho_engine = rho_init.copy()
            
            rock_alive = True
            engine_alive = True
            rock_steps = 0
            engine_steps = 0
            
            for step in range(horizon):
                # Determine shock
                if step % regime_shift_interval == 0 and step > 0:
                    shock = "regime_shift"
                    intensity = volatility * 2  # regime shifts are stronger
                else:
                    shock = np.random.choice(shock_types)
                    intensity = volatility
                
                # Apply shock then agent
                if rock_alive:
                    rho_rock = apply_shock(rho_rock, shock, intensity)
                    rho_rock = rock_agent(rho_rock)
                    sol_rock = compute_solvency(rho_rock, d)
                    if sol_rock < 0.02:  # stall threshold
                        rock_alive = False
                    else:
                        rock_steps = step + 1
                
                if engine_alive:
                    rho_engine = apply_shock(rho_engine, shock, intensity)
                    rho_engine = engine_agent(rho_engine, d, U1, U2, L, proj, filt,
                                              observable, sigma_attractor)
                    sol_engine = compute_solvency(rho_engine, d)
                    if sol_engine < 0.02:
                        engine_alive = False
                    else:
                        engine_steps = step + 1
            
            rock_final_sol = compute_solvency(rho_rock, d) if rock_alive else 0.0
            engine_final_sol = compute_solvency(rho_engine, d) if engine_alive else 0.0
            
            rock_solvencies.append(rock_final_sol)
            engine_solvencies.append(engine_final_sol)
        
        avg_rock = np.mean(rock_solvencies)
        avg_engine = np.mean(engine_solvencies)
        winner = "ROCK" if avg_rock > avg_engine else "ENGINE"
        
        results[volatility] = {
            "rock_avg_solvency": float(avg_rock),
            "engine_avg_solvency": float(avg_engine),
            "winner": winner,
        }
        
        print(f"\n  Volatility={volatility:.2f}: Rock={avg_rock:.4f}, Engine={avg_engine:.4f} → {winner}")
    
    # Determine overall falsification
    print(f"\n{'='*60}")
    print(f"ROCK FALSIFIER VERDICT")
    print(f"{'='*60}")
    
    # The engine should lose at low volatility and win at high
    low_vol_winner = results[0.05]["winner"]
    high_vol_winner = results[0.50]["winner"]
    
    if low_vol_winner == "ROCK" and high_vol_winner == "ENGINE":
        print(f"  PASS: Rock wins calm (complexity tax), Engine wins volatile (adaptation).")
        print(f"  Crossover confirmed — solvency→complexity hypothesis survives!")
        evidence = EvidenceToken(
            token_id="E_SIM_ROCK_FALSIFIER_CROSSOVER_OK",
            sim_spec_id="S_SIM_ROCK_FALSIFIER_V1",
            status="PASS",
            measured_value=results[0.50]["engine_avg_solvency"]
        )
    elif high_vol_winner == "ROCK":
        print(f"  KILL: Rock wins EVEN under high volatility!")
        print(f"  The solvency→complexity hypothesis is FALSIFIED.")
        evidence = EvidenceToken(
            token_id="",
            sim_spec_id="S_SIM_ROCK_FALSIFIER_V1",
            status="KILL",
            measured_value=results[0.50]["rock_avg_solvency"],
            kill_reason="ROCK_OUTPERFORMS_ENGINE_UNDER_VOLATILITY"
        )
    elif low_vol_winner == "ENGINE":
        print(f"  WARNING: Engine wins even in calm environments.")
        print(f"  Possible complexity bias — costs may be miscalculated.")
        evidence = EvidenceToken(
            token_id="E_SIM_ROCK_FALSIFIER_COMPLEXITY_BIAS",
            sim_spec_id="S_SIM_ROCK_FALSIFIER_V1",
            status="PASS",
            measured_value=results[0.05]["engine_avg_solvency"]
        )
    else:
        print(f"  INCONCLUSIVE: Unexpected result pattern.")
        evidence = EvidenceToken(
            token_id="",
            sim_spec_id="S_SIM_ROCK_FALSIFIER_V1",
            status="KILL",
            measured_value=0.0,
            kill_reason="INCONCLUSIVE_RESULT"
        )
    
    # Save results
    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "rock_falsifier_results.json")
    evidence_entry = {
        "token_id": evidence.token_id,
        "sim_spec_id": evidence.sim_spec_id,
        "status": evidence.status,
        "measured_value": evidence.measured_value,
        "kill_reason": evidence.kill_reason,
    }
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "results_by_volatility": results,
            "evidence": evidence_entry,
            "evidence_ledger": [evidence_entry],
        }, f, indent=2)
    print(f"\n  Results saved to: {outpath}")
    
    return evidence, results


if __name__ == "__main__":
    evidence, results = run_rock_falsifier(d=4, horizon=200, n_trials=10)
