#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


ALLOWED_THREAD_CLASSES = {"A2_WORKER", "A1_WORKER"}
ALLOWED_MESSAGE = "go on"
ALLOWED_MODES = {"validate_only", "blocked_proof", "real_send_once"}
ALLOWED_THREAD_PLATFORM = "CODEX_DESKTOP"


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"missing_input:{path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc


def _validate_prior_proof_packet(proof: dict, sender: dict, target: dict) -> list[str]:
    problems: list[str] = []
    required = [
        "target_thread_id",
        "thread_class",
        "execution_path",
        "send_status",
        "message_sent",
        "detail",
        "continuation_count",
    ]
    for key in required:
        value = proof.get(key)
        if value is None:
            problems.append(f"missing_prior_proof_{key}")
            continue
        if isinstance(value, str) and not value.strip():
            problems.append(f"missing_prior_proof_{key}")

    if proof.get("execution_path") != "PATH_BROWSER_AUTOMATED":
        problems.append("invalid_prior_proof_execution_path")

    if proof.get("send_status") != "SEND_BLOCKED":
        problems.append("prior_proof_not_validate_blocked")

    if proof.get("detail") != "browser_send_not_attempted_validate_only":
        problems.append("prior_proof_not_validate_only")

    if proof.get("message_sent") != "NONE":
        problems.append("prior_proof_message_not_none")

    if proof.get("target_thread_id") != sender.get("target_thread_id"):
        problems.append("prior_proof_thread_id_mismatch")

    if proof.get("thread_class") != sender.get("thread_class"):
        problems.append("prior_proof_thread_class_mismatch")

    if proof.get("continuation_count") != sender.get("continuation_count"):
        problems.append("prior_proof_continuation_count_mismatch")

    visible_verification_text = target.get("visible_verification_text", "")
    if not isinstance(visible_verification_text, str) or not visible_verification_text.strip():
        problems.append("missing_visible_verification_text")

    composer_hint = target.get("composer_ready_hint")
    if composer_hint != "COMPOSER_READY_OBSERVED":
        problems.append("composer_not_observed_ready")

    return problems


def _validate_sender_packet(packet: dict) -> list[str]:
    problems: list[str] = []
    required = [
        "target_thread_id",
        "thread_class",
        "message_to_send",
        "expected_return_shape",
        "stop_condition",
        "continuation_count",
        "source_decision_record",
        "boot_surface",
        "bounded_scope",
    ]
    for key in required:
        value = packet.get(key)
        if value is None:
            problems.append(f"missing_{key}")
            continue
        if isinstance(value, str) and not value.strip():
            problems.append(f"missing_{key}")

    thread_class = packet.get("thread_class", "")
    if thread_class not in ALLOWED_THREAD_CLASSES:
        problems.append("blocked_thread_class")

    if packet.get("message_to_send") != ALLOWED_MESSAGE:
        problems.append("blocked_message")

    continuation_count = packet.get("continuation_count")
    if not isinstance(continuation_count, int):
        problems.append("invalid_continuation_count")
    elif continuation_count >= 1:
        problems.append("continuation_ceiling_reached")

    return problems


def _validate_target_packet(target: dict, sender: dict) -> list[str]:
    problems: list[str] = []
    required = [
        "target_thread_id",
        "thread_class",
        "thread_platform",
        "workspace_root",
        "thread_title_hint",
        "visible_verification_text",
        "composer_ready_hint",
        "source_capture_record",
        "target_status",
    ]
    for key in required:
        value = target.get(key)
        if value is None:
            problems.append(f"missing_target_{key}")
            continue
        if isinstance(value, str) and not value.strip():
            problems.append(f"missing_target_{key}")

    if target.get("thread_platform") != ALLOWED_THREAD_PLATFORM:
        problems.append("blocked_thread_platform")

    target_class = target.get("thread_class", "")
    if target_class not in ALLOWED_THREAD_CLASSES:
        problems.append("blocked_target_thread_class")

    sender_thread_id = sender.get("target_thread_id")
    target_thread_id = target.get("target_thread_id")
    if sender_thread_id and target_thread_id and sender_thread_id != target_thread_id:
        problems.append("thread_id_mismatch")

    sender_thread_class = sender.get("thread_class")
    if sender_thread_class and target_class and sender_thread_class != target_class:
        problems.append("thread_class_mismatch")

    target_status = target.get("target_status")
    if target_status != "READY":
        problems.append("target_not_ready")

    return problems


def _proof_packet(
    packet: dict,
    status: str,
    detail: str,
    screenshot_path: str = "NONE",
    snapshot_path: str = "NONE",
) -> dict:
    sent = status == "SEND_SUCCESS"
    return {
        "schema": "BROWSER_GO_ON_PROOF_PACKET_v1",
        "target_thread_id": packet.get("target_thread_id", ""),
        "thread_class": packet.get("thread_class", ""),
        "execution_path": "PATH_BROWSER_AUTOMATED",
        "send_status": status,
        "message_sent": ALLOWED_MESSAGE if sent else "NONE",
        "sent_at": datetime.now(timezone.utc).isoformat() if sent else "NONE",
        "continuation_count": packet.get("continuation_count", 0),
        "source_sender_packet": packet.get("source_sender_packet", ""),
        "stop_condition": packet.get("stop_condition", ""),
        "detail": detail,
        "screenshot_path": screenshot_path or "NONE",
        "snapshot_path": snapshot_path or "NONE",
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Validate one sender packet plus one browser target packet and emit one browser go-on proof packet."
    )
    parser.add_argument("--sender-packet-json", required=True, help="Path to AUTO_GO_ON_SENDER_PACKET_v1 JSON.")
    parser.add_argument("--target-packet-json", required=True, help="Path to BROWSER_CODEX_THREAD_TARGET_v1 JSON.")
    parser.add_argument("--out-json", required=True, help="Path to write BROWSER_GO_ON_PROOF_PACKET_v1 JSON.")
    parser.add_argument(
        "--prior-proof-json",
        help="Path to prior BROWSER_GO_ON_PROOF_PACKET_v1 JSON required for real_send_once mode.",
    )
    parser.add_argument(
        "--mode",
        choices=sorted(ALLOWED_MODES),
        default="validate_only",
        help="Current bounded helper mode.",
    )
    parser.add_argument("--screenshot-path", default="NONE", help="Optional screenshot path to include.")
    parser.add_argument("--snapshot-path", default="NONE", help="Optional snapshot path to include.")
    args = parser.parse_args(argv)

    packet_path = Path(args.sender_packet_json)
    target_path = Path(args.target_packet_json)
    out_path = Path(args.out_json)
    packet = _load_json(packet_path)
    target = _load_json(target_path)
    prior_proof = _load_json(Path(args.prior_proof_json)) if args.prior_proof_json else None

    # Normalize source path into the packet for proof emission.
    packet["source_sender_packet"] = str(packet_path)
    packet["source_target_packet"] = str(target_path)

    problems = _validate_sender_packet(packet)
    if not problems:
        problems.extend(_validate_target_packet(target, packet))

    if problems:
        proof = _proof_packet(packet, "SEND_BLOCKED", ",".join(problems))
    elif args.mode == "validate_only":
        proof = _proof_packet(packet, "SEND_BLOCKED", "browser_send_not_attempted_validate_only")
    elif args.mode == "real_send_once":
        if prior_proof is None:
            proof = _proof_packet(packet, "SEND_BLOCKED", "missing_prior_validate_only_proof")
        else:
            real_send_problems = _validate_prior_proof_packet(prior_proof, packet, target)
            if real_send_problems:
                proof = _proof_packet(packet, "SEND_BLOCKED", ",".join(real_send_problems))
            else:
                proof = _proof_packet(packet, "SEND_BLOCKED", "browser_send_not_attempted_real_send_mode_stub")
    else:
        proof = _proof_packet(packet, "SEND_BLOCKED", "browser_send_not_attempted_blocked_proof")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(proof, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
