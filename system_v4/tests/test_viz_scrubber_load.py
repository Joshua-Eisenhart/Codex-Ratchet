from __future__ import annotations

import importlib.util
import json
import sys
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


def test_prepare_matplotlib_runtime_sets_writable_tmp_dir(monkeypatch: pytest.MonkeyPatch) -> None:
    scrubber = _load_module(SCRUBBER_PATH, "scrubber_pyvista")

    monkeypatch.delenv("MPLCONFIGDIR", raising=False)
    configured = scrubber._prepare_matplotlib_runtime()

    assert configured == "/tmp/codex_ratchet_matplotlib"
    assert Path(configured).exists()


def test_open_scrubber_fails_closed_when_pyvista_is_missing(tmp_path: Path) -> None:
    exporter = _load_module(EXPORTER_PATH, "transport_s2_exporter")
    scrubber = _load_module(SCRUBBER_PATH, "scrubber_pyvista")

    run_dir = exporter.export_transport_s2("scrubber_missing_dep", tmp_path, steps_per_arc=8)
    original = sys.modules.get("pyvista", ...)
    sys.modules["pyvista"] = None

    try:
        with pytest.raises(RuntimeError, match="PyVista is required"):
            scrubber.open_scrubber(run_dir)
    finally:
        if original is ...:
            sys.modules.pop("pyvista", None)
        else:
            sys.modules["pyvista"] = original


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
    original = sys.modules.get("pyvista", ...)
    sys.modules["pyvista"] = None

    try:
        with pytest.raises(RuntimeError, match="PyVista is required"):
            scrubber.open_scrubber(run_dir)
    finally:
        if original is ...:
            sys.modules.pop("pyvista", None)
        else:
            sys.modules["pyvista"] = original


def test_frame_status_text_mentions_multi_entity_primary(tmp_path: Path) -> None:
    exporter = _load_module(HOPF_EXPORTER_PATH, "hopf_bundle_exporter")
    scrubber = _load_module(SCRUBBER_PATH, "scrubber_pyvista")

    run_dir = exporter.export_hopf_bundle("hopf_multi_status", tmp_path, n_points=16, fiber_points=8, fiber_twist=1.0)
    frame_path = sorted((run_dir / "frames").glob("*.json"))[-1]
    frame_payload = json.loads(frame_path.read_text(encoding="utf-8"))
    extra_entity = json.loads(json.dumps(frame_payload["entities"][0]))
    extra_entity["entity_id"] = "carrier_1"
    frame_payload["entities"].append(extra_entity)
    frame_path.write_text(json.dumps(frame_payload, indent=2), encoding="utf-8")

    _manifest, scene, frames, _summary = scrubber.load_run(run_dir)
    text = scrubber._frame_status_text(frames[-1], scene["expected_invariants"]["expected_berry_phase"], _manifest)

    assert "constraint set: hopf_bundle_local_loop" in text
    assert "probe family: hopf_bundle_probe" in text
    assert "claim ceiling: exists" in text
    assert "claim/promotion: candidate / supporting" in text
    assert "admission: pairwise -> coexistence" in text
    assert "lane gate: no lower-lane prerequisites" in text
    assert "entities: 5" in text
    assert "primary: carrier_0" in text


def test_timeline_series_tracks_witness_and_exclusion_progression(tmp_path: Path) -> None:
    exporter = _load_module(HOPF_EXPORTER_PATH, "hopf_bundle_exporter")
    scrubber = _load_module(SCRUBBER_PATH, "scrubber_pyvista")

    run_dir = exporter.export_hopf_bundle("hopf_timeline", tmp_path, n_points=16, fiber_points=8, fiber_twist=1.0)
    witness_trace = json.loads((run_dir / "witness_trace.json").read_text(encoding="utf-8"))
    witness_cumulative, exclusion_cumulative = scrubber._timeline_series(witness_trace, frame_count=16)

    assert witness_cumulative[-1] == len(witness_trace["events"])
    assert exclusion_cumulative[-1] == 0


def test_timeline_series_defaults_exclusion_without_step_to_last_frame(tmp_path: Path) -> None:
    atlas_exporter = _load_module(REPO_ROOT / "system_v4" / "visualization" / "exporters" / "synthetic_atlas.py", "synthetic_atlas_exporter")
    scrubber = _load_module(SCRUBBER_PATH, "scrubber_pyvista")

    run_dir = atlas_exporter.export_synthetic_atlas("atlas_timeline", tmp_path, frame_count=5)
    witness_trace = json.loads((run_dir / "witness_trace.json").read_text(encoding="utf-8"))
    witness_cumulative, exclusion_cumulative = scrubber._timeline_series(witness_trace, frame_count=5)

    assert witness_cumulative[-1] == len(witness_trace["events"])
    assert exclusion_cumulative.tolist() == [0.0, 0.0, 0.0, 0.0, 1.0]
