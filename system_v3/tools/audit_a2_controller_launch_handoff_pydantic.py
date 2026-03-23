#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from a2_controller_launch_handoff_models import load_a2_controller_launch_handoff


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Audit one A2 controller launch handoff through the local Pydantic stack.")
    parser.add_argument("--handoff-json", required=True)
    args = parser.parse_args(argv)

    handoff = load_a2_controller_launch_handoff(Path(args.handoff_json))
    payload = {
        "schema": "A2_CONTROLLER_LAUNCH_HANDOFF_PYDANTIC_AUDIT_RESULT_v1",
        "thread_class": handoff.thread_class,
        "role_type": handoff.role_type,
        "graph": handoff.graph_summary(),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
