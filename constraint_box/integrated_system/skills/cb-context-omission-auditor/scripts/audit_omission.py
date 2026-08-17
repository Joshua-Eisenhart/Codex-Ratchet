#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

STRATA = (
    "original_object",
    "durable_constraints",
    "historical_failures",
    "unresolved_contradictions",
    "current_evidence",
    "rival_branches",
    "negative_results",
)


def audit(packet: dict) -> dict:
    missing = [key for key in STRATA if not packet.get(key)]
    if missing:
        return {"schema": "constraintbox.context-omission.v1", "status": "HOLD", "reason": "HOLD_OMITTED_STRATA", "missing": missing, "promotion_allowed": False}
    return {"schema": "constraintbox.context-omission.v1", "status": "COMPLETE", "missing": [], "promotion_allowed": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", type=str, required=True)
    args = parser.parse_args()
    receipt = audit(json.loads(args.packet))
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["status"] == "COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
