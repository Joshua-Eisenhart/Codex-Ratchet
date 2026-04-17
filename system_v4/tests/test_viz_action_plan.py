from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TRANSPORT_EXPORTER_PATH = REPO_ROOT / "system_v4" / "visualization" / "exporters" / "transport_s2.py"
HOPF_EXPORTER_PATH = REPO_ROOT / "system_v4" / "visualization" / "exporters" / "hopf_bundle.py"
ACTION_PLAN_PATH = REPO_ROOT / "system_v4" / "visualization" / "action_plan.py"
sys.path.insert(0, str(REPO_ROOT))


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_collect_action_plan_groups_keep_now_and_later(tmp_path: Path) -> None:
    transport = _load_module(TRANSPORT_EXPORTER_PATH, "transport_s2_exporter")
    hopf = _load_module(HOPF_EXPORTER_PATH, "hopf_bundle_exporter")
    action_plan = _load_module(ACTION_PLAN_PATH, "viz_action_plan")

    transport_root = tmp_path / "transport_root"
    hopf_root = tmp_path / "hopf_root"
    transport.export_transport_s2("plan_transport_best", transport_root, steps_per_arc=8)
    transport.export_transport_s2("plan_transport_dupe", transport_root, steps_per_arc=8)
    broken_hopf = hopf.export_hopf_bundle("plan_hopf_old", hopf_root, n_points=16, fiber_points=8, fiber_twist=1.0)
    hopf.export_hopf_bundle("plan_hopf_new", hopf_root, n_points=16, fiber_points=8, fiber_twist=1.0)

    frame_path = sorted((broken_hopf / "frames").glob("*.json"))[-1]
    frame_payload = json.loads(frame_path.read_text(encoding="utf-8"))
    del frame_payload["entities"][0]["projected_s3_xyz"]
    frame_path.write_text(json.dumps(frame_payload, indent=2), encoding="utf-8")

    report = action_plan.collect_action_plan([transport_root, hopf_root])

    assert report["summary"]["keep_count"] == 2
    assert report["summary"]["now_count"] == 1
    assert report["summary"]["later_count"] == 1

    keep_ids = {item["run_id"] for item in report["keep_canonical"]}
    assert "plan_hopf_new" in keep_ids
    assert "plan_transport_best" in keep_ids or "plan_transport_dupe" in keep_ids

    do_now = report["do_now"][0]
    assert do_now["action"] == "re_export"
    assert do_now["run_id"] == "plan_hopf_old"
    assert do_now["target_run_id"] == "plan_hopf_new"

    do_later = report["do_later"][0]
    assert do_later["action"] == "archive_candidate"
    assert do_later["reason"] == "duplicate_of_canonical"
    assert do_later["run_id"] in {"plan_transport_best", "plan_transport_dupe"}


def test_render_action_plan_produces_operator_facing_sections(tmp_path: Path) -> None:
    transport = _load_module(TRANSPORT_EXPORTER_PATH, "transport_s2_exporter")
    hopf = _load_module(HOPF_EXPORTER_PATH, "hopf_bundle_exporter")
    action_plan = _load_module(ACTION_PLAN_PATH, "viz_action_plan")

    transport_root = tmp_path / "transport_root"
    hopf_root = tmp_path / "hopf_root"
    transport.export_transport_s2("plan_render_transport", transport_root, steps_per_arc=8)
    broken_hopf = hopf.export_hopf_bundle("plan_render_hopf_old", hopf_root, n_points=16, fiber_points=8, fiber_twist=1.0)
    hopf.export_hopf_bundle("plan_render_hopf_new", hopf_root, n_points=16, fiber_points=8, fiber_twist=1.0)

    frame_path = sorted((broken_hopf / "frames").glob("*.json"))[-1]
    frame_payload = json.loads(frame_path.read_text(encoding="utf-8"))
    del frame_payload["entities"][0]["projected_s3_xyz"]
    frame_path.write_text(json.dumps(frame_payload, indent=2), encoding="utf-8")

    text = action_plan.render_action_plan([transport_root, hopf_root])

    assert "Plan: keep=2 | now=1 | later=0" in text
    assert "Keep Canonical:" in text
    assert "Do Now:" in text
    assert "Do Later:" not in text
    assert "re-export plan_render_hopf_old" in text
    assert "plan_render_hopf_new" in text
