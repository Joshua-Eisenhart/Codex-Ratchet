#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from a1_worker_send_text_companion_models import load_a1_worker_send_text_companion


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit one A1 worker send-text companion through the local Pydantic stack.")
    parser.add_argument("--companion-json", required=True)
    args = parser.parse_args()

    companion = load_a1_worker_send_text_companion(Path(args.companion_json))
    payload = {
        "schema": companion.schema_name,
        "thread_class": companion.thread_class,
        "mode": companion.mode,
        **companion.graph_summary(),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
