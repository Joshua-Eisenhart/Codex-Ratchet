#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from build_a1_worker_launch_handoff import build_handoff as build_a1_handoff
from build_a1_worker_send_text_from_packet import build_send_text as build_a1_send_text
from run_a1_worker_launch_from_packet import build_result as build_a1_gate_result
from validate_a1_worker_launch_packet import validate as validate_a1_packet

from build_a2_controller_launch_handoff import build_handoff as build_a2_handoff
from build_a2_controller_send_text_from_packet import build_send_text as build_a2_send_text
from run_a2_controller_launch_from_packet import build_result as build_a2_gate_result
from validate_a2_controller_launch_packet import validate as validate_a2_packet
from build_a2_worker_launch_handoff import build_handoff as build_a2_worker_handoff
from build_a2_worker_send_text_from_packet import build_send_text as build_a2_worker_send_text
from run_a2_worker_launch_from_packet import build_result as build_a2_worker_gate_result
from validate_a2_worker_launch_packet import validate as validate_a2_worker_packet


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


def _write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def _bundle_names(packet_path: Path, out_dir: Path) -> tuple[Path, Path, Path]:
    stem = packet_path.stem
    return (
        out_dir / f"{stem}__GATE_RESULT.json",
        out_dir / f"{stem}__SEND_TEXT.md",
        out_dir / f"{stem}__HANDOFF.json",
    )


def _bundle_result_path(packet_path: Path, out_dir: Path) -> Path:
    return out_dir / f"{packet_path.stem}__BUNDLE_RESULT.json"


def _prepare_a2(packet_path: Path, packet: dict, out_dir: Path) -> dict:
    validation = validate_a2_packet(packet)
    gate_result = build_a2_gate_result(packet, validation)
    gate_path, send_text_path, handoff_path = _bundle_names(packet_path, out_dir)
    _write_json(gate_path, gate_result)
    if gate_result.get("status") != "LAUNCH_READY":
        return {
            "schema": "CODEX_LAUNCH_BUNDLE_RESULT_v1",
            "status": "BLOCKED",
            "thread_class": "A2_CONTROLLER",
            "packet_json": str(packet_path),
            "gate_result_json": str(gate_path),
            "reason": gate_result.get("status", "UNKNOWN"),
        }

    send_text = build_a2_send_text(packet)
    _write_text(send_text_path, send_text)
    handoff = build_a2_handoff(packet_path, packet, send_text_path)
    _write_json(handoff_path, handoff)
    return {
        "schema": "CODEX_LAUNCH_BUNDLE_RESULT_v1",
        "status": "READY",
        "thread_class": "A2_CONTROLLER",
        "packet_json": str(packet_path),
        "gate_result_json": str(gate_path),
        "send_text_path": str(send_text_path),
        "handoff_json": str(handoff_path),
    }


def _prepare_a1(packet_path: Path, packet: dict, out_dir: Path) -> dict:
    validation = validate_a1_packet(packet)
    gate_result = build_a1_gate_result(packet, validation)
    gate_path, send_text_path, handoff_path = _bundle_names(packet_path, out_dir)
    _write_json(gate_path, gate_result)
    if gate_result.get("status") != "LAUNCH_READY":
        return {
            "schema": "CODEX_LAUNCH_BUNDLE_RESULT_v1",
            "status": "BLOCKED",
            "thread_class": "A1_WORKER",
            "packet_json": str(packet_path),
            "gate_result_json": str(gate_path),
            "reason": gate_result.get("status", "UNKNOWN"),
        }

    send_text = build_a1_send_text(packet)
    _write_text(send_text_path, send_text)
    handoff = build_a1_handoff(packet_path, packet, send_text_path)
    _write_json(handoff_path, handoff)
    return {
        "schema": "CODEX_LAUNCH_BUNDLE_RESULT_v1",
        "status": "READY",
        "thread_class": "A1_WORKER",
        "packet_json": str(packet_path),
        "gate_result_json": str(gate_path),
        "send_text_path": str(send_text_path),
        "handoff_json": str(handoff_path),
        "family_slice_validation_requested_mode": str(packet.get("family_slice_validation_requested_mode", "")),
        "family_slice_validation_resolved_mode": str(packet.get("family_slice_validation_resolved_mode", "")),
        "family_slice_validation_source": str(packet.get("family_slice_validation_source", "")),
        "family_slice_validation_requested_provenance": dict(
            packet.get("family_slice_validation_requested_provenance", {})
        ),
        "family_slice_validation_resolved_provenance": dict(
            packet.get("family_slice_validation_resolved_provenance", {})
        ),
    }


def _prepare_a2_worker(packet_path: Path, packet: dict, out_dir: Path) -> dict:
    validation = validate_a2_worker_packet(packet)
    gate_result = build_a2_worker_gate_result(packet, validation)
    gate_path, send_text_path, handoff_path = _bundle_names(packet_path, out_dir)
    _write_json(gate_path, gate_result)
    if gate_result.get("status") != "LAUNCH_READY":
        return {
            "schema": "CODEX_LAUNCH_BUNDLE_RESULT_v1",
            "status": "BLOCKED",
            "thread_class": "A2_WORKER",
            "packet_json": str(packet_path),
            "gate_result_json": str(gate_path),
            "reason": gate_result.get("status", "UNKNOWN"),
        }

    send_text = build_a2_worker_send_text(packet)
    _write_text(send_text_path, send_text)
    handoff = build_a2_worker_handoff(packet_path, packet, send_text_path)
    _write_json(handoff_path, handoff)
    return {
        "schema": "CODEX_LAUNCH_BUNDLE_RESULT_v1",
        "status": "READY",
        "thread_class": "A2_WORKER",
        "packet_json": str(packet_path),
        "gate_result_json": str(gate_path),
        "send_text_path": str(send_text_path),
        "handoff_json": str(handoff_path),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Prepare one Codex launch bundle from a machine-readable A2 controller or A1 worker launch packet."
    )
    parser.add_argument("--packet-json", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args(argv)

    packet_path = Path(args.packet_json)
    out_dir = Path(args.out_dir)
    if not packet_path.is_absolute():
        raise SystemExit("non_absolute_packet_json")
    if not out_dir.is_absolute():
        raise SystemExit("non_absolute_out_dir")

    packet = _load_json(packet_path)
    schema = packet.get("schema")
    if schema == "A2_CONTROLLER_LAUNCH_PACKET_v1":
        result = _prepare_a2(packet_path, packet, out_dir)
    elif schema == "A2_WORKER_LAUNCH_PACKET_v1":
        result = _prepare_a2_worker(packet_path, packet, out_dir)
    elif schema == "A1_WORKER_LAUNCH_PACKET_v1":
        result = _prepare_a1(packet_path, packet, out_dir)
    else:
        raise SystemExit(f"unsupported_packet_schema:{schema}")

    result_path = _bundle_result_path(packet_path, out_dir)
    _write_json(result_path, result)

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "READY" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
