from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TRANSPORT_EXPORTER_PATH = REPO_ROOT / "system_v4" / "visualization" / "exporters" / "transport_s2.py"
HOPF_EXPORTER_PATH = REPO_ROOT / "system_v4" / "visualization" / "exporters" / "hopf_bundle.py"
STATUS_PATH = REPO_ROOT / "system_v4" / "visualization" / "status.py"
sys.path.insert(0, str(REPO_ROOT))


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_collect_status_report_rolls_up_best_duplicate_and_attention(tmp_path: Path) -> None:
    transport = _load_module(TRANSPORT_EXPORTER_PATH, "transport_s2_exporter")
    hopf = _load_module(HOPF_EXPORTER_PATH, "hopf_bundle_exporter")
    status = _load_module(STATUS_PATH, "viz_status")

    transport_root = tmp_path / "transport_root"
    hopf_root = tmp_path / "hopf_root"
    transport.export_transport_s2("status_transport_best", transport_root, steps_per_arc=8)
    transport.export_transport_s2("status_transport_dupe", transport_root, steps_per_arc=8)
    broken_hopf = hopf.export_hopf_bundle("status_hopf_old", hopf_root, n_points=16, fiber_points=8, fiber_twist=1.0)
    hopf.export_hopf_bundle("status_hopf_new", hopf_root, n_points=16, fiber_points=8, fiber_twist=1.0)

    frame_path = sorted((broken_hopf / "frames").glob("*.json"))[-1]
    frame_payload = json.loads(frame_path.read_text(encoding="utf-8"))
    del frame_payload["entities"][0]["projected_s3_xyz"]
    frame_path.write_text(json.dumps(frame_payload, indent=2), encoding="utf-8")

    report = status.collect_status_report([transport_root, hopf_root])

    assert report["summary"]["run_count"] == 4
    assert report["summary"]["duplicate_group_count"] == 1
    assert report["summary"]["archive_candidate_count"] == 1
    assert report["summary"]["reexport_candidate_count"] == 1

    best_by_sim = {item["sim_name"]: item["run_id"] for item in report["best_runs"]}
    assert best_by_sim["parallel_transport_s2_classical"] in {"status_transport_best", "status_transport_dupe"}
    assert best_by_sim["hopf_bundle_lift"] == "status_hopf_new"

    duplicate_group = report["duplicate_groups"][0]
    duplicate_ids = {item["run_id"] for item in duplicate_group["duplicate_members"]}
    assert duplicate_group["sim_name"] == "parallel_transport_s2_classical"
    assert len(duplicate_ids) == 1

    assert report["reexport_candidates"][0]["run_id"] == "status_hopf_old"


def test_render_status_report_produces_compact_operator_brief(tmp_path: Path) -> None:
    transport = _load_module(TRANSPORT_EXPORTER_PATH, "transport_s2_exporter")
    hopf = _load_module(HOPF_EXPORTER_PATH, "hopf_bundle_exporter")
    status = _load_module(STATUS_PATH, "viz_status")

    transport_root = tmp_path / "transport_root"
    hopf_root = tmp_path / "hopf_root"
    transport.export_transport_s2("status_render_transport", transport_root, steps_per_arc=8)
    broken_hopf = hopf.export_hopf_bundle("status_render_hopf_old", hopf_root, n_points=16, fiber_points=8, fiber_twist=1.0)
    hopf.export_hopf_bundle("status_render_hopf_new", hopf_root, n_points=16, fiber_points=8, fiber_twist=1.0)

    frame_path = sorted((broken_hopf / "frames").glob("*.json"))[-1]
    frame_payload = json.loads(frame_path.read_text(encoding="utf-8"))
    del frame_payload["entities"][0]["projected_s3_xyz"]
    frame_path.write_text(json.dumps(frame_payload, indent=2), encoding="utf-8")

    text = status.render_status_report([transport_root, hopf_root])

    assert "Runs: 3 | valid=2 | invalid=1" in text
    assert "Needs Attention: archive=0 | re-export=1" in text
    assert "Best Runs:" in text
    assert "parallel_transport_s2_classical: status_render_transport" in text
    assert "status=exists" in text
    assert "claim=candidate" in text
    assert "promotion=supporting" in text
    assert "admission=shell-local->pairwise" in text
    assert "consumer_surfaces: eligible=transport_frame_report,shell_local_geometry_inventory" in text
    assert "Re-export:" in text
    assert "Duplicates:" not in text
    assert "status_render_hopf_old" in text
    assert "status_render_hopf_new" in text
