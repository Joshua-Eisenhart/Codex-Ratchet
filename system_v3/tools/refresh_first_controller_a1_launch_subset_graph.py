#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_spec_graph_python() -> Path:
    return _repo_root() / ".venv_spec_graph" / "bin" / "python"


def _default_family_slice_graphml() -> Path:
    return _repo_root() / "work" / "audit_tmp" / "spec_object_drafts" / "A2_TO_A1_FAMILY_SLICE__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.graphml"


def _default_queue_status_graphml() -> Path:
    return _repo_root() / "work" / "audit_tmp" / "spec_object_drafts" / "A1_QUEUE_STATUS_PACKET__CURRENT__2026_03_15__v1.graphml"


def _default_a1_launch_packet_graphml() -> Path:
    return _repo_root() / "work" / "audit_tmp" / "spec_object_drafts" / "A1_WORKER_LAUNCH_PACKET__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.graphml"


def _default_a1_send_text_companion_graphml() -> Path:
    return _repo_root() / "work" / "audit_tmp" / "spec_object_drafts" / "A1_WORKER_SEND_TEXT_COMPANION__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.graphml"


def _default_a1_launch_handoff_graphml() -> Path:
    return _repo_root() / "work" / "audit_tmp" / "spec_object_drafts" / "A1_WORKER_LAUNCH_HANDOFF__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.graphml"


def _default_a1_launch_spine_graphml() -> Path:
    return _repo_root() / "work" / "audit_tmp" / "spec_object_drafts" / "A1_WORKER_LAUNCH_SPINE__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.graphml"


def _default_a2_controller_launch_packet_graphml() -> Path:
    return _repo_root() / "work" / "audit_tmp" / "spec_object_drafts" / "A2_CONTROLLER_LAUNCH_PACKET__CURRENT__2026_03_12__v1.graphml"


def _default_a2_controller_launch_handoff_graphml() -> Path:
    return _repo_root() / "work" / "audit_tmp" / "spec_object_drafts" / "A2_CONTROLLER_LAUNCH_HANDOFF__CURRENT__2026_03_12__v1.graphml"


def _default_a2_controller_launch_spine_graphml() -> Path:
    return _repo_root() / "work" / "audit_tmp" / "spec_object_drafts" / "A2_CONTROLLER_LAUNCH_SPINE__CURRENT__2026_03_15__v1.graphml"


def _default_out_graphml() -> Path:
    return _repo_root() / "work" / "audit_tmp" / "spec_object_drafts" / "FIRST_CONTROLLER_A1_LAUNCH_SUBSET__CURRENT_AND_SUBSTRATE_BASE__2026_03_15__v1.graphml"


def _require_abs_path(path_str: str, key: str) -> Path:
    path = Path(path_str)
    if not path.is_absolute():
        raise SystemExit(f"non_absolute_{key}")
    return path


def _run_json(cmd: list[str]) -> dict:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise SystemExit((proc.stderr or proc.stdout or "").strip() or f"command_failed:{cmd[0]}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json_stdout:{cmd[0]}:{exc.lineno}:{exc.colno}") from exc


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Refresh the fixed first controller/A1 launch subset GraphML from the current bounded source GraphML surfaces."
    )
    parser.add_argument("--spec-graph-python", default=str(_default_spec_graph_python()))
    parser.add_argument("--family-slice-graphml", default=str(_default_family_slice_graphml()))
    parser.add_argument("--queue-status-graphml", default=str(_default_queue_status_graphml()))
    parser.add_argument("--a1-launch-packet-graphml", default=str(_default_a1_launch_packet_graphml()))
    parser.add_argument("--a1-send-text-companion-graphml", default=str(_default_a1_send_text_companion_graphml()))
    parser.add_argument("--a1-launch-handoff-graphml", default=str(_default_a1_launch_handoff_graphml()))
    parser.add_argument("--a1-launch-spine-graphml", default=str(_default_a1_launch_spine_graphml()))
    parser.add_argument(
        "--a2-controller-launch-packet-graphml",
        default=str(_default_a2_controller_launch_packet_graphml()),
    )
    parser.add_argument(
        "--a2-controller-launch-handoff-graphml",
        default=str(_default_a2_controller_launch_handoff_graphml()),
    )
    parser.add_argument(
        "--a2-controller-launch-spine-graphml",
        default=str(_default_a2_controller_launch_spine_graphml()),
    )
    parser.add_argument("--out-graphml", default=str(_default_out_graphml()))
    args = parser.parse_args(argv)

    repo_root = _repo_root()
    spec_graph_python = _require_abs_path(args.spec_graph_python, "spec_graph_python")
    if not spec_graph_python.exists():
        raise SystemExit(f"missing_path_spec_graph_python:{spec_graph_python}")

    out_graphml = _require_abs_path(args.out_graphml, "out_graphml")
    compile_result = _run_json(
        [
            str(spec_graph_python),
            str(repo_root / "system_v3" / "tools" / "compile_first_controller_a1_launch_subset_graph.py"),
            "--family-slice-graphml",
            str(_require_abs_path(args.family_slice_graphml, "family_slice_graphml")),
            "--queue-status-graphml",
            str(_require_abs_path(args.queue_status_graphml, "queue_status_graphml")),
            "--a1-launch-packet-graphml",
            str(_require_abs_path(args.a1_launch_packet_graphml, "a1_launch_packet_graphml")),
            "--a1-send-text-companion-graphml",
            str(_require_abs_path(args.a1_send_text_companion_graphml, "a1_send_text_companion_graphml")),
            "--a1-launch-handoff-graphml",
            str(_require_abs_path(args.a1_launch_handoff_graphml, "a1_launch_handoff_graphml")),
            "--a1-launch-spine-graphml",
            str(_require_abs_path(args.a1_launch_spine_graphml, "a1_launch_spine_graphml")),
            "--a2-controller-launch-packet-graphml",
            str(_require_abs_path(args.a2_controller_launch_packet_graphml, "a2_controller_launch_packet_graphml")),
            "--a2-controller-launch-handoff-graphml",
            str(_require_abs_path(args.a2_controller_launch_handoff_graphml, "a2_controller_launch_handoff_graphml")),
            "--a2-controller-launch-spine-graphml",
            str(_require_abs_path(args.a2_controller_launch_spine_graphml, "a2_controller_launch_spine_graphml")),
            "--out-graphml",
            str(out_graphml),
        ]
    )
    payload = {
        "schema": "ACTIVE_FIRST_CONTROLLER_A1_LAUNCH_SUBSET_REFRESH_RESULT_v1",
        "status": "CREATED",
        "out_graphml": str(out_graphml),
        "compile_result": compile_result,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
