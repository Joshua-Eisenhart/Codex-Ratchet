from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from system_v4.probes import hopf_manifold as hopf
from system_v4.visualization.capabilities import HOPF_CAPABILITIES
from system_v4.visualization.schema_v1 import (
    HOPF_ENTITY_KIND,
    HOPF_FAMILY,
    HOPF_SIM_NAME,
    SCHEMA_VERSION,
)


def _json_dump(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _normalize_vector(vec: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vec)
    if norm < 1e-12:
        return vec.astype(float)
    return (vec / norm).astype(float)


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


def build_run_manifest(run_id: str, frame_count: int) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "family": HOPF_FAMILY,
        "sim_name": HOPF_SIM_NAME,
        "run_id": run_id,
        "capabilities": HOPF_CAPABILITIES,
        "entity_kind": HOPF_ENTITY_KIND,
        "frame_count": frame_count,
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

    return {
        "step_index": int(step_index),
        "sim_time": float(step_index / len(base_points)),
        "entities": [{
            "entity_id": "carrier_0",
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
        }],
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

    for frame in frames:
        frame_name = f"{frame['step_index']:06d}.json"
        _json_dump(frames_dir / frame_name, frame)

    return run_dir
