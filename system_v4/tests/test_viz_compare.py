from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TRANSPORT_EXPORTER_PATH = REPO_ROOT / "system_v4" / "visualization" / "exporters" / "transport_s2.py"
HOPF_EXPORTER_PATH = REPO_ROOT / "system_v4" / "visualization" / "exporters" / "hopf_bundle.py"
COMPARISON_PATH = REPO_ROOT / "system_v4" / "visualization" / "comparison.py"
sys.path.insert(0, str(REPO_ROOT))


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_compare_run_dirs_reports_transport_vs_hopf_differences(tmp_path: Path) -> None:
    transport = _load_module(TRANSPORT_EXPORTER_PATH, "transport_s2_exporter")
    hopf = _load_module(HOPF_EXPORTER_PATH, "hopf_bundle_exporter")
    comparison = _load_module(COMPARISON_PATH, "viz_comparison")

    left_run = transport.export_transport_s2("compare_transport", tmp_path, steps_per_arc=8)
    right_run = hopf.export_hopf_bundle("compare_hopf", tmp_path, n_points=16, fiber_points=8, fiber_twist=1.0)

    report = comparison.compare_run_dirs(left_run, right_run)

    assert report["validation_ok"]["left"] is True
    assert report["validation_ok"]["right"] is True
    assert "holonomy" in report["capabilities"]["only_left"]
    assert "s3_state" in report["capabilities"]["only_right"]
    assert "projected_s3_path" in report["overlays"]["only_right"]
    assert report["projected_path_kind"]["left"] is None
    assert report["projected_path_kind"]["right"] == "stereographic_s3_path"
    assert report["mesh_patch_count"]["left"] == 0
    assert report["mesh_patch_count"]["right"] == 3
    assert "accumulated_holonomy" in report["final_scalars"]
    assert "fiber_phase" in report["final_scalars"]


def test_compare_run_dirs_reports_entity_count_and_scalars_by_entity(tmp_path: Path) -> None:
    transport = _load_module(TRANSPORT_EXPORTER_PATH, "transport_s2_exporter")
    hopf = _load_module(HOPF_EXPORTER_PATH, "hopf_bundle_exporter")
    comparison = _load_module(COMPARISON_PATH, "viz_comparison")

    left_run = transport.export_transport_s2("compare_transport_multi", tmp_path, steps_per_arc=8)
    right_run = hopf.export_hopf_bundle("compare_hopf_multi", tmp_path, n_points=16, fiber_points=8, fiber_twist=1.0)

    right_frame_path = sorted((right_run / "frames").glob("*.json"))[-1]
    right_frame_payload = json.loads(right_frame_path.read_text(encoding="utf-8"))
    extra_entity = json.loads(json.dumps(right_frame_payload["entities"][0]))
    extra_entity["entity_id"] = "carrier_1"
    extra_entity["scalars"]["fiber_phase"] = 3.25
    right_frame_payload["entities"].append(extra_entity)
    right_frame_path.write_text(json.dumps(right_frame_payload, indent=2), encoding="utf-8")

    report = comparison.compare_run_dirs(left_run, right_run)

    assert report["entity_count"]["left"] == 1
    assert report["entity_count"]["right"] == 5
    assert report["entity_count"]["delta"] == 4
    assert report["mesh_patch_count"]["left"] == 0
    assert report["mesh_patch_count"]["right"] == 3
    assert "carrier_1" in report["final_scalars_by_entity"]
    assert report["final_scalars_by_entity"]["carrier_1"]["fiber_phase"]["right"] == 3.25
