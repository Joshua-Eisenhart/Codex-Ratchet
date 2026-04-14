#!/usr/bin/env python3
"""
Entropy Type Sweep — L0 through L3
====================================
Test EVERY entropy form at each base constraint layer.
The constraints FORCE which entropy types survive and which get killed.
Find out which entropy the constraints select — do not assume von Neumann.

Entropy types tested (17 total):
  Single-state (2x2):  von_neumann, shannon, renyi_0.5, renyi_2, renyi_10,
                        min_entropy, max_entropy, linear_entropy,
                        tsallis_0.5, tsallis_2, purity
  Joint-state (4x4):   conditional, mutual_information, coherent_information,
                        negativity, log_negativity, relative_entropy

Layers tested:
  L0: F01+N01 root constraints (finite, noncommuting)
  L1: Fences (canonical ordering vs scrambled)
  L2: Carrier (torus geometry sensitivity)
  L3: Connection (Berry phase / transport sensitivity)
"""

import sys
import os
import json
import numpy as np
from datetime import datetime
classification = "classical_baseline"  # auto-backfill
divergence_log = "Classical baseline: entropy-type survival across L0-L3 is explored here by numeric layer sweeps, not a canonical nonclassical witness."
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "entropy-family sweeps, layer comparisons, and operator-response numerics"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
}

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import (
    GeometricEngine, EngineState, StageControls,
    LOOP_STAGE_ORDER, TERRAINS,
)
from geometric_operators import (
    apply_Ti, apply_Fe, apply_Te, apply_Fi,
    partial_trace_A, partial_trace_B,
    _ensure_valid_density, I2, SIGMA_X, SIGMA_Y, SIGMA_Z,
    OPERATOR_MAP_4X4,
)
from hopf_manifold import (
    TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER,
    torus_coordinates, left_weyl_spinor, right_weyl_spinor,
    berry_phase, lifted_base_loop, inter_torus_transport,
)


# =====================================================================
# ENTROPY FUNCTIONS — ALL 17 TYPES
# =====================================================================

def von_neumann(rho):
    """S_vN(rho) = -Tr(rho log2 rho). Standard quantum entropy."""
    rho = (rho + rho.conj().T) / 2
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > 1e-15]
    if len(evals) == 0:
        return 0.0
    return float(-np.sum(evals * np.log2(evals)))


def shannon(rho):
    """H(p) = -sum p_i log2 p_i on diagonal (measurement in computational basis)."""
    probs = np.real(np.diag(rho))
    probs = probs[probs > 1e-15]
    if len(probs) == 0:
        return 0.0
    return float(-np.sum(probs * np.log2(probs)))


def renyi(rho, alpha):
    """S_alpha(rho) = 1/(1-alpha) log2 Tr(rho^alpha). Family parameterized by alpha."""
    if abs(alpha - 1.0) < 1e-10:
        return von_neumann(rho)
    rho = (rho + rho.conj().T) / 2
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > 1e-15]
    if len(evals) == 0:
        return 0.0
    return float(np.log2(np.sum(evals ** alpha)) / (1 - alpha))


def min_entropy(rho):
    """S_min(rho) = -log2 lambda_max. Renyi alpha -> inf."""
    rho = (rho + rho.conj().T) / 2
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > 1e-15]
    if len(evals) == 0:
        return 0.0
    return float(-np.log2(max(evals)))


def max_entropy(rho):
    """S_max(rho) = log2 rank(rho). Renyi alpha -> 0."""
    rho = (rho + rho.conj().T) / 2
    evals = np.linalg.eigvalsh(rho)
    rank = int(np.sum(evals > 1e-10))
    return float(np.log2(max(rank, 1)))


def linear_entropy(rho):
    """S_L(rho) = 1 - Tr(rho^2). Measures mixedness without log."""
    rho = (rho + rho.conj().T) / 2
    return float(1 - np.real(np.trace(rho @ rho)))


def tsallis(rho, q):
    """S_q(rho) = (1 - Tr(rho^q))/(q-1). Generalization."""
    if abs(q - 1.0) < 1e-10:
        return von_neumann(rho) * np.log(2)  # natural log version
    rho = (rho + rho.conj().T) / 2
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > 1e-15]
    if len(evals) == 0:
        return 0.0
    return float((1 - np.sum(evals ** q)) / (q - 1))


def purity(rho):
    """Tr(rho^2). Not entropy but related. 1=pure, 1/d=maximally mixed."""
    rho = (rho + rho.conj().T) / 2
    return float(np.real(np.trace(rho @ rho)))


def conditional_entropy(rho_AB, rho_B):
    """S(A|B) = S(AB) - S(B). Can be NEGATIVE for entangled states."""
    return von_neumann(rho_AB) - von_neumann(rho_B)


def mutual_information(rho_AB, rho_A, rho_B):
    """I(A:B) = S(A) + S(B) - S(AB). Always >= 0."""
    return von_neumann(rho_A) + von_neumann(rho_B) - von_neumann(rho_AB)


def coherent_information(rho_AB, rho_B):
    """I_c = S(B) - S(AB) = -S(A|B). Positive only for entangled states."""
    return von_neumann(rho_B) - von_neumann(rho_AB)


def relative_entropy(rho, sigma):
    """D(rho||sigma) = Tr(rho(log rho - log sigma)). Distinguishability."""
    rho = (rho + rho.conj().T) / 2
    sigma = (sigma + sigma.conj().T) / 2
    ev_r, U_r = np.linalg.eigh(rho)
    ev_s, U_s = np.linalg.eigh(sigma)
    ev_r = np.maximum(ev_r, 1e-15)
    ev_s = np.maximum(ev_s, 1e-15)
    log_rho = U_r @ np.diag(np.log2(ev_r)) @ U_r.conj().T
    log_sigma = U_s @ np.diag(np.log2(ev_s)) @ U_s.conj().T
    val = float(np.real(np.trace(rho @ (log_rho - log_sigma))))
    return max(val, 0.0)  # numerical floor


def negativity(rho_AB):
    """N(rho) = (||rho^{T_B}||_1 - 1)/2. Entanglement witness."""
    d = int(np.sqrt(rho_AB.shape[0]))
    rho_pt = rho_AB.reshape(d, d, d, d).transpose(0, 3, 2, 1).reshape(d * d, d * d)
    evals = np.linalg.eigvalsh(rho_pt)
    return float((np.sum(np.abs(evals)) - 1) / 2)


def log_negativity(rho_AB):
    """E_N = log2 ||rho^{T_B}||_1. Upper bound on distillable entanglement."""
    d = int(np.sqrt(rho_AB.shape[0]))
    rho_pt = rho_AB.reshape(d, d, d, d).transpose(0, 3, 2, 1).reshape(d * d, d * d)
    evals = np.linalg.eigvalsh(rho_pt)
    trace_norm = np.sum(np.abs(evals))
    return float(np.log2(max(trace_norm, 1.0)))


# =====================================================================
# ENTROPY COMPUTATION HELPERS
# =====================================================================

SINGLE_ENTROPY_NAMES = [
    "von_neumann", "shannon", "renyi_0.5", "renyi_2", "renyi_10",
    "min_entropy", "max_entropy", "linear_entropy",
    "tsallis_0.5", "tsallis_2", "purity",
]

JOINT_ENTROPY_NAMES = [
    "conditional", "mutual_information", "coherent_information",
    "negativity", "log_negativity", "relative_entropy",
]

ALL_ENTROPY_NAMES = SINGLE_ENTROPY_NAMES + JOINT_ENTROPY_NAMES


def compute_single_entropies(rho_2x2):
    """Compute all 11 single-state entropy measures on a 2x2 density matrix."""
    return {
        "von_neumann": von_neumann(rho_2x2),
        "shannon": shannon(rho_2x2),
        "renyi_0.5": renyi(rho_2x2, 0.5),
        "renyi_2": renyi(rho_2x2, 2.0),
        "renyi_10": renyi(rho_2x2, 10.0),
        "min_entropy": min_entropy(rho_2x2),
        "max_entropy": max_entropy(rho_2x2),
        "linear_entropy": linear_entropy(rho_2x2),
        "tsallis_0.5": tsallis(rho_2x2, 0.5),
        "tsallis_2": tsallis(rho_2x2, 2.0),
        "purity": purity(rho_2x2),
    }


def compute_joint_entropies(rho_AB, rho_A, rho_B):
    """Compute all 6 joint-state entropy measures on a 4x4 joint state."""
    d = rho_A.shape[0]
    sigma_mixed = np.eye(d, dtype=complex) / d
    return {
        "conditional": conditional_entropy(rho_AB, rho_B),
        "mutual_information": mutual_information(rho_AB, rho_A, rho_B),
        "coherent_information": coherent_information(rho_AB, rho_B),
        "negativity": negativity(rho_AB),
        "log_negativity": log_negativity(rho_AB),
        "relative_entropy": relative_entropy(rho_A, sigma_mixed),
    }


def compute_all_entropies(rho_AB):
    """Full entropy battery on a 4x4 joint state. Returns dict with all 17 types."""
    rho_A = _ensure_valid_density(partial_trace_B(rho_AB))
    rho_B = _ensure_valid_density(partial_trace_A(rho_AB))
    result = compute_single_entropies(rho_A)
    result.update(compute_joint_entropies(rho_AB, rho_A, rho_B))
    return result


# =====================================================================
# INITIAL STATES
# =====================================================================

def make_initial_states():
    """Three initial states for the sweep: |0>, |+>, I/2."""
    # |0> -- computational basis
    psi_0 = np.array([1.0, 0.0], dtype=complex)
    rho_0 = np.outer(psi_0, psi_0.conj())

    # |+> -- superposition
    psi_plus = np.array([1.0, 1.0], dtype=complex) / np.sqrt(2)
    rho_plus = np.outer(psi_plus, psi_plus.conj())

    # I/2 -- maximally mixed
    rho_mixed = np.eye(2, dtype=complex) / 2

    return {
        "|0>": rho_0,
        "|+>": rho_plus,
        "I/2": rho_mixed,
    }


def make_joint_from_2x2(rho_A, rho_B=None):
    """Build 4x4 joint product state from 2x2 marginals."""
    if rho_B is None:
        rho_B = rho_A.copy()
    return np.kron(rho_A, rho_B)


# =====================================================================
# L0: F01 + N01 ROOT CONSTRAINTS
# =====================================================================

def run_L0_sweep(engine, n_cycles=5):
    """L0: What entropies work on finite noncommuting systems?

    Tests:
      1. Three initial states through 5 engine cycles
      2. NEGATIVE: Break N01 (commuting operators)
      3. NEGATIVE: Break F01 (d=4 padded operators)
    """
    print("=" * 70)
    print("L0: F01+N01 ROOT CONSTRAINT ENTROPY SWEEP")
    print("=" * 70)

    results = {
        "trajectories_per_state": {},
        "N01_break_discrimination": {},
        "F01_break_discrimination": {},
        "ranking": [],
    }

    init_states = make_initial_states()

    # --- 1. CANONICAL: Run engine with proper constraints ---
    canonical_final_entropies = {}
    for state_name, rho_init in init_states.items():
        print(f"\n  State: {state_name}")
        trajectory = []

        # Build initial joint state
        rho_AB_init = make_joint_from_2x2(rho_init)

        # Initialize engine state at Clifford torus
        state = engine.init_state(eta=TORUS_CLIFFORD)
        state.rho_AB = _ensure_valid_density(rho_AB_init)

        for cycle in range(n_cycles):
            state = engine.run_cycle(state)
            entropies = compute_all_entropies(state.rho_AB)
            trajectory.append({"cycle": cycle, **entropies})
            print(f"    Cycle {cycle}: vN={entropies['von_neumann']:.4f}  "
                  f"MI={entropies['mutual_information']:.4f}  "
                  f"neg={entropies['negativity']:.4f}")

        results["trajectories_per_state"][state_name] = trajectory
        canonical_final_entropies[state_name] = trajectory[-1]

    # --- 2. NEGATIVE: Break N01 (commuting operators) ---
    # Replace Ti (sigma_z dephasing) and Fi (U_x rotation) with BOTH being
    # sigma_z dephasing. This makes Ti and Fi commute.
    print("\n  NEGATIVE: Breaking N01 (commuting operators)...")
    n01_break_entropies = {}
    for state_name, rho_init in init_states.items():
        rho_AB = make_joint_from_2x2(rho_init)

        # Manually apply 5 cycles of COMMUTING operators (all sigma_z based)
        for cycle in range(n_cycles):
            # Ti: sigma_z dephasing (canonical)
            P0_4 = np.kron(np.array([[1, 0], [0, 0]], dtype=complex),
                           np.array([[1, 0], [0, 0]], dtype=complex))
            P1_4 = np.kron(np.array([[0, 0], [0, 1]], dtype=complex),
                           np.array([[0, 0], [0, 1]], dtype=complex))
            P2_4 = np.kron(np.array([[1, 0], [0, 0]], dtype=complex),
                           np.array([[0, 0], [0, 1]], dtype=complex))
            P3_4 = np.kron(np.array([[0, 0], [0, 1]], dtype=complex),
                           np.array([[1, 0], [0, 0]], dtype=complex))
            rho_dephased = 0.5 * (P0_4 @ rho_AB @ P0_4 + P1_4 @ rho_AB @ P1_4 +
                                  P2_4 @ rho_AB @ P2_4 + P3_4 @ rho_AB @ P3_4) + 0.5 * rho_AB

            # Fe: U_z rotation (commutes with Ti since both are z-based)
            phi = 0.4
            Uz = np.array([[np.exp(-1j * phi / 2), 0],
                           [0, np.exp(1j * phi / 2)]], dtype=complex)
            Uz4 = np.kron(Uz, Uz.conj())
            rho_AB = _ensure_valid_density(Uz4 @ rho_dephased @ Uz4.conj().T)

            # Te: ALSO sigma_z dephasing (BREAKING N01 -- should be sigma_x)
            rho_AB = _ensure_valid_density(
                0.5 * (P0_4 @ rho_AB @ P0_4 + P1_4 @ rho_AB @ P1_4 +
                        P2_4 @ rho_AB @ P2_4 + P3_4 @ rho_AB @ P3_4) + 0.5 * rho_AB
            )

            # Fi: ALSO U_z rotation (BREAKING N01 -- should be U_x)
            rho_AB = _ensure_valid_density(Uz4 @ rho_AB @ Uz4.conj().T)

        n01_break_entropies[state_name] = compute_all_entropies(rho_AB)

    # --- 3. NEGATIVE: Break F01 (d=4 padded operators) ---
    # Embed 2x2 operators in 4x4 space (top-left block), breaking d=2 constraint
    print("  NEGATIVE: Breaking F01 (d=4 space, padded operators)...")
    f01_break_entropies = {}
    for state_name, rho_init in init_states.items():
        # Pad rho_init into 4x4 single-particle space (top-left block)
        rho_4 = np.zeros((4, 4), dtype=complex)
        rho_4[:2, :2] = rho_init
        # Ensure trace 1
        tr = np.real(np.trace(rho_4))
        if tr > 1e-15:
            rho_4 /= tr

        # Joint state is now 16x16 (two 4-dim subsystems)
        rho_AB = np.kron(rho_4, rho_4)

        for cycle in range(n_cycles):
            # Apply padded 4x4 versions of the operators
            # Ti: dephase in computational basis of 4-dim space
            projs = [np.zeros((4, 4), dtype=complex) for _ in range(4)]
            for k in range(4):
                projs[k][k, k] = 1.0
            rho_deph = sum(p @ rho_4 @ p for p in projs)
            rho_4 = _ensure_valid_density_Nd(0.5 * rho_deph + 0.5 * rho_4, 4)

            # Fe: U_z rotation padded (acts on first 2 dims only)
            phi = 0.4
            Uz = np.eye(4, dtype=complex)
            Uz[0, 0] = np.exp(-1j * phi / 2)
            Uz[1, 1] = np.exp(1j * phi / 2)
            rho_4 = _ensure_valid_density_Nd(Uz @ rho_4 @ Uz.conj().T, 4)

            # Te: sigma_x dephasing padded
            Q_plus_4 = np.zeros((4, 4), dtype=complex)
            Q_plus_4[:2, :2] = np.array([[1, 1], [1, 1]], dtype=complex) / 2
            Q_minus_4 = np.zeros((4, 4), dtype=complex)
            Q_minus_4[:2, :2] = np.array([[1, -1], [-1, 1]], dtype=complex) / 2
            rho_4 = _ensure_valid_density_Nd(
                0.5 * rho_4 + 0.5 * (Q_plus_4 @ rho_4 @ Q_plus_4 + Q_minus_4 @ rho_4 @ Q_minus_4), 4
            )

            # Fi: U_x rotation padded
            theta = 0.4
            Ux = np.eye(4, dtype=complex)
            Ux[:2, :2] = np.cos(theta / 2) * np.eye(2) - 1j * np.sin(theta / 2) * SIGMA_X
            rho_4 = _ensure_valid_density_Nd(Ux @ rho_4 @ Ux.conj().T, 4)

        # Compute entropies on the 4-dim single-particle state
        # (not the 16x16 joint -- compare apples to apples on reduced state)
        f01_break_entropies[state_name] = compute_single_entropies(rho_4[:2, :2])
        # Add dummy joint entropies for comparison
        for name in JOINT_ENTROPY_NAMES:
            f01_break_entropies[state_name][name] = 0.0

    # --- 4. COMPUTE DISCRIMINATION POWER ---
    for entropy_name in ALL_ENTROPY_NAMES:
        # N01 discrimination: average over initial states
        n01_diffs = []
        f01_diffs = []
        for state_name in init_states:
            canon = canonical_final_entropies[state_name].get(entropy_name, 0.0)
            n01_val = n01_break_entropies[state_name].get(entropy_name, 0.0)
            f01_val = f01_break_entropies[state_name].get(entropy_name, 0.0)

            denom_n01 = max(abs(canon), abs(n01_val), 1e-10)
            n01_diffs.append(abs(canon - n01_val) / denom_n01)

            denom_f01 = max(abs(canon), abs(f01_val), 1e-10)
            f01_diffs.append(abs(canon - f01_val) / denom_f01)

        results["N01_break_discrimination"][entropy_name] = float(np.mean(n01_diffs))
        results["F01_break_discrimination"][entropy_name] = float(np.mean(f01_diffs))

    # Combined discrimination = geometric mean of N01 and F01 discrimination
    combined = {}
    for name in ALL_ENTROPY_NAMES:
        n01_d = results["N01_break_discrimination"][name]
        f01_d = results["F01_break_discrimination"][name]
        combined[name] = float(np.sqrt(max(n01_d, 1e-15) * max(f01_d, 1e-15)))

    results["ranking"] = sorted(combined.keys(), key=lambda k: combined[k], reverse=True)

    print("\n  L0 DISCRIMINATION RANKING:")
    for i, name in enumerate(results["ranking"][:10]):
        print(f"    {i+1}. {name}: N01={results['N01_break_discrimination'][name]:.4f}  "
              f"F01={results['F01_break_discrimination'][name]:.4f}  "
              f"combined={combined[name]:.4f}")

    return results


def _ensure_valid_density_Nd(rho, d):
    """Enforce rho >= 0, Tr(rho) = 1, Hermitian for d-dimensional matrix."""
    rho = (rho + rho.conj().T) / 2
    evals, evecs = np.linalg.eigh(rho)
    evals = np.maximum(evals, 0)
    rho = evecs @ np.diag(evals.astype(complex)) @ evecs.conj().T
    tr = np.real(np.trace(rho))
    if tr > 1e-15:
        rho /= tr
    else:
        rho = np.eye(d, dtype=complex) / d
    return rho


# =====================================================================
# L1: FENCES — CANONICAL VS SCRAMBLED ORDERING
# =====================================================================

def run_L1_sweep(engine, n_cycles=5):
    """L1: Which entropies are sensitive to fence violations?

    Canonical ordering: LOOP_STAGE_ORDER (Carnot-grounded)
    Scrambled ordering: random permutation of the 8 stages
    """
    print("\n" + "=" * 70)
    print("L1: FENCE CONSTRAINT ENTROPY SWEEP")
    print("=" * 70)

    results = {
        "fence_discrimination": {},
        "canonical_entropies": {},
        "scrambled_entropies": {},
        "ranking": [],
    }

    # --- Canonical run ---
    print("  Running canonical (fences satisfied)...")
    state_canon = engine.init_state(eta=TORUS_CLIFFORD)
    for _ in range(n_cycles):
        state_canon = engine.run_cycle(state_canon)
    canonical_e = compute_all_entropies(state_canon.rho_AB)
    results["canonical_entropies"] = canonical_e

    # --- Scrambled run (fence-violating) ---
    # Instead of the proper loop order, we scramble the 8 terrain indices
    print("  Running scrambled (fences violated)...")
    rng = np.random.default_rng(99)
    scrambled_order = list(range(8))
    rng.shuffle(scrambled_order)
    print(f"    Scrambled order: {scrambled_order}")

    state_scrambled = engine.init_state(eta=TORUS_CLIFFORD)
    for _ in range(n_cycles):
        # Manually step through scrambled order
        for terrain_idx in scrambled_order:
            state_scrambled = engine.step(state_scrambled, stage_idx=terrain_idx)
    scrambled_e = compute_all_entropies(state_scrambled.rho_AB)
    results["scrambled_entropies"] = scrambled_e

    # --- Discrimination ---
    for name in ALL_ENTROPY_NAMES:
        canon_val = canonical_e.get(name, 0.0)
        scrambled_val = scrambled_e.get(name, 0.0)
        denom = max(abs(canon_val), abs(scrambled_val), 1e-10)
        results["fence_discrimination"][name] = float(abs(canon_val - scrambled_val) / denom)

    results["ranking"] = sorted(
        results["fence_discrimination"].keys(),
        key=lambda k: results["fence_discrimination"][k],
        reverse=True,
    )

    print("\n  L1 FENCE DISCRIMINATION RANKING:")
    for i, name in enumerate(results["ranking"][:10]):
        print(f"    {i+1}. {name}: power={results['fence_discrimination'][name]:.4f}")

    return results


# =====================================================================
# L2: CARRIER — TORUS GEOMETRY SENSITIVITY
# =====================================================================

def run_L2_sweep(engine, n_cycles=5):
    """L2: Which entropies are sensitive to torus geometry?

    Run at three eta values: TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER
    """
    print("\n" + "=" * 70)
    print("L2: CARRIER (TORUS GEOMETRY) ENTROPY SWEEP")
    print("=" * 70)

    eta_values = {
        "inner": TORUS_INNER,
        "clifford": TORUS_CLIFFORD,
        "outer": TORUS_OUTER,
    }

    results = {
        "geometry_sensitivity": {},
        "per_eta_entropies": {},
        "ranking": [],
    }

    for eta_name, eta_val in eta_values.items():
        print(f"  Running at eta={eta_name} ({eta_val:.4f})...")
        state = engine.init_state(eta=eta_val)

        # Set all stage controls to this torus
        controls = {i: StageControls(torus=eta_val) for i in range(8)}
        for _ in range(n_cycles):
            state = engine.run_cycle(state, controls=controls)

        entropies = compute_all_entropies(state.rho_AB)
        results["per_eta_entropies"][eta_name] = entropies
        print(f"    vN={entropies['von_neumann']:.4f}  MI={entropies['mutual_information']:.4f}")

    # --- Spread across eta values ---
    for name in ALL_ENTROPY_NAMES:
        vals = [results["per_eta_entropies"][k].get(name, 0.0) for k in eta_values]
        spread = max(vals) - min(vals)
        denom = max(abs(max(vals)), abs(min(vals)), 1e-10)
        results["geometry_sensitivity"][name] = float(spread / denom)

    results["ranking"] = sorted(
        results["geometry_sensitivity"].keys(),
        key=lambda k: results["geometry_sensitivity"][k],
        reverse=True,
    )

    print("\n  L2 GEOMETRY SENSITIVITY RANKING:")
    for i, name in enumerate(results["ranking"][:10]):
        print(f"    {i+1}. {name}: spread={results['geometry_sensitivity'][name]:.4f}")

    return results


# =====================================================================
# L3: CONNECTION — BERRY PHASE / TRANSPORT SENSITIVITY
# =====================================================================

def run_L3_sweep(engine, n_cycles=5):
    """L3: Which entropies are sensitive to Berry phase / transport?

    Normal: transport edges enabled (torus changes across stages)
    Locked: all stages locked to Clifford torus (no transport)
    """
    print("\n" + "=" * 70)
    print("L3: CONNECTION (TRANSPORT) ENTROPY SWEEP")
    print("=" * 70)

    results = {
        "transport_sensitivity": {},
        "normal_entropies": {},
        "locked_entropies": {},
        "ranking": [],
    }

    # --- Normal: transport across tori ---
    print("  Running with transport (torus cycling)...")
    state_transport = engine.init_state(eta=TORUS_CLIFFORD)

    # Cycle through inner -> clifford -> outer across stages
    torus_cycle = [TORUS_INNER, TORUS_INNER, TORUS_CLIFFORD, TORUS_CLIFFORD,
                   TORUS_OUTER, TORUS_OUTER, TORUS_CLIFFORD, TORUS_CLIFFORD]
    controls_transport = {i: StageControls(torus=torus_cycle[i]) for i in range(8)}
    for _ in range(n_cycles):
        state_transport = engine.run_cycle(state_transport, controls=controls_transport)
    transport_e = compute_all_entropies(state_transport.rho_AB)
    results["normal_entropies"] = transport_e

    # --- Locked: no transport ---
    print("  Running locked (no transport, Clifford only)...")
    state_locked = engine.init_state(eta=TORUS_CLIFFORD)
    controls_locked = {i: StageControls(torus=TORUS_CLIFFORD) for i in range(8)}
    for _ in range(n_cycles):
        state_locked = engine.run_cycle(state_locked, controls=controls_locked)
    locked_e = compute_all_entropies(state_locked.rho_AB)
    results["locked_entropies"] = locked_e

    # --- Discrimination ---
    for name in ALL_ENTROPY_NAMES:
        t_val = transport_e.get(name, 0.0)
        l_val = locked_e.get(name, 0.0)
        denom = max(abs(t_val), abs(l_val), 1e-10)
        results["transport_sensitivity"][name] = float(abs(t_val - l_val) / denom)

    results["ranking"] = sorted(
        results["transport_sensitivity"].keys(),
        key=lambda k: results["transport_sensitivity"][k],
        reverse=True,
    )

    print("\n  L3 TRANSPORT SENSITIVITY RANKING:")
    for i, name in enumerate(results["ranking"][:10]):
        print(f"    {i+1}. {name}: power={results['transport_sensitivity'][name]:.4f}")

    return results


# =====================================================================
# SUMMARY: CROSS-LAYER SURVIVAL ANALYSIS
# =====================================================================

def compute_summary(L0, L1, L2, L3):
    """Determine which entropies survive all layers vs get killed."""
    summary = {
        "survives_all_layers": [],
        "killed_at_L0": [],
        "killed_at_L1": [],
        "killed_at_L2": [],
        "killed_at_L3": [],
        "per_entropy_scores": {},
        "constraint_selected_entropy": "",
    }

    DISCRIMINATION_THRESHOLD = 0.01  # below this = cannot distinguish = killed

    for name in ALL_ENTROPY_NAMES:
        # Combine N01 and F01 discrimination at L0
        n01 = L0["N01_break_discrimination"].get(name, 0.0)
        f01 = L0["F01_break_discrimination"].get(name, 0.0)
        l0_power = float(np.sqrt(max(n01, 1e-15) * max(f01, 1e-15)))
        l1_power = L1["fence_discrimination"].get(name, 0.0)
        l2_power = L2["geometry_sensitivity"].get(name, 0.0)
        l3_power = L3["transport_sensitivity"].get(name, 0.0)

        total_score = l0_power + l1_power + l2_power + l3_power

        summary["per_entropy_scores"][name] = {
            "L0": l0_power,
            "L1": l1_power,
            "L2": l2_power,
            "L3": l3_power,
            "total": total_score,
        }

        survived = True
        if l0_power < DISCRIMINATION_THRESHOLD:
            summary["killed_at_L0"].append(name)
            survived = False
        if l1_power < DISCRIMINATION_THRESHOLD:
            summary["killed_at_L1"].append(name)
            survived = False
        if l2_power < DISCRIMINATION_THRESHOLD:
            summary["killed_at_L2"].append(name)
            survived = False
        if l3_power < DISCRIMINATION_THRESHOLD:
            summary["killed_at_L3"].append(name)
            survived = False

        if survived:
            summary["survives_all_layers"].append(name)

    # Winner = highest total score
    if summary["per_entropy_scores"]:
        winner = max(summary["per_entropy_scores"].keys(),
                     key=lambda k: summary["per_entropy_scores"][k]["total"])
        summary["constraint_selected_entropy"] = winner

    return summary


# =====================================================================
# SERIALIZATION HELPER
# =====================================================================

def sanitize_for_json(obj):
    """Recursively convert numpy types to Python natives for JSON serialization."""
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [sanitize_for_json(v) for v in obj]
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    elif isinstance(obj, complex):
        return {"re": float(obj.real), "im": float(obj.imag)}
    elif isinstance(obj, np.complexfloating):
        return {"re": float(obj.real), "im": float(obj.imag)}
    return obj


# =====================================================================
# MAIN
# =====================================================================

def main():
    print("ENTROPY TYPE SWEEP: L0-L3 CONSTRAINT LAYERS")
    print("Testing 17 entropy types across 4 constraint layers")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    engine = GeometricEngine(engine_type=1)

    L0 = run_L0_sweep(engine, n_cycles=5)
    L1 = run_L1_sweep(engine, n_cycles=5)
    L2 = run_L2_sweep(engine, n_cycles=5)
    L3 = run_L3_sweep(engine, n_cycles=5)

    summary = compute_summary(L0, L1, L2, L3)

    print("\n" + "=" * 70)
    print("CROSS-LAYER SUMMARY")
    print("=" * 70)
    print(f"\n  SURVIVES ALL LAYERS: {summary['survives_all_layers']}")
    print(f"  KILLED AT L0: {summary['killed_at_L0']}")
    print(f"  KILLED AT L1: {summary['killed_at_L1']}")
    print(f"  KILLED AT L2: {summary['killed_at_L2']}")
    print(f"  KILLED AT L3: {summary['killed_at_L3']}")
    print(f"\n  CONSTRAINT-SELECTED ENTROPY: {summary['constraint_selected_entropy']}")

    print("\n  FULL SCORES:")
    scores = summary["per_entropy_scores"]
    ranked = sorted(scores.keys(), key=lambda k: scores[k]["total"], reverse=True)
    for i, name in enumerate(ranked):
        s = scores[name]
        print(f"    {i+1:2d}. {name:25s}  L0={s['L0']:.4f}  L1={s['L1']:.4f}  "
              f"L2={s['L2']:.4f}  L3={s['L3']:.4f}  TOTAL={s['total']:.4f}")

    # --- Save results ---
    output = {
        "name": "entropy_type_sweep_L0_L3",
        "timestamp": datetime.now().isoformat(),
        "entropy_types_tested": ALL_ENTROPY_NAMES,
        "L0_results": L0,
        "L1_results": L1,
        "L2_results": L2,
        "L3_results": L3,
        "summary": summary,
    }

    output_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "a2_state", "sim_results", "entropy_type_sweep_L0_L3_results.json",
    )
    with open(output_path, "w") as f:
        json.dump(sanitize_for_json(output), f, indent=2)
    print(f"\n  Results saved to: {output_path}")

    return output


if __name__ == "__main__":
    main()
