from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
EXPORTER_PATH = REPO_ROOT / "system_v4" / "visualization" / "exporters" / "hopf_torus_atlas.py"
VALIDATOR_PATH = REPO_ROOT / "system_v4" / "visualization" / "validator.py"
INSPECTION_PATH = REPO_ROOT / "system_v4" / "visualization" / "inspection.py"
sys.path.insert(0, str(REPO_ROOT))


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_export_hopf_torus_atlas_writes_probe_real_patch_cells(tmp_path: Path) -> None:
    exporter = _load_module(EXPORTER_PATH, "hopf_torus_atlas_exporter")
    validator = _load_module(VALIDATOR_PATH, "viz_validator")
    inspection = _load_module(INSPECTION_PATH, "viz_inspection")

    run_dir = exporter.export_hopf_torus_atlas("hopf_torus_atlas_demo", tmp_path, frame_count=4, n_theta1=6, n_theta2=6)
    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    frames = sorted((run_dir / "frames").glob("*.json"))
    assert frames

    frame_payload = json.loads(frames[0].read_text(encoding="utf-8"))
    mesh_entities = [entity for entity in frame_payload["entities"] if entity.get("entity_kind") == "mesh_patch"]

    assert manifest["sim_name"] == "hopf_torus_atlas"
    assert manifest["admission_stage"] == "topology-variant"
    assert manifest["promotion_target_stage"] == "emergence"
    assert {entity["entity_id"] for entity in mesh_entities} == {"inner_torus_patch", "outer_torus_patch"}
    assert all(entity["cell_indices"] for entity in mesh_entities)
    assert all(entity["seam_edges"] for entity in mesh_entities)
    assert all(entity["chart_neighbors"] for entity in mesh_entities)
    assert all(entity["transition_meta"] for entity in mesh_entities)

    report = validator.validate_run_dir(run_dir)
    assert report["ok"] is True
    inspect_report = inspection.inspect_run_dir(run_dir)
    assert inspect_report["validation_ok"] is True
    assert "mesh_patch_cells" in inspect_report["overlays"]
    assert "seam_edges" in inspect_report["overlays"]
    assert "transition_annotations" in inspect_report["overlays"]
    assert inspect_report["transition_meta_count"] == 2
    assert inspect_report["probe_family"] == "atlas_surface_probe"
    assert inspect_report["witness_type"] == "probe-real"
    assert inspect_report["witness_event_count"] == 4
