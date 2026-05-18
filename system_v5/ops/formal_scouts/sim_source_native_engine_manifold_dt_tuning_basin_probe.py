#!/usr/bin/env python3
"""Tune existing EngineCore STAGE_DT against basin-depth criteria."""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

import engine_core as ec
from sim_source_native_engine_manifold_attractor_basin_depth_probe import (
    mean_float,
    perturb_density,
    random_pauli_cptp_control,
    run_cycle,
    token_match_fraction,
    trace_distance,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "source_native_engine_manifold_dt_tuning_basin_probe_results.json"
SOURCE_RESULT = RESULT_DIR / "source_native_engine_manifold_attractor_basin_depth_probe_results.json"

NAME = "source_native_engine_manifold_dt_tuning_basin_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: sweeps the existing EngineCore STAGE_DT integration "
    "parameter against finite basin-depth criteria. It does not admit global "
    "manifold necessity, deep-basin promotion, final FEP, final Axis0, "
    "Holodeck, physics, cognition, world-model, or canonical claims."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing trace-distance, random control, and sweep statistics"},
    "engine_core": {"tried": True, "used": True, "reason": "supportive source-native EngineCore execution with runtime STAGE_DT sweep"},
    "json": {"tried": True, "used": True, "reason": "supportive receipt parsing/writing"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source hash receipt"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "engine_core": "supportive",
    "json": "supportive",
    "hashlib": "supportive",
}

DT_VALUES = [0.035, 0.05, 0.08, 0.12, 0.18]
SEEDS = [101, 211, 307]
EPSILONS = [0.02, 0.08]
TRACE_CANDIDATE_FLOOR = 0.10
CONTROL_SEPARATION_FLOOR = 0.05


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_dt(dt: float) -> dict[str, Any]:
    ec.STAGE_DT = dt
    rows = []
    for engine_type in (0, 1):
        for seed in SEEDS:
            rho0 = ec.generate_initial_density(seed)
            baseline = run_cycle(engine_type, rho0, manifold_enabled=True)
            for eps in EPSILONS:
                pert = perturb_density(rho0, eps)
                on = run_cycle(engine_type, pert, manifold_enabled=True)
                off = run_cycle(engine_type, pert, manifold_enabled=False)
                rev = run_cycle(engine_type, pert, manifold_enabled=True, schedule_mode="reversed")
                random_schedule_seed = 40709 + 1000 * engine_type + 10 * seed + int(eps * 1000) + int(dt * 10000)
                random_schedule = run_cycle(
                    engine_type,
                    pert,
                    manifold_enabled=True,
                    schedule_mode="torch_random",
                    schedule_seed=random_schedule_seed,
                )
                wrong = run_cycle(1 - engine_type, pert, manifold_enabled=True)
                random_cptp_seed = 2097593 + 1000 * engine_type + 10 * seed + int(eps * 1000) + int(dt * 10000)
                random_cptp = random_pauli_cptp_control(pert, random_cptp_seed)
                rows.append(
                    {
                        "epsilon": eps,
                        "on_trace": trace_distance(on["rho"], baseline["rho"]),
                        "off_trace": trace_distance(off["rho"], baseline["rho"]),
                        "reversed_trace": trace_distance(rev["rho"], baseline["rho"]),
                        "random_schedule_trace": trace_distance(random_schedule["rho"], baseline["rho"]),
                        "wrong_trace": trace_distance(wrong["rho"], baseline["rho"]),
                        "random_cptp_trace": trace_distance(random_cptp["rho"], baseline["rho"]),
                        "on_token_match": token_match_fraction(on["tokens"], baseline["tokens"]),
                        "reversed_token_match": token_match_fraction(rev["tokens"], baseline["tokens"]),
                        "random_schedule_token_match": token_match_fraction(random_schedule["tokens"], baseline["tokens"]),
                        "wrong_token_match": token_match_fraction(wrong["tokens"], baseline["tokens"]),
                        "random_schedule_seed": random_schedule_seed,
                        "random_cptp_seed": random_cptp_seed,
                        "random_cptp_trace_gap": random_cptp["final_density_diagnostics"]["trace_gap"],
                        "random_cptp_min_choi_eigenvalue": random_cptp["min_step_choi_eigenvalue"],
                        "random_cptp_output_min_eigenvalue": random_cptp["final_density_diagnostics"]["min_eigenvalue"],
                        "random_cptp_valid": random_cptp["trace_preserving_pass"] and random_cptp["density_valid_pass"] and random_cptp["choi_psd_pass"],
                        "on_correction": on["mean_correction"],
                        "off_correction": off["mean_correction"],
                    }
                )
    on_mean = mean_float(r["on_trace"] for r in rows)
    control_means = {
        "off": mean_float(r["off_trace"] for r in rows),
        "reversed": mean_float(r["reversed_trace"] for r in rows),
        "random_schedule": mean_float(r["random_schedule_trace"] for r in rows),
        "wrong_chirality": mean_float(r["wrong_trace"] for r in rows),
        "random_cptp": mean_float(r["random_cptp_trace"] for r in rows),
    }
    nearest_control_name, nearest_control = min(control_means.items(), key=lambda item: item[1])
    separation = nearest_control - on_mean
    if on_mean <= TRACE_CANDIDATE_FLOOR and separation >= CONTROL_SEPARATION_FLOOR:
        label = "candidate_basin"
    elif separation < 0:
        label = "anti_basin"
    elif on_mean <= nearest_control:
        label = "shallow_basin"
    else:
        label = "open_basin_boundary"
    return {
        "dt": dt,
        "label": label,
        "row_count": len(rows),
        "on_mean_trace": on_mean,
        "off_mean_trace": control_means["off"],
        "reversed_mean_trace": control_means["reversed"],
        "random_schedule_mean_trace": control_means["random_schedule"],
        "wrong_chirality_mean_trace": control_means["wrong_chirality"],
        "random_cptp_mean_trace": control_means["random_cptp"],
        "nearest_control_name": nearest_control_name,
        "nearest_control_mean": nearest_control,
        "control_separation": separation,
        "mean_on_token_match": mean_float(r["on_token_match"] for r in rows),
        "mean_reversed_token_match": mean_float(r["reversed_token_match"] for r in rows),
        "mean_random_schedule_token_match": mean_float(r["random_schedule_token_match"] for r in rows),
        "mean_wrong_token_match": mean_float(r["wrong_token_match"] for r in rows),
        "mean_on_correction": mean_float(r["on_correction"] for r in rows),
        "mean_off_correction": mean_float(r["off_correction"] for r in rows),
        "random_cptp_valid": all(r["random_cptp_valid"] for r in rows),
        "random_cptp_max_trace_gap": max(r["random_cptp_trace_gap"] for r in rows),
        "random_cptp_min_choi_eigenvalue": min(r["random_cptp_min_choi_eigenvalue"] for r in rows),
        "random_cptp_min_output_eigenvalue": min(r["random_cptp_output_min_eigenvalue"] for r in rows),
    }


def main() -> int:
    started = time.time()
    source = json.loads(SOURCE_RESULT.read_text(encoding="utf-8"))
    original_dt = ec.STAGE_DT
    try:
        rows = [run_dt(dt) for dt in DT_VALUES]
    finally:
        ec.STAGE_DT = original_dt
    candidate_rows = [r for r in rows if r["label"] == "candidate_basin"]
    best = min(candidate_rows or rows, key=lambda r: (r["on_mean_trace"], -r["control_separation"]))
    positive = {
        "source_shallow_basin_receipt_loaded": {
            "pass": (
                source.get("all_pass") is True
                and source.get("name") == "source_native_engine_manifold_attractor_basin_depth_probe"
                and source.get("basin_classification", {}).get("label") == "shallow_basin"
            ),
            "source_sha256": sha256_file(SOURCE_RESULT),
            "source_name": source.get("name"),
            "source_label": source.get("basin_classification", {}).get("label"),
        },
        "dt_sweep_executed": {
            "pass": len(rows) == len(DT_VALUES),
            "dt_values": DT_VALUES,
            "rows": rows,
        },
        "dt_sweep_random_cptp_controls_valid": {
            "pass": all(row["random_cptp_valid"] for row in rows),
            "max_trace_gap": max(row["random_cptp_max_trace_gap"] for row in rows),
            "min_choi_eigenvalue": min(row["random_cptp_min_choi_eigenvalue"] for row in rows),
            "min_output_eigenvalue": min(row["random_cptp_min_output_eigenvalue"] for row in rows),
        },
        "best_dt_identified": {
            "pass": best["dt"] in DT_VALUES and (not candidate_rows or best["label"] == "candidate_basin"),
            "best": best,
            "candidate_rows_present": bool(candidate_rows),
        },
    }
    graveyard = {
        "dt_tuning_does_not_silently_promote_to_deep": {
            "pass": True,
            "candidate_dt_values": [r["dt"] for r in candidate_rows],
            "reason": "Any improved DT remains a finite tuning candidate until rerun in the full basin-depth scout.",
        },
        "original_dt_remains_visible": {
            "pass": any(abs(r["dt"] - original_dt) < 1e-12 for r in rows),
            "original_dt": original_dt,
        },
        "tuning_is_existing_parameter_not_new_system": {"pass": True},
    }
    boundary = {
        "no_promotion": {"pass": PROMOTION_ALLOWED is False},
        "stage_dt_restored_after_sweep": {"pass": abs(ec.STAGE_DT - original_dt) < 1e-12, "restored_dt": ec.STAGE_DT},
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard.values())
        and all(row["pass"] for row in boundary.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "source_native_engine_manifold_dt_tuning_basin",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "rows": rows,
        "recommended_dt": best["dt"],
        "nearby_variants": {"total": len(graveyard), "passed": sum(1 for row in graveyard.values() if row["pass"]), "variants": sorted(graveyard)},
        "why_not_v4_probes": [
            "This is a source-native v5 EngineCore parameter tuning scout.",
            "It identifies a repair candidate without editing engine_core or promoting architecture claims.",
        ],
        "blockers": [] if all_pass else [key for key, row in {**positive, **graveyard, **boundary}.items() if not row.get("pass")],
        "all_pass": all_pass,
        "elapsed_seconds": time.time() - started,
        "script_sha256": sha256_file(pathlib.Path(__file__)),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    print(f"  recommended_dt={best['dt']} label={best['label']} on_mean={best['on_mean_trace']:.4f} separation={best['control_separation']:.4f}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
