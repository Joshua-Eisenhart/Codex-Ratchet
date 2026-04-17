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


def test_collect_batch_report_counts_valid_and_invalid_runs(tmp_path: Path) -> None:
    transport = _load_module(TRANSPORT_EXPORTER_PATH, "transport_s2_exporter")
    hopf = _load_module(HOPF_EXPORTER_PATH, "hopf_bundle_exporter")
    batch = _load_module(BATCH_REPORTING_PATH, "viz_batch_reporting")

    transport.export_transport_s2("batch_transport", tmp_path / "transport", steps_per_arc=8)
    broken_run = hopf.export_hopf_bundle("batch_hopf_broken", tmp_path / "hopf", n_points=16, fiber_points=8, fiber_twist=1.0)
    hopf.export_hopf_bundle("batch_hopf_best", tmp_path / "hopf", n_points=16, fiber_points=8, fiber_twist=1.0)

    frame_path = sorted((broken_run / "frames").glob("*.json"))[-1]
    frame_payload = json.loads(frame_path.read_text(encoding="utf-8"))
    del frame_payload["entities"][0]["projected_s3_xyz"]
    frame_path.write_text(json.dumps(frame_payload, indent=2), encoding="utf-8")

    report = batch.collect_batch_report(tmp_path)

    assert report["run_count"] == 3
    assert report["valid_count"] == 2
    assert report["invalid_count"] == 1
    assert report["sim_counts"]["parallel_transport_s2_classical"] == 1
    assert report["sim_counts"]["hopf_bundle_lift"] == 2
    assert report["invalid_runs"][0]["run_id"] == "batch_hopf_broken"
    assert report["best_runs_by_sim"]["hopf_bundle_lift"]["run_id"] == "batch_hopf_best"
    stale = {item["run_id"]: item for item in report["stale_candidates"]}
    assert "batch_hopf_broken" in stale
    assert stale["batch_hopf_broken"]["best_run_id"] == "batch_hopf_best"
    assert "invalid" in stale["batch_hopf_broken"]["reasons"]
    assert "missing_projected_frame_point" in stale["batch_hopf_broken"]["reasons"]


def test_render_batch_report_includes_summary_lines(tmp_path: Path) -> None:
    transport = _load_module(TRANSPORT_EXPORTER_PATH, "transport_s2_exporter")
    batch = _load_module(BATCH_REPORTING_PATH, "viz_batch_reporting")

    transport.export_transport_s2("batch_report_transport", tmp_path / "transport", steps_per_arc=8)
    text = batch.render_batch_report(tmp_path)

    assert "Runs: 1" in text
    assert "Valid: 1" in text
    assert "Sim Counts:" in text
    assert "Best Runs By Sim:" in text
    assert "Run Summaries:" in text
    assert "batch_report_transport | parallel_transport_s2_classical" in text
