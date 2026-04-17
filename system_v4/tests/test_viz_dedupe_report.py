from __future__ import annotations

import importlib.util
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


def test_collect_multi_batch_report_exposes_duplicate_groups(tmp_path: Path) -> None:
    transport = _load_module(TRANSPORT_EXPORTER_PATH, "transport_s2_exporter")
    hopf = _load_module(HOPF_EXPORTER_PATH, "hopf_bundle_exporter")
    batch = _load_module(BATCH_REPORTING_PATH, "viz_batch_reporting")

    transport_root = tmp_path / "transport_root"
    hopf_root = tmp_path / "hopf_root"
    transport.export_transport_s2("dupe_transport_a", transport_root, steps_per_arc=8)
    transport.export_transport_s2("dupe_transport_b", transport_root, steps_per_arc=8)
    hopf.export_hopf_bundle("dupe_hopf", hopf_root, n_points=16, fiber_points=8, fiber_twist=1.0)

    report = batch.collect_multi_batch_report([transport_root, hopf_root])

    assert len(report["duplicate_groups"]) == 1
    duplicate_group = report["duplicate_groups"][0]
    assert duplicate_group["sim_name"] == "parallel_transport_s2_classical"
    member_ids = {item["run_id"] for item in duplicate_group["members"]}
    assert member_ids == {"dupe_transport_a", "dupe_transport_b"}
    assert duplicate_group["canonical_run_id"] in member_ids
    assert "canonical_reason" in duplicate_group
    assert "deterministic" in duplicate_group["canonical_reason"]


def test_render_multi_dedupe_report_mentions_canonical_and_members(tmp_path: Path) -> None:
    transport = _load_module(TRANSPORT_EXPORTER_PATH, "transport_s2_exporter")
    batch = _load_module(BATCH_REPORTING_PATH, "viz_batch_reporting")

    transport_root = tmp_path / "transport_root"
    transport.export_transport_s2("dupe_transport_report_a", transport_root, steps_per_arc=8)
    transport.export_transport_s2("dupe_transport_report_b", transport_root, steps_per_arc=8)

    text = batch.render_multi_dedupe_report([transport_root])

    assert "Duplicate Groups: 1" in text
    assert "parallel_transport_s2_classical: canonical=" in text
    assert "reason=all replay fields matched; canonical chosen by deterministic root/run_id fallback" in text
    assert "dupe_transport_report_a" in text
    assert "dupe_transport_report_b" in text
