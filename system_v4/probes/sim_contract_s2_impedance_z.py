#!/usr/bin/env python3
"""
SIM 2 — Contract Impedance Z Baseline
=====================================
Measurement-only probe for the current engine.

Contract target:
  Z = ||d rho / dt||^-1
  outer loop = low impedance
  inner loop = high impedance
  same relation for both Type-1 and Type-2

This probe does not claim the current engine implements the contract.
It measures the current engine's stepwise density displacement and
reports whether the expected outer/inner ordering is present.
"""

from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from datetime import UTC, datetime

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import GeometricEngine, StageControls, STAGES
from proto_ratchet_sim_runner import EvidenceToken


RESULT_NAME = "contract_s2_impedance_z_results.json"
EPS = 1e-12


def rho_step_norm(before: np.ndarray, after: np.ndarray) -> float:
    return float(np.linalg.norm(after - before, ord="fro"))


def loop_position(terrain: dict) -> str:
    return "outer" if terrain["loop"] == "base" else "inner"


def run_probe(n_trials: int = 12, piston: float = 0.8) -> dict:
    records = []
    grouped = defaultdict(list)

    for engine_type in (1, 2):
        for stage_idx, terrain in enumerate(STAGES):
            for trial in range(n_trials):
                rng = np.random.default_rng(10000 * engine_type + 100 * stage_idx + trial)
                torus_eta = 3 * np.pi / 8 if terrain["loop"] == "base" else np.pi / 8
                engine = GeometricEngine(engine_type=engine_type)
                state = engine.init_state(
                    eta=torus_eta,
                    theta1=float(rng.uniform(0, 2 * np.pi)),
                    theta2=float(rng.uniform(0, 2 * np.pi)),
                    rng=np.random.default_rng(20000 * engine_type + 100 * stage_idx + trial),
                )
                history_len_before = len(state.history)
                controls = StageControls(
                    piston=piston,
                    lever=True,
                    torus=torus_eta,
                    spinor="both",
                )
                state_after = engine.step(state, stage_idx=stage_idx, controls=controls)
                macro_history = state_after.history[history_len_before:]

                prev_rho_L = state.rho_L.copy()
                prev_rho_R = state.rho_R.copy()
                for entry in macro_history:
                    step_norm_L = rho_step_norm(prev_rho_L, entry["rho_L"])
                    step_norm_R = rho_step_norm(prev_rho_R, entry["rho_R"])
                    step_norm = 0.5 * (step_norm_L + step_norm_R)
                    impedance_z = 1.0 / max(step_norm, EPS)
                    position = loop_position(terrain)
                    record = {
                        "engine_type": engine_type,
                        "terrain": terrain["name"],
                        "loop": terrain["loop"],
                        "loop_position": position,
                        "operator": entry["op_name"],
                        "trial": trial,
                        "step_norm_L": step_norm_L,
                        "step_norm_R": step_norm_R,
                        "step_norm_avg": step_norm,
                        "impedance_z": impedance_z,
                    }
                    records.append(record)
                    grouped[(engine_type, position)].append(impedance_z)
                    grouped[("all", position)].append(impedance_z)
                    prev_rho_L = entry["rho_L"]
                    prev_rho_R = entry["rho_R"]

    summary = {}
    for key, values in grouped.items():
        label = f"type_{key[0]}_{key[1]}" if key[0] != "all" else f"all_{key[1]}"
        summary[label] = {
            "n": len(values),
            "mean_z": float(np.mean(values)),
            "median_z": float(np.median(values)),
            "min_z": float(np.min(values)),
            "max_z": float(np.max(values)),
        }

    verdicts = {}
    for engine_type in (1, 2):
        outer_mean = summary[f"type_{engine_type}_outer"]["mean_z"]
        inner_mean = summary[f"type_{engine_type}_inner"]["mean_z"]
        verdicts[f"type_{engine_type}_outer_lt_inner"] = bool(outer_mean < inner_mean)
    verdicts["all_outer_lt_inner"] = bool(
        summary["all_outer"]["mean_z"] < summary["all_inner"]["mean_z"]
    )
    verdicts["same_order_for_both_types"] = bool(
        verdicts["type_1_outer_lt_inner"] and verdicts["type_2_outer_lt_inner"]
    )

    token = EvidenceToken(
        token_id="E_SIM_CONTRACT_S2_IMPEDANCE_BASELINE"
        if verdicts["same_order_for_both_types"]
        else "",
        sim_spec_id="S_SIM_CONTRACT_S2_IMPEDANCE_Z_V1",
        status="PASS" if verdicts["same_order_for_both_types"] else "KILL",
        measured_value=float(summary["all_inner"]["mean_z"] - summary["all_outer"]["mean_z"]),
        kill_reason=None if verdicts["same_order_for_both_types"] else "OUTER_INNER_IMPEDANCE_ORDER_NOT_OBSERVED",
    )

    return {
        "schema": "SIM_EVIDENCE_v1",
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "sim_name": "contract_s2_impedance_z",
        "status": "current_engine_baseline_only",
        "contract_target": {
            "formula": "Z = 1 / ||d rho / dt||",
            "expected_order": "outer < inner for both types",
        },
        "measurement_notes": [
            "Uses current engine_core step sequence without modifying semantics.",
            "Treats base terrains as outer-loop telemetry and fiber terrains as inner-loop telemetry.",
            "Computes ||d rho / dt|| from successive Frobenius norms of rho_L and rho_R and averages them.",
        ],
        "summary": summary,
        "verdicts": verdicts,
        "sample_size": len(records),
        "sample_records_preview": records[:24],
        "evidence_ledger": [token.__dict__],
    }


def main() -> None:
    result = run_probe()
    base = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, RESULT_NAME)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Wrote {out_path}")
    print(json.dumps(result["verdicts"], indent=2))


if __name__ == "__main__":
    main()
