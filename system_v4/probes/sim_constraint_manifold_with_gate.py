#!/usr/bin/env python3
"""
sim_constraint_manifold_with_gate.py
====================================
Re-run key constraint manifold tests with the native Ising ZZ entangling
gate ON (entangle_strength=0.3).  The previous manifold runs had C=0
everywhere because the engine was separable.  Now it is not.

Tests replicated with gate:
  L7  - ordering: canonical vs reversed, 5 cycles
  L9  - strength Goldilocks sweep
  L11 - eta sweep at 3 torus positions
  L12 - per-operator delta tracking
  ENTROPY SWEEP - all 6 entropy types per step
  I_c TRAJECTORY - 20 cycles, steady-state tracking

Output: a2_state/sim_results/constraint_manifold_with_gate_results.json
"""

import sys
import os
import json
import time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import (
    GeometricEngine, EngineState, StageControls,
    TERRAINS, STAGE_OPERATOR_LUT, LOOP_STAGE_ORDER, LOOP_GRAMMAR,
    TORUS_CLIFFORD,
)
from geometric_operators import (
    apply_Ti_4x4, apply_Fe_4x4, apply_Te_4x4, apply_Fi_4x4,
    apply_Entangle_4x4, OPERATOR_MAP_4X4,
    partial_trace_A, partial_trace_B,
    _ensure_valid_density, SIGMA_Y,
)
from hopf_manifold import (
    von_neumann_entropy_2x2,
    TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER,
)


# ═══════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════

def concurrence_4x4(rho):
    """Wootters concurrence for 2-qubit density matrix."""
    sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
    sy_sy = np.kron(sy, sy)
    R = rho @ sy_sy @ rho.conj() @ sy_sy
    evals = sorted(np.sqrt(np.maximum(np.real(np.linalg.eigvals(R)), 0)), reverse=True)
    return max(0.0, evals[0] - evals[1] - evals[2] - evals[3])


def vn_entropy(rho):
    """Von Neumann entropy S(rho) in bits."""
    rho_h = (rho + rho.conj().T) / 2
    evals = np.real(np.linalg.eigvalsh(rho_h))
    evals = evals[evals > 1e-15]
    if len(evals) == 0:
        return 0.0
    return float(-np.sum(evals * np.log2(evals)))


def mutual_information(rho_AB):
    """I(A:B) = S(A) + S(B) - S(AB)."""
    rho_A = _ensure_valid_density(partial_trace_B(rho_AB))
    rho_B = _ensure_valid_density(partial_trace_A(rho_AB))
    return vn_entropy(rho_A) + vn_entropy(rho_B) - vn_entropy(rho_AB)


def coherent_information(rho_AB):
    """I_c(A>B) = S(B) - S(AB).  Positive = quantum channel capacity."""
    rho_B = _ensure_valid_density(partial_trace_A(rho_AB))
    return vn_entropy(rho_B) - vn_entropy(rho_AB)


def conditional_entropy(rho_AB):
    """S(A|B) = S(AB) - S(B)."""
    rho_B = _ensure_valid_density(partial_trace_A(rho_AB))
    return vn_entropy(rho_AB) - vn_entropy(rho_B)


def renyi_2_entropy(rho):
    """Renyi-2: S_2 = -log2(Tr(rho^2))."""
    purity = float(np.real(np.trace(rho @ rho)))
    if purity < 1e-15:
        return 0.0
    return float(-np.log2(purity))


def min_entropy(rho):
    """S_min = -log2(lambda_max)."""
    rho_h = (rho + rho.conj().T) / 2
    evals = np.real(np.linalg.eigvalsh(rho_h))
    lmax = max(evals)
    if lmax < 1e-15:
        return 0.0
    return float(-np.log2(lmax))


def linear_entropy(rho):
    """S_lin = (d/(d-1))(1 - Tr(rho^2)).  d = dimension."""
    d = rho.shape[0]
    purity = float(np.real(np.trace(rho @ rho)))
    return float((d / (d - 1)) * (1 - purity))


def all_entropies(rho_AB):
    """Compute all 6 entropy types for the joint state."""
    rho_A = _ensure_valid_density(partial_trace_B(rho_AB))
    return {
        "vN_AB": vn_entropy(rho_AB),
        "vN_A": vn_entropy(rho_A),
        "MI": mutual_information(rho_AB),
        "conditional": conditional_entropy(rho_AB),
        "renyi2_AB": renyi_2_entropy(rho_AB),
        "min_AB": min_entropy(rho_AB),
        "linear_AB": linear_entropy(rho_AB),
    }


def sanitize(obj):
    """Recursively sanitize numpy types for JSON."""
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [sanitize(v) for v in obj]
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    elif isinstance(obj, complex):
        return {"re": float(obj.real), "im": float(obj.imag)}
    elif isinstance(obj, np.complexfloating):
        return {"re": float(np.real(obj)), "im": float(np.imag(obj))}
    return obj


# ═══════════════════════════════════════════════════════════════════
# L7 ORDERING: canonical vs reversed with gate ON
# ═══════════════════════════════════════════════════════════════════

def test_L7_ordering(entangle_strength=0.3, n_cycles=5):
    """Run canonical and reversed orderings, compare C/MI/I_c."""
    print(f"[L7] Ordering test: entangle_strength={entangle_strength}, {n_cycles} cycles")

    canonical_order = LOOP_STAGE_ORDER[1]
    reversed_order = list(reversed(canonical_order))

    results = {}
    for label, order in [("canonical", canonical_order), ("reversed", reversed_order)]:
        eng = GeometricEngine(engine_type=1, entangle_strength=entangle_strength)
        state = eng.init_state()

        trajectory = []
        for cyc in range(n_cycles):
            state = eng.run_cycle(state)
            rho = state.rho_AB
            trajectory.append({
                "cycle": cyc,
                "concurrence": concurrence_4x4(rho),
                "MI": mutual_information(rho),
                "I_c": coherent_information(rho),
            })

        results[label] = {
            "order": order,
            "trajectory": trajectory,
            "final_concurrence": trajectory[-1]["concurrence"],
            "final_MI": trajectory[-1]["MI"],
            "final_I_c": trajectory[-1]["I_c"],
            "mean_concurrence": float(np.mean([t["concurrence"] for t in trajectory])),
            "mean_MI": float(np.mean([t["MI"] for t in trajectory])),
            "mean_I_c": float(np.mean([t["I_c"] for t in trajectory])),
        }
        print(f"  {label}: C={results[label]['final_concurrence']:.4f}, "
              f"MI={results[label]['final_MI']:.4f}, "
              f"I_c={results[label]['final_I_c']:.4f}")

    # Also run with gate OFF for baseline comparison
    eng_off = GeometricEngine(engine_type=1, entangle_strength=0.0)
    state_off = eng_off.init_state()
    for _ in range(n_cycles):
        state_off = eng_off.run_cycle(state_off)
    results["gate_off_baseline"] = {
        "concurrence": concurrence_4x4(state_off.rho_AB),
        "MI": mutual_information(state_off.rho_AB),
        "I_c": coherent_information(state_off.rho_AB),
    }
    print(f"  gate_off: C={results['gate_off_baseline']['concurrence']:.4f}, "
          f"MI={results['gate_off_baseline']['MI']:.4f}, "
          f"I_c={results['gate_off_baseline']['I_c']:.4f}")

    results["ordering_matters"] = abs(
        results["canonical"]["final_concurrence"] - results["reversed"]["final_concurrence"]
    ) > 0.001

    return results


# ═══════════════════════════════════════════════════════════════════
# L9 STRENGTH GOLDILOCKS: sweep with gate ON
# ═══════════════════════════════════════════════════════════════════

def test_L9_strength_goldilocks(entangle_strength=0.3, n_cycles=5):
    """Sweep operator strength [0, 0.25, 0.5, 0.75, 1.0] with gate ON."""
    print(f"[L9] Strength Goldilocks: entangle_strength={entangle_strength}")

    strength_vals = [0.0, 0.25, 0.5, 0.75, 1.0]
    results = []

    for s in strength_vals:
        eng = GeometricEngine(engine_type=1, entangle_strength=entangle_strength)
        state = eng.init_state()

        controls = {i: StageControls(piston=s) for i in range(8)}
        for cyc in range(n_cycles):
            state = eng.run_cycle(state, controls=controls)

        rho = state.rho_AB
        c = concurrence_4x4(rho)
        mi = mutual_information(rho)
        ic = coherent_information(rho)

        results.append({
            "strength": s,
            "concurrence": c,
            "MI": mi,
            "I_c": ic,
        })
        print(f"  s={s:.2f}: C={c:.4f}, MI={mi:.4f}, I_c={ic:.4f}")

    # Find Goldilocks
    best_conc = max(results, key=lambda r: r["concurrence"])
    best_ic = max(results, key=lambda r: r["I_c"])

    return {
        "sweep": results,
        "goldilocks_concurrence": best_conc,
        "goldilocks_I_c": best_ic,
    }


# ═══════════════════════════════════════════════════════════════════
# L11 ETA SWEEP: 3 torus positions with gate ON
# ═══════════════════════════════════════════════════════════════════

def test_L11_eta_sweep(entangle_strength=0.3, n_cycles=5):
    """Run at TORUS_INNER, CLIFFORD, OUTER with gate ON."""
    print(f"[L11] Eta sweep: entangle_strength={entangle_strength}")

    eta_points = {
        "TORUS_INNER": TORUS_INNER,
        "TORUS_CLIFFORD": TORUS_CLIFFORD,
        "TORUS_OUTER": TORUS_OUTER,
    }

    results = {}
    for label, eta in eta_points.items():
        eng = GeometricEngine(engine_type=1, entangle_strength=entangle_strength)
        state = eng.init_state(eta=eta)

        trajectory = []
        for cyc in range(n_cycles):
            state = eng.run_cycle(state)
            rho = state.rho_AB
            trajectory.append({
                "cycle": cyc,
                "concurrence": concurrence_4x4(rho),
                "MI": mutual_information(rho),
                "I_c": coherent_information(rho),
            })

        results[label] = {
            "eta": float(eta),
            "trajectory": trajectory,
            "final_concurrence": trajectory[-1]["concurrence"],
            "final_MI": trajectory[-1]["MI"],
            "final_I_c": trajectory[-1]["I_c"],
        }
        print(f"  {label} (eta={eta:.4f}): C={results[label]['final_concurrence']:.4f}, "
              f"MI={results[label]['final_MI']:.4f}, I_c={results[label]['final_I_c']:.4f}")

    # Which eta is optimal?
    eta_labels = list(eta_points.keys())
    best_eta = max(eta_labels, key=lambda k: results[k]["final_I_c"])
    results["optimal_eta_for_I_c"] = best_eta
    results["optimal_eta_for_concurrence"] = max(eta_labels,
                                                  key=lambda k: results[k]["final_concurrence"])
    return results


# ═══════════════════════════════════════════════════════════════════
# L12 ENTANGLEMENT DYNAMICS: per-operator delta tracking
# ═══════════════════════════════════════════════════════════════════

def test_L12_operator_deltas(entangle_strength=0.3, n_cycles=5):
    """Track what each operator contributes to C/MI/I_c.

    Run one full cycle, but measure after EACH operator application
    (including the entangling gate).
    """
    print(f"[L12] Per-operator delta tracking: entangle_strength={entangle_strength}")

    eng = GeometricEngine(engine_type=1, entangle_strength=entangle_strength)
    state = eng.init_state()

    # Run a few warm-up cycles to get past initial transients
    for _ in range(2):
        state = eng.run_cycle(state)

    # Now do one tracked cycle
    stage_order = LOOP_STAGE_ORDER[1]
    op_deltas = []

    for position, terrain_idx in enumerate(stage_order):
        terrain = TERRAINS[terrain_idx]
        op_name, _ = STAGE_OPERATOR_LUT[(1, terrain["loop"], terrain["topo"])]

        rho_before = state.rho_AB.copy()
        c_before = concurrence_4x4(rho_before)
        mi_before = mutual_information(rho_before)
        ic_before = coherent_information(rho_before)

        ctrl = StageControls()
        state = eng.step(state, stage_idx=terrain_idx, controls=ctrl)

        c_after = concurrence_4x4(state.rho_AB)
        mi_after = mutual_information(state.rho_AB)
        ic_after = coherent_information(state.rho_AB)

        op_deltas.append({
            "position": position,
            "terrain": terrain["name"],
            "operator": op_name,
            "delta_concurrence": c_after - c_before,
            "delta_MI": mi_after - mi_before,
            "delta_I_c": ic_after - ic_before,
            "concurrence_after": c_after,
            "MI_after": mi_after,
            "I_c_after": ic_after,
        })

    # Now apply entangling gate
    rho_pre_ent = state.rho_AB.copy()
    c_pre = concurrence_4x4(rho_pre_ent)
    mi_pre = mutual_information(rho_pre_ent)
    ic_pre = coherent_information(rho_pre_ent)

    if entangle_strength > 0:
        state.rho_AB = apply_Entangle_4x4(state.rho_AB, strength=entangle_strength)

    c_post = concurrence_4x4(state.rho_AB)
    mi_post = mutual_information(state.rho_AB)
    ic_post = coherent_information(state.rho_AB)

    ent_delta = {
        "position": 8,
        "terrain": "END_OF_CYCLE",
        "operator": "Ent_ZZ",
        "delta_concurrence": c_post - c_pre,
        "delta_MI": mi_post - mi_pre,
        "delta_I_c": ic_post - ic_pre,
        "concurrence_after": c_post,
        "MI_after": mi_post,
        "I_c_after": ic_post,
    }
    op_deltas.append(ent_delta)

    # Summary: who builds, who destroys?
    for d in op_deltas:
        label = d["operator"]
        dc = d["delta_concurrence"]
        print(f"  {label:>6} @ {d['terrain']:>8}: dC={dc:+.4f}, dMI={d['delta_MI']:+.4f}, dI_c={d['delta_I_c']:+.4f}")

    return {
        "operator_deltas": op_deltas,
        "entangling_gate_delta": ent_delta,
        "gate_is_dominant_builder": ent_delta["delta_concurrence"] > max(
            d["delta_concurrence"] for d in op_deltas[:-1]
        ),
    }


# ═══════════════════════════════════════════════════════════════════
# ENTROPY SWEEP: all 6 types per step
# ═══════════════════════════════════════════════════════════════════

def test_entropy_sweep(entangle_strength=0.3, n_cycles=5):
    """Compute ALL entropy types at each step. Does MI still win?"""
    print(f"[ENT] Full entropy sweep: entangle_strength={entangle_strength}")

    eng = GeometricEngine(engine_type=1, entangle_strength=entangle_strength)
    state = eng.init_state()

    per_cycle_entropies = []

    for cyc in range(n_cycles):
        state = eng.run_cycle(state)
        ent = all_entropies(state.rho_AB)
        ent["cycle"] = cyc
        per_cycle_entropies.append(ent)

    # Final entropy ranking
    final = per_cycle_entropies[-1]
    ranked_keys = sorted(
        ["vN_AB", "vN_A", "MI", "conditional", "renyi2_AB", "min_AB", "linear_AB"],
        key=lambda k: final[k], reverse=True
    )

    # Also run gate-off for comparison
    eng_off = GeometricEngine(engine_type=1, entangle_strength=0.0)
    state_off = eng_off.init_state()
    for _ in range(n_cycles):
        state_off = eng_off.run_cycle(state_off)
    gate_off_entropies = all_entropies(state_off.rho_AB)

    return {
        "per_cycle": per_cycle_entropies,
        "final_ranking": ranked_keys,
        "final_values": {k: final[k] for k in ranked_keys},
        "gate_off_final": gate_off_entropies,
        "MI_still_wins": ranked_keys[0] == "MI" or (
            "MI" in ranked_keys[:2] and final["MI"] > 0.1
        ),
    }


# ═══════════════════════════════════════════════════════════════════
# I_c TRAJECTORY: 20 cycles, steady-state
# ═══════════════════════════════════════════════════════════════════

def test_Ic_trajectory(entangle_strength=0.3, n_cycles=20):
    """Track I_c every cycle. Does it go positive? Steady state?"""
    print(f"[I_c] Trajectory: entangle_strength={entangle_strength}, {n_cycles} cycles")

    eng = GeometricEngine(engine_type=1, entangle_strength=entangle_strength)
    state = eng.init_state()

    trajectory = []
    for cyc in range(n_cycles):
        state = eng.run_cycle(state)
        rho = state.rho_AB
        ic = coherent_information(rho)
        c = concurrence_4x4(rho)
        mi = mutual_information(rho)
        trajectory.append({
            "cycle": cyc,
            "I_c": ic,
            "concurrence": c,
            "MI": mi,
        })
        print(f"  Cycle {cyc:>2}: I_c={ic:+.4f}, C={c:.4f}, MI={mi:.4f}")

    ic_vals = [t["I_c"] for t in trajectory]
    ever_positive = any(ic > 0 for ic in ic_vals)
    final_positive = ic_vals[-1] > 0

    # Steady state detection: last 5 cycles std
    if len(ic_vals) >= 5:
        tail = ic_vals[-5:]
        steady_state_std = float(np.std(tail))
        steady_state_mean = float(np.mean(tail))
    else:
        steady_state_std = None
        steady_state_mean = None

    return {
        "trajectory": trajectory,
        "I_c_ever_positive": ever_positive,
        "I_c_final_positive": final_positive,
        "I_c_final": ic_vals[-1],
        "I_c_max": max(ic_vals),
        "I_c_min": min(ic_vals),
        "steady_state_mean": steady_state_mean,
        "steady_state_std": steady_state_std,
        "converged": steady_state_std is not None and steady_state_std < 0.01,
    }


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    t0 = time.time()
    ENTANGLE_STRENGTH = 0.3

    print("=" * 70)
    print("CONSTRAINT MANIFOLD WITH NATIVE ENTANGLING GATE")
    print(f"entangle_strength = {ENTANGLE_STRENGTH}")
    print("=" * 70)

    results = {}

    results["L7_ordering"] = test_L7_ordering(entangle_strength=ENTANGLE_STRENGTH, n_cycles=5)
    print()
    results["L9_strength_goldilocks"] = test_L9_strength_goldilocks(entangle_strength=ENTANGLE_STRENGTH, n_cycles=5)
    print()
    results["L11_eta_sweep"] = test_L11_eta_sweep(entangle_strength=ENTANGLE_STRENGTH, n_cycles=5)
    print()
    results["L12_operator_deltas"] = test_L12_operator_deltas(entangle_strength=ENTANGLE_STRENGTH, n_cycles=5)
    print()
    results["entropy_sweep"] = test_entropy_sweep(entangle_strength=ENTANGLE_STRENGTH, n_cycles=5)
    print()
    results["Ic_trajectory"] = test_Ic_trajectory(entangle_strength=ENTANGLE_STRENGTH, n_cycles=20)

    elapsed = time.time() - t0

    # ── SUMMARY ──
    print("\n" + "=" * 70)
    print("SUMMARY: DOES THE ENTANGLING GATE CHANGE WHAT CONSTRAINTS SELECT?")
    print("=" * 70)

    l7 = results["L7_ordering"]
    print(f"\nL7  Ordering matters with gate? {l7['ordering_matters']}")
    print(f"    Canonical: C={l7['canonical']['final_concurrence']:.4f}, I_c={l7['canonical']['final_I_c']:.4f}")
    print(f"    Reversed:  C={l7['reversed']['final_concurrence']:.4f}, I_c={l7['reversed']['final_I_c']:.4f}")
    print(f"    Gate OFF:  C={l7['gate_off_baseline']['concurrence']:.4f}, I_c={l7['gate_off_baseline']['I_c']:.4f}")

    l9 = results["L9_strength_goldilocks"]
    print(f"\nL9  Goldilocks (concurrence): s={l9['goldilocks_concurrence']['strength']}, C={l9['goldilocks_concurrence']['concurrence']:.4f}")
    print(f"    Goldilocks (I_c):          s={l9['goldilocks_I_c']['strength']}, I_c={l9['goldilocks_I_c']['I_c']:.4f}")

    l11 = results["L11_eta_sweep"]
    print(f"\nL11 Optimal eta for I_c:          {l11['optimal_eta_for_I_c']}")
    print(f"    Optimal eta for concurrence:  {l11['optimal_eta_for_concurrence']}")

    l12 = results["L12_operator_deltas"]
    print(f"\nL12 Entangling gate is dominant builder? {l12['gate_is_dominant_builder']}")
    ent_d = l12["entangling_gate_delta"]
    print(f"    Ent gate delta: dC={ent_d['delta_concurrence']:+.4f}, dMI={ent_d['delta_MI']:+.4f}, dI_c={ent_d['delta_I_c']:+.4f}")

    es = results["entropy_sweep"]
    print(f"\nENT Final entropy ranking: {es['final_ranking']}")
    print(f"    MI still dominant?  {es['MI_still_wins']}")

    ic = results["Ic_trajectory"]
    print(f"\nI_c Ever positive?  {ic['I_c_ever_positive']}")
    print(f"    Final positive? {ic['I_c_final_positive']}")
    print(f"    Final I_c:      {ic['I_c_final']:+.4f}")
    print(f"    Converged?      {ic['converged']}")
    if ic['steady_state_mean'] is not None:
        print(f"    Steady state:   mean={ic['steady_state_mean']:+.4f}, std={ic['steady_state_std']:.4f}")

    results["metadata"] = {
        "entangle_strength": ENTANGLE_STRENGTH,
        "runtime_seconds": round(elapsed, 1),
        "timestamp": "2026-04-05",
        "purpose": "Re-run constraint manifold with native Ising ZZ gate ON",
    }

    # Write output
    out_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "a2_state", "sim_results",
        "constraint_manifold_with_gate_results.json",
    )
    with open(out_path, "w") as f:
        json.dump(sanitize(results), f, indent=2)

    print(f"\nResults written to: {out_path}")
    print(f"Total runtime: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
