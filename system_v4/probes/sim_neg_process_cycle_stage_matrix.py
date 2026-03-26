#!/usr/bin/env python3
"""
Negative battery for the 16x4 Process_Cycle stage matrix.

Purpose
-------
Probe what the current stage model is NOT by comparing the baseline
macro-stage program against several wrong-form alternatives:

1. Wrong operator orders
2. Mixed Axis-6 polarity inside a stage
3. Native-only stage collapse
4. Flattened engine-type weighting

This SIM stays exploratory unless explicitly registered.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime, UTC
from itertools import permutations, product

import numpy as np

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import (
    GeometricEngine, EngineState, StageControls, OPERATORS, TERRAINS,
)
from geometric_operators import (
    apply_Ti, apply_Fe, apply_Te, apply_Fi,
    negentropy, trace_distance_2x2, _ensure_valid_density, SIGMA_X,
)
from hopf_manifold import (
    left_density, right_density, inter_torus_transport_partial,
    torus_radii, fiber_action,
)
from process_cycle_stage_matrix_sim import terrain_name_from_row, torus_for_loop
from type2_engine_sim import TYPE1_STAGES, TYPE2_STAGES
from proto_ratchet_sim_runner import EvidenceToken


RESULT_NAME = "neg_process_cycle_stage_matrix_results.json"
N_TRIALS = 4
PISTON = 0.8
AXIS_EPS = 0.005

TERRAIN_INDEX = {terrain["name"]: idx for idx, terrain in enumerate(TERRAINS)}
OP_FN = {"Ti": apply_Ti, "Fe": apply_Fe, "Te": apply_Te, "Fi": apply_Fi}

BASELINE_ORDER = tuple(OPERATORS)
ORDER_VARIANTS = {
    "_".join(order): list(order)
    for order in permutations(OPERATORS)
    if tuple(order) != BASELINE_ORDER
}

AXIS6_VARIANTS = {
    "".join("U" if bit else "D" for bit in pattern): list(pattern)
    for pattern in product([False, True], repeat=len(OPERATORS))
    if tuple(pattern) not in ((False, False, False, False), (True, True, True, True))
}


def init_stage(engine_type: int, row: tuple, trial_seed: int) -> tuple[GeometricEngine, EngineState, dict]:
    stage_num, topo, native_operator, label, axis6_up, loop_role = row
    terrain_name = terrain_name_from_row(topo, loop_role)
    torus_target = torus_for_loop(loop_role)

    rng = np.random.default_rng(trial_seed)
    theta1 = float(rng.uniform(0, 2 * np.pi))
    theta2 = float(rng.uniform(0, 2 * np.pi))

    engine = GeometricEngine(engine_type=engine_type)
    state = engine.init_state(
        eta=torus_target,
        theta1=theta1,
        theta2=theta2,
        rng=np.random.default_rng(trial_seed),
    )
    meta = {
        "stage_num": stage_num,
        "topology": topo,
        "native_operator": native_operator,
        "label": label,
        "axis6_up": bool(axis6_up),
        "loop_role": loop_role,
        "terrain_name": terrain_name,
        "terrain_idx": TERRAIN_INDEX[terrain_name],
        "torus_target": float(torus_target),
    }
    return engine, state, meta


def summarize_axes(delta_axes: dict[str, float]) -> dict[str, float]:
    return {k: float(v) for k, v in delta_axes.items()}


def axes_delta(engine: GeometricEngine, before: EngineState, after: EngineState) -> dict[str, float]:
    axes_before = engine.read_axes(before)
    axes_after = engine.read_axes(after)
    return {k: float(axes_after[k] - axes_before[k]) for k in axes_before}


def apply_subcycle_variant(
    engine: GeometricEngine,
    state: EngineState,
    terrain: dict,
    op_name: str,
    controls: StageControls,
    *,
    lever_override: bool | None = None,
    flatten_type_weighting: bool = False,
) -> EngineState:
    ga0_target = engine._ga0_target(terrain, op_name, controls)
    ga0_alpha = min(1.0, 0.10 + 0.45 * controls.piston + (0.10 if terrain["open"] else 0.0))
    new_ga0 = float(np.clip((1.0 - ga0_alpha) * state.ga0_level + ga0_alpha * ga0_target, 0.0, 1.0))

    if flatten_type_weighting:
        strength = controls.piston
        if op_name in ("Te", "Fe"):
            strength *= 0.7 + 0.6 * new_ga0
        else:
            strength *= 1.3 - 0.6 * new_ga0
        strength = float(np.clip(strength, 0.0, 1.0))
    else:
        strength = float(engine._operator_strength(terrain, op_name, controls, ga0_level=new_ga0))

    polarity = controls.lever if lever_override is None else lever_override
    angle_mod, dt_mod = engine._terrain_modulation(terrain)

    q_old = state.q()
    q_step = q_old
    new_eta = controls.torus
    if abs(new_eta - state.eta) > 1e-8:
        alpha = engine._geometry_transport_alpha(state.eta, new_eta, strength, new_ga0)
        q_step = inter_torus_transport_partial(q_old, state.eta, new_eta, alpha)
        a, b, c, d = q_step
        z1 = a + 1j * b
        z2 = c + 1j * d
        new_theta1 = float(np.angle(z1))
        new_theta2 = float(np.angle(z2))
        new_eta = float(np.arctan2(abs(z2), abs(z1)))

        rho_L_geo = left_density(q_step)
        rho_R_geo = right_density(q_step)
        memory = 0.10 * (1.0 - alpha)
        new_rho_L = _ensure_valid_density((1.0 - memory) * rho_L_geo + memory * state.rho_L)
        new_rho_R = _ensure_valid_density((1.0 - memory) * rho_R_geo + memory * state.rho_R)
    else:
        new_eta = state.eta
        new_theta1 = state.theta1
        new_theta2 = state.theta2
        new_rho_L = state.rho_L.copy()
        new_rho_R = state.rho_R.copy()

    rho_L_axis0 = engine._fiber_coarse_grained_density(q_step, new_ga0, "left")
    rho_R_axis0 = engine._fiber_coarse_grained_density(q_step, new_ga0, "right")
    axis0_blend = min(0.45, strength * (0.05 + 0.30 * new_ga0))
    new_rho_L = _ensure_valid_density((1.0 - axis0_blend) * new_rho_L + axis0_blend * rho_L_axis0)
    new_rho_R = _ensure_valid_density((1.0 - axis0_blend) * new_rho_R + axis0_blend * rho_R_axis0)

    op_kwargs = {"polarity_up": polarity, "strength": strength}
    if op_name == "Te":
        op_kwargs["angle"] = 0.3 * angle_mod
    if op_name == "Fe":
        op_kwargs["dt"] = 0.05 * dt_mod

    op_fn = OP_FN[op_name]

    if controls.spinor in ("left", "both"):
        new_rho_L = op_fn(new_rho_L, **op_kwargs)

    if controls.spinor in ("right", "both"):
        right_kwargs = dict(op_kwargs)
        applied_op = op_name
        if applied_op == "Te":
            right_kwargs["polarity_up"] = not polarity
        elif applied_op == "Ti":
            phase = new_theta2 - new_theta1
            basis = np.array(
                [[1.0, np.exp(1j * phase)],
                 [1.0, -np.exp(1j * phase)]],
                dtype=complex,
            ) / np.sqrt(2.0)
            rho_conj = basis @ new_rho_R @ basis.conj().T
            rho_conj = op_fn(rho_conj, **right_kwargs)
            new_rho_R = basis.conj().T @ rho_conj @ basis
            new_rho_R = _ensure_valid_density(new_rho_R)
            applied_op = None
        elif applied_op == "Fe":
            rho_conj = SIGMA_X @ new_rho_R @ SIGMA_X
            rho_conj = op_fn(rho_conj, **right_kwargs)
            new_rho_R = SIGMA_X @ rho_conj @ SIGMA_X
            new_rho_R = _ensure_valid_density(new_rho_R)
            applied_op = None
        elif applied_op == "Fi":
            rho_conj = SIGMA_X @ new_rho_R @ SIGMA_X
            rho_conj = op_fn(rho_conj, **right_kwargs)
            new_rho_R = SIGMA_X @ rho_conj @ SIGMA_X
            new_rho_R = _ensure_valid_density(new_rho_R)
            applied_op = None
        if applied_op is not None:
            new_rho_R = op_fn(new_rho_R, **right_kwargs)

    d_theta = (2 * np.pi / 32) * strength
    if terrain["loop"] == "fiber":
        new_theta2 = (new_theta2 + d_theta) % (2 * np.pi)
        new_theta1 = (new_theta1 + 0.5 * d_theta) % (2 * np.pi)
    else:
        new_theta1 = (new_theta1 + d_theta) % (2 * np.pi)
        new_theta2 = (new_theta2 + 0.5 * d_theta) % (2 * np.pi)

    return EngineState(
        rho_L=new_rho_L,
        rho_R=new_rho_R,
        eta=new_eta,
        theta1=new_theta1,
        theta2=new_theta2,
        ga0_level=new_ga0,
        stage_idx=state.stage_idx,
        engine_type=state.engine_type,
        history=list(state.history),
    )


def run_program_variant(
    engine_type: int,
    row: tuple,
    trial_seed: int,
    *,
    operator_order: list[str],
    lever_program: list[bool],
    flatten_type_weighting: bool = False,
) -> dict:
    engine, state, meta = init_stage(engine_type, row, trial_seed)
    terrain = TERRAINS[meta["terrain_idx"]]
    before = state
    controls = StageControls(
        piston=PISTON,
        lever=meta["axis6_up"],
        torus=meta["torus_target"],
        spinor="both",
    )

    subcycles = []
    prev_L = state.rho_L.copy()
    prev_R = state.rho_R.copy()

    for idx, (op_name, lever) in enumerate(zip(operator_order, lever_program), start=1):
        state = apply_subcycle_variant(
            engine,
            state,
            terrain,
            op_name,
            controls,
            lever_override=lever,
            flatten_type_weighting=flatten_type_weighting,
        )
        subcycles.append({
            "subcycle_idx": idx,
            "operator": op_name,
            "axis6_up": bool(lever),
            "trace_L": float(trace_distance_2x2(prev_L, state.rho_L)),
            "trace_R": float(trace_distance_2x2(prev_R, state.rho_R)),
            "dphi_L": float(negentropy(state.rho_L) - negentropy(prev_L)),
            "dphi_R": float(negentropy(state.rho_R) - negentropy(prev_R)),
        })
        prev_L = state.rho_L.copy()
        prev_R = state.rho_R.copy()

    return {
        "meta": meta,
        "final_state": state,
        "macro_trace_L": float(trace_distance_2x2(before.rho_L, state.rho_L)),
        "macro_trace_R": float(trace_distance_2x2(before.rho_R, state.rho_R)),
        "delta_axes": summarize_axes(axes_delta(engine, before, state)),
        "subcycles": subcycles,
    }


def compare_variants(base: dict, alt: dict) -> dict:
    base_state = base["final_state"]
    alt_state = alt["final_state"]
    axis_diff = {
        key: float(alt["delta_axes"][key] - base["delta_axes"][key])
        for key in base["delta_axes"]
    }
    return {
        "d_L": float(trace_distance_2x2(base_state.rho_L, alt_state.rho_L)),
        "d_R": float(trace_distance_2x2(base_state.rho_R, alt_state.rho_R)),
        "axis_diff": axis_diff,
        "n_axis_diff": int(sum(abs(v) > AXIS_EPS for v in axis_diff.values())),
    }


def mean_metric(records: list[dict], key: str) -> float:
    return float(np.mean([r[key] for r in records]))


def run():
    type_tables = {1: TYPE1_STAGES, 2: TYPE2_STAGES}

    control_equivalence = []
    order_sweep = defaultdict(list)
    axis6_sweep = defaultdict(list)
    native_only_records = []
    flat_type_records = []

    print("=" * 80)
    print("NEGATIVE PROCESS_CYCLE STAGE MATRIX")
    print("  control: baseline custom runner vs engine.step")
    print("  negatives: wrong order / mixed axis6 / native-only / flat type")
    print("=" * 80)

    for engine_type, table in type_tables.items():
        for row in table:
            stage_num, topo, native_operator, label, axis6_up, loop_role = row
            for t in range(N_TRIALS):
                seed = 4000 + engine_type * 100 + stage_num * 10 + t
                engine, state0, meta = init_stage(engine_type, row, seed)
                controls = StageControls(
                    piston=PISTON,
                    lever=meta["axis6_up"],
                    torus=meta["torus_target"],
                    spinor="both",
                )

                # Baseline from actual engine
                state_engine = engine.step(state0, stage_idx=meta["terrain_idx"], controls=controls)

                # Baseline from custom subcycle runner
                base = run_program_variant(
                    engine_type, row, seed,
                    operator_order=list(OPERATORS),
                    lever_program=[meta["axis6_up"]] * len(OPERATORS),
                )
                control_equivalence.append({
                    "engine_type": engine_type,
                    "stage_num": stage_num,
                    "d_L": float(trace_distance_2x2(state_engine.rho_L, base["final_state"].rho_L)),
                    "d_R": float(trace_distance_2x2(state_engine.rho_R, base["final_state"].rho_R)),
                })

                # Order sweeps
                for variant_name, order in ORDER_VARIANTS.items():
                    alt = run_program_variant(
                        engine_type, row, seed,
                        operator_order=order,
                        lever_program=[meta["axis6_up"]] * len(order),
                    )
                    comp = compare_variants(base, alt)
                    order_sweep[variant_name].append(comp)

                # Mixed axis6 sweeps
                for variant_name, canonical_pattern in AXIS6_VARIANTS.items():
                    lever_program = [
                        meta["axis6_up"] if bit else (not meta["axis6_up"])
                        for bit in canonical_pattern
                    ]
                    alt = run_program_variant(
                        engine_type, row, seed,
                        operator_order=list(OPERATORS),
                        lever_program=lever_program,
                    )
                    comp = compare_variants(base, alt)
                    axis6_sweep[variant_name].append(comp)

                # Native-only collapse
                native_alt = run_program_variant(
                    engine_type, row, seed,
                    operator_order=[native_operator] * len(OPERATORS),
                    lever_program=[meta["axis6_up"]] * len(OPERATORS),
                )
                native_only_records.append(compare_variants(base, native_alt))

                # Flattened engine-type weighting
                flat_alt = run_program_variant(
                    engine_type, row, seed,
                    operator_order=list(OPERATORS),
                    lever_program=[meta["axis6_up"]] * len(OPERATORS),
                    flatten_type_weighting=True,
                )
                flat_type_records.append(compare_variants(base, flat_alt))

    control_mean = {
        "d_L": mean_metric(control_equivalence, "d_L"),
        "d_R": mean_metric(control_equivalence, "d_R"),
    }

    def summarize_family(records_by_name: dict[str, list[dict]]) -> dict:
        summary = {}
        for name, records in records_by_name.items():
            summary[name] = {
                "mean_d_L": mean_metric(records, "d_L"),
                "mean_d_R": mean_metric(records, "d_R"),
                "mean_total_d": float(np.mean([r["d_L"] + r["d_R"] for r in records])),
                "mean_axis_diff_count": float(np.mean([r["n_axis_diff"] for r in records])),
            }
        return summary

    order_summary = summarize_family(order_sweep)
    axis6_summary = summarize_family(axis6_sweep)
    native_only_summary = {
        "mean_d_L": mean_metric(native_only_records, "d_L"),
        "mean_d_R": mean_metric(native_only_records, "d_R"),
        "mean_total_d": float(np.mean([r["d_L"] + r["d_R"] for r in native_only_records])),
        "mean_axis_diff_count": float(np.mean([r["n_axis_diff"] for r in native_only_records])),
    }
    flat_type_summary = {
        "mean_d_L": mean_metric(flat_type_records, "d_L"),
        "mean_d_R": mean_metric(flat_type_records, "d_R"),
        "mean_total_d": float(np.mean([r["d_L"] + r["d_R"] for r in flat_type_records])),
        "mean_axis_diff_count": float(np.mean([r["n_axis_diff"] for r in flat_type_records])),
    }

    closest_wrong_order = min(order_summary.items(), key=lambda kv: kv[1]["mean_total_d"])
    closest_wrong_axis6 = min(axis6_summary.items(), key=lambda kv: kv[1]["mean_total_d"])
    top3_wrong_orders = sorted(order_summary.items(), key=lambda kv: kv[1]["mean_total_d"])[:3]
    top3_mixed_axis6 = sorted(axis6_summary.items(), key=lambda kv: kv[1]["mean_total_d"])[:3]

    print(f"control equivalence: D(L/R)=({control_mean['d_L']:.6f},{control_mean['d_R']:.6f})")
    print(f"closest wrong order: {closest_wrong_order[0]} totalD={closest_wrong_order[1]['mean_total_d']:.4f}")
    print(f"closest mixed axis6: {closest_wrong_axis6[0]} totalD={closest_wrong_axis6[1]['mean_total_d']:.4f}")
    print(f"native-only collapse: totalD={native_only_summary['mean_total_d']:.4f}")
    print(f"flat type weighting: totalD={flat_type_summary['mean_total_d']:.4f}")

    tokens = [
        EvidenceToken(
            "E_NEG_STAGE_MATRIX_CONTROL_EQUIV",
            "S_SIM_NEG_STAGE_MATRIX_CONTROL_V1",
            "PASS" if max(control_mean["d_L"], control_mean["d_R"]) < 1e-9 else "KILL",
            float(max(control_mean["d_L"], control_mean["d_R"])),
        ),
        EvidenceToken(
            "K_NEG_STAGE_ORDER_VARIANTS_V1",
            "S_SIM_NEG_STAGE_ORDER_VARIANTS_V1",
            "KILL" if closest_wrong_order[1]["mean_total_d"] > 0.05 else "PASS",
            float(closest_wrong_order[1]["mean_total_d"]),
        ),
        EvidenceToken(
            "K_NEG_STAGE_AXIS6_MIX_V1",
            "S_SIM_NEG_STAGE_AXIS6_MIX_V1",
            "KILL" if closest_wrong_axis6[1]["mean_total_d"] > 0.05 else "PASS",
            float(closest_wrong_axis6[1]["mean_total_d"]),
        ),
        EvidenceToken(
            "K_NEG_STAGE_NATIVE_ONLY_V1",
            "S_SIM_NEG_STAGE_NATIVE_ONLY_V1",
            "KILL" if native_only_summary["mean_total_d"] > 0.05 else "PASS",
            float(native_only_summary["mean_total_d"]),
        ),
        EvidenceToken(
            "K_NEG_STAGE_TYPE_FLAT_V1",
            "S_SIM_NEG_STAGE_TYPE_FLAT_V1",
            "KILL" if flat_type_summary["mean_total_d"] > 0.05 else "PASS",
            float(flat_type_summary["mean_total_d"]),
        ),
    ]

    payload = {
        "schema": "SIM_EVIDENCE_v1",
        "file": "sim_neg_process_cycle_stage_matrix.py",
        "timestamp": datetime.now(UTC).isoformat(),
        "trial_count_per_stage": N_TRIALS,
        "control_equivalence": control_mean,
        "order_sweep": order_summary,
        "closest_wrong_order": {
            "name": closest_wrong_order[0],
            **closest_wrong_order[1],
        },
        "top3_wrong_orders": [
            {"name": name, **summary} for name, summary in top3_wrong_orders
        ],
        "axis6_sweep": axis6_summary,
        "closest_mixed_axis6": {
            "name": closest_wrong_axis6[0],
            **closest_wrong_axis6[1],
        },
        "top3_mixed_axis6": [
            {"name": name, **summary} for name, summary in top3_mixed_axis6
        ],
        "native_only_collapse": native_only_summary,
        "flat_type_weighting": flat_type_summary,
        "evidence_ledger": [t.__dict__ for t in tokens],
    }

    results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, RESULT_NAME)
    with open(outpath, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"saved: {outpath}")
    return tokens


if __name__ == "__main__":
    run()
