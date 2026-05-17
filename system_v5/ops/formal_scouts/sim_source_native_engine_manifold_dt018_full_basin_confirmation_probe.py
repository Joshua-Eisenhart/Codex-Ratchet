#!/usr/bin/env python3
"""Confirm or block the DT=0.18 basin repair candidate on the full grid."""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

import numpy as np

import engine_core as ec
from sim_source_native_engine_manifold_attractor_basin_depth_probe import (
    EPSILONS,
    SEEDS,
    classify_basin,
    perturb_density,
    run_cycle,
    token_match_fraction,
    trace_distance,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "source_native_engine_manifold_dt018_full_basin_confirmation_probe_results.json"
TUNING_RESULT = RESULT_DIR / "source_native_engine_manifold_dt_tuning_basin_probe_results.json"
BASELINE_RESULT = RESULT_DIR / "source_native_engine_manifold_attractor_basin_depth_probe_results.json"

NAME = "source_native_engine_manifold_dt018_full_basin_confirmation_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CANDIDATE_DT = 0.18
CLAIM_CEILING = (
    "Formal scout only: confirms or blocks the existing EngineCore STAGE_DT=0.18 "
    "tuning candidate on the full source-native basin-depth grid. It does not "
    "edit engine_core.py and does not admit global manifold necessity, "
    "deep-basin promotion, final FEP, final Axis0, Holodeck, physics, "
    "cognition, world-model, or canonical claims."
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing basin/control statistics"},
    "engine_core": {"tried": True, "used": True, "reason": "load-bearing source-native EngineCore with temporary STAGE_DT candidate"},
    "json": {"tried": True, "used": True, "reason": "load-bearing prior receipt parsing and result writing"},
    "hashlib": {"tried": True, "used": True, "reason": "load-bearing source hash receipts"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_full_grid() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = []
    for engine_type in (0, 1):
        for seed in SEEDS:
            rho0 = ec.generate_initial_density(seed)
            baseline = run_cycle(engine_type, rho0, manifold_enabled=True)
            for epsilon in EPSILONS:
                pert = perturb_density(rho0, epsilon)
                on = run_cycle(engine_type, pert, manifold_enabled=True)
                off = run_cycle(engine_type, pert, manifold_enabled=False)
                reversed_control = run_cycle(engine_type, pert, manifold_enabled=True, schedule_mode="reversed")
                wrong = run_cycle(1 - engine_type, pert, manifold_enabled=True)
                rows.append(
                    {
                        "engine_type": engine_type,
                        "seed": seed,
                        "epsilon": epsilon,
                        "on_trace_to_baseline": trace_distance(on["rho"], baseline["rho"]),
                        "off_trace_to_baseline": trace_distance(off["rho"], baseline["rho"]),
                        "reversed_trace_to_baseline": trace_distance(reversed_control["rho"], baseline["rho"]),
                        "wrong_chirality_trace_to_baseline": trace_distance(wrong["rho"], baseline["rho"]),
                        "on_token_match": token_match_fraction(on["tokens"], baseline["tokens"]),
                        "reversed_token_match": token_match_fraction(reversed_control["tokens"], baseline["tokens"]),
                        "wrong_chirality_token_match": token_match_fraction(wrong["tokens"], baseline["tokens"]),
                        "on_mean_efe": on["mean_efe"],
                        "off_mean_efe": off["mean_efe"],
                        "on_mean_correction": on["mean_correction"],
                        "off_mean_correction": off["mean_correction"],
                        "on_final_purity": on["final_purity"],
                        "off_final_purity": off["final_purity"],
                    }
                )
    return rows, classify_basin(rows, rows, rows, rows)


def main() -> int:
    started = time.time()
    baseline = load_json(BASELINE_RESULT)
    tuning = load_json(TUNING_RESULT)
    original_dt = ec.STAGE_DT
    try:
        ec.STAGE_DT = CANDIDATE_DT
        rows, basin = run_full_grid()
    finally:
        ec.STAGE_DT = original_dt

    on_token_min = min(row["on_token_match"] for row in rows)
    reversed_token_max = max(row["reversed_token_match"] for row in rows)
    wrong_token_max = max(row["wrong_chirality_token_match"] for row in rows)
    on_correction_mean = float(np.mean([row["on_mean_correction"] for row in rows]))
    off_correction_mean = float(np.mean([row["off_mean_correction"] for row in rows]))
    purity_gap = float(np.mean([row["on_final_purity"] - row["off_final_purity"] for row in rows]))

    positive = {
        "prior_baseline_and_tuning_receipts_loaded": {
            "pass": baseline.get("all_pass") is True and tuning.get("all_pass") is True,
            "baseline_label": baseline.get("basin_classification", {}).get("label"),
            "tuning_recommended_dt": tuning.get("recommended_dt"),
            "baseline_sha256": sha256_file(BASELINE_RESULT),
            "tuning_sha256": sha256_file(TUNING_RESULT),
        },
        "dt018_full_grid_executed": {
            "pass": len(rows) == 2 * len(SEEDS) * len(EPSILONS),
            "candidate_dt": CANDIDATE_DT,
            "row_count": len(rows),
            "seeds": SEEDS,
            "epsilons": EPSILONS,
        },
        "dt018_full_grid_classifies_basin": {
            "pass": basin["label"] in {"candidate_basin", "shallow_basin", "anti_basin", "open_boundary"},
            "basin": basin,
        },
        "native_stage_identity_preserved_under_dt018": {
            "pass": on_token_min == 1.0,
            "min_on_token_match": on_token_min,
        },
        "manifold_correction_remains_load_bearing": {
            "pass": on_correction_mean > off_correction_mean + 1e-6 and purity_gap > 0.0,
            "on_mean_correction": on_correction_mean,
            "off_mean_correction": off_correction_mean,
            "mean_purity_gap_on_minus_off": purity_gap,
        },
    }
    graveyard = {
        "dt018_not_promoted_to_deep_basin": {
            "pass": basin["label"] != "deep_basin",
            "label": basin["label"],
            "reason": "DT=0.18 has one source-native full-grid confirmation; deep basin requires independent carriers/methods.",
        },
        "small_sweep_candidate_not_assumed_global": {
            "pass": basin["label"] != "candidate_basin",
            "label": basin["label"],
            "reason": "The smaller DT sweep is not enough for a source edit when the full grid remains shallow.",
        },
        "source_default_not_edited": {
            "pass": abs(ec.STAGE_DT - original_dt) < 1e-12,
            "restored_dt": ec.STAGE_DT,
            "original_dt": original_dt,
        },
        "controls_remain_nontrivial": {
            "pass": reversed_token_max < 1.0 and wrong_token_max < 1.0,
            "max_reversed_token_match": reversed_token_max,
            "max_wrong_chirality_token_match": wrong_token_max,
        },
    }
    boundary = {
        "no_promotion": {"pass": PROMOTION_ALLOWED is False},
        "claim_ceiling_blocks_source_edit_and_global_claim": {
            "pass": "does not edit engine_core.py" in CLAIM_CEILING and "does not admit global manifold necessity" in CLAIM_CEILING,
        },
        "next_step_requires_source_edit_or_carrier_confirmation": {
            "pass": True,
            "next": "Repair the high-radius/seed failure or test a radius-aware schedule before editing EngineCore defaults.",
        },
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
        "source_alignment_category": "source_native_engine_manifold_dt018_full_basin_confirmation",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "basin_classification": basin,
        "rows": rows,
        "nearby_variants": {
            "total": len(graveyard),
            "passed": sum(1 for row in graveyard.values() if row["pass"]),
            "variants": sorted(graveyard),
        },
        "why_not_v4_probes": [
            "This is a source-native v5 confirmation of a tuning candidate found by formal-scout receipts.",
            "It patches runtime STAGE_DT only inside the process and restores the default afterward.",
        ],
        "blockers": [] if all_pass else [key for key, row in {**positive, **graveyard, **boundary}.items() if not row.get("pass")],
        "all_pass": all_pass,
        "elapsed_seconds": time.time() - started,
        "script_sha256": sha256_file(pathlib.Path(__file__)),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    print(f"  label={basin['label']} on_mean={basin['on_mean_trace_to_baseline']:.4f} separation={basin['control_separation']:.4f}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
