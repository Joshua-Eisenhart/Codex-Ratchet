from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from system_v4.probes import sim_parallel_transport_s2_classical as probe
from system_v4.visualization.capabilities import TRANSPORT_CAPABILITIES
from system_v4.visualization.schema_v1 import (
    ADMISSION_STAGE_NEXT,
    ADMISSION_STAGE_LABELS,
    SCHEMA_VERSION,
    TRANSPORT_ENTITY_KIND,
    TRANSPORT_FAMILY,
    TRANSPORT_SIM_NAME,
)


def _json_dump(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _normalize_vector(vec: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vec)
    if norm < 1e-12:
        return vec.astype(float)
    return (vec / norm).astype(float)


def build_run_manifest(run_id: str, frame_count: int) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "family": TRANSPORT_FAMILY,
        "sim_name": TRANSPORT_SIM_NAME,
        "run_id": run_id,
        "capabilities": TRANSPORT_CAPABILITIES,
        "entity_kind": TRANSPORT_ENTITY_KIND,
        "frame_count": frame_count,
        "constraint_set": "sphere_parallel_transport_octant_loop",
        "probe_family": "transport_frame_probe",
        "carrier": "unit_sphere_tangent_frame",
        "lane": "shell-local",
        "layer": "transport_frame",
        "witness_type": "direct_probe",
        "admission_stage": "shell-local",
        "admission_stage_index": ADMISSION_STAGE_LABELS.index("shell-local"),
        "promotion_target_stage": ADMISSION_STAGE_NEXT["shell-local"],
        "claim_state": "candidate",
        "promotion_status": "supporting",
        "status_label": "exists",
        "geometry_rendering_status": "admitted_rendering",
        "negative_controls": [
            "reversed_octant_orientation",
            "non_tangent_seed_rejection",
            "endpoint_holonomy_mismatch",
        ],
        "exclusion_criteria": [
            "frame loses tangency to carrier",
            "endpoint loop does not return to carrier start",
            "measured holonomy deviates beyond bounded tolerance",
        ],
        "live_splits": [],
        "witness_trace_id": f"{run_id}::transport_frame_probe",
        "required_negatives": [
            "reversed_octant_orientation",
            "non_tangent_seed_rejection",
            "endpoint_holonomy_mismatch",
        ],
        "negatives_run": [
            "reversed_octant_orientation",
            "non_tangent_seed_rejection",
            "endpoint_holonomy_mismatch",
        ],
        "kill_conditions": [
            "frame loses tangency to carrier",
            "endpoint loop does not return to carrier start",
            "measured holonomy deviates beyond bounded tolerance",
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
        "pass_rule": "bounded transport checks remain within tolerance and summary all_pass stays true",
        "fail_rule": "any positive, negative, or boundary transport check fails or tangency is lost",
        "eligible_consumers": [
            "transport_frame_report",
            "shell_local_geometry_inventory",
        ],
        "blocked_consumers": [
            "pairwise_coupling_claims",
            "bridge_level_claims",
        ],
        "promotion_blockers": [
            "no pairwise coupling evidence",
            "no coexistence rerun evidence",
            "no bridge-level admission evidence",
        ],
        "lane_admission": {
            "current_lane": "shell-local",
            "prerequisite_lanes": [],
            "admission_rule": "shell-local transport evidence does not imply pairwise, coexistence, or bridge admission",
        },
    }


def build_scene_spec() -> dict:
    return {
        "geometry_type": "unit_sphere",
        "static_entities": [{"entity_id": "carrier_0"}],
        "path_spec": {
            "kind": "octant_triangle",
            "vertices": [
                [0.0, 0.0, 1.0],
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0],
            ],
        },
        "initial_base_xyz": [0.0, 0.0, 1.0],
        "initial_tangent_xyz": [1.0, 0.0, 0.0],
        "expected_invariants": {"expected_holonomy": float(np.pi / 2)},
    }


def normalize_frame_record(raw_step: dict, initial_tangent: np.ndarray) -> dict:
    base = _normalize_vector(np.array(raw_step["base_xyz"], dtype=float))
    tangent = _normalize_vector(np.array(raw_step["tangent_xyz"], dtype=float))
    normal = base.copy()
    binormal = _normalize_vector(np.cross(normal, tangent))

    tangent_leakage = float(abs(np.dot(tangent, normal)))
    norm_deviation = float(abs(np.linalg.norm(tangent) - 1.0))
    accumulated_holonomy = float(probe.angle_between_tangent(initial_tangent, tangent, base))
    transport_error = float(tangent_leakage + norm_deviation)

    return {
        "step_index": int(raw_step["step_index"]),
        "sim_time": float(raw_step["loop_progress"]),
        "entities": [{
            "entity_id": "carrier_0",
            "base_xyz": base.tolist(),
            "frame_vectors": {
                "tangent": tangent.tolist(),
                "normal": normal.tolist(),
                "binormal": binormal.tolist(),
            },
            "scalars": {
                "tangent_leakage": tangent_leakage,
                "accumulated_holonomy": accumulated_holonomy,
                "transport_error": transport_error,
            },
            "tags": {"arc_id": int(raw_step["arc_id"])},
        }],
        "events": [],
    }


def build_summary() -> dict:
    positive = {key: bool(value) for key, value in probe.run_positive_tests().items()}
    negative = {key: bool(value) for key, value in probe.run_negative_tests().items()}
    boundary = {key: bool(value) for key, value in probe.run_boundary_tests().items()}
    all_pass = all(positive.values()) and all(negative.values()) and all(boundary.values())
    return {
        "name": TRANSPORT_SIM_NAME,
        "summary": {"all_pass": all_pass},
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "all_pass": all_pass,
    }


def build_witness_trace(raw_trace: list[dict]) -> dict:
    return {
        "witness_trace_id": "transport_frame_probe",
        "probe_family": "transport_frame_probe",
        "constraint_set": "sphere_parallel_transport_octant_loop",
        "events": [
            {
                "event_kind": "trace_step",
                "step_index": int(step["step_index"]),
                "arc_id": int(step["arc_id"]),
                "loop_progress": float(step["loop_progress"]),
                "status_label": "exists",
            }
            for step in raw_trace
        ],
        "negative_controls_run": [
            "reversed_octant_orientation",
            "non_tangent_seed_rejection",
            "endpoint_holonomy_mismatch",
        ],
        "exclusion_events": [],
    }


def export_transport_s2(run_id: str, out_dir: Path, steps_per_arc: int = 200) -> Path:
    out_dir = Path(out_dir)
    run_dir = out_dir / run_id
    frames_dir = run_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    raw_trace = probe.trace_transport_loop_octant(steps_per_arc=steps_per_arc)
    initial_tangent = np.array([1.0, 0.0, 0.0], dtype=float)
    normalized_frames = [normalize_frame_record(step, initial_tangent) for step in raw_trace]

    _json_dump(run_dir / "run_manifest.json", build_run_manifest(run_id, len(normalized_frames)))
    _json_dump(run_dir / "scene.json", build_scene_spec())
    _json_dump(run_dir / "summary.json", build_summary())
    _json_dump(run_dir / "witness_trace.json", build_witness_trace(raw_trace))

    for frame in normalized_frames:
        frame_name = f"{frame['step_index']:06d}.json"
        _json_dump(frames_dir / frame_name, frame)

    return run_dir
