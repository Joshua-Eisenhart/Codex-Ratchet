#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED = ("objective", "non_objectives", "forbidden", "irreversible", "unlicensed_claims")


def check(spec: dict, action: dict | None = None) -> dict:
    missing = [key for key in REQUIRED if key not in spec]
    if missing:
        return {"schema": "constraintbox.spec-boundary.v1", "status": "HOLD", "reason": "HOLD_FENCE_INCOMPLETE", "missing": missing}
    text = str((action or {}).get("text") or "").lower()
    hits = []
    for item in spec.get("forbidden") or []:
        if str(item).lower() in text:
            hits.append(f"forbidden:{item}")
    for item in spec.get("unlicensed_claims") or []:
        if str(item).lower() in text:
            hits.append(f"unlicensed:{item}")
    if hits:
        return {"schema": "constraintbox.spec-boundary.v1", "status": "REFUSE", "reason": "REFUSE_OUT_OF_BOUNDS", "hits": hits, "promotion_allowed": False}
    return {"schema": "constraintbox.spec-boundary.v1", "status": "INSIDE", "objective": spec.get("objective"), "promotion_allowed": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--action", type=str, default="{}")
    args = parser.parse_args()
    receipt = check(json.loads(args.spec.read_text(encoding="utf-8")), json.loads(args.action))
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["status"] == "INSIDE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
