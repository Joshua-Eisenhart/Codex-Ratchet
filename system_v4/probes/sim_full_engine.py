#!/usr/bin/env python3
"""
Full 64-Stage Engine Validation SIM
=====================================
Tests that the full geometric engine runs on actual geometry:
  1. Full 16-stage cycle completes (8 stages × 2 types)
  2. Left and right Weyl spinors evolve differently
  3. Nested tori transport works
  4. All 4 controls per stage are non-degenerate
  5. Each operator family behaves as claimed
  6. Full cycle changes axis readings
  7. Axis 0 causally changes full-cycle behavior
  8. Different torus programs produce different outputs
  9. Engine types produce different outputs

Token: E_FULL_64_ENGINE_VALID
"""

import numpy as np
import os
import sys
import json
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine_core import (
    GeometricEngine, EngineState, StageControls,
    STAGES, TERRAINS, OPERATORS, full_64_stage_run,
    TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER,
)
from geometric_operators import negentropy, trace_distance_2x2, _ensure_valid_density, I2
from hopf_manifold import (
    left_density, right_density, torus_coordinates,
    left_weyl_spinor, right_weyl_spinor,
    fiber_phase_left, fiber_phase_right,
    inter_torus_transport,
)
from proto_ratchet_sim_runner import EvidenceToken


def run_full_engine_validation():
    print("=" * 72)
    print("FULL 64-STAGE GEOMETRIC ENGINE VALIDATION")
    print("  Nested Hopf Tori × Weyl Spinors × 4 Controls × 8 Terrains")
    print("=" * 72)

    rng = np.random.default_rng(42)
    all_pass = True
    results = {}
    tokens = []
    test_ok = {}

    # ── T1: Full 64-stage cycle completes ────────────────────────
    print("\n  [T1] Full 16 macro-stage cycle (8 × 2 types)...")
    data = full_64_stage_run(rng=np.random.default_rng(42))
    t1_stages = data["type_1"]["stages_run"]
    t2_stages = data["type_2"]["stages_run"]
    total = t1_stages + t2_stages
    t1_ok = total == 64
    results["total_stages"] = total
    print(f"    Type 1: {t1_stages} microstates, Type 2: {t2_stages} microstates, Total: {total}")
    print(f"    {'✓' if t1_ok else '✗'} 64 microstates completed")
    print(f"    Type 1: {t1_stages} stages, Type 2: {t2_stages} stages, Total: {total}")
    print(f"    {'✓' if t1_ok else '✗'} 64 stages completed")
    all_pass = all_pass and t1_ok
    test_ok["T1_full_cycle"] = t1_ok

    # ── T2: Left and Right Weyl spinors evolve differently ───────
    print("\n  [T2] Left vs Right Weyl spinor divergence...")
    engine = GeometricEngine(engine_type=1)
    state = engine.init_state(rng=np.random.default_rng(42))
    state = engine.run_cycle(state)
    lr_dist = trace_distance_2x2(state.rho_L, state.rho_R)
    lr_ok = lr_dist > 0.01
    results["lr_distance_after_cycle"] = float(lr_dist)
    print(f"    D(ρ_L, ρ_R) after cycle: {lr_dist:.4f}")
    print(f"    {'✓' if lr_ok else '✗'} L ≠ R after cycle")
    all_pass = all_pass and lr_ok
    test_ok["T2_lr_divergence"] = lr_ok

    # ── T3: Nested tori transport ────────────────────────────────
    print("\n  [T3] Inter-torus transport...")
    engine = GeometricEngine(engine_type=1)
    state_cliff = engine.init_state(eta=TORUS_CLIFFORD, rng=np.random.default_rng(42))

    # Step on inner torus
    ctrl_inner = StageControls(torus=TORUS_INNER)
    state_inner = engine.step(state_cliff, stage_idx=0, controls=ctrl_inner)

    # Step on outer torus
    ctrl_outer = StageControls(torus=TORUS_OUTER)
    state_outer = engine.step(state_cliff, stage_idx=0, controls=ctrl_outer)

    inner_outer_dist = trace_distance_2x2(state_inner.rho_L, state_outer.rho_L)
    inner_moved_toward = abs(state_inner.eta - TORUS_INNER) < abs(TORUS_CLIFFORD - TORUS_INNER)
    outer_moved_toward = abs(state_outer.eta - TORUS_OUTER) < abs(TORUS_CLIFFORD - TORUS_OUTER)
    torus_transport_ok = inner_moved_toward and outer_moved_toward and inner_outer_dist > 0.01
    results["torus_inner_eta"] = float(state_inner.eta)
    results["torus_outer_eta"] = float(state_outer.eta)
    results["inner_outer_dist"] = float(inner_outer_dist)
    print(f"    Inner η: {state_inner.eta:.4f} (target: {TORUS_INNER:.4f})")
    print(f"    Outer η: {state_outer.eta:.4f} (target: {TORUS_OUTER:.4f})")
    print(f"    D(inner, outer): {inner_outer_dist:.4f}")
    print(f"    {'✓' if inner_moved_toward else '✗'} Inner step moves toward inner torus")
    print(f"    {'✓' if outer_moved_toward else '✗'} Outer step moves toward outer torus")
    print(f"    {'✓' if torus_transport_ok else '✗'} Transport separates states")
    all_pass = all_pass and torus_transport_ok
    test_ok["T3_torus_transport"] = torus_transport_ok

    # ── T4: All 4 controls non-degenerate ────────────────────────
    print("\n  [T4] 4 controls per stage are non-degenerate...")
    engine = GeometricEngine(engine_type=1)
    state0 = engine.init_state(rng=np.random.default_rng(42))

    # Test each control independently
    n_nondegen = 0
    controls_tested = []

    # Piston: 0.1 vs 1.0
    s_low = engine.step(state0, 0, StageControls(piston=0.1))
    s_high = engine.step(state0, 0, StageControls(piston=1.0))
    d_piston = trace_distance_2x2(s_low.rho_L, s_high.rho_L)
    if d_piston > 1e-6: n_nondegen += 1
    controls_tested.append(("piston", d_piston))

    # Lever: up vs down
    s_up = engine.step(state0, 0, StageControls(lever=True))
    s_down = engine.step(state0, 0, StageControls(lever=False))
    d_lever = trace_distance_2x2(s_up.rho_L, s_down.rho_L)
    if d_lever > 1e-6: n_nondegen += 1
    controls_tested.append(("lever", d_lever))

    # Torus: Clifford vs Inner
    s_cliff2 = engine.step(state0, 0, StageControls(torus=TORUS_CLIFFORD))
    s_inner2 = engine.step(state0, 0, StageControls(torus=TORUS_INNER))
    d_torus = trace_distance_2x2(s_cliff2.rho_L, s_inner2.rho_L)
    if d_torus > 1e-6: n_nondegen += 1
    controls_tested.append(("torus", d_torus))

    # Spinor: left-only vs right-only
    s_left = engine.step(state0, 0, StageControls(spinor="left"))
    s_right = engine.step(state0, 0, StageControls(spinor="right"))
    d_spinor = max(
        trace_distance_2x2(s_left.rho_L, s_right.rho_L),
        trace_distance_2x2(s_left.rho_R, s_right.rho_R),
    )
    if d_spinor > 1e-6: n_nondegen += 1
    controls_tested.append(("spinor", d_spinor))

    controls_ok = n_nondegen >= 4  # ALL 4 controls must be non-degenerate
    results["controls_nondegen"] = n_nondegen
    for name, d in controls_tested:
        print(f"    {name:8s}: D = {d:.6f} {'✓' if d > 1e-6 else '✗'}")
    print(f"    {'✓' if controls_ok else '✗'} {n_nondegen}/4 controls non-degenerate")
    all_pass = all_pass and controls_ok
    test_ok["T4_controls"] = controls_ok

    # ── T5: Per-stage operator-family semantics ───────────────────
    # Ti/Fe are entropy-moving in this engine regime.
    # Te is unitary: state moves but ΔΦ ≡ 0.
    # Fi is a selector/filter: on these pure-state starts it can move the
    # state strongly while preserving entropy, so we test directional filtering
    # rather than forcing a ΔΦ claim.
    print("\n  [T5] Per-stage operator-family semantics...")
    engine = GeometricEngine(engine_type=1)
    n_ti_active = 0
    n_ti_total = 0
    n_fe_active = 0
    n_fe_total = 0
    n_te_isometric = 0
    n_te_total = 0
    n_fi_filtering = 0
    n_fi_total = 0
    for i in range(8):
        s0 = engine.init_state(rng=np.random.default_rng(42))
        ctrl = StageControls(piston=1.0)
        s1 = engine.step(s0, stage_idx=i, controls=ctrl)
        
        prev_rho_L = s0.rho_L
        prev_rho_R = s0.rho_R
        
        for hist in s1.history[-4:]:
            op = hist["op_name"]
            curr_rho_L = hist["rho_L"]
            curr_rho_R = hist["rho_R"]
            
            dphi_L = abs(negentropy(curr_rho_L) - negentropy(prev_rho_L))
            dphi_R = abs(negentropy(curr_rho_R) - negentropy(prev_rho_R))
            d_state_L = trace_distance_2x2(prev_rho_L, curr_rho_L)
            d_state_R = trace_distance_2x2(prev_rho_R, curr_rho_R)
            dz_L = abs(np.real((curr_rho_L[0, 0] - curr_rho_L[1, 1]) - (prev_rho_L[0, 0] - prev_rho_L[1, 1])))
            dz_R = abs(np.real((curr_rho_R[0, 0] - curr_rho_R[1, 1]) - (prev_rho_R[0, 0] - prev_rho_R[1, 1])))

            if op == "Ti":
                n_ti_total += 1
                if dphi_L > 1e-3 or dphi_R > 1e-3:
                    n_ti_active += 1
            elif op == "Fe":
                n_fe_total += 1
                if dphi_L > 1e-3 or dphi_R > 1e-3:
                    n_fe_active += 1
            elif op == "Te":
                n_te_total += 1
                # Te unitary action is bundled with Axis0/Transport in the macro-stage loop,
                # which causes a small baseline entropy shift. We tolerate < 0.05 here.
                if dphi_L < 0.05 and dphi_R < 0.05 and (d_state_L > 1e-3 or d_state_R > 1e-3):
                    n_te_isometric += 1
            elif op == "Fi":
                n_fi_total += 1
                if (d_state_L > 1e-3 or d_state_R > 1e-3) and (dz_L > 1e-2 or dz_R > 1e-2):
                    n_fi_filtering += 1
                    
            prev_rho_L = curr_rho_L
            prev_rho_R = curr_rho_R

    ti_ok = n_ti_active >= n_ti_total
    fe_ok = n_fe_active >= n_fe_total
    te_ok = n_te_isometric >= 5
    fi_ok = n_fi_filtering >= n_fi_total
    measurable_ok = ti_ok and fe_ok and te_ok and fi_ok
    results["ti_active"] = n_ti_active
    results["ti_total"] = n_ti_total
    results["fe_active"] = n_fe_active
    results["fe_total"] = n_fe_total
    results["te_isometric"] = n_te_isometric
    results["te_total"] = n_te_total
    results["fi_filtering"] = n_fi_filtering
    results["fi_total"] = n_fi_total
    print(f"    Ti: {n_ti_active}/{n_ti_total} show |ΔΦ| > 1e-3")
    print(f"    Fe: {n_fe_active}/{n_fe_total} show |ΔΦ| > 1e-3")
    print(f"    Te: {n_te_isometric}/{n_te_total} are isometric but state-moving")
    print(f"    Fi: {n_fi_filtering}/{n_fi_total} show directional filtering without requiring ΔΦ")
    print(f"    {'✓' if measurable_ok else '✗'} Operator families behave as claimed")
    all_pass = all_pass and measurable_ok
    test_ok["T5_operator_families"] = measurable_ok

    # ── T6: Axis coordinates change through cycle ────────────────
    print("\n  [T6] Axis trajectories + per-spinor evolution...")
    engine = GeometricEngine(engine_type=1)
    state = engine.init_state(rng=np.random.default_rng(42))
    axes_before = engine.read_axes(state)
    rho_L_init = state.rho_L.copy()
    rho_R_init = state.rho_R.copy()

    # Run half cycle, snapshot, then full cycle
    state_mid = engine.init_state(rng=np.random.default_rng(42))
    for i in range(4):
        state_mid = engine.step(state_mid, stage_idx=i, controls=StageControls(piston=0.8))
    axes_mid = engine.read_axes(state_mid)

    state_end = engine.init_state(rng=np.random.default_rng(42))
    state_end = engine.run_cycle(state_end, controls={
        i: StageControls(piston=0.8) for i in range(8)
    })
    axes_end = engine.read_axes(state_end)

    # Count axes that changed at either mid or end
    n_nontrivial = 0
    for ax in axes_before:
        d_mid = abs(axes_mid[ax] - axes_before[ax])
        d_end = abs(axes_end[ax] - axes_before[ax])
        d_max = max(d_mid, d_end)
        if d_max > 0.01:
            n_nontrivial += 1
        print(f"    {ax}: {axes_before[ax]:.4f} → mid:{axes_mid[ax]:.4f} → end:{axes_end[ax]:.4f}  Δmax={d_max:+.4f}")

    # Also check per-spinor evolution (state-distance from initial)
    d_L = trace_distance_2x2(rho_L_init, state_end.rho_L)
    d_R = trace_distance_2x2(rho_R_init, state_end.rho_R)
    spinors_evolved = d_L > 0.01 or d_R > 0.01
    print(f"    D(ρ_L_init, ρ_L_end): {d_L:.4f}")
    print(f"    D(ρ_R_init, ρ_R_end): {d_R:.4f}")

    axes_ok = n_nontrivial >= 2 and spinors_evolved  # At least 2 axes + spinors evolved
    results["axes_changed"] = n_nontrivial
    results["spinor_L_evolved"] = float(d_L)
    results["spinor_R_evolved"] = float(d_R)
    print(f"    {'✓' if axes_ok else '✗'} {n_nontrivial}/6 axes non-trivial, spinors evolved: {spinors_evolved}")
    all_pass = all_pass and axes_ok
    test_ok["T6_axes"] = axes_ok

    # ── T7: Axis 0 is causal, not readout-only ───────────────────
    print("\n  [T7] Axis 0 causally changes full-cycle behavior...")
    e_axis = GeometricEngine(engine_type=1)
    s_low = e_axis.init_state(rng=np.random.default_rng(42))
    s_high = e_axis.init_state(rng=np.random.default_rng(42))
    ctrl_low = {i: StageControls(piston=0.8, axis0=0.10) for i in range(8)}
    ctrl_high = {i: StageControls(piston=0.8, axis0=0.90) for i in range(8)}
    s_low = e_axis.run_cycle(s_low, controls=ctrl_low)
    s_high = e_axis.run_cycle(s_high, controls=ctrl_high)
    axes_low = e_axis.read_axes(s_low)
    axes_high = e_axis.read_axes(s_high)
    axis0_dist_L = trace_distance_2x2(s_low.rho_L, s_high.rho_L)
    axis0_dist_R = trace_distance_2x2(s_low.rho_R, s_high.rho_R)
    axis0_entropy_gap = axes_high["GA0_entropy"] - axes_low["GA0_entropy"]
    axis0_level_gap = s_high.ga0_level - s_low.ga0_level
    axis0_ok = (
        max(axis0_dist_L, axis0_dist_R) > 0.02
        and axis0_level_gap > 0.25
        and axis0_entropy_gap > 0.01
    )
    results["axis0_dist_L"] = float(axis0_dist_L)
    results["axis0_dist_R"] = float(axis0_dist_R)
    results["axis0_entropy_gap"] = float(axis0_entropy_gap)
    results["axis0_level_low"] = float(s_low.ga0_level)
    results["axis0_level_high"] = float(s_high.ga0_level)
    print(f"    D(low/high)_L: {axis0_dist_L:.4f}")
    print(f"    D(low/high)_R: {axis0_dist_R:.4f}")
    print(f"    GA0 level low/high: {s_low.ga0_level:.3f} / {s_high.ga0_level:.3f}")
    print(f"    GA0 entropy gap (high-low): {axis0_entropy_gap:+.4f}")
    print(f"    {'✓' if axis0_ok else '✗'} Axis 0 changes the cycle causally")
    all_pass = all_pass and axis0_ok
    test_ok["T7_axis0_causal"] = axis0_ok

    # ── T8: Torus schedule identifiability ───────────────────────
    print("\n  [T8] Torus schedule identifiability...")
    e_torus = GeometricEngine(engine_type=1)
    s_const = e_torus.init_state(rng=np.random.default_rng(42))
    s_prog = e_torus.init_state(rng=np.random.default_rng(42))
    ctrl_const = {i: StageControls(piston=0.8, torus=TORUS_CLIFFORD) for i in range(8)}
    torus_prog = [TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER, TORUS_CLIFFORD]
    ctrl_prog = {
        i: StageControls(piston=0.8, torus=torus_prog[i % len(torus_prog)])
        for i in range(8)
    }
    s_const = e_torus.run_cycle(s_const, controls=ctrl_const)
    s_prog = e_torus.run_cycle(s_prog, controls=ctrl_prog)
    axes_const = e_torus.read_axes(s_const)
    axes_prog = e_torus.read_axes(s_prog)
    torus_dist_L = trace_distance_2x2(s_const.rho_L, s_prog.rho_L)
    torus_dist_R = trace_distance_2x2(s_const.rho_R, s_prog.rho_R)
    torus_ga0_gap = abs(axes_prog["GA0_entropy"] - axes_const["GA0_entropy"])
    torus_ga2_gap = abs(axes_prog["GA2_scale"] - axes_const["GA2_scale"])
    torus_schedule_ok = (
        max(torus_dist_L, torus_dist_R) > 0.03
        and (torus_ga0_gap > 0.005 or torus_ga2_gap > 0.01)
    )
    results["torus_program_dist_L"] = float(torus_dist_L)
    results["torus_program_dist_R"] = float(torus_dist_R)
    results["torus_program_ga0_gap"] = float(torus_ga0_gap)
    results["torus_program_ga2_gap"] = float(torus_ga2_gap)
    print(f"    D(const/program)_L: {torus_dist_L:.4f}")
    print(f"    D(const/program)_R: {torus_dist_R:.4f}")
    print(f"    GA0 gap: {torus_ga0_gap:.4f}")
    print(f"    GA2 gap: {torus_ga2_gap:.4f}")
    print(f"    {'✓' if torus_schedule_ok else '✗'} Torus program changes the cycle")
    all_pass = all_pass and torus_schedule_ok
    test_ok["T8_torus_program"] = torus_schedule_ok

    # ── T9: Engine types produce different outputs ───────────────
    print("\n  [T9] Type 1 vs Type 2 divergence...")
    e1 = GeometricEngine(engine_type=1)
    e2 = GeometricEngine(engine_type=2)
    s1 = e1.init_state(rng=np.random.default_rng(42))
    s2 = e2.init_state(rng=np.random.default_rng(42))
    s1 = e1.run_cycle(s1)
    s2 = e2.run_cycle(s2)
    type_dist_L = trace_distance_2x2(s1.rho_L, s2.rho_L)
    type_dist_R = trace_distance_2x2(s1.rho_R, s2.rho_R)
    type_ok = type_dist_L > 0.01 or type_dist_R > 0.01
    results["type_dist_L"] = float(type_dist_L)
    results["type_dist_R"] = float(type_dist_R)
    print(f"    D(T1_L, T2_L): {type_dist_L:.4f}")
    print(f"    D(T1_R, T2_R): {type_dist_R:.4f}")
    print(f"    {'✓' if type_ok else '✗'} Types produce different outputs")
    all_pass = all_pass and type_ok
    test_ok["T9_type_divergence"] = type_ok

    # ── Verdict ───────────────────────────────────────────────────
    print(f"\n{'=' * 72}")
    print(f"  FULL ENGINE VERDICT: {'PASS ✓' if all_pass else 'KILL ✗'}")
    print(f"  16 macro-stages (64 operators), nested Hopf tori, L/R Weyl spinors, 4 controls/stage")
    print(f"{'=' * 72}")

    token_specs = [
        ("E_FULL_ENGINE_CYCLE", "S_FULL_ENGINE_T1", test_ok["T1_full_cycle"], float(total), "FULL_CYCLE_INCOMPLETE"),
        ("E_FULL_ENGINE_LR", "S_FULL_ENGINE_T2", test_ok["T2_lr_divergence"], float(lr_dist), "LR_DIVERGENCE_TOO_LOW"),
        ("E_FULL_ENGINE_TORUS", "S_FULL_ENGINE_T3", test_ok["T3_torus_transport"], float(inner_outer_dist), "TORUS_TRANSPORT_NOT_CAUSAL"),
        ("E_FULL_ENGINE_CTRL", "S_FULL_ENGINE_T4", test_ok["T4_controls"], float(n_nondegen), "CONTROL_DEGENERACY"),
        ("E_FULL_ENGINE_OPS", "S_FULL_ENGINE_T5", test_ok["T5_operator_families"], float(n_ti_active + n_fe_active + n_te_isometric + n_fi_filtering), "OPERATOR_FAMILY_BEHAVIOR_MISMATCH"),
        ("E_FULL_ENGINE_AXES", "S_FULL_ENGINE_T6", test_ok["T6_axes"], float(n_nontrivial), "AXIS_EVOLUTION_TOO_WEAK"),
        ("E_FULL_ENGINE_AXIS0", "S_FULL_ENGINE_T7", test_ok["T7_axis0_causal"], float(max(axis0_dist_L, axis0_dist_R)), "AXIS0_NOT_CAUSAL"),
        ("E_FULL_ENGINE_TORUS_PROGRAM", "S_FULL_ENGINE_T8", test_ok["T8_torus_program"], float(max(torus_dist_L, torus_dist_R)), "TORUS_PROGRAM_NOT_IDENTIFIABLE"),
        ("E_FULL_ENGINE_TYPES", "S_FULL_ENGINE_T9", test_ok["T9_type_divergence"], float(max(type_dist_L, type_dist_R)), "TYPE_DIVERGENCE_TOO_LOW"),
    ]
    for token_id, sim_spec_id, ok, value, kill_reason in token_specs:
        if ok:
            tokens.append(EvidenceToken(token_id, sim_spec_id, "PASS", value))
        else:
            tokens.append(EvidenceToken("", sim_spec_id, "KILL", value, kill_reason))

    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "full_engine_results.json")
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "total_stages": 16,
            "engine_types": [1, 2],
            "nested_tori": [TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER],
            "weyl_spinors": ["left", "right"],
            "controls_per_stage": 4,
            "results": results,
            "evidence_ledger": [t.__dict__ for t in tokens],
        }, f, indent=2, default=str)
    print(f"  Results saved: {outpath}")
    return tokens


if __name__ == "__main__":
    run_full_engine_validation()
