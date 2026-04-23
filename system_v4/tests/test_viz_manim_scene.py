from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
ATLAS_EXPORTER_PATH = REPO_ROOT / "system_v4" / "visualization" / "exporters" / "synthetic_atlas.py"
TRANSPORT_EXPORTER_PATH = REPO_ROOT / "system_v4" / "visualization" / "exporters" / "transport_s2.py"
SCRIPT_PATH = REPO_ROOT / "scripts" / "render_manim_atlas_transition.py"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_load_scene_payload_extracts_atlas_patches_and_transitions(tmp_path: Path) -> None:
    atlas = _load_module(ATLAS_EXPORTER_PATH, "synthetic_atlas_exporter")
    scene = _load_module(SCRIPT_PATH, "render_manim_atlas_transition")

    run_dir = atlas.export_synthetic_atlas("atlas_manim_scene", tmp_path, frame_count=5)
    payload = scene.load_scene_payload(run_dir)

    assert payload["constraint_set"] == "two_patch_shared_seam_fixture"
    assert len(payload["patches"]) == 2
    assert len(payload["transitions"]) == 2
    assert payload["exclusion_count"] == 1


def test_load_scene_payload_keeps_transport_run_scene_safe(tmp_path: Path) -> None:
    transport = _load_module(TRANSPORT_EXPORTER_PATH, "transport_s2_exporter")
    scene = _load_module(SCRIPT_PATH, "render_manim_atlas_transition")

    run_dir = transport.export_transport_s2("transport_manim_scene", tmp_path, steps_per_arc=8)
    payload = scene.load_scene_payload(run_dir)

    assert payload["constraint_set"] == "sphere_parallel_transport_octant_loop"
    assert payload["patches"] == []
    assert payload["transitions"] == []


def test_manim_scene_renders_from_atlas_export_payload(tmp_path: Path) -> None:
    atlas = _load_module(ATLAS_EXPORTER_PATH, "synthetic_atlas_exporter")

    manim_check = subprocess.run(
        ["python3", "-c", "import importlib.util; import sys; sys.exit(0 if importlib.util.find_spec('manim') else 1)"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if manim_check.returncode != 0:
        pytest.skip("manim runtime unavailable in the active python3 environment")

    run_dir = atlas.export_synthetic_atlas("atlas_manim_render", tmp_path, frame_count=5)
    media_dir = tmp_path / "media"
    result = subprocess.run(
        [
            "python3",
            "-m",
            "manim",
            "-ql",
            str(SCRIPT_PATH),
            "AtlasTransitionOverview",
            "--media_dir",
            str(media_dir),
        ],
        cwd=REPO_ROOT,
        env={**os.environ, "MANIM_VIZ_RUN_DIR": str(run_dir)},
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert list(media_dir.rglob("AtlasTransitionOverview.mp4"))
