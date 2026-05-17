#!/usr/bin/env python3
"""Seven-control source-execution true perturbation-depth scout.

This is a true epsilon perturbation follow-up for the
seven_control_source_execution row in the basin-depth guard.  It consumes the
existing source-native seven-control 64-microstep receipt, injects bounded
density perturbations at each stage-entry source state, then reruns nominal and
seven matched collapse controls under the same perturbation schedule.

Formal scout only.  It proves a local, task-specific perturbation-depth check
for the existing seven-control row; it does not admit global manifold
necessity, robust architecture-level basin volume, final FEP, final Axis0,
Holodeck, physics, cognition, world-model, or canonical claims.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import math
import pathlib
import time
from typing import Any

import numpy as np


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "seven_control_source_execution_true_perturbation_depth_probe_results.json"

NAME = "seven_control_source_execution_true_perturbation_depth_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "seven_control_source_execution_true_perturbation_depth"
CLAIM_CEILING = (
    "Formal scout only: tests whether the existing seven-control source "
    "execution row keeps its seven matched collapse-control separations under "
    "bounded perturbed stage-entry density states. It does not admit global "
    "manifold requirement, robust architecture-level basin volume, final FEP, "
    "final Axis0, Holodeck, physics, cognition, world-model, architecture, or "
    "canonical claims."
)

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing stage-entry density perturbations and trajectory gap checks",
    },
    "scipy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing through imported seven-control source execution updates",
    },
    "gudhi": {
        "tried": True,
        "used": False,
        "reason": "available through imported seven-control source module, but not receipt-local evidence in this perturbation-depth scout",
    },
    "networkx": {
        "tried": True,
        "used": False,
        "reason": "available through imported seven-control source module, but not receipt-local evidence in this perturbation-depth scout",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "load-bearing receipt parsing and result writing",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "load-bearing source/result hash capture",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "scipy": "load_bearing",
    "gudhi": "None",
    "networkx": "None",
    "json": "load_bearing",
    "hashlib": "load_bearing",
}

SEEDS = [1001, 2003]
EPSILONS = [0.01, 0.03, 0.05]
COLLAPSE_MODES = [
    "collapse_feedback_sign",
    "collapse_stage_bit_one",
    "collapse_stage_bit_two",
    "collapse_loop_placement",
    "collapse_traversal_order",
    "collapse_excitation_level",
    "collapse_operator_sign",
]
MIN_DYNAMIC_GAP = 0.50
MIN_FULL_SIGNATURE_GAP = 0.50
MIN_PERTURBATION_NORM = 0.001
MAX_PERTURBATION_NORM = 0.15


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


def receipt_all_pass(data: dict[str, Any]) -> bool:
    if data.get("all_pass") is True:
        return True
    summary = data.get("summary")
    return bool(isinstance(summary, dict) and summary.get("all_pass") is True)


def random_pure_density(rng: np.random.Generator) -> np.ndarray:
    vector = rng.normal(size=2) + 1j * rng.normal(size=2)
    vector = vector / max(float(np.linalg.norm(vector)), 1e-15)
    return np.outer(vector, vector.conj())


def perturb_density(seven: Any, rho: np.ndarray, rng: np.random.Generator, epsilon: float) -> tuple[np.ndarray, float]:
    perturber = random_pure_density(rng)
    perturbed = seven.normalize_density((1.0 - epsilon) * rho + epsilon * perturber)
    return perturbed, float(np.linalg.norm(perturbed - rho))


def run_perturbed(seven: Any, *, mode: str, seed: int, epsilon: float) -> tuple[list[dict[str, Any]], list[float]]:
    rows: list[dict[str, Any]] = []
    perturbation_norms: list[float] = []
    rng = np.random.default_rng(seed)
    for sheet in ["left_chiral_operating_space", "right_chiral_operating_space"]:
        geom = {"metric_scale": 1.0, "connection": 0.36 if sheet.startswith("left") else -0.36, "twist": 0.07}
        feedback_sign = +1 if sheet.startswith("left") else -1
        if mode == "collapse_feedback_sign":
            feedback_sign = +1
        stage_index = 0
        for traversal_name, raw_stages in seven.TRAVERSALS.items():
            traversal, stages = seven.traversal_for_mode(traversal_name, raw_stages, mode)
            loop = seven.loop_for_mode(traversal, mode)
            for raw_stage in stages:
                stage = seven.stage_for_mode(raw_stage, mode)
                stage_bits = seven.STAGE_BITS[stage]
                rho = seven.SOURCE.loop_density(loop, (stage_index + 1) * (2 * math.pi / 9))
                rho, perturbation_norm = perturb_density(seven, rho, rng, epsilon)
                perturbation_norms.append(perturbation_norm)
                spec = seven.stage_spec(sheet, stage)
                for substage_index, substage in enumerate(seven.SUBSTAGES):
                    family_preview, sign_preview = seven.op_pair(
                        stage_index,
                        substage_index,
                        mode == "collapse_operator_sign",
                    )
                    heat_preview = seven.excitation_level(stage_index, substage_index, mode)
                    geom, grad_norm = seven.entropy_feedback_update(
                        rho,
                        geom,
                        feedback_sign,
                        float(spec["rate"]),
                        freeze=mode == "collapse_feedback_sign",
                        stage_bits=stage_bits,
                        excitation=heat_preview,
                        operator_sign=sign_preview,
                    )
                    rho, (family, op_sign), heat = seven.apply_step(
                        rho,
                        sheet=sheet,
                        stage=stage,
                        loop=loop,
                        stage_index=stage_index,
                        substage_index=substage_index,
                        geom=geom,
                        mode=mode,
                    )
                    rows.append(
                        {
                            "sheet": sheet,
                            "stage_index": stage_index,
                            "substage_index": substage_index,
                            "traversal": traversal,
                            "loop": loop,
                            "stage": stage,
                            "stage_bit_one": stage_bits[0],
                            "stage_bit_two": stage_bits[1],
                            "substage": substage,
                            "operator_family": family,
                            "operator_sign": op_sign,
                            "excitation_level": heat,
                            "feedback_sign": feedback_sign,
                            "stage_law": spec["terrain_law"],
                            "entropy": seven.entropy(rho),
                            "readout": seven.readout(rho),
                            "coherence": float(abs(rho[0, 1]) + abs(rho[1, 0])),
                            "metric_scale": geom["metric_scale"],
                            "connection": geom["connection"],
                            "twist": geom["twist"],
                            "gradient_norm": grad_norm,
                            "valid_density": seven.valid_density(rho),
                        }
                    )
                stage_index += 1
    return rows, perturbation_norms


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(val) for key, val in value.items()}
    if isinstance(value, list):
        return [as_jsonable(val) for val in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if hasattr(value, "item"):
        return value.item()
    return value


def main() -> int:
    started = time.time()
    seven = importlib.import_module("sim_source_chiral_seven_control_sixty_four_microstep_execution_probe")
    source = load_receipt("source_chiral_seven_control_sixty_four_microstep_execution_probe_results.json")
    depth_guard = load_receipt("manifold_dependency_basin_depth_guard_probe_results.json")

    source_rows = (
        source.get("positive", {})
        .get("every_control_is_load_bearing_under_collapse", {})
        .get("effect_summary", {})
        .get("rows", {})
    )
    if set(source_rows) != set(COLLAPSE_MODES):
        raise ValueError("source seven-control receipt does not expose all seven collapse modes")

    rows = []
    cell_rows = []
    for seed in SEEDS:
        for epsilon in EPSILONS:
            nominal, perturbation_norms = run_perturbed(seven, mode="nominal", seed=seed, epsilon=epsilon)
            cell_valid = len(nominal) == 64 and all(row["valid_density"] for row in nominal)
            cell_rows.append(
                {
                    "seed": seed,
                    "epsilon": epsilon,
                    "microstep_count": len(nominal),
                    "all_valid_density": cell_valid,
                    "min_perturbation_norm": min(perturbation_norms),
                    "max_perturbation_norm": max(perturbation_norms),
                    "perturbation_norm_floor": MIN_PERTURBATION_NORM,
                    "perturbation_norm_ceiling": MAX_PERTURBATION_NORM,
                    "perturbation_norm_pass": (
                        min(perturbation_norms) > MIN_PERTURBATION_NORM
                        and max(perturbation_norms) < MAX_PERTURBATION_NORM
                    ),
                }
            )
            for mode in COLLAPSE_MODES:
                control, _control_norms = run_perturbed(seven, mode=mode, seed=seed, epsilon=epsilon)
                dynamic_gap = seven.trajectory_gap(nominal, control)
                full_gap = seven.full_signature_gap(nominal, control)
                rows.append(
                    {
                        "seed": seed,
                        "epsilon": epsilon,
                        "mode": mode,
                        "source_dynamic_gap": float(source_rows[mode]["dynamic_gap"]),
                        "dynamic_gap": dynamic_gap,
                        "full_signature_gap": full_gap,
                        "dynamic_gap_pass": dynamic_gap > MIN_DYNAMIC_GAP,
                        "full_signature_gap_pass": full_gap > MIN_FULL_SIGNATURE_GAP,
                        "control_valid_density": len(control) == 64 and all(row["valid_density"] for row in control),
                    }
                )

    min_dynamic_gap = min(row["dynamic_gap"] for row in rows)
    min_full_signature_gap = min(row["full_signature_gap"] for row in rows)
    modes_seen = sorted({row["mode"] for row in rows})
    dynamic_passed = sum(row["dynamic_gap_pass"] for row in rows)
    full_passed = sum(row["full_signature_gap_pass"] for row in rows)

    positive = {
        "source_seven_control_receipt_loads": {
            "pass": source.get("exists") is True and receipt_all_pass(source),
            "source_sha256": source.get("sha256"),
        },
        "perturbed_seven_control_grid_executes": {
            "pass": len(cell_rows) == len(SEEDS) * len(EPSILONS)
            and all(row["all_valid_density"] and row["perturbation_norm_pass"] for row in cell_rows),
            "seeds": SEEDS,
            "epsilons": EPSILONS,
            "cell_count": len(cell_rows),
            "cell_rows": cell_rows,
        },
        "all_seven_collapse_controls_remain_populated_under_perturbation": {
            "pass": modes_seen == sorted(COLLAPSE_MODES)
            and len(rows) == len(SEEDS) * len(EPSILONS) * len(COLLAPSE_MODES),
            "modes_seen": modes_seen,
            "row_count": len(rows),
        },
        "collapse_dynamic_gaps_survive_perturbations": {
            "pass": all(row["dynamic_gap_pass"] and row["control_valid_density"] for row in rows),
            "min_dynamic_gap": min_dynamic_gap,
            "min_dynamic_gap_floor": MIN_DYNAMIC_GAP,
            "passed": dynamic_passed,
            "total": len(rows),
        },
        "collapse_full_signature_gaps_survive_perturbations": {
            "pass": all(row["full_signature_gap_pass"] for row in rows),
            "min_full_signature_gap": min_full_signature_gap,
            "min_full_signature_gap_floor": MIN_FULL_SIGNATURE_GAP,
            "passed": full_passed,
            "total": len(rows),
        },
    }

    graveyard = {
        "unperturbed_only_seven_control_depth_claim_rejected": {
            "pass": len(cell_rows) > 1 and all(row["perturbation_norm_pass"] for row in cell_rows),
            "reason": "This scout reruns perturbed stage-entry density states instead of relying on the original unperturbed seven-control receipt.",
        },
        "single_control_survival_not_enough": {
            "pass": modes_seen == sorted(COLLAPSE_MODES)
            and len(rows) == len(SEEDS) * len(EPSILONS) * len(COLLAPSE_MODES),
            "reason": "Every one of the seven collapse controls must survive the perturbation grid.",
        },
        "global_basin_volume_not_claimed": {
            "pass": True,
            "reason": "This is a bounded local seed/epsilon perturbation-depth scout, not a basin-volume estimate.",
        },
    }

    boundary = {
        "claim_ceiling_blocks_global_and_canonical_claims": {
            "pass": all(
                term in CLAIM_CEILING.lower()
                for term in ["formal scout", "does not admit", "global manifold requirement"]
            ),
        },
        "downstream_depth_guard_loaded_as_context": {
            "pass": depth_guard.get("exists") is True and receipt_all_pass(depth_guard),
            "depth_guard_sha256": depth_guard.get("sha256"),
            "depth_guard_passes": receipt_all_pass(depth_guard),
        },
        "source_control_gaps_are_consumed_not_recomputed_as_authority": {
            "pass": set(source_rows) == set(COLLAPSE_MODES),
            "source_modes": sorted(source_rows),
        },
        "single_engine_perturbation_grid_is_not_method_multiplicity": {
            "pass": True,
            "note": "The seed/epsilon/control grid is one source-engine perturbation method with several facets, not independent method-family convergence.",
        },
        "next_work_is_wider_grid_or_policy_repair": {
            "pass": True,
            "next": "Consume this in the basin-depth guard/classifier, then either widen seven-control perturbation seeds/epsilons or repair the active-policy scoring branch.",
        },
    }

    nearby_passed = sum(
        row["dynamic_gap_pass"] and row["full_signature_gap_pass"] and row["control_valid_density"]
        for row in rows
    )
    sections = (positive, graveyard, boundary)
    blockers = [
        f"{section_name}.{row_name}"
        for section_name, section in (
            ("positive", positive),
            ("graveyard_companions", graveyard),
            ("boundary", boundary),
        )
        for row_name, row in section.items()
        if isinstance(row, dict) and row.get("pass") is not True
    ]
    all_pass = all(
        row.get("pass") is True
        for section in sections
        for row in section.values()
    )

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
            "passed": nearby_passed,
            "variants": rows,
        },
        "why_not_v4_probes": (
            "This is a v5 seven-control perturbation-depth scout. It does not add "
            "v4 probe authority or promote axis/manifold/physics claims."
        ),
        "perturbation_rows": rows,
        "repair_receipt": {
            "weak_link": "seven_control_source_execution had collapse-control margin evidence but no true perturbed-stage-entry density depth receipt.",
            "target_file_or_result": str(OUT_PATH),
            "admission_rule_improved": "Seven-control basin-depth evidence now requires all seven collapse-control gaps to survive a bounded seed/epsilon perturbation grid.",
            "dependency_subset": [source.get("path"), depth_guard.get("path")],
            "stage_fields_touched_or_consumed": [
                "positive.every_control_is_load_bearing_under_collapse",
                "control_effect_summary.rows",
                "source-native stage-entry density states",
            ],
            "before_baseline/hash": {
                "seven_control_source_execution": source.get("sha256"),
                "depth_guard": depth_guard.get("sha256"),
            },
            "after_delta/hash": {
                "script": sha256_file(pathlib.Path(__file__)),
                "result": "written_after_receipt_payload_assembly",
            },
            "primary_control/result": {
                "row_count": len(rows),
                "cell_count": len(cell_rows),
                "min_dynamic_gap": min_dynamic_gap,
                "min_full_signature_gap": min_full_signature_gap,
                "modes_seen": modes_seen,
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
                "codex_native_subagents": "explorer lanes may audit controller work; not embedded as formal evidence",
            },
            "promotion_ceiling": CLAIM_CEILING,
            "next_step": "Update basin-depth guard/classifier to consume this perturbation-depth receipt, then repair or close the active-policy scoring branch.",
        },
        "audit_method_families": [
            "single_source_engine_perturbation_grid",
            "matched_seven_collapse_control_family",
            "dynamic_and_full_signature_gap_readouts",
        ],
        "method_count_source": "single_engine_perturbation_grid_facets_not_independent_methods",
        "blockers": blockers,
        "all_pass": all_pass,
        "elapsed_seconds": round(time.time() - started, 6),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
