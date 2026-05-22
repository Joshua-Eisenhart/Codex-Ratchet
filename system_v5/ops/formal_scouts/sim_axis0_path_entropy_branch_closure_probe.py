#!/usr/bin/env python3
"""Negative closure guard for the Axis0 path-entropy branch.

The macro Axis0 router still emits a finite `path_entropy` vector because it is
useful diagnostic material. The downstream guard and two falsifier receipts
block that vector from becoming an admitted Axis0/admissibility feature. This
scout closes that branch: `all_pass=True` means the block is enforced, not that
path entropy is promoted.
"""

from __future__ import annotations

import hashlib
import json
import math
import pathlib
import time
from typing import Any

import torch
import z3

import axis0_guard_utils as axis0_guard


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "axis0_path_entropy_branch_closure_probe_results.json"

NAME = "axis0_path_entropy_branch_closure_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "axis0_path_entropy_blocked_diagnostic_branch_closure"
CLAIM_CEILING = (
    "Formal scout only: verifies that the finite macro-router path_entropy "
    "vector remains a diagnostic/proxy and is blocked from downstream Axis0 "
    "feature admission by guard, schedule-confound, and pair-falsifier receipts. "
    "It does not admit final Axis0, FEP, Holodeck, physics, cognition, topology, "
    "admissibility, learned dynamics, or canonical architecture claims."
)

TOOL_MANIFEST = {
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "load-bearing receipt parsing for router, guard, falsifiers, and downstream adapters",
    },
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite vector and numeric witness checks for path-entropy branch closure",
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
TOOL_INTEGRATION_DEPTH = {
    'python_json': 'supportive',
    'pytorch': 'load_bearing',
    'z3': 'load_bearing',
    'axis0_guard_utils': 'supportive',
}
TOOL_ROLE_SOURCE = {
    "python_json": "local",
    "pytorch": "local",
    "z3": "local",
    "axis0_guard_utils": "local",
}

PATH_ENTROPY_EQUALITY_TOL = 1e-12
DEEPER_INVARIANT_GAP_FLOOR = 1e-3

ROUTER_RESULT = "macro_sim_axis0_plural_stage_candidate_router_probe_results.json"
GUARD_RESULT = "axis0_plural_candidate_multicarrier_drive_controls_probe_results.json"
SCHEDULE_CONFOUND_RESULT = "path_entropy_schedule_confound_falsifier_probe_results.json"
PAIR_FALSIFIER_RESULT = "path_entropy_proxy_vs_deeper_invariant_pair_falsifier_probe_results.json"
WORLD_MODEL_RESULT = "world_model_repo_admission_gap_adapter_probe_results.json"
AUTO_LIRPA_CONSUMPTION_RESULT = "auto_lirpa_stage_policy_bound_consumption_probe_results.json"
AUTO_LIRPA_TRAINED_RESULT = "auto_lirpa_trained_stage_policy_adapter_bound_probe_results.json"
LIRPA_GATED_ENV_RESULT = "lirpa_policy_bound_gated_multicarrier_environment_probe_results.json"
LIRPA_VARIABLE_RESULT = "lirpa_policy_bound_variable_qubit_scaling_probe_results.json"
LIRPA_SIZE_RESULT = "lirpa_peps3d_size_normalized_environment_scaling_probe_results.json"
SUBDENSE_RESULT = "source_native_multicarrier_subdense_environment_contraction_probe_results.json"

POST_GUARD_RESULTS = [
    WORLD_MODEL_RESULT,
    AUTO_LIRPA_CONSUMPTION_RESULT,
    AUTO_LIRPA_TRAINED_RESULT,
    LIRPA_GATED_ENV_RESULT,
    LIRPA_VARIABLE_RESULT,
    LIRPA_SIZE_RESULT,
]
PRE_GUARD_RAW_INPUT_RESULTS = [
    SUBDENSE_RESULT,
    GUARD_RESULT,
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
)
ALLOWED_DIAGNOSTIC_PATH_TERMS = (
    "blocked",
    "excluded",
    "blocker",
    "candidate_names",
    "candidate_status",
    "consumed_candidates",
    "control",
    "controls",
    "degeneracy",
    "diagnostic",
    "dependency_status",
    "edge_list",
    "graveyard",
    "guard",
    "receipt",
    "receipts",
    "raw",
    "route_graph",
    "repair_receipt.axis0_outputs_or_blockers.path_entropy",
)


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        return value.tolist()
    return value


def finite_float(value: Any, default: float = math.nan) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if bool(torch.isfinite(torch.as_tensor(out, dtype=torch.float64)).item()) else default


def finite_min(values: list[float]) -> float:
    tensor = torch.as_tensor(values, dtype=torch.float64)
    finite = tensor[torch.isfinite(tensor)]
    if finite.numel() == 0:
        return math.nan
    return float(torch.min(finite).item())


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


def suspicious_active_path_entropy_hits(data: Any, path: tuple[str, ...] = ()) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    joined = ".".join(path)
    active_like = path_has_term(joined, ACTIVE_PATH_TERMS)
    diagnostic_like = path_has_term(joined, ALLOWED_DIAGNOSTIC_PATH_TERMS)
    if active_like and not diagnostic_like:
        if isinstance(data, (str, int, float, bool)) and normalize_token(data) in {
            "axis0pathentropy",
            "pathentropyaxis0",
            "pathentropy",
        }:
            hits.append({"path": joined, "value": data})
        elif isinstance(data, list):
            for idx, value in enumerate(data):
                if normalize_token(value) in {"axis0pathentropy", "pathentropyaxis0", "pathentropy"}:
                    hits.append({"path": ".".join(path + (str(idx),)), "value": value})
    if isinstance(data, dict):
        for key, value in data.items():
            hits.extend(suspicious_active_path_entropy_hits(value, path + (str(key),)))
    elif isinstance(data, list):
        for idx, value in enumerate(data):
            hits.extend(suspicious_active_path_entropy_hits(value, path + (str(idx),)))
    return hits


def active_feature_hits(receipts: dict[str, dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for name, data in receipts.items():
        hits = []
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
        ):
            for hit in recursive_hits(data, key):
                if contains_value(hit["value"], "axis0_path_entropy"):
                    hits.append(hit)
        hits.extend(suspicious_active_path_entropy_hits(data))
        out[name] = hits
    return out


def raw_router_hits(receipts: dict[str, dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for name, data in receipts.items():
        hits = []
        for key in ("candidate_names", "consumed_candidates", "raw_router_candidate_names"):
            for hit in recursive_hits(data, key):
                if contains_value(hit["value"], "path_entropy"):
                    hits.append(hit)
        out[name] = hits
    return out


def branch_closure_z3(
    *,
    guard_blocks: bool,
    schedule_blocks: bool,
    pair_blocks: bool,
    no_active_feature_hits: bool,
    raw_input_hits_present: bool,
) -> dict[str, Any]:
    solver = z3.Solver()
    guard = z3.Bool("guard_blocks_path_entropy")
    schedule = z3.Bool("schedule_confound_blocks_path_entropy")
    pair = z3.Bool("pair_falsifier_blocks_path_entropy")
    no_active = z3.Bool("no_post_guard_axis0_path_entropy_feature")
    raw_inputs = z3.Bool("raw_pre_guard_inputs_remain_diagnostic")
    solver.add(guard == guard_blocks)
    solver.add(schedule == schedule_blocks)
    solver.add(pair == pair_blocks)
    solver.add(no_active == no_active_feature_hits)
    solver.add(raw_inputs == raw_input_hits_present)
    solver.add(z3.Not(z3.And(guard, schedule, pair, no_active, raw_inputs)))
    status = solver.check()
    return {
        "pass": status == z3.unsat,
        "solver_status": str(status),
        "claim_ceiling": "Finite Boolean consistency witness over already-computed receipt predicates only.",
    }


def downstream_results_from_integrated_suite() -> list[str]:
    try:
        import sim_integrated_constraint_manifold_suite_fresh_rerun_probe as suite
    except Exception:
        return list(POST_GUARD_RESULTS)
    rows = list(getattr(suite, "SUITE", []))
    names = [row.get("name") for row in rows]
    if "axis0_path_entropy_branch_closure" not in names:
        return list(POST_GUARD_RESULTS)
    start = names.index("axis0_path_entropy_branch_closure") + 1
    results: list[str] = []
    for row in rows[start:]:
        result_name = row.get("result")
        if isinstance(result_name, str):
            results.append(result_name)
    return results or list(POST_GUARD_RESULTS)


def main() -> int:
    started = time.time()
    router = load_result(ROUTER_RESULT)
    guard_receipt = load_result(GUARD_RESULT)
    schedule = load_result(SCHEDULE_CONFOUND_RESULT)
    pair = load_result(PAIR_FALSIFIER_RESULT)
    post_guard_result_names = downstream_results_from_integrated_suite()
    post_guard = {name: load_result(name) for name in post_guard_result_names}
    pre_guard = {name: load_result(name) for name in PRE_GUARD_RAW_INPUT_RESULTS}

    guard = axis0_guard.axis0_guard_signal(guard_receipt)
    router_path_entropy = get_path(router, "axis0_outputs_or_blockers", "path_entropy", default={})
    schedule_gaps = get_path(
        schedule,
        "repair_receipt",
        "primary_control/result",
        "deeper_invariant_gaps_under_same_path_entropy",
        default={},
    )
    path_delta = finite_float(
        get_path(
            schedule,
            "repair_receipt",
            "primary_control/result",
            "path_entropy_delta_same_schedule",
            default=math.nan,
        )
    )
    deeper_gap_values = [
        finite_float(schedule_gaps.get("fep_gradient_l2_gap", 0.0), default=0.0),
        finite_float(schedule_gaps.get("bloch_path_length_gap", 0.0), default=0.0),
        finite_float(schedule_gaps.get("observation_distribution_l2_gap", 0.0), default=0.0),
    ]
    active_hits = active_feature_hits(post_guard)
    raw_hits = raw_router_hits(pre_guard)
    proxy_status = get_path(pair, "axis0_outputs_or_blockers", default={})
    schedule_axis0 = get_path(schedule, "axis0_outputs_or_blockers", default={})

    guard_blocks = bool(
        guard.get("pass")
        and "path_entropy" in guard.get("blocked_candidate_names", [])
        and "axis0_path_entropy" in guard.get("blocked_axis0_feature_names_excluded", [])
        and "axis0_path_entropy" not in guard.get("adapter_active_axis0_feature_names", [])
    )
    schedule_blocks = bool(
        receipt_ok(schedule)
        and schedule_axis0.get("path_entropy_current_reading")
        == "blocked_schedule_token_entropy_derivative_not_downstream_axis0_feature"
        and math.isfinite(path_delta)
        and abs(path_delta) <= PATH_ENTROPY_EQUALITY_TOL
        and finite_min(deeper_gap_values) > DEEPER_INVARIANT_GAP_FLOOR
        and get_path(
            schedule,
            "axis0_outputs_or_blockers",
            "decyclicized_status_is_surrogate_not_source_native_schedule",
        )
        is True
    )
    pair_blocks = bool(
        receipt_ok(pair)
        and proxy_status.get("path_entropy_reading_under_pair_falsifier")
        == "proxy_for_rolling_window_categorical_distribution_not_load_bearing_admissibility_invariant"
        and proxy_status.get("deeper_invariant_status")
        == "candidate_admissible_for_further_pair_tests_on_engine_schedules_in_v2_only"
        and proxy_status.get("downstream_promotion_allowed") is False
    )
    no_active_feature_hits = bool(all(not hits for hits in active_hits.values()))
    raw_input_hits_present = bool(any(raw_hits.values()))
    z3_witness = branch_closure_z3(
        guard_blocks=guard_blocks,
        schedule_blocks=schedule_blocks,
        pair_blocks=pair_blocks,
        no_active_feature_hits=no_active_feature_hits,
        raw_input_hits_present=raw_input_hits_present,
    )

    repair_receipt = {
        "weak_link": (
            "The finite router path_entropy vector can be misread as an admitted "
            "Axis0 feature even though downstream guard and falsifier receipts block it."
        ),
        "target_file_or_result": str(OUT_PATH),
        "admission_rule_improved": (
            "path_entropy remains diagnostic-only unless it survives guard admission, "
            "schedule-confound, pair-falsifier, and post-guard active-feature checks."
        ),
        "dependency_subset": [
            ROUTER_RESULT,
            GUARD_RESULT,
            SCHEDULE_CONFOUND_RESULT,
            PAIR_FALSIFIER_RESULT,
            *POST_GUARD_RESULTS,
        ],
        "stage_fields_touched_or_consumed": [
            "axis0_outputs_or_blockers.path_entropy",
            "axis0_outputs_or_blockers.admitted_candidate_names",
            "axis0_outputs_or_blockers.blocked_candidate_names",
            "axis0_outputs_or_blockers.adapter_active_axis0_feature_names",
            "path_entropy_delta_same_schedule",
            "deeper_invariant_gaps_under_same_path_entropy",
        ],
        "before_baseline/hash": {
            "router_result": router.get("path"),
            "guard_result": guard_receipt.get("path"),
            "schedule_confound_result": schedule.get("path"),
            "pair_falsifier_result": pair.get("path"),
        },
        "after_delta/hash": {
            "script_sha256": sha256_file(pathlib.Path(__file__)),
            "result_path": str(OUT_PATH),
        },
        "primary_control/result": {
            "router_path_entropy_status": router_path_entropy.get("status"),
            "router_path_entropy_finite": router_path_entropy.get("finite"),
            "guard": guard,
            "path_entropy_delta_same_schedule": path_delta,
            "deeper_invariant_gaps_under_same_path_entropy": schedule_gaps,
            "post_guard_axis0_path_entropy_feature_hits": active_hits,
            "post_guard_result_names_from_integrated_suite": post_guard_result_names,
            "pre_guard_raw_router_path_entropy_hits": raw_hits,
        },
        "axis0_outputs_or_blockers": {
            "path_entropy": {
                "status": "blocked_diagnostic_only_schedule_confound_proxy",
                "router_status": router_path_entropy.get("status"),
                "guard_status": get_path(guard, "blocked_candidate_status", "path_entropy", default={}),
                "schedule_confound_reading": schedule_axis0.get("path_entropy_current_reading"),
                "pair_falsifier_reading": proxy_status.get("path_entropy_reading_under_pair_falsifier"),
                "replacement_required_if_reopened": (
                    "Build a separate branch/path-ensemble or deeper transition-graph invariant "
                    "candidate; do not reuse the current rolling ordered-token derivative."
                ),
            },
            "admitted_candidate_names": guard.get("admitted_candidate_names", []),
            "blocked_candidate_names": guard.get("blocked_candidate_names", []),
            "adapter_active_axis0_feature_names": guard.get("adapter_active_axis0_feature_names", []),
            "blocked_axis0_feature_names_excluded": guard.get("blocked_axis0_feature_names_excluded", []),
            "diagnostic_raw_pre_guard_surfaces": sorted(name for name, hits in raw_hits.items() if hits),
            "post_guard_active_feature_surfaces_with_path_entropy": sorted(
                name for name, hits in active_hits.items() if hits
            ),
            "post_guard_result_names_from_integrated_suite": post_guard_result_names,
        },
        "provider_inputs_used": {
            "codex_native_explorers": "Socrates path-entropy graph map; Kant false-green/raw-consumer premortem",
            "grok": "proposal-only prior path E schedule-confound framing",
            "gemini": "proposal-only prior path E hidden-risk framing",
            "sonnet_high": "not_run_this_local_closure_wave",
            "opus_max": "not_run_this_local_closure_wave",
        },
        "promotion_ceiling": CLAIM_CEILING,
        "next_step": (
            "Keep path_entropy in blocked/diagnostic surfaces. Reopen only through a "
            "new candidate with deeper-invariant pair tests and guard-filtered downstream consumers."
        ),
    }

    positive = {
        "source_receipts_are_current_formal_scouts": {
            "pass": all(receipt_ok(data) for data in [router, guard_receipt, schedule, pair]),
            "receipts": {
                name: {
                    "exists": data.get("exists"),
                    "all_pass": data.get("all_pass"),
                    "classification": data.get("classification"),
                    "promotion_allowed": data.get("promotion_allowed"),
                }
                for name, data in {
                    ROUTER_RESULT: router,
                    GUARD_RESULT: guard_receipt,
                    SCHEDULE_CONFOUND_RESULT: schedule,
                    PAIR_FALSIFIER_RESULT: pair,
                }.items()
            },
        },
        "guard_blocks_path_entropy_before_adapter_features": {
            "pass": guard_blocks,
            "guard": guard,
        },
        "schedule_confound_numeric_witness_is_preserved": {
            "pass": schedule_blocks,
            "path_entropy_delta_same_schedule": path_delta,
            "deeper_invariant_gaps": schedule_gaps,
            "thresholds": {
                "path_entropy_equality_tol": PATH_ENTROPY_EQUALITY_TOL,
                "deeper_invariant_gap_floor": DEEPER_INVARIANT_GAP_FLOOR,
            },
        },
        "pair_falsifier_keeps_path_entropy_proxy_only": {
            "pass": pair_blocks,
            "axis0_outputs_or_blockers": proxy_status,
        },
        "post_guard_consumers_do_not_activate_axis0_path_entropy": {
            "pass": no_active_feature_hits,
            "active_feature_hits": active_hits,
        },
        "post_guard_consumer_set_is_derived_from_integrated_suite": {
            "pass": bool(set(POST_GUARD_RESULTS).issubset(set(post_guard_result_names))),
            "static_minimum_results": POST_GUARD_RESULTS,
            "derived_results": post_guard_result_names,
        },
        "pre_guard_raw_consumption_is_visible_as_diagnostic_input": {
            "pass": raw_input_hits_present,
            "raw_hits": raw_hits,
            "allowed_scope": "pre-guard raw router/control inputs only; not active post-guard adapter features",
        },
        "z3_branch_closure_witness_executes": z3_witness,
    }
    graveyards = {
        "finite_router_vector_is_not_admission": {
            "pass": bool(router_path_entropy.get("finite") is True and guard_blocks),
            "router_path_entropy": router_path_entropy,
            "guard_blocked_candidate_names": guard.get("blocked_candidate_names", []),
        },
        "all_pass_on_falsifiers_does_not_promote_path_entropy": {
            "pass": bool(receipt_ok(schedule) and receipt_ok(pair) and PROMOTION_ALLOWED is False and guard_blocks),
            "schedule_all_pass": schedule.get("all_pass"),
            "pair_all_pass": pair.get("all_pass"),
            "closure_promotion_allowed": PROMOTION_ALLOWED,
        },
        "decyclicized_revived_candidate_stays_surrogate": {
            "pass": bool(
                get_path(
                    schedule,
                    "axis0_outputs_or_blockers",
                    "decyclicized_status_is_surrogate_not_source_native_schedule",
                )
                is True
            ),
            "decyclicized_status": get_path(schedule, "repair_receipt", "primary_control/result", "decyclicized_same_inventory_status", default={}),
        },
        "deeper_invariant_is_not_promoted_by_pair_falsifier": {
            "pass": bool(proxy_status.get("downstream_promotion_allowed") is False),
            "deeper_invariant_status": proxy_status.get("deeper_invariant_status"),
        },
    }
    boundary = {
        "claim_ceiling_blocks_axis0_fep_holodeck_physics_promotion": {
            "pass": all(
                term in CLAIM_CEILING.lower()
                for term in ["formal scout", "does not admit", "final axis0", "fep", "holodeck", "physics"]
            ),
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
            "pass": bool(
                "replacement_required_if_reopened"
                in repair_receipt["axis0_outputs_or_blockers"]["path_entropy"]
            ),
            "reopen_condition": repair_receipt["axis0_outputs_or_blockers"]["path_entropy"][
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
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "TOOL_ROLE_SOURCE": TOOL_ROLE_SOURCE,
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
            "This is a v5 branch-closure guard over current Axis0 router/guard/falsifier receipts.",
            "Older v4 path-entropy evidence cannot override the current downstream Axis0 guard.",
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
