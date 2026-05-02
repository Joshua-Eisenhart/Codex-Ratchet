#!/usr/bin/env python3
"""Backfill run-boundary metadata onto current micro queue packets and receipts.

This is a metadata repair tool, not a simulator.  It only writes the four
scope-boundary fields required by strict run-boundary admission onto existing
MICRO / INTEGRATION_MICRO queue packets and already-canonical result JSON.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from receipt_schema import load_json, relpath, repo_root, result_dir, summary_all_pass
from reconcile_state import PACKET_START_RE, parse_queue

BOUNDARY_FIELDS = (
    "claim_ceiling",
    "next_lego_target",
    "promotion_condition",
    "blocked_until",
)
SCOPE_FIELDS = (
    "demotion_condition",
    "out_of_scope",
)
PROVENANCE_FIELD = "run_boundary_metadata_source"
PROVENANCE_NOTE_FIELD = "run_boundary_metadata_note"

MICRO_PROMOTION_CONDITION = (
    "requires a later admitted lego row that names this exact function receipt "
    "and passes strict runner admission; this MICRO row does not promote the lego"
)
INTEGRATION_PROMOTION_CONDITION = (
    "requires a later admitted integration or lego row that names the exact "
    "parent receipts and passes strict runner admission; this INTEGRATION_MICRO "
    "row does not promote the lego"
)

MICRO_BLOCKED_UNTIL = (
    "blocked until a downstream queue row declares the exact lego target, parent "
    "receipts, and active stage gate for promotion"
)
INTEGRATION_BLOCKED_UNTIL = (
    "blocked until a downstream queue row declares the exact integration target, "
    "parent receipts, and active stage gate for promotion"
)


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--queue",
        action="append",
        default=[
            str(root / "system_v5" / "ops" / "queue_tier_a.txt"),
            str(root / "system_v5" / "ops" / "queue_tier_a_second_wave.txt"),
        ],
        help="Queue file to repair. Repeatable.",
    )
    parser.add_argument(
        "--since",
        default="2026-05-01",
        help="Only update DONE result receipts with timestamps lexically >= this value.",
    )
    parser.add_argument("--apply", action="store_true", help="Write changes.")
    return parser.parse_args()


def _boundary_values(packet_type: str, payload: dict[str, Any]) -> dict[str, str]:
    lego_target = str(payload.get("lego_target") or "").strip()
    if not lego_target:
        lego_target = "no queue-packet lego target declared; no promotion is admitted"
    if packet_type == "INTEGRATION_MICRO":
        return {
            "claim_ceiling": "tool_integration_micro_only",
            "next_lego_target": lego_target,
            "promotion_condition": INTEGRATION_PROMOTION_CONDITION,
            "blocked_until": INTEGRATION_BLOCKED_UNTIL,
        }
    return {
        "claim_ceiling": "tool_function_micro_only",
        "next_lego_target": lego_target,
        "promotion_condition": MICRO_PROMOTION_CONDITION,
        "blocked_until": MICRO_BLOCKED_UNTIL,
    }


def _with_boundary_fields(
    packet_type: str,
    payload: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, str]]:
    values = _boundary_values(packet_type, payload)
    updated: dict[str, Any] = {}
    inserted = False
    for key, value in payload.items():
        updated[key] = value
        if key == "lego_target":
            for field in BOUNDARY_FIELDS:
                if field not in payload:
                    updated[field] = values[field]
                    inserted = True
    if not inserted:
        for field in BOUNDARY_FIELDS:
            if field not in updated:
                updated[field] = values[field]
    return updated, values


def _format_packet(packet_type: str, payload: dict[str, Any]) -> list[str]:
    lines = json.dumps(payload, indent=2).splitlines()
    return [f"# {packet_type}: {lines[0]}"] + [f"# {line}" for line in lines[1:]]


def patch_queue_packet_text(text: str) -> tuple[str, list[dict[str, Any]]]:
    lines = text.splitlines()
    output: list[str] = []
    updates: list[dict[str, Any]] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        match = PACKET_START_RE.match(line)
        if not match:
            output.append(line)
            index += 1
            continue

        packet_type = match.group(1)
        raw_packet_lines = [line]
        json_lines = [match.group(2)]
        index += 1
        while index < len(lines) and not json_lines[-1].strip().endswith("}"):
            raw_packet_lines.append(lines[index])
            content = lines[index][1:].lstrip() if lines[index].startswith("#") else lines[index]
            json_lines.append(content)
            index += 1

        if packet_type not in {"MICRO", "INTEGRATION_MICRO"}:
            output.extend(raw_packet_lines)
            continue
        try:
            payload = json.loads("\n".join(json_lines))
        except json.JSONDecodeError:
            output.extend(raw_packet_lines)
            continue
        if not isinstance(payload, dict):
            output.extend(raw_packet_lines)
            continue

        updated, values = _with_boundary_fields(packet_type, payload)
        if updated == payload:
            output.extend(raw_packet_lines)
            continue
        output.extend(_format_packet(packet_type, updated))
        updates.append({
            "packet_type": packet_type,
            "tool_target": payload.get("tool_target"),
            "added": {field: values[field] for field in BOUNDARY_FIELDS if field not in payload},
        })
    return "\n".join(output) + ("\n" if text.endswith("\n") else ""), updates


def _packet_metadata_by_result(root: Path, queues: list[Path]) -> dict[str, dict[str, Any]]:
    mapping: dict[str, dict[str, Any]] = {}
    for queue in queues:
        for row in parse_queue(queue, root):
            packet = row.get("packet")
            if not packet:
                continue
            payload = packet.get("payload")
            packet_type = packet.get("type")
            result_name = row.get("result_basename")
            if not isinstance(payload, dict) or not isinstance(packet_type, str) or not result_name:
                continue
            metadata: dict[str, Any] = _boundary_values(packet_type, payload)
            for field in SCOPE_FIELDS:
                value = payload.get(field)
                if value:
                    metadata[field] = value
            mapping[str(result_name)] = metadata
    return mapping


def _default_result_boundary(result_name: str) -> dict[str, str]:
    packet_type = "INTEGRATION_MICRO" if result_name.startswith("sim_integration_") else "MICRO"
    return _boundary_values(packet_type, {})


def patch_results(
    *,
    root: Path,
    queues: list[Path],
    since: str,
    apply: bool,
) -> list[dict[str, Any]]:
    packet_metadata = _packet_metadata_by_result(root, queues)
    selected: set[str] = set()
    for queue in queues:
        for row in parse_queue(queue, root):
            if row.get("status") != "DONE":
                continue
            timestamp = str(row.get("timestamp") or "")
            if since and timestamp < since:
                continue
            result_name = row.get("result_basename")
            if result_name:
                selected.add(str(result_name))

    updates: list[dict[str, Any]] = []
    for result_name in sorted(selected):
        result_path = result_dir(root) / f"{result_name}_results.json"
        if not result_path.exists():
            continue
        payload = load_json(result_path)
        if not isinstance(payload, dict):
            continue
        if payload.get("classification") != "canonical" or summary_all_pass(payload) is not True:
            continue
        values = packet_metadata.get(result_name, _default_result_boundary(result_name))
        added = {
            field: values[field]
            for field in BOUNDARY_FIELDS
            if not isinstance(payload.get(field), str) or not payload.get(field).strip()
        }
        for field in SCOPE_FIELDS:
            if field not in values:
                continue
            value = payload.get(field)
            missing = (
                not isinstance(value, list) or not value
                if field == "out_of_scope"
                else not isinstance(value, str) or not value.strip()
            )
            if missing:
                added[field] = values[field]
        if not added:
            continue
        payload.update(added)
        payload[PROVENANCE_FIELD] = (
            "backfilled_from_queue_packet_metadata"
            if result_name in packet_metadata
            else "backfilled_from_default_micro_boundary_metadata"
        )
        payload[PROVENANCE_NOTE_FIELD] = (
            "This metadata repair records the receipt claim boundary for strict "
            "run-boundary admission. It does not change the executable verdict, "
            "test observations, all_pass status, or classification, and it is not "
            "a sim rerun."
        )
        updates.append({
            "result_json": relpath(result_path, root),
            "result_name": result_name,
            "added": added,
            "source": "queue_packet" if result_name in packet_metadata else "default_micro_boundary",
        })
        if apply:
            result_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return updates


def main() -> int:
    args = parse_args()
    root = repo_root()
    queues = [Path(queue) for queue in args.queue]

    queue_updates: list[dict[str, Any]] = []
    for queue in queues:
        text = queue.read_text(encoding="utf-8")
        updated, updates = patch_queue_packet_text(text)
        for update in updates:
            update["queue"] = relpath(queue, root)
        queue_updates.extend(updates)
        if args.apply and updated != text:
            queue.write_text(updated, encoding="utf-8")

    result_updates = patch_results(
        root=root,
        queues=queues,
        since=args.since,
        apply=args.apply,
    )
    print(json.dumps({
        "all_pass": True,
        "applied": bool(args.apply),
        "queue_packet_update_count": len(queue_updates),
        "queue_packet_updates": queue_updates,
        "result_update_count": len(result_updates),
        "result_updates": result_updates,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
