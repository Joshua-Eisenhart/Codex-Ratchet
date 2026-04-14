#!/usr/bin/env python3
"""
Layer 4 Validation SIM — Engine Family Split
============================================
Type 1 vs Type 2 as complete cycles on the live engine core.

From the source doc:
  CANON: Axis-3 = engine-family split (Type-1 vs Type-2).
  HYPOTHESIS: This split manifests as left/right Weyl spinor selection.

  Type 1: Fe/Ti dominant on base, Te/Fi on fiber

  Type 2: Te/Fi dominant on base, Fe/Ti on fiber

Conservative engine-family properties:
  - Type 1 final sheet states differ from Type 2 on the same initial state
  - Type 1 and Type 2 produce different negentropy trajectories
  - Type 1 and Type 2 differ in runtime axis readouts
  - Type 1 and Type 2 swap operator-family dominance across base and fiber

Token: E_ENGINE_CHIRALITY_VALID
"""

import copy
import numpy as np
import os
import sys
import json
from datetime import datetime, UTC
classification = "classical_baseline"  # auto-backfill

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hopf_manifold import (
    random_s3_point, coherent_state_density, density_to_bloch,
    hopf_map, torus_coordinates,
)
from geometric_operators import (
    trace_distance_2x2,
)
from engine_core import GeometricEngine, StageControls
from proto_ratchet_sim_runner import EvidenceToken


def run_live_engine_pair(shared_state) -> tuple[dict, dict]:
    """Run the actual engine core for both families from one shared initial state."""
    engine1 = GeometricEngine(engine_type=1)
    engine2 = GeometricEngine(engine_type=2)
    state1 = engine1.run_cycle(copy.deepcopy(shared_state))
    state2 = engine2.run_cycle(copy.deepcopy(shared_state))
    axes1 = engine1.read_axes(state1)
    axes2 = engine2.read_axes(state2)

    return (
        {
            "state": state1,
            "axes": axes1,
            "total_dphi_L": float(sum(h["dphi_L"] for h in state1.history)),
            "total_dphi_R": float(sum(h["dphi_R"] for h in state1.history)),
        },
        {
            "state": state2,
            "axes": axes2,
            "total_dphi_L": float(sum(h["dphi_L"] for h in state2.history)),
            "total_dphi_R": float(sum(h["dphi_R"] for h in state2.history)),
        },
    )


def run_L4_validation():
    print("=" * 72)
    print("LAYER 4: ENGINE FAMILY VALIDATION (AXIS 3 — CANON: engine-family split)")
    print("  'Type 1 vs Type 2 on the live engine core'")
    print("=" * 72)

    rng = np.random.default_rng(42)
    n_trials = 50
    all_pass = True
    results = {}

    # ── Test 1: Type 1 ≠ Type 2 on same initial state ────────────
    print("\n  [T1] Engine-family distinction on the live engine...")
    family_distinct = True
    total_dist_L = 0.0
    total_dist_R = 0.0
    for _ in range(n_trials):
        shared = GeometricEngine(engine_type=1).init_state(rng=rng)
        r1, r2 = run_live_engine_pair(shared)
        dist_L = trace_distance_2x2(r1["state"].rho_L, r2["state"].rho_L)
        dist_R = trace_distance_2x2(r1["state"].rho_R, r2["state"].rho_R)
        total_dist_L += dist_L
        total_dist_R += dist_R
        if dist_L < 1e-4 and dist_R < 1e-4:
            family_distinct = False

    avg_dist_L = total_dist_L / n_trials
    avg_dist_R = total_dist_R / n_trials
    results["family_distinct"] = bool(family_distinct)
    results["avg_left_sheet_distance"] = float(avg_dist_L)
    results["avg_right_sheet_distance"] = float(avg_dist_R)
    print(f"    {'✓' if family_distinct else '✗'} Left-sheet avg distance = {avg_dist_L:.4f}")
    print(f"      Right-sheet avg distance = {avg_dist_R:.4f}")
    all_pass = all_pass and family_distinct

    # ── Test 2: Both engines are CPTP (output is valid density) ──
    print("\n  [T2] Engine output validity...")
    output_valid = True
    for _ in range(n_trials):
        shared = GeometricEngine(engine_type=1).init_state(rng=rng)
        r1, r2 = run_live_engine_pair(shared)

        for rho_out in [r1["state"].rho_L, r1["state"].rho_R, r2["state"].rho_L, r2["state"].rho_R]:
            evals = np.linalg.eigvalsh(rho_out)
            if np.min(evals) < -1e-8 or abs(np.real(np.trace(rho_out)) - 1.0) > 1e-8:
                output_valid = False
    results["output_valid"] = bool(output_valid)
    print(f"    {'✓' if output_valid else '✗'} Both engines produce valid density matrices")
    all_pass = all_pass and output_valid

    # ── Test 3: Negentropy evolution differs between types ───────
    print("\n  [T3] Sheet negentropy trajectory divergence...")
    shared = GeometricEngine(engine_type=1).init_state(rng=rng)
    r1, r2 = run_live_engine_pair(shared)
    dphi_L_divergence = abs(r1["total_dphi_L"] - r2["total_dphi_L"])
    dphi_R_divergence = abs(r1["total_dphi_R"] - r2["total_dphi_R"])
    diverges = dphi_L_divergence > 1e-4 and dphi_R_divergence > 1e-4
    results["dphi_L_divergence"] = float(dphi_L_divergence)
    results["dphi_R_divergence"] = float(dphi_R_divergence)
    results["type1_total_dphi_L"] = float(r1["total_dphi_L"])
    results["type2_total_dphi_L"] = float(r2["total_dphi_L"])
    results["type1_total_dphi_R"] = float(r1["total_dphi_R"])
    results["type2_total_dphi_R"] = float(r2["total_dphi_R"])
    print(f"    Type 1 total ΔΦ_L: {r1['total_dphi_L']:+.6f}")
    print(f"    Type 2 total ΔΦ_L: {r2['total_dphi_L']:+.6f}")
    print(f"    Type 1 total ΔΦ_R: {r1['total_dphi_R']:+.6f}")
    print(f"    Type 2 total ΔΦ_R: {r2['total_dphi_R']:+.6f}")
    print(f"    {'✓' if diverges else '✗'} Left/right sheet trajectories diverge across engine families")
    all_pass = all_pass and diverges

    # ── Test 4: Runtime axis readouts differ between types ───────
    print("\n  [T4] Runtime axis-readout divergence...")
    ga4_diff = abs(r1["axes"]["GA4_variance"] - r2["axes"]["GA4_variance"])
    ga5_diff = abs(r1["axes"]["GA5_coupling"] - r2["axes"]["GA5_coupling"])
    axes_diverge = ga4_diff > 1e-4 and ga5_diff > 1e-4
    results["ga4_difference"] = float(ga4_diff)
    results["ga5_difference"] = float(ga5_diff)
    results["axes_diverge"] = bool(axes_diverge)
    print(f"    GA4 difference: {ga4_diff:.6f}")
    print(f"    GA5 difference: {ga5_diff:.6f}")
    print(f"    {'✓' if axes_diverge else '✗'} Runtime axis readouts differ across engine families")
    all_pass = all_pass and axes_diverge

    # ── Test 5: Dominance allocation swaps across base/fiber ─────
    print("\n  [T5] Operator-family dominance swap...")
    controls = StageControls(piston=0.5, lever=True)
    engine1 = GeometricEngine(engine_type=1)
    engine2 = GeometricEngine(engine_type=2)
    fiber = next(stage for stage in engine1.stages if stage["name"] == "Se_f")
    base = next(stage for stage in engine1.stages if stage["name"] == "Se_b")

    e1_fiber = {op: engine1._operator_strength(fiber, op, controls, ga0_level=0.5) for op in ("Ti", "Fe", "Te", "Fi")}
    e1_base = {op: engine1._operator_strength(base, op, controls, ga0_level=0.5) for op in ("Ti", "Fe", "Te", "Fi")}
    e2_fiber = {op: engine2._operator_strength(fiber, op, controls, ga0_level=0.5) for op in ("Ti", "Fe", "Te", "Fi")}
    e2_base = {op: engine2._operator_strength(base, op, controls, ga0_level=0.5) for op in ("Ti", "Fe", "Te", "Fi")}

    type1_swap = e1_base["Ti"] > e1_base["Te"] and e1_base["Fe"] > e1_base["Fi"] and e1_fiber["Te"] > e1_fiber["Ti"] and e1_fiber["Fi"] > e1_fiber["Fe"]
    type2_swap = e2_base["Te"] > e2_base["Ti"] and e2_base["Fi"] > e2_base["Fe"] and e2_fiber["Ti"] > e2_fiber["Te"] and e2_fiber["Fe"] > e2_fiber["Fi"]
    dominance_swap = type1_swap and type2_swap
    results["type1_base_strengths"] = e1_base
    results["type1_fiber_strengths"] = e1_fiber
    results["type2_base_strengths"] = e2_base
    results["type2_fiber_strengths"] = e2_fiber
    results["dominance_swap"] = bool(dominance_swap)
    print(f"    Type 1 base strengths: {e1_base}")
    print(f"    Type 1 fiber strengths: {e1_fiber}")
    print(f"    Type 2 base strengths: {e2_base}")
    print(f"    Type 2 fiber strengths: {e2_fiber}")
    print(f"    {'✓' if dominance_swap else '✗'} Base/fiber dominance swaps between engine families")
    all_pass = all_pass and dominance_swap

    # ── Verdict ───────────────────────────────────────────────────
    print(f"\n{'=' * 72}")
    print(f"  LAYER 4 VERDICT: {'PASS ✓' if all_pass else 'KILL ✗'}")
    print(f"{'=' * 72}")

    tokens = []
    if all_pass:
        tokens.append(EvidenceToken(
            "E_ENGINE_CHIRALITY_VALID", "S_L4_ENGINE_CHIRALITY",
            "PASS", float(avg_dist_L + avg_dist_R)
        ))
    else:
        failed = [k for k, v in results.items() if v is False]
        tokens.append(EvidenceToken(
            "", "S_L4_ENGINE_CHIRALITY", "KILL", 0.0,
            f"FAILED: {', '.join(failed)}"
        ))

    # Save
    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base_dir, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "L4_engine_chirality_results.json")
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "layer": 4,
            "name": "Engine_Chirality_Validation",
            "results": results,
            "evidence_ledger": [t.__dict__ for t in tokens],
        }, f, indent=2, default=str)
    print(f"  Results saved: {outpath}")
    return tokens


if __name__ == "__main__":
    run_L4_validation()
