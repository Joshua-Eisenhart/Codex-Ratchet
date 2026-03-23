#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from create_auto_go_on_cycle_packet import ALLOWED_THREAD_CLASSES
from run_auto_go_on_cycle_from_packet import main as run_from_packet_main


def _require_abs(path_value: str, field: str) -> None:
    if not path_value or not Path(path_value).is_absolute():
        raise SystemExit(f"non_absolute_path:{field}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Run one full auto-go-on cycle directly from raw returned thread text plus metadata."
    )
    parser.add_argument("--reply-text", required=True, help="Absolute path to raw returned thread text.")
    parser.add_argument("--target-thread-id", required=True, help="Exact target thread id.")
    parser.add_argument(
        "--thread-class",
        required=True,
        choices=sorted(ALLOWED_THREAD_CLASSES),
        help="Thread class for the returned thread.",
    )
    parser.add_argument("--boot-surface", required=True, help="Absolute path to the boot surface.")
    parser.add_argument("--source-decision-record", required=True, help="Absolute path to the decision/summary record.")
    parser.add_argument("--expected-return-shape", required=True, help="Expected minimum return shape after one more pass.")
    parser.add_argument("--out-dir", required=True, help="Absolute output directory for the cycle outputs.")
    parser.add_argument("--fallback-role", default="", help="Fallback role if ROLE_AND_SCOPE is missing.")
    parser.add_argument("--fallback-scope", default="", help="Fallback scope if ROLE_AND_SCOPE is missing.")
    parser.add_argument("--continuation-count", type=int, default=0, help="Continuation count since last manual review.")
    args = parser.parse_args(argv)

    for field in ("reply_text", "boot_surface", "source_decision_record", "out_dir"):
        _require_abs(getattr(args, field), field)

    reply_path = Path(args.reply_text)
    if not reply_path.exists():
        raise SystemExit(f"missing_reply_text:{reply_path}")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    packet_path = out_dir / "auto_go_on_cycle_packet.json"

    packet = {
        "schema": "AUTO_GO_ON_CYCLE_PACKET_v1",
        "reply_text": args.reply_text,
        "target_thread_id": args.target_thread_id,
        "thread_class": args.thread_class,
        "boot_surface": args.boot_surface,
        "source_decision_record": args.source_decision_record,
        "expected_return_shape": args.expected_return_shape,
        "fallback_role": args.fallback_role,
        "fallback_scope": args.fallback_scope,
        "continuation_count": args.continuation_count,
        "out_dir": args.out_dir,
    }
    packet_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return run_from_packet_main(["--packet-json", str(packet_path)])


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
