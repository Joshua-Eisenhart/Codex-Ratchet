from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
TRANSPORT_EXPORTER_PATH = REPO_ROOT / "system_v4" / "visualization" / "exporters" / "transport_s2.py"
HOPF_EXPORTER_PATH = REPO_ROOT / "system_v4" / "visualization" / "exporters" / "hopf_bundle.py"
ACTION_BUNDLE_PATH = REPO_ROOT / "system_v4" / "visualization" / "action_bundle.py"
ACTION_RUNNER_PATH = REPO_ROOT / "system_v4" / "visualization" / "action_runner.py"
sys.path.insert(0, str(REPO_ROOT))


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_demo_bundle(tmp_path: Path):
    transport = _load_module(TRANSPORT_EXPORTER_PATH, "transport_s2_exporter")
    hopf = _load_module(HOPF_EXPORTER_PATH, "hopf_bundle_exporter")
    bundle = _load_module(ACTION_BUNDLE_PATH, "viz_action_bundle")

    transport_root = tmp_path / "transport_root"
    hopf_root = tmp_path / "hopf_root"
    transport.export_transport_s2("runner_transport_best", transport_root, steps_per_arc=8)
    transport.export_transport_s2("runner_transport_dupe", transport_root, steps_per_arc=8)
    broken_hopf = hopf.export_hopf_bundle("runner_hopf_old", hopf_root, n_points=16, fiber_points=8, fiber_twist=1.0)
    hopf.export_hopf_bundle("runner_hopf_new", hopf_root, n_points=16, fiber_points=8, fiber_twist=1.0)

    frame_path = sorted((broken_hopf / "frames").glob("*.json"))[-1]
    frame_payload = json.loads(frame_path.read_text(encoding="utf-8"))
    del frame_payload["entities"][0]["projected_s3_xyz"]
    frame_path.write_text(json.dumps(frame_payload, indent=2), encoding="utf-8")

    out_dir = tmp_path / "bundle_out"
    result = bundle.write_action_bundle([transport_root, hopf_root], out_dir, prefix="runner_bundle")
    return Path(result["json_path"])


def test_collect_bundle_steps_flattens_named_steps(tmp_path: Path) -> None:
    runner = _load_module(ACTION_RUNNER_PATH, "viz_action_runner")
    bundle_path = _write_demo_bundle(tmp_path)

    report = runner.collect_bundle_steps(bundle_path)

    assert report["summary"]["step_count"] == 5
    step_ids = {item["step_id"] for item in report["steps"]}
    assert "reexport:runner_hopf_old:export" in step_ids
    assert "reexport:runner_hopf_old:validate" in step_ids
    assert "reexport:runner_hopf_old:compare" in step_ids
    assert "archive:runner_transport_dupe:mkdir" in step_ids or "archive:runner_transport_best:mkdir" in step_ids


def test_run_bundle_step_executes_safe_export_step(tmp_path: Path) -> None:
    runner = _load_module(ACTION_RUNNER_PATH, "viz_action_runner")
    bundle_path = _write_demo_bundle(tmp_path)

    result = runner.run_bundle_step(bundle_path, "reexport:runner_hopf_old:export")

    assert result["ok"] is True
    assert result["executed"] is True

    created_run = tmp_path / "hopf_root" / "runner_hopf_old__reexport"
    assert created_run.exists()


def test_run_bundle_step_refuses_archive_without_flag(tmp_path: Path) -> None:
    runner = _load_module(ACTION_RUNNER_PATH, "viz_action_runner")
    bundle_path = _write_demo_bundle(tmp_path)
    report = runner.collect_bundle_steps(bundle_path)
    archive_step = next(item["step_id"] for item in report["steps"] if item["category"] == "archive")

    with pytest.raises(ValueError, match="allow_archive=True"):
        runner.run_bundle_step(bundle_path, archive_step)
