#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from a1_worker_launch_handoff_models import load_a1_worker_launch_handoff


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit one A1 worker launch handoff through the local Pydantic stack.")
    parser.add_argument("--handoff-json", required=True)
    args = parser.parse_args()

    handoff = load_a1_worker_launch_handoff(Path(args.handoff_json))
    payload = {
        "schema": handoff.schema_name,
        "thread_class": handoff.thread_class,
        "mode": handoff.mode,
        **handoff.graph_summary(),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
