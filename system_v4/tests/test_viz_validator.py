from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
EXPORTER_PATH = REPO_ROOT / "system_v4" / "visualization" / "exporters" / "transport_s2.py"
VALIDATOR_PATH = REPO_ROOT / "system_v4" / "visualization" / "validator.py"
sys.path.insert(0, str(REPO_ROOT))


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_validator_accepts_valid_transport_run(tmp_path: Path) -> None:
    exporter = _load_module(EXPORTER_PATH, "transport_s2_exporter")
    validator = _load_module(VALIDATOR_PATH, "viz_validator")

    run_dir = exporter.export_transport_s2("valid_demo", tmp_path, steps_per_arc=8)
    report = validator.validate_run_dir(run_dir)

    assert report["ok"] is True
    assert report["errors"] == []


def test_validator_fails_when_manifest_is_missing(tmp_path: Path) -> None:
    exporter = _load_module(EXPORTER_PATH, "transport_s2_exporter")
    validator = _load_module(VALIDATOR_PATH, "viz_validator")

    run_dir = exporter.export_transport_s2("missing_manifest", tmp_path, steps_per_arc=8)
    (run_dir / "run_manifest.json").unlink()

    report = validator.validate_run_dir(run_dir)
    assert report["ok"] is False
    assert report["errors"]


def test_validator_fails_when_holonomy_capability_has_no_scalar(tmp_path: Path) -> None:
    exporter = _load_module(EXPORTER_PATH, "transport_s2_exporter")
    validator = _load_module(VALIDATOR_PATH, "viz_validator")

    run_dir = exporter.export_transport_s2("broken_holonomy", tmp_path, steps_per_arc=8)

    frame_path = sorted((run_dir / "frames").glob("*.json"))[-1]
    frame_payload = json.loads(frame_path.read_text(encoding="utf-8"))
    del frame_payload["entities"][0]["scalars"]["accumulated_holonomy"]
    frame_path.write_text(json.dumps(frame_payload, indent=2), encoding="utf-8")

    report = validator.validate_run_dir(run_dir)
    assert report["ok"] is False
    assert any("holonomy" in error.lower() for error in report["errors"])
