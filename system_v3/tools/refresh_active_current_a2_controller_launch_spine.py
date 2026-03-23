#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_packet_json() -> Path:
    return _repo_root() / "system_v3" / "a2_state" / "A2_CONTROLLER_LAUNCH_PACKET__CURRENT__2026_03_12__v1.json"


def _default_gate_result_json() -> Path:
    return _repo_root() / "system_v3" / "a2_state" / "A2_CONTROLLER_LAUNCH_GATE_RESULT__CURRENT__2026_03_12__v1.json"


def _default_send_text_companion_json() -> Path:
    return _repo_root() / "system_v3" / "a2_state" / "A2_CONTROLLER_SEND_TEXT_COMPANION__CURRENT__2026_03_15__v1.json"


def _default_handoff_json() -> Path:
    return _repo_root() / "system_v3" / "a2_state" / "A2_CONTROLLER_LAUNCH_HANDOFF__CURRENT__2026_03_12__v1.json"


def _default_spine_json() -> Path:
    return _repo_root() / "system_v3" / "a2_state" / "A2_CONTROLLER_LAUNCH_SPINE__CURRENT__2026_03_15__v1.json"


def _default_graphml() -> Path:
    return _repo_root() / "work" / "audit_tmp" / "spec_object_drafts" / "A2_CONTROLLER_LAUNCH_SPINE__CURRENT__2026_03_15__v1.graphml"


def _default_schema_json() -> Path:
    return _repo_root() / "work" / "audit_tmp" / "spec_object_drafts" / "A2_CONTROLLER_LAUNCH_SPINE_v1__PYDANTIC_SCHEMA__2026_03_15__v1.json"


def _default_spec_graph_python() -> Path:
    return _repo_root() / ".venv_spec_graph" / "bin" / "python"


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


def _run_path(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise SystemExit((proc.stderr or proc.stdout or "").strip() or f"command_failed:{cmd[0]}")
    return (proc.stdout or "").strip()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Refresh the active current A2 controller launch spine from the current packet, gate result, send-text companion, and handoff."
    )
    parser.add_argument("--packet-json", default=str(_default_packet_json()))
    parser.add_argument("--gate-result-json", default=str(_default_gate_result_json()))
    parser.add_argument("--send-text-companion-json", default=str(_default_send_text_companion_json()))
    parser.add_argument("--handoff-json", default=str(_default_handoff_json()))
    parser.add_argument("--spine-json", default=str(_default_spine_json()))
    parser.add_argument("--spec-graph-python", default=str(_default_spec_graph_python()))
    parser.add_argument("--out-graphml", default=str(_default_graphml()))
    parser.add_argument("--out-schema-json", default=str(_default_schema_json()))
    parser.add_argument("--emit-graphml", action="store_true")
    parser.add_argument("--emit-schema", action="store_true")
    args = parser.parse_args(argv)

    repo_root = _repo_root()
    spec_graph_python = _require_abs_path(args.spec_graph_python, "spec_graph_python")
    if not spec_graph_python.exists():
        raise SystemExit(f"missing_path_spec_graph_python:{spec_graph_python}")

    spine_result = _run_json(
        [
            str(spec_graph_python),
            str(repo_root / "system_v3" / "tools" / "build_a2_controller_launch_spine.py"),
            "--packet-json",
            str(_require_abs_path(args.packet_json, "packet_json")),
            "--gate-result-json",
            str(_require_abs_path(args.gate_result_json, "gate_result_json")),
            "--send-text-companion-json",
            str(_require_abs_path(args.send_text_companion_json, "send_text_companion_json")),
            "--handoff-json",
            str(_require_abs_path(args.handoff_json, "handoff_json")),
            "--out-json",
            str(_require_abs_path(args.spine_json, "spine_json")),
        ]
    )

    payload = {
        "schema": "ACTIVE_A2_CONTROLLER_LAUNCH_SPINE_REFRESH_RESULT_v1",
        "status": "CREATED",
        "spine_json": str(_require_abs_path(args.spine_json, "spine_json")),
        "spine_result": spine_result,
    }

    if args.emit_graphml:
        graphml_path = _require_abs_path(args.out_graphml, "out_graphml")
        _run_path(
            [
                str(spec_graph_python),
                str(repo_root / "system_v3" / "tools" / "export_a2_controller_launch_spine_graph.py"),
                "--spine-json",
                str(_require_abs_path(args.spine_json, "spine_json")),
                "--out-graphml",
                str(graphml_path),
            ]
        )
        payload["graphml"] = str(graphml_path)

    if args.emit_schema:
        schema_path = _require_abs_path(args.out_schema_json, "out_schema_json")
        _run_path(
            [
                str(spec_graph_python),
                str(repo_root / "system_v3" / "tools" / "emit_a2_controller_launch_spine_pydantic_schema.py"),
                "--out-json",
                str(schema_path),
            ]
        )
        payload["schema_json"] = str(schema_path)

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
