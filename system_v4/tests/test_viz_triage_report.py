from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TRANSPORT_EXPORTER_PATH = REPO_ROOT / "system_v4" / "visualization" / "exporters" / "transport_s2.py"
HOPF_EXPORTER_PATH = REPO_ROOT / "system_v4" / "visualization" / "exporters" / "hopf_bundle.py"
TRIAGE_PATH = REPO_ROOT / "system_v4" / "visualization" / "triage.py"
sys.path.insert(0, str(REPO_ROOT))


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_collect_triage_report_classifies_keep_archive_and_reexport(tmp_path: Path) -> None:
    transport = _load_module(TRANSPORT_EXPORTER_PATH, "transport_s2_exporter")
    hopf = _load_module(HOPF_EXPORTER_PATH, "hopf_bundle_exporter")
    triage = _load_module(TRIAGE_PATH, "viz_triage")

    transport_root = tmp_path / "transport_root"
    hopf_root = tmp_path / "hopf_root"
    transport.export_transport_s2("triage_transport_best", transport_root, steps_per_arc=8)
    transport.export_transport_s2("triage_transport_dupe", transport_root, steps_per_arc=8)
    broken_hopf = hopf.export_hopf_bundle("triage_hopf_old", hopf_root, n_points=16, fiber_points=8, fiber_twist=1.0)
    hopf.export_hopf_bundle("triage_hopf_new", hopf_root, n_points=16, fiber_points=8, fiber_twist=1.0)

    frame_path = sorted((broken_hopf / "frames").glob("*.json"))[-1]
    frame_payload = json.loads(frame_path.read_text(encoding="utf-8"))
    del frame_payload["entities"][0]["projected_s3_xyz"]
    frame_path.write_text(json.dumps(frame_payload, indent=2), encoding="utf-8")

    report = triage.collect_triage_report([transport_root, hopf_root])

    assert report["summary"]["keep_count"] == 2
    assert report["summary"]["archive_candidate_count"] == 1
    assert report["summary"]["reexport_candidate_count"] == 1

    keep_ids = {item["run_id"] for item in report["keep_runs"]}
    assert "triage_hopf_new" in keep_ids
    assert "triage_transport_best" in keep_ids or "triage_transport_dupe" in keep_ids

    archive = report["archive_candidates"][0]
    assert archive["reason"] == "duplicate_of_canonical"
    assert archive["run_id"] in {"triage_transport_best", "triage_transport_dupe"}
    assert archive["canonical_run_id"] in {"triage_transport_best", "triage_transport_dupe"}
    assert archive["run_id"] != archive["canonical_run_id"]

    reexport = report["reexport_candidates"][0]
    assert reexport["run_id"] == "triage_hopf_old"
    assert "missing_projected_frame_point" in reexport["stale_reasons"]
    assert reexport["best_run_id"] == "triage_hopf_new"


def test_render_triage_report_mentions_sections_and_recommendations(tmp_path: Path) -> None:
    transport = _load_module(TRANSPORT_EXPORTER_PATH, "transport_s2_exporter")
    hopf = _load_module(HOPF_EXPORTER_PATH, "hopf_bundle_exporter")
    triage = _load_module(TRIAGE_PATH, "viz_triage")

    transport_root = tmp_path / "transport_root"
    hopf_root = tmp_path / "hopf_root"
    transport.export_transport_s2("triage_render_transport", transport_root, steps_per_arc=8)
    broken_hopf = hopf.export_hopf_bundle("triage_render_hopf_old", hopf_root, n_points=16, fiber_points=8, fiber_twist=1.0)
    hopf.export_hopf_bundle("triage_render_hopf_new", hopf_root, n_points=16, fiber_points=8, fiber_twist=1.0)

    frame_path = sorted((broken_hopf / "frames").glob("*.json"))[-1]
    frame_payload = json.loads(frame_path.read_text(encoding="utf-8"))
    del frame_payload["entities"][0]["projected_s3_xyz"]
    frame_path.write_text(json.dumps(frame_payload, indent=2), encoding="utf-8")

    text = triage.render_triage_report([transport_root, hopf_root])

    assert "Keep:" in text
    assert "Re-export Candidates:" in text
    assert "triage_render_hopf_old" in text
    assert "triage_render_hopf_new" in text
    assert "reason=best_run_for_sim_family" in text
    assert "target=triage_render_hopf_new" in text


def test_collect_triage_report_demotes_invalid_run_when_valid_replacement_exists(tmp_path: Path) -> None:
    transport = _load_module(TRANSPORT_EXPORTER_PATH, "transport_s2_exporter")
    hopf = _load_module(HOPF_EXPORTER_PATH, "hopf_bundle_exporter")
    triage = _load_module(TRIAGE_PATH, "viz_triage")

    transport_root = tmp_path / "transport_root"
    hopf_root = tmp_path / "hopf_root"
    transport.export_transport_s2("triage_replacement_transport", transport_root, steps_per_arc=8)
    broken_hopf = hopf.export_hopf_bundle("triage_replacement_hopf_old", hopf_root, n_points=16, fiber_points=8, fiber_twist=1.0)
    hopf.export_hopf_bundle("triage_replacement_hopf_best", hopf_root, n_points=16, fiber_points=8, fiber_twist=1.0)
    hopf.export_hopf_bundle("triage_replacement_hopf_refresh", hopf_root, n_points=16, fiber_points=8, fiber_twist=1.0)

    frame_path = sorted((broken_hopf / "frames").glob("*.json"))[-1]
    frame_payload = json.loads(frame_path.read_text(encoding="utf-8"))
    del frame_payload["entities"][0]["projected_s3_xyz"]
    frame_path.write_text(json.dumps(frame_payload, indent=2), encoding="utf-8")

    report = triage.collect_triage_report([transport_root, hopf_root])

    assert report["summary"]["reexport_candidate_count"] == 0
    stale_archive = {item["run_id"]: item for item in report["archive_candidates"]}
    assert stale_archive["triage_replacement_hopf_old"]["reason"] == "superseded_invalid_run"
