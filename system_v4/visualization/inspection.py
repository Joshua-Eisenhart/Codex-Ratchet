from __future__ import annotations

import json
from pathlib import Path

from system_v4.visualization.capabilities import CELL_GEOMETRY, FIBER_SAMPLES, HOLONOMY, MESH_GEOMETRY, S3_STATE, SEAM_MARKERS, TRANSITION_META
from system_v4.visualization.schema_v1 import MESH_PATCH_ENTITY_KIND
from system_v4.visualization.validator import validate_run_dir


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _primary_entity(entities: list[dict]) -> dict:
    for entity in entities:
        if entity.get("entity_id") == "carrier_0":
            return entity
    return entities[0] if entities else {}


def _final_entity_scalars_by_entity(frames_dir: Path) -> dict:
    frame_paths = sorted(frames_dir.glob("*.json"))
    if not frame_paths:
        return {}
    final_frame = _load_json(frame_paths[-1])
    entities = final_frame.get("entities", [])
    if not entities:
        return {}
    return {
        str(entity.get("entity_id", f"entity_{index}")): dict(entity.get("scalars", {}))
        for index, entity in enumerate(entities)
    }


def _final_entity_scalars(frames_dir: Path) -> dict:
    scalars_by_entity = _final_entity_scalars_by_entity(frames_dir)
    if "carrier_0" in scalars_by_entity:
        return scalars_by_entity["carrier_0"]
    if scalars_by_entity:
        return scalars_by_entity[sorted(scalars_by_entity)[0]]
    return {}


def inspect_run_dir(run_dir: Path) -> dict:
    run_dir = Path(run_dir)
    manifest_path = run_dir / "run_manifest.json"
    scene_path = run_dir / "scene.json"
    summary_path = run_dir / "summary.json"
    witness_trace_path = run_dir / "witness_trace.json"
    frames_dir = run_dir / "frames"
    manifest = _load_json(run_dir / "run_manifest.json")
    scene = _load_json(run_dir / "scene.json")
    summary = _load_json(run_dir / "summary.json")
    witness_trace = _load_json(run_dir / "witness_trace.json")
    frames = sorted(frames_dir.glob("*.json"))
    validation = validate_run_dir(run_dir)
    final_frame = _load_json(frames[-1]) if frames else {}
    final_entities = final_frame.get("entities", [])
    primary_entity = _primary_entity(final_entities)

    capabilities = list(manifest.get("capabilities", []))
    overlays = ["base_path", "frame_glyphs"]
    if HOLONOMY in capabilities:
        overlays.append("holonomy_trace")
    if FIBER_SAMPLES in capabilities:
        overlays.append("fiber_ring")
    if S3_STATE in capabilities and scene.get("projected_path_spec"):
        overlays.append("projected_s3_path")
    if MESH_GEOMETRY in capabilities:
        overlays.append("mesh_patch_lines")
    if CELL_GEOMETRY in capabilities:
        overlays.append("mesh_patch_cells")
    if SEAM_MARKERS in capabilities:
        overlays.append("seam_edges")
    if TRANSITION_META in capabilities:
        overlays.append("transition_annotations")

    expected_invariants = scene.get("expected_invariants", {})
    measured_invariants = summary.get("invariants", {})

    return {
        "run_dir": str(run_dir),
        "status_label": manifest.get("status_label", "exists"),
        "run_id": manifest.get("run_id"),
        "sim_name": manifest.get("sim_name"),
        "schema_version": manifest.get("schema_version"),
        "constraint_set": manifest.get("constraint_set"),
        "probe_family": manifest.get("probe_family"),
        "carrier": manifest.get("carrier"),
        "lane": manifest.get("lane"),
        "layer": manifest.get("layer"),
        "witness_type": manifest.get("witness_type"),
        "admission_stage": manifest.get("admission_stage"),
        "admission_stage_index": manifest.get("admission_stage_index"),
        "promotion_target_stage": manifest.get("promotion_target_stage"),
        "claim_state": manifest.get("claim_state"),
        "promotion_status": manifest.get("promotion_status"),
        "geometry_rendering_status": manifest.get("geometry_rendering_status"),
        "negative_controls": list(manifest.get("negative_controls", [])),
        "required_negatives": list(manifest.get("required_negatives", [])),
        "negatives_run": list(manifest.get("negatives_run", [])),
        "kill_conditions": list(manifest.get("kill_conditions", [])),
        "exclusion_criteria": list(manifest.get("exclusion_criteria", [])),
        "live_splits": list(manifest.get("live_splits", [])),
        "witness_trace_id": manifest.get("witness_trace_id"),
        "witness_event_count": len(witness_trace.get("events", [])),
        "exclusion_event_count": len(witness_trace.get("exclusion_events", [])),
        "negative_controls_run": list(witness_trace.get("negative_controls_run", [])),
        "required_artifacts": list(manifest.get("required_artifacts", [])),
        "artifacts_emitted": list(manifest.get("artifacts_emitted", [])),
        "pass_rule": manifest.get("pass_rule"),
        "fail_rule": manifest.get("fail_rule"),
        "eligible_consumers": list(manifest.get("eligible_consumers", [])),
        "blocked_consumers": list(manifest.get("blocked_consumers", [])),
        "promotion_blockers": list(manifest.get("promotion_blockers", [])),
        "lane_admission": dict(manifest.get("lane_admission", {})),
        "frame_count": len(frames),
        "entity_count": len(final_entities),
        "mesh_patch_count": sum(1 for entity in final_entities if entity.get("entity_kind") == MESH_PATCH_ENTITY_KIND),
        "transition_meta_count": sum(
            len(entity.get("transition_meta", []))
            for entity in final_entities
            if entity.get("entity_kind") == MESH_PATCH_ENTITY_KIND and isinstance(entity.get("transition_meta"), list)
        ),
        "primary_entity_id": primary_entity.get("entity_id"),
        "capabilities": capabilities,
        "path_kind": scene.get("path_spec", {}).get("kind"),
        "projected_path_kind": scene.get("projected_path_spec", {}).get("kind"),
        "overlays": overlays,
        "expected_invariants": expected_invariants,
        "measured_invariants": measured_invariants,
        "final_scalars": _final_entity_scalars(run_dir / "frames"),
        "final_scalars_by_entity": _final_entity_scalars_by_entity(run_dir / "frames"),
        "evidence_paths": {
            "manifest": str(manifest_path),
            "scene": str(scene_path),
            "summary": str(summary_path),
            "witness_trace": str(witness_trace_path),
            "frames_dir": str(frames_dir),
            "final_frame": str(frames[-1]) if frames else None,
        },
        "criteria_checked": [
            "constraint_set_named",
            "probe_family_named",
            "admission_stage_named",
            "negative_controls_named",
            "witness_trace_named",
            "lane_admission_named",
            "artifact_exists",
            "schema_validation",
            "overlay_inference",
            "summary_invariants_read",
        ],
        "summary_all_pass": summary.get("all_pass"),
        "validation_ok": validation.get("ok"),
        "validation_errors": validation.get("errors", []),
        "validation_warnings": validation.get("warnings", []),
        "admission_audit": None,
    }
