#!/usr/bin/env python3
"""Validate bounded max-exploration receipts and frontier matrices.

This is a narrow process guard for the 20260525 formal-sim failure class:

* one receipt must not be confused with level completion;
* active-level receipts must carry the current LEGO minimal fields;
* active-level packet receipts must not name downstream stages as the next move;
* a level closeout must have a frontier matrix when required.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


LEGO_REQUIRED_FIELDS = [
    "sim_id",
    "name",
    "version",
    "tier",
    "purpose",
    "scientific_question",
    "sim_execution_kind",
    "sim_class",
    "root_constraints_in_force",
    "finite_map",
    "domain",
    "codomain_or_output",
    "carrier_layer",
    "geometry_layer",
    "carrier_realization",
    "peps3d_embedding",
    "spinor_state",
    "quaternion_action",
    "dependency_receipts",
    "downstream_blocks",
    "bridge_layer",
    "cut_layer",
    "law_or_candidate_tested",
    "branch_status_before_run",
    "allowed_claims",
    "promotion_blockers",
    "required_tools",
    "actual_tools_used",
    "proof_surfaces_used",
    "graph_surfaces_used",
    "topology_surfaces_used",
    "tool_manifest",
    "tool_integration_depth",
    "classification",
    "required_inputs",
    "data_or_artifact_dependencies",
    "required_negatives",
    "negatives_run",
    "kill_conditions",
    "required_artifacts",
    "artifacts_emitted",
    "witness_trace_id",
    "result_summary",
    "pass_rule",
    "fail_rule",
    "promotion_status",
    "eligible_consumers",
    "blocked_consumers",
]

FIELD_ALIASES = {
    "tool_manifest": ["tool_manifest", "TOOL_MANIFEST"],
    "tool_integration_depth": ["tool_integration_depth", "TOOL_INTEGRATION_DEPTH"],
}

LEAK_KEYS = {
    "eligible_consumers",
    "next_admissible_step",
    "next_required_work",
    "next_step",
    "recommended_next_move",
}

DOWNSTREAM_PATTERNS = [
    ("phase 2", re.compile(r"\bphase\s*2\b", re.IGNORECASE)),
    ("phase2", re.compile(r"\bphase2\b", re.IGNORECASE)),
    ("peps3d seed", re.compile(r"\bpeps3d\s+seed\b", re.IGNORECASE)),
    ("spinor/hopf/weyl", re.compile(r"\bspinor\s*/\s*hopf\s*/\s*weyl\b", re.IGNORECASE)),
    ("terrain", re.compile(r"\bterrain\b", re.IGNORECASE)),
    ("operator substage", re.compile(r"\boperator\s+substage\b", re.IGNORECASE)),
    ("flux", re.compile(r"\bflux\b", re.IGNORECASE)),
    ("xi", re.compile(r"\bxi\b|xi\s*/|/\s*xi", re.IGNORECASE)),
    ("phi0", re.compile(r"\bphi0\b", re.IGNORECASE)),
    ("axis0", re.compile(r"\baxis0\b", re.IGNORECASE)),
    ("holodeck", re.compile(r"\bholodeck\b", re.IGNORECASE)),
    ("physics", re.compile(r"\bphysics\b", re.IGNORECASE)),
]

FRONTIER_ROW_REQUIRED_FIELDS = [
    "row_id",
    "candidate_family",
    "carrier",
    "probe_or_effect_family",
    "operator_or_path_witness",
    "positive_case",
    "negative_control",
    "boundary_control",
    "status",
    "blocked_consumers",
    "next_in_level_move",
]

CONTRACT_COMPLETE_STATUSES = {"contract_complete", "survived"}
POST_THRESHOLD_ACTIONS = {
    "continue_active_level",
    "write_transition_artifact",
    "blocked_with_repair",
}
WORKING_GEOMETRY_FIELDS = [
    "plain_answer",
    "active_geometry_object",
    "finite_map",
    "domain",
    "codomain_or_output",
    "earned_structure",
    "noncommuting_or_order_sensitive_structure",
    "controls_that_hold",
    "not_yet_geometry",
    "next_geometry_question",
]
TRANSITION_REQUIRED_FIELDS = [
    "kind",
    "from_level",
    "frontier_matrix_path",
    "validator_command",
    "validator_all_pass",
    "contract_complete_rows",
    "decision",
    "decision_reason",
    "opened_level_or_blocked_level",
    "next_admissible_packet",
    "next_worker_prompt",
    "working_geometry",
    "blocked_downstream_consumers",
    "not_a_stop",
]
TRANSITION_DECISIONS = {"open_next_level", "continue_active_level", "blocked"}
TRANSITION_PROGRESS_FIELDS = [
    "started_next_packet",
    "started_packet_path",
    "started_result_path",
    "continuation_required_artifact_path",
    "blocked_reason_or_repair_path",
]
WIZARD_STATUS_VALUES = {"FULL", "PARTIAL", "BLOCKED"}
PARALLELISM_STATUS_VALUES = {"max_used", "partial", "blocked"}
PARALLELISM_POOL_COMPLETED = {"completed", "accepted", "pass", "passed", "ok"}
PARALLELISM_POOL_ATTEMPTED = PARALLELISM_POOL_COMPLETED | {
    "attempted",
    "partial",
    "blocked",
    "degraded",
    "failed_degraded",
    "timeout",
    "timed_out",
    "failed",
    "rerouted",
}
PROVIDER_LAUNCH_SURFACES = {
    "gemini": {"direct_gemini_api"},
    "grok": {"direct_xai_api"},
    "xai": {"direct_xai_api"},
}
BLOCKER_REQUIRED_FIELDS = [
    "kind",
    "scope",
    "classification",
    "latest_admitted_packet",
    "blocker_map",
    "blocked_reason",
    "downstream_consumers_still_blocked",
    "next_admissible_step",
    "not_a_stop",
]
BLOCKER_MAP_REQUIRED_FIELDS = ["finite_map", "domain", "codomain_or_output"]
LATEST_PACKET_REQUIRED_FIELDS = ["packet_id", "finite_map", "source_path", "result_path", "status"]
PROVIDER_CLI_MARKERS = [
    "gemini cli",
    "grok cli",
    "omx ",
    "omx_",
    "omx-",
]


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _has_field(data: dict[str, Any], field: str) -> bool:
    aliases = FIELD_ALIASES.get(field, [field])
    return any(alias in data and data[alias] not in (None, "", [], {}) for alias in aliases)


def _stringify(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, sort_keys=True, default=str)


def _leak_rows(data: dict[str, Any]) -> list[dict[str, str]]:
    leaks: list[dict[str, str]] = []
    for key in LEAK_KEYS:
        if key not in data:
            continue
        text = _stringify(data[key])
        for keyword, pattern in DOWNSTREAM_PATTERNS:
            if pattern.search(text):
                leaks.append({"field": key, "keyword": keyword})
    return leaks


def _contains_path(value: Any, target: str) -> bool:
    if isinstance(value, str):
        return value == target
    if isinstance(value, list):
        return any(_contains_path(item, target) for item in value)
    if isinstance(value, dict):
        return any(_contains_path(item, target) for item in value.values())
    return False


def _validate_boundary_projection_shape_bond_replay(data: dict[str, Any]) -> list[str]:
    violations: list[str] = []
    if data.get("sim_id") != "peps3d_boundary_projection_shape_bond_replay_probe":
        return violations
    summary = data.get("result_summary")
    domain = data.get("domain")
    positive = data.get("positive")
    graveyard = data.get("graveyard_companions")
    if not isinstance(summary, dict) or not isinstance(domain, dict):
        return ["replay_specific_summary_or_domain_missing"]
    if summary.get("control_row_count") != 1 or domain.get("control_row_count") != 1:
        violations.append("replay_control_row_count_not_one")
    if summary.get("dense_state_closure_used") is not False or summary.get("dense_environment_closure_used") is not False:
        violations.append("replay_dense_closure_flag_not_false")
    if not isinstance(positive, dict):
        violations.append("replay_positive_section_missing")
        return violations
    replay = positive.get("P1_boundary_projection_shape_bond_replay")
    if not isinstance(replay, dict):
        violations.append("replay_positive_row_missing")
        return violations
    if replay.get("bond_dim_one_admitted") is not False:
        violations.append("replay_bond_dim_one_admitted")
    control_shape = tuple(domain.get("zero_interior_control_shape") or [])
    rows = replay.get("rows")
    if not isinstance(rows, list) or not rows:
        violations.append("replay_support_rows_missing")
    else:
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                violations.append(f"replay_support_row_{index}_not_object")
                continue
            if int(row.get("interior_site_count", 0)) <= 0:
                violations.append(f"replay_support_row_{index}_interior_not_positive")
            if control_shape and tuple(row.get("shape") or []) == control_shape:
                violations.append(f"replay_support_row_{index}_uses_zero_interior_control_shape")
            if row.get("dense_state_closure_used") is not False or row.get("dense_environment_closure_used") is not False:
                violations.append(f"replay_support_row_{index}_dense_closure_flag_not_false")
    if not isinstance(graveyard, dict):
        violations.append("replay_graveyard_missing")
    else:
        zero = graveyard.get("GC_zero_interior_shape_blocked_control")
        if not isinstance(zero, dict):
            violations.append("replay_zero_interior_control_missing")
        else:
            if zero.get("control_status") != "blocked_control_only":
                violations.append("replay_zero_interior_control_status_not_blocked")
            if int(zero.get("interior_site_count", -1)) != 0:
                violations.append("replay_zero_interior_control_interior_not_zero")
            if control_shape and tuple(zero.get("shape") or []) != control_shape:
                violations.append("replay_zero_interior_control_shape_mismatch")
    return violations


def validate_receipt(path: Path, transition_artifact: Path | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {
        "path": str(path),
        "pass": True,
        "missing_fields": [],
        "stage_leaks": [],
        "violations": [],
    }
    try:
        data = _load_json(path)
    except Exception as exc:  # pragma: no cover - defensive CLI path
        row["pass"] = False
        row["violations"].append(f"json_load_failed: {exc!r}")
        return row
    if not isinstance(data, dict):
        row["pass"] = False
        row["violations"].append("receipt root is not a JSON object")
        return row

    missing = [field for field in LEGO_REQUIRED_FIELDS if not _has_field(data, field)]
    leaks = _leak_rows(data)
    if missing:
        row["missing_fields"] = missing
        row["violations"].append("missing_current_lego_minimal_fields")
    if leaks:
        row["stage_leaks"] = leaks
        row["violations"].append("downstream_stage_leak_in_next_or_eligible_field")
    if data.get("all_pass") is not True:
        row["violations"].append("receipt_all_pass_not_true")
    if data.get("promotion_allowed") is True:
        row["violations"].append("promotion_allowed_true_for_active_level_receipt")
    if data.get("classification") not in {"formal_scout", "canonical", "tool_lego_fit_probe"}:
        row["violations"].append("classification_missing_or_not_admissible_for_active_level")
    if transition_artifact is not None:
        target = str(transition_artifact)
        for field in ("dependency_receipts", "required_inputs", "data_or_artifact_dependencies"):
            if _contains_path(data.get(field), target):
                row["violations"].append(f"receipt_lists_active_transition_artifact_in_{field}")
    row["violations"].extend(_validate_boundary_projection_shape_bond_replay(data))

    row["classification"] = data.get("classification")
    row["promotion_allowed"] = data.get("promotion_allowed")
    row["all_pass_field"] = data.get("all_pass")
    row["pass"] = not row["violations"]
    return row


def _frontier_rows(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    if isinstance(data, dict):
        rows = data.get("rows") or data.get("frontier_rows") or data.get("matrix")
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
    return []


def validate_frontier_matrix(path: Path | None, min_complete: int, require: bool) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(path) if path else None,
        "required": require,
        "pass": True,
        "violations": [],
        "row_count": 0,
        "contract_complete_rows": 0,
        "rows_missing_fields": [],
    }
    if path is None:
        if require:
            result["pass"] = False
            result["violations"].append("frontier_matrix_required_but_not_provided")
        return result
    if not path.exists():
        result["pass"] = False
        result["violations"].append("frontier_matrix_path_missing")
        return result
    try:
        data = _load_json(path)
    except Exception as exc:  # pragma: no cover - defensive CLI path
        result["pass"] = False
        result["violations"].append(f"frontier_matrix_json_load_failed: {exc!r}")
        return result

    rows = _frontier_rows(data)
    result["row_count"] = len(rows)
    for index, row in enumerate(rows):
        missing = [field for field in FRONTIER_ROW_REQUIRED_FIELDS if not row.get(field)]
        if missing:
            result["rows_missing_fields"].append({"index": index, "missing_fields": missing})
        if str(row.get("status", "")).strip().lower() in CONTRACT_COMPLETE_STATUSES:
            result["contract_complete_rows"] += 1
    if not rows:
        result["violations"].append("frontier_matrix_has_no_rows")
    if result["rows_missing_fields"]:
        result["violations"].append("frontier_matrix_rows_missing_required_fields")
    if result["contract_complete_rows"] < min_complete:
        result["violations"].append(f"frontier_matrix_contract_complete_rows_lt_{min_complete}")
    if result["contract_complete_rows"] >= min_complete:
        action = data.get("post_threshold_action")
        next_action = data.get("next_controller_action")
        if action not in POST_THRESHOLD_ACTIONS:
            result["violations"].append("frontier_matrix_missing_nonstop_post_threshold_action")
        geometry = data.get("working_geometry")
        if not isinstance(geometry, dict):
            result["violations"].append("frontier_matrix_working_geometry_missing")
        else:
            missing_geometry = [
                field for field in WORKING_GEOMETRY_FIELDS
                if geometry.get(field) in (None, "", [], {})
            ]
            if missing_geometry:
                result["violations"].append(
                    "frontier_matrix_working_geometry_fields_missing:"
                    + ",".join(missing_geometry)
                )
        if action == "write_transition_artifact" and not data.get("transition_artifact_path"):
            result["violations"].append("frontier_matrix_transition_artifact_path_missing")
        if action == "continue_active_level" and not data.get("next_in_level_packet_set"):
            result["violations"].append("frontier_matrix_next_in_level_packet_set_missing")
        if action == "blocked_with_repair" and not data.get("blocked_reason_or_repair_path"):
            result["violations"].append("frontier_matrix_blocked_repair_path_missing")
        if action == "blocked_with_repair" and data.get("blocked_reason_or_repair_path"):
            blocker = validate_blocker_artifact(Path(str(data["blocked_reason_or_repair_path"])), require=True)
            result["blocker_artifact"] = blocker
            if not blocker["pass"]:
                result["violations"].append("frontier_matrix_blocker_artifact_invalid")
        if not next_action:
            result["violations"].append("frontier_matrix_next_controller_action_missing")
    result["pass"] = not result["violations"]
    return result


def _path_exists_from_cwd(path_value: Any) -> bool:
    if not isinstance(path_value, str) or not path_value:
        return False
    return Path(path_value).exists()


def _json_text(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str).lower()


def _receipt_launch_surfaces(data: Any) -> set[str]:
    surfaces: set[str] = set()
    if not isinstance(data, dict):
        return surfaces
    launch = data.get("launch_surface")
    if isinstance(launch, str) and launch:
        surfaces.add(launch)
    children = data.get("children")
    if isinstance(children, list):
        for child in children:
            if not isinstance(child, dict):
                continue
            child_launch = child.get("launch_surface")
            if isinstance(child_launch, str) and child_launch:
                surfaces.add(child_launch)
    return surfaces


def _receipt_model_text(data: Any) -> str:
    if not isinstance(data, dict):
        return ""
    fields = [
        str(data.get(field, ""))
        for field in ("model", "model_name", "provider", "runtime", "pool")
    ]
    children = data.get("children")
    if isinstance(children, list):
        for child in children:
            if isinstance(child, dict):
                fields.extend(
                    str(child.get(field, ""))
                    for field in ("model", "model_name", "provider", "runtime", "pool")
                )
    return " ".join(fields).lower()


def _provider_receipt_violations(
    *,
    kind: str,
    field: str,
    path_value: Any,
    allowed_surfaces: set[str],
    require_completed: bool,
) -> list[str]:
    if not isinstance(path_value, str) or not path_value:
        return [f"{kind}_provider_{field}_missing"]
    path = Path(path_value)
    if not path.exists():
        return [f"{kind}_provider_{field}_path_missing"]
    try:
        data = _load_json(path)
    except Exception as exc:  # pragma: no cover - defensive CLI path
        return [f"{kind}_provider_{field}_json_load_failed:{exc!r}"]
    if not isinstance(data, dict):
        return [f"{kind}_provider_{field}_not_json_object"]

    violations: list[str] = []
    text = _json_text(data)
    for marker in PROVIDER_CLI_MARKERS:
        if marker in text:
            violations.append(f"{kind}_provider_{field}_contains_cli_or_omx_marker:{marker.strip()}")
    surfaces = _receipt_launch_surfaces(data)
    if not surfaces.intersection(allowed_surfaces):
        violations.append(f"{kind}_provider_{field}_missing_direct_api_launch_surface")
    model_text = _receipt_model_text(data)
    if kind == "gemini" and "gemini" not in model_text:
        violations.append(f"{kind}_provider_{field}_model_metadata_missing")
    if kind in {"grok", "xai"} and not ({"grok", "xai"} & set(model_text.split())) and "grok" not in model_text and "xai" not in model_text:
        violations.append(f"{kind}_provider_{field}_model_metadata_missing")
    if require_completed and str(data.get("status", "")).strip().lower() != "completed":
        violations.append(f"{kind}_provider_{field}_status_not_completed")
    return violations


def validate_blocker_artifact(path: Path | None, require: bool) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(path) if path else None,
        "required": require,
        "pass": True,
        "violations": [],
        "missing_fields": [],
    }
    if path is None:
        if require:
            result["pass"] = False
            result["violations"].append("blocker_artifact_required_but_not_provided")
        return result
    if not path.exists():
        result["pass"] = False
        result["violations"].append("blocker_artifact_path_missing")
        return result
    try:
        data = _load_json(path)
    except Exception as exc:  # pragma: no cover - defensive CLI path
        result["pass"] = False
        result["violations"].append(f"blocker_artifact_json_load_failed: {exc!r}")
        return result
    if not isinstance(data, dict):
        result["pass"] = False
        result["violations"].append("blocker_artifact_root_is_not_json_object")
        return result

    missing = [field for field in BLOCKER_REQUIRED_FIELDS if data.get(field) in (None, "", [], {})]
    if missing:
        result["missing_fields"] = missing
        result["violations"].append("blocker_artifact_missing_required_fields")
    if data.get("kind") != "blocked_reason":
        result["violations"].append("blocker_artifact_kind_not_blocked_reason")
    if data.get("not_a_stop") is not True:
        result["violations"].append("blocker_artifact_not_a_stop_not_true")
    blocker_map = data.get("blocker_map")
    if not isinstance(blocker_map, dict):
        result["violations"].append("blocker_artifact_blocker_map_missing")
    else:
        missing_map = [field for field in BLOCKER_MAP_REQUIRED_FIELDS if blocker_map.get(field) in (None, "", [], {})]
        if missing_map:
            result["violations"].append("blocker_artifact_blocker_map_fields_missing:" + ",".join(missing_map))
    latest = data.get("latest_admitted_packet")
    if not isinstance(latest, dict):
        result["violations"].append("blocker_artifact_latest_packet_missing")
    else:
        missing_latest = [field for field in LATEST_PACKET_REQUIRED_FIELDS if latest.get(field) in (None, "", [], {})]
        if missing_latest:
            result["violations"].append("blocker_artifact_latest_packet_fields_missing:" + ",".join(missing_latest))
        for field in ("source_path", "result_path"):
            if latest.get(field) and not Path(str(latest[field])).exists():
                result["violations"].append(f"blocker_artifact_latest_packet_{field}_missing")
    downstream = data.get("downstream_consumers_still_blocked")
    if not isinstance(downstream, list) or not downstream:
        result["violations"].append("blocker_artifact_downstream_consumers_missing")
    result["pass"] = not result["violations"]
    return result


def _transition_has_progress(data: dict[str, Any]) -> bool:
    for field in TRANSITION_PROGRESS_FIELDS:
        value = data.get(field)
        if value in (None, "", [], {}):
            continue
        if field.endswith("_path") and isinstance(value, str):
            return _path_exists_from_cwd(value)
        return True
    return False


def _transition_wizard_status(data: dict[str, Any]) -> str | None:
    wizard = data.get("wizard_v4_2") or data.get("wizard")
    if isinstance(wizard, dict):
        status = wizard.get("status")
        if isinstance(status, str) and status.upper() in WIZARD_STATUS_VALUES:
            has_receipt = any(
                wizard.get(field)
                for field in (
                    "run_root",
                    "receipt_path",
                    "compiled_output_path",
                    "blocked_reason",
                )
            )
            if has_receipt:
                return status.upper()
    status = data.get("wizard_status")
    if isinstance(status, str) and status.upper() in WIZARD_STATUS_VALUES:
        has_receipt = any(
            data.get(field)
            for field in (
                "wizard_run_root",
                "wizard_receipt_path",
                "wizard_compiled_output_path",
                "wizard_blocked_reason",
            )
        )
        if has_receipt:
            return status.upper()
    return None


def _pool_key(pool: Any) -> str | None:
    if not isinstance(pool, dict):
        return None
    for field in ("model", "model_id", "pool", "runtime", "name"):
        value = pool.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _pool_status(pool: Any) -> str:
    if not isinstance(pool, dict):
        return ""
    value = pool.get("status")
    return str(value).strip().lower() if value is not None else ""


def _provider_kind(pool: dict[str, Any]) -> str | None:
    text = " ".join(
        str(pool.get(field, "")).lower()
        for field in ("pool", "model", "model_id", "runtime", "name")
    )
    if "gemini" in text:
        return "gemini"
    if "grok" in text:
        return "grok"
    if "xai" in text:
        return "xai"
    return None


def _provider_pool_violations(pool: dict[str, Any]) -> list[str]:
    kind = _provider_kind(pool)
    if kind is None:
        return []
    status = _pool_status(pool)
    if status not in PARALLELISM_POOL_ATTEMPTED:
        return []
    violations: list[str] = []
    launch = pool.get("launch_surface")
    allowed_surfaces = PROVIDER_LAUNCH_SURFACES[kind]
    if launch not in allowed_surfaces:
        violations.append(f"{kind}_provider_launch_surface_invalid")
    require_completed = status in PARALLELISM_POOL_COMPLETED
    for field in ("receipt", "child_receipt"):
        violations.extend(
            _provider_receipt_violations(
                kind=kind,
                field=field,
                path_value=pool.get(field),
                allowed_surfaces=allowed_surfaces,
                require_completed=require_completed,
            )
        )
    return violations


def _parallelism_blockers(parallelism: dict[str, Any]) -> list[Any]:
    blockers = parallelism.get("blockers")
    if isinstance(blockers, list):
        return [item for item in blockers if item not in (None, "", [], {})]
    if isinstance(blockers, str) and blockers.strip():
        return [blockers]
    blocker = parallelism.get("blocked_reason") or parallelism.get("blocker")
    if isinstance(blocker, str) and blocker.strip():
        return [blocker]
    return []


def validate_multi_model_parallelism(
    data: dict[str, Any],
    require: bool,
    min_model_pools: int,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "required": require,
        "pass": True,
        "violations": [],
        "status": None,
        "attempted_model_pools": 0,
        "completed_model_pools": 0,
    }
    parallelism = data.get("multi_model_parallelism") or data.get("parallelism")
    if not isinstance(parallelism, dict):
        if require:
            result["pass"] = False
            result["violations"].append("multi_model_parallelism_missing")
        return result

    status = parallelism.get("status")
    if isinstance(status, str):
        status = status.strip().lower()
    result["status"] = status
    if status not in PARALLELISM_STATUS_VALUES:
        result["violations"].append("multi_model_parallelism_status_invalid")

    pools = (
        parallelism.get("model_pools")
        or parallelism.get("model_pools_attempted")
        or parallelism.get("worker_pools")
        or []
    )
    if not isinstance(pools, list):
        pools = []
    attempted: set[str] = set()
    completed: set[str] = set()
    provider_violations: list[str] = []
    for pool in pools:
        if not isinstance(pool, dict):
            continue
        provider_violations.extend(_provider_pool_violations(pool))
        if _provider_kind(pool) is None:
            continue
        key = _pool_key(pool)
        if key is None:
            continue
        pool_status = _pool_status(pool)
        if pool_status in PARALLELISM_POOL_ATTEMPTED:
            attempted.add(key)
        if pool_status in PARALLELISM_POOL_COMPLETED:
            completed.add(key)
    result["attempted_model_pools"] = len(attempted)
    result["completed_model_pools"] = len(completed)
    result["provider_violations"] = provider_violations
    if provider_violations:
        result["violations"].append("multi_model_parallelism_provider_surface_invalid")

    independent = (
        parallelism.get("independent_packets")
        or parallelism.get("independent_routes")
        or parallelism.get("parallel_packets")
        or []
    )
    if status != "blocked" and (not isinstance(independent, list) or not independent):
        result["violations"].append("multi_model_parallelism_independent_packets_missing")

    blockers = _parallelism_blockers(parallelism)
    if status == "blocked":
        if not blockers:
            result["violations"].append("multi_model_parallelism_blocked_without_reason")
    elif status == "partial":
        if len(attempted) < min_model_pools and not blockers:
            result["violations"].append(
                f"multi_model_parallelism_attempted_model_pools_lt_{min_model_pools}"
            )
        if not blockers:
            result["violations"].append("multi_model_parallelism_partial_without_blockers")
    elif status == "max_used":
        if len(completed) < min_model_pools:
            result["violations"].append(
                f"multi_model_parallelism_completed_model_pools_lt_{min_model_pools}"
            )
    result["pass"] = not result["violations"]
    return result


def validate_transition_artifact(
    path: Path | None,
    require: bool,
    require_progress: bool,
    require_wizard: bool,
    require_parallelism: bool,
    min_model_pools: int,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(path) if path else None,
        "required": require,
        "pass": True,
        "violations": [],
        "missing_fields": [],
        "decision": None,
        "wizard_status": None,
        "multi_model_parallelism": {
            "required": require_parallelism,
            "pass": True,
            "violations": [],
            "status": None,
            "attempted_model_pools": 0,
            "completed_model_pools": 0,
        },
        "blocker_artifact": {
            "required": False,
            "pass": True,
            "violations": [],
        },
    }
    if path is None:
        if require:
            result["pass"] = False
            result["violations"].append("transition_artifact_required_but_not_provided")
        return result
    if not path.exists():
        result["pass"] = False
        result["violations"].append("transition_artifact_path_missing")
        return result
    try:
        data = _load_json(path)
    except Exception as exc:  # pragma: no cover - defensive CLI path
        result["pass"] = False
        result["violations"].append(f"transition_artifact_json_load_failed: {exc!r}")
        return result
    if not isinstance(data, dict):
        result["pass"] = False
        result["violations"].append("transition_artifact_root_is_not_json_object")
        return result

    missing = [
        field for field in TRANSITION_REQUIRED_FIELDS
        if data.get(field) in (None, "", [], {})
    ]
    if missing:
        result["missing_fields"] = missing
        result["violations"].append("transition_artifact_missing_required_fields")
    decision = data.get("decision")
    result["decision"] = decision
    if decision not in TRANSITION_DECISIONS:
        result["violations"].append("transition_artifact_decision_invalid")
    if data.get("not_a_stop") is not True:
        result["violations"].append("transition_artifact_not_a_stop_not_true")
    if data.get("validator_all_pass") is not True:
        result["violations"].append("transition_artifact_validator_all_pass_not_true")
    if not isinstance(data.get("working_geometry"), dict):
        result["violations"].append("transition_artifact_working_geometry_missing")
    if require_progress and decision in {"open_next_level", "continue_active_level"}:
        if not _transition_has_progress(data):
            result["violations"].append(
                "transition_missing_next_packet_progress_or_continuation_artifact"
            )
    if decision == "blocked":
        blocker_path = data.get("blocked_reason_or_repair_path")
        blocker = validate_blocker_artifact(Path(str(blocker_path)) if blocker_path else None, require=True)
        result["blocker_artifact"] = blocker
        if not blocker["pass"]:
            result["violations"].append("transition_blocker_artifact_invalid")
    if require_wizard:
        wizard_status = _transition_wizard_status(data)
        result["wizard_status"] = wizard_status
        if wizard_status is None:
            result["violations"].append(
                "transition_missing_wizard_v4_2_receipt_or_blocker"
            )
    parallelism = validate_multi_model_parallelism(
        data,
        require_parallelism,
        min_model_pools,
    )
    result["multi_model_parallelism"] = parallelism
    if not parallelism["pass"]:
        result["violations"].append("transition_multi_model_parallelism_invalid")
    result["pass"] = not result["violations"]
    return result


def validate_frontier_transition_consistency(
    frontier_path: Path | None,
    transition_path: Path | None,
    require: bool,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "required": require,
        "pass": True,
        "violations": [],
        "frontier_blocker_path": None,
        "transition_blocker_path": None,
    }
    if frontier_path is None or transition_path is None:
        if require:
            result["pass"] = False
            result["violations"].append("frontier_transition_consistency_inputs_missing")
        return result
    if not frontier_path.exists() or not transition_path.exists():
        if require:
            result["pass"] = False
            result["violations"].append("frontier_transition_consistency_paths_missing")
        return result
    try:
        frontier = _load_json(frontier_path)
        transition = _load_json(transition_path)
    except Exception as exc:  # pragma: no cover - defensive CLI path
        result["pass"] = False
        result["violations"].append(f"frontier_transition_consistency_json_load_failed:{exc!r}")
        return result
    if not isinstance(frontier, dict) or not isinstance(transition, dict):
        result["pass"] = False
        result["violations"].append("frontier_transition_consistency_root_not_object")
        return result

    if frontier.get("post_threshold_action") == "blocked_with_repair":
        frontier_blocker = frontier.get("blocked_reason_or_repair_path")
        transition_blocker = transition.get("blocked_reason_or_repair_path")
        result["frontier_blocker_path"] = frontier_blocker
        result["transition_blocker_path"] = transition_blocker
        if transition.get("decision") != "blocked":
            result["violations"].append("frontier_blocked_with_repair_transition_decision_not_blocked")
        if not frontier_blocker:
            result["violations"].append("frontier_blocked_with_repair_blocker_path_missing")
        if not transition_blocker:
            result["violations"].append("transition_blocked_repair_path_missing")
        if frontier_blocker and transition_blocker and frontier_blocker != transition_blocker:
            result["violations"].append("frontier_transition_blocker_path_mismatch")
        if frontier_blocker:
            blocker = validate_blocker_artifact(Path(str(frontier_blocker)), require=True)
            result["blocker_artifact"] = blocker
            if not blocker["pass"]:
                result["violations"].append("frontier_transition_blocker_artifact_invalid")

    result["pass"] = not result["violations"]
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipts", nargs="*", type=Path, help="active-level result JSON receipts")
    parser.add_argument("--frontier-matrix", type=Path, default=None)
    parser.add_argument("--require-frontier-matrix", action="store_true")
    parser.add_argument("--min-contract-complete-rows", type=int, default=3)
    parser.add_argument("--transition-artifact", type=Path, default=None)
    parser.add_argument("--require-transition-artifact", action="store_true")
    parser.add_argument("--require-transition-progress", action="store_true")
    parser.add_argument("--require-wizard-receipt", action="store_true")
    parser.add_argument("--require-multi-model-parallelism", action="store_true")
    parser.add_argument("--min-model-pools", type=int, default=2)
    args = parser.parse_args()

    receipt_rows = [
        validate_receipt(path, args.transition_artifact)
        for path in args.receipts
    ]
    frontier = validate_frontier_matrix(
        args.frontier_matrix,
        args.min_contract_complete_rows,
        args.require_frontier_matrix,
    )
    transition = validate_transition_artifact(
        args.transition_artifact,
        args.require_transition_artifact,
        args.require_transition_progress,
        args.require_wizard_receipt,
        args.require_multi_model_parallelism,
        args.min_model_pools,
    )
    consistency = validate_frontier_transition_consistency(
        args.frontier_matrix,
        args.transition_artifact,
        args.require_frontier_matrix and args.require_transition_artifact,
    )
    all_pass = (
        all(row["pass"] for row in receipt_rows)
        and frontier["pass"]
        and transition["pass"]
        and consistency["pass"]
    )
    report = {
        "kind": "bounded_max_exploration_validation",
        "all_pass": all_pass,
        "receipt_count": len(receipt_rows),
        "receipt_rows": receipt_rows,
        "frontier_matrix": frontier,
        "transition_artifact": transition,
        "frontier_transition_consistency": consistency,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
