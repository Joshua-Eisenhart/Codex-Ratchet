from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
EXPORTER_PATH = REPO_ROOT / "system_v4" / "visualization" / "exporters" / "transport_s2.py"
HOPF_EXPORTER_PATH = REPO_ROOT / "system_v4" / "visualization" / "exporters" / "hopf_bundle.py"
SCRUBBER_PATH = REPO_ROOT / "system_v4" / "visualization" / "viewers" / "scrubber_pyvista.py"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_load_run_reads_exported_transport_artifacts(tmp_path: Path) -> None:
    exporter = _load_module(EXPORTER_PATH, "transport_s2_exporter")
    scrubber = _load_module(SCRUBBER_PATH, "scrubber_pyvista")

    run_dir = exporter.export_transport_s2("scrubber_demo", tmp_path, steps_per_arc=8)
    manifest, scene, frames, summary = scrubber.load_run(run_dir)

    assert manifest["run_id"] == "scrubber_demo"
    assert scene["geometry_type"] == "unit_sphere"
    assert frames
    assert summary["all_pass"] is True


def test_open_scrubber_fails_closed_when_pyvista_is_missing(tmp_path: Path) -> None:
    exporter = _load_module(EXPORTER_PATH, "transport_s2_exporter")
    scrubber = _load_module(SCRUBBER_PATH, "scrubber_pyvista")

    run_dir = exporter.export_transport_s2("scrubber_missing_dep", tmp_path, steps_per_arc=8)

    with pytest.raises(RuntimeError, match="PyVista is required"):
        scrubber.open_scrubber(run_dir)


def test_load_run_reads_exported_hopf_artifacts_and_overlay_payload(tmp_path: Path) -> None:
    exporter = _load_module(HOPF_EXPORTER_PATH, "hopf_bundle_exporter")
    scrubber = _load_module(SCRUBBER_PATH, "scrubber_pyvista")

    run_dir = exporter.export_hopf_bundle("hopf_scrubber_demo", tmp_path, n_points=16, fiber_points=8, fiber_twist=1.0)
    manifest, scene, frames, summary = scrubber.load_run(run_dir)

    assert manifest["sim_name"] == "hopf_bundle_lift"
    assert scene["geometry_type"] == "unit_sphere"
    assert summary["all_pass"] is True
    assert frames

    overlay = scrubber._fiber_overlay_points(frames[0]["entities"][0])
    assert overlay is not None
    assert overlay.shape == (8, 3)
    projected_path = scrubber._projected_path_points(scene)
    assert projected_path is not None
    assert projected_path.shape[1] == 3
    projected_point = scrubber._projected_frame_point(frames[0]["entities"][0])
    assert projected_point is not None
    assert projected_point.shape == (3,)
    offset = scrubber._projected_overlay_offset(scene)
    assert offset.shape == (3,)


def test_open_scrubber_hopf_run_reaches_pyvista_dependency_boundary(tmp_path: Path) -> None:
    exporter = _load_module(HOPF_EXPORTER_PATH, "hopf_bundle_exporter")
    scrubber = _load_module(SCRUBBER_PATH, "scrubber_pyvista")

    run_dir = exporter.export_hopf_bundle("hopf_missing_dep", tmp_path, n_points=16, fiber_points=8, fiber_twist=1.0)

    with pytest.raises(RuntimeError, match="PyVista is required"):
        scrubber.open_scrubber(run_dir)
