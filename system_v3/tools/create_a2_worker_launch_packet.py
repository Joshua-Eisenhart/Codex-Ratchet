#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SCHEMA = "A2_WORKER_LAUNCH_PACKET_v1"
THREAD_CLASS = "A2_WORKER"
MODE = "A2_ONLY"
ALLOWED_ROLE_TYPES = {
    "A2_BRAIN_REFRESH",
    "A2_HIGH_REFINERY_PASS",
    "A2_HIGH_FAMILY_ROUTING_PASS",
    "A2_QUEUE_INTEGRITY_AUDIT",
    "A2_RUN_FOLDER_CLEANUP_PREP",
    "A2_BOOT/PROCEDURE_BUILD",
    "A2_EXTERNAL_RETURN_AUDIT_CAPTURE",
    "A2_DELTA_CONSOLIDATION",
}


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
        description="Create one machine-readable A2_WORKER_LAUNCH_PACKET_v1."
    )
    parser.add_argument("--model", required=True)
    parser.add_argument("--dispatch-id", required=True)
    parser.add_argument("--role-label", required=True)
    parser.add_argument("--role-type", required=True, choices=sorted(ALLOWED_ROLE_TYPES))
    parser.add_argument("--role-scope", required=True)
    parser.add_argument("--required-a2-boot", required=True)
    parser.add_argument("--source-artifact", action="append", required=True)
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
        "dispatch_id": _require_text(args.dispatch_id, "dispatch_id"),
        "role_label": _require_text(args.role_label, "role_label"),
        "role_type": _require_text(args.role_type, "role_type"),
        "role_scope": _require_text(args.role_scope, "role_scope"),
        "required_a2_boot": _require_abs_existing(args.required_a2_boot, "required_a2_boot"),
        "source_artifacts": [
            _require_abs_existing(path, f"source_artifact_{index}")
            for index, path in enumerate(args.source_artifact, start=1)
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
