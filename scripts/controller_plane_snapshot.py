#!/usr/bin/env python3
"""Emit a plane-separated controller snapshot from current local surfaces.

Read-only helper:
  - control_plane: queue counts + recent dispatch
  - state_plane: triage counts + integration summary + top examples

This does not enqueue, mutate sims, or rewrite doctrine surfaces.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import adaptive_controller


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry", action="store_true", help="Print snapshot only; do not write log file")
    args = parser.parse_args()

    state = adaptive_controller.triage_cycle(dry=True)
    integration = adaptive_controller.build_integration_summary(state)
    snapshot = adaptive_controller.build_plane_snapshot(state, integration)

    if args.dry:
        print(json.dumps(snapshot, indent=2))
        return 0

    adaptive_controller.LOGS.mkdir(exist_ok=True)
    out_path = adaptive_controller.LOGS / (
        f"controller_plane_snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    out_path.write_text(json.dumps(snapshot, indent=2))
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
