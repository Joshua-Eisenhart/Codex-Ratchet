from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from system_v4.visualization.capabilities import (
    FIBER_PHASE,
    FIBER_SAMPLES,
    FRAME,
    HOLONOMY,
    S3_STATE,
    TRANSPORT_PATH,
)
from system_v4.visualization.schema_v1 import SCHEMA_VERSION


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


def validate_run_dir(run_dir: Path) -> dict:
    run_dir = Path(run_dir)
    errors: list[str] = []
    warnings: list[str] = []

    manifest_path = run_dir / "run_manifest.json"
    scene_path = run_dir / "scene.json"
    summary_path = run_dir / "summary.json"
    frames_dir = run_dir / "frames"

    for required in (manifest_path, scene_path, summary_path, frames_dir):
        if not required.exists():
            errors.append(f"missing required path: {required.name}")

    if errors:
        return {"ok": False, "errors": errors, "warnings": warnings}

    manifest = _load_json(manifest_path)
    _load_json(scene_path)
    _load_json(summary_path)
    frame_paths = sorted(frames_dir.glob("*.json"))
    if not frame_paths:
        errors.append("no frame JSON files present")
        return {"ok": False, "errors": errors, "warnings": warnings}

    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"unsupported schema version: {manifest.get('schema_version')}")

    capabilities = list(manifest.get("capabilities", []))
    previous_step = None

    for frame_path in frame_paths:
        frame = _load_json(frame_path)
        step_index = frame.get("step_index")
        if not isinstance(step_index, int):
            errors.append(f"invalid step_index in {frame_path.name}")
            continue
        if previous_step is not None and step_index <= previous_step:
            errors.append("step_index must be strictly increasing")
        previous_step = step_index

        entities = frame.get("entities", [])
        if not isinstance(entities, list) or len(entities) != 1:
            errors.append(f"{frame_path.name} must contain exactly one entity")
            continue

        entity = entities[0]
        if FRAME in capabilities:
            frame_vectors = entity.get("frame_vectors", {})
            for key in ("tangent", "normal", "binormal"):
                if not _is_vector3(frame_vectors.get(key)):
                    errors.append(f"{frame_path.name} missing valid frame vector: {key}")
            if not _is_vector3(entity.get("base_xyz")):
                errors.append(f"{frame_path.name} missing valid base_xyz")

        if TRANSPORT_PATH in capabilities and "arc_id" not in entity.get("tags", {}):
            tags = entity.get("tags", {})
            if "arc_id" not in tags and "loop_theta" not in tags:
                errors.append(f"{frame_path.name} declares transport_path but has no arc_id or loop_theta tag")

        scalars = entity.get("scalars", {})
        if HOLONOMY in capabilities and "accumulated_holonomy" not in scalars:
            errors.append(f"{frame_path.name} declares holonomy but has no accumulated_holonomy scalar")
        if FIBER_PHASE in capabilities and "fiber_phase" not in scalars:
            errors.append(f"{frame_path.name} declares fiber_phase but has no fiber_phase scalar")

        if S3_STATE in capabilities and not _is_vector4(entity.get("s3_point")):
            errors.append(f"{frame_path.name} declares s3_state but has no valid s3_point")
        if FIBER_SAMPLES in capabilities:
            fiber_samples = entity.get("fiber_samples_xyz")
            if not isinstance(fiber_samples, list) or not fiber_samples:
                errors.append(f"{frame_path.name} declares fiber_samples but has no fiber_samples_xyz payload")
            elif not all(_is_vector3(sample) for sample in fiber_samples):
                errors.append(f"{frame_path.name} fiber_samples_xyz must contain only vector3 entries")

        base_xyz = entity.get("base_xyz")
        if _is_vector3(base_xyz):
            base_norm = float(np.linalg.norm(np.array(base_xyz, dtype=float)))
            if abs(base_norm - 1.0) > 1e-3:
                errors.append(f"{frame_path.name} base_xyz is not on the unit sphere")

        s3_point = entity.get("s3_point")
        if _is_vector4(s3_point):
            s3_norm = float(np.linalg.norm(np.array(s3_point, dtype=float)))
            if abs(s3_norm - 1.0) > 1e-3:
                errors.append(f"{frame_path.name} s3_point is not on the unit sphere")

        tangent_leakage = scalars.get("tangent_leakage")
        if isinstance(tangent_leakage, (float, int)) and abs(float(tangent_leakage)) > 1e-3:
            warnings.append(f"{frame_path.name} tangent leakage exceeds threshold")

    if not errors:
        final_frame = _load_json(frame_paths[-1])
        holonomy = final_frame["entities"][0]["scalars"].get("accumulated_holonomy")
        if isinstance(holonomy, (float, int)) and abs(abs(float(holonomy)) - (np.pi / 2)) > 5e-2:
            warnings.append("final holonomy deviates from expected pi/2 target")

    return {
        "ok": not errors,
        "schema_version": manifest.get("schema_version"),
        "capabilities": capabilities,
        "frame_count": len(frame_paths),
        "errors": errors,
        "warnings": warnings,
    }
