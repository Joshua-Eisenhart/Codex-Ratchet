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
        description="Prepare one machine-readable A1 queue-status packet plus one current-note render from explicit NO_WORK or one bounded family slice."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--no-work-reason")
    mode.add_argument("--family-slice-json")
    parser.add_argument("--family-slice-schema-json")
    parser.add_argument(
        "--family-slice-validation-mode",
        choices=("jsonschema", "local_pydantic", "auto"),
        default="auto",
    )
    parser.add_argument("--spec-graph-python")
    parser.add_argument("--model")
    parser.add_argument("--queue-status", default="READY_FROM_NEW_A2_HANDOFF")
    parser.add_argument("--dispatch-id", default="")
    parser.add_argument("--required-a1-boot")
    parser.add_argument("--a1-reload-artifact", action="append", default=[])
    parser.add_argument("--go-on-count", type=int, default=0)
    parser.add_argument("--go-on-budget", type=int, default=1)
    parser.add_argument("--preparation-mode", choices=("packet", "bundle"), default="packet")
    parser.add_argument("--out-dir")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-note", required=True)
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[2]
    out_json = _require_abs_path(args.out_json, "out_json")
    out_note = _require_abs_path(args.out_note, "out_note")

    build_cmd = [
        sys.executable,
        str(repo_root / "system_v3" / "tools" / "build_a1_queue_status_packet.py"),
        "--out-json",
        str(out_json),
    ]
    if args.no_work_reason is not None:
        build_cmd.extend(["--no-work-reason", args.no_work_reason])
    else:
        build_cmd.extend(["--family-slice-json", str(_require_abs_path(args.family_slice_json, "family_slice_json"))])
        if args.family_slice_schema_json:
            build_cmd.extend(
                ["--family-slice-schema-json", str(_require_abs_path(args.family_slice_schema_json, "family_slice_schema_json"))]
            )
        build_cmd.extend(["--family-slice-validation-mode", args.family_slice_validation_mode])
        if args.spec_graph_python:
            build_cmd.extend(["--spec-graph-python", str(_require_abs_path(args.spec_graph_python, "spec_graph_python"))])
        if not args.model:
            raise SystemExit("missing_model")
        if not args.out_dir:
            raise SystemExit("missing_out_dir")
        build_cmd.extend(
            [
                "--model",
                args.model,
                "--dispatch-id",
                args.dispatch_id,
                "--queue-status",
                args.queue_status,
                "--go-on-count",
                str(args.go_on_count),
                "--go-on-budget",
                str(args.go_on_budget),
                "--preparation-mode",
                args.preparation_mode,
                "--out-dir",
                str(_require_abs_path(args.out_dir, "out_dir")),
            ]
        )
        if args.required_a1_boot:
            build_cmd.extend(["--required-a1-boot", str(_require_abs_path(args.required_a1_boot, "required_a1_boot"))])
        for artifact in args.a1_reload_artifact:
            build_cmd.extend(["--a1-reload-artifact", str(_require_abs_path(artifact, "a1_reload_artifact"))])

    _run_json(build_cmd)
    queue_packet = _load_json(out_json)

    render_result = _run_json(
        [
            sys.executable,
            str(repo_root / "system_v3" / "tools" / "render_a1_queue_status_current_note_from_packet.py"),
            "--packet-json",
            str(out_json),
            "--out-text",
            str(out_note),
        ]
    )
    result = {
        "schema": "A1_QUEUE_STATUS_SURFACES_RESULT_v1",
        "status": "CREATED",
        "queue_status_packet_json": str(out_json),
        "current_note_text": str(out_note),
        "family_slice_validation_requested_mode": str(queue_packet.get("family_slice_validation_requested_mode", "")),
        "family_slice_validation_resolved_mode": str(queue_packet.get("family_slice_validation_resolved_mode", "")),
        "family_slice_validation_source": str(queue_packet.get("family_slice_validation_source", "")),
        "family_slice_validation_requested_provenance": dict(
            queue_packet.get("family_slice_validation_requested_provenance", {})
        ),
        "family_slice_validation_resolved_provenance": dict(
            queue_packet.get("family_slice_validation_resolved_provenance", {})
        ),
        "note_result": render_result,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
