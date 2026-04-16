from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
EXPORTER_PATH = REPO_ROOT / "system_v4" / "visualization" / "exporters" / "transport_s2.py"
sys.path.insert(0, str(REPO_ROOT))


def _load_module():
    spec = importlib.util.spec_from_file_location("transport_s2_exporter", EXPORTER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_export_transport_s2_writes_separate_run_dir(tmp_path: Path) -> None:
    module = _load_module()
    run_dir = module.export_transport_s2("demo_s2_octant", tmp_path, steps_per_arc=8)

    assert run_dir.parent == tmp_path
    assert (run_dir / "run_manifest.json").exists()
    assert (run_dir / "scene.json").exists()
    assert (run_dir / "summary.json").exists()

    frames = sorted((run_dir / "frames").glob("*.json"))
    assert frames

    final_frame = json.loads(frames[-1].read_text(encoding="utf-8"))
    holonomy = final_frame["entities"][0]["scalars"]["accumulated_holonomy"]
    assert abs(abs(holonomy) - (np.pi / 2)) < 5e-2


def test_export_transport_s2_does_not_write_into_sim_results(tmp_path: Path) -> None:
    module = _load_module()
    run_dir = module.export_transport_s2("demo_s2_octant", tmp_path, steps_per_arc=8)

    assert "sim_results" not in str(run_dir)
