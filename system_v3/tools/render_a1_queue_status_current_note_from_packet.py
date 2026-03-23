#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from validate_a1_queue_status_packet import validate as validate_queue_packet


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"missing_input:{path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc


def build_note(packet: dict, *, title: str) -> str:
    queue_status = packet["queue_status"]
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [
        f"# {title}",
        "Status: ACTIVE CONTROL NOTE / NONCANON",
        f"Date: {today}",
        "Role: current concrete `a1?` response based on existing bounded fuel",
        "",
        "## Current answer",
        "",
        "```text",
        f"A1_QUEUE_STATUS: {queue_status}",
        f"reason: {packet['reason']}",
        "```",
    ]

    if queue_status.startswith("READY_FROM_"):
        lines.extend(
            [
                "",
                "## Current ready path",
                "",
                f"- dispatch_id: {packet['dispatch_id']}",
                f"- target_a1_role: {packet['target_a1_role']}",
                f"- ready_surface_kind: {packet['ready_surface_kind']}",
                f"- ready_packet_json: {packet['ready_packet_json']}",
                f"- family_slice_json: {packet['family_slice_json']}",
                f"- required_a1_boot: {packet['required_a1_boot']}",
                f"- stop_rule: {packet['stop_rule']}",
            ]
        )
        if packet.get("ready_bundle_result_json"):
            lines.append(f"- ready_bundle_result_json: {packet['ready_bundle_result_json']}")
        if packet.get("ready_send_text_companion_json"):
            lines.append(f"- ready_send_text_companion_json: {packet['ready_send_text_companion_json']}")
        if packet.get("ready_launch_spine_json"):
            lines.append(f"- ready_launch_spine_json: {packet['ready_launch_spine_json']}")
        if packet.get("family_slice_validation_requested_mode"):
            lines.append(
                f"- family_slice_validation_requested_mode: {packet['family_slice_validation_requested_mode']}"
            )
        if packet.get("family_slice_validation_resolved_mode"):
            lines.append(
                f"- family_slice_validation_resolved_mode: {packet['family_slice_validation_resolved_mode']}"
            )
        if packet.get("family_slice_validation_source"):
            lines.append(f"- family_slice_validation_source: {packet['family_slice_validation_source']}")
        if packet.get("family_slice_validation_requested_provenance"):
            lines.append(
                "- family_slice_validation_requested_provenance: "
                + json.dumps(packet["family_slice_validation_requested_provenance"], sort_keys=True)
            )
        if packet.get("family_slice_validation_resolved_provenance"):
            lines.append(
                "- family_slice_validation_resolved_provenance: "
                + json.dumps(packet["family_slice_validation_resolved_provenance"], sort_keys=True)
            )
        reload_artifacts = list(packet.get("a1_reload_artifacts", []))
        if reload_artifacts:
            lines.extend(["", "## Reload artifacts", ""])
            lines.extend(f"- {path}" for path in reload_artifacts)
        source_artifacts = list(packet.get("source_a2_artifacts", []))
        if source_artifacts:
            lines.extend(["", "## Source A2 artifacts", ""])
            lines.extend(f"- {path}" for path in source_artifacts)
    elif queue_status.startswith("BLOCKED_"):
        missing = list(packet.get("missing", []))
        if missing:
            lines.extend(["", "## Missing", ""])
            lines.extend(f"- {item}" for item in missing)

    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Render one repo-held current A1 queue-status note from one validated A1_QUEUE_STATUS_PACKET_v1."
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
    validation = validate_queue_packet(packet)
    if not validation["valid"]:
        raise SystemExit(f"queue_status_packet_invalid:{validation['errors'][0]}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_note(packet, title=out_path.stem), encoding="utf-8")
    print(
        json.dumps(
            {
                "schema": "A1_QUEUE_STATUS_CURRENT_NOTE_RESULT_v1",
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
