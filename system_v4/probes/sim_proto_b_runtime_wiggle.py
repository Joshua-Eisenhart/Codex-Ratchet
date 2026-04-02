#!/usr/bin/env python3
"""
Proto-B Runtime Wiggle Exploration
==================================
Status: [Exploratory probe]

Purpose:
  Run a bounded, runtime-native wiggle exploration over candidate math
  families related to Carnot/Szilard-style descriptions without
  canonizing any family as ontology.

Proto-B guardrails:
  - no canon claims
  - no structural 64 closure claims
  - no FEP/Ax0 identity claims
  - no metaphor-first conclusions
  - fail closed on dead candidates
  - report signed and absolute summaries separately

This probe uses live engine microsteps only:
  - engine type
  - torus program
  - axis0 program
  - ga0 updates
  - transport activation
  - phase / torus movement
  - left/right negentropy and coherence changes
"""

from __future__ import annotations

import copy
import json
import math
import os
import sys
from collections import defaultdict
from datetime import UTC, datetime

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import (  # noqa: E402
    GeometricEngine,
    EngineState,
    OPERATORS,
    STAGES,
    StageControls,
    TORUS_CLIFFORD,
    TORUS_INNER,
    TORUS_OUTER,
)
from geometric_operators import (  # noqa: E402
    SIGMA_X,
    _ensure_valid_density,
    apply_Fe,
    apply_Fi,
    apply_Te,
    apply_Ti,
    negentropy,
    partial_trace_A,
    partial_trace_B,
    trace_distance_2x2,
)
from hopf_manifold import (  # noqa: E402
    density_to_bloch,
    inter_torus_transport_partial,
    left_density,
    left_weyl_spinor,
    right_density,
    right_weyl_spinor,
    torus_coordinates,
    torus_radii,
)


SEEDS = list(range(24))
ENGINE_TYPES = [1, 2]
AXIS0_LEVELS = [0.1, 0.9]
TORUS_PROGRAMS = ["constant_clifford", "inner_outer_wave"]

ROLE_YANG = {"Fe", "Te"}
ROLE_YIN = {"Ti", "Fi"}
CONTROL_LEFT = {"Ti", "Te"}
CONTROL_RIGHT = {"Fe", "Fi"}


def wrapped_delta(theta_after: float, theta_before: float) -> float:
    return float(np.arctan2(np.sin(theta_after - theta_before), np.cos(theta_after - theta_before)))


def density_summary(rho: np.ndarray) -> dict:
    b = density_to_bloch(rho)
    return {
        "negentropy": float(negentropy(rho)),
        "coherence": float(abs(rho[0, 1])),
        "bloch_norm": float(np.linalg.norm(b)),
        "pop_gap": float(np.real(rho[0, 0] - rho[1, 1])),
    }


def pair_summary(rho_L: np.ndarray, rho_R: np.ndarray) -> dict:
    bL = density_to_bloch(rho_L)
    bR = density_to_bloch(rho_R)
    dot = float(np.dot(bL, bR) / (np.linalg.norm(bL) * np.linalg.norm(bR) + 1e-12))
    dot = float(np.clip(dot, -1.0, 1.0))
    return {
        "trace_distance_LR": float(trace_distance_2x2(rho_L, rho_R)),
        "bloch_angle": float(np.arccos(abs(dot))),
        "avg_negentropy": float(0.5 * (negentropy(rho_L) + negentropy(rho_R))),
        "avg_coherence": float(0.5 * (abs(rho_L[0, 1]) + abs(rho_R[0, 1]))),
    }


def stage_controls(axis0_level: float, torus_program: str) -> dict[int, StageControls]:
    if torus_program == "constant_clifford":
        torus_values = [TORUS_CLIFFORD] * 8
    elif torus_program == "inner_outer_wave":
        torus_values = [
            TORUS_INNER,
            TORUS_CLIFFORD,
            TORUS_OUTER,
            TORUS_CLIFFORD,
            TORUS_OUTER,
            TORUS_CLIFFORD,
            TORUS_INNER,
            TORUS_CLIFFORD,
        ]
    else:
        raise ValueError(f"unknown torus program: {torus_program}")

    return {
        i: StageControls(
            piston=0.8,
            lever=(i % 2 == 0),
            torus=torus_values[i],
            spinor="both",
            axis0=axis0_level,
        )
        for i in range(8)
    }


def init_random_state(engine: GeometricEngine, rng: np.random.Generator) -> EngineState:
    eta = float(rng.choice([TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER]))
    theta1 = float(rng.uniform(0.0, 2.0 * np.pi))
    theta2 = float(rng.uniform(0.0, 2.0 * np.pi))
    ga0_level = float(rng.uniform(0.15, 0.85))
    return engine.init_state(eta=eta, theta1=theta1, theta2=theta2, ga0_level=ga0_level, rng=rng)


def trace_one_cycle(engine_type: int, seed: int, axis0_level: float, torus_program: str) -> dict:
    rng = np.random.default_rng(seed)
    engine = GeometricEngine(engine_type=engine_type)
    state = init_random_state(engine, rng)
    initial_state = copy.deepcopy(state)
    controls = stage_controls(axis0_level, torus_program)
    microsteps = []

    current_state = copy.deepcopy(state)
    for stage_idx, terrain in enumerate(STAGES):
        ctrl = controls[stage_idx]
        for op_slot, op_name in enumerate(OPERATORS):
            before = copy.deepcopy(current_state)

            ga0_target = engine._ga0_target(terrain, op_name, ctrl)
            ga0_alpha = min(1.0, 0.10 + 0.45 * ctrl.piston + (0.10 if terrain["open"] else 0.0))
            if ga0_target is None:
                new_ga0 = float(current_state.ga0_level)
            else:
                new_ga0 = float(
                    np.clip((1.0 - ga0_alpha) * current_state.ga0_level + ga0_alpha * ga0_target, 0.0, 1.0)
                )
            strength = engine._operator_strength(terrain, op_name, ctrl, ga0_level=new_ga0)
            polarity = ctrl.lever
            angle_mod, dt_mod = engine._terrain_modulation(terrain)

            q_old = current_state.q()
            q_step = q_old
            new_eta = current_state.eta
            new_theta1 = current_state.theta1
            new_theta2 = current_state.theta2

            if abs(ctrl.torus - current_state.eta) > 1e-8:
                alpha = engine._geometry_transport_alpha(current_state.eta, ctrl.torus, strength, new_ga0)
                q_step = inter_torus_transport_partial(q_old, current_state.eta, ctrl.torus, alpha)
                a, b, c, d = q_step
                z1 = a + 1j * b
                z2 = c + 1j * d
                new_theta1 = float(np.angle(z1))
                new_theta2 = float(np.angle(z2))
                new_eta = float(np.arctan2(abs(z2), abs(z1)))
                rho_L_geo = left_density(q_step)
                rho_R_geo = right_density(q_step)
                memory = 0.10 * (1.0 - alpha)
                new_rho_L = _ensure_valid_density((1.0 - memory) * rho_L_geo + memory * current_state.rho_L)
                new_rho_R = _ensure_valid_density((1.0 - memory) * rho_R_geo + memory * current_state.rho_R)
            else:
                alpha = 0.0
                new_rho_L = current_state.rho_L.copy()
                new_rho_R = current_state.rho_R.copy()

            rho_AB_axis0 = engine._fiber_coarse_grained_density(q_step, new_ga0)
            rho_L_axis0 = _ensure_valid_density(partial_trace_B(rho_AB_axis0))
            rho_R_axis0 = _ensure_valid_density(partial_trace_A(rho_AB_axis0))
            axis0_blend = min(0.45, strength * (0.05 + 0.30 * new_ga0))
            axis0_injection_norm = float(
                np.linalg.norm(rho_L_axis0 - new_rho_L) + np.linalg.norm(rho_R_axis0 - new_rho_R)
            )
            axis0_effective_gain = float(axis0_blend * axis0_injection_norm)
            new_rho_L = _ensure_valid_density((1.0 - axis0_blend) * new_rho_L + axis0_blend * rho_L_axis0)
            new_rho_R = _ensure_valid_density((1.0 - axis0_blend) * new_rho_R + axis0_blend * rho_R_axis0)

            op_kwargs = {"polarity_up": polarity, "strength": strength}
            if op_name == "Te":
                op_kwargs["q"] = 0.3 * angle_mod
            if op_name == "Fe":
                op_kwargs["phi"] = 0.05 * dt_mod
            op_fn = {"Ti": apply_Ti, "Fe": apply_Fe, "Te": apply_Te, "Fi": apply_Fi}[op_name]

            left_before = density_summary(new_rho_L)
            right_before = density_summary(new_rho_R)
            pair_before = pair_summary(new_rho_L, new_rho_R)

            new_rho_L = op_fn(new_rho_L, **op_kwargs)

            right_kwargs = dict(op_kwargs)
            applied_op = op_name
            if op_name == "Te":
                right_kwargs["polarity_up"] = not polarity
            elif op_name == "Ti":
                phase = new_theta2 - new_theta1
                basis = np.array(
                    [[1.0, np.exp(1j * phase)], [1.0, -np.exp(1j * phase)]],
                    dtype=complex,
                ) / np.sqrt(2.0)
                rho_conj = basis @ new_rho_R @ basis.conj().T
                rho_conj = op_fn(rho_conj, **right_kwargs)
                new_rho_R = basis.conj().T @ rho_conj @ basis
                new_rho_R = _ensure_valid_density(new_rho_R)
                applied_op = None
            elif op_name in ("Fe", "Fi"):
                rho_conj = SIGMA_X @ new_rho_R @ SIGMA_X
                rho_conj = op_fn(rho_conj, **right_kwargs)
                new_rho_R = SIGMA_X @ rho_conj @ SIGMA_X
                new_rho_R = _ensure_valid_density(new_rho_R)
                applied_op = None
            if applied_op is not None:
                new_rho_R = op_fn(new_rho_R, **right_kwargs)

            d_theta = (2.0 * np.pi / 32.0) * strength
            if terrain["loop"] == "fiber":
                new_theta2 = (new_theta2 + d_theta) % (2.0 * np.pi)
                new_theta1 = (new_theta1 + 0.5 * d_theta) % (2.0 * np.pi)
            else:
                new_theta1 = (new_theta1 + d_theta) % (2.0 * np.pi)
                new_theta2 = (new_theta2 + 0.5 * d_theta) % (2.0 * np.pi)

            q_current = np.array(
                [
                    np.cos(new_eta) * np.cos(new_theta1),
                    np.cos(new_eta) * np.sin(new_theta1),
                    np.sin(new_eta) * np.cos(new_theta2),
                    np.sin(new_eta) * np.sin(new_theta2),
                ],
                dtype=float,
            )
            current_state = EngineState(
                psi_L=left_weyl_spinor(q_current),
                psi_R=right_weyl_spinor(q_current),
                rho_AB=_ensure_valid_density(np.kron(new_rho_L, new_rho_R)),
                eta=new_eta,
                theta1=new_theta1,
                theta2=new_theta2,
                stage_idx=current_state.stage_idx,
                engine_type=engine_type,
                history=current_state.history + [],
            )

            left_after = density_summary(new_rho_L)
            right_after = density_summary(new_rho_R)
            pair_after = pair_summary(new_rho_L, new_rho_R)
            R_major_before, R_minor_before = torus_radii(before.eta)
            R_major_after, R_minor_after = torus_radii(current_state.eta)
            dphi_L = left_after["negentropy"] - left_before["negentropy"]
            dphi_R = right_after["negentropy"] - right_before["negentropy"]

            microsteps.append(
                {
                    "stage_idx": stage_idx,
                    "terrain": terrain["name"],
                    "loop": terrain["loop"],
                    "expansion": terrain["expansion"],
                    "open": terrain["open"],
                    "operator": op_name,
                    "operator_slot": op_slot,
                    "strength": float(strength),
                    "ga0_before": float(before.ga0_level),
                    "ga0_target": None if ga0_target is None else float(ga0_target),
                    "ga0_after": float(new_ga0),
                    "axis0_blend": float(axis0_blend),
                    "axis0_injection_norm": float(axis0_injection_norm),
                    "axis0_effective_gain": float(axis0_effective_gain),
                    "transport_alpha": float(alpha),
                    "eta_before": float(before.eta),
                    "eta_after": float(current_state.eta),
                    "deta": float(current_state.eta - before.eta),
                    "theta1_before": float(before.theta1),
                    "theta1_after": float(current_state.theta1),
                    "dtheta1": float(wrapped_delta(current_state.theta1, before.theta1)),
                    "theta2_before": float(before.theta2),
                    "theta2_after": float(current_state.theta2),
                    "dtheta2": float(wrapped_delta(current_state.theta2, before.theta2)),
                    "dphase": float(
                        wrapped_delta(
                            wrapped_delta(current_state.theta2, current_state.theta1),
                            wrapped_delta(before.theta2, before.theta1),
                        )
                    ),
                    "radii_before": [float(R_major_before), float(R_minor_before)],
                    "radii_after": [float(R_major_after), float(R_minor_after)],
                    "left_before": left_before,
                    "left_after": left_after,
                    "right_before": right_before,
                    "right_after": right_after,
                    "pair_before": pair_before,
                    "pair_after": pair_after,
                    "dphi_L": float(dphi_L),
                    "dphi_R": float(dphi_R),
                    "dphi_total": float(dphi_L + dphi_R),
                    "dcoh_total": float(
                        (left_before["coherence"] + right_before["coherence"])
                        - (left_after["coherence"] + right_after["coherence"])
                    ),
                }
            )

    return {
        "engine_type": engine_type,
        "seed": seed,
        "axis0_level": axis0_level,
        "torus_program": torus_program,
        "initial_state": {
            "eta": float(initial_state.eta),
            "theta1": float(initial_state.theta1),
            "theta2": float(initial_state.theta2),
            "ga0": float(initial_state.ga0_level),
            "pair": pair_summary(initial_state.rho_L, initial_state.rho_R),
        },
        "final_state": {
            "eta": float(current_state.eta),
            "theta1": float(current_state.theta1),
            "theta2": float(current_state.theta2),
            "ga0": float(current_state.ga0_level),
            "pair": pair_summary(current_state.rho_L, current_state.rho_R),
        },
        "microsteps": microsteps,
    }


def polygon_area(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 3:
        return 0.0
    x = np.asarray(xs + [xs[0]], dtype=float)
    y = np.asarray(ys + [ys[0]], dtype=float)
    return float(0.5 * np.sum(x[:-1] * y[1:] - x[1:] * y[:-1]))


def mean_or_zero(xs: list[float]) -> float:
    return float(np.mean(xs)) if xs else 0.0


def safe_corr(xs: list[float], ys: list[float]) -> tuple[float | None, str | None]:
    if len(xs) < 3 or len(ys) < 3:
        return None, "too_few_points"
    x = np.asarray(xs, dtype=float)
    y = np.asarray(ys, dtype=float)
    if np.std(x) < 1e-10 or np.std(y) < 1e-10:
        return None, "low_variance"
    return float(np.corrcoef(x, y)[0, 1]), None


def evaluate_run(trace: dict) -> dict:
    steps = trace["microsteps"]
    init_state = trace["initial_state"]
    final_state = trace["final_state"]

    work_abs = float(sum(abs(s["dphi_total"]) for s in steps))
    work_signed = float(sum(s["dphi_total"] for s in steps))
    transport_work_abs = float(sum(abs(s["dphi_total"]) for s in steps if s["transport_alpha"] > 0.0))
    eta_closure = abs(final_state["eta"] - init_state["eta"])
    theta1_closure = abs(wrapped_delta(final_state["theta1"], init_state["theta1"]))
    theta2_closure = abs(wrapped_delta(final_state["theta2"], init_state["theta2"]))
    closure = float(eta_closure + theta1_closure + theta2_closure)

    transport_cost = float(
        sum(
            abs(s["deta"])
            + abs(s["radii_after"][0] - s["radii_before"][0])
            + abs(s["radii_after"][1] - s["radii_before"][1])
            + 0.25 * (abs(s["dtheta1"]) + abs(s["dtheta2"]))
            for s in steps
        )
    )

    ga0s = [s["ga0_after"] for s in steps]
    negs = [s["pair_after"]["avg_negentropy"] for s in steps]
    cycle_area = polygon_area(ga0s, negs)

    expansion = [s["dphi_total"] for s in steps if s["expansion"]]
    compression = [s["dphi_total"] for s in steps if not s["expansion"]]
    role_yang = [s["dphi_total"] for s in steps if s["operator"] in ROLE_YANG]
    role_yin = [s["dphi_total"] for s in steps if s["operator"] in ROLE_YIN]
    control_left = [s["dphi_total"] for s in steps if s["operator"] in CONTROL_LEFT]
    control_right = [s["dphi_total"] for s in steps if s["operator"] in CONTROL_RIGHT]

    lag_score, lag_reason = safe_corr(
        [-s["ga0_after"] + s["ga0_before"] for s in steps[:-1]],
        [s["dphi_total"] for s in steps[1:]],
    )

    candidates = {}

    def add_candidate(name: str, family: str, value: float | None, active: bool, reason: str | None, detail: dict):
        candidates[name] = {
            "family": family,
            "active": bool(active),
            "value": None if value is None else float(value),
            "abs_value": None if value is None else float(abs(value)),
            "reason": reason,
            "detail": detail,
        }

    add_candidate(
        "carnot_closure_adjusted_yield",
        "carnot_style",
        None if work_abs <= 1e-10 else work_abs / (closure + 1e-6),
        work_abs > 1e-10,
        None if work_abs > 1e-10 else "zero_work",
        {"work_abs": work_abs, "closure": closure},
    )
    add_candidate(
        "carnot_transport_normalized_work",
        "carnot_style",
        None if transport_cost <= 1e-10 else work_abs / (transport_cost + 1e-6),
        transport_cost > 1e-10,
        None if transport_cost > 1e-10 else "zero_transport_cost",
        {"work_abs": work_abs, "transport_cost": transport_cost},
    )
    add_candidate(
        "hybrid_transport_actuation",
        "runtime_hybrid",
        (
            sum((s["ga0_after"] - s["ga0_before"]) * s["axis0_effective_gain"] for s in steps)
            / (sum(abs(s["axis0_effective_gain"]) for s in steps) + 1e-6)
        )
        * (transport_work_abs / (transport_cost + 1e-6)),
        len(steps) > 0 and transport_cost > 1e-10,
        None if transport_cost > 1e-10 else "zero_transport_cost",
        {
            "transport_work_abs": transport_work_abs,
            "transport_cost": transport_cost,
            "mean_axis0_effective_gain": mean_or_zero([s["axis0_effective_gain"] for s in steps]),
        },
    )
    add_candidate(
        "carnot_expansion_compression_gap",
        "carnot_style",
        mean_or_zero(expansion) - mean_or_zero(compression),
        bool(expansion and compression),
        None if expansion and compression else "missing_leg_bucket",
        {
            "mean_expansion": mean_or_zero(expansion),
            "mean_compression": mean_or_zero(compression),
        },
    )
    add_candidate(
        "carnot_cycle_area_ga0_neg",
        "carnot_style",
        cycle_area,
        len(steps) >= 3,
        None,
        {"ga0_span": float(max(ga0s) - min(ga0s)), "neg_span": float(max(negs) - min(negs))},
    )
    add_candidate(
        "szilard_net_structure_yield",
        "szilard_style",
        work_signed / max(len(steps), 1),
        len(steps) > 0,
        None,
        {"work_signed": work_signed, "n_steps": len(steps)},
    )
    add_candidate(
        "szilard_coherence_erasure",
        "szilard_style",
        mean_or_zero([s["dcoh_total"] for s in steps]),
        len(steps) > 0,
        None,
        {},
    )
    add_candidate(
        "szilard_ceiling_actuation",
        "szilard_style",
        sum((s["ga0_after"] - s["ga0_before"]) * s["axis0_effective_gain"] for s in steps)
        / (sum(abs(s["axis0_effective_gain"]) for s in steps) + 1e-6),
        len(steps) > 0,
        None,
        {
            "mean_ga0_delta": mean_or_zero([s["ga0_after"] - s["ga0_before"] for s in steps]),
            "mean_axis0_effective_gain": mean_or_zero([s["axis0_effective_gain"] for s in steps]),
        },
    )
    add_candidate(
        "szilard_role_gap",
        "szilard_style",
        mean_or_zero(role_yang) - mean_or_zero(role_yin),
        bool(role_yang and role_yin),
        None if role_yang and role_yin else "missing_role_bucket",
        {
            "mean_yang": mean_or_zero(role_yang),
            "mean_yin": mean_or_zero(role_yin),
        },
    )
    add_candidate(
        "control_partition_gap",
        "control",
        mean_or_zero(control_left) - mean_or_zero(control_right),
        bool(control_left and control_right),
        None if control_left and control_right else "missing_control_bucket",
        {
            "mean_control_left": mean_or_zero(control_left),
            "mean_control_right": mean_or_zero(control_right),
        },
    )
    add_candidate(
        "szilard_lagged_measure_extract",
        "szilard_style",
        lag_score,
        lag_score is not None,
        lag_reason,
        {},
    )

    return {
        "engine_type": trace["engine_type"],
        "seed": trace["seed"],
        "axis0_level": trace["axis0_level"],
        "torus_program": trace["torus_program"],
        "run_meta": {
            "work_abs": work_abs,
            "work_signed": work_signed,
            "closure": closure,
            "transport_cost": transport_cost,
            "final_pair_trace_distance": final_state["pair"]["trace_distance_LR"],
            "final_pair_avg_negentropy": final_state["pair"]["avg_negentropy"],
        },
        "candidates": candidates,
    }


def summarize_family(name: str, family: str, runs: list[dict]) -> dict:
    values = []
    abs_values = []
    inactive_reasons = defaultdict(int)
    by_condition = defaultdict(list)

    for run in runs:
        candidate = run["candidates"][name]
        key = (run["engine_type"], run["axis0_level"], run["torus_program"])
        if candidate["active"] and candidate["value"] is not None:
            values.append(candidate["value"])
            abs_values.append(candidate["abs_value"])
            by_condition[key].append(candidate["value"])
        else:
            inactive_reasons[candidate["reason"] or "inactive"] += 1

    summary_conditions = []
    for key in sorted(by_condition):
        engine_type, axis0_level, torus_program = key
        vals = by_condition[key]
        summary_conditions.append(
            {
                "engine_type": engine_type,
                "axis0_level": axis0_level,
                "torus_program": torus_program,
                "count": len(vals),
                "mean_signed": float(np.mean(vals)),
                "mean_abs": float(np.mean(np.abs(vals))),
                "std_signed": float(np.std(vals)),
            }
        )

    def paired_gap(engine_type: int | None = None, axis0_level: float | None = None, torus_program: str | None = None):
        subset = []
        for run in runs:
            cand = run["candidates"][name]
            if not cand["active"] or cand["value"] is None:
                continue
            if engine_type is not None and run["engine_type"] != engine_type:
                continue
            if axis0_level is not None and run["axis0_level"] != axis0_level:
                continue
            if torus_program is not None and run["torus_program"] != torus_program:
                continue
            subset.append(run)
        return subset

    def mean_for(engine_type: int, axis0_level: float, torus_program: str):
        vals = [
            run["candidates"][name]["value"]
            for run in runs
            if run["engine_type"] == engine_type
            and run["axis0_level"] == axis0_level
            and run["torus_program"] == torus_program
            and run["candidates"][name]["active"]
            and run["candidates"][name]["value"] is not None
        ]
        return None if not vals else float(np.mean(vals))

    axis0_gaps = []
    torus_gaps = []
    type_gaps = []
    for engine_type in ENGINE_TYPES:
        for torus_program in TORUS_PROGRAMS:
            low = mean_for(engine_type, 0.1, torus_program)
            high = mean_for(engine_type, 0.9, torus_program)
            if low is not None and high is not None:
                axis0_gaps.append(high - low)
    for engine_type in ENGINE_TYPES:
        for axis0_level in AXIS0_LEVELS:
            const = mean_for(engine_type, axis0_level, "constant_clifford")
            wave = mean_for(engine_type, axis0_level, "inner_outer_wave")
            if const is not None and wave is not None:
                torus_gaps.append(wave - const)
    for axis0_level in AXIS0_LEVELS:
        for torus_program in TORUS_PROGRAMS:
            t1 = mean_for(1, axis0_level, torus_program)
            t2 = mean_for(2, axis0_level, torus_program)
            if t1 is not None and t2 is not None:
                type_gaps.append(t2 - t1)

    sign_flip_rate = None
    if values:
        pos = sum(v > 0 for v in values)
        neg = sum(v < 0 for v in values)
        sign_flip_rate = float(min(pos, neg) / max(len(values), 1))

    return {
        "family": family,
        "active_fraction": float(len(values) / max(len(runs), 1)),
        "inactive_reasons": dict(inactive_reasons),
        "overall_mean_signed": None if not values else float(np.mean(values)),
        "overall_mean_abs": None if not abs_values else float(np.mean(abs_values)),
        "overall_std_signed": None if not values else float(np.std(values)),
        "sign_flip_rate": sign_flip_rate,
        "by_condition": summary_conditions,
        "paired_gaps": {
            "axis0_high_minus_low_mean": None if not axis0_gaps else float(np.mean(axis0_gaps)),
            "torus_wave_minus_constant_mean": None if not torus_gaps else float(np.mean(torus_gaps)),
            "type2_minus_type1_mean": None if not type_gaps else float(np.mean(type_gaps)),
        },
    }


def main():
    runs = []

    for seed in SEEDS:
        for engine_type in ENGINE_TYPES:
            for axis0_level in AXIS0_LEVELS:
                for torus_program in TORUS_PROGRAMS:
                    trace = trace_one_cycle(
                        engine_type=engine_type,
                        seed=seed,
                        axis0_level=axis0_level,
                        torus_program=torus_program,
                    )
                    runs.append(evaluate_run(trace))

    candidate_names = list(runs[0]["candidates"].keys())
    families = {
        name: runs[0]["candidates"][name]["family"]
        for name in candidate_names
    }

    summary = {
        name: summarize_family(name, families[name], runs)
        for name in candidate_names
    }

    def ranking(sort_key: str):
        ranked = []
        for name, info in summary.items():
            value = info["paired_gaps"][sort_key]
            if value is None:
                continue
            ranked.append({"candidate": name, "family": info["family"], "value": float(value)})
        return sorted(ranked, key=lambda r: abs(r["value"]), reverse=True)

    out = {
        "schema": "SIM_EVIDENCE_v1",
        "file": os.path.basename(__file__),
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "status": "exploratory",
        "proto_b_guardrails": [
            "candidate-family evidence only",
            "runtime-native metrics only",
            "no structural 64 closure claims",
            "no FEP integration claims",
            "signed and absolute summaries kept separate",
            "inactive/dead candidates are reported, not hidden",
        ],
        "sweep": {
            "seeds": SEEDS,
            "engine_types": ENGINE_TYPES,
            "axis0_levels": AXIS0_LEVELS,
            "torus_programs": TORUS_PROGRAMS,
            "n_runs": len(runs),
        },
        "candidate_summaries": summary,
        "rankings": {
            "axis0_gap": ranking("axis0_high_minus_low_mean"),
            "torus_gap": ranking("torus_wave_minus_constant_mean"),
            "type_gap": ranking("type2_minus_type1_mean"),
        },
        "sample_run_meta": [
            {
                "engine_type": run["engine_type"],
                "seed": run["seed"],
                "axis0_level": run["axis0_level"],
                "torus_program": run["torus_program"],
                **run["run_meta"],
            }
            for run in runs[:8]
        ],
    }

    out_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "a2_state",
        "sim_results",
        "proto_b_runtime_wiggle.json",
    )
    out_file = os.path.abspath(out_file)
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    print("=" * 72)
    print("PROTO-B RUNTIME WIGGLE EXPLORATION")
    print("=" * 72)
    print("This is exploratory candidate-family evidence, not canon.\n")
    for name, info in summary.items():
        print(
            f"{name}: family={info['family']}, "
            f"active={info['active_fraction']:.2f}, "
            f"mean={info['overall_mean_signed']}, "
            f"torus_gap={info['paired_gaps']['torus_wave_minus_constant_mean']}, "
            f"axis0_gap={info['paired_gaps']['axis0_high_minus_low_mean']}"
        )
    print(f"\nResults written to {out_file}")


if __name__ == "__main__":
    main()
