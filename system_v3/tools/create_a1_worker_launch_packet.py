#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SCHEMA = "A1_WORKER_LAUNCH_PACKET_v1"
THREAD_CLASS = "A1_WORKER"
MODE = "PROPOSAL_ONLY"
ALLOWED_QUEUE_STATUSES = {
    "READY_FROM_NEW_A2_HANDOFF",
    "READY_FROM_EXISTING_FUEL",
    "READY_FROM_A2_PREBUILT_BATCH",
}
ALLOWED_ROLES = {"A1_ROSETTA", "A1_PROPOSAL", "A1_PACKAGING"}


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
        description="Create one machine-readable A1_WORKER_LAUNCH_PACKET_v1."
    )
    parser.add_argument("--model", required=True)
    parser.add_argument("--queue-status", required=True, choices=sorted(ALLOWED_QUEUE_STATUSES))
    parser.add_argument("--dispatch-id", required=True)
    parser.add_argument("--target-a1-role", required=True, choices=sorted(ALLOWED_ROLES))
    parser.add_argument("--required-a1-boot", required=True)
    parser.add_argument("--source-a2-artifact", action="append", required=True)
    parser.add_argument("--a1-reload-artifact", action="append", default=[])
    parser.add_argument("--bounded-scope", required=True)
    parser.add_argument("--prompt-to-send", required=True)
    parser.add_argument("--stop-rule", required=True)
    parser.add_argument("--go-on-count", type=int, default=0)
    parser.add_argument("--go-on-budget", type=int, default=1)
    parser.add_argument("--out-json", required=True)
    args = parser.parse_args(argv)

    packet = {
        "schema": SCHEMA,
        "model": _require_text(args.model, "model"),
        "thread_class": THREAD_CLASS,
        "mode": MODE,
        "queue_status": _require_text(args.queue_status, "queue_status"),
        "dispatch_id": _require_text(args.dispatch_id, "dispatch_id"),
        "target_a1_role": _require_text(args.target_a1_role, "target_a1_role"),
        "required_a1_boot": _require_abs_existing(args.required_a1_boot, "required_a1_boot"),
        "source_a2_artifacts": [
            _require_abs_existing(path, f"source_a2_artifact_{index}")
            for index, path in enumerate(args.source_a2_artifact, start=1)
        ],
        "a1_reload_artifacts": [
            _require_abs_existing(path, f"a1_reload_artifact_{index}")
            for index, path in enumerate(args.a1_reload_artifact, start=1)
        ],
        "bounded_scope": _require_text(args.bounded_scope, "bounded_scope"),
        "prompt_to_send": _require_text(args.prompt_to_send, "prompt_to_send"),
        "stop_rule": _require_text(args.stop_rule, "stop_rule"),
        "go_on_count": _require_nonnegative(args.go_on_count, "go_on_count"),
        "go_on_budget": _require_nonnegative(args.go_on_budget, "go_on_budget"),
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
