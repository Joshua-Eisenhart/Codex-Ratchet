#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def _require_abs_path(path_str: str, key: str) -> Path:
    path = Path(path_str)
    if not path.is_absolute():
        raise SystemExit(f"non_absolute_{key}")
    return path


def _packet_path(out_dir: Path, dispatch_id: str) -> Path:
    return out_dir / f"A1_WORKER_LAUNCH_PACKET__{dispatch_id}.json"


def _bundle_result_path(out_dir: Path, packet_path: Path) -> Path:
    return out_dir / f"{packet_path.stem}__BUNDLE_RESULT.json"


def _send_text_companion_path(out_dir: Path, packet_path: Path) -> Path:
    return out_dir / f"{packet_path.stem}__SEND_TEXT_COMPANION.json"


def _launch_spine_path(out_dir: Path, packet_path: Path) -> Path:
    return out_dir / f"{packet_path.stem}__SPINE.json"


def _run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise SystemExit((proc.stderr or proc.stdout or "").strip() or f"command_failed:{cmd[0]}")


def _run_json(cmd: list[str]) -> dict:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise SystemExit((proc.stderr or proc.stdout or "").strip() or f"command_failed:{cmd[0]}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json_stdout:{cmd[0]}:{exc.lineno}:{exc.colno}") from exc


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"missing_input:{path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Compile one A1 family slice into one A1 launch packet and ready launch bundle."
    )
    parser.add_argument("--family-slice-json", required=True)
    parser.add_argument("--family-slice-schema-json")
    parser.add_argument("--model", required=True)
    parser.add_argument("--dispatch-id", required=True)
    parser.add_argument("--queue-status", default="READY_FROM_NEW_A2_HANDOFF")
    parser.add_argument(
        "--family-slice-validation-mode",
        choices=("jsonschema", "local_pydantic", "auto"),
        default="auto",
    )
    parser.add_argument("--spec-graph-python")
    parser.add_argument("--required-a1-boot")
    parser.add_argument("--a1-reload-artifact", action="append", default=[])
    parser.add_argument("--go-on-count", type=int, default=0)
    parser.add_argument("--go-on-budget", type=int, default=1)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args(argv)

    out_dir = _require_abs_path(args.out_dir, "out_dir")
    out_dir.mkdir(parents=True, exist_ok=True)
    packet_path = _packet_path(out_dir, args.dispatch_id)

    repo_root = Path(__file__).resolve().parents[2]
    compiler_cmd = [
        sys.executable,
        str(repo_root / "system_v3" / "tools" / "build_a1_worker_launch_packet_from_family_slice.py"),
        "--family-slice-json",
        str(_require_abs_path(args.family_slice_json, "family_slice_json")),
        "--model",
        args.model,
        "--dispatch-id",
        args.dispatch_id,
        "--queue-status",
        args.queue_status,
        "--family-slice-validation-mode",
        args.family_slice_validation_mode,
        "--go-on-count",
        str(args.go_on_count),
        "--go-on-budget",
        str(args.go_on_budget),
        "--out-json",
        str(packet_path),
    ]
    if args.spec_graph_python:
        compiler_cmd.extend(["--spec-graph-python", str(_require_abs_path(args.spec_graph_python, "spec_graph_python"))])
    if args.family_slice_schema_json:
        compiler_cmd.extend(
            [
                "--family-slice-schema-json",
                str(_require_abs_path(args.family_slice_schema_json, "family_slice_schema_json")),
            ]
        )
    if args.required_a1_boot:
        compiler_cmd.extend(
            [
                "--required-a1-boot",
                str(_require_abs_path(args.required_a1_boot, "required_a1_boot")),
            ]
        )
    for artifact in args.a1_reload_artifact:
        compiler_cmd.extend(["--a1-reload-artifact", str(_require_abs_path(artifact, "a1_reload_artifact"))])

    _run(compiler_cmd)
    packet = _load_json(packet_path)

    bundle_cmd = [
        sys.executable,
        str(repo_root / "system_v3" / "tools" / "prepare_codex_launch_bundle.py"),
        "--packet-json",
        str(packet_path),
        "--out-dir",
        str(out_dir),
    ]
    bundle_result = _run_json(bundle_cmd)

    if bundle_result.get("status") != "READY":
        raise SystemExit(f"bundle_not_ready:{bundle_result.get('status', 'UNKNOWN')}")

    send_text_companion_path = _send_text_companion_path(out_dir, packet_path)
    send_text_companion_cmd = [
        sys.executable,
        str(repo_root / "system_v3" / "tools" / "build_a1_worker_send_text_companion.py"),
        "--packet-json",
        str(packet_path),
        "--send-text",
        str(_require_abs_path(bundle_result["send_text_path"], "send_text_path")),
        "--out-json",
        str(send_text_companion_path),
    ]
    _run(send_text_companion_cmd)

    launch_spine_path = _launch_spine_path(out_dir, packet_path)
    launch_spine_cmd = [
        sys.executable,
        str(repo_root / "system_v3" / "tools" / "build_a1_worker_launch_spine.py"),
        "--packet-json",
        str(packet_path),
        "--gate-result-json",
        str(_require_abs_path(bundle_result["gate_result_json"], "gate_result_json")),
        "--send-text-companion-json",
        str(send_text_companion_path),
        "--handoff-json",
        str(_require_abs_path(bundle_result["handoff_json"], "handoff_json")),
        "--out-json",
        str(launch_spine_path),
    ]
    _run(launch_spine_cmd)

    result = {
        "schema": "A1_FAMILY_SLICE_LAUNCH_BUNDLE_RESULT_v1",
        "status": "READY",
        "family_slice_json": str(args.family_slice_json),
        "packet_json": str(packet_path),
        "bundle_result_json": str(_bundle_result_path(out_dir, packet_path)),
        "send_text_companion_json": str(send_text_companion_path),
        "launch_spine_json": str(launch_spine_path),
        "out_dir": str(out_dir),
        "family_slice_validation_requested_mode": str(packet.get("family_slice_validation_requested_mode", "")),
        "family_slice_validation_resolved_mode": str(packet.get("family_slice_validation_resolved_mode", "")),
        "family_slice_validation_source": str(packet.get("family_slice_validation_source", "")),
        "family_slice_validation_requested_provenance": dict(
            packet.get("family_slice_validation_requested_provenance", {})
        ),
        "family_slice_validation_resolved_provenance": dict(
            packet.get("family_slice_validation_resolved_provenance", {})
        ),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
