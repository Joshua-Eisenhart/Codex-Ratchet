from __future__ import annotations

import json
from pathlib import Path

from system_v4.visualization.capabilities import ATLAS_CAPABILITIES
from system_v4.visualization.schema_v1 import (
    ADMISSION_STAGE_LABELS,
    ADMISSION_STAGE_NEXT,
    ATLAS_ENTITY_KIND,
    ATLAS_FAMILY,
    ATLAS_SIM_NAME,
    MESH_PATCH_ENTITY_KIND,
    POINT_FRAME_ENTITY_KIND,
    SCHEMA_VERSION,
)


def _json_dump(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def build_run_manifest(run_id: str, frame_count: int) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "family": ATLAS_FAMILY,
        "sim_name": ATLAS_SIM_NAME,
        "run_id": run_id,
        "capabilities": ATLAS_CAPABILITIES,
        "entity_kind": ATLAS_ENTITY_KIND,
        "frame_count": frame_count,
        "constraint_set": "two_patch_shared_seam_fixture",
        "probe_family": "atlas_surface_probe",
        "carrier": "synthetic_two_patch_fixture",
        "lane": "pairwise",
        "layer": "atlas_patch_surface",
        "witness_type": "synthetic_fixture",
        "admission_stage": "coexistence",
        "admission_stage_index": ADMISSION_STAGE_LABELS.index("coexistence"),
        "promotion_target_stage": ADMISSION_STAGE_NEXT["coexistence"],
        "claim_state": "snapshot-labeled",
        "promotion_status": "supporting",
        "status_label": "exists",
        "geometry_rendering_status": "admitted_rendering",
        "negative_controls": [
            "missing_shared_seam",
            "neighbor_relation_asymmetry",
            "carrier_without_patch_context",
        ],
        "exclusion_criteria": [
            "patch cells fail to share a declared seam edge",
            "chart neighbors fail pairwise reciprocity",
            "transition annotations fail seam-bound check",
        ],
        "live_splits": [
            "fixture_proves_contract_shape_only",
        ],
        "witness_trace_id": f"{run_id}::atlas_surface_probe",
        "required_negatives": [
            "missing_shared_seam",
            "neighbor_relation_asymmetry",
            "carrier_without_patch_context",
        ],
        "negatives_run": [
            "missing_shared_seam",
            "neighbor_relation_asymmetry",
            "carrier_without_patch_context",
        ],
        "kill_conditions": [
            "patch cells fail to share a declared seam edge",
            "chart neighbors fail pairwise reciprocity",
            "transition annotations fail seam-bound check",
        ],
        "required_artifacts": [
            "run_manifest.json",
            "scene.json",
            "summary.json",
            "witness_trace.json",
            "frames/*.json",
        ],
        "artifacts_emitted": [
            "run_manifest.json",
            "scene.json",
            "summary.json",
            "witness_trace.json",
            "frames/*.json",
        ],
        "pass_rule": "two patch cells, shared seam metadata, and reciprocal chart neighbors remain present",
        "fail_rule": "declared seam or reciprocal neighbor relation is missing",
        "eligible_consumers": [
            "atlas_contract_regression",
            "viewer_surface_smoke",
        ],
        "blocked_consumers": [
            "probe_real_atlas_promotion",
            "bridge_level_claims",
        ],
        "promotion_blockers": [
            "synthetic fixture only",
            "not probe-real",
            "not admissible for bridge claims",
        ],
        "lane_admission": {
            "current_lane": "pairwise",
            "prerequisite_lanes": ["shell-local"],
            "admission_rule": "fixture atlas evidence remains snapshot-labeled and cannot promote coexistence, emergence, or bridge claims",
        },
    }


def build_scene_spec() -> dict:
    return {
        "geometry_type": "atlas_patch_fixture",
        "static_entities": [
            {"entity_id": "patch_A"},
            {"entity_id": "patch_B"},
            {"entity_id": "carrier_0"},
        ],
        "path_spec": {
            "kind": "synthetic_two_patch_seam",
            "vertices": [
                [0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0],
                [0.5, 0.8, 0.0],
                [0.5, -0.8, 0.0],
            ],
        },
        "expected_invariants": {
            "patch_count": 2,
            "shared_seam_edges": 1,
        },
    }


def _line_indices_for_triangle() -> list[list[int]]:
    return [[0, 1], [1, 2], [2, 0]]


def build_frame(step_index: int, frame_count: int) -> dict:
    seam_phase = float(step_index / max(frame_count - 1, 1))
    carrier_x = 0.5
    carrier_y = -0.3 + 0.6 * seam_phase
    carrier = {
        "entity_id": "carrier_0",
        "entity_kind": POINT_FRAME_ENTITY_KIND,
        "base_xyz": [carrier_x, carrier_y, 0.12],
        "frame_vectors": {
            "tangent": [0.0, 1.0, 0.0],
            "normal": [0.0, 0.0, 1.0],
            "binormal": [1.0, 0.0, 0.0],
        },
        "scalars": {
            "transport_error": 0.0,
            "seam_proximity": abs(carrier_y),
        },
        "tags": {
            "seam_side": "A" if carrier_y >= 0.0 else "B",
        },
    }
    patch_a = {
        "entity_id": "patch_A",
        "entity_kind": MESH_PATCH_ENTITY_KIND,
        "points_xyz": [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.5, 0.8, 0.0],
        ],
        "line_indices": _line_indices_for_triangle(),
        "cell_indices": [[0, 1, 2]],
        "patch_id": "patch_A",
        "chart_id": "chart_upper",
        "seam_edges": [[0, 1]],
        "chart_neighbors": ["patch_B"],
        "transition_meta": [{
            "neighbor_patch_id": "patch_B",
            "transition_kind": "shared_edge_flip",
            "seam_edges": [[0, 1]],
        }],
        "point_scalars": {
            "height": [0.0, 0.0, 0.8],
        },
    }
    patch_b = {
        "entity_id": "patch_B",
        "entity_kind": MESH_PATCH_ENTITY_KIND,
        "points_xyz": [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.5, -0.8, 0.0],
        ],
        "line_indices": _line_indices_for_triangle(),
        "cell_indices": [[0, 1, 2]],
        "patch_id": "patch_B",
        "chart_id": "chart_lower",
        "seam_edges": [[0, 1]],
        "chart_neighbors": ["patch_A"],
        "transition_meta": [{
            "neighbor_patch_id": "patch_A",
            "transition_kind": "shared_edge_flip",
            "seam_edges": [[0, 1]],
        }],
        "point_scalars": {
            "height": [0.0, 0.0, -0.8],
        },
    }
    return {
        "step_index": step_index,
        "sim_time": seam_phase,
        "entities": [patch_a, patch_b, carrier],
        "events": [
            {
                "kind": "seam_crossing_candidate",
                "entity_id": "carrier_0",
                "seam_phase": seam_phase,
            }
        ],
    }


def build_summary() -> dict:
    return {
        "name": ATLAS_SIM_NAME,
        "summary": {"all_pass": True},
        "checks": {
            "two_patches_present": True,
            "shared_seam_declared": True,
            "carrier_present": True,
        },
        "invariants": {
            "patch_count": 2,
            "shared_seam_edges": 1,
        },
        "all_pass": True,
    }


def build_witness_trace(frame_count: int) -> dict:
    return {
        "witness_trace_id": "atlas_surface_probe",
        "probe_family": "atlas_surface_probe",
        "constraint_set": "two_patch_shared_seam_fixture",
        "events": [
            {
                "event_kind": "seam_phase_step",
                "step_index": int(index),
                "seam_phase": float(index / max(frame_count - 1, 1)),
                "status_label": "exists",
            }
            for index in range(frame_count)
        ],
        "negative_controls_run": [
            "missing_shared_seam",
            "neighbor_relation_asymmetry",
            "carrier_without_patch_context",
        ],
        "exclusion_events": [
            {
                "event_kind": "fixture_scope_fence",
                "detail": "synthetic atlas remains supporting and snapshot-labeled",
            }
        ],
    }


def export_synthetic_atlas(run_id: str, out_dir: Path, frame_count: int = 9) -> Path:
    out_dir = Path(out_dir)
    run_dir = out_dir / run_id
    frames_dir = run_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    frames = [build_frame(step_index=index, frame_count=frame_count) for index in range(frame_count)]

    _json_dump(run_dir / "run_manifest.json", build_run_manifest(run_id, len(frames)))
    _json_dump(run_dir / "scene.json", build_scene_spec())
    _json_dump(run_dir / "summary.json", build_summary())
    _json_dump(run_dir / "witness_trace.json", build_witness_trace(frame_count))

    for frame in frames:
        _json_dump(frames_dir / f"{frame['step_index']:06d}.json", frame)

    return run_dir
