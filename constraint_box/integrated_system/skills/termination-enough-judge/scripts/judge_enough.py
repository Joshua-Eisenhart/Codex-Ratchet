#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def judge(state: dict) -> dict:
    delta = state.get("delta")
    cap = state.get("round_cap", 8)
    round_n = state.get("round", 0)
    if state.get("handoff"):
        return {"schema": "constraintbox.enough.v1", "status": "STOP", "reason": "HUMAN_HANDOFF", "promotion_allowed": False}
    if state.get("alignment_refuse"):
        return {"schema": "constraintbox.enough.v1", "status": "STOP", "reason": "ALIGNMENT_VETO", "promotion_allowed": False}
    if isinstance(round_n, int) and isinstance(cap, int) and round_n >= cap:
        return {"schema": "constraintbox.enough.v1", "status": "STOP", "reason": "ROUND_CAP", "promotion_allowed": False}
    if delta == 0:
        return {"schema": "constraintbox.enough.v1", "status": "STOP", "reason": "NO_IMPROVE", "promotion_allowed": False}
    return {"schema": "constraintbox.enough.v1", "status": "CONTINUE", "promotion_allowed": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", type=Path, required=True)
    args = parser.parse_args()
    receipt = judge(json.loads(args.state.read_text(encoding="utf-8")))
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["status"] == "CONTINUE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
