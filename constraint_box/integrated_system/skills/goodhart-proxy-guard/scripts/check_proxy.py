#!/usr/bin/env python3
"""Refuse a score rise that hides a fallen protected measure."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


PROTECTED = (
    "seed_admit",
    "light_decides_control",
    "valid_v1",
    "zip_valid",
    "tests_passed",
)


def check(before: dict, after: dict) -> dict:
    fallen = []
    for key in PROTECTED:
        if after.get(key) is False and before.get(key) is not False:
            fallen.append(key)
        if isinstance(before.get(key), int) and isinstance(after.get(key), int):
            if after[key] < before[key]:
                fallen.append(key)
    if after.get("promotion_allowed") is True:
        fallen.append("promotion_allowed")
    if after.get("test_failures") and not before.get("test_failures"):
        fallen.append("test_failures")
    rose = after.get("score", 0) > before.get("score", 0)
    if rose and fallen:
        return {
            "schema": "constraintbox.goodhart-proxy.v1",
            "status": "REFUSE",
            "reason": "REFUSE_PROXY",
            "fallen": fallen,
            "promotion_allowed": False,
        }
    return {
        "schema": "constraintbox.goodhart-proxy.v1",
        "status": "PROXY_CLEAN",
        "fallen": fallen,
        "promotion_allowed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    args = parser.parse_args()
    before = json.loads(args.before.read_text(encoding="utf-8"))
    after = json.loads(args.after.read_text(encoding="utf-8"))
    receipt = check(before, after)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["status"] == "PROXY_CLEAN" else 2


if __name__ == "__main__":
    raise SystemExit(main())
