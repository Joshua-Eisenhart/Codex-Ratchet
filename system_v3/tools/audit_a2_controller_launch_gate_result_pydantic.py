#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from a2_controller_launch_gate_result_models import load_a2_controller_launch_gate_result


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Audit one A2 controller launch gate result through the local Pydantic stack.")
    parser.add_argument("--gate-result-json", required=True)
    args = parser.parse_args(argv)

    result = load_a2_controller_launch_gate_result(Path(args.gate_result_json))
    payload = {
        "schema": "A2_CONTROLLER_LAUNCH_GATE_RESULT_PYDANTIC_AUDIT_RESULT_v1",
        "status": result.status,
        "valid": result.valid,
        "graph": result.graph_summary(),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
