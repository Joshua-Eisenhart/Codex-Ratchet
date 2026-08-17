#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json


def audit(current: dict, ablated: dict) -> dict:
    flip = current.get("decision") != ablated.get("decision")
    if flip and not current.get("causal_evidence"):
        return {"schema": "constraintbox.recency-audit.v1", "status": "REFUSE", "reason": "REFUSE_RECENCY_FLIP", "promotion_allowed": False}
    return {"schema": "constraintbox.recency-audit.v1", "status": "STABLE" if not flip else "EXPLAINED", "flipped": flip, "promotion_allowed": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--current", type=str, required=True)
    parser.add_argument("--ablated", type=str, required=True)
    args = parser.parse_args()
    receipt = audit(json.loads(args.current), json.loads(args.ablated))
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["status"] in {"STABLE", "EXPLAINED"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
