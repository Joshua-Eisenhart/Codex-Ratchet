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


def _choose_family_slice(candidates: list[Path], selected: Path | None) -> Path | None:
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]
    if selected is None:
        raise SystemExit("ambiguous_family_slice_candidates")
    if selected not in candidates:
        raise SystemExit("selected_family_slice_not_in_candidates")
    return selected


def _load_registry(path: Path) -> tuple[list[Path], Path | None]:
    if not path.exists():
        raise SystemExit(f"missing_input:{path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc
    candidates = [_require_abs_path(item, f"candidate_family_slice_jsons[{index}]") for index, item in enumerate(payload.get("candidate_family_slice_jsons", []), start=1)]
    selected_raw = str(payload.get("selected_family_slice_json", "")).strip()
    selected = _require_abs_path(selected_raw, "selected_family_slice_json") if selected_raw else None
    return candidates, selected


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Prepare one current A1 queue-status packet/note from zero, one, or many bounded family-slice candidates."
    )
    parser.add_argument("--candidate-registry-json")
    parser.add_argument("--family-slice-json", action="append", default=[])
    parser.add_argument("--selected-family-slice-json")
    parser.add_argument("--no-work-reason", default="no bounded A1 family slice is currently prepared")
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
    if args.candidate_registry_json:
        registry_candidates, registry_selected = _load_registry(
            _require_abs_path(args.candidate_registry_json, "candidate_registry_json")
        )
    else:
        registry_candidates, registry_selected = [], None
    direct_candidates = [_require_abs_path(path, f"family_slice_json[{index}]") for index, path in enumerate(args.family_slice_json, start=1)]
    if args.candidate_registry_json and direct_candidates:
        raise SystemExit("mixed_candidate_registry_and_direct_candidates")
    candidate_paths = registry_candidates or direct_candidates
    selected_path = (
        _require_abs_path(args.selected_family_slice_json, "selected_family_slice_json")
        if args.selected_family_slice_json
        else registry_selected
    )
    chosen = _choose_family_slice(candidate_paths, selected_path)

    cmd = [
        sys.executable,
        str(repo_root / "system_v3" / "tools" / "prepare_a1_queue_status_surfaces.py"),
        "--out-json",
        str(_require_abs_path(args.out_json, "out_json")),
        "--out-note",
        str(_require_abs_path(args.out_note, "out_note")),
    ]
    if chosen is None:
        cmd.extend(["--no-work-reason", args.no_work_reason])
    else:
        missing_fields: list[str] = []
        if not args.model:
            missing_fields.append("model")
        if not args.dispatch_id.strip():
            missing_fields.append("dispatch_id")
        if not args.out_dir:
            missing_fields.append("out_dir")
        if missing_fields:
            raise SystemExit(f"missing_ready_queue_inputs:{','.join(missing_fields)}")
        cmd.extend(["--family-slice-json", str(chosen)])
        if args.family_slice_schema_json:
            cmd.extend(
                ["--family-slice-schema-json", str(_require_abs_path(args.family_slice_schema_json, "family_slice_schema_json"))]
            )
        cmd.extend(["--family-slice-validation-mode", args.family_slice_validation_mode])
        if args.spec_graph_python:
            cmd.extend(["--spec-graph-python", str(_require_abs_path(args.spec_graph_python, "spec_graph_python"))])
        cmd.extend(
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
            cmd.extend(["--required-a1-boot", str(_require_abs_path(args.required_a1_boot, "required_a1_boot"))])
        for artifact in args.a1_reload_artifact:
            cmd.extend(["--a1-reload-artifact", str(_require_abs_path(artifact, "a1_reload_artifact"))])

    result = _run_json(cmd)
    queue_packet_path = _require_abs_path(result["queue_status_packet_json"], "queue_status_packet_json")
    queue_packet = _load_json(queue_packet_path)
    payload = {
        "schema": "A1_CURRENT_QUEUE_SELECTION_RESULT_v1",
        "status": "CREATED",
        "candidate_count": len(candidate_paths),
        "selected_family_slice_json": str(chosen) if chosen else "",
        "queue_status_packet_json": result["queue_status_packet_json"],
        "current_note_text": result["current_note_text"],
        "family_slice_validation_requested_mode": str(queue_packet.get("family_slice_validation_requested_mode", "")),
        "family_slice_validation_resolved_mode": str(queue_packet.get("family_slice_validation_resolved_mode", "")),
        "family_slice_validation_source": str(queue_packet.get("family_slice_validation_source", "")),
        "family_slice_validation_requested_provenance": dict(
            queue_packet.get("family_slice_validation_requested_provenance", {})
        ),
        "family_slice_validation_resolved_provenance": dict(
            queue_packet.get("family_slice_validation_resolved_provenance", {})
        ),
        "surfaces_result": result,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
