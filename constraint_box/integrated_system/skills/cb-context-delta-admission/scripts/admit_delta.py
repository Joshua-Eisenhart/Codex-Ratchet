#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

CLASSES = {
    "observation",
    "inference",
    "proposal",
    "contradiction",
    "rejection",
    "owner_amendment",
    "earned_state",
}


def admit(delta: dict) -> dict:
    klass = delta.get("class")
    if klass not in CLASSES:
        return {"schema": "constraintbox.context-delta.v1", "status": "REFUSE", "reason": "REFUSE_UNCLASSIFIED"}
    if delta.get("outranks_primary") and klass in {"proposal", "inference"}:
        return {"schema": "constraintbox.context-delta.v1", "status": "REFUSE", "reason": "REFUSE_RECENCY_OUTRANKS_PRIMARY"}
    if klass == "owner_amendment" and not delta.get("amendment_receipt"):
        return {"schema": "constraintbox.context-delta.v1", "status": "HOLD", "reason": "HOLD_AMENDMENT_RECEIPT"}
    if klass == "earned_state" and not delta.get("gate_receipt"):
        return {"schema": "constraintbox.context-delta.v1", "status": "HOLD", "reason": "HOLD_NOT_EARNED"}
    return {"schema": "constraintbox.context-delta.v1", "status": "ADMITTED", "class": klass, "promotion_allowed": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--delta", type=str, required=True)
    args = parser.parse_args()
    receipt = admit(json.loads(args.delta))
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["status"] == "ADMITTED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
