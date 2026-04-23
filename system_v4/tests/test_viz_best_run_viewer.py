from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TRANSPORT_EXPORTER_PATH = REPO_ROOT / "system_v4" / "visualization" / "exporters" / "transport_s2.py"
HOPF_EXPORTER_PATH = REPO_ROOT / "system_v4" / "visualization" / "exporters" / "hopf_bundle.py"
BEST_RUN_VIEWER_PATH = REPO_ROOT / "system_v4" / "visualization" / "best_run_viewer.py"
sys.path.insert(0, str(REPO_ROOT))


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_resolve_best_run_dir_picks_best_sim_run(tmp_path: Path) -> None:
    transport = _load_module(TRANSPORT_EXPORTER_PATH, "transport_s2_exporter")
    hopf = _load_module(HOPF_EXPORTER_PATH, "hopf_bundle_exporter")
    best_viewer = _load_module(BEST_RUN_VIEWER_PATH, "viz_best_run_viewer")

    transport_root = tmp_path / "transport_root"
    hopf_root = tmp_path / "hopf_root"
    transport.export_transport_s2("best_view_transport", transport_root, steps_per_arc=8)
    hopf.export_hopf_bundle("best_view_hopf", hopf_root, n_points=16, fiber_points=8, fiber_twist=1.0)

    resolved = best_viewer.resolve_best_run_dir([transport_root, hopf_root], "hopf_bundle_lift")

    assert resolved["run_id"] == "best_view_hopf"
    assert resolved["root"] == str(hopf_root)
    assert resolved["run_dir"] == str(hopf_root / "best_view_hopf")


def test_collect_best_viewer_launch_wraps_best_run_and_command(tmp_path: Path) -> None:
    transport = _load_module(TRANSPORT_EXPORTER_PATH, "transport_s2_exporter")
    best_viewer = _load_module(BEST_RUN_VIEWER_PATH, "viz_best_run_viewer")

    transport_root = tmp_path / "transport_root"
    transport.export_transport_s2("best_view_transport_only", transport_root, steps_per_arc=8)

    report = best_viewer.collect_best_viewer_launch(
        [transport_root],
        "parallel_transport_s2_classical",
        off_screen_smoke=True,
    )

    assert report["best_run"]["run_id"] == "best_view_transport_only"
    assert report["best_run"]["consumer"] is None
    assert report["launch"]["off_screen_smoke"] is True
    assert report["launch"]["command"][-1] == "--off-screen-smoke"


def test_launch_best_viewer_dry_run_returns_launch_payload(tmp_path: Path) -> None:
    hopf = _load_module(HOPF_EXPORTER_PATH, "hopf_bundle_exporter")
    best_viewer = _load_module(BEST_RUN_VIEWER_PATH, "viz_best_run_viewer")

    hopf_root = tmp_path / "hopf_root"
    hopf.export_hopf_bundle("best_view_launch_hopf", hopf_root, n_points=16, fiber_points=8, fiber_twist=1.0)

    result = best_viewer.launch_best_viewer(
        [hopf_root],
        "hopf_bundle_lift",
        off_screen_smoke=True,
        dry_run=True,
    )

    assert result["best_run"]["run_id"] == "best_view_launch_hopf"
    assert result["launch_result"]["ok"] is True
    assert result["launch_result"]["executed"] is False


def test_resolve_best_run_dir_raises_for_unknown_sim(tmp_path: Path) -> None:
    transport = _load_module(TRANSPORT_EXPORTER_PATH, "transport_s2_exporter")
    best_viewer = _load_module(BEST_RUN_VIEWER_PATH, "viz_best_run_viewer")

    transport_root = tmp_path / "transport_root"
    transport.export_transport_s2("best_view_unknown_transport", transport_root, steps_per_arc=8)

    try:
        best_viewer.resolve_best_run_dir([transport_root], "hopf_bundle_lift")
    except ValueError as exc:
        assert "Available: parallel_transport_s2_classical" in str(exc)
    else:
        raise AssertionError("expected ValueError for unknown sim")


def test_resolve_best_run_dir_skips_blocked_consumer_candidate(tmp_path: Path) -> None:
    transport = _load_module(TRANSPORT_EXPORTER_PATH, "transport_s2_exporter")
    best_viewer = _load_module(BEST_RUN_VIEWER_PATH, "viz_best_run_viewer")

    transport_root = tmp_path / "transport_root"
    blocked_run = transport.export_transport_s2("transport_z_blocked", transport_root, steps_per_arc=8)
    admitted_run = transport.export_transport_s2("transport_a_admitted", transport_root, steps_per_arc=8)

    blocked_manifest_path = blocked_run / "run_manifest.json"
    blocked_manifest = json.loads(blocked_manifest_path.read_text(encoding="utf-8"))
    blocked_manifest["blocked_consumers"] = blocked_manifest["blocked_consumers"] + ["viewer_surface_smoke"]
    blocked_manifest_path.write_text(json.dumps(blocked_manifest, indent=2), encoding="utf-8")

    admitted_manifest_path = admitted_run / "run_manifest.json"
    admitted_manifest = json.loads(admitted_manifest_path.read_text(encoding="utf-8"))
    admitted_manifest["eligible_consumers"] = admitted_manifest["eligible_consumers"] + ["viewer_surface_smoke"]
    admitted_manifest_path.write_text(json.dumps(admitted_manifest, indent=2), encoding="utf-8")

    resolved = best_viewer.resolve_best_run_dir(
        [transport_root],
        "parallel_transport_s2_classical",
        consumer="viewer_surface_smoke",
    )

    assert resolved["run_id"] == "transport_a_admitted"
    assert resolved["consumer"] == "viewer_surface_smoke"
    assert resolved["consumer_admission"]["admitted"] is True
    assert resolved["blocked_candidates"][0]["run_id"] == "transport_z_blocked"
