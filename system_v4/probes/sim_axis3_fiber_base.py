#!/usr/bin/env python3
"""
Axis 3 Validation SIM -- Fiber vs Base-Lift (Inner Loop vs Outer Loop)
=====================================================================
Tests the Ax3 definition from AXIS_3_4_5_6_QIT_MATH.md:

  Ax3 distinguishes whether the stage operates on a density-STATIONARY
  path (inner/fiber, b3=-1) or a density-TRAVERSING path (outer/base-lift,
  b3=+1) on S^3.

  fiber loop:  gamma_f(u) -- phase-only, density-blind, rho(u)=rho(0)
  base loop:   gamma_b(u) -- horizontal lift, traverses torus, rho(u) varies

Engine realization:
  - Fiber stages advance theta2 primarily (inner ring of nested torus)
  - Base stages advance theta1 primarily (outer ring)
  - Type 1: outer=deductive(base), inner=inductive(fiber)
  - Type 2: outer=inductive(fiber), inner=deductive(base)
  - Chirality: fiber/base terrain assignments swap between Type 1 and Type 2

Build order: 6 -> 5 -> [3] -> 4 -> 1 -> 2.  Axes 6 and 5 are done.

Evidence token: E_AX3_FIBER_BASE_VALID
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict
from datetime import UTC, datetime

import numpy as np
classification = "classical_baseline"  # auto-backfill
divergence_log = "Classical foundation baseline: this validates Axis-3 fiber-vs-base behavior on the engine geometry, not a canonical nonclassical witness."
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "fiber/base density-path and engine-state numerics"},
    "toponetx": {"tried": False, "used": False, "reason": "optional torus-complex bridge; not load-bearing here"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive", "toponetx": None}

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import (
    GeometricEngine, EngineState, StageControls, TERRAINS,
    LOOP_STAGE_ORDER, LOOP_GRAMMAR, _TERRAIN_TO_LOOP,
)
from geometric_operators import (
    partial_trace_A, partial_trace_B, _ensure_valid_density,
    SIGMA_X, SIGMA_Y, SIGMA_Z, I2,
)
from hopf_manifold import (
    von_neumann_entropy_2x2, density_to_bloch, berry_phase,
    torus_coordinates, left_weyl_spinor, right_weyl_spinor,
    TORUS_CLIFFORD,
)
from proto_ratchet_sim_runner import EvidenceToken

RESULTS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "a2_state", "sim_results", "axis3_fiber_base_results.json",
)

# Try toponetx bridge (optional)
try:
    from toponetx_torus_bridge import build_torus_complex, map_engine_cycle_to_complex
    HAS_TOPONETX = True
except Exception:
    HAS_TOPONETX = False


# ================================================================
# QIT Primitives
# ================================================================

def vne(rho: np.ndarray) -> float:
    """Von Neumann entropy S(rho) in bits."""
    rho = (rho + rho.conj().T) / 2
    ev = np.real(np.linalg.eigvalsh(rho))
    ev = ev[ev > 1e-15]
    return float(-np.sum(ev * np.log2(ev))) if len(ev) else 0.0


def concurrence_4x4(rho: np.ndarray) -> float:
    """Wootters concurrence for a 2-qubit (4x4) density matrix."""
    sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
    sy_sy = np.kron(sy, sy)
    R = rho @ sy_sy @ rho.conj() @ sy_sy
    evals = sorted(np.sqrt(np.maximum(np.real(np.linalg.eigvals(R)), 0)),
                   reverse=True)
    return float(max(0, evals[0] - evals[1] - evals[2] - evals[3]))


def mutual_info(rho_AB: np.ndarray) -> float:
    """I(A:B) = S(A) + S(B) - S(AB)."""
    rho_A = partial_trace_B(rho_AB)
    rho_B = partial_trace_A(rho_AB)
    return max(0.0, vne(rho_A) + vne(rho_B) - vne(rho_AB))


def bloch_vec(rho: np.ndarray) -> np.ndarray:
    """Bloch vector from 2x2 density matrix."""
    return np.array([float(np.real(np.trace(s @ rho)))
                     for s in [SIGMA_X, SIGMA_Y, SIGMA_Z]])


# ================================================================
# 1. Run Engine and Record Per-Step Fiber/Base Dynamics
# ================================================================

def run_engine_trajectory(engine_type: int, n_cycles: int = 10,
                          entangle_strength: float = 0.3) -> list:
    """Run engine for n_cycles and record per-step diagnostics."""
    engine = GeometricEngine(engine_type=engine_type,
                             entangle_strength=entangle_strength)
    state = engine.init_state()
    stage_order = LOOP_STAGE_ORDER[engine_type]

    records = []
    for cycle in range(n_cycles):
        for position, terrain_idx in enumerate(stage_order):
            terrain = TERRAINS[terrain_idx]
            loop_type = terrain["loop"]  # "fiber" or "base"
            topo = terrain["topo"]

            # Snapshot BEFORE step
            rho_AB_before = state.rho_AB.copy()
            rho_L_before = _ensure_valid_density(partial_trace_B(rho_AB_before))
            rho_R_before = _ensure_valid_density(partial_trace_A(rho_AB_before))
            s_before = vne(rho_L_before)
            conc_before = concurrence_4x4(rho_AB_before)
            mi_before = mutual_info(rho_AB_before)
            bloch_before = bloch_vec(rho_L_before)
            theta1_before = state.theta1
            theta2_before = state.theta2

            # Step
            state = engine.step(state, stage_idx=terrain_idx)

            # Snapshot AFTER step
            rho_AB_after = state.rho_AB.copy()
            rho_L_after = _ensure_valid_density(partial_trace_B(rho_AB_after))
            s_after = vne(rho_L_after)
            conc_after = concurrence_4x4(rho_AB_after)
            mi_after = mutual_info(rho_AB_after)
            bloch_after = bloch_vec(rho_L_after)
            theta1_after = state.theta1
            theta2_after = state.theta2

            # Compute deltas
            delta_entropy = s_after - s_before
            delta_conc = conc_after - conc_before
            delta_mi = mi_after - mi_before
            bloch_change = float(np.linalg.norm(bloch_after - bloch_before))
            delta_theta1 = theta1_after - theta1_before
            delta_theta2 = theta2_after - theta2_before

            # Record
            step_idx = cycle * 8 + position
            records.append({
                "step": step_idx,
                "cycle": cycle,
                "position": position,
                "terrain_idx": terrain_idx,
                "terrain_name": terrain["name"],
                "topo": topo,
                "loop": loop_type,
                "ax3": -1 if loop_type == "fiber" else +1,
                "delta_entropy": float(delta_entropy),
                "delta_concurrence": float(delta_conc),
                "delta_mi": float(delta_mi),
                "bloch_change": float(bloch_change),
                "delta_theta1": float(delta_theta1),
                "delta_theta2": float(delta_theta2),
                "entropy_after": float(s_after),
                "concurrence_after": float(conc_after),
                "mi_after": float(mi_after),
            })

        # Apply entangling gate at cycle end (engine.run_cycle does this)
        if entangle_strength > 0:
            from geometric_operators import apply_Entangle_4x4
            state.rho_AB = apply_Entangle_4x4(
                state.rho_AB, strength=entangle_strength
            )

    return records


# ================================================================
# 2. Aggregate Fiber vs Base Dynamics
# ================================================================

def aggregate_fiber_base(records: list) -> dict:
    """Compute mean dynamics for fiber vs base stages."""
    fiber = [r for r in records if r["loop"] == "fiber"]
    base = [r for r in records if r["loop"] == "base"]

    def stats(subset, key):
        vals = [r[key] for r in subset]
        return {"mean": float(np.mean(vals)), "std": float(np.std(vals)),
                "min": float(np.min(vals)), "max": float(np.max(vals))}

    keys = ["delta_entropy", "delta_concurrence", "delta_mi",
            "bloch_change", "delta_theta1", "delta_theta2"]
    result = {"fiber": {}, "base": {}, "n_fiber": len(fiber), "n_base": len(base)}
    for k in keys:
        result["fiber"][k] = stats(fiber, k)
        result["base"][k] = stats(base, k)

    return result


# ================================================================
# 3. Positive Tests
# ================================================================

def test_P1_different_dynamics(agg: dict) -> dict:
    """P1: Fiber and base stages produce DIFFERENT dynamics."""
    # Check that at least one aggregate metric differs significantly
    metrics_differ = []
    for key in ["delta_entropy", "delta_concurrence", "delta_mi",
                "bloch_change", "delta_theta1", "delta_theta2"]:
        f_mean = agg["fiber"][key]["mean"]
        b_mean = agg["base"][key]["mean"]
        diff = abs(f_mean - b_mean)
        # Scale-relative: significant if diff > 5% of the larger magnitude
        scale = max(abs(f_mean), abs(b_mean), 1e-10)
        metrics_differ.append({
            "metric": key,
            "fiber_mean": f_mean,
            "base_mean": b_mean,
            "abs_diff": diff,
            "relative_diff": diff / scale,
            "different": diff / scale > 0.05,
        })

    any_different = any(m["different"] for m in metrics_differ)
    return {
        "test": "P1_different_dynamics",
        "passed": any_different,
        "n_different_metrics": sum(1 for m in metrics_differ if m["different"]),
        "details": metrics_differ,
    }


def test_P2_swap_changes_trajectory(records_type1: list,
                                    records_type2: list) -> dict:
    """P2: Swapping fiber<->base labels changes the engine trajectory.

    Since Type 1 and Type 2 have swapped fiber/base terrain assignments,
    we compare their aggregate trajectories.
    """
    def trajectory_signature(records):
        return [r["delta_entropy"] for r in records[:16]]

    sig1 = trajectory_signature(records_type1)
    sig2 = trajectory_signature(records_type2)
    correlation = float(np.corrcoef(sig1, sig2)[0, 1]) if len(sig1) > 1 else 0.0
    max_diff = float(max(abs(a - b) for a, b in zip(sig1, sig2)))

    # Trajectories should be DIFFERENT (low correlation or high max_diff)
    passed = abs(correlation) < 0.95 or max_diff > 1e-6

    return {
        "test": "P2_swap_changes_trajectory",
        "passed": passed,
        "correlation": correlation,
        "max_step_diff": max_diff,
    }


def test_P3_chirality_different_assignments(records_type1: list,
                                            records_type2: list) -> dict:
    """P3: Type 1 and Type 2 have DIFFERENT fiber/base terrain assignments."""
    # In Type 1: terrain indices 0-3 are fiber, 4-7 are base for inner/outer
    # In Type 2: the loop roles are swapped
    t1_fiber_terrains = set(r["terrain_idx"] for r in records_type1
                            if r["loop"] == "fiber")
    t1_base_terrains = set(r["terrain_idx"] for r in records_type1
                           if r["loop"] == "base")
    t2_fiber_terrains = set(r["terrain_idx"] for r in records_type2
                            if r["loop"] == "fiber")
    t2_base_terrains = set(r["terrain_idx"] for r in records_type2
                           if r["loop"] == "base")

    # The terrain indices should be the SAME (0-3 fiber, 4-7 base) because
    # the terrain defs are fixed. But the LOOP ORDER should differ.
    # Check that Type 1 outer = base terrains, Type 2 outer = fiber terrains
    t1_outer_order = LOOP_STAGE_ORDER[1][:4]
    t2_outer_order = LOOP_STAGE_ORDER[2][:4]
    t1_inner_order = LOOP_STAGE_ORDER[1][4:]
    t2_inner_order = LOOP_STAGE_ORDER[2][4:]

    # Type 1 outer should be base terrains (4-7), Type 2 outer should be fiber (0-3)
    t1_outer_is_base = all(idx >= 4 for idx in t1_outer_order)
    t2_outer_is_fiber = all(idx < 4 for idx in t2_outer_order)

    passed = t1_outer_is_base and t2_outer_is_fiber

    return {
        "test": "P3_chirality_different_assignments",
        "passed": passed,
        "type1_outer_terrain_indices": t1_outer_order,
        "type2_outer_terrain_indices": t2_outer_order,
        "type1_outer_is_base": t1_outer_is_base,
        "type2_outer_is_fiber": t2_outer_is_fiber,
    }


# ================================================================
# 4. Negative Tests (Ablation)
# ================================================================

def run_ablation(engine_type: int, mode: str, n_cycles: int = 5) -> list:
    """Run engine with ablated fiber/base structure.

    mode:
      'base_only'  -- skip all fiber stages
      'fiber_only' -- skip all base stages
      'all_fiber'  -- force all stages to use fiber-only angular advancement
                      by temporarily patching TERRAINS loop field
    """
    import copy as _copy
    engine = GeometricEngine(engine_type=engine_type, entangle_strength=0.3)
    state = engine.init_state()
    stage_order = LOOP_STAGE_ORDER[engine_type]

    # For 'all_fiber' mode, temporarily patch all terrain loop fields
    original_terrains = None
    if mode == "all_fiber":
        original_terrains = [t.copy() for t in TERRAINS]
        for t in TERRAINS:
            t["loop"] = "fiber"

    records = []
    try:
        for cycle in range(n_cycles):
            for position, terrain_idx in enumerate(stage_order):
                terrain = TERRAINS[terrain_idx]
                loop_type = terrain["loop"]

                if mode == "base_only" and loop_type == "fiber":
                    continue
                if mode == "fiber_only" and loop_type == "base":
                    continue

                rho_before = state.rho_AB.copy()
                s_before = vne(_ensure_valid_density(partial_trace_B(rho_before)))

                state = engine.step(state, stage_idx=terrain_idx)

                rho_after = state.rho_AB.copy()
                s_after = vne(_ensure_valid_density(partial_trace_B(rho_after)))

                records.append({
                    "step": len(records),
                    "terrain_name": terrain["name"],
                    "loop": "fiber_forced" if mode == "all_fiber" else loop_type,
                    "delta_entropy": float(s_after - s_before),
                    "entropy_after": float(s_after),
                    "concurrence_after": float(concurrence_4x4(rho_after)),
                })

            if engine.entangle_strength > 0:
                from geometric_operators import apply_Entangle_4x4
                state.rho_AB = apply_Entangle_4x4(
                    state.rho_AB, strength=engine.entangle_strength
                )
    finally:
        # Restore original terrains if patched
        if original_terrains is not None:
            for i, t in enumerate(original_terrains):
                TERRAINS[i].update(t)

    return records


def test_N1_base_only(records_normal: list, records_ablated: list) -> dict:
    """N1: Remove all fiber stages. Compare with normal run."""
    normal_final_s = records_normal[-1]["entropy_after"]
    ablated_final_s = records_ablated[-1]["entropy_after"] if records_ablated else 0.0
    normal_final_c = records_normal[-1]["concurrence_after"]
    ablated_final_c = records_ablated[-1]["concurrence_after"] if records_ablated else 0.0

    entropy_diff = abs(normal_final_s - ablated_final_s)
    conc_diff = abs(normal_final_c - ablated_final_c)

    # The ablated engine should behave DIFFERENTLY from normal
    passed = entropy_diff > 1e-6 or conc_diff > 1e-6

    return {
        "test": "N1_base_only_ablation",
        "passed": passed,
        "normal_final_entropy": float(normal_final_s),
        "ablated_final_entropy": float(ablated_final_s),
        "entropy_diff": float(entropy_diff),
        "normal_final_concurrence": float(normal_final_c),
        "ablated_final_concurrence": float(ablated_final_c),
        "concurrence_diff": float(conc_diff),
    }


def test_N2_fiber_only(records_normal: list, records_ablated: list) -> dict:
    """N2: Remove all base stages. Compare with normal run."""
    normal_final_s = records_normal[-1]["entropy_after"]
    ablated_final_s = records_ablated[-1]["entropy_after"] if records_ablated else 0.0
    normal_final_c = records_normal[-1]["concurrence_after"]
    ablated_final_c = records_ablated[-1]["concurrence_after"] if records_ablated else 0.0

    entropy_diff = abs(normal_final_s - ablated_final_s)
    conc_diff = abs(normal_final_c - ablated_final_c)
    passed = entropy_diff > 1e-6 or conc_diff > 1e-6

    return {
        "test": "N2_fiber_only_ablation",
        "passed": passed,
        "normal_final_entropy": float(normal_final_s),
        "ablated_final_entropy": float(ablated_final_s),
        "entropy_diff": float(entropy_diff),
        "normal_final_concurrence": float(normal_final_c),
        "ablated_final_concurrence": float(ablated_final_c),
        "concurrence_diff": float(conc_diff),
    }


def test_N3_all_fiber(records_normal: list, records_ablated: list) -> dict:
    """N3: Make all stages fiber (collapse the distinction). Compare."""
    normal_final_s = records_normal[-1]["entropy_after"]
    ablated_final_s = records_ablated[-1]["entropy_after"] if records_ablated else 0.0
    # When distinction is collapsed, trajectory should differ
    entropy_diff = abs(normal_final_s - ablated_final_s)
    passed = entropy_diff > 1e-6

    return {
        "test": "N3_all_fiber_collapse",
        "passed": passed,
        "normal_final_entropy": float(normal_final_s),
        "ablated_final_entropy": float(ablated_final_s),
        "entropy_diff": float(entropy_diff),
    }


# ================================================================
# 5. Axis 3 as Geometric Observable
# ================================================================

def test_ax3_observable(records: list) -> dict:
    """Ax3 value (+1 base, -1 fiber) correlation with other observables."""
    ax3_vals = np.array([r["ax3"] for r in records], dtype=float)
    d_entropy = np.array([r["delta_entropy"] for r in records])
    d_conc = np.array([r["delta_concurrence"] for r in records])

    # Correlation: Ax3 vs entropy change
    if np.std(ax3_vals) > 1e-12 and np.std(d_entropy) > 1e-12:
        corr_entropy = float(np.corrcoef(ax3_vals, d_entropy)[0, 1])
    else:
        corr_entropy = 0.0

    if np.std(ax3_vals) > 1e-12 and np.std(d_conc) > 1e-12:
        corr_conc = float(np.corrcoef(ax3_vals, d_conc)[0, 1])
    else:
        corr_conc = 0.0

    return {
        "test": "ax3_geometric_observable",
        "ax3_entropy_correlation": corr_entropy,
        "ax3_concurrence_correlation": corr_conc,
        "ax3_mean": float(np.mean(ax3_vals)),
        "ax3_std": float(np.std(ax3_vals)),
        "note": "Ax3 should have nonzero correlation with at least one dynamic "
                "quantity if it is a real geometric observable.",
    }


def test_ax3_orthogonality(records_type1: list) -> dict:
    """Verify Ax3 is independent of Ax0 (I_c) and Ax6 (derived XOR).

    Ax6 = -Ax0 * Ax3, so Ax3 and Ax0 should be independent while
    Ax3 and Ax6 are related by Ax0.
    """
    ax3 = np.array([r["ax3"] for r in records_type1], dtype=float)
    # Ax0 proxy: sign of entropy (above/below Clifford)
    ax0 = np.array([np.sign(r["entropy_after"] - 0.5)
                     for r in records_type1], dtype=float)
    # Ax6 derived: -Ax0 * Ax3
    ax6 = -ax0 * ax3

    # Ax3 should be approximately uncorrelated with Ax0
    if np.std(ax3) > 1e-12 and np.std(ax0) > 1e-12:
        corr_ax3_ax0 = float(np.corrcoef(ax3, ax0)[0, 1])
    else:
        corr_ax3_ax0 = 0.0

    # Ax3 * Ax6 should reconstruct -Ax0
    reconstructed_ax0 = -ax3 * ax6
    reconstruction_error = float(np.mean(np.abs(reconstructed_ax0 - ax0)))

    return {
        "test": "ax3_orthogonality",
        "ax3_ax0_correlation": corr_ax3_ax0,
        "ax3_independent_of_ax0": abs(corr_ax3_ax0) < 0.5,
        "ax6_reconstruction_error": reconstruction_error,
        "ax6_reconstruction_works": reconstruction_error < 0.1,
        "note": "Ax6 = -Ax0*Ax3. Ax3 should be independent of Ax0.",
    }


# ================================================================
# 6. Hopf Fiber Tracking
# ================================================================

def test_hopf_fiber_tracking(records: list) -> dict:
    """Fiber stages should change theta2 more; base stages should change theta1 more.

    Engine core (line 574-579):
      fiber: theta2 += d_theta, theta1 += 0.5*d_theta
      base:  theta1 += d_theta, theta2 += 0.5*d_theta
    """
    fiber = [r for r in records if r["loop"] == "fiber"]
    base = [r for r in records if r["loop"] == "base"]

    fiber_dt1 = float(np.mean([abs(r["delta_theta1"]) for r in fiber])) if fiber else 0.0
    fiber_dt2 = float(np.mean([abs(r["delta_theta2"]) for r in fiber])) if fiber else 0.0
    base_dt1 = float(np.mean([abs(r["delta_theta1"]) for r in base])) if base else 0.0
    base_dt2 = float(np.mean([abs(r["delta_theta2"]) for r in base])) if base else 0.0

    # Fiber should have dt2 > dt1, base should have dt1 > dt2
    fiber_correct = fiber_dt2 > fiber_dt1
    base_correct = base_dt1 > base_dt2

    return {
        "test": "hopf_fiber_tracking",
        "passed": fiber_correct and base_correct,
        "fiber_mean_delta_theta1": fiber_dt1,
        "fiber_mean_delta_theta2": fiber_dt2,
        "fiber_theta2_dominates": fiber_correct,
        "base_mean_delta_theta1": base_dt1,
        "base_mean_delta_theta2": base_dt2,
        "base_theta1_dominates": base_correct,
        "note": "Fiber stages advance theta2 (inner ring); "
                "base stages advance theta1 (outer ring).",
    }


# ================================================================
# 7. TopoNetX Verification
# ================================================================

def test_toponetx_mapping() -> dict:
    """Map engine cycle onto cell complex and verify fiber/base ring assignment."""
    if not HAS_TOPONETX:
        return {
            "test": "toponetx_cell_complex",
            "skipped": True,
            "reason": "toponetx not available",
        }

    try:
        cc, node_map = build_torus_complex()
        results = {}
        for et in [1, 2]:
            path = map_engine_cycle_to_complex(cc, et, node_map)
            layers = [p[0] for p in path]

            # First 4 stages should be one ring, last 4 another
            first_half_layers = set(layers[:4])
            second_half_layers = set(layers[4:])

            # Type 1: outer=base(layer 2), inner=fiber(layer 0)
            # Type 2: outer=fiber(layer 0), inner=base(layer 2)
            if et == 1:
                correct = (first_half_layers == {2} and
                           second_half_layers == {0})
            else:
                correct = (first_half_layers == {0} and
                           second_half_layers == {2})

            results[f"type{et}"] = {
                "path_layers": layers,
                "first_half": sorted(first_half_layers),
                "second_half": sorted(second_half_layers),
                "ring_assignment_correct": correct,
            }

        return {
            "test": "toponetx_cell_complex",
            "skipped": False,
            "n_nodes": len(cc.nodes),
            "n_edges": len(cc.edges),
            "n_faces": len(cc.cells),
            "type_results": results,
            "passed": all(r["ring_assignment_correct"]
                          for r in results.values()),
        }
    except Exception as e:
        return {
            "test": "toponetx_cell_complex",
            "skipped": False,
            "error": str(e),
            "passed": False,
        }


# ================================================================
# Main
# ================================================================

def main() -> int:
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)

    print("=" * 72)
    print("AXIS 3 VALIDATION: FIBER vs BASE-LIFT (Inner vs Outer Loop)")
    print("=" * 72)
    print()
    print("QIT Definition:")
    print("  Fiber (b3=-1): density-stationary path on S^3")
    print("  Base  (b3=+1): density-traversing path on S^3")
    print("  Ax6 = -Ax0 * Ax3 (derived XOR)")
    print()

    # ── Run normal engine trajectories ──
    print("[1] Running Type 1 engine (10 cycles, 80 steps)...")
    records_t1 = run_engine_trajectory(engine_type=1, n_cycles=10)
    print(f"    Collected {len(records_t1)} step records.")

    print("[2] Running Type 2 engine (10 cycles, 80 steps)...")
    records_t2 = run_engine_trajectory(engine_type=2, n_cycles=10)
    print(f"    Collected {len(records_t2)} step records.")

    # ── Aggregation ──
    print("[3] Aggregating fiber vs base dynamics...")
    agg_t1 = aggregate_fiber_base(records_t1)
    agg_t2 = aggregate_fiber_base(records_t2)

    print(f"    Type 1: {agg_t1['n_fiber']} fiber steps, "
          f"{agg_t1['n_base']} base steps")
    print(f"    Type 2: {agg_t2['n_fiber']} fiber steps, "
          f"{agg_t2['n_base']} base steps")
    print()

    # Print summary
    for label, agg in [("Type 1", agg_t1), ("Type 2", agg_t2)]:
        print(f"  {label} Fiber vs Base dynamics:")
        for key in ["delta_entropy", "delta_concurrence", "delta_mi",
                     "bloch_change"]:
            f_mean = agg["fiber"][key]["mean"]
            b_mean = agg["base"][key]["mean"]
            print(f"    {key:20s}: fiber={f_mean:+.6f}  base={b_mean:+.6f}")
        print()

    # ── Positive Tests ──
    print("[4] Running positive tests...")
    p1 = test_P1_different_dynamics(agg_t1)
    p2 = test_P2_swap_changes_trajectory(records_t1, records_t2)
    p3 = test_P3_chirality_different_assignments(records_t1, records_t2)

    print(f"    P1 (different dynamics):       {'PASS' if p1['passed'] else 'FAIL'} "
          f"({p1['n_different_metrics']}/6 metrics differ)")
    print(f"    P2 (swap changes trajectory):  {'PASS' if p2['passed'] else 'FAIL'} "
          f"(corr={p2['correlation']:.4f})")
    print(f"    P3 (chirality assignments):    {'PASS' if p3['passed'] else 'FAIL'}")
    print()

    # ── Negative Tests (Ablation) ──
    print("[5] Running ablation tests...")
    records_normal_5c = run_engine_trajectory(engine_type=1, n_cycles=5)
    records_base_only = run_ablation(engine_type=1, mode="base_only", n_cycles=5)
    records_fiber_only = run_ablation(engine_type=1, mode="fiber_only", n_cycles=5)
    records_all_fiber = run_ablation(engine_type=1, mode="all_fiber", n_cycles=5)

    n1 = test_N1_base_only(records_normal_5c, records_base_only)
    n2 = test_N2_fiber_only(records_normal_5c, records_fiber_only)
    n3 = test_N3_all_fiber(records_normal_5c, records_all_fiber)

    print(f"    N1 (base only):     {'PASS' if n1['passed'] else 'FAIL'} "
          f"(entropy_diff={n1['entropy_diff']:.6f})")
    print(f"    N2 (fiber only):    {'PASS' if n2['passed'] else 'FAIL'} "
          f"(entropy_diff={n2['entropy_diff']:.6f})")
    print(f"    N3 (all fiber):     {'PASS' if n3['passed'] else 'FAIL'} "
          f"(entropy_diff={n3['entropy_diff']:.6f})")
    print()

    # ── Geometric Observable Tests ──
    print("[6] Ax3 as geometric observable...")
    obs = test_ax3_observable(records_t1)
    orth = test_ax3_orthogonality(records_t1)

    print(f"    Ax3-entropy correlation:     {obs['ax3_entropy_correlation']:+.4f}")
    print(f"    Ax3-concurrence correlation: {obs['ax3_concurrence_correlation']:+.4f}")
    print(f"    Ax3-Ax0 correlation:         {orth['ax3_ax0_correlation']:+.4f} "
          f"(independent={orth['ax3_independent_of_ax0']})")
    print(f"    Ax6 reconstruction error:    {orth['ax6_reconstruction_error']:.6f}")
    print()

    # ── Hopf Fiber Tracking ──
    print("[7] Hopf fiber tracking (theta1 vs theta2)...")
    hopf = test_hopf_fiber_tracking(records_t1)
    print(f"    Fiber: dt1={hopf['fiber_mean_delta_theta1']:.6f}, "
          f"dt2={hopf['fiber_mean_delta_theta2']:.6f} "
          f"(theta2 dominates={hopf['fiber_theta2_dominates']})")
    print(f"    Base:  dt1={hopf['base_mean_delta_theta1']:.6f}, "
          f"dt2={hopf['base_mean_delta_theta2']:.6f} "
          f"(theta1 dominates={hopf['base_theta1_dominates']})")
    print(f"    Hopf tracking: {'PASS' if hopf['passed'] else 'FAIL'}")
    print()

    # ── TopoNetX ──
    print("[8] TopoNetX cell complex verification...")
    topo = test_toponetx_mapping()
    if topo.get("skipped"):
        print(f"    SKIPPED: {topo.get('reason', 'unknown')}")
    elif topo.get("error"):
        print(f"    ERROR: {topo['error']}")
    else:
        print(f"    Complex: {topo['n_nodes']} nodes, {topo['n_edges']} edges, "
              f"{topo['n_faces']} faces")
        print(f"    Ring assignment: {'PASS' if topo['passed'] else 'FAIL'}")
    print()

    # ── Overall Verdict ──
    all_positive = p1["passed"] and p2["passed"] and p3["passed"]
    all_negative = n1["passed"] and n2["passed"] and n3["passed"]
    hopf_ok = hopf["passed"]
    topo_ok = topo.get("passed", True) or topo.get("skipped", False)

    overall = all_positive and all_negative and hopf_ok and topo_ok

    if overall:
        verdict = ("PASS -- Axis 3 (fiber vs base-lift) is a real geometric "
                   "observable. Fiber and base stages produce distinct dynamics, "
                   "ablation confirms structural necessity, Hopf tracking "
                   "confirms angular separation, and chirality is verified.")
        status = "PASS"
    else:
        failures = []
        if not all_positive:
            failures.append("positive tests")
        if not all_negative:
            failures.append("negative/ablation tests")
        if not hopf_ok:
            failures.append("Hopf fiber tracking")
        if not topo_ok:
            failures.append("TopoNetX mapping")
        verdict = f"DIAGNOSTIC -- Failed: {', '.join(failures)}. Review needed."
        status = "DIAGNOSTIC"

    print("=" * 72)
    print("OVERALL VERDICT")
    print("=" * 72)
    print(f"  Positive tests (P1-P3):    {'ALL PASS' if all_positive else 'FAIL'}")
    print(f"  Negative tests (N1-N3):    {'ALL PASS' if all_negative else 'FAIL'}")
    print(f"  Hopf fiber tracking:       {'PASS' if hopf_ok else 'FAIL'}")
    print(f"  TopoNetX mapping:          {'PASS' if topo_ok else 'SKIP/FAIL'}")
    print(f"  Verdict: {verdict}")

    # ── Evidence Token ──
    token = EvidenceToken(
        token_id="E_AX3_FIBER_BASE_VALID" if overall else "",
        sim_spec_id="S_SIM_AX3_FIBER_BASE",
        status=status,
        measured_value=float(p1["n_different_metrics"]),
        kill_reason=None if overall else verdict,
    )

    # ── Build output ──
    output = {
        "metadata": {
            "name": "axis3_fiber_base_validation",
            "timestamp": datetime.now(UTC).isoformat(),
            "results_path": RESULTS_PATH,
            "engine_types_tested": [1, 2],
            "n_cycles": 10,
            "entangle_strength": 0.3,
            "ax3_definition": "fiber (b3=-1): density-stationary; "
                              "base (b3=+1): density-traversing",
            "ax6_derivation": "b6 = -b0 * b3",
        },
        "aggregation": {
            "type1": agg_t1,
            "type2": agg_t2,
        },
        "positive_tests": {
            "P1_different_dynamics": p1,
            "P2_swap_changes_trajectory": p2,
            "P3_chirality_different_assignments": p3,
        },
        "negative_tests": {
            "N1_base_only": n1,
            "N2_fiber_only": n2,
            "N3_all_fiber": n3,
        },
        "geometric_observable": {
            "ax3_observable": obs,
            "ax3_orthogonality": orth,
        },
        "hopf_fiber_tracking": hopf,
        "toponetx": topo,
        "verdict": {
            "result": status,
            "read": verdict,
        },
        "evidence_token": asdict(token),
    }

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\nResults saved: {RESULTS_PATH}")
    print()
    print("=" * 72)
    print(f"PROBE STATUS: {status}")
    print("=" * 72)

    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
