from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TRANSPORT_EXPORTER_PATH = REPO_ROOT / "system_v4" / "visualization" / "exporters" / "transport_s2.py"
ATLAS_EXPORTER_PATH = REPO_ROOT / "system_v4" / "visualization" / "exporters" / "synthetic_atlas.py"
AUDIT_PATH = REPO_ROOT / "system_v4" / "visualization" / "admission_audit.py"
STATUS_PATH = REPO_ROOT / "system_v4" / "visualization" / "status.py"
sys.path.insert(0, str(REPO_ROOT))


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_admission_audit_flags_missing_lower_stage_support(tmp_path: Path) -> None:
    atlas = _load_module(ATLAS_EXPORTER_PATH, "synthetic_atlas_exporter")
    audit = _load_module(AUDIT_PATH, "viz_admission_audit")

    run_dir = atlas.export_synthetic_atlas("atlas_only", tmp_path, frame_count=5)
    report = audit.audit_run_admission(run_dir, [run_dir])

    assert report["ok"] is False
    assert "shell-local" in report["missing_lower_stages"]


def test_admission_audit_accepts_supported_higher_stage_run(tmp_path: Path) -> None:
    transport = _load_module(TRANSPORT_EXPORTER_PATH, "transport_exporter")
    atlas = _load_module(ATLAS_EXPORTER_PATH, "synthetic_atlas_exporter")
    audit = _load_module(AUDIT_PATH, "viz_admission_audit")

    lower = transport.export_transport_s2("transport_support", tmp_path, steps_per_arc=8)
    higher = atlas.export_synthetic_atlas("atlas_supported", tmp_path, frame_count=5)
    report = audit.audit_run_admission(higher, [lower, higher])

    assert report["ok"] is True
    assert report["missing_lower_stages"] == []


def test_status_report_mentions_admission_warnings(tmp_path: Path) -> None:
    atlas = _load_module(ATLAS_EXPORTER_PATH, "synthetic_atlas_exporter")
    status = _load_module(STATUS_PATH, "viz_status")

    atlas.export_synthetic_atlas("atlas_warning", tmp_path, frame_count=5)
    text = status.render_status_report([tmp_path])

    assert "Admission Warnings: 1" in text
    assert "missing_lower_stages=shell-local" in text
