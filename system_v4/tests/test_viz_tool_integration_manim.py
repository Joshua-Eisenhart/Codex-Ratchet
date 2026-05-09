from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PROBE_PATH = REPO_ROOT / "system_v4" / "probes" / "tool_integration_manim.py"
RESULT_PATH = REPO_ROOT / "system_v4" / "probes" / "a2_state" / "sim_results" / "tool_integration_manim_results.json"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_tool_integration_manim_probe_writes_green_results() -> None:
    result = subprocess.run(
        ["python3", str(PROBE_PATH)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    assert payload["name"] == "tool_integration_manim"
    positive = payload["positive"]
    if "manim_low_quality_scene_render" in positive:
        assert payload["classification"] == "canonical"
        assert positive["manim_low_quality_scene_render"]["render_succeeded"] is True
    else:
        assert payload["classification"] == "classical_baseline"
        assert payload["status"] == "skipped_missing_runtime"
        assert positive["positive_import_gate"]["status"] == "skipped"
        assert "manim" in positive["positive_import_gate"]["missing"]
    assert payload["boundary"]["transport_run_without_patch_transitions_stays_scene_safe"]["scene_safe_without_transitions"] is True
