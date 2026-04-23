from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
HOPF_EXPORTER_PATH = REPO_ROOT / "system_v4" / "visualization" / "exporters" / "hopf_bundle.py"
VIEWER_LAUNCHER_PATH = REPO_ROOT / "system_v4" / "visualization" / "viewer_launcher.py"
sys.path.insert(0, str(REPO_ROOT))


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_collect_viewer_launch_builds_isolated_command(tmp_path: Path) -> None:
    exporter = _load_module(HOPF_EXPORTER_PATH, "hopf_bundle_exporter")
    launcher = _load_module(VIEWER_LAUNCHER_PATH, "viz_viewer_launcher")

    run_dir = exporter.export_hopf_bundle("viewer_launch_demo", tmp_path, n_points=16, fiber_points=8, fiber_twist=1.0)
    report = launcher.collect_viewer_launch(run_dir, off_screen_smoke=True, python_executable=Path(sys.executable))

    assert report["run_dir"] == str(run_dir)
    assert report["python_executable"] == sys.executable
    assert report["python_exists"] is True
    assert report["consumer"] is None
    assert report["consumer_admission"]["admitted"] is True
    assert report["off_screen_smoke"] is True
    assert report["command"][-1] == "--off-screen-smoke"


def test_launch_viewer_dry_run_returns_command_without_execution(tmp_path: Path) -> None:
    exporter = _load_module(HOPF_EXPORTER_PATH, "hopf_bundle_exporter")
    launcher = _load_module(VIEWER_LAUNCHER_PATH, "viz_viewer_launcher")

    run_dir = exporter.export_hopf_bundle("viewer_launch_dry", tmp_path, n_points=16, fiber_points=8, fiber_twist=1.0)
    result = launcher.launch_viewer(
        run_dir,
        off_screen_smoke=True,
        dry_run=True,
        python_executable=Path(sys.executable),
    )

    assert result["ok"] is True
    assert result["executed"] is False
    assert result["command"][0] == sys.executable


def test_render_viewer_launch_mentions_python_and_command(tmp_path: Path) -> None:
    exporter = _load_module(HOPF_EXPORTER_PATH, "hopf_bundle_exporter")
    launcher = _load_module(VIEWER_LAUNCHER_PATH, "viz_viewer_launcher")

    run_dir = exporter.export_hopf_bundle("viewer_launch_render", tmp_path, n_points=16, fiber_points=8, fiber_twist=1.0)
    text = launcher.render_viewer_launch(run_dir, off_screen_smoke=True, python_executable=Path(sys.executable))

    assert "Python:" in text
    assert "Consumer: (none)" in text
    assert "Python Exists: True" in text
    assert "Claim Ceiling: exists" in text
    assert "Promotion Blockers: no coexistence rerun evidence, no topology-variant rerun evidence" in text
    assert "Off Screen Smoke: True" in text
    assert "Command:" in text


def test_launch_viewer_blocks_denied_consumer(tmp_path: Path) -> None:
    exporter = _load_module(HOPF_EXPORTER_PATH, "hopf_bundle_exporter")
    launcher = _load_module(VIEWER_LAUNCHER_PATH, "viz_viewer_launcher")

    run_dir = exporter.export_hopf_bundle("viewer_launch_blocked", tmp_path, n_points=16, fiber_points=8, fiber_twist=1.0)

    try:
        launcher.launch_viewer(
            run_dir,
            consumer="bridge_level_claims",
            dry_run=True,
            python_executable=Path(sys.executable),
        )
    except RuntimeError as exc:
        assert "bridge_level_claims" in str(exc)
        assert "consumer_blocked" in str(exc)
    else:
        raise AssertionError("expected blocked consumer launch to fail closed")
