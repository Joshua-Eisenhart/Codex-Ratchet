from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TRANSPORT_EXPORTER_PATH = REPO_ROOT / "system_v4" / "visualization" / "exporters" / "transport_s2.py"
HOPF_EXPORTER_PATH = REPO_ROOT / "system_v4" / "visualization" / "exporters" / "hopf_bundle.py"
ACTION_COMMANDS_PATH = REPO_ROOT / "system_v4" / "visualization" / "action_commands.py"
sys.path.insert(0, str(REPO_ROOT))


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_collect_action_commands_infers_reexport_and_archive_commands(tmp_path: Path) -> None:
    transport = _load_module(TRANSPORT_EXPORTER_PATH, "transport_s2_exporter")
    hopf = _load_module(HOPF_EXPORTER_PATH, "hopf_bundle_exporter")
    action_commands = _load_module(ACTION_COMMANDS_PATH, "viz_action_commands")

    transport_root = tmp_path / "transport_root"
    hopf_root = tmp_path / "hopf_root"
    transport.export_transport_s2("commands_transport_best", transport_root, steps_per_arc=8)
    transport.export_transport_s2("commands_transport_dupe", transport_root, steps_per_arc=8)
    broken_hopf = hopf.export_hopf_bundle("commands_hopf_old", hopf_root, n_points=16, fiber_points=8, fiber_twist=1.25)
    hopf.export_hopf_bundle("commands_hopf_new", hopf_root, n_points=16, fiber_points=8, fiber_twist=1.25)

    frame_path = sorted((broken_hopf / "frames").glob("*.json"))[-1]
    frame_payload = json.loads(frame_path.read_text(encoding="utf-8"))
    del frame_payload["entities"][0]["projected_s3_xyz"]
    frame_path.write_text(json.dumps(frame_payload, indent=2), encoding="utf-8")

    report = action_commands.collect_action_commands([transport_root, hopf_root])

    assert report["summary"]["reexport_command_count"] == 1
    assert report["summary"]["archive_command_count"] == 1

    reexport = report["reexport_commands"][0]
    assert reexport["sim_name"] == "hopf_bundle_lift"
    assert reexport["suggested_run_id"] == "commands_hopf_old__reexport"
    assert "export hopf_bundle" in reexport["export_command"]
    assert "--n-points 16" in reexport["export_command"]
    assert "--fiber-points 8" in reexport["export_command"]
    assert "--fiber-twist 1.25" in reexport["export_command"]
    assert "validate --run" in reexport["validate_command"]
    assert "compare --left" in reexport["compare_command"]

    archive = report["archive_commands"][0]
    assert archive["sim_name"] == "parallel_transport_s2_classical"
    assert "mkdir -p" in archive["mkdir_command"]
    assert "archive" in archive["archive_dir"]
    assert "mv " in archive["move_command"]


def test_render_action_commands_shows_dry_run_commands(tmp_path: Path) -> None:
    transport = _load_module(TRANSPORT_EXPORTER_PATH, "transport_s2_exporter")
    hopf = _load_module(HOPF_EXPORTER_PATH, "hopf_bundle_exporter")
    action_commands = _load_module(ACTION_COMMANDS_PATH, "viz_action_commands")

    transport_root = tmp_path / "transport_root"
    hopf_root = tmp_path / "hopf_root"
    transport.export_transport_s2("commands_render_transport", transport_root, steps_per_arc=8)
    broken_hopf = hopf.export_hopf_bundle("commands_render_hopf_old", hopf_root, n_points=16, fiber_points=8, fiber_twist=1.0)
    hopf.export_hopf_bundle("commands_render_hopf_new", hopf_root, n_points=16, fiber_points=8, fiber_twist=1.0)

    frame_path = sorted((broken_hopf / "frames").glob("*.json"))[-1]
    frame_payload = json.loads(frame_path.read_text(encoding="utf-8"))
    del frame_payload["entities"][0]["projected_s3_xyz"]
    frame_path.write_text(json.dumps(frame_payload, indent=2), encoding="utf-8")

    text = action_commands.render_action_commands([transport_root, hopf_root])

    assert "Run Now Commands:" in text
    assert "Run Later Commands:" not in text
    assert "python3 -m system_v4.visualization.cli export hopf_bundle" in text
    assert "python3 -m system_v4.visualization.cli validate" in text
    assert "python3 -m system_v4.visualization.cli compare" in text
