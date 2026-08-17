#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def check(payload: dict) -> dict:
    if not payload.get("beneficiaries") or "absent" not in payload or not payload.get("bearers"):
        return {"schema": "constraintbox.externality-map.v1", "status": "HOLD", "reason": "HOLD_MAP_INCOMPLETE"}
    if not payload.get("absent"):
        return {"schema": "constraintbox.externality-map.v1", "status": "HOLD", "reason": "HOLD_NO_ABSENT_PARTY"}
    heavy = {"evidence base", "future users", "maintainers"}
    bearers = {str(item).lower() for item in payload.get("bearers") or []}
    if bearers & heavy and not payload.get("mitigation"):
        return {"schema": "constraintbox.externality-map.v1", "status": "REFUSE", "reason": "REFUSE_OMISSION", "promotion_allowed": False}
    return {"schema": "constraintbox.externality-map.v1", "status": "MAPPED", "promotion_allowed": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--map", type=Path, required=True)
    args = parser.parse_args()
    receipt = check(json.loads(args.map.read_text(encoding="utf-8")))
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["status"] == "MAPPED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
