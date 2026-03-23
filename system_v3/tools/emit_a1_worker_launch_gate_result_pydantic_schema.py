#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from a1_worker_launch_gate_result_models import A1WorkerLaunchGateResult


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit a local Pydantic schema for A1 worker launch gate results.")
    parser.add_argument("--out-json", required=True)
    args = parser.parse_args()

    out_path = Path(args.out_json)
    if not out_path.is_absolute():
        raise SystemExit("non_absolute_out_json")

    schema = A1WorkerLaunchGateResult.model_json_schema()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
