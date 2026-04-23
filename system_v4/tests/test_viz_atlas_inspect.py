from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
EXPORTER_PATH = REPO_ROOT / "system_v4" / "visualization" / "exporters" / "synthetic_atlas.py"
INSPECTION_PATH = REPO_ROOT / "system_v4" / "visualization" / "inspection.py"
SCRUBBER_PATH = REPO_ROOT / "system_v4" / "visualization" / "viewers" / "scrubber_pyvista.py"
sys.path.insert(0, str(REPO_ROOT))


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_inspect_and_scrubber_status_report_atlas_overlays(tmp_path: Path) -> None:
    exporter = _load_module(EXPORTER_PATH, "synthetic_atlas_exporter")
    inspection = _load_module(INSPECTION_PATH, "viz_inspection")
    scrubber = _load_module(SCRUBBER_PATH, "scrubber_pyvista")

    run_dir = exporter.export_synthetic_atlas("atlas_inspect", tmp_path, frame_count=5)
    report = inspection.inspect_run_dir(run_dir)
    assert report["validation_ok"] is True
    assert "mesh_patch_lines" in report["overlays"]
    assert "mesh_patch_cells" in report["overlays"]
    assert "seam_edges" in report["overlays"]
    assert "transition_annotations" in report["overlays"]
    assert report["mesh_patch_count"] == 2
    assert report["transition_meta_count"] == 2
    assert report["lineage_meta_count"] == 2
    assert report["topology_change_count"] == 2
    assert report["lane"] == "pairwise"
    assert report["claim_state"] == "snapshot-labeled"
    assert report["witness_type"] == "synthetic_fixture"
    assert report["witness_event_count"] == 5
    assert report["exclusion_event_count"] == 1

    _manifest, scene, frames, _summary = scrubber.load_run(run_dir)
    text = scrubber._frame_status_text(frames[-1], scene["expected_invariants"].get("patch_count", 0.0), _manifest)
    assert "constraint set: two_patch_shared_seam_fixture" in text
    assert "probe family: atlas_surface_probe" in text
    assert "claim ceiling: exists" in text
    assert "entities: 3" in text
    assert "primary: carrier_0" in text
