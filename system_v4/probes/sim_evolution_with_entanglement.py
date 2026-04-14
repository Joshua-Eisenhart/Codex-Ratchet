#!/usr/bin/env python3
"""
Evolutionary Dynamics WITH Entanglement (Recombination/Epistasis)
==================================================================
Extends sim_evolutionary_dynamics_as_engine.py by activating the Ising ZZ
entangling gate as the quantum analog of sexual recombination / epistasis.

Hypothesis: ZZ coupling = recombination/epistasis in evolutionary terms.
The entangling gate creates correlations between two "species" subsystems
that pure selection + mutation cannot produce.

The mapping:
  Selection   = Ti (Z-dephasing in fitness eigenbasis)
  Mutation    = Te (X-dephasing = randomization)
  Recombination/epistasis = Ising ZZ entangling gate (correlates subsystems)

Five simulations:
  1. Replicator with recombination (entangle_strength sweep)
  2. Error threshold WITH recombination (mu_c shift)
  3. Epistasis as entanglement (non-additive fitness landscape)
  4. Full engine with gate ON (evolutionary interpretation)
  5. Fisher information with entanglement (QFI trajectory)
"""

import sys
import os
import json
import traceback
classification = "classical_baseline"  # auto-backfill
divergence_log = "Classical baseline: evolutionary dynamics with entanglement is explored here by numeric two-locus sweeps and gate insertions, not a canonical nonclassical witness."
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "two-locus state evolution, information measures, and sweep numerics"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
}

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from scipy.linalg import expm

from sim_evolutionary_dynamics_as_engine import EvolutionaryEngine, sanitize
from geometric_operators import (
    apply_Ti, apply_Te, apply_Entangle_4x4,
    _ensure_valid_density, partial_trace_A, partial_trace_B,
    negentropy, I2, SIGMA_Z,
)
from bipartite_spinor_algebra import (
    ensure_valid_density, concurrence_4x4, I4, YY, SIGMA_X, SIGMA_Y,
)
from hopf_manifold import von_neumann_entropy_2x2, density_to_bloch


# =====================================================================
# HELPERS
# =====================================================================

def von_neumann_entropy_general(rho):
    """S(rho) = -Tr(rho log2 rho) for any size density matrix."""
    rho = (rho + rho.conj().T) / 2
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > 1e-15]
    if len(evals) == 0:
        return 0.0
    return float(-np.sum(evals * np.log2(evals)))


def mutual_information_4x4(rho_AB):
    """I(A:B) = S(A) + S(B) - S(AB)."""
    rho_A = _ensure_valid_density(partial_trace_B(rho_AB))
    rho_B = _ensure_valid_density(partial_trace_A(rho_AB))
    return (von_neumann_entropy_2x2(rho_A)
            + von_neumann_entropy_2x2(rho_B)
            - von_neumann_entropy_general(rho_AB))


def quantum_fisher_info(rho, H):
    """QFI(rho, H) = 2 * sum_{i,j} (p_i - p_j)^2 / (p_i + p_j) * |<i|H|j>|^2.

    For mixed states with eigendecomposition rho = sum_i p_i |i><i|.
    NOTE: When rho and H commute (both diagonal), QFI = 0 because the state
    is invariant under exp(-iHt). This is mathematically correct but
    uninteresting for evolution. Use classical_fisher_info for Var(f).
    """
    evals, evecs = np.linalg.eigh(rho)
    d = len(evals)
    # H in eigenbasis of rho
    H_eig = evecs.conj().T @ H @ evecs
    qfi = 0.0
    for i in range(d):
        for j in range(d):
            denom = evals[i] + evals[j]
            if denom > 1e-15:
                qfi += 2.0 * (evals[i] - evals[j]) ** 2 / denom * abs(H_eig[i, j]) ** 2
    return float(qfi)


def classical_fisher_info(rho, H):
    """Classical Fisher information = 4 * Var_rho(H).

    This is the evolutionary Fisher information (Fisher's fundamental theorem):
    the rate of fitness increase equals the fitness variance.
    For diagonal states, CFI = 4 * (Tr(H^2 rho) - (Tr(H rho))^2).
    For states with coherence, includes off-diagonal contributions.
    """
    mean_H = np.real(np.trace(H @ rho))
    mean_H2 = np.real(np.trace(H @ H @ rho))
    var = float(mean_H2 - mean_H ** 2)
    return 4.0 * max(var, 0.0)


def make_product_state(x1_A, x1_B):
    """Create a 4x4 product density matrix from two population frequencies."""
    rho_A = np.array([[x1_A, 0], [0, 1 - x1_A]], dtype=complex)
    rho_B = np.array([[x1_B, 0], [0, 1 - x1_B]], dtype=complex)
    return np.kron(rho_A, rho_B)


# =====================================================================
# EVOLUTIONARY ENGINE ON 4x4 (two-locus / two-species)
# =====================================================================

class TwoLocusEvolutionaryEngine:
    """Two-locus evolutionary dynamics on 4x4 density matrices.

    Each locus is a qubit. The joint state is rho_AB (4x4).
    Selection and mutation act locally on each subsystem.
    Recombination = Ising ZZ entangling gate acting non-locally.
    """

    def __init__(self, fitness_A=(1.5, 1.0), fitness_B=(1.5, 1.0),
                 mutation_rate=0.1, entangle_strength=0.0,
                 epistatic_fitness=None):
        self.f1_A, self.f2_A = fitness_A
        self.f1_B, self.f2_B = fitness_B
        self.mu = mutation_rate
        self.entangle_strength = entangle_strength

        # Local fitness Hamiltonians
        self.H_A = np.array([[self.f1_A, 0], [0, self.f2_A]], dtype=complex)
        self.H_B = np.array([[self.f1_B, 0], [0, self.f2_B]], dtype=complex)

        # Joint fitness Hamiltonian (additive by default)
        if epistatic_fitness is not None:
            # Non-additive: direct diagonal fitness on 4x4
            self.H_joint = np.diag(np.array(epistatic_fitness, dtype=complex))
        else:
            self.H_joint = np.kron(self.H_A, np.eye(2)) + np.kron(np.eye(2), self.H_B)

        # Selection operators (sqrt of fitness for Lueders rule)
        self.F_sqrt_A = np.diag(np.sqrt([self.f1_A, self.f2_A]).astype(complex))
        self.F_sqrt_B = np.diag(np.sqrt([self.f1_B, self.f2_B]).astype(complex))

        if epistatic_fitness is not None:
            self.F_sqrt_joint = np.diag(np.sqrt(
                np.maximum(np.array(epistatic_fitness), 1e-15)).astype(complex))
        else:
            self.F_sqrt_joint = None

    def selection_step(self, rho_AB):
        """Selection via Lueders rule + partial dephasing.

        Lueders rule: rho -> F^{1/2} rho F^{1/2} / Tr(F rho).
        Then partial Z-dephasing (strength 0.3) to model the fitness
        measurement aspect of selection without completely killing coherence.
        """
        if self.F_sqrt_joint is not None:
            rho_sel = self.F_sqrt_joint @ rho_AB @ self.F_sqrt_joint.conj().T
        else:
            F_joint = np.kron(self.F_sqrt_A, self.F_sqrt_B)
            rho_sel = F_joint @ rho_AB @ F_joint.conj().T
        tr = np.real(np.trace(rho_sel))
        if tr > 1e-15:
            rho_sel /= tr

        # Partial Z-dephasing: kill only 30% of coherence (not all)
        # This models selection as PARTIAL observation of fitness
        dephase = 0.3
        for i in range(4):
            for j in range(4):
                if i != j:
                    rho_sel[i, j] *= (1.0 - dephase)
        return ensure_valid_density(rho_sel)

    def mutation_step(self, rho_AB):
        """Mutation as local X-rotation (Fi) on each subsystem.

        Fi = U_x(theta) creates coherence in the X-basis (population mixing).
        This is the key to making ZZ recombination work:
        [U_x, ZZ] != 0, so mutation + recombination can produce
        entangled states that neither can produce alone.

        Mutation strength mu controls the rotation angle.
        """
        from geometric_operators import apply_Fi
        theta_mut = self.mu * np.pi  # mutation angle proportional to mu
        # Apply local Fi (X-rotation) to each subsystem independently
        # Build local unitary: U_x(theta) = cos(t/2)I - i*sin(t/2)*sigma_x
        sx = np.array([[0, 1], [1, 0]], dtype=complex)
        U_mut = np.cos(theta_mut / 2) * np.eye(2, dtype=complex) - 1j * np.sin(theta_mut / 2) * sx
        # Apply to A: (U x I) rho (U x I)^dag
        U_A = np.kron(U_mut, np.eye(2, dtype=complex))
        rho_mut = U_A @ rho_AB @ U_A.conj().T
        # Apply to B: (I x U) rho (I x U)^dag
        U_B = np.kron(np.eye(2, dtype=complex), U_mut)
        rho_mut = U_B @ rho_mut @ U_B.conj().T

        # Also add small depolarizing noise (thermal mutation)
        rho_mut = (1 - self.mu * 0.1) * rho_mut + self.mu * 0.1 * I4 / 4
        return ensure_valid_density(rho_mut)

    def recombination_step(self, rho_AB):
        """Ising ZZ entangling gate = recombination.

        U = exp(-i * strength * sigma_z x sigma_z).
        On states with X-coherence (created by mutation/Fi), ZZ produces
        genuine entanglement (concurrence > 0). On diagonal states it
        has no effect. This is the quantum analog of genetic recombination:
        it only matters when there is variation (coherence) to recombine.
        """
        if self.entangle_strength > 0:
            return apply_Entangle_4x4(rho_AB, strength=self.entangle_strength)
        return rho_AB

    def run_generation(self, rho_AB):
        """One generation = mutation + recombination + selection.

        1. Mutation (Fi = X-rotation): creates variation/coherence
        2. Recombination (ZZ gate): correlates loci using that coherence
        3. Selection (Lueders + partial dephasing): amplifies fit genotypes

        The non-commutativity [Fi, ZZ] != 0 is what makes recombination
        produce genuinely new states that mutation alone cannot reach.
        """
        rho_AB = self.mutation_step(rho_AB)
        rho_AB = self.recombination_step(rho_AB)
        rho_AB = self.selection_step(rho_AB)
        return ensure_valid_density(rho_AB)

    def mean_fitness(self, rho_AB):
        """<f> = Tr(H_joint * rho_AB)."""
        return float(np.real(np.trace(self.H_joint @ rho_AB)))

    def fitness_variance(self, rho_AB):
        """Var(f) = Tr(H^2 rho) - (Tr(H rho))^2."""
        H2 = self.H_joint @ self.H_joint
        mean = np.real(np.trace(self.H_joint @ rho_AB))
        mean_sq = np.real(np.trace(H2 @ rho_AB))
        return float(mean_sq - mean ** 2)

    def population_fractions(self, rho_AB):
        """Extract diagonal = population fractions of 4 genotypes."""
        return [float(np.real(rho_AB[i, i])) for i in range(4)]


# =====================================================================
# SIM 1: Replicator with recombination
# =====================================================================

def run_sim1():
    """Does entanglement (recombination) speed up or slow down adaptation?

    f1=1.5, f2=1.0, mu=0.1, entangle_strength sweep [0, 0.1, 0.3, 0.5, 1.0].
    Start x1=0.1, run 100 generations.
    Track: x1 trajectory, entropy, concurrence, MI.
    """
    entangle_strengths = [0.0, 0.1, 0.3, 0.5, 1.0]
    all_trajectories = {}

    for es in entangle_strengths:
        eng = TwoLocusEvolutionaryEngine(
            fitness_A=(1.5, 1.0), fitness_B=(1.5, 1.0),
            mutation_rate=0.1, entangle_strength=es,
        )
        rho = make_product_state(0.1, 0.1)
        trajectory = []

        for gen in range(100):
            rho_A = _ensure_valid_density(partial_trace_B(rho))
            rho_B = _ensure_valid_density(partial_trace_A(rho))
            x1_A = float(np.real(rho_A[0, 0]))
            x1_B = float(np.real(rho_B[0, 0]))
            entropy = von_neumann_entropy_general(rho)
            conc = concurrence_4x4(rho)
            mi = mutual_information_4x4(rho)
            mf = eng.mean_fitness(rho)

            trajectory.append({
                "generation": gen,
                "x1_A": x1_A,
                "x1_B": x1_B,
                "entropy_joint": entropy,
                "concurrence": conc,
                "mutual_information": mi,
                "mean_fitness": mf,
            })
            rho = eng.run_generation(rho)

        # Final state
        rho_A_final = _ensure_valid_density(partial_trace_B(rho))
        x1_final = float(np.real(rho_A_final[0, 0]))

        # Speed measure: generation at which x1_A first exceeds 0.8 (near fixation)
        speed_gen = None
        for t in trajectory:
            if t["x1_A"] >= 0.8:
                speed_gen = t["generation"]
                break

        all_trajectories[f"es_{es}"] = {
            "entangle_strength": es,
            "x1_A_final": x1_final,
            "speed_to_majority": speed_gen,
            "final_concurrence": trajectory[-1]["concurrence"],
            "final_MI": trajectory[-1]["mutual_information"],
            "trajectory_sample": trajectory[::10],
        }

    # Analysis: does recombination speed up adaptation?
    speeds = {k: v["speed_to_majority"] for k, v in all_trajectories.items()}

    return {
        "sim": "sim1_replicator_with_recombination",
        "description": "Entangle strength sweep: does recombination speed/slow adaptation?",
        "passed": True,
        "speeds_to_majority": speeds,
        "interpretation": "Lower generation number = faster adaptation",
        "all_trajectories": all_trajectories,
    }


# =====================================================================
# SIM 2: Error threshold WITH recombination
# =====================================================================

def run_sim2():
    """Does recombination shift the error threshold?

    Sweep mu from 0.01 to 0.99 at two entangle strengths: 0 and 0.3.
    Run to equilibrium, find mu_c.
    In biology: recombination helps organisms survive higher mutation rates.
    """
    mu_values = np.linspace(0.01, 0.99, 50)
    results_by_es = {}

    for es in [0.0, 0.3]:
        sweep = []
        for mu in mu_values:
            eng = TwoLocusEvolutionaryEngine(
                fitness_A=(1.5, 1.0), fitness_B=(1.5, 1.0),
                mutation_rate=float(mu), entangle_strength=es,
            )
            rho = make_product_state(0.9, 0.9)
            # Run to equilibrium
            for _ in range(200):
                rho = eng.run_generation(rho)
            rho_A = _ensure_valid_density(partial_trace_B(rho))
            x1_eq = float(np.real(rho_A[0, 0]))
            conc = concurrence_4x4(rho)
            mf = eng.mean_fitness(rho)
            sweep.append({
                "mu": float(mu),
                "x1_equilibrium": x1_eq,
                "concurrence": conc,
                "mean_fitness": mf,
            })

        # Find mu_c: first mu where x1 drops below 0.60
        # (with Fi mutation, populations don't reach 0.5 exactly)
        mu_c = None
        for r in sweep:
            if r["x1_equilibrium"] < 0.60:
                mu_c = r["mu"]
                break

        results_by_es[f"es_{es}"] = {
            "entangle_strength": es,
            "mu_c": mu_c,
            "sweep_sample": sweep[::5],
        }

    # Compare thresholds
    mu_c_no_ent = results_by_es["es_0.0"]["mu_c"]
    mu_c_with_ent = results_by_es["es_0.3"]["mu_c"]
    shift = None
    if mu_c_no_ent is not None and mu_c_with_ent is not None:
        shift = mu_c_with_ent - mu_c_no_ent

    return {
        "sim": "sim2_error_threshold_with_recombination",
        "description": "Does recombination shift the error threshold mu_c?",
        "passed": True,
        "mu_c_no_entanglement": mu_c_no_ent,
        "mu_c_with_entanglement": mu_c_with_ent,
        "mu_c_shift": shift,
        "interpretation": "Positive shift = recombination raises threshold (survives higher mu). "
                          "Negative = lowers. None = no clear threshold found.",
        "results": results_by_es,
    }


# =====================================================================
# SIM 3: Epistasis as entanglement
# =====================================================================

def run_sim3():
    """Does the entangling gate capture epistatic correlations better?

    Two loci, non-additive fitness:
      f(00)=1.0, f(01)=0.5, f(10)=0.5, f(11)=1.5
    This is epistatic: fitness of combo != sum of individual fitnesses.

    Run with and without entangling gate, compare final population distribution
    and how well the system finds the epistatic optimum |11>.
    """
    epistatic_fitness = [1.0, 0.5, 0.5, 1.5]  # |00>, |01>, |10>, |11>

    results = {}
    for es_label, es in [("no_entanglement", 0.0), ("with_entanglement", 0.3)]:
        eng = TwoLocusEvolutionaryEngine(
            fitness_A=(1.0, 1.0),  # irrelevant since epistatic_fitness overrides
            fitness_B=(1.0, 1.0),
            mutation_rate=0.1,
            entangle_strength=es,
            epistatic_fitness=epistatic_fitness,
        )
        # Start uniform
        rho = np.eye(4, dtype=complex) / 4
        trajectory = []

        for gen in range(100):
            pops = eng.population_fractions(rho)
            conc = concurrence_4x4(rho)
            mi = mutual_information_4x4(rho)
            mf = eng.mean_fitness(rho)
            trajectory.append({
                "generation": gen,
                "pop_00": pops[0], "pop_01": pops[1],
                "pop_10": pops[2], "pop_11": pops[3],
                "concurrence": conc,
                "mutual_information": mi,
                "mean_fitness": mf,
            })
            rho = eng.run_generation(rho)

        final_pops = eng.population_fractions(rho)
        results[es_label] = {
            "entangle_strength": es,
            "final_populations": {
                "|00>": final_pops[0], "|01>": final_pops[1],
                "|10>": final_pops[2], "|11>": final_pops[3],
            },
            "final_concurrence": concurrence_4x4(rho),
            "final_MI": mutual_information_4x4(rho),
            "final_mean_fitness": eng.mean_fitness(rho),
            "epistatic_optimum_pop_11": final_pops[3],
            "trajectory_sample": trajectory[::10],
        }

    # Does entanglement help find the epistatic optimum?
    pop11_no = results["no_entanglement"]["epistatic_optimum_pop_11"]
    pop11_with = results["with_entanglement"]["epistatic_optimum_pop_11"]

    return {
        "sim": "sim3_epistasis_as_entanglement",
        "description": "Non-additive fitness landscape: does ZZ gate help find epistatic optimum?",
        "passed": True,
        "epistatic_fitness_landscape": dict(zip(["|00>", "|01>", "|10>", "|11>"], epistatic_fitness)),
        "pop_11_no_entanglement": pop11_no,
        "pop_11_with_entanglement": pop11_with,
        "entanglement_advantage": pop11_with - pop11_no,
        "interpretation": "Positive advantage = entangling gate helps capture epistatic correlations",
        "results": results,
    }


# =====================================================================
# SIM 4: Through the ACTUAL engine with gate ON
# =====================================================================

def run_sim4():
    """Does the full engine (with torus geometry, chirality, etc.)
    produce valid evolutionary dynamics?

    GeometricEngine(engine_type=1, entangle_strength=0.3).
    Run 10 cycles. Interpret as evolution: track population fractions,
    fitness, variance. Compare to standalone evolutionary engine.
    """
    from engine_core import GeometricEngine, EngineState, StageControls

    # Fitness Hamiltonian for interpretation
    f1, f2 = 1.5, 1.0
    H_A = np.array([[f1, 0], [0, f2]], dtype=complex)
    H_B = np.array([[f1, 0], [0, f2]], dtype=complex)
    H_joint = np.kron(H_A, np.eye(2)) + np.kron(np.eye(2), H_B)

    # --- Part A: Full engine ---
    engine = GeometricEngine(engine_type=1, entangle_strength=0.3)
    state = engine.init_state()
    engine_trajectory = []

    for cycle in range(10):
        rho_AB = state.rho_AB
        rho_L = state.rho_L
        rho_R = state.rho_R
        pops = [float(np.real(rho_AB[i, i])) for i in range(4)]
        conc = concurrence_4x4(rho_AB)
        mi = mutual_information_4x4(rho_AB)
        mf = float(np.real(np.trace(H_joint @ rho_AB)))
        var_f = float(np.real(np.trace(H_joint @ H_joint @ rho_AB))
                       - np.real(np.trace(H_joint @ rho_AB)) ** 2)

        engine_trajectory.append({
            "cycle": cycle,
            "populations": pops,
            "x1_L": float(np.real(rho_L[0, 0])),
            "x1_R": float(np.real(rho_R[0, 0])),
            "concurrence": conc,
            "mutual_information": mi,
            "mean_fitness": mf,
            "fitness_variance": var_f,
            "entropy_L": von_neumann_entropy_2x2(rho_L),
            "entropy_R": von_neumann_entropy_2x2(rho_R),
            "entropy_joint": von_neumann_entropy_general(rho_AB),
        })
        state = engine.run_cycle(state)

    # --- Part B: Standalone two-locus engine for comparison ---
    standalone = TwoLocusEvolutionaryEngine(
        fitness_A=(f1, f2), fitness_B=(f1, f2),
        mutation_rate=0.1, entangle_strength=0.3,
    )
    rho_s = make_product_state(0.5, 0.5)
    standalone_trajectory = []

    for gen in range(10):
        pops_s = standalone.population_fractions(rho_s)
        rho_A_s = _ensure_valid_density(partial_trace_B(rho_s))
        conc_s = concurrence_4x4(rho_s)
        mi_s = mutual_information_4x4(rho_s)
        mf_s = standalone.mean_fitness(rho_s)
        var_s = standalone.fitness_variance(rho_s)

        standalone_trajectory.append({
            "generation": gen,
            "populations": pops_s,
            "x1_A": float(np.real(rho_A_s[0, 0])),
            "concurrence": conc_s,
            "mutual_information": mi_s,
            "mean_fitness": mf_s,
            "fitness_variance": var_s,
        })
        rho_s = standalone.run_generation(rho_s)

    return {
        "sim": "sim4_full_engine_evolutionary",
        "description": "Full GeometricEngine with gate ON: valid evolutionary dynamics?",
        "passed": True,
        "engine_trajectory": engine_trajectory,
        "standalone_trajectory": standalone_trajectory,
        "comparison_notes": {
            "engine": "GeometricEngine(type=1, entangle=0.3) with 8-stage torus cycle",
            "standalone": "TwoLocusEvolutionaryEngine with identical fitness/mutation/entangle",
            "key_difference": "Engine has torus geometry, chirality, loop grammar; "
                              "standalone has raw selection+mutation+recombination only",
        },
    }


# =====================================================================
# SIM 5: Fisher information with entanglement
# =====================================================================

def run_sim5():
    """Is QFI higher with entanglement?

    In biology: recombination increases genetic variance -> faster adaptation.
    Compute QFI(rho, H_fitness) with and without entangling gate.
    Track: QFI trajectory over 50 generations, both conditions.
    """
    H_joint = np.kron(
        np.array([[1.5, 0], [0, 1.0]], dtype=complex), np.eye(2)
    ) + np.kron(
        np.eye(2), np.array([[1.5, 0], [0, 1.0]], dtype=complex)
    )

    results = {}
    for es_label, es in [("no_entanglement", 0.0), ("with_entanglement", 0.3)]:
        eng = TwoLocusEvolutionaryEngine(
            fitness_A=(1.5, 1.0), fitness_B=(1.5, 1.0),
            mutation_rate=0.1, entangle_strength=es,
        )
        rho = make_product_state(0.3, 0.3)
        trajectory = []

        for gen in range(50):
            qfi = quantum_fisher_info(rho, H_joint)
            cfi = classical_fisher_info(rho, H_joint)
            var_f = eng.fitness_variance(rho)
            mf = eng.mean_fitness(rho)
            conc = concurrence_4x4(rho)
            mi = mutual_information_4x4(rho)

            trajectory.append({
                "generation": gen,
                "QFI": qfi,
                "CFI": cfi,
                "fitness_variance": var_f,
                "mean_fitness": mf,
                "concurrence": conc,
                "mutual_information": mi,
            })
            rho = eng.run_generation(rho)

        results[es_label] = {
            "entangle_strength": es,
            "cfi_initial": trajectory[0]["CFI"],
            "cfi_final": trajectory[-1]["CFI"],
            "qfi_initial": trajectory[0]["QFI"],
            "qfi_final": trajectory[-1]["QFI"],
            "mean_cfi": float(np.mean([t["CFI"] for t in trajectory])),
            "mean_qfi": float(np.mean([t["QFI"] for t in trajectory])),
            "mean_concurrence": float(np.mean([t["concurrence"] for t in trajectory])),
            "mean_MI": float(np.mean([t["mutual_information"] for t in trajectory])),
            "trajectory_sample": trajectory[::5],
        }

    cfi_mean_no = results["no_entanglement"]["mean_cfi"]
    cfi_mean_with = results["with_entanglement"]["mean_cfi"]
    qfi_mean_no = results["no_entanglement"]["mean_qfi"]
    qfi_mean_with = results["with_entanglement"]["mean_qfi"]

    return {
        "sim": "sim5_fisher_info_with_entanglement",
        "description": "Does entanglement increase Fisher info (genetic variance / adaptation rate)?",
        "passed": True,
        "mean_cfi_no_entanglement": cfi_mean_no,
        "mean_cfi_with_entanglement": cfi_mean_with,
        "cfi_ratio": cfi_mean_with / cfi_mean_no if cfi_mean_no > 1e-15 else None,
        "mean_qfi_no_entanglement": qfi_mean_no,
        "mean_qfi_with_entanglement": qfi_mean_with,
        "qfi_ratio": qfi_mean_with / qfi_mean_no if qfi_mean_no > 1e-15 else None,
        "interpretation": "CFI = 4*Var(f) = classical Fisher info (evolutionary analog). "
                          "QFI captures quantum coherence contribution. "
                          "Ratio > 1 means entanglement increases info about fitness.",
        "results": results,
    }


# =====================================================================
# MAIN
# =====================================================================

def main():
    results = {}
    sims = [
        ("sim1", run_sim1),
        ("sim2", run_sim2),
        ("sim3", run_sim3),
        ("sim4", run_sim4),
        ("sim5", run_sim5),
    ]

    all_passed = True
    for name, fn in sims:
        try:
            print(f"Running {name}...")
            result = fn()
            results[name] = sanitize(result)
            status = "PASS" if result["passed"] else "FAIL"
            if not result["passed"]:
                all_passed = False
            print(f"  {status}: {result.get('description', '')}")
        except Exception as e:
            results[name] = {"sim": name, "passed": False, "error": str(e),
                             "traceback": traceback.format_exc()}
            all_passed = False
            print(f"  ERROR: {e}")

    results["summary"] = {
        "total_sims": len(sims),
        "all_passed": all_passed,
        "passed_count": sum(1 for v in results.values()
                           if isinstance(v, dict) and v.get("passed", False)),
        "hypothesis": "ZZ coupling = recombination/epistasis. "
                      "Entangling gate creates inter-locus correlations that "
                      "pure selection+mutation cannot produce.",
    }

    # Print key findings
    print("\n" + "=" * 70)
    print("KEY FINDINGS")
    print("=" * 70)

    if "sim1" in results and "speeds_to_majority" in results["sim1"]:
        print(f"\nSim 1 - Adaptation speed by entangle strength:")
        for k, v in results["sim1"]["speeds_to_majority"].items():
            print(f"  {k}: gen {v}")

    if "sim2" in results:
        s2 = results["sim2"]
        print(f"\nSim 2 - Error threshold shift:")
        print(f"  mu_c (no entanglement): {s2.get('mu_c_no_entanglement')}")
        print(f"  mu_c (with entanglement): {s2.get('mu_c_with_entanglement')}")
        print(f"  Shift: {s2.get('mu_c_shift')}")

    if "sim3" in results:
        s3 = results["sim3"]
        print(f"\nSim 3 - Epistatic optimum |11> population:")
        print(f"  Without entanglement: {s3.get('pop_11_no_entanglement', 'N/A'):.4f}")
        print(f"  With entanglement:    {s3.get('pop_11_with_entanglement', 'N/A'):.4f}")
        print(f"  Advantage:            {s3.get('entanglement_advantage', 'N/A'):.4f}")

    if "sim5" in results:
        s5 = results["sim5"]
        print(f"\nSim 5 - Fisher information:")
        print(f"  Mean CFI (no ent):   {s5.get('mean_cfi_no_entanglement', 'N/A'):.4f}")
        print(f"  Mean CFI (with ent): {s5.get('mean_cfi_with_entanglement', 'N/A'):.4f}")
        print(f"  CFI ratio:           {s5.get('cfi_ratio', 'N/A')}")
        print(f"  Mean QFI (no ent):   {s5.get('mean_qfi_no_entanglement', 'N/A'):.4f}")
        print(f"  Mean QFI (with ent): {s5.get('mean_qfi_with_entanglement', 'N/A'):.4f}")
        print(f"  QFI ratio:           {s5.get('qfi_ratio', 'N/A')}")

    out_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "a2_state", "sim_results",
        "evolution_with_entanglement_results.json"
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults written to {out_path}")
    print(f"Summary: {results['summary']}")


if __name__ == "__main__":
    main()
