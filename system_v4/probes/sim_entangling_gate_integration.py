#!/usr/bin/env python3
"""
Entangling Gate Integration Simulation
=======================================
The engine produces ZERO entanglement because it applies operators
independently to A and B subsystems (local channels cannot entangle).
This sim inserts genuine 2-qubit entangling gates from the Cartan/Weyl
chamber classification and tests whether the engine can then cross
the separability boundary.

From Cartan decomposition (KAK form):
  U = k1 . exp(i(c1 XX + c2 YY + c3 ZZ)) . k2
  Entangling when (c1,c2,c3) != (0,0,0)
  Special points:
    CNOT:   (pi/4, 0, 0)
    iSWAP:  (pi/4, pi/4, 0)
    SWAP:   (pi/4, pi/4, pi/4) -- NOT entangling
    sqSWAP: (pi/8, pi/8, pi/8)

Tests:
  1. Insert entangling gate into engine cycle
  2. Sweep entangling strength (threshold detection)
  3. Gate position within cycle
  4. Entanglement survival under dephasing
  5. Coherent information (I_c) trajectory
  6. Per-operator entanglement dynamics (build vs destroy)
"""

import sys
import os
import json
import warnings
import numpy as np
from scipy.linalg import expm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import GeometricEngine, StageControls, LOOP_STAGE_ORDER
from geometric_operators import (
    OPERATOR_MAP_4X4, partial_trace_A, partial_trace_B,
    _ensure_valid_density,
)
from bipartite_spinor_algebra import (
    SIGMA_X, SIGMA_Y, SIGMA_Z, I2, ensure_valid_density,
)

warnings.filterwarnings("ignore", category=RuntimeWarning)


# =====================================================================
# ENTANGLING GATES (Cartan / Weyl chamber)
# =====================================================================

def build_ising_xx(strength):
    """exp(-i * strength * sigma_x (x) sigma_x). Ising XX coupling."""
    H = np.kron(SIGMA_X, SIGMA_X)
    return expm(-1j * strength * H)


def build_ising_zz(strength):
    """exp(-i * strength * sigma_z (x) sigma_z). Ising ZZ coupling."""
    H = np.kron(SIGMA_Z, SIGMA_Z)
    return expm(-1j * strength * H)


def build_heisenberg(strength):
    """exp(-i * strength * (XX + YY + ZZ)). Isotropic Heisenberg coupling."""
    H = (np.kron(SIGMA_X, SIGMA_X)
         + np.kron(SIGMA_Y, SIGMA_Y)
         + np.kron(SIGMA_Z, SIGMA_Z))
    return expm(-1j * strength * H)


def build_cnot():
    """CNOT gate. Weyl coordinates (pi/4, 0, 0). Maximum single-shot entangler."""
    return np.array([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
        [0, 0, 1, 0],
    ], dtype=complex)


def build_partial_swap(t):
    """exp(-i * t * SWAP). At t=pi/4: sqrt(SWAP) -- entangling."""
    SWAP = np.array([
        [1, 0, 0, 0],
        [0, 0, 1, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
    ], dtype=complex)
    return expm(-1j * t * SWAP)


GATE_CATALOG = {
    "ising_xx":      lambda: build_ising_xx(np.pi / 4),
    "ising_zz":      lambda: build_ising_zz(np.pi / 4),
    "heisenberg":    lambda: build_heisenberg(np.pi / 8),
    "cnot":          build_cnot,
    "partial_swap":  lambda: build_partial_swap(np.pi / 4),
}


# =====================================================================
# MEASUREMENT FUNCTIONS (imported from deep entanglement sim style)
# =====================================================================

def vn_entropy(rho):
    """Von Neumann entropy S(rho) in bits."""
    rho = (rho + rho.conj().T) / 2
    evals = np.real(np.linalg.eigvalsh(rho))
    evals = evals[evals > 1e-15]
    if len(evals) == 0:
        return 0.0
    return float(-np.sum(evals * np.log2(evals)))


def concurrence(rho):
    """Wootters concurrence for a 2-qubit state."""
    sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
    sy_sy = np.kron(sy, sy)
    R = rho @ sy_sy @ rho.conj() @ sy_sy
    evals = sorted(np.sqrt(np.maximum(np.real(np.linalg.eigvals(R)), 0)),
                   reverse=True)
    return float(max(0, evals[0] - evals[1] - evals[2] - evals[3]))


def negativity(rho):
    """Negativity: (||rho^{T_B}||_1 - 1) / 2."""
    rho_pt = rho.reshape(2, 2, 2, 2).transpose(0, 3, 2, 1).reshape(4, 4)
    evals = np.linalg.eigvalsh(rho_pt)
    return float(max(0, (np.sum(np.abs(evals)) - 1) / 2))


def quantum_mutual_information(rho_AB, rho_A, rho_B):
    """I(A:B) = S(A) + S(B) - S(AB)."""
    return float(vn_entropy(rho_A) + vn_entropy(rho_B) - vn_entropy(rho_AB))


def coherent_information(rho_AB, rho_B):
    """I_c(A>B) = S(B) - S(AB)."""
    return float(vn_entropy(rho_B) - vn_entropy(rho_AB))


def chsh_value(rho):
    """Maximum CHSH value B_max = 2*sqrt(M1+M2) from correlation tensor."""
    sigmas = [SIGMA_X, SIGMA_Y, SIGMA_Z]
    T = np.zeros((3, 3))
    for i, si in enumerate(sigmas):
        for j, sj in enumerate(sigmas):
            T[i, j] = np.real(np.trace(rho @ np.kron(si, sj)))
    U = T.T @ T
    evals = sorted(np.real(np.linalg.eigvalsh(U)), reverse=True)
    return float(2 * np.sqrt(max(evals[0] + evals[1], 0)))


def quantum_discord(rho_AB, rho_A, rho_B):
    """Quantum discord D(A|B) = I(A:B) - J(A|B).
    J optimized over 10x10 Bloch sphere grid for speed.
    """
    MI = quantum_mutual_information(rho_AB, rho_A, rho_B)
    s_A = vn_entropy(rho_A)
    best_J = 0.0
    for theta in np.linspace(0, np.pi, 10):
        for phi in np.linspace(0, 2 * np.pi, 10):
            m0 = np.array([np.cos(theta / 2),
                           np.exp(1j * phi) * np.sin(theta / 2)])
            m1 = np.array([-np.exp(-1j * phi) * np.sin(theta / 2),
                           np.cos(theta / 2)])
            J = s_A
            for m in [m0, m1]:
                proj_B = np.outer(m, m.conj())
                proj_AB = np.kron(np.eye(2), proj_B)
                rho_post = proj_AB @ rho_AB @ proj_AB
                p = np.real(np.trace(rho_post))
                if p > 1e-15:
                    rho_A_cond = partial_trace_B(rho_post / p)
                    J -= p * vn_entropy(rho_A_cond)
            best_J = max(best_J, J)
    return float(MI - best_J)


def apply_unitary_gate(rho, U):
    """Apply a 4x4 unitary gate to a 4x4 density matrix."""
    rho_out = U @ rho @ U.conj().T
    return ensure_valid_density(rho_out)


def measure_all(rho):
    """Return dict of all key measures for a 4x4 state."""
    rho_A = partial_trace_B(rho)
    rho_B = partial_trace_A(rho)
    C = concurrence(rho)
    N = negativity(rho)
    MI = quantum_mutual_information(rho, rho_A, rho_B)
    Ic = coherent_information(rho, rho_B)
    B = chsh_value(rho)
    return {
        "concurrence": C,
        "negativity": N,
        "mutual_information": MI,
        "coherent_information": Ic,
        "chsh": B,
        "bell_violated": bool(B > 2.0),
    }


# =====================================================================
# TEST 1: Insert entangling gate into engine cycle
# =====================================================================

def test1_gate_in_cycle(n_cycles=10):
    """For each of 5 gates, run engine with gate inserted between Fe and Te
    (positions 1 and 2 in the 8-stage order). Measure at every step.
    """
    print("=" * 72)
    print("TEST 1: Insert entangling gate into engine cycle")
    print("=" * 72)

    results = {}

    for gate_name, gate_fn in GATE_CATALOG.items():
        U_gate = gate_fn()
        engine = GeometricEngine(engine_type=1)
        state = engine.init_state()
        stage_order = LOOP_STAGE_ORDER[engine.engine_type]

        trajectory = []
        for cycle in range(n_cycles):
            for pos, terrain_idx in enumerate(stage_order):
                # Apply engine step
                state = engine.step(state, stage_idx=terrain_idx)

                # Insert entangling gate after position 1 (after Fe in outer loop)
                if pos == 1:
                    state.rho_AB = apply_unitary_gate(state.rho_AB, U_gate)

                m = measure_all(state.rho_AB)
                m["cycle"] = cycle
                m["position"] = pos
                trajectory.append(m)

        max_C = max(t["concurrence"] for t in trajectory)
        max_N = max(t["negativity"] for t in trajectory)
        max_chsh = max(t["chsh"] for t in trajectory)
        any_bell = any(t["bell_violated"] for t in trajectory)
        crossed = max_C > 1e-6

        results[gate_name] = {
            "max_concurrence": max_C,
            "max_negativity": max_N,
            "max_chsh": max_chsh,
            "bell_violated": any_bell,
            "crossed_separability": crossed,
            "trajectory_length": len(trajectory),
            "final_concurrence": trajectory[-1]["concurrence"],
            "final_coherent_info": trajectory[-1]["coherent_information"],
        }
        print(f"  {gate_name:16s}: max_C={max_C:.6f}  max_N={max_N:.6f}  "
              f"CHSH={max_chsh:.4f}  Bell={'YES' if any_bell else 'no'}  "
              f"crossed={'YES' if crossed else 'no'}")

    return results


# =====================================================================
# TEST 2: Sweep entangling strength (threshold detection)
# =====================================================================

def test2_strength_sweep(n_cycles=10, n_strengths=20):
    """Sweep Ising ZZ strength from 0 to pi/4. (ZZ works where XX doesn't
    because the init state is an XX eigenstate but NOT a ZZ eigenstate.)
    Measure per-step (not just end-of-cycle) and at best position (after stage 7).
    """
    print("\n" + "=" * 72)
    print("TEST 2: Sweep Ising ZZ coupling strength (per-step measurement)")
    print("=" * 72)

    strengths = np.linspace(0.0, np.pi / 4, n_strengths)
    results = []

    for s_val in strengths:
        U_gate = build_ising_zz(s_val)
        engine = GeometricEngine(engine_type=1)
        state = engine.init_state()
        stage_order = LOOP_STAGE_ORDER[engine.engine_type]

        max_C = 0.0
        max_N = 0.0
        max_chsh = 0.0
        first_entangled_cycle = None

        for cycle in range(n_cycles):
            for pos, terrain_idx in enumerate(stage_order):
                state = engine.step(state, stage_idx=terrain_idx)

                # Insert at end of cycle (best position from Test 3 pattern)
                if pos == 7:
                    state.rho_AB = apply_unitary_gate(state.rho_AB, U_gate)

                # Measure at every step
                C = concurrence(state.rho_AB)
                N = negativity(state.rho_AB)
                B = chsh_value(state.rho_AB)
                if C > max_C:
                    max_C = C
                if N > max_N:
                    max_N = N
                if B > max_chsh:
                    max_chsh = B
                if C > 1e-6 and first_entangled_cycle is None:
                    first_entangled_cycle = cycle

        results.append({
            "strength": float(s_val),
            "strength_over_pi_4": float(s_val / (np.pi / 4)),
            "max_concurrence": max_C,
            "max_negativity": max_N,
            "max_chsh": max_chsh,
            "bell_violated": bool(max_chsh > 2.0),
            "first_entangled_cycle": first_entangled_cycle,
        })
        marker = "*" if max_C > 1e-6 else " "
        print(f"  {marker} strength={s_val:.4f} ({s_val/(np.pi/4)*100:5.1f}%): "
              f"max_C={max_C:.6f}  max_N={max_N:.6f}  CHSH={max_chsh:.4f}  "
              f"first_ent_cycle={first_entangled_cycle}")

    # Find threshold
    threshold = None
    for r in results:
        if r["max_concurrence"] > 1e-6:
            threshold = r["strength"]
            break

    summary = {
        "sweep": results,
        "threshold_strength": threshold,
        "threshold_fraction_of_cnot": float(threshold / (np.pi / 4)) if threshold else None,
    }
    print(f"\n  THRESHOLD: strength={threshold}  "
          f"({threshold/(np.pi/4)*100:.1f}% of CNOT)" if threshold else
          "\n  THRESHOLD: No entanglement detected at any strength!")

    return summary


# =====================================================================
# TEST 3: Gate position within cycle
# =====================================================================

def test3_gate_position(n_cycles=10):
    """Test inserting Heisenberg gate at 5 different positions in the cycle."""
    print("\n" + "=" * 72)
    print("TEST 3: Entangling gate position within cycle")
    print("=" * 72)

    U_gate = build_heisenberg(np.pi / 8)
    positions = {
        "pos0_before_all": -1,   # Before first stage
        "pos1_after_stage0": 0,  # After first stage
        "pos2_after_stage1": 1,  # After second stage (between Fe/Te region)
        "pos3_after_stage2": 2,  # After third stage
        "pos4_after_stage3": 3,  # After fourth stage (end of outer loop)
        "pos5_after_stage5": 5,  # Mid inner loop
        "pos6_after_stage7": 7,  # After last stage (before next cycle)
    }

    results = {}
    for pos_name, insert_after in positions.items():
        engine = GeometricEngine(engine_type=1)
        state = engine.init_state()
        stage_order = LOOP_STAGE_ORDER[engine.engine_type]

        max_C = 0.0
        max_N = 0.0
        all_C = []

        for cycle in range(n_cycles):
            # Insert before all stages
            if insert_after == -1:
                state.rho_AB = apply_unitary_gate(state.rho_AB, U_gate)

            for pos, terrain_idx in enumerate(stage_order):
                state = engine.step(state, stage_idx=terrain_idx)

                if pos == insert_after:
                    state.rho_AB = apply_unitary_gate(state.rho_AB, U_gate)

            C = concurrence(state.rho_AB)
            N = negativity(state.rho_AB)
            all_C.append(C)
            if C > max_C:
                max_C = C
            if N > max_N:
                max_N = N

        results[pos_name] = {
            "max_concurrence": max_C,
            "max_negativity": max_N,
            "mean_concurrence": float(np.mean(all_C)),
            "final_concurrence": all_C[-1],
            "concurrence_trajectory": all_C,
        }
        print(f"  {pos_name:24s}: max_C={max_C:.6f}  mean_C={np.mean(all_C):.6f}  "
              f"final_C={all_C[-1]:.6f}")

    # Find best/worst
    best = max(results, key=lambda k: results[k]["max_concurrence"])
    worst = min(results, key=lambda k: results[k]["max_concurrence"])
    print(f"\n  BEST position:  {best} (max_C={results[best]['max_concurrence']:.6f})")
    print(f"  WORST position: {worst} (max_C={results[worst]['max_concurrence']:.6f})")

    results["_best_position"] = best
    results["_worst_position"] = worst
    return results


# =====================================================================
# TEST 4: Entanglement survival under dephasing operators
# =====================================================================

def test4_entanglement_survival():
    """Apply entangling gate then each engine operator. Which kills entanglement?"""
    print("\n" + "=" * 72)
    print("TEST 4: Does entanglement survive the engine operators?")
    print("=" * 72)

    # Create a Bell state |Phi+> = (|00> + |11>)/sqrt(2) as the entangled input.
    # The engine init state is |-->|--> which is a CNOT eigenstate (CNOT does not
    # entangle it). So we use an explicit Bell pair instead.
    bell_plus = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
    rho_entangled = np.outer(bell_plus, bell_plus.conj())
    rho_entangled = ensure_valid_density(rho_entangled)
    C_init = concurrence(rho_entangled)
    N_init = negativity(rho_entangled)
    print(f"  After CNOT: C={C_init:.6f}  N={N_init:.6f}")

    operators = ["Ti", "Fe", "Te", "Fi"]
    results = {"initial_concurrence": C_init, "initial_negativity": N_init}

    for op_name in operators:
        op_fn = OPERATOR_MAP_4X4[op_name]
        # Apply operator with default params
        rho_after = op_fn(rho_entangled.copy(), polarity_up=True, strength=1.0)
        C_after = concurrence(rho_after)
        N_after = negativity(rho_after)
        delta_C = C_after - C_init
        survival = C_after / C_init if C_init > 1e-10 else 0.0

        results[op_name] = {
            "concurrence_after": C_after,
            "negativity_after": N_after,
            "delta_concurrence": delta_C,
            "survival_ratio": survival,
            "kills_entanglement": bool(C_after < 1e-6),
        }
        status = "KILLS" if C_after < 1e-6 else ("REDUCES" if delta_C < -1e-6 else "PRESERVES")
        print(f"  CNOT -> {op_name}: C={C_after:.6f}  delta={delta_C:+.6f}  "
              f"survival={survival*100:.1f}%  [{status}]")

    # Also test sequences: Bell -> dephase -> re-entangle
    print("\n  Sequential: Bell+ -> Ti -> Heisenberg (re-entangle after dephasing)")
    U_heis = build_heisenberg(np.pi / 8)
    rho_seq = rho_entangled.copy()
    rho_seq = OPERATOR_MAP_4X4["Ti"](rho_seq, polarity_up=True, strength=1.0)
    C_mid = concurrence(rho_seq)
    rho_seq = apply_unitary_gate(rho_seq, U_heis)
    C_re = concurrence(rho_seq)
    print(f"  After Ti: C={C_mid:.6f}  After re-entangle: C={C_re:.6f}")
    results["re_entangle_after_Ti"] = {
        "C_after_Ti": C_mid,
        "C_after_re_entangle": C_re,
    }

    return results


# =====================================================================
# TEST 5: Coherent information (I_c) trajectory
# =====================================================================

def test5_coherent_information(n_cycles=20):
    """Track I_c with optimal entangling gate over many cycles.
    Does I_c cross zero?
    """
    print("\n" + "=" * 72)
    print("TEST 5: Coherent information I_c trajectory (20 cycles)")
    print("=" * 72)

    # Use Heisenberg gate at best position (after stage 7, end of cycle)
    U_gate = build_heisenberg(np.pi / 8)
    engine = GeometricEngine(engine_type=1)
    state = engine.init_state()
    stage_order = LOOP_STAGE_ORDER[engine.engine_type]

    Ic_trajectory = []
    C_trajectory = []
    MI_trajectory = []

    for cycle in range(n_cycles):
        for pos, terrain_idx in enumerate(stage_order):
            state = engine.step(state, stage_idx=terrain_idx)
            # Insert at end of cycle (best position from Test 3)
            if pos == 7:
                state.rho_AB = apply_unitary_gate(state.rho_AB, U_gate)

        rho = state.rho_AB
        rho_A = partial_trace_B(rho)
        rho_B = partial_trace_A(rho)
        Ic = coherent_information(rho, rho_B)
        C = concurrence(rho)
        MI = quantum_mutual_information(rho, rho_A, rho_B)

        Ic_trajectory.append(Ic)
        C_trajectory.append(C)
        MI_trajectory.append(MI)

        crossed = "CROSSED" if Ic > 0 else ""
        print(f"  Cycle {cycle:2d}: I_c={Ic:+.6f}  C={C:.6f}  MI={MI:.6f}  {crossed}")

    first_positive = None
    for i, ic in enumerate(Ic_trajectory):
        if ic > 0:
            first_positive = i
            break

    results = {
        "Ic_trajectory": Ic_trajectory,
        "C_trajectory": C_trajectory,
        "MI_trajectory": MI_trajectory,
        "Ic_crossed_zero": first_positive is not None,
        "first_positive_cycle": first_positive,
        "max_Ic": float(max(Ic_trajectory)),
        "min_Ic": float(min(Ic_trajectory)),
        "final_Ic": Ic_trajectory[-1],
        "max_concurrence": float(max(C_trajectory)),
    }

    if first_positive is not None:
        print(f"\n  I_c CROSSED ZERO at cycle {first_positive}!")
    else:
        print(f"\n  I_c never crossed zero. Max I_c = {max(Ic_trajectory):.6f}")

    return results


# =====================================================================
# TEST 6: Per-operator entanglement dynamics (build vs destroy)
# =====================================================================

def test6_build_vs_destroy(n_cycles=10):
    """Track delta_concurrence for each operator WITH entangling gate in cycle."""
    print("\n" + "=" * 72)
    print("TEST 6: Per-operator entanglement dynamics (build vs destroy)")
    print("=" * 72)

    U_gate = build_heisenberg(np.pi / 8)
    engine = GeometricEngine(engine_type=1)
    state = engine.init_state()
    stage_order = LOOP_STAGE_ORDER[engine.engine_type]

    op_deltas = {}  # op_name -> list of delta_C
    gate_deltas = []
    all_C = []

    for cycle in range(n_cycles):
        for pos, terrain_idx in enumerate(stage_order):
            C_before = concurrence(state.rho_AB)

            state = engine.step(state, stage_idx=terrain_idx)
            C_after_op = concurrence(state.rho_AB)

            # Get the operator name from history
            if state.history:
                op_name = state.history[-1].get("op_name", "unknown")
            else:
                op_name = "unknown"

            if op_name not in op_deltas:
                op_deltas[op_name] = []
            op_deltas[op_name].append(C_after_op - C_before)

            # Insert entangling gate at end of cycle (best position)
            if pos == 7:
                C_before_gate = concurrence(state.rho_AB)
                state.rho_AB = apply_unitary_gate(state.rho_AB, U_gate)
                C_after_gate = concurrence(state.rho_AB)
                gate_deltas.append(C_after_gate - C_before_gate)

            all_C.append(concurrence(state.rho_AB))

    results = {"per_operator": {}, "entangling_gate": {}, "steady_state": {}}

    for op_name, deltas in op_deltas.items():
        arr = np.array(deltas)
        role = "BUILDS" if np.mean(arr) > 1e-6 else ("DESTROYS" if np.mean(arr) < -1e-6 else "NEUTRAL")
        results["per_operator"][op_name] = {
            "mean_delta_C": float(np.mean(arr)),
            "std_delta_C": float(np.std(arr)),
            "min_delta_C": float(np.min(arr)),
            "max_delta_C": float(np.max(arr)),
            "n_applications": len(arr),
            "role": role,
        }
        print(f"  {op_name:12s}: mean_dC={np.mean(arr):+.6f}  std={np.std(arr):.6f}  [{role}]")

    if gate_deltas:
        arr_g = np.array(gate_deltas)
        results["entangling_gate"] = {
            "mean_delta_C": float(np.mean(arr_g)),
            "std_delta_C": float(np.std(arr_g)),
            "min_delta_C": float(np.min(arr_g)),
            "max_delta_C": float(np.max(arr_g)),
            "n_applications": len(arr_g),
        }
        print(f"  {'ENTANGLE':12s}: mean_dC={np.mean(arr_g):+.6f}  std={np.std(arr_g):.6f}  [GATE]")

    # Steady-state: last 20% of concurrence values
    tail = all_C[int(len(all_C) * 0.8):]
    results["steady_state"] = {
        "mean_concurrence": float(np.mean(tail)),
        "std_concurrence": float(np.std(tail)),
        "min_concurrence": float(np.min(tail)),
        "max_concurrence": float(np.max(tail)),
    }
    print(f"\n  Steady-state C (last 20%): mean={np.mean(tail):.6f}  "
          f"std={np.std(tail):.6f}  range=[{np.min(tail):.6f}, {np.max(tail):.6f}]")

    return results


# =====================================================================
# JSON SANITIZER
# =====================================================================

def sanitize(obj):
    """Recursively convert numpy types to native Python for JSON."""
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [sanitize(v) for v in obj]
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return sanitize(obj.tolist())
    return obj


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    print("ENTANGLING GATE INTEGRATION SIMULATION")
    print("=" * 72)
    print("Testing whether genuine 2-qubit entangling gates can break")
    print("the engine's separability barrier.\n")

    all_results = {}

    all_results["test1_gate_in_cycle"] = test1_gate_in_cycle(n_cycles=10)
    all_results["test2_strength_sweep"] = test2_strength_sweep(n_cycles=10, n_strengths=20)
    all_results["test3_gate_position"] = test3_gate_position(n_cycles=10)
    all_results["test4_entanglement_survival"] = test4_entanglement_survival()
    all_results["test5_coherent_information"] = test5_coherent_information(n_cycles=20)
    all_results["test6_build_vs_destroy"] = test6_build_vs_destroy(n_cycles=10)

    # === SUMMARY ===
    print("\n" + "=" * 72)
    print("GRAND SUMMARY")
    print("=" * 72)

    t1 = all_results["test1_gate_in_cycle"]
    print("\nTest 1 - Gate insertion (separability crossing):")
    for name, data in t1.items():
        status = "CROSSED" if data["crossed_separability"] else "STILL SEPARABLE"
        print(f"  {name:16s}: max_C={data['max_concurrence']:.6f}  [{status}]")

    t2 = all_results["test2_strength_sweep"]
    print(f"\nTest 2 - Threshold strength: {t2['threshold_strength']}")
    if t2["threshold_fraction_of_cnot"]:
        print(f"  = {t2['threshold_fraction_of_cnot']*100:.1f}% of CNOT strength")

    t3 = all_results["test3_gate_position"]
    print(f"\nTest 3 - Best position: {t3['_best_position']}")
    print(f"         Worst position: {t3['_worst_position']}")

    t4 = all_results["test4_entanglement_survival"]
    print("\nTest 4 - Operator survival:")
    for op in ["Ti", "Fe", "Te", "Fi"]:
        d = t4[op]
        print(f"  {op}: survival={d['survival_ratio']*100:.1f}%  "
              f"{'KILLS' if d['kills_entanglement'] else 'survives'}")

    t5 = all_results["test5_coherent_information"]
    print(f"\nTest 5 - I_c crossed zero: {t5['Ic_crossed_zero']}")
    print(f"         Max I_c: {t5['max_Ic']:.6f}")
    print(f"         Max concurrence: {t5['max_concurrence']:.6f}")

    t6 = all_results["test6_build_vs_destroy"]
    print(f"\nTest 6 - Steady-state concurrence: "
          f"{t6['steady_state']['mean_concurrence']:.6f}")

    # Save
    out_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "a2_state", "sim_results", "entangling_gate_integration_results.json"
    )
    with open(out_path, "w") as f:
        json.dump(sanitize(all_results), f, indent=2)
    print(f"\nResults saved to: {out_path}")
