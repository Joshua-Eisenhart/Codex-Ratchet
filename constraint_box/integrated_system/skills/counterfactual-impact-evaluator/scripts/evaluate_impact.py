#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


HELD_OUT = ("seed_admit", "light_decides_control", "valid_v1", "zip_valid")


def evaluate(before: dict, after: dict) -> dict:
    world_worse = []
    for key in HELD_OUT:
        if after.get(key) is False and before.get(key) is not False:
            world_worse.append(key)
        if isinstance(before.get(key), int) and isinstance(after.get(key), int) and after[key] < before[key]:
            world_worse.append(key)
    proxy_up = after.get("score", 0) > before.get("score", 0)
    if proxy_up and world_worse:
        return {"schema": "constraintbox.counterfactual-impact.v1", "status": "REFUSE", "reason": "REFUSE_THEATER", "world_worse": world_worse, "promotion_allowed": False}
    return {"schema": "constraintbox.counterfactual-impact.v1", "status": "OBJECT_NOT_WORSE", "world_worse": world_worse, "promotion_allowed": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    args = parser.parse_args()
    receipt = evaluate(json.loads(args.before.read_text(encoding="utf-8")), json.loads(args.after.read_text(encoding="utf-8")))
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["status"] == "OBJECT_NOT_WORSE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
