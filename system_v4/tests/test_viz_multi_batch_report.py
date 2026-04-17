from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TRANSPORT_EXPORTER_PATH = REPO_ROOT / "system_v4" / "visualization" / "exporters" / "transport_s2.py"
HOPF_EXPORTER_PATH = REPO_ROOT / "system_v4" / "visualization" / "exporters" / "hopf_bundle.py"
BATCH_REPORTING_PATH = REPO_ROOT / "system_v4" / "visualization" / "batch_reporting.py"
sys.path.insert(0, str(REPO_ROOT))


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_collect_multi_batch_report_groups_runs_across_roots(tmp_path: Path) -> None:
    transport = _load_module(TRANSPORT_EXPORTER_PATH, "transport_s2_exporter")
    hopf = _load_module(HOPF_EXPORTER_PATH, "hopf_bundle_exporter")
    batch = _load_module(BATCH_REPORTING_PATH, "viz_batch_reporting")

    transport_root = tmp_path / "transport_root"
    hopf_root = tmp_path / "hopf_root"
    transport.export_transport_s2("multi_transport", transport_root, steps_per_arc=8)
    broken_hopf = hopf.export_hopf_bundle("multi_hopf_old", hopf_root, n_points=16, fiber_points=8, fiber_twist=1.0)
    hopf.export_hopf_bundle("multi_hopf_new", hopf_root, n_points=16, fiber_points=8, fiber_twist=1.0)

    frame_path = sorted((broken_hopf / "frames").glob("*.json"))[-1]
    frame_payload = json.loads(frame_path.read_text(encoding="utf-8"))
    del frame_payload["entities"][0]["projected_s3_xyz"]
    frame_path.write_text(json.dumps(frame_payload, indent=2), encoding="utf-8")

    report = batch.collect_multi_batch_report([transport_root, hopf_root])

    assert report["root_count"] == 2
    assert report["run_count"] == 3
    assert report["valid_count"] == 2
    assert report["invalid_count"] == 1
    assert report["best_runs_by_sim"]["parallel_transport_s2_classical"]["run_id"] == "multi_transport"
    assert report["best_runs_by_sim"]["hopf_bundle_lift"]["run_id"] == "multi_hopf_new"
    stale = {item["run_id"]: item for item in report["stale_candidates"]}
    assert stale["multi_hopf_old"]["best_run_id"] == "multi_hopf_new"
    assert "missing_projected_frame_point" in stale["multi_hopf_old"]["reasons"]


def test_render_multi_batch_report_mentions_roots_and_best_runs(tmp_path: Path) -> None:
    transport = _load_module(TRANSPORT_EXPORTER_PATH, "transport_s2_exporter")
    hopf = _load_module(HOPF_EXPORTER_PATH, "hopf_bundle_exporter")
    batch = _load_module(BATCH_REPORTING_PATH, "viz_batch_reporting")

    transport_root = tmp_path / "transport_root"
    hopf_root = tmp_path / "hopf_root"
    transport.export_transport_s2("multi_transport_report", transport_root, steps_per_arc=8)
    hopf.export_hopf_bundle("multi_hopf_report", hopf_root, n_points=16, fiber_points=8, fiber_twist=1.0)

    text = batch.render_multi_batch_report([transport_root, hopf_root])

    assert "Roots:" in text
    assert str(transport_root) in text
    assert str(hopf_root) in text
    assert "Root Summaries:" in text
    assert "Best Runs By Sim:" in text
    assert "multi_hopf_report" in text
    assert "multi_transport_report" in text
