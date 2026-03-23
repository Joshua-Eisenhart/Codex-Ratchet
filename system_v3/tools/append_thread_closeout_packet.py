#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ALLOWED_DECISIONS = {
    "STOP",
    "CONTINUE_ONE_BOUNDED_STEP",
    "CORRECT_LANE_LATER",
}

ALLOWED_DIAGNOSES = {
    "healthy_but_ready_to_stop",
    "healthy_but_needs_one_bounded_final_step",
    "stalled",
    "duplicate",
    "drifted_off_scope",
    "metadata_polish_only",
    "waiting_on_external_input",
}

ALLOWED_OUTPUT_STATUSES = {
    "complete",
    "usable_but_partial",
    "not_actually_reusable",
}

REQUIRED_TOP_LEVEL = [
    "schema",
    "captured_utc",
    "source_thread_label",
    "final_decision",
    "thread_diagnosis",
    "role_and_scope",
    "strongest_outputs",
    "keepers",
    "if_one_more_step",
    "risks",
    "handoff_packet",
    "closed_statement",
]


def _fail(msg: str) -> None:
    raise SystemExit(msg)


def _load_packet(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"missing_packet_file:{path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc


def _validate_packet(packet: dict) -> None:
    for key in REQUIRED_TOP_LEVEL:
        if key not in packet:
            _fail(f"missing_required_field:{key}")

    if packet["schema"] != "THREAD_CLOSEOUT_PACKET_v1":
        _fail("schema_mismatch:expected:THREAD_CLOSEOUT_PACKET_v1")

    if packet["final_decision"] not in ALLOWED_DECISIONS:
        _fail(f"invalid_final_decision:{packet['final_decision']}")

    if packet["thread_diagnosis"] not in ALLOWED_DIAGNOSES:
        _fail(f"invalid_thread_diagnosis:{packet['thread_diagnosis']}")

    role_and_scope = packet["role_and_scope"]
    if not isinstance(role_and_scope, dict):
        _fail("role_and_scope_must_be_object")
    for key in ("role_label", "scope"):
        if not isinstance(role_and_scope.get(key), str) or not role_and_scope[key].strip():
            _fail(f"invalid_role_and_scope_field:{key}")

    outputs = packet["strongest_outputs"]
    if not isinstance(outputs, list):
        _fail("strongest_outputs_must_be_list")
    for idx, item in enumerate(outputs):
        if not isinstance(item, dict):
            _fail(f"strongest_outputs_item_not_object:{idx}")
        for key in ("artifact_path", "why_it_matters", "status"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                _fail(f"invalid_strongest_outputs_field:{idx}:{key}")
        if item["status"] not in ALLOWED_OUTPUT_STATUSES:
            _fail(f"invalid_output_status:{idx}:{item['status']}")

    if not isinstance(packet["keepers"], list):
        _fail("keepers_must_be_list")
    if not isinstance(packet["risks"], list):
        _fail("risks_must_be_list")

    one_more = packet["if_one_more_step"]
    if not isinstance(one_more, dict):
        _fail("if_one_more_step_must_be_object")
    for key in ("next_step", "stop_condition"):
        if key not in one_more or not isinstance(one_more[key], str):
            _fail(f"invalid_if_one_more_step_field:{key}")
    if "touches" not in one_more or not isinstance(one_more["touches"], list):
        _fail("invalid_if_one_more_step_field:touches")

    handoff = packet["handoff_packet"]
    if not isinstance(handoff, dict):
        _fail("handoff_packet_must_be_object")
    if "boot_files" not in handoff or not isinstance(handoff["boot_files"], list):
        _fail("invalid_handoff_packet_field:boot_files")
    if "artifact_paths" not in handoff or not isinstance(handoff["artifact_paths"], list):
        _fail("invalid_handoff_packet_field:artifact_paths")
    if not isinstance(handoff.get("unresolved_question"), str):
        _fail("invalid_handoff_packet_field:unresolved_question")

    if not isinstance(packet["captured_utc"], str) or not packet["captured_utc"].strip():
        _fail("invalid_captured_utc")
    if not isinstance(packet["source_thread_label"], str) or not packet["source_thread_label"].strip():
        _fail("invalid_source_thread_label")
    if not isinstance(packet["closed_statement"], str) or not packet["closed_statement"].strip():
        _fail("invalid_closed_statement")


def _append_packet(sink: Path, packet: dict) -> None:
    sink.parent.mkdir(parents=True, exist_ok=True)
    with sink.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(packet, sort_keys=True))
        f.write("\n")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Append one validated thread closeout packet to the repo-held sink.")
    parser.add_argument("--packet-json", required=True, help="Path to a JSON packet file matching THREAD_CLOSEOUT_PACKET_v1.")
    parser.add_argument(
        "--sink",
        default="system_v3/a2_derived_indices_noncanonical/thread_closeout_packets.000.jsonl",
        help="Append-only JSONL sink path.",
    )
    args = parser.parse_args(argv)

    packet_path = Path(args.packet_json)
    sink_path = Path(args.sink)

    packet = _load_packet(packet_path)
    _validate_packet(packet)
    _append_packet(sink_path, packet)

    print(
        json.dumps(
            {
                "schema": "THREAD_CLOSEOUT_PACKET_APPEND_RESULT_v1",
                "packet_json": str(packet_path),
                "sink": str(sink_path),
                "source_thread_label": packet["source_thread_label"],
                "final_decision": packet["final_decision"],
                "thread_diagnosis": packet["thread_diagnosis"],
                "status": "APPENDED",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
