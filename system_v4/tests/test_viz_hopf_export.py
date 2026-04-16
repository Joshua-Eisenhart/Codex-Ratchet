from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
EXPORTER_PATH = REPO_ROOT / "system_v4" / "visualization" / "exporters" / "hopf_bundle.py"
VALIDATOR_PATH = REPO_ROOT / "system_v4" / "visualization" / "validator.py"
sys.path.insert(0, str(REPO_ROOT))


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_export_hopf_bundle_writes_extended_geometry_payload(tmp_path: Path) -> None:
    exporter = _load_module(EXPORTER_PATH, "hopf_bundle_exporter")
    validator = _load_module(VALIDATOR_PATH, "viz_validator")

    run_dir = exporter.export_hopf_bundle(
        "hopf_demo",
        tmp_path,
        n_points=16,
        fiber_points=8,
        fiber_twist=1.0,
    )

    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    frames = sorted((run_dir / "frames").glob("*.json"))
    assert frames

    frame_payload = json.loads(frames[0].read_text(encoding="utf-8"))
    entity = frame_payload["entities"][0]
    scene = json.loads((run_dir / "scene.json").read_text(encoding="utf-8"))

    assert manifest["sim_name"] == "hopf_bundle_lift"
    assert "s3_state" in manifest["capabilities"]
    assert "fiber_phase" in manifest["capabilities"]
    assert "fiber_samples" in manifest["capabilities"]
    assert "holonomy" not in manifest["capabilities"]
    assert len(entity["s3_point"]) == 4
    assert len(entity["projected_s3_xyz"]) == 3
    assert len(entity["fiber_samples_xyz"]) == 8
    assert scene["projected_path_spec"]["kind"] == "stereographic_s3_path"
    assert len(scene["projected_path_spec"]["offset_xyz"]) == 3
    assert "fiber_phase" in entity["scalars"]
    assert abs(abs(summary["invariants"]["measured_berry_phase"]) - np.pi) < 5e-2

    report = validator.validate_run_dir(run_dir)
    assert report["ok"] is True
    assert report["errors"] == []
