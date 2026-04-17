from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "view_best_replay.sh"
TRANSPORT_EXPORTER_PATH = REPO_ROOT / "system_v4" / "visualization" / "exporters" / "transport_s2.py"
HOPF_EXPORTER_PATH = REPO_ROOT / "system_v4" / "visualization" / "exporters" / "hopf_bundle.py"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_view_best_replay_script_dry_run_for_hopf(tmp_path: Path) -> None:
    transport = _load_module(TRANSPORT_EXPORTER_PATH, "transport_s2_exporter")
    hopf = _load_module(HOPF_EXPORTER_PATH, "hopf_bundle_exporter")
    transport_root = tmp_path / "transport_root"
    hopf_root = tmp_path / "hopf_root"
    transport.export_transport_s2("script_transport_demo", transport_root, steps_per_arc=8)
    hopf.export_hopf_bundle("script_hopf_demo", hopf_root, n_points=16, fiber_points=8, fiber_twist=1.0)

    result = subprocess.run(
        [
            str(SCRIPT_PATH),
            "hopf_bundle_lift",
            "--off-screen-smoke",
            "--dry-run",
        ],
        cwd=REPO_ROOT,
        env={
            **dict(**__import__("os").environ),
            "VIZ_RUN_ROOT_TRANSPORT": str(transport_root),
            "VIZ_RUN_ROOT_HOPF": str(hopf_root),
            "VIZ_VIEWER_PYTHON": sys.executable,
        },
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["best_run"]["sim_name"] == "hopf_bundle_lift"
    assert payload["best_run"]["run_id"] == "script_hopf_demo"
    assert payload["launch_result"]["off_screen_smoke"] is True
    assert payload["launch_result"]["executed"] is False


def test_view_best_replay_script_dry_run_for_transport(tmp_path: Path) -> None:
    transport = _load_module(TRANSPORT_EXPORTER_PATH, "transport_s2_exporter")
    hopf = _load_module(HOPF_EXPORTER_PATH, "hopf_bundle_exporter")
    transport_root = tmp_path / "transport_root"
    hopf_root = tmp_path / "hopf_root"
    transport.export_transport_s2("script_transport_demo", transport_root, steps_per_arc=8)
    hopf.export_hopf_bundle("script_hopf_demo", hopf_root, n_points=16, fiber_points=8, fiber_twist=1.0)

    result = subprocess.run(
        [
            str(SCRIPT_PATH),
            "parallel_transport_s2_classical",
            "--off-screen-smoke",
            "--dry-run",
        ],
        cwd=REPO_ROOT,
        env={
            **dict(**__import__("os").environ),
            "VIZ_RUN_ROOT_TRANSPORT": str(transport_root),
            "VIZ_RUN_ROOT_HOPF": str(hopf_root),
            "VIZ_VIEWER_PYTHON": sys.executable,
        },
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["best_run"]["sim_name"] == "parallel_transport_s2_classical"
    assert payload["best_run"]["run_id"] == "script_transport_demo"
    assert payload["launch_result"]["off_screen_smoke"] is True
    assert payload["launch_result"]["executed"] is False


def test_view_best_replay_script_forwards_consumer_flag(tmp_path: Path) -> None:
    transport = _load_module(TRANSPORT_EXPORTER_PATH, "transport_s2_exporter")
    hopf = _load_module(HOPF_EXPORTER_PATH, "hopf_bundle_exporter")
    transport_root = tmp_path / "transport_root"
    hopf_root = tmp_path / "hopf_root"
    transport_run = transport.export_transport_s2("script_transport_demo", transport_root, steps_per_arc=8)
    hopf.export_hopf_bundle("script_hopf_demo", hopf_root, n_points=16, fiber_points=8, fiber_twist=1.0)

    manifest_path = transport_run / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["eligible_consumers"] = manifest["eligible_consumers"] + ["viewer_surface_smoke"]
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    result = subprocess.run(
        [
            str(SCRIPT_PATH),
            "parallel_transport_s2_classical",
            "--consumer",
            "viewer_surface_smoke",
            "--off-screen-smoke",
            "--dry-run",
        ],
        cwd=REPO_ROOT,
        env={
            **dict(**__import__("os").environ),
            "VIZ_RUN_ROOT_TRANSPORT": str(transport_root),
            "VIZ_RUN_ROOT_HOPF": str(hopf_root),
            "VIZ_VIEWER_PYTHON": sys.executable,
        },
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["best_run"]["consumer"] == "viewer_surface_smoke"
    assert payload["launch_result"]["consumer"] == "viewer_surface_smoke"
    assert payload["launch_result"]["consumer_admission"]["admitted"] is True
