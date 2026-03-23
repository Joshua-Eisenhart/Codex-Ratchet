#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SCHEMA = "A2_CONTROLLER_LAUNCH_PACKET_v1"
THREAD_CLASS = "A2_CONTROLLER"
MODE = "CONTROLLER_ONLY"


def _require_text(value: str, key: str) -> str:
    text = value.strip()
    if not text:
        raise SystemExit(f"missing_{key}")
    return text


def _require_abs_existing(value: str, key: str) -> str:
    path = Path(_require_text(value, key))
    if not path.is_absolute():
        raise SystemExit(f"non_absolute_{key}")
    if not path.exists():
        raise SystemExit(f"missing_path_{key}:{path}")
    return str(path)


def _require_nonnegative(value: int, key: str) -> int:
    if value < 0:
        raise SystemExit(f"negative_{key}")
    return value


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Create one machine-readable A2_CONTROLLER_LAUNCH_PACKET_v1."
    )
    parser.add_argument("--model", required=True)
    parser.add_argument("--primary-corpus", required=True)
    parser.add_argument("--state-record", required=True)
    parser.add_argument("--current-primary-lane", required=True)
    parser.add_argument("--current-a1-queue-status", required=True)
    parser.add_argument("--go-on-count", required=True, type=int)
    parser.add_argument("--go-on-budget", required=True, type=int)
    parser.add_argument("--stop-rule", required=True)
    parser.add_argument("--dispatch-rule", required=True)
    parser.add_argument("--initial-bounded-scope", required=True)
    parser.add_argument("--boot-surface", required=True)
    parser.add_argument("--out-json", required=True)
    args = parser.parse_args(argv)

    packet = {
        "schema": SCHEMA,
        "model": _require_text(args.model, "model"),
        "thread_class": THREAD_CLASS,
        "mode": MODE,
        "primary_corpus": _require_abs_existing(args.primary_corpus, "primary_corpus"),
        "state_record": _require_abs_existing(args.state_record, "state_record"),
        "current_primary_lane": _require_text(args.current_primary_lane, "current_primary_lane"),
        "current_a1_queue_status": _require_text(args.current_a1_queue_status, "current_a1_queue_status"),
        "go_on_count": _require_nonnegative(args.go_on_count, "go_on_count"),
        "go_on_budget": _require_nonnegative(args.go_on_budget, "go_on_budget"),
        "stop_rule": _require_text(args.stop_rule, "stop_rule"),
        "dispatch_rule": _require_text(args.dispatch_rule, "dispatch_rule"),
        "initial_bounded_scope": _require_text(args.initial_bounded_scope, "initial_bounded_scope"),
        "boot_surface": _require_abs_existing(args.boot_surface, "boot_surface"),
    }

    if packet["go_on_count"] > packet["go_on_budget"]:
        raise SystemExit("go_on_count_exceeds_budget")

    out_path = Path(_require_text(args.out_json, "out_json"))
    if not out_path.is_absolute():
        raise SystemExit("non_absolute_out_json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(packet, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
