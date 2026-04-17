from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TRANSPORT_EXPORTER_PATH = REPO_ROOT / "system_v4" / "visualization" / "exporters" / "transport_s2.py"
HOPF_EXPORTER_PATH = REPO_ROOT / "system_v4" / "visualization" / "exporters" / "hopf_bundle.py"
ACTION_BUNDLE_PATH = REPO_ROOT / "system_v4" / "visualization" / "action_bundle.py"
sys.path.insert(0, str(REPO_ROOT))


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_write_action_bundle_creates_json_and_shell_outputs(tmp_path: Path) -> None:
    transport = _load_module(TRANSPORT_EXPORTER_PATH, "transport_s2_exporter")
    hopf = _load_module(HOPF_EXPORTER_PATH, "hopf_bundle_exporter")
    bundle = _load_module(ACTION_BUNDLE_PATH, "viz_action_bundle")

    transport_root = tmp_path / "transport_root"
    hopf_root = tmp_path / "hopf_root"
    transport.export_transport_s2("bundle_transport_best", transport_root, steps_per_arc=8)
    transport.export_transport_s2("bundle_transport_dupe", transport_root, steps_per_arc=8)
    broken_hopf = hopf.export_hopf_bundle("bundle_hopf_old", hopf_root, n_points=16, fiber_points=8, fiber_twist=1.5)
    hopf.export_hopf_bundle("bundle_hopf_new", hopf_root, n_points=16, fiber_points=8, fiber_twist=1.5)

    frame_path = sorted((broken_hopf / "frames").glob("*.json"))[-1]
    frame_payload = json.loads(frame_path.read_text(encoding="utf-8"))
    del frame_payload["entities"][0]["projected_s3_xyz"]
    frame_path.write_text(json.dumps(frame_payload, indent=2), encoding="utf-8")

    out_dir = tmp_path / "bundle_out"
    result = bundle.write_action_bundle([transport_root, hopf_root], out_dir, prefix="demo_bundle")

    json_path = Path(result["json_path"])
    script_path = Path(result["script_path"])
    assert json_path.exists()
    assert script_path.exists()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["summary"]["reexport_command_count"] == 1
    assert payload["summary"]["archive_command_count"] == 1

    shell = script_path.read_text(encoding="utf-8")
    assert shell.startswith("#!/usr/bin/env bash")
    assert "set -euo pipefail" in shell
    assert "python3 -m system_v4.visualization.cli export hopf_bundle" in shell
    assert "python3 -m system_v4.visualization.cli validate" in shell
    assert "python3 -m system_v4.visualization.cli compare" in shell
    assert "mkdir -p" in shell
    assert "mv " in shell


def test_render_action_bundle_write_result_mentions_written_paths(tmp_path: Path) -> None:
    transport = _load_module(TRANSPORT_EXPORTER_PATH, "transport_s2_exporter")
    hopf = _load_module(HOPF_EXPORTER_PATH, "hopf_bundle_exporter")
    bundle = _load_module(ACTION_BUNDLE_PATH, "viz_action_bundle")

    transport_root = tmp_path / "transport_root"
    hopf_root = tmp_path / "hopf_root"
    transport.export_transport_s2("bundle_render_transport", transport_root, steps_per_arc=8)
    broken_hopf = hopf.export_hopf_bundle("bundle_render_hopf_old", hopf_root, n_points=16, fiber_points=8, fiber_twist=1.0)
    hopf.export_hopf_bundle("bundle_render_hopf_new", hopf_root, n_points=16, fiber_points=8, fiber_twist=1.0)

    frame_path = sorted((broken_hopf / "frames").glob("*.json"))[-1]
    frame_payload = json.loads(frame_path.read_text(encoding="utf-8"))
    del frame_payload["entities"][0]["projected_s3_xyz"]
    frame_path.write_text(json.dumps(frame_payload, indent=2), encoding="utf-8")

    text = bundle.render_action_bundle_write_result(
        [transport_root, hopf_root],
        tmp_path / "bundle_out",
        prefix="render_bundle",
    )

    assert "Bundle Dir:" in text
    assert "JSON:" in text
    assert "Script:" in text
    assert "Commands: re-export=1 | archive=0" in text
