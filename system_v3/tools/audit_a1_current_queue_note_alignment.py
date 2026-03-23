#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from validate_a1_queue_status_packet import validate as validate_queue_packet


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"missing_input:{path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc


def _load_text(path: Path) -> str:
    if not path.exists():
        raise SystemExit(f"missing_input:{path}")
    return path.read_text(encoding="utf-8")


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("`", " ")).strip()


def build_result(packet: dict, note_text: str, packet_path: Path, note_path: Path) -> dict:
    validation = validate_queue_packet(packet)
    errors = list(validation.get("errors", []))
    normalized_note = _normalize(note_text)

    queue_line = _normalize(f"A1_QUEUE_STATUS: {packet['queue_status']}")
    reason_line = _normalize(f"reason: {packet['reason']}")
    if queue_line not in normalized_note:
        errors.append("note_missing_queue_status")
    if reason_line not in normalized_note:
        errors.append("note_missing_reason")

    return {
        "schema": "A1_CURRENT_QUEUE_NOTE_ALIGNMENT_AUDIT_v1",
        "valid": not errors,
        "errors": errors,
        "queue_status": packet.get("queue_status", ""),
        "packet_json": str(packet_path),
        "note_text": str(note_path),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Audit whether the current human-readable A1 queue note matches the current machine-readable queue packet."
    )
    parser.add_argument("--packet-json", required=True)
    parser.add_argument("--note-text", required=True)
    args = parser.parse_args(argv)

    packet_path = Path(args.packet_json)
    note_path = Path(args.note_text)
    if not packet_path.is_absolute():
        raise SystemExit("non_absolute_packet_json")
    if not note_path.is_absolute():
        raise SystemExit("non_absolute_note_text")

    result = build_result(_load_json(packet_path), _load_text(note_path), packet_path, note_path)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
