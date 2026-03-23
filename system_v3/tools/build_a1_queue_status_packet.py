#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from validate_a1_queue_status_packet import validate as validate_queue_packet


SCHEMA = "A1_QUEUE_STATUS_PACKET_v1"
READY_QUEUE_STATUSES = {
    "READY_FROM_NEW_A2_HANDOFF",
    "READY_FROM_EXISTING_FUEL",
    "READY_FROM_A2_PREBUILT_BATCH",
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_family_slice_schema() -> Path:
    return _repo_root() / "work" / "audit_tmp" / "spec_object_drafts" / "A2_TO_A1_FAMILY_SLICE_v1.schema.json"


def _require_abs_path(path_str: str, key: str) -> Path:
    path = Path(path_str)
    if not path.is_absolute():
        raise SystemExit(f"non_absolute_{key}")
    return path


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"missing_input:{path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _run_json_command(cmd: list[str]) -> dict:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise SystemExit((proc.stderr or proc.stdout or "").strip() or f"command_failed:{cmd[0]}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json_stdout:{cmd[0]}:{exc.lineno}:{exc.colno}") from exc


def _default_packet_path(out_dir: Path, dispatch_id: str) -> Path:
    return out_dir / f"A1_WORKER_LAUNCH_PACKET__{dispatch_id}.json"


def _build_no_work_packet(reason: str) -> dict:
    return {
        "schema": SCHEMA,
        "queue_status": "NO_WORK",
        "reason": reason.strip(),
    }


def _build_ready_packet(
    *,
    family_slice_json: Path,
    family_slice_schema_json: Path,
    model: str,
    queue_status: str,
    dispatch_id: str,
    required_a1_boot: str | None,
    a1_reload_artifacts: list[str],
    go_on_count: int,
    go_on_budget: int,
    preparation_mode: str,
    out_dir: Path,
    family_slice_validation_mode: str,
    spec_graph_python: Path | None,
) -> dict:
    repo_root = _repo_root()
    packet_json = _default_packet_path(out_dir, dispatch_id)
    bundle_result_json = ""
    launch_spine_json = ""
    send_text_companion_json = ""

    if preparation_mode == "packet":
        cmd = [
            sys.executable,
            str(repo_root / "system_v3" / "tools" / "build_a1_worker_launch_packet_from_family_slice.py"),
            "--family-slice-json",
            str(family_slice_json),
            "--family-slice-schema-json",
            str(family_slice_schema_json),
            "--model",
            model,
            "--dispatch-id",
            dispatch_id,
            "--queue-status",
            queue_status,
            "--family-slice-validation-mode",
            family_slice_validation_mode,
            "--go-on-count",
            str(go_on_count),
            "--go-on-budget",
            str(go_on_budget),
            "--out-json",
            str(packet_json),
        ]
        if spec_graph_python is not None:
            cmd.extend(["--spec-graph-python", str(spec_graph_python)])
        if required_a1_boot:
            cmd.extend(["--required-a1-boot", required_a1_boot])
        for artifact in a1_reload_artifacts:
            cmd.extend(["--a1-reload-artifact", artifact])
        _run_json_command(cmd)
        ready_surface_kind = "A1_WORKER_LAUNCH_PACKET"
    elif preparation_mode == "bundle":
        cmd = [
            sys.executable,
            str(repo_root / "system_v3" / "tools" / "prepare_a1_launch_bundle_from_family_slice.py"),
            "--family-slice-json",
            str(family_slice_json),
            "--family-slice-schema-json",
            str(family_slice_schema_json),
            "--model",
            model,
            "--dispatch-id",
            dispatch_id,
            "--queue-status",
            queue_status,
            "--family-slice-validation-mode",
            family_slice_validation_mode,
            "--go-on-count",
            str(go_on_count),
            "--go-on-budget",
            str(go_on_budget),
            "--out-dir",
            str(out_dir),
        ]
        if spec_graph_python is not None:
            cmd.extend(["--spec-graph-python", str(spec_graph_python)])
        if required_a1_boot:
            cmd.extend(["--required-a1-boot", required_a1_boot])
        for artifact in a1_reload_artifacts:
            cmd.extend(["--a1-reload-artifact", artifact])
        result = _run_json_command(cmd)
        packet_json = Path(result["packet_json"])
        bundle_result_json = str(result["bundle_result_json"])
        launch_spine_json = str(result.get("launch_spine_json", ""))
        send_text_companion_json = str(result.get("send_text_companion_json", ""))
        ready_surface_kind = "A1_LAUNCH_BUNDLE"
    else:
        raise SystemExit(f"unsupported_preparation_mode:{preparation_mode}")

    worker_packet = _load_json(packet_json)
    return {
        "schema": SCHEMA,
        "queue_status": queue_status,
        "reason": f"bounded A2 family slice compiled into one ready A1 {preparation_mode} surface",
        "dispatch_id": worker_packet["dispatch_id"],
        "target_a1_role": worker_packet["target_a1_role"],
        "required_a1_boot": worker_packet["required_a1_boot"],
        "a1_reload_artifacts": list(worker_packet.get("a1_reload_artifacts", [])),
        "source_a2_artifacts": list(worker_packet["source_a2_artifacts"]),
        "bounded_scope": worker_packet["bounded_scope"],
        "prompt_to_send": worker_packet["prompt_to_send"],
        "stop_rule": worker_packet["stop_rule"],
        "go_on_count": worker_packet["go_on_count"],
        "go_on_budget": worker_packet["go_on_budget"],
        "family_slice_json": str(family_slice_json),
        "ready_surface_kind": ready_surface_kind,
        "ready_packet_json": str(packet_json),
        "ready_bundle_result_json": bundle_result_json,
        "ready_send_text_companion_json": send_text_companion_json,
        "ready_launch_spine_json": launch_spine_json,
        "family_slice_validation_requested_mode": str(worker_packet.get("family_slice_validation_requested_mode", "")),
        "family_slice_validation_resolved_mode": str(worker_packet.get("family_slice_validation_resolved_mode", "")),
        "family_slice_validation_source": str(worker_packet.get("family_slice_validation_source", "")),
        "family_slice_validation_requested_provenance": dict(
            worker_packet.get("family_slice_validation_requested_provenance", {})
        ),
        "family_slice_validation_resolved_provenance": dict(
            worker_packet.get("family_slice_validation_resolved_provenance", {})
        ),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Build one bounded A1_QUEUE_STATUS_PACKET_v1 from explicit NO_WORK or one bounded family slice."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--no-work-reason")
    mode.add_argument("--family-slice-json")
    parser.add_argument("--family-slice-schema-json", default=str(_default_family_slice_schema()))
    parser.add_argument("--model")
    parser.add_argument("--queue-status", default="READY_FROM_NEW_A2_HANDOFF")
    parser.add_argument(
        "--family-slice-validation-mode",
        choices=("jsonschema", "local_pydantic", "auto"),
        default="auto",
    )
    parser.add_argument("--spec-graph-python")
    parser.add_argument("--dispatch-id", default="")
    parser.add_argument("--required-a1-boot")
    parser.add_argument("--a1-reload-artifact", action="append", default=[])
    parser.add_argument("--go-on-count", type=int, default=0)
    parser.add_argument("--go-on-budget", type=int, default=1)
    parser.add_argument("--preparation-mode", choices=("packet", "bundle"), default="packet")
    parser.add_argument("--out-dir")
    parser.add_argument("--out-json", required=True)
    args = parser.parse_args(argv)

    out_json = _require_abs_path(args.out_json, "out_json")

    if args.no_work_reason is not None:
        packet = _build_no_work_packet(args.no_work_reason)
    else:
        if args.queue_status not in READY_QUEUE_STATUSES:
            raise SystemExit("invalid_ready_queue_status")
        if not args.model:
            raise SystemExit("missing_model")
        if not args.dispatch_id.strip():
            raise SystemExit("missing_dispatch_id")
        if not args.out_dir:
            raise SystemExit("missing_out_dir")

        family_slice_json = _require_abs_path(args.family_slice_json, "family_slice_json")
        family_slice_schema_json = _require_abs_path(args.family_slice_schema_json, "family_slice_schema_json")
        out_dir = _require_abs_path(args.out_dir, "out_dir")
        out_dir.mkdir(parents=True, exist_ok=True)
        packet = _build_ready_packet(
            family_slice_json=family_slice_json,
            family_slice_schema_json=family_slice_schema_json,
            model=args.model,
            queue_status=args.queue_status,
            dispatch_id=args.dispatch_id.strip(),
            required_a1_boot=args.required_a1_boot,
            a1_reload_artifacts=list(args.a1_reload_artifact),
            go_on_count=args.go_on_count,
            go_on_budget=args.go_on_budget,
            preparation_mode=args.preparation_mode,
            out_dir=out_dir,
            family_slice_validation_mode=args.family_slice_validation_mode,
            spec_graph_python=(
                _require_abs_path(args.spec_graph_python, "spec_graph_python") if args.spec_graph_python else None
            ),
        )

    validation = validate_queue_packet(packet)
    if not validation["valid"]:
        raise SystemExit(f"queue_status_packet_invalid:{validation['errors'][0]}")

    _write_json(out_json, packet)
    print(json.dumps(packet, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
