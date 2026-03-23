#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from a1_worker_launch_gate_result_models import load_a1_worker_launch_gate_result


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit one A1 worker launch gate result through the local Pydantic stack.")
    parser.add_argument("--gate-result-json", required=True)
    args = parser.parse_args()

    gate_result = load_a1_worker_launch_gate_result(Path(args.gate_result_json))
    payload = {
        "schema": gate_result.schema_name,
        "thread_class": gate_result.thread_class,
        "mode": gate_result.mode,
        **gate_result.graph_summary(),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
