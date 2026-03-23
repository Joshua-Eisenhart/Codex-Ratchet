#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from auto_go_on_runner import evaluate
from extract_auto_go_on_thread_result import _build_packet


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Run one full auto-go-on cycle from raw returned thread text to runner output."
    )
    parser.add_argument("--reply-text", required=True, help="Path to raw returned thread text.")
    parser.add_argument("--target-thread-id", required=True, help="Exact target thread id.")
    parser.add_argument(
        "--thread-class",
        required=True,
        choices=["A2_WORKER", "A1_WORKER", "A2_CONTROLLER"],
        help="Thread class for the returned thread.",
    )
    parser.add_argument("--boot-surface", required=True, help="Exact boot surface path.")
    parser.add_argument("--source-decision-record", required=True, help="Exact decision/summary record path.")
    parser.add_argument(
        "--expected-return-shape",
        required=True,
        help="Expected minimum return shape after one more pass.",
    )
    parser.add_argument("--fallback-role", default="", help="Fallback role if ROLE_AND_SCOPE is missing.")
    parser.add_argument("--fallback-scope", default="", help="Fallback scope if ROLE_AND_SCOPE is missing.")
    parser.add_argument("--continuation-count", type=int, default=0, help="Continuation count since last manual review.")
    parser.add_argument(
        "--out-dir",
        required=True,
        help="Directory where normalized result JSON and runner output JSON should be written.",
    )
    args = parser.parse_args(argv)

    reply_path = Path(args.reply_text)
    if not reply_path.exists():
        raise SystemExit(f"missing_reply_text:{reply_path}")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    packet = _build_packet(
        reply_path.read_text(encoding="utf-8"),
        args.target_thread_id,
        args.thread_class,
        args.boot_surface,
        args.source_decision_record,
        args.expected_return_shape,
        args.fallback_role,
        args.fallback_scope,
        args.continuation_count,
    )

    normalized_path = out_dir / "auto_go_on_thread_result.json"
    normalized_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    runner_output = evaluate(packet)
    runner_output_path = out_dir / "auto_go_on_runner_output.json"
    runner_output_path.write_text(json.dumps(runner_output, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "schema": "AUTO_GO_ON_CYCLE_RESULT_v1",
                "reply_text": str(reply_path),
                "normalized_result_json": str(normalized_path),
                "runner_output_json": str(runner_output_path),
                "runner_output": runner_output.get("runner_output", ""),
                "decision": runner_output.get("decision", ""),
                "reason": runner_output.get("reason", ""),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
