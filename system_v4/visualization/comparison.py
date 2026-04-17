from __future__ import annotations

import json
from pathlib import Path

from system_v4.visualization.inspection import inspect_run_dir


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _final_entity_scalars_by_entity(run_dir: Path) -> dict:
    frame_paths = sorted((Path(run_dir) / "frames").glob("*.json"))
    if not frame_paths:
        return {}
    final_frame = _load_json(frame_paths[-1])
    entities = final_frame.get("entities", [])
    return {
        str(entity.get("entity_id", f"entity_{index}")): dict(entity.get("scalars", {}))
        for index, entity in enumerate(entities)
    }


def _final_entity_scalars(run_dir: Path) -> dict:
    scalars_by_entity = _final_entity_scalars_by_entity(run_dir)
    if "carrier_0" in scalars_by_entity:
        return scalars_by_entity["carrier_0"]
    if scalars_by_entity:
        return scalars_by_entity[sorted(scalars_by_entity)[0]]
    return {}


def _diff_mapping(left: dict, right: dict) -> dict:
    keys = sorted(set(left) | set(right))
    diff: dict[str, dict] = {}
    for key in keys:
        left_value = left.get(key)
        right_value = right.get(key)
        entry = {"left": left_value, "right": right_value}
        if isinstance(left_value, (int, float)) and isinstance(right_value, (int, float)):
            entry["delta"] = float(right_value) - float(left_value)
        diff[key] = entry
    return diff


def compare_run_dirs(left_run: Path, right_run: Path) -> dict:
    left_run = Path(left_run)
    right_run = Path(right_run)

    left = inspect_run_dir(left_run)
    right = inspect_run_dir(right_run)
    left_scalars = _final_entity_scalars(left_run)
    right_scalars = _final_entity_scalars(right_run)
    left_scalars_by_entity = _final_entity_scalars_by_entity(left_run)
    right_scalars_by_entity = _final_entity_scalars_by_entity(right_run)

    return {
        "left_run_id": left["run_id"],
        "right_run_id": right["run_id"],
        "left_sim_name": left["sim_name"],
        "right_sim_name": right["sim_name"],
        "status_label": {
            "left": left["status_label"],
            "right": right["status_label"],
        },
        "claim_state": {
            "left": left.get("claim_state"),
            "right": right.get("claim_state"),
        },
        "promotion_status": {
            "left": left.get("promotion_status"),
            "right": right.get("promotion_status"),
        },
        "lane": {
            "left": left.get("lane"),
            "right": right.get("lane"),
        },
        "layer": {
            "left": left.get("layer"),
            "right": right.get("layer"),
        },
        "probe_family": {
            "left": left.get("probe_family"),
            "right": right.get("probe_family"),
        },
        "witness_type": {
            "left": left.get("witness_type"),
            "right": right.get("witness_type"),
        },
        "admission_stage": {
            "left": left.get("admission_stage"),
            "right": right.get("admission_stage"),
        },
        "admission_stage_index": {
            "left": left.get("admission_stage_index"),
            "right": right.get("admission_stage_index"),
        },
        "promotion_target_stage": {
            "left": left.get("promotion_target_stage"),
            "right": right.get("promotion_target_stage"),
        },
        "validation_ok": {
            "left": left["validation_ok"],
            "right": right["validation_ok"],
        },
        "summary_all_pass": {
            "left": left["summary_all_pass"],
            "right": right["summary_all_pass"],
        },
        "frame_count": {
            "left": left["frame_count"],
            "right": right["frame_count"],
            "delta": int(right["frame_count"]) - int(left["frame_count"]),
        },
        "entity_count": {
            "left": left.get("entity_count", 0),
            "right": right.get("entity_count", 0),
            "delta": int(right.get("entity_count", 0)) - int(left.get("entity_count", 0)),
        },
        "mesh_patch_count": {
            "left": left.get("mesh_patch_count", 0),
            "right": right.get("mesh_patch_count", 0),
            "delta": int(right.get("mesh_patch_count", 0)) - int(left.get("mesh_patch_count", 0)),
        },
        "transition_meta_count": {
            "left": left.get("transition_meta_count", 0),
            "right": right.get("transition_meta_count", 0),
            "delta": int(right.get("transition_meta_count", 0)) - int(left.get("transition_meta_count", 0)),
        },
        "capabilities": {
            "left": left["capabilities"],
            "right": right["capabilities"],
            "only_left": sorted(set(left["capabilities"]) - set(right["capabilities"])),
            "only_right": sorted(set(right["capabilities"]) - set(left["capabilities"])),
        },
        "overlays": {
            "left": left["overlays"],
            "right": right["overlays"],
            "only_left": sorted(set(left["overlays"]) - set(right["overlays"])),
            "only_right": sorted(set(right["overlays"]) - set(left["overlays"])),
        },
        "path_kind": {
            "left": left["path_kind"],
            "right": right["path_kind"],
        },
        "projected_path_kind": {
            "left": left["projected_path_kind"],
            "right": right["projected_path_kind"],
        },
        "expected_invariants": _diff_mapping(left["expected_invariants"], right["expected_invariants"]),
        "measured_invariants": _diff_mapping(left["measured_invariants"], right["measured_invariants"]),
        "final_scalars": _diff_mapping(left_scalars, right_scalars),
        "final_scalars_by_entity": {
            entity_id: _diff_mapping(left_scalars_by_entity.get(entity_id, {}), right_scalars_by_entity.get(entity_id, {}))
            for entity_id in sorted(set(left_scalars_by_entity) | set(right_scalars_by_entity))
        },
        "validation_errors": {
            "left": left["validation_errors"],
            "right": right["validation_errors"],
        },
        "validation_warnings": {
            "left": left["validation_warnings"],
            "right": right["validation_warnings"],
        },
    }
