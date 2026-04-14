#!/usr/bin/env python3
"""
Full 64-Step Engine Simulation with Entangling Gate
=====================================================
Runs the COMPLETE dual-type interleaved schedule:
  Type 1 runs 8 stages, then Type 2 runs 8 stages, repeat 4 times = 64 stages.

At every step: entropy, correlations, entanglement (concurrence), geometry.
Sweeps across 3 torus positions and 3 entangling strengths.
Computes axis orthogonality matrix at the end.

Output: a2_state/sim_results/full_64step_with_gate_results.json
"""

import sys
import os
import json
import numpy as np
from datetime import datetime
classification = "classical_baseline"  # auto-backfill

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import (
    GeometricEngine, EngineState, StageControls,
    LOOP_STAGE_ORDER, TERRAINS, STAGE_OPERATOR_LUT,
)
from geometric_operators import (
    partial_trace_A, partial_trace_B, _ensure_valid_density,
    apply_Entangle_4x4,
)
from hopf_manifold import (
    TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER,
    von_neumann_entropy_2x2, density_to_bloch,
)


# ═══════════════════════════════════════════════════════════════════
# MEASUREMENT FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def concurrence_4x4(rho):
    """Wootters concurrence for a 4x4 density matrix."""
    sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
    sy_sy = np.kron(sy, sy)
    R = rho @ sy_sy @ rho.conj() @ sy_sy
    evals = sorted(np.sqrt(np.maximum(np.real(np.linalg.eigvals(R)), 0)),
                   reverse=True)
    return float(max(0, evals[0] - evals[1] - evals[2] - evals[3]))


def entropy_4x4(rho):
    """Von Neumann entropy of a 4x4 matrix in bits."""
    rho_h = (rho + rho.conj().T) / 2
    evals = np.linalg.eigvalsh(rho_h)
    evals = evals[evals > 1e-15]
    if len(evals) == 0:
        return 0.0
    return float(-np.sum(evals * np.log2(evals)))


def entropy_2x2(rho):
    """Von Neumann entropy of a 2x2 matrix in bits."""
    return float(von_neumann_entropy_2x2(rho))


def mutual_information(s_a, s_b, s_ab):
    """I(A:B) = S(A) + S(B) - S(AB)."""
    return max(0.0, s_a + s_b - s_ab)


def conditional_entropy(s_ab, s_b):
    """S(A|B) = S(AB) - S(B)."""
    return s_ab - s_b


def coherent_information(s_ab, s_b):
    """I_c(A>B) = -S(A|B) = S(B) - S(AB)."""
    return s_b - s_ab


# ═══════════════════════════════════════════════════════════════════
# SINGLE STEP MEASUREMENT
# ═══════════════════════════════════════════════════════════════════

def measure_state(state, step_idx, terrain_idx, engine_type):
    """Extract full measurement record from an EngineState."""
    rho_AB = state.rho_AB
    rho_A = _ensure_valid_density(partial_trace_B(rho_AB))
    rho_B = _ensure_valid_density(partial_trace_A(rho_AB))

    s_a = entropy_2x2(rho_A)
    s_b = entropy_2x2(rho_B)
    s_ab = entropy_4x4(rho_AB)

    mi = mutual_information(s_a, s_b, s_ab)
    cond_ent = conditional_entropy(s_ab, s_b)
    i_c = coherent_information(s_ab, s_b)
    conc = concurrence_4x4(rho_AB)

    b_L = density_to_bloch(rho_A)
    b_R = density_to_bloch(rho_B)
    r_L = float(np.linalg.norm(b_L))
    r_R = float(np.linalg.norm(b_R))
    purity_A = float(np.real(np.trace(rho_A @ rho_A)))
    purity_B = float(np.real(np.trace(rho_B @ rho_B)))
    purity_AB = float(np.real(np.trace(rho_AB @ rho_AB)))
    dot_LR = float(np.dot(b_L, b_R))

    terrain = TERRAINS[terrain_idx]
    loop_family = terrain["loop"]
    topo = terrain["topo"]
    op_name, polarity_up = STAGE_OPERATOR_LUT[(engine_type, loop_family, topo)]

    # Axis assignments
    ax3_fiber_base = 1 if loop_family == "fiber" else -1   # +1 fiber, -1 base
    ax5_tf_kernel = 1 if op_name in ("Ti", "Te") else -1   # +1 T-kernel, -1 F-kernel
    ax6_left_right = 1 if engine_type == 1 else -1          # +1 left (type1), -1 right (type2)

    return {
        "step_idx": step_idx,
        "terrain_idx": terrain_idx,
        "terrain_name": terrain["name"],
        "operator": op_name,
        "polarity_up": polarity_up,
        "engine_type": engine_type,
        "loop_family": loop_family,
        # Axis assignments
        "ax3_fiber_base": ax3_fiber_base,
        "ax5_tf_kernel": ax5_tf_kernel,
        "ax6_left_right": ax6_left_right,
        # Entropy
        "S_A": s_a,
        "S_B": s_b,
        "S_AB": s_ab,
        # Correlations
        "MI": mi,
        "cond_entropy": cond_ent,
        "I_c": i_c,
        # Entanglement
        "concurrence": conc,
        # Geometry
        "bloch_L": [float(x) for x in b_L],
        "bloch_R": [float(x) for x in b_R],
        "r_L": r_L,
        "r_R": r_R,
        "purity_A": purity_A,
        "purity_B": purity_B,
        "purity_AB": purity_AB,
        "dot_LR": dot_LR,
        "eta": float(state.eta),
        "theta1": float(state.theta1),
        "theta2": float(state.theta2),
    }


# ═══════════════════════════════════════════════════════════════════
# FULL 64-STEP SCHEDULE
# ═══════════════════════════════════════════════════════════════════

def build_64step_schedule():
    """Build the full 64-step interleaved schedule.

    Pattern: Type 1 runs 8 stages, Type 2 runs 8 stages, repeat 4 times.
    Each type uses its own LOOP_STAGE_ORDER for the 8-stage sequence.
    Total: 8 * 2 * 4 = 64 stages.
    """
    schedule = []
    for rep in range(4):
        for engine_type in [1, 2]:
            stage_order = LOOP_STAGE_ORDER[engine_type]
            for pos_in_cycle, terrain_idx in enumerate(stage_order):
                schedule.append({
                    "rep": rep,
                    "engine_type": engine_type,
                    "terrain_idx": terrain_idx,
                    "pos_in_cycle": pos_in_cycle,
                })
    return schedule


def run_64step(eta=TORUS_CLIFFORD, entangle_strength=0.3, seed=42):
    """Run the full 64-step schedule and return per-step measurements.

    The state is shared across both engine types -- Type 1 and Type 2
    alternate acting on the same joint rho_AB. The entangling gate fires
    at the end of each 8-stage half-cycle (after each engine type finishes
    its 8 stages).
    """
    schedule = build_64step_schedule()
    rng = np.random.default_rng(seed)

    # Initialize engines
    eng1 = GeometricEngine(engine_type=1, entangle_strength=entangle_strength)
    eng2 = GeometricEngine(engine_type=2, entangle_strength=entangle_strength)
    engines = {1: eng1, 2: eng2}

    # Initialize shared state from Type 1
    state = eng1.init_state(eta=eta, rng=rng)

    measurements = []
    prev_s_a = entropy_2x2(state.rho_L)

    for step_idx, entry in enumerate(schedule):
        engine_type = entry["engine_type"]
        terrain_idx = entry["terrain_idx"]
        pos_in_cycle = entry["pos_in_cycle"]
        eng = engines[engine_type]

        controls = StageControls(torus=eta)
        state = eng.step(state, stage_idx=terrain_idx, controls=controls)

        m = measure_state(state, step_idx, terrain_idx, engine_type)
        m["rep"] = entry["rep"]
        m["pos_in_cycle"] = pos_in_cycle

        # delta entropy
        m["delta_S_A"] = m["S_A"] - prev_s_a
        prev_s_a = m["S_A"]

        measurements.append(m)

        # Fire entangling gate at end of each 8-stage block
        if pos_in_cycle == 7 and entangle_strength > 0:
            state.rho_AB = apply_Entangle_4x4(
                state.rho_AB, strength=entangle_strength
            )
            state.rho_AB = _ensure_valid_density(state.rho_AB)

    return measurements


# ═══════════════════════════════════════════════════════════════════
# POST-PROCESSING: STATISTICS & AXIS ORTHOGONALITY
# ═══════════════════════════════════════════════════════════════════

def compute_per_axis_stats(measurements):
    """Group delta_S_A by axis assignments."""
    groups = {
        "ax3_fiber": [], "ax3_base": [],
        "ax5_T": [], "ax5_F": [],
        "ax6_left": [], "ax6_right": [],
    }
    for m in measurements:
        d = m["delta_S_A"]
        if m["ax3_fiber_base"] == 1:
            groups["ax3_fiber"].append(d)
        else:
            groups["ax3_base"].append(d)
        if m["ax5_tf_kernel"] == 1:
            groups["ax5_T"].append(d)
        else:
            groups["ax5_F"].append(d)
        if m["ax6_left_right"] == 1:
            groups["ax6_left"].append(d)
        else:
            groups["ax6_right"].append(d)

    stats = {}
    for k, vals in groups.items():
        if vals:
            stats[k] = {
                "mean_delta_S": float(np.mean(vals)),
                "std_delta_S": float(np.std(vals)),
                "count": len(vals),
            }
    return stats


def compute_per_operator_stats(measurements):
    """Group metrics by operator name."""
    ops = {}
    for m in measurements:
        op = m["operator"]
        if op not in ops:
            ops[op] = {"delta_S": [], "MI": [], "I_c": [], "conc": []}
        ops[op]["delta_S"].append(m["delta_S_A"])
        ops[op]["MI"].append(m["MI"])
        ops[op]["I_c"].append(m["I_c"])
        ops[op]["conc"].append(m["concurrence"])

    stats = {}
    for op, data in ops.items():
        stats[op] = {
            "mean_delta_S": float(np.mean(data["delta_S"])),
            "mean_MI": float(np.mean(data["MI"])),
            "mean_I_c": float(np.mean(data["I_c"])),
            "mean_concurrence": float(np.mean(data["conc"])),
            "count": len(data["delta_S"]),
        }
    return stats


def extract_trajectories(measurements):
    """Pull out the 64-point time series."""
    return {
        "entropy_A": [m["S_A"] for m in measurements],
        "entropy_B": [m["S_B"] for m in measurements],
        "entropy_AB": [m["S_AB"] for m in measurements],
        "concurrence": [m["concurrence"] for m in measurements],
        "I_c": [m["I_c"] for m in measurements],
        "MI": [m["MI"] for m in measurements],
        "purity_AB": [m["purity_AB"] for m in measurements],
        "dot_LR": [m["dot_LR"] for m in measurements],
    }


def compute_axis_orthogonality(measurements):
    """Compute pairwise correlations between axis sequences.

    Ax3: +1 fiber, -1 base
    Ax5: +1 T-kernel, -1 F-kernel
    Ax6: +1 left (type1), -1 right (type2)
    Ax0: I_c value at each step

    All pairwise correlations should be near zero (axes are independent).
    """
    ax3 = np.array([m["ax3_fiber_base"] for m in measurements], dtype=float)
    ax5 = np.array([m["ax5_tf_kernel"] for m in measurements], dtype=float)
    ax6 = np.array([m["ax6_left_right"] for m in measurements], dtype=float)
    ax0 = np.array([m["I_c"] for m in measurements], dtype=float)

    labels = ["Ax3_fiber_base", "Ax5_TF_kernel", "Ax6_left_right", "Ax0_I_c"]
    sequences = [ax3, ax5, ax6, ax0]

    matrix = {}
    for i, (li, si) in enumerate(zip(labels, sequences)):
        for j, (lj, sj) in enumerate(zip(labels, sequences)):
            if i < j:
                # Pearson correlation
                if np.std(si) > 1e-12 and np.std(sj) > 1e-12:
                    corr = float(np.corrcoef(si, sj)[0, 1])
                else:
                    corr = 0.0
                matrix[f"{li}_vs_{lj}"] = corr
    return matrix


# ═══════════════════════════════════════════════════════════════════
# MAIN SWEEP
# ═══════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("FULL 64-STEP ENGINE SIM WITH ENTANGLING GATE")
    print("=" * 70)

    results = {
        "meta": {
            "timestamp": datetime.now().isoformat(),
            "description": "Full 64-step dual-type interleaved engine run",
            "schedule": "Type1(8) -> Type2(8) x 4 reps = 64 stages",
            "entangling_gate": "Ising ZZ applied after each 8-stage block",
        },
        "torus_sweep": {},
        "strength_sweep": {},
        "axis_orthogonality": {},
    }

    # ── SWEEP 1: Torus positions (at default strength=0.3) ──
    torus_configs = {
        "TORUS_INNER": TORUS_INNER,
        "TORUS_CLIFFORD": TORUS_CLIFFORD,
        "TORUS_OUTER": TORUS_OUTER,
    }

    for name, eta in torus_configs.items():
        print(f"\n--- Torus: {name} (eta={eta:.4f}) ---")
        meas = run_64step(eta=eta, entangle_strength=0.3)

        per_axis = compute_per_axis_stats(meas)
        per_op = compute_per_operator_stats(meas)
        traj = extract_trajectories(meas)
        ortho = compute_axis_orthogonality(meas)

        # Strip heavy fields for JSON (bloch vectors already in measurements)
        meas_lite = []
        for m in meas:
            ml = {k: v for k, v in m.items()}
            meas_lite.append(ml)

        results["torus_sweep"][name] = {
            "eta": float(eta),
            "measurements": meas_lite,
            "per_axis_stats": per_axis,
            "per_operator_stats": per_op,
            "trajectories": traj,
            "axis_orthogonality": ortho,
            "summary": {
                "final_S_A": meas[-1]["S_A"],
                "final_S_B": meas[-1]["S_B"],
                "final_S_AB": meas[-1]["S_AB"],
                "final_MI": meas[-1]["MI"],
                "final_I_c": meas[-1]["I_c"],
                "final_concurrence": meas[-1]["concurrence"],
                "max_concurrence": max(m["concurrence"] for m in meas),
                "mean_MI": float(np.mean([m["MI"] for m in meas])),
                "mean_I_c": float(np.mean([m["I_c"] for m in meas])),
                "mean_concurrence": float(np.mean([m["concurrence"] for m in meas])),
            },
        }
        s = results["torus_sweep"][name]["summary"]
        print(f"  Final S_A={s['final_S_A']:.4f}  MI={s['final_MI']:.4f}  "
              f"I_c={s['final_I_c']:.4f}  Conc={s['final_concurrence']:.4f}")
        print(f"  Max concurrence={s['max_concurrence']:.4f}  "
              f"Mean I_c={s['mean_I_c']:.4f}")

    # ── SWEEP 2: Entangling strengths (at Clifford torus) ──
    strengths = {"off_0.0": 0.0, "default_0.3": 0.3, "strong_0.6": 0.6}

    for name, strength in strengths.items():
        print(f"\n--- Entangle strength: {name} ---")
        meas = run_64step(eta=TORUS_CLIFFORD, entangle_strength=strength)

        per_axis = compute_per_axis_stats(meas)
        per_op = compute_per_operator_stats(meas)
        traj = extract_trajectories(meas)
        ortho = compute_axis_orthogonality(meas)

        meas_lite = []
        for m in meas:
            ml = {k: v for k, v in m.items()}
            meas_lite.append(ml)

        results["strength_sweep"][name] = {
            "entangle_strength": strength,
            "measurements": meas_lite,
            "per_axis_stats": per_axis,
            "per_operator_stats": per_op,
            "trajectories": traj,
            "axis_orthogonality": ortho,
            "summary": {
                "final_S_A": meas[-1]["S_A"],
                "final_S_B": meas[-1]["S_B"],
                "final_S_AB": meas[-1]["S_AB"],
                "final_MI": meas[-1]["MI"],
                "final_I_c": meas[-1]["I_c"],
                "final_concurrence": meas[-1]["concurrence"],
                "max_concurrence": max(m["concurrence"] for m in meas),
                "mean_MI": float(np.mean([m["MI"] for m in meas])),
                "mean_I_c": float(np.mean([m["I_c"] for m in meas])),
                "mean_concurrence": float(np.mean([m["concurrence"] for m in meas])),
            },
        }
        s = results["strength_sweep"][name]["summary"]
        print(f"  Final S_A={s['final_S_A']:.4f}  MI={s['final_MI']:.4f}  "
              f"I_c={s['final_I_c']:.4f}  Conc={s['final_concurrence']:.4f}")
        print(f"  Max concurrence={s['max_concurrence']:.4f}  "
              f"Mean I_c={s['mean_I_c']:.4f}")

    # ── AXIS ORTHOGONALITY COMPARISON ──
    print("\n" + "=" * 70)
    print("AXIS ORTHOGONALITY (pairwise correlations, should be ~0)")
    print("=" * 70)

    # Use the Clifford/default run as the reference
    ref_ortho = results["torus_sweep"]["TORUS_CLIFFORD"]["axis_orthogonality"]
    for pair, corr in ref_ortho.items():
        flag = " *** HIGH ***" if abs(corr) > 0.3 else ""
        print(f"  {pair}: {corr:+.4f}{flag}")

    results["axis_orthogonality"]["reference_clifford_default"] = ref_ortho

    # Cross-torus comparison
    print("\n--- Cross-torus orthogonality ---")
    for tname in torus_configs:
        o = results["torus_sweep"][tname]["axis_orthogonality"]
        max_corr = max(abs(v) for v in o.values()) if o else 0
        print(f"  {tname}: max |corr| = {max_corr:.4f}")

    # Cross-strength comparison
    print("\n--- Cross-strength orthogonality ---")
    for sname in strengths:
        o = results["strength_sweep"][sname]["axis_orthogonality"]
        max_corr = max(abs(v) for v in o.values()) if o else 0
        print(f"  {sname}: max |corr| = {max_corr:.4f}")

    # ── SUMMARY TABLE ──
    print("\n" + "=" * 70)
    print("SUMMARY TABLE: TORUS SWEEP")
    print("=" * 70)
    print(f"{'Torus':<18} {'Final S_A':>10} {'Mean MI':>10} {'Mean I_c':>10} {'Max Conc':>10}")
    print("-" * 60)
    for tname in torus_configs:
        s = results["torus_sweep"][tname]["summary"]
        print(f"{tname:<18} {s['final_S_A']:>10.4f} {s['mean_MI']:>10.4f} "
              f"{s['mean_I_c']:>10.4f} {s['max_concurrence']:>10.4f}")

    print(f"\n{'Strength':<18} {'Final S_A':>10} {'Mean MI':>10} {'Mean I_c':>10} {'Max Conc':>10}")
    print("-" * 60)
    for sname in strengths:
        s = results["strength_sweep"][sname]["summary"]
        print(f"{sname:<18} {s['final_S_A']:>10.4f} {s['mean_MI']:>10.4f} "
              f"{s['mean_I_c']:>10.4f} {s['max_concurrence']:>10.4f}")

    # ── WRITE OUTPUT ──
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "full_64step_with_gate_results.json")

    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nResults written to: {out_path}")
    print(f"Total entries: {sum(len(v['measurements']) for v in results['torus_sweep'].values())} "
          f"(torus) + {sum(len(v['measurements']) for v in results['strength_sweep'].values())} (strength)")


if __name__ == "__main__":
    main()
