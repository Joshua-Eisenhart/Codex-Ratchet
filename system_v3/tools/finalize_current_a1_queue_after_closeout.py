#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from validate_a1_queue_candidate_registry import validate as validate_registry


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_candidate_registry() -> Path:
    return _repo_root() / "system_v3" / "a2_state" / "A1_QUEUE_CANDIDATE_REGISTRY__CURRENT__2026_03_15__v1.json"


def _default_queue_status_packet() -> Path:
    return _repo_root() / "system_v3" / "a2_state" / "A1_QUEUE_STATUS_PACKET__CURRENT__2026_03_15__v1.json"


def _default_queue_status_note() -> Path:
    return _repo_root() / "system_v3" / "a2_state" / "A1_QUEUE_STATUS__CURRENT__2026_03_16__v1.md"


def _default_closeout_sink() -> Path:
    return _repo_root() / "system_v3" / "a2_derived_indices_noncanonical" / "thread_closeout_packets.000.jsonl"


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


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"missing_input:{path}")
    packets: list[dict] = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            packets.append(json.loads(raw))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"invalid_jsonl:{path}:{lineno}:{exc.colno}") from exc
    return packets


def _run_json(cmd: list[str]) -> dict:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise SystemExit((proc.stderr or proc.stdout or "").strip() or f"command_failed:{cmd[0]}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json_stdout:{cmd[0]}:{exc.lineno}:{exc.colno}") from exc


def _find_closeout(packets: list[dict], dispatch_id: str) -> dict:
    matches = [
        packet
        for packet in packets
        if str(packet.get("source_thread_label", "")).strip() in {dispatch_id, f"{dispatch_id}__A1_PROPOSAL"}
    ]
    if not matches:
        raise SystemExit(f"missing_closeout_for_dispatch:{dispatch_id}")
    return matches[-1]


def _finalize_registry(registry: dict, consumed_family_slice: str) -> dict:
    candidates = [str(item).strip() for item in registry.get("candidate_family_slice_jsons", []) if str(item).strip()]
    if consumed_family_slice not in candidates:
        raise SystemExit("consumed_family_slice_not_in_current_candidate_registry")
    selected = str(registry.get("selected_family_slice_json", "")).strip()
    if selected and selected != consumed_family_slice:
        raise SystemExit("selected_family_slice_mismatch_with_current_queue")

    remaining = [item for item in candidates if item != consumed_family_slice]
    updated = {
        "schema": "A1_QUEUE_CANDIDATE_REGISTRY_v1",
        "candidate_family_slice_jsons": remaining,
        "selected_family_slice_json": "",
    }
    validation = validate_registry(updated)
    if not validation["valid"]:
        raise SystemExit(f"candidate_registry_invalid:{validation['errors'][0]}")
    return updated


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Retire the current ready A1 queue dispatch after a STOP closeout without auto-promoting the next candidate."
    )
    parser.add_argument("--candidate-registry-json", default=str(_default_candidate_registry()))
    parser.add_argument("--queue-status-packet-json", default=str(_default_queue_status_packet()))
    parser.add_argument("--queue-status-note", default=str(_default_queue_status_note()))
    parser.add_argument("--closeout-sink", default=str(_default_closeout_sink()))
    parser.add_argument(
        "--no-work-reason-template",
        default=(
            "current ready dispatch {dispatch_id} closed with STOP at {captured_utc}; "
            "no current A1 work remains admitted until a new explicit queue refresh/select pass runs"
        ),
    )
    args = parser.parse_args(argv)

    candidate_registry_path = _require_abs_path(args.candidate_registry_json, "candidate_registry_json")
    queue_status_packet_path = _require_abs_path(args.queue_status_packet_json, "queue_status_packet_json")
    queue_status_note_path = _require_abs_path(args.queue_status_note, "queue_status_note")
    closeout_sink_path = _require_abs_path(args.closeout_sink, "closeout_sink")

    queue_packet = _load_json(queue_status_packet_path)
    queue_status = str(queue_packet.get("queue_status", "")).strip()
    if queue_status == "NO_WORK":
        raise SystemExit("queue_already_no_work")
    dispatch_id = str(queue_packet.get("dispatch_id", "")).strip()
    family_slice_json = str(queue_packet.get("family_slice_json", "")).strip()
    if not dispatch_id:
        raise SystemExit("missing_dispatch_id")
    if not family_slice_json:
        raise SystemExit("missing_family_slice_json")

    closeout = _find_closeout(_load_jsonl(closeout_sink_path), dispatch_id)
    if str(closeout.get("final_decision", "")).strip() != "STOP":
        raise SystemExit("closeout_not_stop")

    updated_registry = _finalize_registry(_load_json(candidate_registry_path), family_slice_json)
    _write_json(candidate_registry_path, updated_registry)

    reason = args.no_work_reason_template.format(
        dispatch_id=dispatch_id,
        captured_utc=str(closeout.get("captured_utc", "")).strip() or "unknown_utc",
    )
    queue_surface_result = _run_json(
        [
            sys.executable,
            str(_repo_root() / "system_v3" / "tools" / "prepare_a1_queue_status_surfaces.py"),
            "--no-work-reason",
            reason,
            "--out-json",
            str(queue_status_packet_path),
            "--out-note",
            str(queue_status_note_path),
        ]
    )

    print(
        json.dumps(
            {
                "schema": "A1_CURRENT_QUEUE_FINALIZE_RESULT_v1",
                "status": "FINALIZED",
                "dispatch_id": dispatch_id,
                "consumed_family_slice_json": family_slice_json,
                "closeout_captured_utc": closeout.get("captured_utc", ""),
                "closeout_thread_label": closeout.get("source_thread_label", ""),
                "remaining_candidate_family_slice_jsons": updated_registry["candidate_family_slice_jsons"],
                "candidate_registry_json": str(candidate_registry_path),
                "queue_status_packet_json": str(queue_status_packet_path),
                "queue_status_note": str(queue_status_note_path),
                "queue_surface_result": queue_surface_result,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
