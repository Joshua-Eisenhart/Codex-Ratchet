from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
EXPORTER_PATH = REPO_ROOT / "system_v4" / "visualization" / "exporters" / "synthetic_atlas.py"
VALIDATOR_PATH = REPO_ROOT / "system_v4" / "visualization" / "validator.py"
sys.path.insert(0, str(REPO_ROOT))


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_export_synthetic_atlas_writes_cells_and_seams(tmp_path: Path) -> None:
    exporter = _load_module(EXPORTER_PATH, "synthetic_atlas_exporter")
    validator = _load_module(VALIDATOR_PATH, "viz_validator")

    run_dir = exporter.export_synthetic_atlas("atlas_demo", tmp_path, frame_count=5)
    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    frames = sorted((run_dir / "frames").glob("*.json"))
    assert frames

    frame_payload = json.loads(frames[0].read_text(encoding="utf-8"))
    mesh_entities = [entity for entity in frame_payload["entities"] if entity.get("entity_kind") == "mesh_patch"]

    assert manifest["sim_name"] == "synthetic_two_patch_atlas"
    assert "cell_geometry" in manifest["capabilities"]
    assert "seam_markers" in manifest["capabilities"]
    assert "chart_patch" in manifest["capabilities"]
    assert "transition_meta" in manifest["capabilities"]
    assert {entity["entity_id"] for entity in mesh_entities} == {"patch_A", "patch_B"}
    assert all(entity["cell_indices"] for entity in mesh_entities)
    assert all(entity["seam_edges"] for entity in mesh_entities)
    assert all(entity["chart_neighbors"] for entity in mesh_entities)
    assert all(entity["transition_meta"] for entity in mesh_entities)

    report = validator.validate_run_dir(run_dir)
    assert report["ok"] is True
    assert report["errors"] == []
