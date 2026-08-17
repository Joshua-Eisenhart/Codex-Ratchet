#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json


def check(action: dict) -> dict:
    if action.get("irreversible") and not action.get("evidence_receipt"):
        return {"schema": "constraintbox.reversibility.v1", "status": "REFUSE", "reason": "REFUSE_IRREVERSIBLE", "promotion_allowed": False}
    return {"schema": "constraintbox.reversibility.v1", "status": "REVERSIBLE_OR_EVIDENCED", "promotion_allowed": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", type=str, required=True)
    args = parser.parse_args()
    receipt = check(json.loads(args.action))
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["status"] == "REVERSIBLE_OR_EVIDENCED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
