from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from system_v4.visualization.capabilities import (
    FIBER_PHASE,
    FIBER_SAMPLES,
    FRAME,
    HOLONOMY,
    MESH_GEOMETRY,
    S3_STATE,
    TRANSITION_META,
    TRANSPORT_PATH,
)
from system_v4.visualization.schema_v1 import (
    ADMISSION_STAGE_LABELS,
    ADMISSION_STAGE_NEXT,
    CLAIM_STATE_LABELS,
    MESH_PATCH_ENTITY_KIND,
    POINT_FRAME_ENTITY_KIND,
    PROMOTION_STATUS_LABELS,
    PUBLIC_STATUS_LABELS,
    SCHEMA_VERSION,
)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _is_vector3(value: object) -> bool:
    if not isinstance(value, list) or len(value) != 3:
        return False
    try:
        [float(x) for x in value]
    except Exception:
        return False
    return True


def _is_vector4(value: object) -> bool:
    if not isinstance(value, list) or len(value) != 4:
        return False
    try:
        [float(x) for x in value]
    except Exception:
        return False
    return True


def _is_vector3_list(value: object) -> bool:
    return isinstance(value, list) and all(_is_vector3(item) for item in value)


def _iter_entities(frame: dict) -> list[dict]:
    entities = frame.get("entities", [])
    if not isinstance(entities, list):
        return []
    return entities


def _is_index_pair_list(value: object) -> bool:
    if not isinstance(value, list):
        return False
    for item in value:
        if not isinstance(item, list) or len(item) != 2:
            return False
        if not all(isinstance(index, int) for index in item):
            return False
    return True


def _is_index_triple_list(value: object) -> bool:
    if not isinstance(value, list):
        return False
    for item in value:
        if not isinstance(item, list) or len(item) != 3:
            return False
        if not all(isinstance(index, int) for index in item):
            return False
    return True


def _is_transition_meta(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    neighbor_patch_id = value.get("neighbor_patch_id")
    transition_kind = value.get("transition_kind")
    seam_edges = value.get("seam_edges")
    if not isinstance(neighbor_patch_id, str) or not neighbor_patch_id:
        return False
    if not isinstance(transition_kind, str) or not transition_kind:
        return False
    if seam_edges is not None and not _is_index_pair_list(seam_edges):
        return False
    return True


def _is_non_empty_string_list(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) and item for item in value)


def _is_witness_event(value: object) -> bool:
    return isinstance(value, dict) and isinstance(value.get("event_kind"), str) and bool(value.get("event_kind"))


def validate_run_dir(run_dir: Path) -> dict:
    run_dir = Path(run_dir)
    errors: list[str] = []
    warnings: list[str] = []

    manifest_path = run_dir / "run_manifest.json"
    scene_path = run_dir / "scene.json"
    summary_path = run_dir / "summary.json"
    witness_trace_path = run_dir / "witness_trace.json"
    frames_dir = run_dir / "frames"

    for required in (manifest_path, scene_path, summary_path, witness_trace_path, frames_dir):
        if not required.exists():
            errors.append(f"missing required path: {required.name}")

    if errors:
        return {"ok": False, "errors": errors, "warnings": warnings}

    manifest = _load_json(manifest_path)
    scene = _load_json(scene_path)
    _load_json(summary_path)
    witness_trace = _load_json(witness_trace_path)
    frame_paths = sorted(frames_dir.glob("*.json"))
    if not frame_paths:
        errors.append("no frame JSON files present")
        return {"ok": False, "errors": errors, "warnings": warnings}

    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"unsupported schema version: {manifest.get('schema_version')}")

    if not isinstance(manifest.get("constraint_set"), str) or not manifest.get("constraint_set"):
        errors.append("manifest missing valid constraint_set")
    if not isinstance(manifest.get("probe_family"), str) or not manifest.get("probe_family"):
        errors.append("manifest missing valid probe_family")
    if not isinstance(manifest.get("carrier"), str) or not manifest.get("carrier"):
        errors.append("manifest missing valid carrier")
    if not isinstance(manifest.get("lane"), str) or not manifest.get("lane"):
        errors.append("manifest missing valid lane")
    if not isinstance(manifest.get("layer"), str) or not manifest.get("layer"):
        errors.append("manifest missing valid layer")
    if not isinstance(manifest.get("witness_type"), str) or not manifest.get("witness_type"):
        errors.append("manifest missing valid witness_type")
    if manifest.get("admission_stage") not in ADMISSION_STAGE_LABELS:
        errors.append("manifest admission_stage is invalid")
    admission_stage = manifest.get("admission_stage")
    admission_stage_index = manifest.get("admission_stage_index")
    if isinstance(admission_stage, str) and admission_stage in ADMISSION_STAGE_LABELS:
        expected_index = ADMISSION_STAGE_LABELS.index(admission_stage)
        if admission_stage_index != expected_index:
            errors.append("manifest admission_stage_index does not match admission_stage")
    else:
        expected_index = None
    promotion_target_stage = manifest.get("promotion_target_stage")
    if promotion_target_stage not in ADMISSION_STAGE_LABELS:
        errors.append("manifest promotion_target_stage is invalid")
    elif isinstance(admission_stage, str) and admission_stage in ADMISSION_STAGE_LABELS:
        if promotion_target_stage != ADMISSION_STAGE_NEXT[admission_stage]:
            errors.append("manifest promotion_target_stage must be the next admission stage")
    if manifest.get("status_label") not in PUBLIC_STATUS_LABELS:
        errors.append("manifest status_label must use the public controller status spine")
    if manifest.get("claim_state") not in CLAIM_STATE_LABELS:
        errors.append("manifest claim_state is invalid")
    if manifest.get("promotion_status") not in PROMOTION_STATUS_LABELS:
        errors.append("manifest promotion_status is invalid")
    if manifest.get("promotion_status") == "canonical" and admission_stage != "bridge-claims":
        errors.append("canonical promotion_status is reserved for bridge-claims stage")
    if manifest.get("claim_state") == "proven" and admission_stage != "bridge-claims" and manifest.get("promotion_status") == "canonical":
        errors.append("proven canonical promotion requires bridge-claims stage")
    if not isinstance(manifest.get("geometry_rendering_status"), str) or not manifest.get("geometry_rendering_status"):
        errors.append("manifest missing valid geometry_rendering_status")
    if not _is_non_empty_string_list(manifest.get("negative_controls")):
        errors.append("manifest negative_controls must be a non-empty list of strings")
    if not _is_non_empty_string_list(manifest.get("exclusion_criteria")):
        errors.append("manifest exclusion_criteria must be a non-empty list of strings")
    live_splits = manifest.get("live_splits")
    if live_splits is not None and not _is_non_empty_string_list(live_splits) and live_splits != []:
        errors.append("manifest live_splits must be a list of non-empty strings")
    if not isinstance(manifest.get("witness_trace_id"), str) or not manifest.get("witness_trace_id"):
        errors.append("manifest missing valid witness_trace_id")
    for field_name in (
        "required_negatives",
        "negatives_run",
        "kill_conditions",
        "required_artifacts",
        "artifacts_emitted",
        "eligible_consumers",
        "blocked_consumers",
        "promotion_blockers",
    ):
        if not _is_non_empty_string_list(manifest.get(field_name)):
            errors.append(f"manifest {field_name} must be a non-empty list of strings")
    if not isinstance(manifest.get("pass_rule"), str) or not manifest.get("pass_rule"):
        errors.append("manifest missing valid pass_rule")
    if not isinstance(manifest.get("fail_rule"), str) or not manifest.get("fail_rule"):
        errors.append("manifest missing valid fail_rule")
    lane_admission = manifest.get("lane_admission")
    if not isinstance(lane_admission, dict):
        errors.append("manifest missing valid lane_admission")
    else:
        if lane_admission.get("current_lane") != manifest.get("lane"):
            errors.append("lane_admission current_lane must match manifest lane")
        prereqs = lane_admission.get("prerequisite_lanes")
        if not isinstance(prereqs, list) or not all(isinstance(item, str) and item for item in prereqs):
            errors.append("lane_admission prerequisite_lanes must be a list of non-empty strings")
        if not isinstance(lane_admission.get("admission_rule"), str) or not lane_admission.get("admission_rule"):
            errors.append("lane_admission missing admission_rule")

    witness_suffix = manifest.get("witness_trace_id", "").split("::")[-1]
    if witness_trace.get("witness_trace_id") != witness_suffix:
        errors.append("witness_trace_id mismatch between manifest and witness_trace")
    if witness_trace.get("probe_family") != manifest.get("probe_family"):
        errors.append("witness_trace probe_family must match manifest probe_family")
    if witness_trace.get("constraint_set") != manifest.get("constraint_set"):
        errors.append("witness_trace constraint_set must match manifest constraint_set")
    events = witness_trace.get("events")
    if not isinstance(events, list) or not events:
        errors.append("witness_trace events must be a non-empty list")
    else:
        for event_index, event in enumerate(events):
            if not _is_witness_event(event):
                errors.append(f"witness_trace events[{event_index}] is malformed")
    if not _is_non_empty_string_list(witness_trace.get("negative_controls_run")):
        errors.append("witness_trace negative_controls_run must be a non-empty list of strings")
    exclusion_events = witness_trace.get("exclusion_events")
    if not isinstance(exclusion_events, list):
        errors.append("witness_trace exclusion_events must be a list")

    capabilities = list(manifest.get("capabilities", []))
    previous_step = None
    geometry_type = scene.get("geometry_type")

    if S3_STATE in capabilities:
        projected_spec = scene.get("projected_path_spec")
        if not isinstance(projected_spec, dict):
            errors.append("declares s3_state but scene has no projected_path_spec")
        else:
            if not _is_vector3_list(projected_spec.get("vertices")):
                errors.append("projected_path_spec must contain vector3 vertices")
            offset_xyz = projected_spec.get("offset_xyz")
            if offset_xyz is not None and not _is_vector3(offset_xyz):
                errors.append("projected_path_spec offset_xyz must be a vector3")

    for frame_path in frame_paths:
        frame = _load_json(frame_path)
        step_index = frame.get("step_index")
        if not isinstance(step_index, int):
            errors.append(f"invalid step_index in {frame_path.name}")
            continue
        if previous_step is not None and step_index <= previous_step:
            errors.append("step_index must be strictly increasing")
        previous_step = step_index

        entities = _iter_entities(frame)
        if not entities:
            errors.append(f"{frame_path.name} must contain at least one entity")
            continue

        entity_ids: list[str] = []
        for entity_index, entity in enumerate(entities):
            entity_id = entity.get("entity_id")
            label = f"{frame_path.name} entity[{entity_index}]"
            if not isinstance(entity_id, str) or not entity_id:
                errors.append(f"{label} missing valid entity_id")
                entity_id = f"entity[{entity_index}]"
            entity_ids.append(entity_id)
            label = f"{frame_path.name}::{entity_id}"
            entity_kind = entity.get("entity_kind", POINT_FRAME_ENTITY_KIND)

            if entity_kind == POINT_FRAME_ENTITY_KIND and FRAME in capabilities:
                frame_vectors = entity.get("frame_vectors", {})
                for key in ("tangent", "normal", "binormal"):
                    if not _is_vector3(frame_vectors.get(key)):
                        errors.append(f"{label} missing valid frame vector: {key}")
                if not _is_vector3(entity.get("base_xyz")):
                    errors.append(f"{label} missing valid base_xyz")

            if entity_kind == POINT_FRAME_ENTITY_KIND and TRANSPORT_PATH in capabilities:
                tags = entity.get("tags", {})
                if "arc_id" not in tags and "loop_theta" not in tags:
                    errors.append(f"{label} declares transport_path but has no arc_id or loop_theta tag")

            scalars = entity.get("scalars", {})
            if entity_kind == POINT_FRAME_ENTITY_KIND and HOLONOMY in capabilities and "accumulated_holonomy" not in scalars:
                errors.append(f"{label} declares holonomy but has no accumulated_holonomy scalar")
            if entity_kind == POINT_FRAME_ENTITY_KIND and FIBER_PHASE in capabilities and "fiber_phase" not in scalars:
                errors.append(f"{label} declares fiber_phase but has no fiber_phase scalar")

            if entity_kind == POINT_FRAME_ENTITY_KIND and S3_STATE in capabilities and not _is_vector4(entity.get("s3_point")):
                errors.append(f"{label} declares s3_state but has no valid s3_point")
            if entity_kind == POINT_FRAME_ENTITY_KIND and S3_STATE in capabilities and not _is_vector3(entity.get("projected_s3_xyz")):
                errors.append(f"{label} declares s3_state but has no valid projected_s3_xyz")
            if entity_kind == POINT_FRAME_ENTITY_KIND and FIBER_SAMPLES in capabilities:
                fiber_samples = entity.get("fiber_samples_xyz")
                if not isinstance(fiber_samples, list) or not fiber_samples:
                    errors.append(f"{label} declares fiber_samples but has no fiber_samples_xyz payload")
                elif not all(_is_vector3(sample) for sample in fiber_samples):
                    errors.append(f"{label} fiber_samples_xyz must contain only vector3 entries")

            if entity_kind == POINT_FRAME_ENTITY_KIND:
                base_xyz = entity.get("base_xyz")
                if geometry_type == "unit_sphere" and _is_vector3(base_xyz):
                    base_norm = float(np.linalg.norm(np.array(base_xyz, dtype=float)))
                    if abs(base_norm - 1.0) > 1e-3:
                        errors.append(f"{label} base_xyz is not on the unit sphere")

                s3_point = entity.get("s3_point")
                if _is_vector4(s3_point):
                    s3_norm = float(np.linalg.norm(np.array(s3_point, dtype=float)))
                    if abs(s3_norm - 1.0) > 1e-3:
                        errors.append(f"{label} s3_point is not on the unit sphere")

                tangent_leakage = scalars.get("tangent_leakage")
                if isinstance(tangent_leakage, (float, int)) and abs(float(tangent_leakage)) > 1e-3:
                    warnings.append(f"{label} tangent leakage exceeds threshold")

            if entity_kind == MESH_PATCH_ENTITY_KIND:
                if MESH_GEOMETRY not in capabilities:
                    errors.append(f"{label} uses mesh_patch but manifest lacks mesh_geometry capability")
                points_xyz = entity.get("points_xyz")
                if not _is_vector3_list(points_xyz):
                    errors.append(f"{label} missing valid points_xyz")
                    points_count = 0
                else:
                    points_count = len(points_xyz)

                line_indices = entity.get("line_indices")
                if not _is_index_pair_list(line_indices):
                    errors.append(f"{label} missing valid line_indices")
                elif points_count:
                    for edge_index, pair in enumerate(line_indices):
                        if not all(0 <= index < points_count for index in pair):
                            errors.append(f"{label} line_indices[{edge_index}] references out-of-bounds point")

                cell_indices = entity.get("cell_indices")
                if cell_indices is not None:
                    if not _is_index_triple_list(cell_indices):
                        errors.append(f"{label} cell_indices must be triangle index triples")
                    elif points_count:
                        for cell_index, triple in enumerate(cell_indices):
                            if not all(0 <= index < points_count for index in triple):
                                errors.append(f"{label} cell_indices[{cell_index}] references out-of-bounds point")

                if not isinstance(entity.get("patch_id"), str) or not entity.get("patch_id"):
                    errors.append(f"{label} missing valid patch_id")
                if not isinstance(entity.get("chart_id"), str) or not entity.get("chart_id"):
                    errors.append(f"{label} missing valid chart_id")

                seam_edges = entity.get("seam_edges")
                if seam_edges is not None:
                    if not _is_index_pair_list(seam_edges):
                        errors.append(f"{label} seam_edges must be index pairs")
                    elif points_count:
                        for seam_index, pair in enumerate(seam_edges):
                            if not all(0 <= index < points_count for index in pair):
                                errors.append(f"{label} seam_edges[{seam_index}] references out-of-bounds point")

                chart_neighbors = entity.get("chart_neighbors")
                if chart_neighbors is not None:
                    if not isinstance(chart_neighbors, list) or not all(isinstance(item, str) and item for item in chart_neighbors):
                        errors.append(f"{label} chart_neighbors must be a list of non-empty strings")

                transition_meta = entity.get("transition_meta")
                if transition_meta is not None:
                    if TRANSITION_META not in capabilities:
                        errors.append(f"{label} uses transition_meta but manifest lacks transition_meta capability")
                    elif not isinstance(transition_meta, list) or not transition_meta:
                        errors.append(f"{label} transition_meta must be a non-empty list")
                    else:
                        for transition_index, entry in enumerate(transition_meta):
                            if not _is_transition_meta(entry):
                                errors.append(f"{label} transition_meta[{transition_index}] is malformed")
                                continue
                            transition_seam_edges = entry.get("seam_edges")
                            if transition_seam_edges is not None and points_count:
                                for seam_index, pair in enumerate(transition_seam_edges):
                                    if not all(0 <= index < points_count for index in pair):
                                        errors.append(
                                            f"{label} transition_meta[{transition_index}].seam_edges[{seam_index}] references out-of-bounds point"
                                        )
                        if chart_neighbors is not None:
                            transition_neighbors = {entry["neighbor_patch_id"] for entry in transition_meta if isinstance(entry, dict) and "neighbor_patch_id" in entry}
                            missing_neighbors = sorted(set(chart_neighbors) - transition_neighbors)
                            if missing_neighbors:
                                warnings.append(f"{label} chart_neighbors missing transition_meta entries for: {', '.join(missing_neighbors)}")

                point_scalars = entity.get("point_scalars", {})
                if point_scalars is not None:
                    if not isinstance(point_scalars, dict):
                        errors.append(f"{label} point_scalars must be a mapping")
                    elif points_count:
                        for scalar_name, scalar_values in point_scalars.items():
                            if not isinstance(scalar_values, list) or len(scalar_values) != points_count:
                                errors.append(f"{label} point_scalars[{scalar_name}] length must match points_xyz")

        if len(entity_ids) != len(set(entity_ids)):
            errors.append(f"{frame_path.name} contains duplicate entity_id values")

    if not errors:
        final_frame = _load_json(frame_paths[-1])
        for entity in _iter_entities(final_frame):
            holonomy = entity.get("scalars", {}).get("accumulated_holonomy")
            entity_id = entity.get("entity_id", "unknown")
            if isinstance(holonomy, (float, int)) and abs(abs(float(holonomy)) - (np.pi / 2)) > 5e-2:
                warnings.append(f"final holonomy deviates from expected pi/2 target for {entity_id}")

    return {
        "ok": not errors,
        "schema_version": manifest.get("schema_version"),
        "capabilities": capabilities,
        "frame_count": len(frame_paths),
        "admission_stage": admission_stage,
        "admission_stage_index": admission_stage_index,
        "promotion_target_stage": promotion_target_stage,
        "errors": errors,
        "warnings": warnings,
    }
