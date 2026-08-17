#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def check(plan: dict) -> dict:
    missing = [key for key in ("failure_modes", "tripwires", "stop_or_demote") if not plan.get(key)]
    if missing:
        return {"schema": "constraintbox.kill-criteria.v1", "status": "HOLD", "reason": "HOLD_NO_TRIPWIRE", "missing": missing}
    fired = [name for name in plan.get("tripwires") if name in set(plan.get("already_fired") or [])]
    if fired:
        return {"schema": "constraintbox.kill-criteria.v1", "status": "REFUSE", "reason": "REFUSE_DEAD_PLAN", "fired": fired, "promotion_allowed": False}
    return {"schema": "constraintbox.kill-criteria.v1", "status": "ARMED", "promotion_allowed": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    receipt = check(json.loads(args.plan.read_text(encoding="utf-8")))
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["status"] == "ARMED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
