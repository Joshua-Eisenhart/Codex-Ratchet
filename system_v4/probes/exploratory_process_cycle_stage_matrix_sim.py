#!/usr/bin/env python3
"""
Process_Cycle Stage Matrix SIM
==============================
Exploratory wrapper over the current engine_core implementation.

Purpose
-------
Expose the user's documented macro-stage view directly:
  - 2 engine types
  - 8 macro-stages per type
  - each macro-stage runs 4 fixed operator subcycles
  - one shared Axis-6 up/down polarity per macro-stage
  - one documented native operator label per macro-stage

Important honesty boundary
--------------------------
This SIM does NOT claim engine_core natively models 16 macro-stages.
It regroups the existing flat terrain×operator schedule into a 16×4
readout matrix.

Operational choices
-------------------
- Uses current engine_core execution order: Ti -> Fe -> Te -> Fi
- Maps outer stages to base terrains (*_b) and inner stages to fiber terrains (*_f)
- Applies the same StageControls (piston / lever / torus / spinor) across all
  4 operator subcycles of a macro-stage
- Records both a representative trace and trial-averaged summaries
"""

from __future__ import annotations

import json
import os
from datetime import datetime, UTC
from collections import Counter, defaultdict

import numpy as np

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import (
    GeometricEngine, StageControls, TERRAINS, OPERATORS,
    TORUS_INNER, TORUS_OUTER,
)
from geometric_operators import trace_distance_2x2, negentropy
from type2_engine_sim import TYPE1_STAGES, TYPE2_STAGES
from proto_ratchet_sim_runner import EvidenceToken


RESULT_NAME = "process_cycle_stage_matrix_results.json"
OPERATOR_ORDER_SOURCE = "engine_core.py OPERATORS = ['Ti', 'Fe', 'Te', 'Fi']"
DOC_ORDER_CONFLICT = (
    "Some docs imply Fe -> Fi -> Te -> Ti while current engine_core executes "
    "Ti -> Fe -> Te -> Fi. This SIM uses current engine_core order as operational truth."
)
N_TRIALS = 6
PISTON = 0.8


TERRAIN_INDEX = {terrain["name"]: idx for idx, terrain in enumerate(TERRAINS)}


def terrain_name_from_row(topo: str, loop_role: str) -> str:
    suffix = "b" if "outer" in loop_role.lower() else "f"
    return f"{topo}_{suffix}"


def torus_for_loop(loop_role: str) -> float:
    return TORUS_OUTER if "outer" in loop_role.lower() else TORUS_INNER


def summarize_axes(delta_axes: dict[str, float]) -> dict[str, float]:
    return {k: float(v) for k, v in delta_axes.items()}


def run_macro_stage(
    engine_type: int,
    row: tuple,
    trial_seed: int,
) -> dict:
    stage_num, topo, native_operator, label, axis6_up, loop_role = row
    terrain_name = terrain_name_from_row(topo, loop_role)
    terrain_idx = TERRAIN_INDEX[terrain_name]
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
    axes_before = engine.read_axes(state)
    rho_L_start = state.rho_L.copy()
    rho_R_start = state.rho_R.copy()
    history_len_before = len(state.history)

    controls = StageControls(
        piston=PISTON,
        lever=bool(axis6_up),
        torus=torus_target,
        spinor="both",
    )

    subcycles = []
    strength_by_operator = {}
    abs_dphi_score = {}
    trace_score = {}

    state = engine.step(state, stage_idx=terrain_idx, controls=controls)
    macro_history = state.history[history_len_before:]
    if len(macro_history) != len(OPERATORS):
        raise RuntimeError(
            f"Expected {len(OPERATORS)} operator subcycles for {terrain_name}, got {len(macro_history)}"
        )

    prev_rho_L = rho_L_start.copy()
    prev_rho_R = rho_R_start.copy()
    observed_order = [entry["op_name"] for entry in macro_history]

    for subcycle_idx, entry in enumerate(macro_history, start=1):
        operator = entry["op_name"]
        rho_L_after = entry["rho_L"]
        rho_R_after = entry["rho_R"]
        dphi_L = float(entry["dphi_L"])
        dphi_R = float(entry["dphi_R"])
        dist_L = float(trace_distance_2x2(prev_rho_L, rho_L_after))
        dist_R = float(trace_distance_2x2(prev_rho_R, rho_R_after))
        effective_strength = float(entry["strength"])

        strength_by_operator[operator] = effective_strength
        abs_dphi_score[operator] = abs(dphi_L) + abs(dphi_R)
        trace_score[operator] = dist_L + dist_R

        subcycles.append({
            "subcycle_idx": subcycle_idx,
            "operator": operator,
            "terrain_idx": terrain_idx,
            "effective_strength": effective_strength,
            "dphi_L": dphi_L,
            "dphi_R": dphi_R,
            "trace_L": dist_L,
            "trace_R": dist_R,
            "ga0_before": float(entry["ga0_before"]),
            "ga0_after": float(entry["ga0_after"]),
        })

        prev_rho_L = rho_L_after.copy()
        prev_rho_R = rho_R_after.copy()

    axes_after = engine.read_axes(state)
    delta_axes = {k: float(axes_after[k] - axes_before[k]) for k in axes_before}

    observed_native_by_dphi = max(abs_dphi_score, key=abs_dphi_score.get)
    observed_native_by_trace = max(trace_score, key=trace_score.get)

    max_dphi = max(abs_dphi_score.values()) if any(abs_dphi_score.values()) else 1.0
    max_trace = max(trace_score.values()) if any(trace_score.values()) else 1.0
    mixed_score = {}
    for op in OPERATORS:
        mx = (abs_dphi_score.get(op, 0.0) / max_dphi) + (trace_score.get(op, 0.0) / max_trace)
        mixed_score[op] = mx
    observed_native_by_mixed = max(mixed_score, key=mixed_score.get)

    return {
        "engine_type": engine_type,
        "stage_num": stage_num,
        "topology": topo,
        "terrain": terrain_name,
        "loop_role": loop_role,
        "native_operator_doc": native_operator,
        "label": label,
        "axis6_up": bool(axis6_up),
        "axis6_label": "UP" if axis6_up else "DOWN",
        "torus_target": float(torus_target),
        "theta1_init": theta1,
        "theta2_init": theta2,
        "terrain_idx": terrain_idx,
        "observed_operator_order": observed_order,
        "expected_operator_order": list(OPERATORS),
        "operator_order_matches": observed_order == list(OPERATORS),
        "macro_trace_L": float(trace_distance_2x2(rho_L_start, state.rho_L)),
        "macro_trace_R": float(trace_distance_2x2(rho_R_start, state.rho_R)),
        "macro_dphi_L": float(negentropy(state.rho_L) - negentropy(rho_L_start)),
        "macro_dphi_R": float(negentropy(state.rho_R) - negentropy(rho_R_start)),
        "delta_axes": summarize_axes(delta_axes),
        "observed_native_by_abs_dphi": observed_native_by_dphi,
        "observed_native_by_trace": observed_native_by_trace,
        "observed_native_by_mixed": observed_native_by_mixed,
        "native_matches_abs_dphi": observed_native_by_dphi == native_operator,
        "native_matches_trace": observed_native_by_trace == native_operator,
        "native_matches_mixed": observed_native_by_mixed == native_operator,
        "subcycles": subcycles,
    }


def aggregate_macro_runs(records: list[dict]) -> dict:
    sample = records[0]
    axis_keys = list(sample["delta_axes"].keys())
    sub_ops = [r["operator"] for r in sample["subcycles"]]

    agg = {
        "engine_type": sample["engine_type"],
        "stage_num": sample["stage_num"],
        "topology": sample["topology"],
        "terrain": sample["terrain"],
        "loop_role": sample["loop_role"],
        "native_operator_doc": sample["native_operator_doc"],
        "label": sample["label"],
        "axis6_up": sample["axis6_up"],
        "torus_target": sample["torus_target"],
        "representative": records[0],
        "trial_averages": {
            "macro_trace_L": float(np.mean([r["macro_trace_L"] for r in records])),
            "macro_trace_R": float(np.mean([r["macro_trace_R"] for r in records])),
            "macro_dphi_L": float(np.mean([r["macro_dphi_L"] for r in records])),
            "macro_dphi_R": float(np.mean([r["macro_dphi_R"] for r in records])),
            "delta_axes": {
                k: float(np.mean([r["delta_axes"][k] for r in records])) for k in axis_keys
            },
            "native_match_rate_abs_dphi": float(np.mean([r["native_matches_abs_dphi"] for r in records])),
            "native_match_rate_trace": float(np.mean([r["native_matches_trace"] for r in records])),
            "native_match_rate_mixed": float(np.mean([r["native_matches_mixed"] for r in records])),
        },
        "subcycle_averages": [],
    }

    for op in sub_ops:
        sub_records = []
        for r in records:
            sub_records.extend([s for s in r["subcycles"] if s["operator"] == op])
        agg["subcycle_averages"].append({
            "operator": op,
            "effective_strength": float(np.mean([s["effective_strength"] for s in sub_records])),
            "dphi_L": float(np.mean([s["dphi_L"] for s in sub_records])),
            "dphi_R": float(np.mean([s["dphi_R"] for s in sub_records])),
            "trace_L": float(np.mean([s["trace_L"] for s in sub_records])),
            "trace_R": float(np.mean([s["trace_R"] for s in sub_records])),
        })

    return agg


def build_type_summaries(matrix_rows: list[dict]) -> dict:
    summaries = {}
    for engine_type in (1, 2):
        subset = [row for row in matrix_rows if row["engine_type"] == engine_type]
        op_totals = defaultdict(lambda: {"dphi_L": 0.0, "dphi_R": 0.0, "trace_L": 0.0, "trace_R": 0.0, "n": 0})
        dominant_counts_dphi = Counter()
        dominant_counts_trace = Counter()
        dominant_counts_mixed = Counter()

        for row in subset:
            rep = row["representative"]
            dominant_counts_dphi[rep["observed_native_by_abs_dphi"]] += 1
            dominant_counts_trace[rep["observed_native_by_trace"]] += 1
            dominant_counts_mixed[rep["observed_native_by_mixed"]] += 1
            for sub in row["subcycle_averages"]:
                bucket = op_totals[sub["operator"]]
                for key in ("dphi_L", "dphi_R", "trace_L", "trace_R"):
                    bucket[key] += float(sub[key])
                bucket["n"] += 1

        operator_profiles = {}
        for op in OPERATORS:
            bucket = op_totals[op]
            operator_profiles[op] = {
                key: float(bucket[key] / bucket["n"]) if bucket["n"] else 0.0
                for key in ("dphi_L", "dphi_R", "trace_L", "trace_R")
            }

        summaries[str(engine_type)] = {
            "macro_stage_count": len(subset),
            "avg_native_match_rate_abs_dphi": float(np.mean([
                row["trial_averages"]["native_match_rate_abs_dphi"] for row in subset
            ])),
            "avg_native_match_rate_trace": float(np.mean([
                row["trial_averages"]["native_match_rate_trace"] for row in subset
            ])),
            "avg_native_match_rate_mixed": float(np.mean([
                row["trial_averages"]["native_match_rate_mixed"] for row in subset
            ])),
            "operator_profiles": operator_profiles,
            "dominant_counts_abs_dphi": dict(dominant_counts_dphi),
            "dominant_counts_trace": dict(dominant_counts_trace),
            "dominant_counts_mixed": dict(dominant_counts_mixed),
        }
    return summaries


def run():
    matrix_rows = []
    type_tables = {
        1: TYPE1_STAGES,
        2: TYPE2_STAGES,
    }

    print("=" * 80)
    print("PROCESS_CYCLE STAGE MATRIX")
    print("  16 macro-stages = 8 per engine type")
    print("  4 fixed operator subcycles per macro-stage")
    print(f"  Operator order: {', '.join(OPERATORS)}")
    print("=" * 80)

    for engine_type, table in type_tables.items():
        print(f"\nTYPE-{engine_type}")
        print("-" * 80)
        for row in table:
            stage_num, topo, native_operator, label, axis6_up, loop_role = row
            records = [
                run_macro_stage(engine_type, row, trial_seed=1000 + engine_type * 100 + stage_num * 10 + t)
                for t in range(N_TRIALS)
            ]
            agg = aggregate_macro_runs(records)
            matrix_rows.append(agg)
            avg = agg["trial_averages"]
            print(
                f"  S{stage_num:02d} {agg['terrain']:4s} native={native_operator:2s} "
                f"axis6={'UP' if axis6_up else 'DN'} "
                f"ΔΦ(L/R)=({avg['macro_dphi_L']:+.4f},{avg['macro_dphi_R']:+.4f}) "
                f"D(L/R)=({avg['macro_trace_L']:.4f},{avg['macro_trace_R']:.4f}) "
                f"native-match[dphi]={avg['native_match_rate_abs_dphi']:.2f} "
                f"order={'/'.join(agg['representative']['observed_operator_order'])}"
            )

    total_mixed_matches = sum([1 for row in matrix_rows if row["trial_averages"]["native_match_rate_mixed"] >= 0.5])
    tokens = [
        EvidenceToken(
            "E_PROCESS_CYCLE_STAGE_MATRIX_OK",
            "S_PROCESS_CYCLE_STAGE_MATRIX",
            "PASS",
            float(len(matrix_rows)),
        ),
        EvidenceToken(
            "E_PROCESS_CYCLE_NATIVE_DOMINANT",
            "S_PROCESS_CYCLE_STAGE_MATRIX",
            "PASS" if total_mixed_matches >= 8 else "FAIL",
            float(total_mixed_matches),
            f"Mixed score matches >= 8 required, got {total_mixed_matches}",
        )
    ]

    payload = {
        "schema": "SIM_EVIDENCE_v1",
        "file": "process_cycle_stage_matrix_sim.py",
        "timestamp": datetime.now(UTC).isoformat(),
        "operator_order_used": OPERATORS,
        "operator_order_source": OPERATOR_ORDER_SOURCE,
        "operator_order_conflict_note": DOC_ORDER_CONFLICT,
        "macro_stage_count": len(matrix_rows),
        "subcycles_per_macro_stage": len(OPERATORS),
        "trial_count_per_macro_stage": N_TRIALS,
        "type_summaries": build_type_summaries(matrix_rows),
        "matrix_rows": matrix_rows,
        "evidence_ledger": [t.__dict__ for t in tokens],
    }

    results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, RESULT_NAME)
    with open(outpath, "w") as f:
        json.dump(payload, f, indent=2)

    print("\n" + "=" * 80)
    print(f"Saved: {outpath}")
    print("=" * 80)
    return tokens


if __name__ == "__main__":
    run()
