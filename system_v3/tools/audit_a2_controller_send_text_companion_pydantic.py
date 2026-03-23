#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from a2_controller_send_text_companion_models import load_a2_controller_send_text_companion


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Audit one A2 controller send-text companion through the local Pydantic stack.")
    parser.add_argument("--companion-json", required=True)
    args = parser.parse_args(argv)

    companion = load_a2_controller_send_text_companion(Path(args.companion_json))
    payload = {
        "schema": "A2_CONTROLLER_SEND_TEXT_COMPANION_PYDANTIC_AUDIT_RESULT_v1",
        "thread_class": companion.thread_class,
        "mode": companion.mode,
        "graph": companion.graph_summary(),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
