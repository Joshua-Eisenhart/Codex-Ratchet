#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from a2_controller_launch_handoff_models import A2ControllerLaunchHandoff


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Emit a local Pydantic schema for A2 controller launch handoff packets.")
    parser.add_argument("--out-json", required=True)
    args = parser.parse_args(argv)

    out_path = Path(args.out_json)
    if not out_path.is_absolute():
        raise SystemExit("non_absolute_out_json")
    _write_json(out_path, A2ControllerLaunchHandoff.model_json_schema())
    payload = {
        "schema": "A2_CONTROLLER_LAUNCH_HANDOFF_PYDANTIC_SCHEMA_EMIT_RESULT_v1",
        "out_json": str(out_path),
        "status": "CREATED",
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
