#!/usr/bin/env python3
"""
sim_cross_layer_negative_propagation.py
=======================================

Cross-Layer Negative Propagation Battery
-----------------------------------------
If you break something at layer N, do layers N+1, N+2, ... also break?
Tests whether the constraint ladder is truly hierarchical — each layer
depends on those below it.

10 breaks × full upward propagation check = dependency matrix.
"""

import json
import os
import sys
import copy
import numpy as np
from datetime import datetime, UTC
classification = "classical_baseline"  # auto-backfill
divergence_log = "Classical baseline: cross-layer negative propagation is evaluated here by engine and bridge numerics, not a canonical nonclassical witness."
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "engine-state metrics, propagation aggregates, and JSON-safe numerics"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
}

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import (
    GeometricEngine, TERRAINS, STAGE_OPERATOR_LUT, LOOP_STAGE_ORDER,
    EngineState, StageControls, _TERRAIN_TO_LOOP,
)
from geometric_operators import (
    apply_Ti, apply_Fe, apply_Te, apply_Fi,
    OPERATOR_MAP_4X4,
    _ensure_valid_density, I2, SIGMA_X, SIGMA_Y, SIGMA_Z,
    partial_trace_A, partial_trace_B,
    negentropy, apply_Ti_4x4, apply_Fe_4x4, apply_Te_4x4, apply_Fi_4x4,
)
from hopf_manifold import (
    von_neumann_entropy_2x2, berry_phase, torus_coordinates, torus_radii,
    TORUS_CLIFFORD, density_to_bloch, left_weyl_spinor, right_weyl_spinor,
    lifted_base_loop,
)
from sim_3qubit_bridge_prototype import (
    partial_trace_keep, von_neumann_entropy, ensure_valid_density,
    build_3q_Ti, build_3q_Fe, build_3q_Te, build_3q_Fi,
    compute_info_measures,
)


# ═══════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════

def sanitize(obj):
    """Recursively convert numpy types to native Python for JSON."""
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, complex):
        return {"re": float(obj.real), "im": float(obj.imag)}
    if isinstance(obj, (np.complexfloating,)):
        return {"re": float(obj.real), "im": float(obj.imag)}
    return obj


def concurrence_4x4(rho):
    """Wootters concurrence for a 4x4 density matrix."""
    sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
    sy_sy = np.kron(sy, sy)
    R = rho @ sy_sy @ rho.conj() @ sy_sy
    evals = sorted(np.sqrt(np.maximum(np.real(np.linalg.eigvals(R)), 0)), reverse=True)
    return max(0, evals[0] - evals[1] - evals[2] - evals[3])


def entropy_4x4(rho):
    """Von Neumann entropy for a 4x4 density matrix, in bits."""
    rho = (rho + rho.conj().T) / 2
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > 1e-15]
    if len(evals) == 0:
        return 0.0
    return float(-np.sum(evals * np.log2(evals)))


def bloch_LR_dot(rho_AB):
    """Dot product of L and R Bloch vectors from a 4x4 density matrix."""
    rho_L = _ensure_valid_density(partial_trace_B(rho_AB))
    rho_R = _ensure_valid_density(partial_trace_A(rho_AB))
    bL = density_to_bloch(rho_L)
    bR = density_to_bloch(rho_R)
    nL = np.linalg.norm(bL)
    nR = np.linalg.norm(bR)
    if nL < 1e-12 or nR < 1e-12:
        return 0.0
    return float(np.dot(bL, bR) / (nL * nR))


def berry_phase_from_state(state):
    """Berry phase from lifted base loop at current eta."""
    loop = lifted_base_loop(n_points=64)
    return berry_phase(loop)


# ═══════════════════════════════════════════════════════════════════
# BASELINE: Run canonical engine for reference metrics
# ═══════════════════════════════════════════════════════════════════

def run_baseline(n_cycles=10):
    """Run canonical 2-qubit engine, return per-cycle metrics."""
    engine = GeometricEngine(engine_type=1)
    state = engine.init_state()
    metrics = []
    for cyc in range(n_cycles):
        state = engine.run_cycle(state)
        rho = state.rho_AB
        m = {
            "cycle": cyc + 1,
            "concurrence": float(concurrence_4x4(rho)),
            "entropy": float(entropy_4x4(rho)),
            "LR_dot": float(bloch_LR_dot(rho)),
            "berry_phase": float(berry_phase_from_state(state)),
            "negentropy": float(negentropy(rho)),
            "entropy_L": float(von_neumann_entropy_2x2(state.rho_L)),
            "entropy_R": float(von_neumann_entropy_2x2(state.rho_R)),
        }
        metrics.append(m)
    return metrics, state


def aggregate_metrics(metrics_list):
    """Average metrics across cycles, return dict."""
    if not metrics_list:
        return {}
    keys = [k for k in metrics_list[0] if k != "cycle"]
    result = {}
    for k in keys:
        vals = [m[k] for m in metrics_list]
        result[k] = float(np.mean(vals))
        result[k + "_max"] = float(np.max(vals))
        result[k + "_min"] = float(np.min(vals))
    return result


# ═══════════════════════════════════════════════════════════════════
# BREAK IMPLEMENTATIONS
# ═══════════════════════════════════════════════════════════════════

def break_L2_real_only(n_cycles=10):
    """BREAK 1: Kill the carrier (Layer 2) — replace C^2 with R^2.
    Force all density matrices to real after each operator application."""
    engine = GeometricEngine(engine_type=1)
    state = engine.init_state()

    # Monkey-patch: wrap all 4x4 operators to force real output
    original_ops = dict(OPERATOR_MAP_4X4)

    def make_real_wrapper(fn):
        def wrapper(rho, **kwargs):
            rho_out = fn(rho, **kwargs)
            rho_out = np.real(rho_out).astype(complex)  # kill imaginary
            return _ensure_valid_density(rho_out)
        return wrapper

    for k in OPERATOR_MAP_4X4:
        OPERATOR_MAP_4X4[k] = make_real_wrapper(original_ops[k])

    metrics = []
    try:
        for cyc in range(n_cycles):
            state = engine.run_cycle(state)
            # Also force the rho_AB real after cycle
            state.rho_AB = np.real(state.rho_AB).astype(complex)
            state.rho_AB = _ensure_valid_density(state.rho_AB)
            rho = state.rho_AB
            m = {
                "cycle": cyc + 1,
                "concurrence": float(concurrence_4x4(rho)),
                "entropy": float(entropy_4x4(rho)),
                "LR_dot": float(bloch_LR_dot(rho)),
                "berry_phase": float(berry_phase_from_state(state)),
                "negentropy": float(negentropy(rho)),
                "entropy_L": float(von_neumann_entropy_2x2(state.rho_L)),
                "entropy_R": float(von_neumann_entropy_2x2(state.rho_R)),
            }
            metrics.append(m)
    finally:
        # Restore originals
        for k in original_ops:
            OPERATOR_MAP_4X4[k] = original_ops[k]

    return metrics


def break_L4_no_chirality(n_cycles=10):
    """BREAK 2: Kill chirality (Layer 4) — force psi_L = psi_R each cycle."""
    engine = GeometricEngine(engine_type=1)
    state = engine.init_state()
    metrics = []
    for cyc in range(n_cycles):
        state = engine.run_cycle(state)
        # Force L = R: rebuild rho_AB from psi_L only (no chirality distinction)
        psi_L = left_weyl_spinor(state.q())
        psi_AB = np.outer(psi_L, psi_L).flatten()  # L tensor L, not L tensor R
        state.rho_AB = _ensure_valid_density(np.outer(psi_AB, psi_AB.conj()))
        rho = state.rho_AB
        m = {
            "cycle": cyc + 1,
            "concurrence": float(concurrence_4x4(rho)),
            "entropy": float(entropy_4x4(rho)),
            "LR_dot": float(bloch_LR_dot(rho)),
            "berry_phase": float(berry_phase_from_state(state)),
            "negentropy": float(negentropy(rho)),
            "entropy_L": float(von_neumann_entropy_2x2(state.rho_L)),
            "entropy_R": float(von_neumann_entropy_2x2(state.rho_R)),
        }
        metrics.append(m)
    return metrics


def break_L5_remove_Se(n_cycles=10):
    """BREAK 3: Kill one topology (Layer 5) — replace Se stages with Ne operator.
    Map Se terrains to Ne's operator in the LUT."""
    engine = GeometricEngine(engine_type=1)
    state = engine.init_state()

    # Patch: replace Se→Ne in the LUT for this engine type
    original_lut = dict(STAGE_OPERATOR_LUT)
    for key in list(STAGE_OPERATOR_LUT.keys()):
        et, loop, topo = key
        if topo == "Se":
            # Replace with Ne's operator
            ne_key = (et, loop, "Ne")
            if ne_key in original_lut:
                STAGE_OPERATOR_LUT[key] = original_lut[ne_key]

    metrics = []
    try:
        for cyc in range(n_cycles):
            state = engine.run_cycle(state)
            rho = state.rho_AB
            m = {
                "cycle": cyc + 1,
                "concurrence": float(concurrence_4x4(rho)),
                "entropy": float(entropy_4x4(rho)),
                "LR_dot": float(bloch_LR_dot(rho)),
                "berry_phase": float(berry_phase_from_state(state)),
                "negentropy": float(negentropy(rho)),
                "entropy_L": float(von_neumann_entropy_2x2(state.rho_L)),
                "entropy_R": float(von_neumann_entropy_2x2(state.rho_R)),
            }
            metrics.append(m)
    finally:
        for k, v in original_lut.items():
            STAGE_OPERATOR_LUT[k] = v

    return metrics


def break_L7_random_order(n_cycles=10, n_trials=20):
    """BREAK 4: Kill composition order (Layer 7) — randomize stage order each cycle."""
    rng = np.random.default_rng(42)
    all_trial_metrics = []

    for trial in range(n_trials):
        engine = GeometricEngine(engine_type=1)
        state = engine.init_state()
        original_order = list(LOOP_STAGE_ORDER[1])

        trial_metrics = []
        for cyc in range(n_cycles):
            # Randomize stage order
            shuffled = list(original_order)
            rng.shuffle(shuffled)
            LOOP_STAGE_ORDER[1] = shuffled
            state = engine.run_cycle(state)
            rho = state.rho_AB
            m = {
                "cycle": cyc + 1,
                "concurrence": float(concurrence_4x4(rho)),
                "entropy": float(entropy_4x4(rho)),
                "LR_dot": float(bloch_LR_dot(rho)),
                "berry_phase": float(berry_phase_from_state(state)),
                "negentropy": float(negentropy(rho)),
                "entropy_L": float(von_neumann_entropy_2x2(state.rho_L)),
                "entropy_R": float(von_neumann_entropy_2x2(state.rho_R)),
            }
            trial_metrics.append(m)

        LOOP_STAGE_ORDER[1] = original_order
        all_trial_metrics.append(trial_metrics)

    # Average across trials
    avg_metrics = []
    for cyc_idx in range(n_cycles):
        agg = {}
        keys = [k for k in all_trial_metrics[0][0] if k != "cycle"]
        for k in keys:
            vals = [all_trial_metrics[t][cyc_idx][k] for t in range(n_trials)]
            agg[k] = float(np.mean(vals))
        agg["cycle"] = cyc_idx + 1
        avg_metrics.append(agg)

    return avg_metrics


def break_L8_same_polarity(n_cycles=10):
    """BREAK 5: Kill polarity (Layer 8) — force all operators to polarity_up=True."""
    # Patch the LUT so all polarities are True
    original_lut = dict(STAGE_OPERATOR_LUT)
    for key in STAGE_OPERATOR_LUT:
        op_name, _ = STAGE_OPERATOR_LUT[key]
        STAGE_OPERATOR_LUT[key] = (op_name, True)  # Force all UP

    engine = GeometricEngine(engine_type=1)
    state = engine.init_state()
    metrics = []
    try:
        for cyc in range(n_cycles):
            state = engine.run_cycle(state)
            rho = state.rho_AB
            m = {
                "cycle": cyc + 1,
                "concurrence": float(concurrence_4x4(rho)),
                "entropy": float(entropy_4x4(rho)),
                "LR_dot": float(bloch_LR_dot(rho)),
                "berry_phase": float(berry_phase_from_state(state)),
                "negentropy": float(negentropy(rho)),
                "entropy_L": float(von_neumann_entropy_2x2(state.rho_L)),
                "entropy_R": float(von_neumann_entropy_2x2(state.rho_R)),
            }
            metrics.append(m)
    finally:
        for k, v in original_lut.items():
            STAGE_OPERATOR_LUT[k] = v

    return metrics


def break_L9_strength(n_cycles=10, strength_val=0.0):
    """BREAK 6: Kill operator strength (Layer 9) — set all piston to given value."""
    engine = GeometricEngine(engine_type=1)
    state = engine.init_state()
    controls = {i: StageControls(piston=strength_val) for i in range(8)}
    metrics = []
    for cyc in range(n_cycles):
        state = engine.run_cycle(state, controls=controls)
        rho = state.rho_AB
        m = {
            "cycle": cyc + 1,
            "concurrence": float(concurrence_4x4(rho)),
            "entropy": float(entropy_4x4(rho)),
            "LR_dot": float(bloch_LR_dot(rho)),
            "berry_phase": float(berry_phase_from_state(state)),
            "negentropy": float(negentropy(rho)),
            "entropy_L": float(von_neumann_entropy_2x2(state.rho_L)),
            "entropy_R": float(von_neumann_entropy_2x2(state.rho_R)),
        }
        metrics.append(m)
    return metrics


def break_L10_single_type(n_cycles=20, engine_type=1):
    """BREAK 7: Kill dual-stack (Layer 10) — single engine type only, 20 cycles."""
    engine = GeometricEngine(engine_type=engine_type)
    state = engine.init_state()
    metrics = []
    for cyc in range(n_cycles):
        state = engine.run_cycle(state)
        rho = state.rho_AB
        m = {
            "cycle": cyc + 1,
            "concurrence": float(concurrence_4x4(rho)),
            "entropy": float(entropy_4x4(rho)),
            "LR_dot": float(bloch_LR_dot(rho)),
            "berry_phase": float(berry_phase_from_state(state)),
            "negentropy": float(negentropy(rho)),
            "entropy_L": float(von_neumann_entropy_2x2(state.rho_L)),
            "entropy_R": float(von_neumann_entropy_2x2(state.rho_R)),
        }
        metrics.append(m)
    return metrics


def run_interleaved_baseline(n_cycles=20):
    """Baseline for dual-stack comparison: interleave Type 1 and Type 2."""
    engine1 = GeometricEngine(engine_type=1)
    engine2 = GeometricEngine(engine_type=2)
    state1 = engine1.init_state()
    state2 = engine2.init_state()
    metrics = []
    for cyc in range(n_cycles):
        state1 = engine1.run_cycle(state1)
        state2 = engine2.run_cycle(state2)
        # Combine: average entropy variance and state diversity
        rho1 = state1.rho_AB
        rho2 = state2.rho_AB
        m = {
            "cycle": cyc + 1,
            "concurrence": float((concurrence_4x4(rho1) + concurrence_4x4(rho2)) / 2),
            "entropy": float((entropy_4x4(rho1) + entropy_4x4(rho2)) / 2),
            "LR_dot": float((bloch_LR_dot(rho1) + bloch_LR_dot(rho2)) / 2),
            "berry_phase": float(berry_phase_from_state(state1)),
            "negentropy": float((negentropy(rho1) + negentropy(rho2)) / 2),
            "entropy_L": float((von_neumann_entropy_2x2(state1.rho_L)
                                + von_neumann_entropy_2x2(state2.rho_L)) / 2),
            "entropy_R": float((von_neumann_entropy_2x2(state1.rho_R)
                                + von_neumann_entropy_2x2(state2.rho_R)) / 2),
        }
        metrics.append(m)
    return metrics


def break_L11_lock_eta(n_cycles=10, eta_lock=0.001):
    """BREAK 8: Kill torus transport (Layer 11) — lock to degenerate eta."""
    engine = GeometricEngine(engine_type=1)
    state = engine.init_state(eta=eta_lock)
    # Force torus control to locked eta
    controls = {i: StageControls(torus=eta_lock) for i in range(8)}
    metrics = []
    for cyc in range(n_cycles):
        state = engine.run_cycle(state, controls=controls)
        # Also force eta back after cycle
        state.eta = eta_lock
        rho = state.rho_AB
        m = {
            "cycle": cyc + 1,
            "concurrence": float(concurrence_4x4(rho)),
            "entropy": float(entropy_4x4(rho)),
            "LR_dot": float(bloch_LR_dot(rho)),
            "berry_phase": float(berry_phase_from_state(state)),
            "negentropy": float(negentropy(rho)),
            "entropy_L": float(von_neumann_entropy_2x2(state.rho_L)),
            "entropy_R": float(von_neumann_entropy_2x2(state.rho_R)),
        }
        metrics.append(m)
    return metrics


def break_L12_no_Fi_4x4(n_cycles=10):
    """BREAK 9: Kill entanglement dynamics (Layer 12) — remove Fi from 4x4.
    Replace Fi_4x4 with identity."""
    original_fi = OPERATOR_MAP_4X4["Fi"]
    OPERATOR_MAP_4X4["Fi"] = lambda rho, **kw: _ensure_valid_density(rho.copy())

    engine = GeometricEngine(engine_type=1)
    state = engine.init_state()
    metrics = []
    try:
        for cyc in range(n_cycles):
            state = engine.run_cycle(state)
            rho = state.rho_AB
            m = {
                "cycle": cyc + 1,
                "concurrence": float(concurrence_4x4(rho)),
                "entropy": float(entropy_4x4(rho)),
                "LR_dot": float(bloch_LR_dot(rho)),
                "berry_phase": float(berry_phase_from_state(state)),
                "negentropy": float(negentropy(rho)),
                "entropy_L": float(von_neumann_entropy_2x2(state.rho_L)),
                "entropy_R": float(von_neumann_entropy_2x2(state.rho_R)),
            }
            metrics.append(m)
    finally:
        OPERATOR_MAP_4X4["Fi"] = original_fi

    return metrics


def break_L13_no_Fe_3q(n_cycles=10, deph=0.05, theta=np.pi):
    """BREAK 10: Kill bridge (Layer 13-14) — remove Fe from 3q engine.
    Run Ti+Te+Fi only (no Fe)."""
    rho_init = np.zeros((8, 8), dtype=complex)
    rho_init[0, 0] = 1.0

    Ti = build_3q_Ti(strength=deph)
    Te = build_3q_Te(strength=deph, q=0.7)
    Fi = build_3q_Fi(strength=1.0, theta=theta)

    rho = rho_init.copy()
    metrics = []
    for cyc in range(n_cycles):
        rho = Ti(rho)
        rho = Te(rho)
        rho = Fi(rho)
        info = compute_info_measures(rho)
        best_ic = max(info[cn]["I_c"] for cn in info)
        m = {
            "cycle": cyc + 1,
            "best_I_c": float(best_ic),
            "info": info,
        }
        metrics.append(m)

    return metrics


def run_3q_baseline(n_cycles=10, deph=0.05, theta=np.pi):
    """3-qubit baseline with all 4 operators for comparison."""
    rho_init = np.zeros((8, 8), dtype=complex)
    rho_init[0, 0] = 1.0

    Ti = build_3q_Ti(strength=deph)
    Fe = build_3q_Fe(strength=1.0, phi=0.4)
    Te = build_3q_Te(strength=deph, q=0.7)
    Fi = build_3q_Fi(strength=1.0, theta=theta)

    rho = rho_init.copy()
    metrics = []
    for cyc in range(n_cycles):
        rho = Ti(rho)
        rho = Fe(rho)
        rho = Te(rho)
        rho = Fi(rho)
        info = compute_info_measures(rho)
        best_ic = max(info[cn]["I_c"] for cn in info)
        m = {
            "cycle": cyc + 1,
            "best_I_c": float(best_ic),
            "info": info,
        }
        metrics.append(m)

    return metrics


# ═══════════════════════════════════════════════════════════════════
# LAYER HEALTH ASSESSMENT
# ═══════════════════════════════════════════════════════════════════

# Metric-to-layer mapping: which metrics diagnose which layers
LAYER_METRICS = {
    "L2_carrier":           "entropy",           # Complex carrier → entropy should be nonzero
    "L4_chirality":         "LR_dot",            # L!=R → dot < 1.0
    "L5_topology":          "entropy",           # Topology variety → entropy diversity
    "L6_su2_algebra":       "concurrence",       # su(2) commutators → entanglement
    "L7_composition_order": "concurrence",       # Order matters → concurrence depends on sequence
    "L8_polarity":          "entropy",           # Polarity mixing → richer entropy trajectory
    "L9_strength":          "concurrence",       # Strength tuning → concurrence amplitude
    "L10_dual_stack":       "entropy",           # Two types → entropy diversity
    "L11_torus_transport":  "berry_phase",       # Torus movement → berry phase nonzero
    "L12_entanglement":     "concurrence",       # Fi entangles → concurrence > 0
}


def classify_layer_health(baseline_val, broken_val, threshold_kill=0.1, threshold_degrade=0.5):
    """Classify layer health relative to baseline.
    Returns: 'killed' | 'degraded' | 'survived'
    """
    if abs(baseline_val) < 1e-12:
        # Baseline is zero — check if broken is also zero
        if abs(broken_val) < 1e-12:
            return "survived"  # Both zero, no change
        return "survived"  # Broken has signal where baseline didn't — not killed

    ratio = abs(broken_val) / abs(baseline_val)
    if ratio < threshold_kill:
        return "killed"
    elif ratio < threshold_degrade:
        return "degraded"
    else:
        return "survived"


def assess_all_layers(baseline_agg, broken_agg):
    """Given aggregated baseline and broken metrics, classify each layer's health."""
    results = {}
    for layer, metric_key in LAYER_METRICS.items():
        b_val = baseline_agg.get(metric_key, 0.0)
        k_val = broken_agg.get(metric_key, 0.0)
        status = classify_layer_health(b_val, k_val)
        results[layer] = {
            "status": status,
            "baseline": float(b_val),
            "broken": float(k_val),
            "ratio": float(abs(k_val) / abs(b_val)) if abs(b_val) > 1e-12 else None,
        }
    return results


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    print("=" * 72)
    print("  CROSS-LAYER NEGATIVE PROPAGATION BATTERY")
    print("=" * 72)

    N_CYCLES = 10

    # ─── BASELINE ─────────────────────────────────────────────────
    print("\n[BASELINE] Running canonical 2q engine...")
    baseline_metrics, baseline_state = run_baseline(N_CYCLES)
    baseline_agg = aggregate_metrics(baseline_metrics)
    print(f"  Baseline concurrence (mean): {baseline_agg['concurrence']:.6f}")
    print(f"  Baseline entropy (mean):     {baseline_agg['entropy']:.6f}")
    print(f"  Baseline LR_dot (mean):      {baseline_agg['LR_dot']:.6f}")
    print(f"  Baseline berry_phase (mean): {baseline_agg['berry_phase']:.6f}")
    print(f"  Baseline negentropy (mean):  {baseline_agg['negentropy']:.6f}")

    # 3q baseline
    print("\n[BASELINE 3Q] Running canonical 3q engine...")
    baseline_3q = run_3q_baseline(N_CYCLES)
    baseline_3q_best_ic = max(m["best_I_c"] for m in baseline_3q)
    print(f"  3q baseline best I_c: {baseline_3q_best_ic:.6f}")

    # Dual-stack baseline
    print("\n[BASELINE DUAL] Running interleaved dual-stack...")
    dual_baseline = run_interleaved_baseline(n_cycles=20)
    dual_baseline_agg = aggregate_metrics(dual_baseline)

    breaks = {}
    all_layer_health = {}

    # ─── BREAK 1: L2 Real Only ────────────────────────────────────
    print("\n[BREAK 1] L2 — Force rho to real (kill C^2)...")
    b1 = break_L2_real_only(N_CYCLES)
    b1_agg = aggregate_metrics(b1)
    health = assess_all_layers(baseline_agg, b1_agg)
    killed = [l for l, h in health.items() if h["status"] == "killed"]
    degraded = [l for l, h in health.items() if h["status"] == "degraded"]
    survived = [l for l, h in health.items() if h["status"] == "survived"]
    breaks["break_L2_real_only"] = {
        "what": "Force rho to real after each operator (kill complex carrier)",
        "layers_killed": killed,
        "layers_degraded": degraded,
        "layers_survived": survived,
        "details": health,
        "metrics": b1_agg,
    }
    all_layer_health["L2"] = health
    print(f"  Killed: {killed}")
    print(f"  Degraded: {degraded}")
    print(f"  Survived: {survived}")

    # ─── BREAK 2: L4 No Chirality ─────────────────────────────────
    print("\n[BREAK 2] L4 — Force psi_L = psi_R (kill chirality)...")
    b2 = break_L4_no_chirality(N_CYCLES)
    b2_agg = aggregate_metrics(b2)
    health = assess_all_layers(baseline_agg, b2_agg)
    killed = [l for l, h in health.items() if h["status"] == "killed"]
    degraded = [l for l, h in health.items() if h["status"] == "degraded"]
    survived = [l for l, h in health.items() if h["status"] == "survived"]
    breaks["break_L4_no_chirality"] = {
        "what": "Force psi_L = psi_R each cycle (kill chirality)",
        "layers_killed": killed,
        "layers_degraded": degraded,
        "layers_survived": survived,
        "details": health,
        "metrics": b2_agg,
    }
    all_layer_health["L4"] = health
    print(f"  Killed: {killed}")
    print(f"  Degraded: {degraded}")
    print(f"  Survived: {survived}")

    # ─── BREAK 3: L5 Remove Se ────────────────────────────────────
    print("\n[BREAK 3] L5 — Replace Se with Ne operator (kill topology variety)...")
    b3 = break_L5_remove_Se(N_CYCLES)
    b3_agg = aggregate_metrics(b3)
    health = assess_all_layers(baseline_agg, b3_agg)
    killed = [l for l, h in health.items() if h["status"] == "killed"]
    degraded = [l for l, h in health.items() if h["status"] == "degraded"]
    survived = [l for l, h in health.items() if h["status"] == "survived"]
    breaks["break_L5_remove_Se"] = {
        "what": "Replace Se topology with Ne operator (only 3 distinct topologies)",
        "layers_killed": killed,
        "layers_degraded": degraded,
        "layers_survived": survived,
        "details": health,
        "metrics": b3_agg,
    }
    all_layer_health["L5"] = health
    print(f"  Killed: {killed}")
    print(f"  Degraded: {degraded}")
    print(f"  Survived: {survived}")

    # ─── BREAK 4: L7 Random Order ─────────────────────────────────
    print("\n[BREAK 4] L7 — Randomize stage order each cycle (20 trials)...")
    b4 = break_L7_random_order(N_CYCLES, n_trials=20)
    b4_agg = aggregate_metrics(b4)
    health = assess_all_layers(baseline_agg, b4_agg)
    killed = [l for l, h in health.items() if h["status"] == "killed"]
    degraded = [l for l, h in health.items() if h["status"] == "degraded"]
    survived = [l for l, h in health.items() if h["status"] == "survived"]
    breaks["break_L7_random_order"] = {
        "what": "Randomize 8-stage order each cycle, averaged over 20 trials",
        "layers_killed": killed,
        "layers_degraded": degraded,
        "layers_survived": survived,
        "details": health,
        "metrics": b4_agg,
    }
    all_layer_health["L7"] = health
    print(f"  Killed: {killed}")
    print(f"  Degraded: {degraded}")
    print(f"  Survived: {survived}")

    # ─── BREAK 5: L8 Same Polarity ────────────────────────────────
    print("\n[BREAK 5] L8 — Force all polarity_up=True (kill polarity mixing)...")
    b5 = break_L8_same_polarity(N_CYCLES)
    b5_agg = aggregate_metrics(b5)
    health = assess_all_layers(baseline_agg, b5_agg)
    killed = [l for l, h in health.items() if h["status"] == "killed"]
    degraded = [l for l, h in health.items() if h["status"] == "degraded"]
    survived = [l for l, h in health.items() if h["status"] == "survived"]
    breaks["break_L8_same_polarity"] = {
        "what": "Force all operators to polarity_up=True",
        "layers_killed": killed,
        "layers_degraded": degraded,
        "layers_survived": survived,
        "details": health,
        "metrics": b5_agg,
    }
    all_layer_health["L8"] = health
    print(f"  Killed: {killed}")
    print(f"  Degraded: {degraded}")
    print(f"  Survived: {survived}")

    # ─── BREAK 6: L9 Strength ─────────────────────────────────────
    print("\n[BREAK 6a] L9 — Strength=0 (all identity)...")
    b6a = break_L9_strength(N_CYCLES, strength_val=0.0)
    b6a_agg = aggregate_metrics(b6a)

    print("[BREAK 6b] L9 — Strength=1.0 (maximum)...")
    b6b = break_L9_strength(N_CYCLES, strength_val=1.0)
    b6b_agg = aggregate_metrics(b6b)

    print("[BREAK 6c] L9 — Strength=0.5 (midrange)...")
    b6c = break_L9_strength(N_CYCLES, strength_val=0.5)
    b6c_agg = aggregate_metrics(b6c)

    health_0 = assess_all_layers(baseline_agg, b6a_agg)
    health_1 = assess_all_layers(baseline_agg, b6b_agg)

    killed_0 = [l for l, h in health_0.items() if h["status"] == "killed"]
    killed_1 = [l for l, h in health_1.items() if h["status"] == "killed"]

    breaks["break_L9_strength_0"] = {
        "what": "Set all piston strength to 0 (identity)",
        "layers_killed": killed_0,
        "layers_degraded": [l for l, h in health_0.items() if h["status"] == "degraded"],
        "layers_survived": [l for l, h in health_0.items() if h["status"] == "survived"],
        "details": health_0,
        "metrics": b6a_agg,
    }
    breaks["break_L9_strength_1"] = {
        "what": "Set all piston strength to 1.0 (maximum)",
        "layers_killed": killed_1,
        "layers_degraded": [l for l, h in health_1.items() if h["status"] == "degraded"],
        "layers_survived": [l for l, h in health_1.items() if h["status"] == "survived"],
        "details": health_1,
        "metrics": b6b_agg,
    }
    breaks["break_L9_strength_0.5"] = {
        "what": "Set all piston strength to 0.5 (midrange reference)",
        "metrics": b6c_agg,
    }
    all_layer_health["L9"] = health_0  # Use strength=0 as the primary break
    print(f"  Strength=0 killed: {killed_0}")
    print(f"  Strength=1 killed: {killed_1}")

    # ─── BREAK 7: L10 Single Type ─────────────────────────────────
    print("\n[BREAK 7] L10 — Single type only (20 cycles)...")
    b7_t1 = break_L10_single_type(n_cycles=20, engine_type=1)
    b7_t2 = break_L10_single_type(n_cycles=20, engine_type=2)
    b7_t1_agg = aggregate_metrics(b7_t1)
    b7_t2_agg = aggregate_metrics(b7_t2)

    # Compare to interleaved dual
    health_t1 = assess_all_layers(dual_baseline_agg, b7_t1_agg)
    health_t2 = assess_all_layers(dual_baseline_agg, b7_t2_agg)

    breaks["break_L10_type1_only"] = {
        "what": "Run 20 cycles of Type 1 only",
        "layers_killed": [l for l, h in health_t1.items() if h["status"] == "killed"],
        "layers_degraded": [l for l, h in health_t1.items() if h["status"] == "degraded"],
        "layers_survived": [l for l, h in health_t1.items() if h["status"] == "survived"],
        "details": health_t1,
        "metrics": b7_t1_agg,
    }
    breaks["break_L10_type2_only"] = {
        "what": "Run 20 cycles of Type 2 only",
        "layers_killed": [l for l, h in health_t2.items() if h["status"] == "killed"],
        "layers_degraded": [l for l, h in health_t2.items() if h["status"] == "degraded"],
        "layers_survived": [l for l, h in health_t2.items() if h["status"] == "survived"],
        "details": health_t2,
        "metrics": b7_t2_agg,
    }
    all_layer_health["L10"] = health_t1
    print(f"  Type1-only killed: {[l for l, h in health_t1.items() if h['status'] == 'killed']}")
    print(f"  Type2-only killed: {[l for l, h in health_t2.items() if h['status'] == 'killed']}")

    # Entropy variance comparison
    t1_entropy_var = float(np.var([m["entropy"] for m in b7_t1]))
    t2_entropy_var = float(np.var([m["entropy"] for m in b7_t2]))
    dual_entropy_var = float(np.var([m["entropy"] for m in dual_baseline]))
    print(f"  Entropy variance: T1={t1_entropy_var:.6f}, T2={t2_entropy_var:.6f}, Dual={dual_entropy_var:.6f}")

    # ─── BREAK 8: L11 Lock Eta ────────────────────────────────────
    print("\n[BREAK 8] L11 — Lock eta=0.001 (degenerate inner torus)...")
    b8 = break_L11_lock_eta(N_CYCLES, eta_lock=0.001)
    b8_agg = aggregate_metrics(b8)
    health = assess_all_layers(baseline_agg, b8_agg)
    killed = [l for l, h in health.items() if h["status"] == "killed"]
    degraded = [l for l, h in health.items() if h["status"] == "degraded"]
    survived = [l for l, h in health.items() if h["status"] == "survived"]
    breaks["break_L11_lock_eta"] = {
        "what": "Lock torus to eta=0.001 (degenerate inner)",
        "layers_killed": killed,
        "layers_degraded": degraded,
        "layers_survived": survived,
        "details": health,
        "metrics": b8_agg,
    }
    all_layer_health["L11"] = health
    print(f"  Killed: {killed}")
    print(f"  Degraded: {degraded}")
    print(f"  Survived: {survived}")

    # ─── BREAK 9: L12 No Fi 4x4 ──────────────────────────────────
    print("\n[BREAK 9] L12 — Remove Fi from 4x4 engine (kill entanglement dynamics)...")
    b9 = break_L12_no_Fi_4x4(N_CYCLES)
    b9_agg = aggregate_metrics(b9)
    health = assess_all_layers(baseline_agg, b9_agg)
    killed = [l for l, h in health.items() if h["status"] == "killed"]
    degraded = [l for l, h in health.items() if h["status"] == "degraded"]
    survived = [l for l, h in health.items() if h["status"] == "survived"]
    breaks["break_L12_no_Fi"] = {
        "what": "Remove Fi from 4x4 engine (identity replacement)",
        "layers_killed": killed,
        "layers_degraded": degraded,
        "layers_survived": survived,
        "details": health,
        "metrics": b9_agg,
    }
    all_layer_health["L12"] = health
    print(f"  Killed: {killed}")
    print(f"  Degraded: {degraded}")
    print(f"  Survived: {survived}")

    # ─── BREAK 10: L13 No Fe 3q ──────────────────────────────────
    print("\n[BREAK 10] L13 — Remove Fe from 3q engine (kill bridge)...")
    b10 = break_L13_no_Fe_3q(N_CYCLES)
    b10_best_ic = max(m["best_I_c"] for m in b10)

    # Classify relative to 3q baseline
    ic_ratio = abs(b10_best_ic) / abs(baseline_3q_best_ic) if abs(baseline_3q_best_ic) > 1e-12 else 0.0
    if ic_ratio < 0.1:
        ic_status = "killed"
    elif ic_ratio < 0.5:
        ic_status = "degraded"
    else:
        ic_status = "survived"

    breaks["break_L13_no_Fe_3q"] = {
        "what": "Remove Fe from 3q engine (Ti+Te+Fi only), deph=0.05, theta=pi",
        "I_c_status": ic_status,
        "best_I_c_broken": float(b10_best_ic),
        "best_I_c_baseline": float(baseline_3q_best_ic),
        "I_c_ratio": float(ic_ratio),
        "all_cuts_nonpositive": all(
            all(m["info"][cn]["I_c"] <= 0 for cn in m["info"]) for m in b10
        ),
        "trajectory": [float(m["best_I_c"]) for m in b10],
    }
    print(f"  Best I_c (broken): {b10_best_ic:.6f} vs baseline {baseline_3q_best_ic:.6f}")
    print(f"  Status: {ic_status}")

    # ─── DEPENDENCY MATRIX ────────────────────────────────────────
    print("\n" + "=" * 72)
    print("  DEPENDENCY MATRIX")
    print("=" * 72)

    # For each break, record which layers it kills
    layer_order = ["L2_carrier", "L4_chirality", "L5_topology", "L6_su2_algebra",
                   "L7_composition_order", "L8_polarity", "L9_strength",
                   "L10_dual_stack", "L11_torus_transport", "L12_entanglement"]

    dependency_matrix = {}
    break_to_layer = {
        "L2": all_layer_health.get("L2", {}),
        "L4": all_layer_health.get("L4", {}),
        "L5": all_layer_health.get("L5", {}),
        "L7": all_layer_health.get("L7", {}),
        "L8": all_layer_health.get("L8", {}),
        "L9": all_layer_health.get("L9", {}),
        "L10": all_layer_health.get("L10", {}),
        "L11": all_layer_health.get("L11", {}),
        "L12": all_layer_health.get("L12", {}),
    }

    for break_layer, health_map in break_to_layer.items():
        deps = []
        for layer_name, layer_health in health_map.items():
            if layer_health.get("status") in ("killed", "degraded"):
                deps.append(layer_name)
        dependency_matrix[break_layer] = deps

    # Print dependency matrix
    for break_layer, deps in sorted(dependency_matrix.items()):
        print(f"  Break {break_layer} --> kills/degrades: {deps}")

    # ─── SUMMARY ──────────────────────────────────────────────────
    # Count how many higher layers each break kills
    load_bearing_score = {}
    for break_layer, deps in dependency_matrix.items():
        load_bearing_score[break_layer] = len(deps)

    most_load_bearing = max(load_bearing_score, key=load_bearing_score.get)

    # Fragile = killed by most breaks
    fragility_score = {}
    for layer in layer_order:
        count = 0
        for break_layer, health_map in break_to_layer.items():
            if layer in health_map and health_map[layer].get("status") in ("killed", "degraded"):
                count += 1
        fragility_score[layer] = count

    most_fragile = max(fragility_score, key=fragility_score.get) if fragility_score else "none"

    # Fully independent = survived all breaks
    fully_independent = [
        l for l in layer_order
        if fragility_score.get(l, 0) == 0
    ]

    summary = {
        "most_load_bearing_layer": most_load_bearing,
        "most_load_bearing_score": load_bearing_score[most_load_bearing],
        "most_fragile_layer": most_fragile,
        "most_fragile_score": fragility_score.get(most_fragile, 0),
        "fully_independent_layers": fully_independent,
        "load_bearing_scores": load_bearing_score,
        "fragility_scores": fragility_score,
    }

    print(f"\n  MOST LOAD-BEARING: {most_load_bearing} (kills {load_bearing_score[most_load_bearing]} layers)")
    print(f"  MOST FRAGILE:     {most_fragile} (broken by {fragility_score.get(most_fragile, 0)} breaks)")
    print(f"  INDEPENDENT:      {fully_independent}")

    # ─── OUTPUT JSON ──────────────────────────────────────────────
    output = {
        "name": "cross_layer_negative_propagation",
        "baseline": {
            "metrics_2q": baseline_agg,
            "best_I_c_3q": float(baseline_3q_best_ic),
            "dual_stack_metrics": dual_baseline_agg,
        },
        "breaks": breaks,
        "dependency_matrix": dependency_matrix,
        "summary": summary,
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%d"),
    }

    output = sanitize(output)

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "cross_layer_negative_propagation_results.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults written to {out_path}")

    return output


if __name__ == "__main__":
    main()
