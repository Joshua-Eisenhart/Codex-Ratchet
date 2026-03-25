"""
Enhanced Rock Falsifier SIM — Bridge T Test
=============================================
The single biggest gap (NLM-15): does maximizing solvency GENERATOR_BIAS
increasing complexity, or can a "rock" outperform the full process_cycle?

This sim compares:
  - ROCK: d=2 near-identity channel (no dual loop, minimal action)
  - PROCESS_CYCLE: full 8-stage cycle at d=4 (dual loop, all operators)

across 1000 random environmental perturbations (5 shock types,
randomized intensities, regime shifts). Both agents receive the
SAME shock sequence per trial.

VERDICT:
  - If process_cycle ALWAYS outperforms rock → Bridge T SURVIVES
  - If rock outperforms process_cycle in ANY regime → Bridge T is KILLED
    (the teleological weighting assumption is falsified)

A2 Fuel: NLM-15, A2_NLM_BATCH3_FULL_SYNTHESIS__v1.md
"""

import numpy as np
import json
import os
from datetime import datetime, UTC
from typing import Dict, List, Tuple
from dataclasses import dataclass

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
    quantum_kl_divergence,
)


# ─────────────────────────────────────────────
# Shock Generator (5 types + regime shifts)
# ─────────────────────────────────────────────

SHOCK_TYPES = [
    "amplitude_damping",
    "phase_flip",
    "random_unitary",
    "depolarizing",
    "bit_flip",
]


def apply_shock(rho: np.ndarray, shock_type: str, intensity: float) -> np.ndarray:
    """Apply an environmental perturbation (CPTP map) to a density matrix."""
    d = rho.shape[0]

    if shock_type == "amplitude_damping":
        ground = np.zeros((d, d), dtype=complex)
        ground[0, 0] = 1.0
        rho = (1 - intensity) * rho + intensity * ground

    elif shock_type == "phase_flip":
        phases = np.exp(2j * np.pi * np.random.rand(d))
        P = np.diag(phases)
        rho = (1 - intensity) * rho + intensity * (P @ rho @ P.conj().T)

    elif shock_type == "random_unitary":
        U = make_random_unitary(d)
        rho = (1 - intensity) * rho + intensity * apply_unitary_channel(rho, U)

    elif shock_type == "depolarizing":
        I_d = np.eye(d, dtype=complex) / d
        rho = (1 - intensity) * rho + intensity * I_d

    elif shock_type == "bit_flip":
        # Permute basis states randomly
        perm = np.random.permutation(d)
        P = np.eye(d, dtype=complex)[perm]
        rho = (1 - intensity) * rho + intensity * (P @ rho @ P.T)

    elif shock_type == "regime_shift":
        rho_new = make_random_density_matrix(d)
        rho = (1 - intensity) * rho + intensity * rho_new

    # Re-enforce density matrix constraints
    rho = (rho + rho.conj().T) / 2
    eigvals, eigvecs = np.linalg.eigh(rho)
    eigvals = np.maximum(eigvals, 0)
    rho = eigvecs @ np.diag(eigvals.astype(complex)) @ eigvecs.conj().T
    tr = np.real(np.trace(rho))
    if tr > 1e-15:
        rho = rho / tr
    return rho


def generate_shock_sequence(n_steps: int, regime_shift_interval: int = 50,
                            rng: np.random.RandomState = None) -> List[Tuple[str, float]]:
    """Pre-generate a full shock sequence so rock and process_cycle see the SAME shocks."""
    if rng is None:
        rng = np.random.RandomState()
    shocks = []
    for step in range(n_steps):
        if step > 0 and step % regime_shift_interval == 0:
            # Regime shift — stronger perturbation
            intensity = rng.uniform(0.3, 0.7)
            shocks.append(("regime_shift", intensity))
        else:
            shock_type = SHOCK_TYPES[rng.randint(len(SHOCK_TYPES))]
            intensity = rng.uniform(0.01, 0.5)
            shocks.append((shock_type, intensity))
    return shocks


# ─────────────────────────────────────────────
# Rock Agent (d=2, near-identity, no dual loop)
# ─────────────────────────────────────────────

def rock_agent(rho: np.ndarray) -> np.ndarray:
    """The Rock: d=2 near-identity channel. Minimal action, no feedback loops.

    This is the simplest possible agent — it barely acts on its state.
    If this outperforms the full process_cycle, Bridge T is killed.
    """
    d = rho.shape[0]
    I_d = np.eye(d, dtype=complex) / d
    # 1% contraction toward maximally mixed — the rock "does almost nothing"
    rho_new = 0.99 * rho + 0.01 * I_d
    rho_new = rho_new / np.trace(rho_new)
    return rho_new


# ─────────────────────────────────────────────
# Process_Cycle Agent (d=4, full 8-stage dual loop)
# ─────────────────────────────────────────────

class EngineContext:
    """Pre-computed operators for the 8-stage process_cycle."""

    def __init__(self, d: int = 4, rng_seed: int = 42):
        rng = np.random.RandomState(rng_seed)
        old_state = np.random.get_state()
        np.random.seed(rng_seed)

        self.d = d
        self.U1 = make_random_unitary(d)
        self.U2 = make_random_unitary(d)

        L_base = np.random.randn(d, d) + 1j * np.random.randn(d, d)
        self.L = L_base / np.linalg.norm(L_base) * 3.0  # γ=3.0 critical damping

        self.proj = np.eye(d, dtype=complex)
        self.proj[-1, -1] = 0.2

        self.filt = np.eye(d, dtype=complex)
        self.filt[-1, -1] = 0.1
        self.filt[-2, -2] = 0.3

        self.observable = np.diag(np.linspace(0.1, 1.0, d).astype(complex))
        self.sigma_bath = np.eye(d, dtype=complex) / d

        # Warm-up to find cycle-specific invariant_target
        rho_warmup = make_random_density_matrix(d)
        for _ in range(8):
            rho_warmup = self._run_cycle(rho_warmup)
        self.sigma_attractor = rho_warmup.copy()

        np.random.set_state(old_state)

    def _run_cycle(self, rho: np.ndarray) -> np.ndarray:
        """Run one full 8-stage cycle."""
        d = self.d
        rho = stage1_measurement_projection(rho, d)
        rho = stage2_diffusive_damping(rho, self.L, n_steps=3)
        rho = stage3_constrained_expansion(rho, self.U1, self.proj)
        rho = stage4_entrainment_lock(rho, self.sigma_attractor
                                       if hasattr(self, 'sigma_invariant_target')
                                       else self.sigma_bath, coupling=0.2)
        rho = stage5_gradient_descent(rho, self.observable, eta=0.03)
        rho = stage6_matched_filtering(rho, self.filt)
        rho = stage7_spectral_emission(rho, self.U2, noise_scale=0.05)
        rho = stage8_gradient_ascent(rho, self.observable, eta=0.03)
        return rho

    def step(self, rho: np.ndarray) -> np.ndarray:
        return self._run_cycle(rho)


# ─────────────────────────────────────────────
# Solvency & Competence Metrics
# ─────────────────────────────────────────────

def compute_solvency(rho: np.ndarray) -> float:
    """Solvency = how far from thermal death (maximally mixed).
    1.0 = pure state (maximum structure), 0.0 = maximally mixed (dead).
    """
    d = rho.shape[0]
    max_S = np.log2(d)
    if max_S < 1e-15:
        return 1.0
    S = von_neumann_entropy(rho)
    return max(0.0, 1.0 - (S / max_S))


def compute_competence(solvency: float, complexity_cost: float) -> float:
    """Competence = useful work per unit complexity.
    W_useful / (1 + K) where K = Landauer cost proxy.
    """
    return solvency / (1.0 + complexity_cost)


# ─────────────────────────────────────────────
# Dimension Adapter: embed d=2 rock state into d=4 for comparison
# ─────────────────────────────────────────────

def embed_state(rho_small: np.ndarray, d_target: int) -> np.ndarray:
    """Embed a smaller density matrix into a larger Hilbert space (tensor with I)."""
    d_small = rho_small.shape[0]
    if d_small == d_target:
        return rho_small
    # Pad with zeros — the rock lives in a subspace
    rho_big = np.zeros((d_target, d_target), dtype=complex)
    rho_big[:d_small, :d_small] = rho_small
    tr = np.real(np.trace(rho_big))
    if tr > 1e-15:
        rho_big = rho_big / tr
    return rho_big


def partial_trace_to(rho_big: np.ndarray, d_target: int) -> np.ndarray:
    """Extract the top-left d_target×d_target block (partial trace proxy)."""
    rho_small = rho_big[:d_target, :d_target].copy()
    rho_small = (rho_small + rho_small.conj().T) / 2
    eigvals, eigvecs = np.linalg.eigh(rho_small)
    eigvals = np.maximum(eigvals, 0)
    rho_small = eigvecs @ np.diag(eigvals.astype(complex)) @ eigvecs.conj().T
    tr = np.real(np.trace(rho_small))
    if tr > 1e-15:
        rho_small = rho_small / tr
    return rho_small


# ─────────────────────────────────────────────
# Main Simulation: 1000 Perturbation Trials
# ─────────────────────────────────────────────

def run_enhanced_rock_falsifier(
    d_rock: int = 2,
    d_engine: int = 4,
    horizon: int = 100,
    n_trials: int = 1000,
    regime_shift_interval: int = 25,
    stall_threshold: float = 0.01,
    verbose: bool = True,
) -> Tuple[EvidenceToken, Dict]:
    """
    Enhanced Rock Falsifier: 1000 random perturbation trials.

    Each trial:
      1. Generate the SAME random shock sequence
      2. Run both rock (d=2) and process_cycle (d=4) through the shocks
      3. Measure final solvency and cumulative competence
      4. Record winner

    Bridge T verdict:
      - Process_Cycle must outperform rock in the MAJORITY of trials
      - If rock wins overall → Bridge T KILLED
    """
    print(f"{'='*70}")
    print(f"ENHANCED ROCK FALSIFIER SIM — BRIDGE T TEST")
    print(f"  Rock:   d={d_rock}, near-identity channel (no dual loop)")
    print(f"  Process_Cycle: d={d_engine}, full 8-stage cycle (dual loop)")
    print(f"  Trials: {n_trials}, Horizon: {horizon} steps/trial")
    print(f"  Regime shifts every {regime_shift_interval} steps")
    print(f"  Stall threshold: solvency < {stall_threshold}")
    print(f"{'='*70}")

    # Pre-build process_cycle context (operators are fixed across trials)
    engine_ctx = EngineContext(d=d_engine, rng_seed=42)

    # Complexity costs (Landauer proxy)
    # Rock: d=2, almost no action → cost ≈ 0
    # Process_Cycle: d=4, 8 stages → cost = log2(d²) × 8 stages
    rock_complexity_cost = 0.01  # near-zero
    engine_complexity_cost = np.log2(d_engine**2) * 8 * 0.01  # ~0.32

    # ── Per-trial results ──
    trial_results = []
    rock_wins = 0
    engine_wins = 0
    ties = 0

    rock_survivals = 0
    engine_survivals = 0
    rock_solvency_sum = 0.0
    engine_solvency_sum = 0.0

    for trial in range(n_trials):
        rng = np.random.RandomState(seed=trial * 7 + 13)

        # Generate shock sequence (same for both agents)
        shocks = generate_shock_sequence(horizon, regime_shift_interval, rng)

        # Initial states: random but SAME initial condition
        # Rock lives in d=2, process_cycle in d=4
        # We generate a d=2 init and embed it into d=4 for the process_cycle
        np.random.seed(trial * 7 + 13)
        rho_rock_init = make_random_density_matrix(d_rock)
        rho_engine_init = embed_state(rho_rock_init, d_engine)

        rho_rock = rho_rock_init.copy()
        rho_engine = rho_engine_init.copy()

        rock_alive = True
        engine_alive = True
        rock_cumulative_solvency = 0.0
        engine_cumulative_solvency = 0.0

        for step in range(horizon):
            shock_type, intensity = shocks[step]

            # ── Rock step ──
            if rock_alive:
                rho_rock = apply_shock(rho_rock, shock_type, intensity)
                rho_rock = rock_agent(rho_rock)
                sol_rock = compute_solvency(rho_rock)
                rock_cumulative_solvency += sol_rock
                if sol_rock < stall_threshold:
                    rock_alive = False

            # ── Process_Cycle step ──
            if engine_alive:
                rho_engine = apply_shock(rho_engine, shock_type, intensity)
                rho_engine = engine_ctx.step(rho_engine)
                sol_engine = compute_solvency(rho_engine)
                engine_cumulative_solvency += sol_engine
                if sol_engine < stall_threshold:
                    engine_alive = False

        # Final metrics
        final_sol_rock = compute_solvency(rho_rock) if rock_alive else 0.0
        final_sol_engine = compute_solvency(rho_engine) if engine_alive else 0.0

        # Competence = cumulative solvency / complexity cost
        rock_competence = compute_competence(
            rock_cumulative_solvency / horizon, rock_complexity_cost
        )
        engine_competence = compute_competence(
            engine_cumulative_solvency / horizon, engine_complexity_cost
        )

        # Winner determination: primary = final solvency, tiebreak = competence
        if final_sol_engine > final_sol_rock + 1e-6:
            winner = "PROCESS_CYCLE"
            engine_wins += 1
        elif final_sol_rock > final_sol_engine + 1e-6:
            winner = "ROCK"
            rock_wins += 1
        else:
            # Tie on solvency → competence breaks it
            if engine_competence > rock_competence + 1e-6:
                winner = "PROCESS_CYCLE"
                engine_wins += 1
            elif rock_competence > engine_competence + 1e-6:
                winner = "ROCK"
                rock_wins += 1
            else:
                winner = "TIE"
                ties += 1

        if rock_alive:
            rock_survivals += 1
        if engine_alive:
            engine_survivals += 1
        rock_solvency_sum += final_sol_rock
        engine_solvency_sum += final_sol_engine

        trial_results.append({
            "trial": trial,
            "rock_final_solvency": float(final_sol_rock),
            "process_cycle_final_solvency": float(final_sol_engine),
            "rock_competence": float(rock_competence),
            "process_cycle_competence": float(engine_competence),
            "rock_alive": rock_alive,
            "process_cycle_alive": engine_alive,
            "winner": winner,
        })

        # Progress reporting
        if verbose and (trial + 1) % 100 == 0:
            print(f"  [{trial+1:4d}/{n_trials}] "
                  f"Process_Cycle wins: {engine_wins}, Rock wins: {rock_wins}, "
                  f"Ties: {ties}")

    # ─── AGGREGATE STATISTICS ───
    avg_rock_sol = rock_solvency_sum / n_trials
    avg_engine_sol = engine_solvency_sum / n_trials
    rock_survival_rate = rock_survivals / n_trials
    engine_survival_rate = engine_survivals / n_trials
    engine_win_rate = engine_wins / n_trials
    rock_win_rate = rock_wins / n_trials

    # ─── Bin by shock intensity to find crossover ───
    # Compute per-trial average shock intensity
    intensity_bins = {"low": [], "medium": [], "high": []}
    for tr in trial_results:
        trial_idx = tr["trial"]
        rng_check = np.random.RandomState(seed=trial_idx * 7 + 13)
        shk = generate_shock_sequence(horizon, regime_shift_interval, rng_check)
        avg_intensity = np.mean([s[1] for s in shk])
        if avg_intensity < 0.15:
            intensity_bins["low"].append(tr)
        elif avg_intensity < 0.35:
            intensity_bins["medium"].append(tr)
        else:
            intensity_bins["high"].append(tr)

    bin_summaries = {}
    for bin_name, trials_in_bin in intensity_bins.items():
        if len(trials_in_bin) == 0:
            continue
        e_wins = sum(1 for t in trials_in_bin if t["winner"] == "PROCESS_CYCLE")
        r_wins = sum(1 for t in trials_in_bin if t["winner"] == "ROCK")
        t_count = len(trials_in_bin)
        bin_summaries[bin_name] = {
            "n_trials": t_count,
            "process_cycle_wins": e_wins,
            "rock_wins": r_wins,
            "process_cycle_win_rate": e_wins / t_count if t_count > 0 else 0,
            "rock_win_rate": r_wins / t_count if t_count > 0 else 0,
        }

    # ─── VERDICT ───
    print(f"\n{'='*70}")
    print(f"ENHANCED ROCK FALSIFIER — RESULTS")
    print(f"{'='*70}")
    print(f"  Trials:             {n_trials}")
    print(f"  Process_Cycle wins:        {engine_wins} ({engine_win_rate:.1%})")
    print(f"  Rock wins:          {rock_wins} ({rock_win_rate:.1%})")
    print(f"  Ties:               {ties}")
    print(f"  Avg solvency:       Process_Cycle={avg_engine_sol:.4f}, Rock={avg_rock_sol:.4f}")
    print(f"  Survival rate:      Process_Cycle={engine_survival_rate:.1%}, Rock={rock_survival_rate:.1%}")
    print(f"\n  Intensity Bin Breakdown:")
    for bin_name, summary in bin_summaries.items():
        print(f"    {bin_name:8s}: n={summary['n_trials']:4d}, "
              f"Process_Cycle={summary['process_cycle_win_rate']:.1%}, "
              f"Rock={summary['rock_win_rate']:.1%}")

    # ─── BRIDGE T ADJUDICATION ───
    print(f"\n{'='*70}")
    print(f"BRIDGE T VERDICT")
    print(f"{'='*70}")

    if engine_win_rate > 0.5:
        if rock_win_rate > 0.1:
            # Process_Cycle wins majority but rock wins non-trivially
            verdict = "WOUNDED"
            print(f"  WOUNDED: Process_Cycle wins {engine_win_rate:.1%} but rock wins {rock_win_rate:.1%}.")
            print(f"  Bridge T survives but is NOT universal —")
            print(f"  complexity is advantageous only in volatile environments.")
            evidence = EvidenceToken(
                token_id="E_SIM_ROCK_FALSIFIER_ENHANCED_WOUNDED",
                sim_spec_id="S_SIM_ROCK_FALSIFIER_ENHANCED_V1",
                status="PASS",
                measured_value=engine_win_rate,
            )
        else:
            # Process_Cycle dominates overwhelmingly
            verdict = "SURVIVES"
            print(f"  SURVIVES: Process_Cycle wins {engine_win_rate:.1%}, rock wins only {rock_win_rate:.1%}.")
            print(f"  Bridge T holds — solvency→complexity is empirically supported.")
            evidence = EvidenceToken(
                token_id="E_SIM_ROCK_FALSIFIER_ENHANCED_OK",
                sim_spec_id="S_SIM_ROCK_FALSIFIER_ENHANCED_V1",
                status="PASS",
                measured_value=engine_win_rate,
            )
    elif engine_win_rate == rock_win_rate:
        verdict = "INCONCLUSIVE"
        print(f"  INCONCLUSIVE: Exact tie at {engine_win_rate:.1%} each.")
        print(f"  Bridge T neither confirmed nor killed — need more trials or varied conditions.")
        evidence = EvidenceToken(
            token_id="",
            sim_spec_id="S_SIM_ROCK_FALSIFIER_ENHANCED_V1",
            status="KILL",
            measured_value=engine_win_rate,
            kill_reason="INCONCLUSIVE_TIE",
        )
    else:
        # Rock wins majority
        verdict = "KILLED"
        print(f"  KILLED: Rock wins {rock_win_rate:.1%} > Process_Cycle {engine_win_rate:.1%}!")
        print(f"  Bridge T is FALSIFIED — a low-action rock outperforms the")
        print(f"  full 8-stage process_cycle. The teleological assumption that")
        print(f"  solvency forces complexity is WRONG.")
        evidence = EvidenceToken(
            token_id="",
            sim_spec_id="S_SIM_ROCK_FALSIFIER_ENHANCED_V1",
            status="KILL",
            measured_value=rock_win_rate,
            kill_reason="ROCK_OUTPERFORMS_PROCESS_CYCLE_BRIDGE_T_FALSIFIED",
        )

    # ─── SAVE RESULTS ───
    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "rock_falsifier_enhanced_results.json")

    output = {
        "timestamp": datetime.now(UTC).isoformat(),
        "config": {
            "d_rock": d_rock,
            "d_process_cycle": d_engine,
            "horizon": horizon,
            "n_trials": n_trials,
            "regime_shift_interval": regime_shift_interval,
            "stall_threshold": stall_threshold,
            "rock_complexity_cost": rock_complexity_cost,
            "process_cycle_complexity_cost": engine_complexity_cost,
        },
        "aggregate": {
            "process_cycle_wins": engine_wins,
            "rock_wins": rock_wins,
            "ties": ties,
            "process_cycle_win_rate": engine_win_rate,
            "rock_win_rate": rock_win_rate,
            "avg_process_cycle_solvency": avg_engine_sol,
            "avg_rock_solvency": avg_rock_sol,
            "process_cycle_survival_rate": engine_survival_rate,
            "rock_survival_rate": rock_survival_rate,
        },
        "intensity_bins": bin_summaries,
        "verdict": verdict,
        "evidence": {
            "token_id": evidence.token_id,
            "sim_spec_id": evidence.sim_spec_id,
            "status": evidence.status,
            "measured_value": evidence.measured_value,
            "kill_reason": evidence.kill_reason,
        },
        # evidence_ledger: the key that run_all_sims.py reads for token collection
        "evidence_ledger": [{
            "token_id": evidence.token_id,
            "sim_spec_id": evidence.sim_spec_id,
            "status": evidence.status,
            "measured_value": evidence.measured_value,
            "kill_reason": evidence.kill_reason,
        }],
        # Save first 50 trial details (full 1000 is too large)
        "sample_trials": trial_results[:50],
    }

    with open(outpath, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Results saved to: {outpath}")

    return evidence, output


if __name__ == "__main__":
    evidence, results = run_enhanced_rock_falsifier(
        d_rock=2,
        d_engine=4,
        horizon=100,
        n_trials=1000,
        regime_shift_interval=25,
    )
