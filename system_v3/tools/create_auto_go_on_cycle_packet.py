#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ALLOWED_THREAD_CLASSES = {"A2_WORKER", "A1_WORKER", "A2_CONTROLLER"}


def _require_abs(path_value: str, field: str) -> None:
    if not path_value or not Path(path_value).is_absolute():
        raise SystemExit(f"non_absolute_path:{field}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Create one AUTO_GO_ON_CYCLE_PACKET_v1 from raw returned thread text metadata."
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
    parser.add_argument("--out-dir", required=True, help="Absolute output directory for the cycle runner outputs.")
    parser.add_argument("--out-json", required=True, help="Absolute output path for the cycle packet JSON.")
    parser.add_argument("--fallback-role", default="", help="Fallback role if ROLE_AND_SCOPE is missing.")
    parser.add_argument("--fallback-scope", default="", help="Fallback scope if ROLE_AND_SCOPE is missing.")
    parser.add_argument("--continuation-count", type=int, default=0, help="Continuation count since last manual review.")
    args = parser.parse_args(argv)

    for field in ("reply_text", "boot_surface", "source_decision_record", "out_dir", "out_json"):
        _require_abs(getattr(args, field), field)

    reply_path = Path(args.reply_text)
    if not reply_path.exists():
        raise SystemExit(f"missing_reply_text:{reply_path}")

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

    out_path = Path(args.out_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "schema": "AUTO_GO_ON_CYCLE_PACKET_CREATE_RESULT_v1",
                "reply_text": args.reply_text,
                "out_json": str(out_path),
                "thread_class": args.thread_class,
                "target_thread_id": args.target_thread_id,
                "status": "CREATED",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
