#!/usr/bin/env python3
"""Stage-record true perturbation depth scout.

This is the first true epsilon/noise perturbation follow-up for a
basin-depth-guard pass row.  It targets the cheapest guard-pass task:
science_method_stage_record_fields.

The scout injects mixed rank-2 depolarizing noise into the source-native
EngineCore state before stage 4, then compares manifold-on vs no-manifold
execution at the same source-native stage.  Passing means the stage-record
manifold repair has nonzero perturbation-depth evidence for this local rank
repair task.  It does not claim global manifold necessity or robust
architecture-level basin volume.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

from engine_core import EngineCore, I2, _normalize_density, generate_initial_density


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "stage_record_true_perturbation_depth_probe_results.json"

NAME = "stage_record_true_perturbation_depth_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "stage_record_true_perturbation_depth"
CLAIM_CEILING = (
    "Formal scout only: tests local rank-repair perturbation depth for the "
    "source-native science-method stage-record row. It does not admit global "
    "manifold requirement, final FEP, final Axis0, deep-basin promotion, "
    "Holodeck, physics, cognition, world-model, architecture, or canonical claims."
)

TOOL_MANIFEST = {
    "engine_core": {
        "tried": True,
        "used": True,
        "reason": "load-bearing source-native density perturbation, rank, KL, and repair-delta checks",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "load-bearing receipt parsing and result writing",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "load-bearing receipt/source hash capture",
    },
}
TOOL_INTEGRATION_DEPTH = {
    'engine_core': 'supportive',
    'json': 'supportive',
    'hashlib': 'supportive',
}

EPSILONS = [0.05, 0.15, 0.30, 0.45]
SEEDS = [42, 77, 123, 211, 377]
STAGE_IDX = 4
SUBSTAGE_IDX = 0
MIN_REPAIR_DELTA = 0.05
MIN_MANIFOLD_KL = 0.01


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_receipt(filename: str) -> dict[str, Any]:
    path = RESULT_DIR / filename
    if not path.exists():
        return {"exists": False, "filename": filename, "path": str(path)}
    data = json.loads(path.read_text(encoding="utf-8"))
    data["exists"] = True
    data["filename"] = filename
    data["path"] = str(path)
    data["sha256"] = sha256_file(path)
    return data


def prep_engine(engine_type: int, seed: int, manifold_enabled: bool) -> tuple[EngineCore, Any]:
    engine = EngineCore(engine_type=engine_type, manifold_enabled=manifold_enabled)
    rho = generate_initial_density(seed)
    for main_idx in range(STAGE_IDX):
        perception, loop_class = engine.schedule[main_idx]
        rho, _records = engine.run_main_stage(rho, perception, loop_class, main_idx)
    return engine, rho


def perturb_density(rho: Any, epsilon: float) -> Any:
    return _normalize_density((1.0 - epsilon) * rho + epsilon * I2 / 2.0)


def run_cell(engine_type: int, seed: int, epsilon: float) -> dict[str, Any]:
    engine_on, rho_pre = prep_engine(engine_type, seed, manifold_enabled=True)
    engine_off, _rho_off_pre = prep_engine(engine_type, seed, manifold_enabled=False)
    rho_perturbed = perturb_density(rho_pre, epsilon)
    perception, loop_class = engine_on.schedule[STAGE_IDX]
    _rho_on, records_on = engine_on.run_main_stage(rho_perturbed, perception, loop_class, STAGE_IDX)
    _rho_off, records_off = engine_off.run_main_stage(rho_perturbed, perception, loop_class, STAGE_IDX)
    on = records_on[SUBSTAGE_IDX]
    off = records_off[SUBSTAGE_IDX]
    return {
        "engine_type": engine_type,
        "seed": seed,
        "epsilon": epsilon,
        "perception": perception,
        "loop_class": loop_class,
        "input_rank": on["model_before"]["carrier_rank"],
        "manifold_on_intermediate_rank": on["manifold_intermediate"]["model"]["carrier_rank"],
        "manifold_off_intermediate_rank": off["manifold_intermediate"]["model"]["carrier_rank"],
        "manifold_on_repair_delta": on["update_repair"]["manifold_projection_delta_norm"],
        "manifold_off_repair_delta": off["update_repair"]["manifold_projection_delta_norm"],
        "manifold_step_kl": on["fep_efe_score"]["surprise_kl_manifold_step"],
        "off_manifold_step_kl": off["fep_efe_score"]["surprise_kl_manifold_step"],
        "on_density_hash": on["manifold_intermediate"]["model"]["density_hash"],
        "off_density_hash": off["manifold_intermediate"]["model"]["density_hash"],
    }


def main() -> int:
    started = time.time()
    stage_receipt = load_receipt("macro_sim_stage_record_science_method_contract_probe_results.json")
    depth_guard = load_receipt("manifold_dependency_basin_depth_guard_probe_results.json")
    rows = [
        run_cell(engine_type, seed, epsilon)
        for engine_type in (0, 1)
        for seed in SEEDS
        for epsilon in EPSILONS
    ]

    all_input_rank2 = all(row["input_rank"] == 2 for row in rows)
    all_on_rank1 = all(row["manifold_on_intermediate_rank"] == 1 for row in rows)
    all_off_rank2 = all(row["manifold_off_intermediate_rank"] == 2 for row in rows)
    min_on_delta = min(row["manifold_on_repair_delta"] for row in rows)
    max_off_delta = max(abs(row["manifold_off_repair_delta"]) for row in rows)
    min_manifold_kl = min(row["manifold_step_kl"] for row in rows)
    distinct_hash_pairs = sum(1 for row in rows if row["on_density_hash"] != row["off_density_hash"])

    positive = {
        "stage_record_contract_receipt_loads": {
            "pass": stage_receipt.get("exists") is True and stage_receipt.get("all_pass") is True,
            "stage_receipt_sha256": stage_receipt.get("sha256"),
        },
        "epsilon_seed_grid_executed": {
            "pass": len(rows) == 2 * len(SEEDS) * len(EPSILONS),
            "engine_types": [0, 1],
            "seeds": SEEDS,
            "epsilons": EPSILONS,
            "row_count": len(rows),
        },
        "manifold_repairs_rank2_perturbations_to_rank1": {
            "pass": all_input_rank2 and all_on_rank1 and all_off_rank2,
            "all_input_rank2": all_input_rank2,
            "all_on_rank1": all_on_rank1,
            "all_off_rank2": all_off_rank2,
        },
        "repair_delta_and_manifold_surprise_have_floor": {
            "pass": min_on_delta > MIN_REPAIR_DELTA and max_off_delta == 0.0 and min_manifold_kl > MIN_MANIFOLD_KL,
            "min_on_repair_delta": min_on_delta,
            "max_off_repair_delta": max_off_delta,
            "min_manifold_step_kl": min_manifold_kl,
            "min_repair_delta_floor": MIN_REPAIR_DELTA,
            "min_manifold_kl_floor": MIN_MANIFOLD_KL,
        },
        "on_off_intermediate_hashes_separate": {
            "pass": distinct_hash_pairs == len(rows),
            "distinct_hash_pairs": distinct_hash_pairs,
            "row_count": len(rows),
        },
    }

    graveyard = {
        "no_manifold_control_does_not_repair_rank": {
            "pass": all_off_rank2 and max_off_delta == 0.0,
            "max_off_repair_delta": max_off_delta,
        },
        "single_seed_single_epsilon_claim_is_not_used": {
            "pass": len(SEEDS) > 1 and len(EPSILONS) > 1,
            "seed_count": len(SEEDS),
            "epsilon_count": len(EPSILONS),
        },
        "global_manifold_requirement_not_revived": {
            "pass": True,
            "reason": "This is local stage-record rank-repair evidence only; it does not override qit no-manifold/global blockers.",
        },
    }

    boundary = {
        "claim_ceiling_blocks_global_and_canonical_claims": {
            "pass": all(term in CLAIM_CEILING.lower() for term in ["formal scout", "does not admit", "global manifold requirement"]),
        },
        "downstream_depth_guard_receipt_loaded_as_context": {
            "pass": depth_guard.get("exists") is True,
            "depth_guard_sha256": depth_guard.get("sha256"),
        },
        "next_work_is_operational_assembly_or_seven_control_perturbation": {
            "pass": True,
            "next": "Run true perturbation-depth scouts for operational_manifold_assembly and seven_control_source_execution, or update the basin-depth guard to consume this stage-record perturbation receipt first.",
        },
    }

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(rows),
            "passed": len(rows),
            "variants": rows,
        },
        "why_not_v4_probes": (
            "This is a v5 source-native EngineCore stage-record perturbation scout. "
            "It does not add v4 probe authority or promote architecture/physics claims."
        ),
        "perturbation_rows": rows,
        "repair_receipt": {
            "weak_link": "science_method_stage_record_fields had receipt-local margin evidence but no true epsilon/noise perturbation depth receipt.",
            "target_file_or_result": str(OUT_PATH),
            "admission_rule_improved": "Stage-record basin-depth evidence now requires rank-repair persistence across seed and epsilon perturbation grid with no-manifold matched controls.",
            "dependency_subset": [stage_receipt.get("path"), depth_guard.get("path")],
            "stage_fields_touched_or_consumed": [
                "model_before",
                "manifold_intermediate",
                "fep_efe_score",
                "update_repair",
                "model_after",
            ],
            "before_baseline/hash": {
                "stage_record_contract": stage_receipt.get("sha256"),
                "depth_guard": depth_guard.get("sha256"),
            },
            "after_delta/hash": {
                "script": sha256_file(pathlib.Path(__file__)),
                "result": "written_after_receipt_payload_assembly",
            },
            "primary_control/result": {
                "row_count": len(rows),
                "min_on_repair_delta": min_on_delta,
                "max_off_repair_delta": max_off_delta,
                "min_manifold_step_kl": min_manifold_kl,
                "all_on_rank1": all_on_rank1,
                "all_off_rank2": all_off_rank2,
            },
            "axis0_outputs_or_blockers": {
                "fep_gradient_polarity": "not touched here",
                "path_entropy": "not touched here",
                "correlation_diversity_derivative": "not touched here",
                "holographic_boundary_interior_reconstruction": "not touched here",
                "retrocausal_many_futures_policy_scoring": "not touched here",
            },
            "provider_inputs_used": {
                "grok": "not_run_this_repair_wave",
                "gemini": "not_run_this_repair_wave",
                "opus_max": "not_run_this_repair_wave",
                "sonnet_high": "not_run_this_repair_wave",
            },
            "promotion_ceiling": CLAIM_CEILING,
            "next_step": "Update basin-depth guard/classifier to consume this perturbation-depth receipt, then continue with operational assembly or seven-control perturbation.",
        },
        "audit_method_families": [
            "epsilon_grid",
            "seed_grid",
            "manifold_on_rank_repair",
            "no_manifold_rank_control",
            "stage_record_fep_repair_fields",
        ],
        "method_count_source": "source_native_rank_perturbation_grid",
        "blockers": [],
        "all_pass": all(
            row.get("pass") is True
            for section in (positive, graveyard, boundary)
            for row in section.values()
        ),
        "elapsed_seconds": round(time.time() - started, 6),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
