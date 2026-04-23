from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TRANSPORT_EXPORTER_PATH = REPO_ROOT / "system_v4" / "visualization" / "exporters" / "transport_s2.py"
ATLAS_EXPORTER_PATH = REPO_ROOT / "system_v4" / "visualization" / "exporters" / "synthetic_atlas.py"
MANIM_EXPORT_PATH = REPO_ROOT / "system_v4" / "visualization" / "manim_export.py"
sys.path.insert(0, str(REPO_ROOT))


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_collect_manim_export_for_transport_run(tmp_path: Path) -> None:
    transport = _load_module(TRANSPORT_EXPORTER_PATH, "transport_s2_exporter")
    manim_export = _load_module(MANIM_EXPORT_PATH, "viz_manim_export")

    run_dir = transport.export_transport_s2("manim_transport", tmp_path, steps_per_arc=8)
    payload = manim_export.collect_manim_export(run_dir)

    assert payload["run_id"] == "manim_transport"
    assert payload["constraint_set"] == "sphere_parallel_transport_octant_loop"
    assert payload["probe_family"] == "transport_frame_probe"
    assert payload["witnesses"]["witness_type"] == "direct_probe"
    assert payload["witnesses"]["event_count"] == len(payload["witnesses"]["events"])
    assert payload["witnesses"]["event_count"] > 0
    assert payload["exclusions"]["exclusion_event_count"] == 0
    assert payload["lane_progression"]["admission_stage"] == "shell-local"
    assert payload["lane_progression"]["promotion_target_stage"] == "pairwise"
    assert payload["validation"]["validation_ok"] is True
    assert payload["validation"]["summary_all_pass"] is True
    assert payload["admitted_survivors"][0]["entity_id"] == "carrier_0"


def test_collect_manim_export_for_atlas_run(tmp_path: Path) -> None:
    atlas = _load_module(ATLAS_EXPORTER_PATH, "synthetic_atlas_exporter")
    manim_export = _load_module(MANIM_EXPORT_PATH, "viz_manim_export")

    run_dir = atlas.export_synthetic_atlas("manim_atlas", tmp_path, frame_count=5)
    payload = manim_export.collect_manim_export(run_dir)

    assert payload["run_id"] == "manim_atlas"
    assert payload["witnesses"]["witness_type"] == "synthetic_fixture"
    assert payload["exclusions"]["exclusion_event_count"] == 1
    assert len(payload["exclusions"]["exclusion_events"]) == 1
    assert payload["lane_progression"]["admission_stage"] == "coexistence"
    assert payload["lane_progression"]["promotion_target_stage"] == "topology-variant"
    assert len(payload["admitted_survivors"]) == 3
    mesh_survivors = [item for item in payload["admitted_survivors"] if item.get("entity_kind") == "mesh_patch"]
    assert len(mesh_survivors) == 2
    assert all("points_xyz" in item for item in mesh_survivors)
    assert all("transition_meta" in item for item in mesh_survivors)


def test_collect_batch_manim_export_rolls_up_lane_counts(tmp_path: Path) -> None:
    transport = _load_module(TRANSPORT_EXPORTER_PATH, "transport_s2_exporter")
    atlas = _load_module(ATLAS_EXPORTER_PATH, "synthetic_atlas_exporter")
    manim_export = _load_module(MANIM_EXPORT_PATH, "viz_manim_export")

    transport_root = tmp_path / "transport_root"
    atlas_root = tmp_path / "atlas_root"
    transport.export_transport_s2("manim_transport", transport_root, steps_per_arc=8)
    atlas.export_synthetic_atlas("manim_atlas", atlas_root, frame_count=5)

    payload = manim_export.collect_batch_manim_export([transport_root, atlas_root])

    assert payload["run_count"] == 2
    assert payload["lane_counts"] == {"pairwise": 1, "shell-local": 1}
    run_ids = {item["run_id"] for item in payload["runs"]}
    assert run_ids == {"manim_transport", "manim_atlas"}
