import os
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from run_a2_controller_launch_from_packet import build_result as build_gate_result
from validate_a2_controller_launch_packet import validate as validate_packet


GOVERNING_SURFACES = [
    os.environ.get("CODEX_RATCHET_ROOT", ".") + "/system_v3/specs/27_MASTER_CONTROLLER_THREAD_PROCESS__v1.md",
    os.environ.get("CODEX_RATCHET_ROOT", ".") + "/system_v3/specs/28_A2_THREAD_BOOT__v1.md",
    os.environ.get("CODEX_RATCHET_ROOT", ".") + "/system_v3/specs/40_PARALLEL_CODEX_THREAD_CONTROL__v1.md",
    os.environ.get("CODEX_RATCHET_ROOT", ".") + "/system_v3/specs/66_PARALLEL_CODEX_RUN_PLAYBOOK__v1.md",
    os.environ.get("CODEX_RATCHET_ROOT", ".") + "/system_v3/specs/71_A2_CONTROLLER_LAUNCH_PACKET__v1.md",
]

ACTIVE_CONTEXT_SURFACES = [
    os.environ.get("CODEX_RATCHET_ROOT", ".") + "/system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md",
    os.environ.get("CODEX_RATCHET_ROOT", ".") + "/system_v3/a2_state/OPEN_UNRESOLVED__v1.md",
    os.environ.get("CODEX_RATCHET_ROOT", ".") + "/work/CURRENT.md",
]


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"missing_input:{path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc


def build_send_text(packet: dict) -> str:
    queue_helper_lines: list[str] = []
    initial_scope = str(packet.get("initial_bounded_scope", ""))
    if "a1? queue answer" in initial_scope:
        queue_helper_lines = [
            "",
            "For the bounded `a1?` queue-answer action, use these helpers:",
            "- /home/ratchet/Desktop/Codex Ratchet/system_v3/tools/refresh_active_current_a1_queue_state.py",
            "- /home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_a1_queue_status_packet.py",
            "- /home/ratchet/Desktop/Codex Ratchet/system_v3/tools/validate_a1_queue_status_packet.py",
            "- prefer family-slice `packet` or `bundle` preparation mode when a valid bounded family slice exists",
            "- current queue refresh defaults to `--family-slice-validation-mode auto`",
            "- `auto` means: use `local_pydantic` when `/home/ratchet/Desktop/Codex Ratchet/.venv_spec_graph/bin/python` exists, else fall back to `jsonschema`",
            "- if you explicitly want the local spec-object stack, use `--family-slice-validation-mode local_pydantic --spec-graph-python /home/ratchet/Desktop/Codex Ratchet/.venv_spec_graph/bin/python` through the current-queue refresh path",
        ]
    lines = [
        "Use Ratchet A2/A1.",
        "",
        "You are a fresh A2 controller thread.",
        "",
        "This is a fresh controller thread with no usable prior thread memory.",
        "Bootstrap entirely from repo-held files.",
        "Do not rely on any earlier conversation state.",
        "",
        f"Use {packet['model']}.",
        "",
        "Purpose:",
        "You are the master controller for the current Codex Ratchet A2 control lane.",
        "Your job is to:",
        "- recover weighted current state from repo-held artifacts",
        "- choose one bounded controller action",
        "- dispatch substantive work to a worker whenever a worker expression already exists",
        "- keep the system bootable from artifacts, not thread memory",
        "",
        "You are not a raw intake worker.",
        "You are not an A2-high lane.",
        "You are not an A2-mid lane.",
        "You are not an A1 worker lane.",
        "You are the controller.",
        "",
        "First read these files in order:",
    ]
    read_paths = GOVERNING_SURFACES + [packet["state_record"]] + ACTIVE_CONTEXT_SURFACES
    for idx, path in enumerate(read_paths, start=1):
        lines.append(f"{idx}. {path}")
    lines.extend(
        [
            "",
            "Then build your controller state only from repo-held artifacts.",
            "",
            "Launch packet:",
            f"MODEL: {packet['model']}",
            f"THREAD_CLASS: {packet['thread_class']}",
            f"MODE: {packet['mode']}",
            f"PRIMARY_CORPUS: {packet['primary_corpus']}",
            f"STATE_RECORD: {packet['state_record']}",
            f"CURRENT_PRIMARY_LANE: {packet['current_primary_lane']}",
            f"CURRENT_A1_QUEUE_STATUS: {packet['current_a1_queue_status']}",
            f"GO_ON_COUNT: {packet['go_on_count']}",
            f"GO_ON_BUDGET: {packet['go_on_budget']}",
            f"STOP_RULE: {packet['stop_rule']}",
            f"DISPATCH_RULE: {packet['dispatch_rule']}",
            f"INITIAL_BOUNDED_SCOPE: {packet['initial_bounded_scope']}",
            "",
            "Controller rules:",
            "- prefer repo-held state over chat memory",
            "- one bounded controller action per response",
            "- do not invent worker status; inspect current artifacts",
            "- if a bounded worker expression already exists for the required substantive work, dispatch instead of absorbing the work",
            "- do not run A1 unless the live queue path is explicitly ready",
            "- preserve contradictions",
            "- do not rewrite active doctrine broadly",
            "- stop after one bounded controller action unless one exact worker dispatch is issued",
            *queue_helper_lines,
            "",
            "At the end of every response, always say:",
            "- current phase",
            "- what was read/updated",
            "- whether to stay on Medium or switch models",
            "- exactly how many more “go on” prompts I should queue",
            "- what the next “go on” will do",
            "",
            "First task:",
            "- refresh weighted controller state from the files above",
            "- summarize:",
            "  - strongest active lane",
            "  - second strongest active lane",
            "  - weakest active lane",
            "  - highest-value bounded controller action",
            "- do not assume prior chat history",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Build operator-ready A2 controller send text from one validated launch packet."
    )
    parser.add_argument("--packet-json", required=True)
    parser.add_argument("--out-text", required=True)
    args = parser.parse_args(argv)

    packet_path = Path(args.packet_json)
    out_path = Path(args.out_text)
    if not packet_path.is_absolute():
        raise SystemExit("non_absolute_packet_json")
    if not out_path.is_absolute():
        raise SystemExit("non_absolute_out_text")

    packet = _load_json(packet_path)
    validation_result = validate_packet(packet)
    gate_result = build_gate_result(packet, validation_result)
    if gate_result.get("status") != "LAUNCH_READY":
        raise SystemExit(f"packet_not_launch_ready:{gate_result.get('status','UNKNOWN')}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_send_text(packet), encoding="utf-8")
    print(
        json.dumps(
            {
                "schema": "A2_CONTROLLER_SEND_TEXT_RESULT_v1",
                "packet_json": str(packet_path),
                "out_text": str(out_path),
                "status": "CREATED",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
