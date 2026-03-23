#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from a1_worker_launch_spine_models import load_a1_worker_launch_spine


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit one A1 worker launch spine through the local Pydantic stack.")
    parser.add_argument("--spine-json", required=True)
    args = parser.parse_args()

    spine = load_a1_worker_launch_spine(Path(args.spine_json))
    payload = {
        "schema": spine.schema_name,
        "thread_class": spine.thread_class,
        "mode": spine.mode,
        **spine.graph_summary(),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
