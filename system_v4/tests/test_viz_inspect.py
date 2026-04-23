from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
HOPF_EXPORTER_PATH = REPO_ROOT / "system_v4" / "visualization" / "exporters" / "hopf_bundle.py"
INSPECTION_PATH = REPO_ROOT / "system_v4" / "visualization" / "inspection.py"
sys.path.insert(0, str(REPO_ROOT))


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_inspect_run_dir_reports_hopf_overlays(tmp_path: Path) -> None:
    exporter = _load_module(HOPF_EXPORTER_PATH, "hopf_bundle_exporter")
    inspection = _load_module(INSPECTION_PATH, "viz_inspection")

    run_dir = exporter.export_hopf_bundle("inspect_hopf_demo", tmp_path, n_points=16, fiber_points=8, fiber_twist=1.0)
    report = inspection.inspect_run_dir(run_dir)

    assert report["sim_name"] == "hopf_bundle_lift"
    assert report["validation_ok"] is True
    assert "fiber_ring" in report["overlays"]
    assert "mesh_patch_lines" in report["overlays"]
    assert "projected_s3_path" in report["overlays"]
    assert report["projected_path_kind"] == "stereographic_s3_path"
    assert report["mesh_patch_count"] == 3


def test_inspect_run_dir_reports_multi_entity_scalars_by_entity(tmp_path: Path) -> None:
    exporter = _load_module(HOPF_EXPORTER_PATH, "hopf_bundle_exporter")
    inspection = _load_module(INSPECTION_PATH, "viz_inspection")

    run_dir = exporter.export_hopf_bundle("inspect_multi_entity", tmp_path, n_points=16, fiber_points=8, fiber_twist=1.0)
    frame_path = sorted((run_dir / "frames").glob("*.json"))[-1]
    frame_payload = json.loads(frame_path.read_text(encoding="utf-8"))
    extra_entity = json.loads(json.dumps(frame_payload["entities"][0]))
    extra_entity["entity_id"] = "carrier_1"
    extra_entity["scalars"]["fiber_phase"] = 7.0
    frame_payload["entities"].append(extra_entity)
    frame_path.write_text(json.dumps(frame_payload, indent=2), encoding="utf-8")

    report = inspection.inspect_run_dir(run_dir)

    assert report["validation_ok"] is True
    assert report["entity_count"] == 5
    assert report["mesh_patch_count"] == 3
    assert report["primary_entity_id"] == "carrier_0"
    assert "carrier_1" in report["final_scalars_by_entity"]
    assert report["final_scalars_by_entity"]["carrier_1"]["fiber_phase"] == 7.0
