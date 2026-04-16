from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from system_v4.probes import sim_parallel_transport_s2_classical as probe
from system_v4.visualization.capabilities import TRANSPORT_CAPABILITIES
from system_v4.visualization.schema_v1 import (
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

    for frame in normalized_frames:
        frame_name = f"{frame['step_index']:06d}.json"
        _json_dump(frames_dir / frame_name, frame)

    return run_dir
