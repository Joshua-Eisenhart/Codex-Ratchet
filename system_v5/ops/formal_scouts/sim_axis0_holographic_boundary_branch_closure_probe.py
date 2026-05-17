#!/usr/bin/env python3
"""Negative closure guard for the Axis0 holographic-boundary branch.

The boundary/interior reconstruction scout emits a finite vector and a green
receipt because the diagnostic computation is valid. That is not admission as a
holographic dictionary, an interior-reconstruction feature, or final Axis0.
This scout closes the branch: `all_pass=True` means the block is enforced.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

import numpy as np
import z3

import axis0_guard_utils as axis0_guard


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "axis0_holographic_boundary_branch_closure_probe_results.json"

NAME = "axis0_holographic_boundary_branch_closure_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "axis0_holographic_boundary_blocked_branch_closure"
CLAIM_CEILING = (
    "Formal scout only: verifies that the finite holographic_boundary_interior_"
    "reconstruction vector remains diagnostic-only and is blocked from "
    "downstream Axis0 feature admission by strict best-KL, path-label recovery, "
    "and post-guard active-feature checks. It does not admit final Axis0, a "
    "holographic dictionary, interior reconstruction, FEP, Holodeck, physics, "
    "cognition, topology, learned dynamics, or canonical architecture claims."
)

TOOL_MANIFEST = {
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "load-bearing receipt parsing for source, router, guard, and downstream adapters",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite vector and numeric blocker checks",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite branch-closure consistency witness",
    },
    "axis0_guard_utils": {
        "tried": True,
        "used": True,
        "reason": "load-bearing admitted/blocked Axis0 feature boundary",
    },
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

HBI = "holographic_boundary_interior_reconstruction"
AXIS0_HBI = f"axis0_{HBI}"
STRICT_BEST_KL_STATUS = "blocked_strict_best_kl_gap_below_old_floor"
PATH_LABEL_STATUS = "blocked_path_features_do_not_reliably_recover_engine_or_terrain_labels"

SOURCE_RESULT = "source_native_engine_boundary_path_fep_reconstruction_probe_results.json"
ROUTER_RESULT = "macro_sim_axis0_plural_stage_candidate_router_probe_results.json"
GUARD_RESULT = "axis0_plural_candidate_multicarrier_drive_controls_probe_results.json"
WORLD_MODEL_RESULT = "world_model_repo_admission_gap_adapter_probe_results.json"
AUTO_LIRPA_CONSUMPTION_RESULT = "auto_lirpa_stage_policy_bound_consumption_probe_results.json"
AUTO_LIRPA_TRAINED_RESULT = "auto_lirpa_trained_stage_policy_adapter_bound_probe_results.json"
LIRPA_GATED_ENV_RESULT = "lirpa_policy_bound_gated_multicarrier_environment_probe_results.json"
LIRPA_VARIABLE_RESULT = "lirpa_policy_bound_variable_qubit_scaling_probe_results.json"
LIRPA_SIZE_RESULT = "lirpa_peps3d_size_normalized_environment_scaling_probe_results.json"
SUBDENSE_RESULT = "source_native_multicarrier_subdense_environment_contraction_probe_results.json"
FEP_GRADIENT_CLOSURE_RESULT = "axis0_fep_gradient_stage_local_adapter_closure_probe_results.json"
MPS_LOCAL_BOUNDARY_SCALING_RESULT = "mps_local_boundary_path_fep_scaling_8_16_32_engine_transport_probe_results.json"
OPERATIONAL_MANIFEST_RESULT = "operational_manifest_source_downstream_quarantine_probe_results.json"

POST_GUARD_RESULTS = [
    WORLD_MODEL_RESULT,
    AUTO_LIRPA_CONSUMPTION_RESULT,
    AUTO_LIRPA_TRAINED_RESULT,
    LIRPA_GATED_ENV_RESULT,
    LIRPA_VARIABLE_RESULT,
    LIRPA_SIZE_RESULT,
]
EXPECTED_DERIVED_POST_GUARD_RESULTS = [
    FEP_GRADIENT_CLOSURE_RESULT,
    MPS_LOCAL_BOUNDARY_SCALING_RESULT,
    *POST_GUARD_RESULTS,
    OPERATIONAL_MANIFEST_RESULT,
]
PRE_GUARD_RAW_INPUT_RESULTS = [
    SOURCE_RESULT,
    ROUTER_RESULT,
    GUARD_RESULT,
    SUBDENSE_RESULT,
]

ACTIVE_PATH_TERMS = (
    "active",
    "enabled",
    "feature",
    "features",
    "feature_names",
    "columns",
    "column",
    "in_use",
    "axis0_features",
    "adapter_features",
    "enabled_features",
    "features_in_use",
    "used_features",
    "consumed_candidates",
)
ALLOWED_DIAGNOSTIC_PATH_TERMS = (
    "blocked",
    "excluded",
    "blocker",
    "candidate_names",
    "candidate_status",
    "control",
    "controls",
    "dependency_status",
    "diagnostic",
    "explicit_blockers",
    "graveyard",
    "guard",
    "raw",
    "receipt",
    "receipts",
    "route_graph",
)
ACTIVE_HBI_NORMALIZED_TERMS = {
    "axis0holographicboundaryinteriorreconstruction",
    "holographicboundaryinteriorreconstructionaxis0",
    "holographicboundaryinteriorreconstruction",
    "hbi",
    "boundaryinterior",
    "interiorreconstruction",
    "holographicdictionary",
    "boundaryreconstruction",
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    return value


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_result(name: str) -> dict[str, Any]:
    path = RESULT_DIR / name
    if not path.exists():
        return {"exists": False, "path": str(path)}
    data = json.loads(path.read_text(encoding="utf-8"))
    data["exists"] = True
    data["path"] = str(path)
    return data


def receipt_ok(data: dict[str, Any]) -> bool:
    return bool(
        data.get("exists") is True
        and data.get("all_pass") is True
        and data.get("classification") == "formal_scout"
        and data.get("promotion_allowed") is False
    )


def get_path(data: Any, *parts: str, default: Any = None) -> Any:
    cur = data
    for part in parts:
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def recursive_hits(data: Any, needle: str, path: tuple[str, ...] = ()) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    if isinstance(data, dict):
        for key, value in data.items():
            next_path = path + (str(key),)
            if key == needle:
                hits.append({"path": ".".join(next_path), "value": value})
            hits.extend(recursive_hits(value, needle, next_path))
    elif isinstance(data, list):
        for idx, value in enumerate(data):
            hits.extend(recursive_hits(value, needle, path + (str(idx),)))
    return hits


def contains_value(data: Any, target: str) -> bool:
    if data == target:
        return True
    if isinstance(data, dict):
        return any(contains_value(value, target) for value in data.values())
    if isinstance(data, list):
        return any(contains_value(value, target) for value in data)
    return False


def normalize_token(value: Any) -> str:
    return "".join(ch for ch in str(value).lower() if ch.isalnum())


def path_has_term(path: str, terms: tuple[str, ...]) -> bool:
    lowered = path.lower()
    return any(term in lowered for term in terms)


def suspicious_active_hbi_hits(data: Any, path: tuple[str, ...] = ()) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    joined = ".".join(path)
    active_like = path_has_term(joined, ACTIVE_PATH_TERMS)
    diagnostic_like = path_has_term(joined, ALLOWED_DIAGNOSTIC_PATH_TERMS)
    if active_like and not diagnostic_like:
        if isinstance(data, (str, int, float, bool)) and normalize_token(data) in ACTIVE_HBI_NORMALIZED_TERMS:
            hits.append({"path": joined, "value": data})
        elif isinstance(data, list):
            for idx, value in enumerate(data):
                if normalize_token(value) in ACTIVE_HBI_NORMALIZED_TERMS:
                    hits.append({"path": ".".join(path + (str(idx),)), "value": value})
    if isinstance(data, dict):
        for key, value in data.items():
            hits.extend(suspicious_active_hbi_hits(value, path + (str(key),)))
    elif isinstance(data, list):
        for idx, value in enumerate(data):
            hits.extend(suspicious_active_hbi_hits(value, path + (str(idx),)))
    return hits


def active_feature_hits(receipts: dict[str, dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for name, data in receipts.items():
        hits: list[dict[str, Any]] = []
        for key in (
            "adapter_active_axis0_feature_names",
            "active_axis0_feature_names",
            "feature_names",
            "active_feature_names",
            "axis0_features_in_use",
            "adapter_features",
            "enabled_features",
            "features_in_use",
            "used_features",
            "consumed_candidates",
        ):
            for hit in recursive_hits(data, key):
                if path_has_term(hit["path"], ALLOWED_DIAGNOSTIC_PATH_TERMS):
                    continue
                if contains_value(hit["value"], AXIS0_HBI) or contains_value(hit["value"], HBI):
                    hits.append(hit)
        hits.extend(suspicious_active_hbi_hits(data))
        out[name] = hits
    return out


def raw_router_hits(receipts: dict[str, dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for name, data in receipts.items():
        hits: list[dict[str, Any]] = []
        for key in (
            "candidate_names",
            "consumed_candidates",
            "raw_router_candidate_names",
            "blocked_candidate_names",
            "axis0_outputs_or_blockers",
            "explicit_blockers",
        ):
            for hit in recursive_hits(data, key):
                if contains_value(hit["value"], HBI):
                    hits.append(hit)
        out[name] = hits
    return out


def finite_hbi_values(hbi: dict[str, Any]) -> bool:
    if hbi.get("finite") is True:
        return True
    values = [
        hbi.get("mean_tomographic_fep_gap"),
        hbi.get("selection_gap"),
        hbi.get("axis0_path_entropy_mean_abs_delta"),
    ]
    return bool(values and all(np.isfinite(float(value)) for value in values))


def blocker_statuses(source_hbi: dict[str, Any], router_hbi: dict[str, Any]) -> dict[str, Any]:
    source_strict = source_hbi.get("strict_best_kl_blocker") or {}
    source_path = source_hbi.get("path_label_recovery_blocker") or {}
    router_blockers = router_hbi.get("explicit_blockers") or {}
    router_strict = router_blockers.get("strict_best_kl_selection_gap") or {}
    router_path = router_blockers.get("path_label_recovery") or {}
    strict_gap = float(source_strict.get("selection_gap", np.nan))
    strict_floor = float(source_strict.get("old_selection_gap_floor", np.nan))
    engine_accuracy = float(source_path.get("engine_accuracy", np.nan))
    engine_floor = float(source_path.get("old_required_engine_floor", np.nan))
    engine_margin = engine_accuracy - float(source_path.get("engine_shuffled_accuracy", np.nan))
    engine_margin_floor = float(source_path.get("old_required_engine_margin_over_shuffle", np.nan))
    terrain_accuracy = float(source_path.get("terrain_accuracy", np.nan))
    terrain_floor = float(source_path.get("old_required_terrain_floor", np.nan))
    terrain_margin = terrain_accuracy - float(source_path.get("terrain_shuffled_accuracy", np.nan))
    terrain_margin_floor = float(source_path.get("old_required_terrain_margin_over_shuffle", np.nan))
    stage_accuracy = float(source_path.get("stage_accuracy", np.nan))
    return {
        "strict_best_kl": {
            "source": source_strict,
            "router": router_strict,
            "numeric_failure": bool(
                np.isfinite(strict_gap)
                and np.isfinite(strict_floor)
                and strict_gap < strict_floor
                and source_strict.get("status") == STRICT_BEST_KL_STATUS
                and router_strict.get("status") == STRICT_BEST_KL_STATUS
            ),
        },
        "path_label_recovery": {
            "source": source_path,
            "router": router_path,
            "numeric_failure": bool(
                source_path.get("status") == PATH_LABEL_STATUS
                and router_path.get("status") == PATH_LABEL_STATUS
                and (
                    engine_accuracy < engine_floor
                    or engine_margin < engine_margin_floor
                    or terrain_accuracy < terrain_floor
                    or terrain_margin < terrain_margin_floor
                    or stage_accuracy <= 0.125
                )
            ),
            "margins": {
                "engine_margin_over_shuffle": engine_margin,
                "terrain_margin_over_shuffle": terrain_margin,
            },
        },
    }


def branch_closure_z3(
    *,
    source_blocks: bool,
    router_blocks: bool,
    guard_blocks: bool,
    no_active_feature_hits: bool,
    raw_input_hits_present: bool,
) -> dict[str, Any]:
    solver = z3.Solver()
    source = z3.Bool("source_hbi_blockers_preserved")
    router = z3.Bool("router_hbi_blockers_preserved")
    guard = z3.Bool("guard_blocks_hbi")
    no_active = z3.Bool("no_post_guard_axis0_hbi_feature")
    raw_inputs = z3.Bool("raw_pre_guard_hbi_inputs_remain_diagnostic")
    solver.add(source == source_blocks)
    solver.add(router == router_blocks)
    solver.add(guard == guard_blocks)
    solver.add(no_active == no_active_feature_hits)
    solver.add(raw_inputs == raw_input_hits_present)
    solver.add(z3.Not(z3.And(source, router, guard, no_active, raw_inputs)))
    status = solver.check()
    return {
        "pass": status == z3.unsat,
        "solver_status": str(status),
        "claim_ceiling": "Finite Boolean consistency witness over already-computed receipt predicates only.",
    }


def downstream_results_from_integrated_suite() -> list[str]:
    try:
        import sim_integrated_constraint_manifold_suite_fresh_rerun_probe as suite
    except Exception as exc:
        raise RuntimeError("could not import integrated suite for HBI downstream derivation") from exc
    rows = list(getattr(suite, "SUITE", []))
    names = [row.get("name") for row in rows]
    if "axis0_holographic_boundary_branch_closure" not in names:
        raise RuntimeError("integrated suite is missing axis0_holographic_boundary_branch_closure")
    start = names.index("axis0_holographic_boundary_branch_closure") + 1
    results: list[str] = []
    for row in rows[start:]:
        result_name = row.get("result")
        if isinstance(result_name, str):
            results.append(result_name)
    if not results:
        raise RuntimeError("integrated suite has no downstream rows after HBI closure")
    return results


def guard_has_required_keys(guard: dict[str, Any]) -> bool:
    required = {
        "pass",
        "admitted_candidate_names",
        "blocked_candidate_names",
        "candidate_status",
        "blocked_candidate_status",
        "adapter_active_axis0_feature_names",
        "blocked_axis0_feature_names_excluded",
    }
    return required.issubset(set(guard))


def claim_ceiling_has_required_terms() -> bool:
    lowered = CLAIM_CEILING.lower()
    required = [
        "formal scout",
        "does not admit",
        "final axis0",
        "holographic dictionary",
        "interior reconstruction",
        "physics",
        "canonical architecture",
    ]
    banned = [
        "admitted holography",
        "validated reconstruction",
        "dictionary learned",
        "interior recovered",
    ]
    return all(term in lowered for term in required) and not any(term in lowered for term in banned)


def main() -> int:
    started = time.time()
    source = load_result(SOURCE_RESULT)
    router = load_result(ROUTER_RESULT)
    guard_receipt = load_result(GUARD_RESULT)
    post_guard_result_names = downstream_results_from_integrated_suite()
    post_guard = {name: load_result(name) for name in post_guard_result_names}
    pre_guard = {name: load_result(name) for name in PRE_GUARD_RAW_INPUT_RESULTS}

    guard = axis0_guard.axis0_guard_signal(guard_receipt)
    source_hbi = get_path(source, "axis0_outputs_or_blockers", HBI, default={})
    router_hbi = get_path(router, "axis0_outputs_or_blockers", HBI, default={})
    guard_hbi = get_path(guard, "blocked_candidate_status", HBI, default={})
    blockers = blocker_statuses(source_hbi, router_hbi)
    active_hits = active_feature_hits(post_guard)
    raw_hits = raw_router_hits(pre_guard)

    source_blocks = bool(
        receipt_ok(source)
        and source_hbi.get("status") == "routing_candidate_not_final"
        and finite_hbi_values(source_hbi)
        and blockers["strict_best_kl"]["numeric_failure"]
        and blockers["path_label_recovery"]["numeric_failure"]
    )
    router_blocks = bool(
        receipt_ok(router)
        and router_hbi.get("status") == "routing_candidate_not_final"
        and finite_hbi_values(router_hbi)
        and set((router_hbi.get("explicit_blockers") or {}).keys())
        >= {"path_label_recovery", "strict_best_kl_selection_gap"}
        and blockers["strict_best_kl"]["numeric_failure"]
        and blockers["path_label_recovery"]["numeric_failure"]
    )
    guard_blocks = bool(
        guard_has_required_keys(guard)
        and guard.get("pass")
        and HBI in guard.get("blocked_candidate_names", [])
        and AXIS0_HBI in guard.get("blocked_axis0_feature_names_excluded", [])
        and AXIS0_HBI not in guard.get("adapter_active_axis0_feature_names", [])
        and guard_hbi.get("candidate_admissible_for_downstream_drop_controls") is False
    )
    post_guard_receipts_exist = bool(all(data.get("exists") is True for data in post_guard.values()))
    no_active_feature_hits = bool(post_guard_receipts_exist and all(not hits for hits in active_hits.values()))
    raw_input_hits_present = bool(any(raw_hits.values()))
    z3_witness = branch_closure_z3(
        source_blocks=source_blocks,
        router_blocks=router_blocks,
        guard_blocks=guard_blocks,
        no_active_feature_hits=no_active_feature_hits,
        raw_input_hits_present=raw_input_hits_present,
    )

    repair_receipt = {
        "weak_link": (
            "A finite HBI vector and green source receipt can be misread as "
            "holographic dictionary or interior-reconstruction admission."
        ),
        "target_file_or_result": str(OUT_PATH),
        "admission_rule_improved": (
            "HBI remains diagnostic-only unless it clears strict best-KL and "
            "path-label recovery blockers, is guard-admitted, and appears in no "
            "post-guard active feature surface while blocked."
        ),
        "dependency_subset": [
            SOURCE_RESULT,
            ROUTER_RESULT,
            GUARD_RESULT,
            *POST_GUARD_RESULTS,
        ],
        "stage_fields_touched_or_consumed": [
            f"axis0_outputs_or_blockers.{HBI}",
            "axis0_outputs_or_blockers.admitted_candidate_names",
            "axis0_outputs_or_blockers.blocked_candidate_names",
            "axis0_outputs_or_blockers.adapter_active_axis0_feature_names",
            "strict_best_kl_selection_gap",
            "path_label_recovery",
        ],
        "before_baseline/hash": {
            "source_result": source.get("path"),
            "router_result": router.get("path"),
            "guard_result": guard_receipt.get("path"),
        },
        "after_delta/hash": {
            "script_sha256": sha256_file(pathlib.Path(__file__)),
            "result_path": str(OUT_PATH),
        },
        "primary_control/result": {
            "source_hbi_status": source_hbi.get("status"),
            "source_hbi_finite": finite_hbi_values(source_hbi),
            "router_hbi_status": router_hbi.get("status"),
            "router_hbi_finite": finite_hbi_values(router_hbi),
            "blockers": blockers,
            "guard": guard,
            "post_guard_axis0_hbi_feature_hits": active_hits,
            "post_guard_result_names_from_integrated_suite": post_guard_result_names,
            "pre_guard_raw_hbi_hits": raw_hits,
        },
        "axis0_outputs_or_blockers": {
            HBI: {
                "status": "blocked_diagnostic_only_boundary_interior_reconstruction_proxy",
                "source_status": source_hbi.get("status"),
                "router_status": router_hbi.get("status"),
                "guard_status": guard_hbi,
                "strict_best_kl_blocker": blockers["strict_best_kl"],
                "path_label_recovery_blocker": blockers["path_label_recovery"],
                "replacement_required_if_reopened": (
                    "Clear strict best-KL selection and path-label recovery under "
                    "matched controls before any downstream Axis0, holographic "
                    "dictionary, or interior-reconstruction feature admission. A "
                    "finite boundary metric alone is insufficient."
                ),
            },
            "admitted_candidate_names": guard.get("admitted_candidate_names", []),
            "blocked_candidate_names": guard.get("blocked_candidate_names", []),
            "adapter_active_axis0_feature_names": guard.get("adapter_active_axis0_feature_names", []),
            "blocked_axis0_feature_names_excluded": guard.get("blocked_axis0_feature_names_excluded", []),
            "diagnostic_raw_pre_guard_surfaces": sorted(name for name, hits in raw_hits.items() if hits),
            "post_guard_active_feature_surfaces_with_hbi": sorted(
                name for name, hits in active_hits.items() if hits
            ),
            "post_guard_result_names_from_integrated_suite": post_guard_result_names,
        },
        "provider_inputs_used": {
            "codex_native_explorers": "Galileo closure-shape map; Parfit false-green premortem",
            "grok": "proposal-only prior HBI/FEP/Axis0 branch framing",
            "gemini": "proposal-only prior Axis0 premortem framing",
            "sonnet_high": "not_run_this_local_closure_wave",
            "opus_max": "not_run_this_local_closure_wave",
        },
        "promotion_ceiling": CLAIM_CEILING,
        "next_step": (
            "Keep HBI in blocked/diagnostic surfaces. Reopen only through a "
            "matched-control reconstruction candidate that clears both existing blockers."
        ),
    }

    positive = {
        "source_router_guard_receipts_are_current_formal_scouts": {
            "pass": all(receipt_ok(data) for data in [source, router, guard_receipt]),
            "receipts": {
                name: {
                    "exists": data.get("exists"),
                    "all_pass": data.get("all_pass"),
                    "classification": data.get("classification"),
                    "promotion_allowed": data.get("promotion_allowed"),
                }
                for name, data in {
                    SOURCE_RESULT: source,
                    ROUTER_RESULT: router,
                    GUARD_RESULT: guard_receipt,
                }.items()
            },
        },
        "source_hbi_keeps_numeric_blockers": {
            "pass": source_blocks,
            "source_hbi": source_hbi,
            "blockers": blockers,
        },
        "router_hbi_keeps_routing_candidate_not_final": {
            "pass": router_blocks,
            "router_hbi": router_hbi,
        },
        "guard_blocks_hbi_before_adapter_features": {
            "pass": guard_blocks,
            "required_guard_keys_present": guard_has_required_keys(guard),
            "guard": guard,
        },
        "post_guard_consumers_do_not_activate_axis0_hbi": {
            "pass": no_active_feature_hits,
            "post_guard_receipts_exist": post_guard_receipts_exist,
            "active_feature_hits": active_hits,
        },
        "post_guard_consumer_set_is_derived_from_integrated_suite": {
            "pass": post_guard_result_names == EXPECTED_DERIVED_POST_GUARD_RESULTS,
            "expected_exact_results": EXPECTED_DERIVED_POST_GUARD_RESULTS,
            "static_minimum_results": POST_GUARD_RESULTS,
            "derived_results": post_guard_result_names,
        },
        "pre_guard_raw_consumption_is_visible_as_diagnostic_input": {
            "pass": raw_input_hits_present,
            "raw_hits": raw_hits,
            "allowed_scope": "pre-guard raw/source/router/control inputs only; not active post-guard adapter features",
        },
        "z3_branch_closure_witness_executes": z3_witness,
    }
    graveyards = {
        "finite_boundary_candidate_is_not_holographic_dictionary": {
            "pass": bool(finite_hbi_values(source_hbi) and finite_hbi_values(router_hbi) and guard_blocks),
            "source_hbi_status": source_hbi.get("status"),
            "router_hbi_status": router_hbi.get("status"),
            "guard_blocked_candidate_names": guard.get("blocked_candidate_names", []),
        },
        "green_source_receipt_does_not_promote_hbi": {
            "pass": bool(receipt_ok(source) and source_blocks and PROMOTION_ALLOWED is False),
            "source_all_pass": source.get("all_pass"),
            "source_promotion_allowed": source.get("promotion_allowed"),
            "closure_promotion_allowed": PROMOTION_ALLOWED,
        },
        "path_label_failure_blocks_reconstruction_claim": {
            "pass": bool(blockers["path_label_recovery"]["numeric_failure"]),
            "path_label_recovery": blockers["path_label_recovery"],
        },
        "strict_best_kl_floor_blocks_dictionary_claim": {
            "pass": bool(blockers["strict_best_kl"]["numeric_failure"]),
            "strict_best_kl": blockers["strict_best_kl"],
        },
    }
    boundary = {
        "claim_ceiling_blocks_axis0_holography_interior_physics_promotion": {
            "pass": claim_ceiling_has_required_terms(),
        },
        "repair_receipt_has_required_loop_fields": {
            "pass": all(
                key in repair_receipt
                for key in [
                    "weak_link",
                    "target_file_or_result",
                    "admission_rule_improved",
                    "dependency_subset",
                    "stage_fields_touched_or_consumed",
                    "before_baseline/hash",
                    "after_delta/hash",
                    "primary_control/result",
                    "axis0_outputs_or_blockers",
                    "provider_inputs_used",
                    "promotion_ceiling",
                    "next_step",
                ]
            ),
            "keys": sorted(repair_receipt),
        },
        "blocked_branch_has_reopen_condition": {
            "pass": bool("replacement_required_if_reopened" in repair_receipt["axis0_outputs_or_blockers"][HBI]),
            "reopen_condition": repair_receipt["axis0_outputs_or_blockers"][HBI][
                "replacement_required_if_reopened"
            ],
        },
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyards.values())
        and all(row["pass"] for row in boundary.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "repair_receipt": repair_receipt,
        "axis0_outputs_or_blockers": repair_receipt["axis0_outputs_or_blockers"],
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(graveyards),
            "passed": sum(1 for row in graveyards.values() if row["pass"]),
            "variants": sorted(graveyards),
        },
        "why_not_v4_probes": [
            "This is a v5 branch-closure guard over current source/router/guard receipts.",
            "Older boundary/Holodeck language cannot override the current downstream Axis0 guard.",
        ],
        "all_pass": all_pass,
        "blockers": [],
        "elapsed_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
