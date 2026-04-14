#!/usr/bin/env python3
"""
Mass sweep of the current geometric engine.

This is intentionally operational, not canonical:
- many seeds
- both engine types
- low/high Axis 0 programs
- constant vs varying torus schedules

Goal:
  Check whether the current engine works as a controllable dynamical system
  across a batch of runs, not whether its ontology is final.
"""

import json
import os
import sys
from datetime import UTC, datetime

import numpy as np
classification = "classical_baseline"  # auto-backfill

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import GeometricEngine, StageControls, TORUS_CLIFFORD, TORUS_INNER, TORUS_OUTER
from geometric_operators import trace_distance_2x2


def stage_controls(axis0_level: float, torus_program: str):
    controls = {}
    if torus_program == "constant_clifford":
        torus_values = [TORUS_CLIFFORD] * 8
    elif torus_program == "inner_outer_wave":
        torus_values = [
            TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER, TORUS_CLIFFORD,
            TORUS_OUTER, TORUS_CLIFFORD, TORUS_INNER, TORUS_CLIFFORD,
        ]
    else:
        raise ValueError(f"unknown torus program: {torus_program}")

    for i, torus in enumerate(torus_values):
        controls[i] = StageControls(
            piston=0.8,
            lever=(i % 2 == 0),
            torus=torus,
            spinor="both",
            axis0=axis0_level,
        )
    return controls


def init_random_state(engine: GeometricEngine, rng: np.random.Generator):
    eta = float(rng.choice([TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER]))
    theta1 = float(rng.uniform(0.0, 2 * np.pi))
    theta2 = float(rng.uniform(0.0, 2 * np.pi))
    ga0_level = float(rng.uniform(0.15, 0.85))
    return engine.init_state(eta=eta, theta1=theta1, theta2=theta2, ga0_level=ga0_level, rng=rng)


def run_one(engine_type: int, seed: int, axis0_level: float, torus_program: str):
    rng = np.random.default_rng(seed)
    engine = GeometricEngine(engine_type=engine_type)
    state0 = init_random_state(engine, rng)
    axes0 = engine.read_axes(state0)
    state1 = engine.run_cycle(state0, controls=stage_controls(axis0_level, torus_program))
    axes1 = engine.read_axes(state1)
    return {
        "state0": state0,
        "state1": state1,
        "axes0": axes0,
        "axes1": axes1,
        "dL": float(trace_distance_2x2(state0.rho_L, state1.rho_L)),
        "dR": float(trace_distance_2x2(state0.rho_R, state1.rho_R)),
        "dGA0": float(axes1["GA0_entropy"] - axes0["GA0_entropy"]),
        "dGA3": float(axes1["GA3_chirality"] - axes0["GA3_chirality"]),
        "dGA5": float(axes1["GA5_coupling"] - axes0["GA5_coupling"]),
        "history_len": len(state1.history),
    }


def main():
    seeds = list(range(24))
    low_axis0 = 0.1
    high_axis0 = 0.9

    low_runs = []
    high_runs = []
    type_divergence = []
    torus_divergence = []

    for seed in seeds:
        low_t1 = run_one(1, seed, low_axis0, "constant_clifford")
        high_t1 = run_one(1, seed, high_axis0, "constant_clifford")
        low_t2 = run_one(2, seed, low_axis0, "constant_clifford")
        wave_t1 = run_one(1, seed, high_axis0, "inner_outer_wave")

        low_runs.append({"seed": seed, "type1": low_t1, "type2": low_t2})
        high_runs.append({"seed": seed, "type1": high_t1})

        type_divergence.append({
            "seed": seed,
            "L": float(trace_distance_2x2(low_t1["state1"].rho_L, low_t2["state1"].rho_L)),
            "R": float(trace_distance_2x2(low_t1["state1"].rho_R, low_t2["state1"].rho_R)),
        })
        torus_divergence.append({
            "seed": seed,
            "L": float(trace_distance_2x2(high_t1["state1"].rho_L, wave_t1["state1"].rho_L)),
            "R": float(trace_distance_2x2(high_t1["state1"].rho_R, wave_t1["state1"].rho_R)),
        })

    low_type1_move = [0.5 * (r["type1"]["dL"] + r["type1"]["dR"]) for r in low_runs]
    high_type1_move = [0.5 * (r["type1"]["dL"] + r["type1"]["dR"]) for r in high_runs]
    ga0_effect = [
        {
            "seed": seed,
            "L": float(trace_distance_2x2(low_runs[i]["type1"]["state1"].rho_L, high_runs[i]["type1"]["state1"].rho_L)),
            "R": float(trace_distance_2x2(low_runs[i]["type1"]["state1"].rho_R, high_runs[i]["type1"]["state1"].rho_R)),
            "dGA0_gap": float(high_runs[i]["type1"]["dGA0"] - low_runs[i]["type1"]["dGA0"]),
        }
        for i, seed in enumerate(seeds)
    ]

    summary = {
        "schema": "SIM_EVIDENCE_v1",
        "file": os.path.basename(__file__),
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "n_seeds": len(seeds),
        "summary": {
            "all_runs_completed_32_steps": all(r["type1"]["history_len"] == 32 and r["type2"]["history_len"] == 32 for r in low_runs),
            "type_divergence_mean_L": float(np.mean([x["L"] for x in type_divergence])),
            "type_divergence_mean_R": float(np.mean([x["R"] for x in type_divergence])),
            "type_divergence_pass_rate_0p05": float(np.mean([(x["L"] > 0.05 or x["R"] > 0.05) for x in type_divergence])),
            "axis0_program_mean_gap_L": float(np.mean([x["L"] for x in ga0_effect])),
            "axis0_program_mean_gap_R": float(np.mean([x["R"] for x in ga0_effect])),
            "axis0_program_pass_rate_0p05": float(np.mean([(x["L"] > 0.05 or x["R"] > 0.05) for x in ga0_effect])),
            "torus_program_mean_gap_L": float(np.mean([x["L"] for x in torus_divergence])),
            "torus_program_mean_gap_R": float(np.mean([x["R"] for x in torus_divergence])),
            "torus_program_pass_rate_0p05": float(np.mean([(x["L"] > 0.05 or x["R"] > 0.05) for x in torus_divergence])),
            "state_motion_mean_low_type1": float(np.mean(low_type1_move)),
            "state_motion_mean_high_type1": float(np.mean(high_type1_move)),
            "state_motion_pass_rate_0p05": float(np.mean([x > 0.05 for x in low_type1_move + high_type1_move])),
        },
        "type_divergence": type_divergence,
        "axis0_effect": ga0_effect,
        "torus_program_effect": torus_divergence,
    }

    out_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "a2_state", "sim_results", "engine_mass_sweep_results.json"
    )
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w") as f:
        json.dump(summary, f, indent=2)

    print("=" * 72)
    print("ENGINE MASS SWEEP")
    print("=" * 72)
    for k, v in summary["summary"].items():
        print(f"{k}: {v}")
    print(f"\nResults written to {out_file}")


if __name__ == "__main__":
    main()
