#!/usr/bin/env python3
"""
Tier VIZ slice 6 capability sim for Manim + manim_export interop.

This probe checks that the Hermes Manim skill surface is usable through the local
Manim runtime, that replay-manifest data can be pulled through
system_v4.visualization.manim_export, and that the prototype atlas-transition
scene renders from that exported payload.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict

classification = "canonical"
NAME = "tool_integration_manim"
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

TOOL_MANIFEST = {
    "manim": {
        "tried": False,
        "used": False,
        "reason": "Manim is the load-bearing rendering engine that admits or excludes whether replay metadata can be turned into a concrete explainer scene rather than remaining a decorative export.",
    },
    "manim_export": {
        "tried": False,
        "used": False,
        "reason": "manim_export is the load-bearing replay-to-explainer bridge that selects constraint/probe/exclusion/survivor data for scene construction.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "manim": "load_bearing",
    "manim_export": "load_bearing",
}

try:
    import manim  # noqa: F401

    TOOL_MANIFEST["manim"]["tried"] = True
except ImportError:
    manim = None
    TOOL_MANIFEST["manim"]["reason"] = "Manim import failed on this machine; runtime capability cannot be admitted."

try:
    from system_v4.visualization.exporters.synthetic_atlas import export_synthetic_atlas
    from system_v4.visualization.exporters.transport_s2 import export_transport_s2
    from system_v4.visualization.manim_export import collect_manim_export
    from scripts.render_manim_atlas_transition import load_scene_payload

    TOOL_MANIFEST["manim_export"]["tried"] = True
except ImportError:
    export_synthetic_atlas = None
    export_transport_s2 = None
    collect_manim_export = None
    load_scene_payload = None
    TOOL_MANIFEST["manim_export"]["reason"] = "Visualization export or Manim scene bridge imports failed; replay-to-scene capability cannot be admitted."


def _mark_used(*tools: str) -> None:
    for tool in tools:
        TOOL_MANIFEST[tool]["used"] = True


def _serialize(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _serialize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize(v) for v in value]
    return value


def _integration_ready() -> bool:
    return all(TOOL_MANIFEST[name]["tried"] for name in ("manim", "manim_export")) and manim is not None and collect_manim_export is not None and load_scene_payload is not None


def _gate_results(section: str) -> Dict[str, Any]:
    missing = [name for name, payload in TOOL_MANIFEST.items() if not payload["tried"]]
    return {f"{section}_import_gate": {"status": "skipped", "missing": missing}}


def _render_scene(run_dir: Path, media_dir: Path) -> subprocess.CompletedProcess[str]:
    command = [
        "python3",
        "-m",
        "manim",
        "-ql",
        "scripts/render_manim_atlas_transition.py",
        "AtlasTransitionOverview",
        "--media_dir",
        str(media_dir),
    ]
    env = {**os.environ, "MANIM_VIZ_RUN_DIR": str(run_dir)}
    return subprocess.run(command, capture_output=True, text=True, check=False, env=env, cwd=REPO_ROOT)


def run_positive_tests() -> Dict[str, Any]:
    if not _integration_ready():
        return _gate_results("positive")

    with tempfile.TemporaryDirectory(prefix="tool_integration_manim_") as tmp_dir:
        tmp_path = Path(tmp_dir)
        run_dir = export_synthetic_atlas("manim_probe_atlas", tmp_path, frame_count=5)
        export_payload = collect_manim_export(run_dir)
        scene_payload = load_scene_payload(run_dir)
        media_dir = tmp_path / "media"
        rendered = _render_scene(run_dir, media_dir)
        video_paths = sorted(media_dir.rglob("AtlasTransitionOverview.mp4"))
        _mark_used("manim", "manim_export")
        return {
            "manim_export_feeds_scene_payload": {
                "constraint_set": export_payload.get("constraint_set"),
                "probe_family": export_payload.get("probe_family"),
                "patch_count": len(scene_payload.get("patches", [])),
                "transition_count": len(scene_payload.get("transitions", [])),
                "has_mesh_geometry": any(item.get("entity_kind") == "mesh_patch" for item in export_payload.get("admitted_survivors", [])),
            },
            "manim_low_quality_scene_render": {
                "returncode": rendered.returncode,
                "stdout_tail": rendered.stdout.splitlines()[-5:],
                "stderr_tail": rendered.stderr.splitlines()[-5:],
                "video_paths": [str(path) for path in video_paths],
                "render_succeeded": rendered.returncode == 0 and bool(video_paths),
            },
        }


def run_negative_tests() -> Dict[str, Any]:
    if collect_manim_export is None or load_scene_payload is None:
        return _gate_results("negative")

    results: Dict[str, Any] = {}
    missing_run = Path("/tmp/definitely_missing_manim_run")
    try:
        collect_manim_export(missing_run)
        results["missing_run_is_excluded_before_scene_build"] = {"status": "unexpected_success"}
    except FileNotFoundError as exc:
        _mark_used("manim_export")
        results["missing_run_is_excluded_before_scene_build"] = {
            "status": "file_not_found",
            "detail": str(exc),
        }

    previous = os.environ.pop("MANIM_VIZ_RUN_DIR", None)
    try:
        try:
            load_scene_payload(Path("/tmp/does_not_matter"))
            scene_status = "unexpected_success"
            detail = "scene payload loaded without a real run"
        except FileNotFoundError as exc:
            scene_status = "file_not_found"
            detail = str(exc)
        results["scene_bridge_rejects_missing_run_artifacts"] = {
            "status": scene_status,
            "detail": detail,
        }
    finally:
        if previous is not None:
            os.environ["MANIM_VIZ_RUN_DIR"] = previous

    return results


def run_boundary_tests() -> Dict[str, Any]:
    if collect_manim_export is None or load_scene_payload is None or export_transport_s2 is None:
        return _gate_results("boundary")

    with tempfile.TemporaryDirectory(prefix="tool_integration_manim_boundary_") as tmp_dir:
        tmp_path = Path(tmp_dir)
        run_dir = export_transport_s2("manim_probe_transport", tmp_path, steps_per_arc=8)
        scene_payload = load_scene_payload(run_dir)
        _mark_used("manim_export")
        return {
            "transport_run_without_patch_transitions_stays_scene_safe": {
                "patch_count": len(scene_payload.get("patches", [])),
                "transition_count": len(scene_payload.get("transitions", [])),
                "status_label": scene_payload.get("status_label"),
                "scene_safe_without_transitions": len(scene_payload.get("transitions", [])) == 0,
            }
        }


if __name__ == "__main__":
    results = {
        "name": NAME,
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": _serialize(run_positive_tests()),
        "negative": _serialize(run_negative_tests()),
        "boundary": _serialize(run_boundary_tests()),
    }

    out_dir = Path(__file__).resolve().parent / "a2_state" / "sim_results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{NAME}_results.json"
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Results written to {out_path}")
