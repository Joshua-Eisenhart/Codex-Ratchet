#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_candidate_registry() -> Path:
    return _repo_root() / "system_v3" / "a2_state" / "A1_QUEUE_CANDIDATE_REGISTRY__CURRENT__2026_03_15__v1.json"


def _default_queue_status_packet() -> Path:
    return _repo_root() / "system_v3" / "a2_state" / "A1_QUEUE_STATUS_PACKET__CURRENT__2026_03_15__v1.json"


def _default_preview_note() -> Path:
    return _repo_root() / "work" / "audit_tmp" / "spec_object_drafts" / "A1_QUEUE_STATUS__CURRENT__ACTIVE_REFRESH_PREVIEW__2026_03_15__v1.md"


def _default_active_current_note() -> Path:
    return _repo_root() / "system_v3" / "a2_state" / "A1_QUEUE_STATUS__CURRENT__2026_03_16__v1.md"


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
        description="Refresh the active current A1 queue packet from the active current candidate registry."
    )
    parser.add_argument("--candidate-registry-json", default=str(_default_candidate_registry()))
    parser.add_argument("--queue-status-packet-json", default=str(_default_queue_status_packet()))
    parser.add_argument("--preview-note", default=str(_default_preview_note()))
    parser.add_argument("--active-current-note", default=str(_default_active_current_note()))
    parser.add_argument("--write-active-current-note", action="store_true")
    parser.add_argument("--family-slice-schema-json")
    parser.add_argument(
        "--family-slice-validation-mode",
        choices=("jsonschema", "local_pydantic", "auto"),
        default="auto",
    )
    parser.add_argument("--spec-graph-python")
    parser.add_argument("--model")
    parser.add_argument("--dispatch-id", default="")
    parser.add_argument("--queue-status", default="READY_FROM_NEW_A2_HANDOFF")
    parser.add_argument("--required-a1-boot")
    parser.add_argument("--a1-reload-artifact", action="append", default=[])
    parser.add_argument("--go-on-count", type=int, default=0)
    parser.add_argument("--go-on-budget", type=int, default=1)
    parser.add_argument("--preparation-mode", choices=("packet", "bundle"), default="packet")
    parser.add_argument("--out-dir")
    args = parser.parse_args(argv)

    repo_root = _repo_root()
    cmd = [
        sys.executable,
        str(repo_root / "system_v3" / "tools" / "prepare_current_a1_queue_status_from_candidates.py"),
        "--candidate-registry-json",
        str(_require_abs_path(args.candidate_registry_json, "candidate_registry_json")),
        "--out-json",
        str(_require_abs_path(args.queue_status_packet_json, "queue_status_packet_json")),
        "--out-note",
        str(_require_abs_path(args.preview_note, "preview_note")),
    ]
    if args.family_slice_schema_json:
        cmd.extend(["--family-slice-schema-json", str(_require_abs_path(args.family_slice_schema_json, "family_slice_schema_json"))])
    cmd.extend(["--family-slice-validation-mode", args.family_slice_validation_mode])
    if args.spec_graph_python:
        cmd.extend(["--spec-graph-python", str(_require_abs_path(args.spec_graph_python, "spec_graph_python"))])
    if args.model:
        cmd.extend(["--model", args.model])
    if args.dispatch_id:
        cmd.extend(["--dispatch-id", args.dispatch_id])
    cmd.extend(
        [
            "--queue-status",
            args.queue_status,
            "--go-on-count",
            str(args.go_on_count),
            "--go-on-budget",
            str(args.go_on_budget),
            "--preparation-mode",
            args.preparation_mode,
        ]
    )
    if args.required_a1_boot:
        cmd.extend(["--required-a1-boot", str(_require_abs_path(args.required_a1_boot, "required_a1_boot"))])
    for artifact in args.a1_reload_artifact:
        cmd.extend(["--a1-reload-artifact", str(_require_abs_path(artifact, "a1_reload_artifact"))])
    if args.out_dir:
        cmd.extend(["--out-dir", str(_require_abs_path(args.out_dir, "out_dir"))])

    result = _run_json(cmd)
    queue_packet_path = _require_abs_path(args.queue_status_packet_json, "queue_status_packet_json")
    queue_packet = _load_json(queue_packet_path)
    payload = {
        "schema": "ACTIVE_A1_QUEUE_REFRESH_RESULT_v1",
        "status": "CREATED",
        "candidate_registry_json": str(_require_abs_path(args.candidate_registry_json, "candidate_registry_json")),
        "queue_status_packet_json": str(queue_packet_path),
        "preview_note": str(_require_abs_path(args.preview_note, "preview_note")),
        "family_slice_validation_requested_mode": str(queue_packet.get("family_slice_validation_requested_mode", "")),
        "family_slice_validation_resolved_mode": str(queue_packet.get("family_slice_validation_resolved_mode", "")),
        "family_slice_validation_source": str(queue_packet.get("family_slice_validation_source", "")),
        "family_slice_validation_requested_provenance": dict(
            queue_packet.get("family_slice_validation_requested_provenance", {})
        ),
        "family_slice_validation_resolved_provenance": dict(
            queue_packet.get("family_slice_validation_resolved_provenance", {})
        ),
        "selection_result": result,
    }
    if args.write_active_current_note:
        active_note_path = _require_abs_path(args.active_current_note, "active_current_note")
        note_result = _run_json(
            [
                sys.executable,
                str(repo_root / "system_v3" / "tools" / "render_a1_queue_status_current_note_from_packet.py"),
                "--packet-json",
                str(_require_abs_path(args.queue_status_packet_json, "queue_status_packet_json")),
                "--out-text",
                str(active_note_path),
            ]
        )
        payload["active_current_note"] = str(active_note_path)
        payload["active_current_note_result"] = note_result
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
