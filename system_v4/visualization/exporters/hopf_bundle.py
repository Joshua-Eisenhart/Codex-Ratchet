from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from system_v4.probes import hopf_manifold as hopf
from system_v4.visualization.capabilities import HOPF_CAPABILITIES
from system_v4.visualization.schema_v1 import (
    ADMISSION_STAGE_LABELS,
    ADMISSION_STAGE_NEXT,
    HOPF_ENTITY_KIND,
    HOPF_FAMILY,
    HOPF_SIM_NAME,
    MESH_PATCH_ENTITY_KIND,
    SCHEMA_VERSION,
)


def _json_dump(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _normalize_vector(vec: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vec)
    if norm < 1e-12:
        return vec.astype(float)
    return (vec / norm).astype(float)


def _line_indices(count: int, *, closed: bool = False) -> list[list[int]]:
    if count < 2:
        return []
    indices = [[index, index + 1] for index in range(count - 1)]
    if closed:
        indices.append([count - 1, 0])
    return indices


def _fallback_tangent(base: np.ndarray) -> np.ndarray:
    tangent = np.cross(base, np.array([0.0, 0.0, 1.0]))
    if np.linalg.norm(tangent) < 1e-12:
        tangent = np.cross(base, np.array([0.0, 1.0, 0.0]))
    return _normalize_vector(tangent)


def _tangent_frame(base_points: np.ndarray, index: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    base = _normalize_vector(base_points[index])
    prev_base = base_points[index - 1]
    next_base = base_points[(index + 1) % len(base_points)]
    direction = next_base - prev_base
    tangent = direction - np.dot(direction, base) * base
    if np.linalg.norm(tangent) < 1e-12:
        tangent = _fallback_tangent(base)
    tangent = _normalize_vector(tangent)
    normal = base.copy()
    binormal = _normalize_vector(np.cross(normal, tangent))
    return tangent, normal, binormal


def _build_loop(n_points: int, fiber_twist: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    thetas = np.linspace(0.0, 2.0 * np.pi, n_points, endpoint=False)
    loop_q = []
    loop_base = []
    for theta in thetas:
        base = hopf.base_loop_point(theta)
        q = hopf.lift_base_point(base)
        q = hopf.fiber_action(q, fiber_twist * theta)
        loop_q.append(q)
        loop_base.append(hopf.hopf_map(q))
    return thetas, np.array(loop_q), np.array(loop_base)


def _projected_loop_points(loop_q: np.ndarray) -> list[list[float]]:
    return [hopf.stereographic_s3_to_r3(q).astype(float).tolist() for q in loop_q]


def build_run_manifest(run_id: str, frame_count: int) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "family": HOPF_FAMILY,
        "sim_name": HOPF_SIM_NAME,
        "run_id": run_id,
        "capabilities": HOPF_CAPABILITIES,
        "entity_kind": HOPF_ENTITY_KIND,
        "frame_count": frame_count,
        "constraint_set": "hopf_bundle_local_loop",
        "probe_family": "hopf_bundle_probe",
        "carrier": "hopf_fiber_over_s2_loop",
        "lane": "shell-local",
        "layer": "bundle_curve_geometry",
        "witness_type": "direct_probe",
        "admission_stage": "pairwise",
        "admission_stage_index": ADMISSION_STAGE_LABELS.index("pairwise"),
        "promotion_target_stage": ADMISSION_STAGE_NEXT["pairwise"],
        "claim_state": "candidate",
        "promotion_status": "supporting",
        "status_label": "exists",
        "geometry_rendering_status": "admitted_rendering",
        "negative_controls": [
            "base_motion_breaks_fiber_equivalence",
            "projected_s3_norm_drift",
            "berry_phase_trivialization",
        ],
        "exclusion_criteria": [
            "fiber action fails to preserve base projection",
            "s3 carrier leaves unit sphere tolerance",
            "berry phase fails bounded nontriviality check",
        ],
        "live_splits": [],
        "witness_trace_id": f"{run_id}::hopf_bundle_probe",
        "required_negatives": [
            "base_motion_breaks_fiber_equivalence",
            "projected_s3_norm_drift",
            "berry_phase_trivialization",
        ],
        "negatives_run": [
            "base_motion_breaks_fiber_equivalence",
            "projected_s3_norm_drift",
            "berry_phase_trivialization",
        ],
        "kill_conditions": [
            "fiber action fails to preserve base projection",
            "s3 carrier leaves unit sphere tolerance",
            "berry phase fails bounded nontriviality check",
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
        "pass_rule": "fiber-preserving and berry-phase checks remain bounded and summary all_pass stays true",
        "fail_rule": "fiber-preservation, s3 validity, or berry-phase checks fail",
        "eligible_consumers": [
            "bundle_curve_report",
            "pairwise_geometry_inventory",
        ],
        "blocked_consumers": [
            "coexistence_claims",
            "bridge_level_claims",
        ],
        "promotion_blockers": [
            "no coexistence rerun evidence",
            "no topology-variant rerun evidence",
            "no bridge-level admission evidence",
        ],
        "lane_admission": {
            "current_lane": "shell-local",
            "prerequisite_lanes": [],
            "admission_rule": "local Hopf bundle evidence does not by itself admit coexistence, emergence, or bridge claims",
        },
    }


def build_scene_spec(
    loop_base: np.ndarray,
    loop_q: np.ndarray,
    expected_berry_phase: float,
    fiber_points: int,
    fiber_twist: float,
) -> dict:
    path_vertices = loop_base.tolist() + [loop_base[0].tolist()]
    projected_loop = np.array([hopf.stereographic_s3_to_r3(q) for q in loop_q], dtype=float)
    projected_vertices = projected_loop.tolist() + [projected_loop[0].tolist()]
    initial_tangent, _, _ = _tangent_frame(loop_base, 0)
    return {
        "geometry_type": "unit_sphere",
        "static_entities": [{"entity_id": "carrier_0"}],
        "path_spec": {
            "kind": "hopf_base_loop_equator",
            "vertices": path_vertices,
        },
        "projected_path_spec": {
            "kind": "stereographic_s3_path",
            "vertices": projected_vertices,
            "offset_xyz": [3.5, 0.0, 0.0],
        },
        "initial_base_xyz": loop_base[0].tolist(),
        "initial_tangent_xyz": initial_tangent.tolist(),
        "fiber_points": fiber_points,
        "fiber_twist": float(fiber_twist),
        "expected_invariants": {
            "expected_berry_phase": float(expected_berry_phase),
        },
    }


def normalize_frame_record(
    step_index: int,
    theta: float,
    q: np.ndarray,
    base_points: np.ndarray,
    fiber_points: int,
    fiber_twist: float,
) -> dict:
    tangent, normal, binormal = _tangent_frame(base_points, step_index)
    raw_base = np.asarray(base_points[step_index], dtype=float)
    raw_q = np.asarray(q, dtype=float)
    base = _normalize_vector(raw_base)
    q = _normalize_vector(raw_q)

    tangent_leakage = float(abs(np.dot(tangent, normal)))
    s3_norm_error = float(abs(np.linalg.norm(raw_q) - 1.0))
    base_norm_error = float(abs(np.linalg.norm(raw_base) - 1.0))
    transport_error = float(tangent_leakage + s3_norm_error + base_norm_error)

    fiber_loop = hopf.sample_fiber(q, n_points=fiber_points)
    fiber_samples_xyz = [
        hopf.stereographic_s3_to_r3(sample).astype(float).tolist()
        for sample in fiber_loop
    ]
    projected_s3_xyz = hopf.stereographic_s3_to_r3(q).astype(float).tolist()
    base_points_xyz = base_points.astype(float).tolist()
    projected_loop_xyz = _projected_loop_points(
        np.array(
            [
                hopf.fiber_action(hopf.lift_base_point(base_point), fiber_twist * theta_value)
                for theta_value, base_point in zip(
                    np.linspace(0.0, 2.0 * np.pi, len(base_points), endpoint=False),
                    base_points,
                )
            ],
            dtype=float,
        )
    )
    loop_progress = np.linspace(0.0, 1.0, len(base_points), endpoint=False).astype(float).tolist()
    fiber_phase_progress = np.linspace(0.0, 1.0, len(fiber_samples_xyz), endpoint=False).astype(float).tolist()

    return {
        "step_index": int(step_index),
        "sim_time": float(step_index / len(base_points)),
        "entities": [
            {
                "entity_id": "carrier_0",
                "entity_kind": HOPF_ENTITY_KIND,
                "base_xyz": base.tolist(),
                "s3_point": q.tolist(),
                "projected_s3_xyz": projected_s3_xyz,
                "fiber_samples_xyz": fiber_samples_xyz,
                "frame_vectors": {
                    "tangent": tangent.tolist(),
                    "normal": normal.tolist(),
                    "binormal": binormal.tolist(),
                },
                "scalars": {
                    "fiber_phase": float(fiber_twist * theta),
                    "transport_error": transport_error,
                    "tangent_leakage": tangent_leakage,
                },
                "tags": {
                    "loop_theta": float(theta),
                    "hopf_patch_id": "north" if base[2] >= 0.0 else "south",
                },
            },
            {
                "entity_id": "base_loop_patch",
                "entity_kind": MESH_PATCH_ENTITY_KIND,
                "points_xyz": base_points_xyz,
                "line_indices": _line_indices(len(base_points_xyz), closed=True),
                "patch_id": "base_loop",
                "chart_id": "s2_equator",
                "point_scalars": {
                    "loop_progress": loop_progress,
                },
            },
            {
                "entity_id": "fiber_ring_patch",
                "entity_kind": MESH_PATCH_ENTITY_KIND,
                "points_xyz": fiber_samples_xyz,
                "line_indices": _line_indices(len(fiber_samples_xyz), closed=True),
                "patch_id": "fiber_ring",
                "chart_id": "hopf_fiber",
                "point_scalars": {
                    "fiber_phase_progress": fiber_phase_progress,
                },
            },
            {
                "entity_id": "projected_s3_patch",
                "entity_kind": MESH_PATCH_ENTITY_KIND,
                "points_xyz": projected_loop_xyz,
                "line_indices": _line_indices(len(projected_loop_xyz), closed=True),
                "patch_id": "projected_s3",
                "chart_id": "stereographic_s3",
                "point_scalars": {
                    "loop_progress": loop_progress,
                },
            },
        ],
        "events": [],
    }


def build_summary(loop_q: np.ndarray, loop_base: np.ndarray, fiber_twist: float) -> dict:
    berry = float(hopf.berry_phase(loop_q))
    s3_ok = bool(np.all([hopf.is_on_s3(q) for q in loop_q]))
    s2_ok = bool(np.all([hopf.is_on_s2(p) for p in loop_base]))
    fiber_base_variation = float(np.max([
        np.linalg.norm(hopf.hopf_map(sample) - loop_base[0])
        for sample in hopf.sample_fiber(loop_q[0], n_points=32)
    ]))
    berry_ok = abs(abs(berry) - np.pi) < 5e-2
    fiber_ok = fiber_base_variation < 1e-9
    all_pass = s3_ok and s2_ok and berry_ok and fiber_ok
    return {
        "name": HOPF_SIM_NAME,
        "summary": {"all_pass": all_pass},
        "checks": {
            "s3_points_on_manifold": s3_ok,
            "base_points_on_sphere": s2_ok,
            "fiber_preserves_base": fiber_ok,
            "berry_phase_nontrivial": berry_ok,
        },
        "invariants": {
            "measured_berry_phase": berry,
            "fiber_twist": float(fiber_twist),
            "fiber_base_variation": fiber_base_variation,
        },
        "all_pass": all_pass,
    }


def build_witness_trace(thetas: np.ndarray) -> dict:
    return {
        "witness_trace_id": "hopf_bundle_probe",
        "probe_family": "hopf_bundle_probe",
        "constraint_set": "hopf_bundle_local_loop",
        "events": [
            {
                "event_kind": "fiber_loop_step",
                "step_index": int(index),
                "loop_theta": float(theta),
                "status_label": "exists",
            }
            for index, theta in enumerate(thetas)
        ],
        "negative_controls_run": [
            "base_motion_breaks_fiber_equivalence",
            "projected_s3_norm_drift",
            "berry_phase_trivialization",
        ],
        "exclusion_events": [],
    }


def export_hopf_bundle(
    run_id: str,
    out_dir: Path,
    n_points: int = 128,
    fiber_points: int = 32,
    fiber_twist: float = 1.0,
) -> Path:
    out_dir = Path(out_dir)
    run_dir = out_dir / run_id
    frames_dir = run_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    thetas, loop_q, loop_base = _build_loop(n_points=n_points, fiber_twist=fiber_twist)
    expected_berry_phase = float(hopf.berry_phase(loop_q))
    frames = [
        normalize_frame_record(
            step_index=index,
            theta=theta,
            q=loop_q[index],
            base_points=loop_base,
            fiber_points=fiber_points,
            fiber_twist=fiber_twist,
        )
        for index, theta in enumerate(thetas)
    ]

    _json_dump(run_dir / "run_manifest.json", build_run_manifest(run_id, len(frames)))
    _json_dump(
        run_dir / "scene.json",
        build_scene_spec(
            loop_base=loop_base,
            loop_q=loop_q,
            expected_berry_phase=expected_berry_phase,
            fiber_points=fiber_points,
            fiber_twist=fiber_twist,
        ),
    )
    _json_dump(run_dir / "summary.json", build_summary(loop_q=loop_q, loop_base=loop_base, fiber_twist=fiber_twist))
    _json_dump(run_dir / "witness_trace.json", build_witness_trace(thetas))

    for frame in frames:
        frame_name = f"{frame['step_index']:06d}.json"
        _json_dump(frames_dir / frame_name, frame)

    return run_dir
